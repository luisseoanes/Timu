"""F1-PLA-01..04 Planes, cambios, cupos y recomendacion."""

from datetime import timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text

from app.core.enums import Rol
from app.core.errores import ReglaNegocio
from app.core.tiempo import hoy
from app.modules.cartera import contratos
from app.modules.cartera import service as cartera
from app.modules.cartera.contratos import _ciclo_actual
from app.modules.cartera.models import Cuota
from app.modules.cartera.periodos import dias_del_periodo, dinero
from app.modules.planes import service
from app.modules.reglas.models import Regla
from scripts import seed
from tests import fabricas
from tests.conftest import crear_usuario, login


async def test_crear_plan_con_beneficios(client: AsyncClient, headers):
    resp = await client.post(
        "/api/v1/planes",
        json={
            "codigo": "premium",
            "nombre": "Plan Premium",
            "ciudades": ["Cali"],
            "tarifas": {"por_peludos": ["95000", "90000", "85000", "80000"]},
            "beneficios": [
                {"tipo_servicio_codigo": "consulta_domiciliaria", "cupo": 4},
                {"tipo_servicio_codigo": "vacunacion"},
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    beneficios = {b["tipo_servicio_codigo"]: b["cupo"] for b in resp.json()["beneficios"]}
    assert beneficios == {"consulta_domiciliaria": 4, "vacunacion": None}


async def test_reemplazar_beneficios_por_la_api(client: AsyncClient, db, headers):
    """Responde con los beneficios nuevos y conserva los anteriores como inactivos. La
    respuesta se serializa fuera de la sesion sincrona: la coleccion tiene que llegar
    cargada, no caducada."""
    plan = await db.run_sync(
        fabricas.plan, "reemplazo", beneficios=[{"tipo_servicio_codigo": "vacunacion", "cupo": 1}]
    )
    await db.commit()
    resp = await client.put(
        f"/api/v1/planes/{plan.id}/beneficios",
        json=[{"tipo_servicio_codigo": "vacunacion", "cupo": 3}],
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert [(b["tipo_servicio_codigo"], b["cupo"]) for b in resp.json()["beneficios"]] == [
        ("vacunacion", 3)
    ]
    inactivos = await db.scalar(
        text("SELECT count(*) FROM beneficios_plan WHERE plan_id = :p AND NOT activo"),
        {"p": plan.id},
    )
    assert inactivos == 1


async def test_beneficio_con_tipo_inexistente(client: AsyncClient, headers):
    resp = await client.post(
        "/api/v1/planes",
        json={
            "codigo": "plan_x",
            "nombre": "Plan X",
            "ciudades": ["Cali"],
            "tarifas": {"por_peludos": ["1", "1", "1", "1"]},
            "beneficios": [{"tipo_servicio_codigo": "peluqueria"}],
        },
        headers=headers,
    )
    assert resp.status_code == 404


# --- 6.2 / 6.3 Tarifas por peludos, por periodicidad y por ciudad ------------------------------


@pytest.fixture
async def timu(client: AsyncClient, headers) -> dict[str, str]:
    """Los tres planes de TIMU, creados por la API como lo haria el administrador."""
    ids = {}
    for codigo, nombre, ciudades, por_peludos, largos in seed.PLANES_TIMU:
        resp = await client.post(
            "/api/v1/planes",
            json={
                "codigo": codigo,
                "nombre": nombre,
                "ciudades": ciudades,
                "especies": ["canino", "felino"],
                "tarifas": {"por_peludos": por_peludos, **largos},
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        ids[codigo] = resp.json()["id"]
    return ids


async def _cotizar(client, headers, ciudad: str, *peludos: tuple[str, str]) -> dict[str, dict]:
    resp = await client.post(
        "/api/v1/planes/cotizacion",
        json={"ciudad": ciudad, "peludos": [{"especie": e, "plan_id": p} for e, p in peludos]},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    return {c["periodicidad"]: c for c in resp.json()}


async def test_los_planes_que_siembra_el_seed_se_pueden_cotizar(db):
    """En local el seed crea los planes de TIMU: sin tarifas ni ciudades no se podria
    afiliar a nadie en un stack recien levantado."""
    creados = {p.codigo: p for p in await db.run_sync(seed.crear_planes_timu)}
    cotizacion = await db.run_sync(
        service.cotizar,
        "Bogota",
        [("felino", creados["colita_feliz"].id), ("canino", creados["mi_amigo_fiel"].id)],
        "mensual",
    )
    assert cotizacion.valor_mensual == Decimal("91500")
    with pytest.raises(ReglaNegocio, match="no esta disponible en Bogota"):
        await db.run_sync(
            service.cotizar, "Bogota", [("canino", creados["amigos_por_siempre"].id)], "mensual"
        )


async def test_un_plan_guarda_sus_tarifas_y_sus_ciudades(client: AsyncClient, headers, timu):
    plan = (await client.get(f"/api/v1/planes/{timu['colita_feliz']}", headers=headers)).json()
    assert plan["ciudades"] == ["Bogota", "Medellin"]
    assert [(t["peludos"], t["valor"]) for t in plan["tarifas"]] == [
        (1, "35500.00"),
        (2, "30500.00"),
        (3, "26000.00"),
        (4, "24000.00"),
    ]
    assert {t["periodicidad"]: t["valor"] for t in plan["tarifas_periodicidad"]} == {
        "trimestral": "103800.00",
        "semestral": "202350.00",
        "anual": "378000.00",
    }


async def test_un_solo_peludo_tiene_el_descuento_de_cada_periodo(
    client: AsyncClient, headers, timu
):
    opciones = await _cotizar(client, headers, "Medellin", ("felino", timu["colita_feliz"]))
    resumen = {
        p: (c["valor_mensual"], c["valor_periodo"], c["descuento"], c["ahorro"])
        for p, c in opciones.items()
    }
    assert resumen == {
        "mensual": ("35500.00", "35500.00", False, "0.00"),
        "trimestral": ("35500.00", "103800.00", True, "2700.00"),
        "semestral": ("35500.00", "202350.00", True, "10650.00"),
        # El anual de Colita Feliz es un precio especial: se respeta tal cual.
        "anual": ("35500.00", "378000.00", True, "48000.00"),
    }
    assert opciones["mensual"]["tarifa_de"] == 1


async def test_con_dos_peludos_cada_uno_paga_la_tarifa_de_dos_aunque_esten_en_planes_distintos(
    client: AsyncClient, headers, timu
):
    opciones = await _cotizar(
        client,
        headers,
        "Bogota",
        ("felino", timu["colita_feliz"]),
        ("canino", timu["mi_amigo_fiel"]),
    )
    mensual = opciones["mensual"]
    assert mensual["tarifa_de"] == 2
    assert [p["valor_mensual"] for p in mensual["peludos"]] == ["30500.00", "61000.00"]
    assert mensual["valor_mensual"] == "91500.00"
    # El descuento de cantidad no se acumula con el de periodicidad: periodos largos sin
    # descuento, el mensual por los meses.
    assert (opciones["trimestral"]["valor_periodo"], opciones["trimestral"]["descuento"]) == (
        "274500.00",
        False,
    )
    assert opciones["anual"]["valor_periodo"] == "1098000.00"


async def test_desde_cuatro_peludos_todos_pagan_la_tarifa_de_cuatro_y_el_maximo_es_diez(
    client: AsyncClient, headers, timu
):
    cinco = [("canino", timu["colita_feliz"])] * 5
    mensual = (await _cotizar(client, headers, "Medellin", *cinco))["mensual"]
    assert (mensual["tarifa_de"], mensual["valor_mensual"]) == (4, "120000.00")
    once = await client.post(
        "/api/v1/planes/cotizacion",
        json={
            "ciudad": "Medellin",
            "peludos": [{"especie": "canino", "plan_id": timu["colita_feliz"]}] * 11,
        },
        headers=headers,
    )
    assert once.status_code == 422 and "maximo 10" in once.text


async def test_la_cotizacion_respeta_la_ciudad_y_la_especie_del_plan(
    client: AsyncClient, headers, timu
):
    en_bogota = await client.post(
        "/api/v1/planes/cotizacion",
        json={
            "ciudad": "Bogota",
            "peludos": [{"especie": "canino", "plan_id": timu["amigos_por_siempre"]}],
        },
        headers=headers,
    )
    assert en_bogota.status_code == 422 and "no esta disponible en Bogota" in en_bogota.text
    ave = await client.post(
        "/api/v1/planes/cotizacion",
        json={
            "ciudad": "Medellin",
            "peludos": [{"especie": "ave", "plan_id": timu["colita_feliz"]}],
        },
        headers=headers,
    )
    assert ave.status_code == 422 and "no cubre: ave" in ave.text
    # El listado por ciudad solo trae lo que se vende alli.
    bogota = (await client.get("/api/v1/planes?ciudad=Bogota", headers=headers)).json()
    assert {p["codigo"] for p in bogota} == {"colita_feliz", "mi_amigo_fiel"}


async def test_el_administrador_cambia_tarifas_y_ciudades_sin_borrar_nada(
    client: AsyncClient, db, headers, timu
):
    plan = timu["colita_feliz"]
    resp = await client.put(
        f"/api/v1/planes/{plan}/tarifas",
        json={"por_peludos": ["36000", "31000", "26500", "24500"], "semestral": "205000"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    # Sin trimestral ni anual: esos descuentos se retiran.
    assert [t["periodicidad"] for t in resp.json()["tarifas_periodicidad"]] == ["semestral"]
    opciones = await _cotizar(client, headers, "Medellin", ("canino", plan))
    assert (opciones["trimestral"]["valor_periodo"], opciones["trimestral"]["descuento"]) == (
        "108000.00",
        False,
    )
    retiradas = await db.scalar(
        text("SELECT count(*) FROM tarifas_periodicidad WHERE plan_id = :p AND NOT activa"),
        {"p": plan},
    )
    assert retiradas == 2

    resp = await client.put(f"/api/v1/planes/{plan}/ciudades", json=["medellin"], headers=headers)
    assert resp.status_code == 200 and resp.json()["ciudades"] == ["Medellin"]
    resp = await client.put(
        f"/api/v1/planes/{plan}/ciudades", json=["Medellin", "Bogota"], headers=headers
    )
    assert resp.json()["ciudades"] == ["Bogota", "Medellin"]
    filas = await db.scalar(
        text("SELECT count(*) FROM ciudades_plan WHERE plan_id = :p"), {"p": plan}
    )
    assert filas == 2  # Bogota volvio a activarse; no se creo otra fila

    tres = await client.put(
        f"/api/v1/planes/{plan}/tarifas",
        json={"por_peludos": ["1", "2", "3"]},
        headers=headers,
    )
    assert tres.status_code == 422


async def test_solo_el_administrador_cambia_tarifas(client: AsyncClient, db, timu):
    await crear_usuario(db, "comercial@timu.co", Rol.COMERCIAL)
    comercial = await login(client, "comercial@timu.co")
    resp = await client.put(
        f"/api/v1/planes/{timu['colita_feliz']}/tarifas",
        json={"por_peludos": ["1", "1", "1", "1"]},
        headers=comercial,
    )
    assert resp.status_code == 403
    # Cotizar si: el equipo comercial la usa para afiliar.
    opciones = await _cotizar(client, comercial, "Medellin", ("canino", timu["colita_feliz"]))
    assert opciones["mensual"]["valor_periodo"] == "35500.00"


# --- F1-PLA-04 --------------------------------------------------------------------------------


async def test_recomendacion_por_composicion(client: AsyncClient, db, headers):
    await db.run_sync(fabricas.plan, "individual", 45_000, 1)
    await db.run_sync(fabricas.plan, "familiar", 75_000, 3)
    await db.commit()
    una = await client.get(
        "/api/v1/planes/recomendacion", params={"ciudad": "cali"}, headers=headers
    )
    assert (una.json()["plan"]["codigo"], una.json()["regla"]) == (
        "individual",
        "recomendar_individual",
    )
    dos = await client.get(
        "/api/v1/planes/recomendacion",
        params={"ciudad": "Cali", "especies": ["canino", "felino"]},
        headers=headers,
    )
    assert dos.json()["plan"]["codigo"] == "familiar"
    assert "varias mascotas" in dos.json()["motivo"]


async def test_recomendacion_salta_plan_de_otra_ciudad(db):
    await db.run_sync(fabricas.plan, "familiar", 75_000, 3, ciudad="Bogota")
    await db.run_sync(fabricas.plan, "multi", 80_000, 4)
    plan, _, regla = await db.run_sync(service.recomendar, "Cali", ["canino", "canino"])
    assert plan.codigo == "multi"
    assert regla == "por_defecto"


# --- F1-PLA-02 --------------------------------------------------------------------------------


async def test_subir_de_plan_cobra_prorrateo(db):
    basico = await db.run_sync(fabricas.plan, "basico", 45_000)
    superior = await db.run_sync(fabricas.plan, "superior", 75_000)
    _, contrato = await fabricas.afiliada(db, hoy() - timedelta(days=10), basico)

    cambio = await db.run_sync(contratos.cambiar_plan, contrato, superior, None)

    inicio, fin = _ciclo_actual(contrato, hoy())
    esperado = dinero(Decimal(30_000) * (fin - hoy()).days / dias_del_periodo(inicio))
    assert dinero(cambio.ajuste) == esperado
    assert cambio.regla_codigo == "cambio_plan_prorrateo"
    assert dinero(contrato.valor_mensual) == Decimal("75000.00")
    ajuste = await db.scalar(select(Cuota).where(Cuota.tipo == "ajuste"))
    assert dinero(ajuste.valor) == esperado


async def test_bajar_de_plan_deja_saldo_a_favor(db):
    superior = await db.run_sync(fabricas.plan, "superior", 75_000)
    basico = await db.run_sync(fabricas.plan, "basico", 45_000)
    _, contrato = await fabricas.afiliada(db, hoy() - timedelta(days=3), superior)
    cambio = await db.run_sync(contratos.cambiar_plan, contrato, basico, None)
    assert cambio.ajuste < 0
    assert dinero(contrato.saldo_a_favor) == -dinero(cambio.ajuste)


async def test_no_cambia_de_plan_en_mora(db):
    basico = await db.run_sync(fabricas.plan, "basico", 45_000)
    superior = await db.run_sync(fabricas.plan, "superior", 75_000)
    # La primera cuota vencio hace 10 dias y no se pago.
    _, contrato = await fabricas.afiliada(db, hoy() - timedelta(days=10), basico)
    await db.run_sync(cartera.reevaluar_estado, contrato)
    import pytest

    with pytest.raises(ReglaNegocio, match="al dia"):
        await db.run_sync(contratos.cambiar_plan, contrato, superior, None)


async def test_cambio_al_proximo_ciclo_por_regla(db):
    """Cambiar la regla (sin desplegar) cambia como se cobra el cambio de plan."""
    regla = await db.scalar(select(Regla).where(Regla.codigo == "cambio_plan_prorrateo"))
    regla.accion = {"tipo": "prorrateo", "modo": "proximo_ciclo"}
    basico = await db.run_sync(fabricas.plan, "basico", 45_000)
    superior = await db.run_sync(fabricas.plan, "superior", 75_000)
    _, contrato = await fabricas.afiliada(db, hoy() - timedelta(days=10), basico)

    cambio = await db.run_sync(contratos.cambiar_plan, contrato, superior, None)
    assert cambio.aplicado is False
    assert contrato.plan_id == basico.id

    await db.run_sync(cartera.generar_cuotas, cambio.fecha_efectiva)
    assert cambio.aplicado is True
    assert contrato.plan_id == superior.id
    siguiente = await db.scalar(
        select(Cuota).where(Cuota.fecha_vencimiento == cambio.fecha_efectiva)
    )
    assert dinero(siguiente.valor) == Decimal("75000.00")


# --- F1-PLA-03 --------------------------------------------------------------------------------


async def test_mascota_sobre_el_cupo_se_rechaza(client: AsyncClient, db, headers):
    familia, _ = await fabricas.afiliada(db, hoy())
    await db.commit()
    resp = await client.post(
        f"/api/v1/familias/{familia.id}/mascotas",
        json={
            "nombre": "Otra",
            "especie": "canino",
            "fecha_nacimiento": "2021-03-01",
            "peso_kg": 12.5,
        },
        headers=headers,
    )
    assert resp.status_code == 422
    assert "cupo" in resp.json()["detail"]


async def test_mascota_adicional_con_regla_de_ajuste(client: AsyncClient, db, headers):
    p = await db.run_sync(fabricas.plan, "individual", 45_000, 1)
    db.add(
        Regla(
            codigo="adicional_individual",
            nombre="Adicional 15.000",
            evento="plan.mascota",
            condicion={},
            accion={
                "tipo": "ajuste_mascota",
                "valor_por_mascota_adicional": 15000,
                "maximo_adicionales": 2,
            },
            prioridad=10,
            detener=True,
            plan_id=p.id,
        )
    )
    familia, contrato = await fabricas.afiliada(db, hoy(), p)
    await db.commit()

    alta = await client.post(
        f"/api/v1/familias/{familia.id}/mascotas",
        json={
            "nombre": "Luna",
            "especie": "canino",
            "fecha_nacimiento": "2021-03-01",
            "peso_kg": 12.5,
        },
        headers=headers,
    )
    assert alta.status_code == 201
    await db.refresh(contrato)
    assert (contrato.mascotas_adicionales, dinero(contrato.valor_mensual)) == (
        1,
        Decimal("60000.00"),
    )

    baja = await client.post(
        f"/api/v1/mascotas/{alta.json()['id']}/baja", json={"motivo": "Adopcion"}, headers=headers
    )
    assert baja.status_code == 200
    await db.refresh(contrato)
    assert dinero(contrato.valor_mensual) == Decimal("45000.00")


async def test_mascota_nueva_recibe_calendario_preventivo(client: AsyncClient, db, headers):
    from app.modules.preventivos.models import EventoPreventivo

    p = await db.run_sync(fabricas.plan, "familiar", 75_000, 3)
    familia, _ = await fabricas.afiliada(db, hoy(), p)
    await db.commit()
    resp = await client.post(
        f"/api/v1/familias/{familia.id}/mascotas",
        json={
            "nombre": "Michi",
            "especie": "felino",
            "fecha_nacimiento": str(hoy() - timedelta(weeks=4)),
            "peso_kg": 0.6,
        },
        headers=headers,
    )
    eventos = list(
        await db.scalars(
            select(EventoPreventivo).where(EventoPreventivo.mascota_id == UUID(resp.json()["id"]))
        )
    )
    triple = sorted(
        (e for e in eventos if e.esquema_codigo == "fel_triple"), key=lambda e: e.dosis_numero
    )
    # Gatito de 4 semanas: la triple arranca a las 8 semanas, 2 dosis con 21 dias.
    assert [e.fecha_programada for e in triple] == [
        hoy() + timedelta(weeks=4),
        hoy() + timedelta(weeks=4, days=21),
    ]

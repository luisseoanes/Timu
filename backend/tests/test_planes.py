"""F1-PLA-01..04 Planes, cambios, cupos y recomendacion."""

from datetime import timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text

from app.core.enums import ColorPlan, Rol
from app.core.errores import ReglaNegocio
from app.core.tiempo import hoy
from app.modules.cartera import contratos
from app.modules.cartera import service as cartera
from app.modules.cartera.contratos import ciclo_actual
from app.modules.cartera.models import Cuota
from app.modules.cartera.periodos import dias_del_periodo, dinero, sumar_meses
from app.modules.familias import service as familias_service
from app.modules.familias.models import Mascota
from app.modules.planes import service
from app.modules.planes.models import CambioPlan
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
    for codigo, nombre, color, ciudades, por_peludos, largos in seed.PLANES_TIMU:
        resp = await client.post(
            "/api/v1/planes",
            json={
                "codigo": codigo,
                "nombre": nombre,
                "color": color,
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


async def test_los_planes_de_timu_llevan_el_color_del_manual_de_marca(db):
    """R1-PLA-01: la interfaz reconoce el plan por su color, que sale del catalogo y no de
    comparar nombres (docs/manual-de-marca.md, seccion 4)."""
    creados = {p.codigo: p.color for p in await db.run_sync(seed.crear_planes_timu)}
    assert creados == {
        "colita_feliz": ColorPlan.NARANJA,
        "mi_amigo_fiel": ColorPlan.VERDE,
        "amigos_por_siempre": ColorPlan.AZUL,
    }


async def test_un_plan_nuevo_es_verde_hasta_que_se_le_cambia_el_color(client: AsyncClient, headers):
    creado = await client.post(
        "/api/v1/planes",
        json={
            "codigo": "basico",
            "nombre": "Plan Basico",
            "ciudades": ["Cali"],
            "tarifas": {"por_peludos": ["30000", "28000", "26000", "24000"]},
        },
        headers=headers,
    )
    assert creado.status_code == 201, creado.text
    assert creado.json()["color"] == "verde"

    cambiado = await client.patch(
        f"/api/v1/planes/{creado.json()['id']}", json={"color": "azul"}, headers=headers
    )
    assert cambiado.status_code == 200, cambiado.text
    assert cambiado.json()["color"] == "azul"


async def test_el_color_de_un_plan_solo_puede_ser_uno_del_logo(client: AsyncClient, headers, timu):
    resp = await client.patch(
        f"/api/v1/planes/{timu['colita_feliz']}", json={"color": "rojo"}, headers=headers
    )
    assert resp.status_code == 422


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


# --- F1-PLA-02 Cambio de plan de un peludo ---------------------------------------------------


async def test_subir_de_plan_cobra_prorrateo(db):
    basico = await db.run_sync(fabricas.plan, "basico", 45_000)
    superior = await db.run_sync(fabricas.plan, "superior", 75_000)
    familia, contrato = await fabricas.afiliada(db, hoy() - timedelta(days=10), basico)
    mascota = familia.mascotas[0].id

    cambio = await db.run_sync(contratos.cambiar_plan, contrato, mascota, superior, None)

    inicio, fin = ciclo_actual(contrato, hoy())
    esperado = dinero(Decimal(30_000) * (fin - hoy()).days / dias_del_periodo(inicio))
    assert dinero(cambio.ajuste) == esperado
    assert (cambio.regla_codigo, cambio.mascota_id) == ("cambio_plan_prorrateo", mascota)
    assert dinero(contrato.valor_periodo) == Decimal("75000.00")
    assert (await db.run_sync(contratos.plan_de_mascota, mascota)).id == superior.id
    ajuste = await db.scalar(select(Cuota).where(Cuota.tipo == "ajuste"))
    assert dinero(ajuste.valor) == esperado


async def test_bajar_de_plan_deja_saldo_a_favor(db):
    superior = await db.run_sync(fabricas.plan, "superior", 75_000)
    basico = await db.run_sync(fabricas.plan, "basico", 45_000)
    familia, contrato = await fabricas.afiliada(db, hoy() - timedelta(days=3), superior)
    cambio = await db.run_sync(
        contratos.cambiar_plan, contrato, familia.mascotas[0].id, basico, None
    )
    assert cambio.ajuste < 0
    assert dinero(contrato.saldo_a_favor) == -dinero(cambio.ajuste)


async def test_no_cambia_de_plan_en_mora(db):
    basico = await db.run_sync(fabricas.plan, "basico", 45_000)
    superior = await db.run_sync(fabricas.plan, "superior", 75_000)
    # La primera cuota vencio hace 10 dias y no se pago.
    familia, contrato = await fabricas.afiliada(db, hoy() - timedelta(days=10), basico)
    await db.run_sync(cartera.reevaluar_estado, contrato)
    with pytest.raises(ReglaNegocio, match="al dia"):
        await db.run_sync(contratos.cambiar_plan, contrato, familia.mascotas[0].id, superior, None)


async def test_cambio_al_proximo_ciclo_por_regla(db):
    """Cambiar la regla (sin desplegar) cambia como se cobra el cambio de plan."""
    regla = await db.scalar(select(Regla).where(Regla.codigo == "cambio_plan_prorrateo"))
    regla.accion = {"tipo": "prorrateo", "modo": "proximo_ciclo"}
    basico = await db.run_sync(fabricas.plan, "basico", 45_000)
    superior = await db.run_sync(fabricas.plan, "superior", 75_000)
    familia, contrato = await fabricas.afiliada(db, hoy() - timedelta(days=10), basico)
    mascota = familia.mascotas[0].id

    cambio = await db.run_sync(contratos.cambiar_plan, contrato, mascota, superior, None)
    assert cambio.aplicado is False
    assert (await db.run_sync(contratos.plan_de_mascota, mascota)).id == basico.id

    await db.run_sync(cartera.generar_cuotas, cambio.fecha_efectiva)
    assert cambio.aplicado is True
    assert (await db.run_sync(contratos.plan_de_mascota, mascota)).id == superior.id
    siguiente = await db.scalar(
        select(Cuota).where(Cuota.fecha_vencimiento == cambio.fecha_efectiva)
    )
    assert dinero(siguiente.valor) == Decimal("75000.00")


async def test_el_cambio_de_plan_de_un_peludo_no_cambia_el_de_los_demas(db):
    colita = await db.run_sync(fabricas.plan, "colita", tarifas=[35_500, 30_500, 26_000, 24_000])
    fiel = await db.run_sync(fabricas.plan, "fiel", tarifas=[69_000, 61_000, 57_500, 57_000])
    familia, contrato = await fabricas.afiliada(db, hoy(), colita, mascotas=2)
    luna, max_ = familia.mascotas
    await db.run_sync(contratos.cambiar_plan, contrato, max_.id, fiel, None)
    assert (await db.run_sync(contratos.plan_de_mascota, luna.id)).id == colita.id
    # Siguen siendo 2 peludos: cada uno con la tarifa de 2 de su plan.
    assert dinero(contrato.valor_periodo) == Decimal("91500.00")


# --- 6.3 Alta y retiro de un peludo ------------------------------------------------------------

PELUDO = {"especie": "canino", "fecha_nacimiento": "2021-03-01", "peso_kg": 12.5}


@pytest.fixture
async def colita(db):
    """Un plan con las tarifas de Colita Feliz y una familia con un peludo en el."""
    plan = await db.run_sync(
        fabricas.plan,
        "colita",
        tarifas=[35_500, 30_500, 26_000, 24_000],
        largos={"trimestral": 103_800},
    )
    familia, contrato = await fabricas.afiliada(db, hoy(), plan)
    await db.commit()
    return plan, familia, contrato


async def test_con_afiliacion_vigente_el_panel_pide_el_plan_de_la_mascota_nueva(
    client: AsyncClient, colita, headers
):
    _, familia, _ = colita
    resp = await client.post(
        f"/api/v1/familias/{familia.id}/mascotas",
        json={"nombre": "Otra", **PELUDO},
        headers=headers,
    )
    assert resp.status_code == 422 and "Elige el plan" in resp.text


async def test_un_peludo_mas_baja_la_tarifa_de_todos_desde_la_siguiente_cuota(
    client: AsyncClient, db, colita, headers
):
    plan, familia, contrato = colita
    primera = await db.scalar(select(Cuota).where(Cuota.contrato_id == contrato.id))
    alta = await client.post(
        f"/api/v1/familias/{familia.id}/mascotas",
        json={"nombre": "Luna", "plan_id": str(plan.id), **PELUDO},
        headers=headers,
    )
    assert alta.status_code == 201, alta.text
    await db.refresh(contrato)
    assert dinero(contrato.valor_periodo) == Decimal("61000.00")  # 2 x 30.500
    lineas = await db.run_sync(contratos.lineas, contrato)
    assert [dinero(linea.valor_mensual) for linea in lineas] == [Decimal("30500.00")] * 2
    # La cuota ya emitida no cambia.
    await db.refresh(primera)
    assert dinero(primera.valor) == Decimal("35500.00")
    cambio = await db.scalar(select(CambioPlan).where(CambioPlan.tipo == "mascota_alta"))
    assert (dinero(cambio.valor_anterior), dinero(cambio.valor_nuevo)) == (
        Decimal("35500.00"),
        Decimal("61000.00"),
    )

    # Al retirarlo, el que queda vuelve a la tarifa de 1.
    baja = await client.post(
        f"/api/v1/mascotas/{alta.json()['id']}/baja", json={"motivo": "Adopcion"}, headers=headers
    )
    assert baja.status_code == 200
    await db.refresh(contrato)
    assert dinero(contrato.valor_periodo) == Decimal("35500.00")


async def test_el_unico_peludo_no_se_retira_sin_cancelar_el_contrato(
    client: AsyncClient, colita, headers
):
    _, familia, _ = colita
    resp = await client.post(
        f"/api/v1/mascotas/{familia.mascotas[0].id}/baja",
        json={"motivo": "Fallecio"},
        headers=headers,
    )
    assert resp.status_code == 422 and "cancelar el contrato" in resp.text


async def test_un_plan_que_deja_de_venderse_no_impide_retirar_a_otro_peludo(db):
    viejo = await db.run_sync(fabricas.plan, "viejo", 40_000)
    familia, contrato = await fabricas.afiliada(db, hoy(), viejo, mascotas=2)
    await db.run_sync(lambda s: service.fijar_ciudades(s, viejo, ["Bogota"]))  # ya no en Cali
    await db.run_sync(contratos.retirar_mascota, contrato, familia.mascotas[1].id, None)
    assert dinero(contrato.valor_periodo) == Decimal("40000.00")


async def test_trimestral_con_un_peludo_y_sin_descuento_al_sumar_otro(db, colita):
    plan, familia, _ = colita
    otra = await db.run_sync(fabricas.familia)
    planes_otra = {otra.mascotas[0].id: plan.id}
    contrato, cuota = await db.run_sync(
        lambda s: cartera.crear_contrato(
            s, otra, planes_otra, periodicidad="trimestral", fecha_inicio=hoy()
        )
    )
    assert (dinero(contrato.valor_periodo), dinero(contrato.valor_mensual)) == (
        Decimal("103800.00"),
        Decimal("35500.00"),
    )
    assert (cuota.meses, dinero(cuota.valor)) == (3, Decimal("103800.00"))
    # La siguiente cuota es tres meses despues.
    await db.run_sync(cartera.generar_cuotas, sumar_meses(hoy(), 3))
    periodos = list(
        await db.scalars(
            select(Cuota.periodo).where(Cuota.contrato_id == contrato.id).order_by(Cuota.periodo)
        )
    )
    assert periodos == [f"{hoy():%Y-%m}", f"{sumar_meses(hoy(), 3):%Y-%m}"]

    # Con un segundo peludo ya no hay descuento: el mensual de los dos por tres meses.
    nueva = await db.run_sync(
        lambda s: familias_service.incorporar_mascota(
            s, otra, Mascota(nombre="Coco", especie="felino", familia_id=otra.id)
        )
    )
    await db.run_sync(contratos.agregar_mascota, contrato, nueva, plan.id, None)
    assert dinero(contrato.valor_periodo) == Decimal("183000.00")  # 2 x 30.500 x 3


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
            "plan_id": str(p.id),
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

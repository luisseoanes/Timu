"""F1-PLA-01..04 Planes, cambios, cupos y recomendacion."""

from datetime import timedelta
from decimal import Decimal
from uuid import UUID

from httpx import AsyncClient
from sqlalchemy import select

from app.core.tiempo import hoy
from app.modules.cartera import service as cartera
from app.modules.cartera.models import Cuota
from app.modules.cartera.periodos import dias_del_periodo, dinero
from app.modules.planes import service
from app.modules.planes.service import _ciclo_actual
from app.modules.reglas.models import Regla
from tests import fabricas


async def test_crear_plan_con_beneficios(client: AsyncClient, headers):
    resp = await client.post(
        "/api/v1/planes",
        json={
            "codigo": "premium",
            "nombre": "Plan Premium",
            "valor_mensual": "95000",
            "cupos_mascotas": 2,
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


async def test_beneficio_con_tipo_inexistente(client: AsyncClient, headers):
    resp = await client.post(
        "/api/v1/planes",
        json={
            "codigo": "plan_x",
            "nombre": "Plan X",
            "valor_mensual": "1",
            "beneficios": [{"tipo_servicio_codigo": "peluqueria"}],
        },
        headers=headers,
    )
    assert resp.status_code == 404


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

    cambio = await db.run_sync(service.cambiar_plan, contrato, superior, None)

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
    cambio = await db.run_sync(service.cambiar_plan, contrato, basico, None)
    assert cambio.ajuste < 0
    assert dinero(contrato.saldo_a_favor) == -dinero(cambio.ajuste)


async def test_no_cambia_de_plan_en_mora(db):
    basico = await db.run_sync(fabricas.plan, "basico", 45_000)
    superior = await db.run_sync(fabricas.plan, "superior", 75_000)
    # La primera cuota vencio hace 10 dias y no se pago.
    _, contrato = await fabricas.afiliada(db, hoy() - timedelta(days=10), basico)
    await db.run_sync(cartera.reevaluar_estado, contrato)
    import pytest

    from app.core.errores import ReglaNegocio

    with pytest.raises(ReglaNegocio, match="al dia"):
        await db.run_sync(service.cambiar_plan, contrato, superior, None)


async def test_cambio_al_proximo_ciclo_por_regla(db):
    """Cambiar la regla (sin desplegar) cambia como se cobra el cambio de plan."""
    regla = await db.scalar(select(Regla).where(Regla.codigo == "cambio_plan_prorrateo"))
    regla.accion = {"tipo": "prorrateo", "modo": "proximo_ciclo"}
    basico = await db.run_sync(fabricas.plan, "basico", 45_000)
    superior = await db.run_sync(fabricas.plan, "superior", 75_000)
    _, contrato = await fabricas.afiliada(db, hoy() - timedelta(days=10), basico)

    cambio = await db.run_sync(service.cambiar_plan, contrato, superior, None)
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
        json={"nombre": "Otra", "especie": "canino"},
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
        json={"nombre": "Luna", "especie": "canino"},
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

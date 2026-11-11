"""R2-PAN-02 La linea de cada familia: cuotas, preventivos y servicios por fecha."""

from datetime import UTC, date, datetime
from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy import select, update

from app.core.enums import (
    ColorPlan,
    EstadoEventoPreventivo,
    EstadoServicio,
    TipoPreventivo,
    TipoServicio,
)
from app.modules.afiliaciones import linea
from app.modules.cartera.models import Contrato, Cuota, EstadoCuota
from app.modules.preventivos.models import EventoPreventivo
from app.modules.servicios.models import Servicio
from tests import fabricas

DIA = date(2026, 11, 10)


def _cuota(contrato_id, periodo: str, vence: date, estado: EstadoCuota) -> Cuota:
    pagada = estado == EstadoCuota.PAGADA
    return Cuota(
        contrato_id=contrato_id,
        periodo=periodo,
        fecha_vencimiento=vence,
        valor=Decimal("69000"),
        valor_pagado=Decimal("69000") if pagada else Decimal("0"),
        estado=estado,
    )


async def _familia_con_historia(db):
    """Una familia afiliada con cuotas, preventivos y servicios en todos los estados. La
    cuota que crea el contrato se anula para que no se cuele en las comprobaciones."""
    familia, contrato = await fabricas.afiliada(db, DIA)
    await db.execute(
        update(Cuota).where(Cuota.contrato_id == contrato.id).values(estado=EstadoCuota.ANULADA)
    )
    mascota = familia.mascotas[0]
    db.add_all(
        [
            _cuota(
                contrato.id, "2025-01", date(2025, 1, 5), EstadoCuota.PENDIENTE
            ),  # vencida antigua
            _cuota(
                contrato.id, "2025-02", date(2025, 2, 5), EstadoCuota.PAGADA
            ),  # fuera de ventana
            _cuota(contrato.id, "2026-06", date(2026, 6, 5), EstadoCuota.PAGADA),
            _cuota(contrato.id, "2026-07", date(2026, 7, 5), EstadoCuota.ANULADA),
            _cuota(contrato.id, "2026-09", date(2026, 9, 5), EstadoCuota.PENDIENTE),
            _cuota(contrato.id, "2026-12", date(2026, 12, 5), EstadoCuota.PENDIENTE),
            _cuota(contrato.id, "2027-01", date(2027, 1, 5), EstadoCuota.PENDIENTE),
            EventoPreventivo(
                mascota_id=mascota.id,
                tipo=TipoPreventivo.VACUNA,
                fecha_programada=date(2026, 8, 1),
                fecha_aplicacion=date(2026, 8, 3),
                estado=EstadoEventoPreventivo.APLICADO,
            ),
            EventoPreventivo(
                mascota_id=mascota.id,
                tipo=TipoPreventivo.DESPARASITACION_INTERNA,
                fecha_programada=date(2026, 11, 18),
                estado=EstadoEventoPreventivo.PROGRAMADO,
            ),
            EventoPreventivo(
                mascota_id=mascota.id,
                tipo=TipoPreventivo.VACUNA,
                fecha_programada=date(2026, 12, 1),
                estado=EstadoEventoPreventivo.CANCELADO,
            ),
            Servicio(
                familia_id=familia.id,
                mascota_id=mascota.id,
                tipo_codigo="consulta_domiciliaria",
                tipo=TipoServicio.DOMICILIARIO,
                ciudad="Cali",
                programado_para=datetime(2026, 10, 28, 15, tzinfo=UTC),
                estado=EstadoServicio.COMPLETADO,
            ),
            Servicio(
                familia_id=familia.id,
                tipo_codigo="consulta_domiciliaria",
                tipo=TipoServicio.DOMICILIARIO,
                ciudad="Cali",
                programado_para=datetime(2026, 11, 20, 15, tzinfo=UTC),
                estado=EstadoServicio.CANCELADO,
                motivo_estado="La familia no estaba",
            ),
        ]
    )
    await db.flush()
    return familia


async def test_la_linea_ordena_por_fecha_y_marca_cada_estacion(db):
    familia = await _familia_con_historia(db)
    estaciones = (await db.run_sync(linea.lineas, [familia.id], DIA))[familia.id]
    resumen = [(e.fecha, e.tipo, e.estado, e.titulo) for e in estaciones]
    assert resumen == [
        (date(2025, 1, 5), "cuota", "vencida", "Cuota de enero de 2025"),
        (date(2026, 6, 5), "cuota", "hecha", "Cuota de junio"),
        (date(2026, 8, 3), "preventivo", "hecha", "Vacuna"),
        (date(2026, 9, 5), "cuota", "vencida", "Cuota de septiembre"),
        (date(2026, 10, 28), "servicio", "hecha", "Consulta domiciliaria"),
        (date(2026, 11, 18), "preventivo", "proxima", "Desparasitación interna"),
        (date(2026, 12, 5), "cuota", "futura", "Cuota de diciembre"),
        (date(2027, 1, 5), "cuota", "futura", "Cuota de enero de 2027"),
    ]
    assert {e.mascota for e in estaciones if e.tipo != "cuota"} == {familia.mascotas[0].nombre}


async def test_lo_vencido_entra_aunque_quede_fuera_de_la_ventana(db):
    """Una ventana que escondiera una cuota vencida hace un ano mentiria sobre la familia."""
    familia = await _familia_con_historia(db)
    estaciones = (await db.run_sync(linea.lineas, [familia.id], DIA))[familia.id]
    antiguas = [e for e in estaciones if e.fecha < date(2026, 5, 10)]
    assert [(e.titulo, e.estado) for e in antiguas] == [("Cuota de enero de 2025", "vencida")]


async def test_una_familia_sin_nada_tiene_la_linea_vacia(db):
    familia = await db.run_sync(fabricas.familia)
    assert await db.run_sync(linea.lineas, [familia.id], DIA) == {familia.id: []}


async def test_el_listado_pide_la_linea_de_varias_familias_a_la_vez(
    client: AsyncClient, db, headers
):
    con_historia = await _familia_con_historia(db)
    sin_nada = await db.run_sync(fabricas.familia, telefono="+573001112244")
    ids = [con_historia.id, sin_nada.id]
    resp = await client.get(
        "/api/v1/afiliaciones/lineas", params=[("familia_id", str(i)) for i in ids], headers=headers
    )
    assert resp.status_code == 200, resp.text
    lineas = {item["familia_id"]: item["estaciones"] for item in resp.json()}
    assert set(lineas) == {str(i) for i in ids}
    assert lineas[str(sin_nada.id)] == []
    assert {item["familia_id"] for item in resp.json() if item["planes"]} == {str(con_historia.id)}
    assert {"tipo", "referencia_id", "fecha", "estado", "titulo", "mascota"} <= set(
        lineas[str(con_historia.id)][0]
    )


async def test_el_listado_limita_cuantas_familias_se_piden(client: AsyncClient, headers):
    sin_ninguna = await client.get("/api/v1/afiliaciones/lineas", headers=headers)
    assert sin_ninguna.status_code == 422
    demasiadas = [
        ("familia_id", f"00000000-0000-7000-8000-{i:012d}") for i in range(linea.MAX_FAMILIAS + 1)
    ]
    resp = await client.get("/api/v1/afiliaciones/lineas", params=demasiadas, headers=headers)
    assert resp.status_code == 422


async def test_la_linea_de_una_familia(client: AsyncClient, db, headers):
    familia = await _familia_con_historia(db)
    resp = await client.get(f"/api/v1/familias/{familia.id}/linea", headers=headers)
    assert resp.status_code == 200, resp.text
    cuerpo = resp.json()
    assert cuerpo["familia_id"] == str(familia.id)
    proximas = [e for e in cuerpo["estaciones"] if e["estado"] == "proxima"]
    assert len(proximas) <= 1


async def test_la_linea_de_una_familia_que_no_existe_es_404(client: AsyncClient, headers):
    resp = await client.get(
        "/api/v1/familias/00000000-0000-7000-8000-000000000000/linea", headers=headers
    )
    assert resp.status_code == 404


async def test_las_cuotas_de_otra_familia_no_se_cuelan(db):
    familia = await _familia_con_historia(db)
    otra, _ = await fabricas.afiliada(db, DIA, telefono="+573001112255")
    lineas = await db.run_sync(linea.lineas, [familia.id, otra.id], DIA)
    ids = {e.referencia_id for e in lineas[familia.id]}
    assert not ids & {e.referencia_id for e in lineas[otra.id]}
    cuotas_de_otra = set(
        await db.scalars(
            select(Cuota.id)
            .join(Contrato, Cuota.contrato_id == Contrato.id)
            .where(Contrato.familia_id == otra.id)
        )
    )
    assert cuotas_de_otra, "la otra familia tiene la primera cuota de su contrato"
    assert not ids & cuotas_de_otra


async def test_la_linea_trae_los_planes_vigentes_con_su_color(db):
    """El listado muestra el plan de cada familia con el color del catalogo, no deducido del
    nombre (manual de marca, regla 5)."""
    p = await db.run_sync(fabricas.plan, "azulito")
    p.color = ColorPlan.AZUL
    familia, _ = await fabricas.afiliada(db, DIA, p, mascotas=2)
    sin_contrato = await db.run_sync(fabricas.familia, telefono="+573001112266")
    await db.flush()
    planes = await db.run_sync(linea.planes, [familia.id, sin_contrato.id])
    assert planes[sin_contrato.id] == []
    [plan] = planes[familia.id]
    assert (plan.nombre, plan.color) == ("Plan azulito", ColorPlan.AZUL)
    assert plan.mascotas == tuple(sorted(m.nombre for m in familia.mascotas))

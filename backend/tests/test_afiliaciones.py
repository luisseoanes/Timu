"""F1-AFI-01..03 Afiliacion: formulario -> pago -> contrato -> perfil."""

from decimal import Decimal
from urllib.parse import parse_qs, urlparse
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.core.config import settings
from app.modules.afiliaciones.models import SolicitudAfiliacion
from app.modules.cartera import pasarela
from app.modules.cartera.models import Contrato, Cuota
from app.modules.comunicaciones.models import Mensaje
from app.modules.familias.models import Familia
from app.modules.planes import service as planes_service
from app.modules.preventivos.models import EventoPreventivo
from app.modules.tareas.models import Tarea
from tests import fabricas
from tests.test_cartera import _evento

FORMULARIO = {
    "barrio": "Centro",
    "titular_nombre": "Luisa Gomez",
    "documento": "52111222",
    "telefono": "3157778899",
    "email": "luisa@correo.com",
    "ciudad": "Cali",
    "direccion": "Calle 5 # 10-20",
    "mascotas": [{"nombre": "Toby", "especie": "canino"}],
    "plan_codigo": "individual",
    "acepta_condiciones": True,
    "acepta_tratamiento_datos": True,
}


@pytest.fixture
async def catalogo_planes(db, monkeypatch):
    monkeypatch.setattr(settings, "WOMPI_EVENTS_SECRET", "secreto-eventos")
    monkeypatch.setattr(settings, "WOMPI_INTEGRITY_SECRET", "secreto-integridad")
    await db.run_sync(fabricas.plan, "individual", 45_000, 1)
    await db.run_sync(fabricas.plantillas_aprobadas)
    await db.commit()


async def _pagar(db, solicitud_id: str, centavos: int = 4_500_000) -> None:
    solicitud = await db.get(SolicitudAfiliacion, UUID(solicitud_id))
    registro, _ = await db.run_sync(
        pasarela.registrar_evento, _evento(solicitud.referencia_pago, centavos)
    )
    assert await db.run_sync(pasarela.procesar_evento, registro.id) == "procesado"
    await db.commit()


async def test_ciclo_completo_sin_redigitar(
    client: AsyncClient, db, headers, catalogo_planes, almacenamiento
):
    inicio = await client.post("/api/v1/afiliaciones", json=FORMULARIO)
    assert inicio.status_code == 201, inicio.text
    datos = inicio.json()
    assert datos["valor"] == "45000.00"
    enlace = parse_qs(urlparse(datos["enlace_pago"]).query)
    assert enlace["amount-in-cents"] == ["4500000"]
    assert len(enlace["signature:integrity"][0]) == 64

    familia = await db.scalar(select(Familia).where(Familia.documento == "52111222"))
    assert familia.estado == "prospecto"

    await _pagar(db, datos["solicitud_id"])

    solicitud = await db.get(SolicitudAfiliacion, UUID(datos["solicitud_id"]))
    await db.refresh(solicitud)
    assert solicitud.estado == "completada", solicitud.error
    contrato = await db.get(Contrato, solicitud.contrato_id)
    assert contrato.medio_aceptacion == "formulario_web"
    assert contrato.evidencia_aceptacion["version_terminos"]
    assert len(contrato.evidencia_aceptacion["sha256_documento"]) == 64

    await db.refresh(familia)
    assert familia.estado == "activa"
    assert familia.usuario_portal_id is not None
    cuota = await db.scalar(select(Cuota).where(Cuota.contrato_id == contrato.id))
    assert cuota.estado == "pagada"
    preventivos = await db.scalar(
        select(func.count())
        .select_from(EventoPreventivo)
        .where(EventoPreventivo.mascota_id == familia.mascotas[0].id)
    )
    # Adulto sin fecha de nacimiento: un refuerzo por cada uno de los 4 esquemas caninos.
    assert preventivos == 4
    plantillas = set(
        await db.scalars(select(Mensaje.plantilla).where(Mensaje.familia_id == familia.id))
    )
    assert "bienvenida" in plantillas

    documento = await client.get(
        f"/api/v1/cartera/contratos/{contrato.id}/documento", headers=headers
    )
    assert documento.status_code == 200
    (pdf,) = [c for c, _ in almacenamiento.objetos.values()]
    assert pdf.startswith(b"%PDF-")


async def test_aprobacion_repetida_no_duplica(db, client, catalogo_planes):
    datos = (await client.post("/api/v1/afiliaciones", json=FORMULARIO)).json()
    await _pagar(db, datos["solicitud_id"])
    solicitud = await db.get(SolicitudAfiliacion, UUID(datos["solicitud_id"]))
    from app.modules.afiliaciones import service
    from app.modules.cartera.models import Pago

    pago = await db.get(Pago, solicitud.pago_id)
    await db.run_sync(service.completar, pago)
    assert await db.scalar(select(func.count()).select_from(Contrato)) == 1


async def test_exige_aceptacion(client: AsyncClient, catalogo_planes):
    resp = await client.post(
        "/api/v1/afiliaciones", json={**FORMULARIO, "acepta_condiciones": False}
    )
    assert resp.status_code == 422


async def test_familia_ya_afiliada_no_revela_su_estado(client: AsyncClient, db, catalogo_planes):
    datos = (await client.post("/api/v1/afiliaciones", json=FORMULARIO)).json()
    await _pagar(db, datos["solicitud_id"])
    otra = await client.post("/api/v1/afiliaciones", json=FORMULARIO)
    assert otra.status_code == 422
    assert "un asesor te contactara" in otra.json()["detail"]


async def test_asistida_con_pago_manual(client: AsyncClient, db, headers, catalogo_planes):
    familia = await db.run_sync(fabricas.familia, telefono="+573001234567")
    plan = await db.scalar(select(fabricas.Plan).where(fabricas.Plan.codigo == "individual"))
    await db.commit()
    inicio = await client.post(
        "/api/v1/afiliaciones/asistida",
        json={
            "familia_id": str(familia.id),
            "peludos": [{"mascota_id": str(familia.mascotas[0].id), "plan_id": str(plan.id)}],
            "medio_aceptacion": "presencial",
            "detalle_aceptacion": "Firma en sede Cali",
        },
        headers=headers,
    )
    assert inicio.status_code == 201, inicio.text
    resp = await client.post(
        f"/api/v1/afiliaciones/{inicio.json()['solicitud_id']}/pago-manual",
        json={"medio": "efectivo", "comprobante": "RC-0091"},
        headers=headers,
    )
    assert resp.json()["estado"] == "completada"
    assert resp.json()["aceptacion"]["medio"] == "presencial"


async def test_pago_que_no_completa_deja_tarea(client: AsyncClient, db, catalogo_planes):
    datos = (await client.post("/api/v1/afiliaciones", json=FORMULARIO)).json()
    plan = await db.scalar(select(fabricas.Plan).where(fabricas.Plan.codigo == "individual"))
    plan.activo = False  # el plan se desactivo entre el formulario y el pago
    await db.commit()
    await _pagar(db, datos["solicitud_id"])
    solicitud = await db.get(SolicitudAfiliacion, UUID(datos["solicitud_id"]))
    await db.refresh(solicitud)
    assert solicitud.estado == "error"
    assert await db.scalar(select(func.count()).select_from(Contrato)) == 0
    tarea = await db.scalar(select(Tarea).where(Tarea.origen == "afiliacion"))
    assert tarea.prioridad == "alta"
    assert isinstance(Decimal(1), Decimal)


async def test_pagar_un_enlace_reemplazado_no_afilia_con_condiciones_viejas(
    db, client, catalogo_planes
):
    """Revision F1: si la familia pide un segundo enlace (p. ej. cambio de plan) y paga el
    primero, no se afilia con el plan viejo: se deja una tarea para decidir."""
    primero = (await client.post("/api/v1/afiliaciones", json=FORMULARIO)).json()
    await client.post("/api/v1/afiliaciones", json=FORMULARIO)  # reemplaza al primero
    await _pagar(db, primero["solicitud_id"])
    assert await db.scalar(select(func.count()).select_from(Contrato)) == 0
    tarea = await db.scalar(select(Tarea).where(Tarea.origen == "afiliacion"))
    assert "reemplazada" in tarea.titulo


# --- 6.3 Cada peludo con su plan ---------------------------------------------------------------


async def test_asistida_con_un_plan_por_peludo_y_pago_trimestral_sin_descuento(
    client: AsyncClient, db, headers, catalogo_planes
):
    """Dos peludos en planes distintos pagan cada uno la tarifa de 2 de su plan, y con dos
    el trimestral es el mensual por tres. La solicitud guarda lo cotizado de cada uno y el
    contrato sale igual."""
    colita = await db.run_sync(fabricas.plan, "colita", tarifas=[35_500, 30_500, 26_000, 24_000])
    fiel = await db.run_sync(fabricas.plan, "fiel", tarifas=[69_000, 61_000, 57_500, 57_000])
    familia = await db.run_sync(fabricas.familia, mascotas=2, telefono="+573001234568")
    luna, max_ = familia.mascotas
    await db.commit()
    inicio = await client.post(
        "/api/v1/afiliaciones/asistida",
        json={
            "familia_id": str(familia.id),
            "peludos": [
                {"mascota_id": str(luna.id), "plan_id": str(colita.id)},
                {"mascota_id": str(max_.id), "plan_id": str(fiel.id)},
            ],
            "periodicidad": "trimestral",
            "medio_aceptacion": "presencial",
        },
        headers=headers,
    )
    assert inicio.status_code == 201, inicio.text
    assert Decimal(inicio.json()["valor"]) == Decimal("274500")  # (30.500 + 61.000) x 3
    solicitud = (
        await client.get(f"/api/v1/afiliaciones/{inicio.json()['solicitud_id']}", headers=headers)
    ).json()
    assert solicitud["periodicidad"] == "trimestral"
    assert [(p["nombre"], p["valor_mensual"]) for p in solicitud["peludos"]] == [
        (luna.nombre, "30500.00"),
        (max_.nombre, "61000.00"),
    ]

    pagada = await client.post(
        f"/api/v1/afiliaciones/{inicio.json()['solicitud_id']}/pago-manual",
        json={"medio": "efectivo", "comprobante": "RC-0092"},
        headers=headers,
    )
    assert pagada.json()["estado"] == "completada"
    contrato = await db.scalar(select(Contrato).where(Contrato.familia_id == familia.id))
    await db.refresh(contrato)
    assert (contrato.periodicidad, contrato.valor_periodo) == ("trimestral", Decimal("274500"))
    cuota = await db.scalar(select(Cuota).where(Cuota.contrato_id == contrato.id))
    assert (cuota.meses, cuota.estado) == (3, "pagada")


async def test_la_asistida_exige_el_plan_de_cada_peludo(
    client: AsyncClient, db, headers, catalogo_planes
):
    plan = await db.scalar(select(fabricas.Plan).where(fabricas.Plan.codigo == "individual"))
    familia = await db.run_sync(fabricas.familia, mascotas=2, telefono="+573001234569")
    primera, sin_plan = familia.mascotas[0].id, familia.mascotas[1].nombre
    await db.commit()
    resp = await client.post(
        "/api/v1/afiliaciones/asistida",
        json={
            "familia_id": str(familia.id),
            "peludos": [{"mascota_id": str(primera), "plan_id": str(plan.id)}],
            "medio_aceptacion": "presencial",
        },
        headers=headers,
    )
    assert resp.status_code == 422 and sin_plan in resp.text


async def test_si_la_tarifa_cambia_entre_la_cotizacion_y_el_pago_no_se_afilia(
    client: AsyncClient, db, catalogo_planes
):
    """Se cobra lo que la familia acepto y pago: con otro precio, el equipo decide."""
    datos = (await client.post("/api/v1/afiliaciones", json=FORMULARIO)).json()
    plan = await db.scalar(select(fabricas.Plan).where(fabricas.Plan.codigo == "individual"))
    await db.run_sync(
        lambda s: planes_service.reemplazar_tarifas(s, plan, [Decimal(50_000)] * 4, {})
    )
    await db.commit()
    await _pagar(db, datos["solicitud_id"])
    solicitud = await db.get(SolicitudAfiliacion, UUID(datos["solicitud_id"]))
    await db.refresh(solicitud)
    assert solicitud.estado == "error" and "valor cambio" in solicitud.error
    assert await db.scalar(select(func.count()).select_from(Contrato)) == 0
    tarea = await db.scalar(select(Tarea).where(Tarea.origen == "afiliacion"))
    assert tarea is not None

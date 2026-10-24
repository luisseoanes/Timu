"""F1-CAR-01..10 Cartera."""

import hashlib
from contextlib import nullcontext
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.core.config import settings
from app.core.tiempo import hoy
from app.integrations.payments import ErrorPasarela
from app.modules.cartera import pasarela, service
from app.modules.cartera.models import AvisoCartera, Cuota, EventoPasarela, IntentoCobro, Pago
from app.modules.cartera.periodos import dinero, sumar_meses
from app.modules.comunicaciones.models import Mensaje
from app.modules.familias.models import Familia
from app.modules.tareas.models import Tarea
from tests import fabricas


async def _cuotas(db, contrato) -> list[Cuota]:
    return list(
        await db.scalars(
            select(Cuota).where(Cuota.contrato_id == contrato.id).order_by(Cuota.fecha_vencimiento)
        )
    )


# --- F1-CAR-01 / 02 -------------------------------------------------------------------------


async def test_contrato_con_corte_renovacion_y_primera_cuota(db):
    inicio = date(2026, 1, 30)
    familia, contrato = await fabricas.afiliada(db, inicio)
    assert contrato.numero == "C2026-00001"
    assert contrato.dia_corte == 28  # un 30 no existe en febrero
    assert contrato.fecha_renovacion == date(2027, 1, 30)
    (primera,) = await _cuotas(db, contrato)
    assert (primera.periodo, primera.fecha_vencimiento) == ("2026-01", date(2026, 1, 28))
    assert familia.estado == "activa"


async def test_no_hay_dos_contratos_vigentes(db):
    familia, _ = await fabricas.afiliada(db, hoy())
    p = await db.run_sync(fabricas.plan, "otro")
    from app.core.errores import Conflicto

    with pytest.raises(Conflicto):
        await db.run_sync(service.crear_contrato, familia, p)


async def test_generacion_de_cuotas_es_idempotente(db):
    _, contrato = await fabricas.afiliada(db, date(2026, 1, 10))
    dia = date(2026, 4, 7)
    # Emite febrero, marzo y abril (abril vence el 10, dentro de la ventana de 5 dias).
    assert await db.run_sync(service.generar_cuotas, dia) == 3
    assert await db.run_sync(service.generar_cuotas, dia) == 0
    assert [c.periodo for c in await _cuotas(db, contrato)] == [
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
    ]


async def test_congelada_no_genera_cuotas(db):
    _, contrato = await fabricas.afiliada(db, date(2026, 1, 10))
    contrato.estado = "congelada"
    assert await db.run_sync(service.generar_cuotas, date(2026, 6, 1)) == 0


async def test_saldo_a_favor_se_descuenta_de_la_cuota(db):
    _, contrato = await fabricas.afiliada(db, date(2026, 1, 10))
    contrato.saldo_a_favor = Decimal("10000")
    await db.run_sync(service.generar_cuotas, date(2026, 2, 6))
    febrero = (await _cuotas(db, contrato))[1]
    assert (dinero(febrero.valor_pagado), febrero.estado) == (Decimal("10000.00"), "parcial")
    assert dinero(contrato.saldo_a_favor) == 0


# --- F1-CAR-03 / 05 Estados, congelamiento y reactivacion -----------------------------------


async def test_estados_por_dias_de_mora_y_reactivacion(db, tareas):
    await db.run_sync(fabricas.plantillas_aprobadas)
    inicio = hoy() - timedelta(days=40)
    familia, contrato = await fabricas.afiliada(db, inicio)
    vence = (await _cuotas(db, contrato))[0].fecha_vencimiento

    assert (
        await db.run_sync(service.reevaluar_estado, contrato, vence + timedelta(days=2))
        == "sin_cambio"
    )
    assert (
        await db.run_sync(service.reevaluar_estado, contrato, vence + timedelta(days=5))
        == "en_mora"
    )
    assert familia.estado == "en_mora"
    assert (
        await db.run_sync(service.reevaluar_estado, contrato, vence + timedelta(days=30))
        == "congelada"
    )
    assert familia.estado == "congelada"

    await db.run_sync(
        service.registrar_pago_manual,
        familia_id=familia.id,
        valor=Decimal(45000),
        medio="efectivo",
        referencia="REC-001",
        fecha_pago=None,
        cuota_id=None,
        notas=None,
        usuario_id=None,
    )
    assert contrato.estado == "activa"
    assert familia.estado == "activa"
    plantillas = set(
        await db.scalars(select(Mensaje.plantilla).where(Mensaje.familia_id == familia.id))
    )
    assert {"afiliacion_congelada", "afiliacion_reactivada"} <= plantillas


# --- F1-CAR-04 Avisos -----------------------------------------------------------------------


async def test_avisos_escalonados_sin_repetir(db):
    await db.run_sync(fabricas.plantillas_aprobadas)
    _, contrato = await fabricas.afiliada(db, date(2026, 1, 10))
    vence = date(2026, 1, 10)

    assert await db.run_sync(service.avisar_mora, contrato, vence + timedelta(days=1)) == "mora_1"
    assert await db.run_sync(service.avisar_mora, contrato, vence + timedelta(days=1)) is None
    # El proceso no corrio del dia 2 al 16: se envia solo el aviso mas avanzado.
    assert await db.run_sync(service.avisar_mora, contrato, vence + timedelta(days=16)) == "mora_15"
    avisos = {a.clave: a.omitido for a in await db.scalars(select(AvisoCartera))}
    assert avisos == {"mora_1": False, "mora_5": True, "mora_15": False}


async def test_sin_plantilla_el_aviso_se_reintenta(db):
    _, contrato = await fabricas.afiliada(db, date(2026, 1, 10))
    assert await db.run_sync(service.avisar_mora, contrato, date(2026, 1, 12)) is None
    assert await db.scalar(select(func.count()).select_from(AvisoCartera)) == 0


async def test_revision_diaria(db):
    await db.run_sync(fabricas.plantillas_aprobadas)
    await fabricas.afiliada(db, date(2026, 1, 10))
    await fabricas.afiliada(db, date(2026, 1, 10), telefono="+573109998877")
    resumen = await db.run_sync(service.revisar_cartera, date(2026, 1, 20))
    assert resumen.revisados == 2
    assert resumen.transiciones == {"en_mora": 2}
    assert resumen.avisos == 2


# --- F1-CAR-06 Pagos manuales ---------------------------------------------------------------


async def test_pago_se_aplica_de_la_cuota_mas_antigua_y_sobra_saldo(
    client: AsyncClient, db, headers
):
    familia, contrato = await fabricas.afiliada(db, date(2026, 1, 10))
    await db.run_sync(service.generar_cuotas, date(2026, 2, 6))
    await db.commit()
    resp = await client.post(
        "/api/v1/cartera/pagos",
        json={
            "familia_id": str(familia.id),
            "valor": "100000",
            "medio": "transferencia",
            "referencia": "TRF-778",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    enero, febrero = await _cuotas(db, contrato)
    await db.refresh(enero)
    await db.refresh(febrero)
    await db.refresh(contrato)
    assert (enero.estado, febrero.estado) == ("pagada", "pagada")
    assert dinero(contrato.saldo_a_favor) == Decimal("10000.00")

    duplicado = await client.post(
        "/api/v1/cartera/pagos",
        json={
            "familia_id": str(familia.id),
            "valor": "1",
            "medio": "efectivo",
            "referencia": "TRF-778",
        },
        headers=headers,
    )
    assert duplicado.status_code == 409


async def test_pago_a_cuota_de_otra_familia(client: AsyncClient, db, headers):
    _, contrato = await fabricas.afiliada(db, date(2026, 1, 10))
    otra = await db.run_sync(fabricas.familia, telefono="+573157778899")
    cuota = (await _cuotas(db, contrato))[0]
    await db.commit()
    resp = await client.post(
        "/api/v1/cartera/pagos",
        json={
            "familia_id": str(otra.id),
            "valor": "1000",
            "medio": "efectivo",
            "referencia": "X-1",
            "cuota_id": str(cuota.id),
        },
        headers=headers,
    )
    assert resp.status_code == 422


# --- F1-CAR-10 Estado de cuenta -------------------------------------------------------------


async def test_estado_de_cuenta(client: AsyncClient, db, headers):
    inicio = hoy() - timedelta(days=15)
    familia, contrato = await fabricas.afiliada(db, inicio)
    await db.commit()
    resp = await client.get(f"/api/v1/cartera/familias/{familia.id}/estado-cuenta", headers=headers)
    cuenta = resp.json()
    assert cuenta["saldo_vencido"] == "45000.00"
    assert cuenta["dias_mora"] == (hoy() - (await _cuotas(db, contrato))[0].fecha_vencimiento).days
    assert cuenta["proximo_cobro"]["fecha"] == str(
        sumar_meses(inicio, 1).replace(day=contrato.dia_corte)
    )
    assert len(cuenta["cuotas"]) == 1


# --- F1-CAR-07 Renovacion -------------------------------------------------------------------


async def test_renovacion_genera_una_tarea(db):
    _, contrato = await fabricas.afiliada(db, hoy() - timedelta(days=340))
    assert await db.run_sync(service.detectar_renovaciones) == 1
    assert await db.run_sync(service.detectar_renovaciones) == 0
    tarea = await db.scalar(select(Tarea))
    assert (tarea.area, tarea.contrato_id) == ("comercial", contrato.id)

    anterior = contrato.fecha_renovacion
    await db.run_sync(service.renovar, contrato)
    assert contrato.fecha_renovacion == sumar_meses(anterior, 12)


# --- F1-CAR-09 Webhook de la pasarela --------------------------------------------------------


def _evento(referencia: str, centavos: int, estado: str = "APPROVED", tx_id: str = "tx-1") -> dict:
    tx = {
        "id": tx_id,
        "reference": referencia,
        "status": estado,
        "amount_in_cents": centavos,
        "payment_method_type": "CARD",
    }
    props = ["transaction.id", "transaction.status", "transaction.amount_in_cents"]
    timestamp = 1790000000
    cadena = f"{tx_id}{estado}{centavos}{timestamp}{settings.WOMPI_EVENTS_SECRET}"
    return {
        "event": "transaction.updated",
        "data": {"transaction": tx},
        "signature": {"properties": props, "checksum": hashlib.sha256(cadena.encode()).hexdigest()},
        "timestamp": timestamp,
    }


@pytest.fixture
def secreto_wompi(monkeypatch):
    monkeypatch.setattr(settings, "WOMPI_EVENTS_SECRET", "secreto-eventos")


async def _pago_pendiente(db, familia, contrato, referencia="WEB-1", valor=45000) -> Pago:
    pago = Pago(
        familia_id=familia.id,
        contrato_id=contrato.id,
        referencia_externa=referencia,
        proveedor="wompi",
        valor=valor,
        estado="pendiente",
    )
    db.add(pago)
    await db.flush()
    return pago


async def test_webhook_idempotente_y_conciliacion(client: AsyncClient, db, secreto_wompi, tareas):
    familia, contrato = await fabricas.afiliada(db, date(2026, 1, 10))
    pago = await _pago_pendiente(db, familia, contrato)
    await db.commit()
    evento = _evento("WEB-1", 4_500_000)

    primero = await client.post("/api/v1/webhooks/pagos", json=evento)
    segundo = await client.post("/api/v1/webhooks/pagos", json=evento)
    assert (primero.json()["status"], segundo.json()["status"]) == ("encolado", "duplicado")
    assert await db.scalar(select(func.count()).select_from(EventoPasarela)) == 1
    (evento_id,) = await tareas.de(pasarela.TAREA_PROCESAR_EVENTO)

    from uuid import UUID

    assert await db.run_sync(pasarela.procesar_evento, UUID(evento_id[0])) == "procesado"
    await db.refresh(pago)
    assert (pago.estado, pago.aplicado) == ("aprobado", True)
    # Reprocesar no aplica el pago dos veces.
    await db.run_sync(pasarela.procesar_evento, UUID(evento_id[0]), forzar=True)
    cuota = (await _cuotas(db, contrato))[0]
    assert dinero(cuota.valor_pagado) == Decimal("45000.00")


async def test_webhook_con_firma_invalida(client: AsyncClient, secreto_wompi):
    evento = _evento("WEB-1", 100)
    evento["signature"]["checksum"] = "0" * 64
    assert (await client.post("/api/v1/webhooks/pagos", json=evento)).status_code == 401


async def test_monto_distinto_queda_en_error(db, secreto_wompi):
    familia, contrato = await fabricas.afiliada(db, date(2026, 1, 10))
    await _pago_pendiente(db, familia, contrato)
    registro, _ = await db.run_sync(pasarela.registrar_evento, _evento("WEB-1", 100))
    assert await db.run_sync(pasarela.procesar_evento, registro.id) == "error"
    assert "no coincide" in registro.error


class WompiFalso:
    def __init__(self, respuestas: list) -> None:
        self.respuestas = list(respuestas)
        self.cobros: list[dict] = []

    def cobrar_fuente(self, **kwargs):
        self.cobros.append(kwargs)
        r = self.respuestas.pop(0)
        if isinstance(r, Exception):
            raise r
        return {"id": f"tx-{len(self.cobros)}", "status": r}

    def consultar_transaccion(self, tx_id):
        return {
            "id": tx_id,
            "reference": "WEB-1",
            "status": "APPROVED",
            "amount_in_cents": 4_500_000,
        }

    def token_aceptacion(self):
        return "acc"

    def crear_fuente_pago(self, token, email, aceptacion):
        return "3891"


async def test_evento_perdido_se_recupera(db):
    familia, contrato = await fabricas.afiliada(db, date(2026, 1, 10))
    pago = await _pago_pendiente(db, familia, contrato)
    evento = await db.run_sync(pasarela.recuperar_transaccion, "tx-99", WompiFalso([]))
    assert evento.estado == "procesado"
    assert pago.estado == "aprobado"


# --- F1-CAR-08 Cobro recurrente -------------------------------------------------------------


async def _cobrar(db, dia, wompi) -> dict:
    """En el worker cada paso abre su transaccion (sesion_worker); en la prueba todos
    comparten la de la prueba, que se revierte al final."""
    return await db.run_sync(
        lambda s: pasarela.cobrar_recurrentes(lambda: nullcontext(s), dia, wompi)
    )


async def _con_tarjeta(db, familia) -> None:
    await db.run_sync(
        pasarela.registrar_medio,
        familia,
        token_tarjeta="tok",
        email="a@b.co",
        marca=None,
        ultimos4=None,
        cliente=WompiFalso([]),
    )


async def test_cobro_recurrente_con_reintentos(db):
    familia, contrato = await fabricas.afiliada(db, date(2026, 1, 10))
    await db.run_sync(
        pasarela.registrar_medio,
        familia,
        token_tarjeta="tok_test",
        email="a@b.co",
        marca="VISA",
        ultimos4="4242",
        cliente=WompiFalso([]),
    )
    wompi = WompiFalso(["DECLINED", ErrorPasarela("fondos", temporal=False), "APPROVED"])
    vence = date(2026, 1, 10)

    assert (await _cobrar(db, vence, wompi))["rechazados"] == 1
    # Dia 2: aun no toca el segundo intento (calendario 0, 3, 7).
    assert (await _cobrar(db, vence + timedelta(days=2), wompi))["intentados"] == 0
    assert (await _cobrar(db, vence + timedelta(days=3), wompi))["rechazados"] == 1
    assert (await _cobrar(db, vence + timedelta(days=7), wompi))["aprobados"] == 1
    assert wompi.cobros[0]["valor_centavos"] == 4_500_000
    cuota = (await _cuotas(db, contrato))[0]
    assert cuota.estado == "pagada"
    assert [
        i.estado for i in await db.scalars(select(IntentoCobro).order_by(IntentoCobro.numero))
    ] == ["rechazado", "rechazado", "aprobado"]


async def test_cobro_recurrente_agotado_crea_tarea(db):
    familia, _ = await fabricas.afiliada(db, date(2026, 1, 10))
    await db.run_sync(
        pasarela.registrar_medio,
        familia,
        token_tarjeta="tok",
        email="a@b.co",
        marca=None,
        ultimos4=None,
        cliente=WompiFalso([]),
    )
    wompi = WompiFalso(["DECLINED"] * 3)
    for dias in (0, 3, 7, 8):
        await _cobrar(db, date(2026, 1, 10) + timedelta(days=dias), wompi)
    tarea = await db.scalar(select(Tarea).where(Tarea.origen == "cobro_recurrente"))
    assert (tarea.area, tarea.prioridad) == ("cartera", "alta")


async def test_nueva_tarjeta_desactiva_la_anterior(db):
    from app.modules.cartera.models import MedioPagoRecurrente

    familia = await db.run_sync(fabricas.familia)
    for token in ("tok1", "tok2"):
        await db.run_sync(
            pasarela.registrar_medio,
            familia,
            token_tarjeta=token,
            email="a@b.co",
            marca=None,
            ultimos4=None,
            cliente=WompiFalso([]),
        )
    activos = await db.scalar(
        select(func.count())
        .select_from(MedioPagoRecurrente)
        .where(MedioPagoRecurrente.activo.is_(True))
    )
    assert activos == 1


async def test_familia_sin_contrato_no_recibe_pago(db):
    familia = await db.run_sync(fabricas.familia)
    from app.core.errores import ReglaNegocio

    with pytest.raises(ReglaNegocio):
        await db.run_sync(
            service.registrar_pago_manual,
            familia_id=familia.id,
            valor=Decimal(1),
            medio="efectivo",
            referencia="R",
            fecha_pago=None,
            cuota_id=None,
            notas=None,
            usuario_id=None,
        )
    assert isinstance(familia, Familia)


async def test_cobro_pendiente_lo_confirma_el_webhook(db):
    """Lo normal en Wompi: la transaccion nace PENDING y se aprueba por webhook. El pago
    ya esta registrado cuando el evento llega, asi que se concilia."""
    familia, contrato = await fabricas.afiliada(db, date(2026, 1, 10))
    await _con_tarjeta(db, familia)
    wompi = WompiFalso(["PENDING"])
    assert (await _cobrar(db, date(2026, 1, 10), wompi))["intentados"] == 1
    pago = await db.scalar(select(Pago).where(Pago.referencia_externa.like("REC-%")))
    assert (pago.estado, pago.id_transaccion) == ("pendiente", "tx-1")

    registro, _ = await db.run_sync(
        pasarela.registrar_evento, _evento(pago.referencia_externa, 4_500_000)
    )
    assert await db.run_sync(pasarela.procesar_evento, registro.id) == "procesado"
    assert pago.estado == "aprobado"
    assert (await _cuotas(db, contrato))[0].estado == "pagada"
    # Mientras habia un intento pendiente no se intento cobrar de nuevo.
    assert len(wompi.cobros) == 1


async def test_un_cobro_que_falla_no_detiene_a_los_demas(db):
    primera, _ = await fabricas.afiliada(db, date(2026, 1, 10))
    segunda, contrato2 = await fabricas.afiliada(db, date(2026, 1, 10), telefono="+573002223344")
    await _con_tarjeta(db, primera)
    await _con_tarjeta(db, segunda)
    wompi = WompiFalso([RuntimeError("se cayo la red a mitad"), "APPROVED"])
    resumen = await _cobrar(db, date(2026, 1, 10), wompi)
    assert (resumen["errores"], resumen["aprobados"]) == (1, 1)
    # El intento que fallo quedo registrado: no se vuelve a cobrar como si fuera nuevo.
    assert await db.scalar(select(func.count()).select_from(IntentoCobro)) == 2


async def test_conciliar_pendientes_consulta_la_pasarela(db, monkeypatch):
    familia, contrato = await fabricas.afiliada(db, date(2026, 1, 10))
    await _con_tarjeta(db, familia)
    await _cobrar(db, date(2026, 1, 10), WompiFalso(["PENDING"]))
    pago = await db.scalar(select(Pago).where(Pago.referencia_externa.like("REC-%")))

    class Consulta(WompiFalso):
        def consultar_transaccion(self, tx_id):
            return {
                "id": tx_id,
                "reference": pago.referencia_externa,
                "status": "APPROVED",
                "amount_in_cents": 4_500_000,
            }

    from datetime import timedelta as td

    resumen = await db.run_sync(pasarela.conciliar_pendientes, Consulta([]), td(seconds=-1))
    assert resumen["conciliados"] == 1
    assert pago.estado == "aprobado"


async def test_baja_de_familia_cancela_contrato_y_tarjeta(db):
    """Revision F1: dar de baja dejaba el contrato vigente y se seguia facturando."""
    from app.modules.cartera.models import MedioPagoRecurrente
    from app.modules.familias import service as familias

    familia, contrato = await fabricas.afiliada(db, date(2026, 1, 10))
    await _con_tarjeta(db, familia)
    await db.run_sync(familias.dar_de_baja, familia, "se fue del pais")
    assert contrato.estado == "cancelada"
    assert await db.run_sync(service.generar_cuotas, date(2026, 4, 8)) == 0
    medio = await db.scalar(select(MedioPagoRecurrente))
    assert medio.activo is False


async def test_un_contrato_con_error_no_frena_la_generacion(db, monkeypatch):
    _, roto = await fabricas.afiliada(db, date(2026, 1, 10))
    _, sano = await fabricas.afiliada(db, date(2026, 1, 10), telefono="+573002223344")
    real = service.planes.aplicar_cambios_programados

    def falla_para_uno(sesion, contrato, hasta):
        if contrato.id == roto.id:
            raise RuntimeError("dato corrupto")
        return real(sesion, contrato, hasta)

    monkeypatch.setattr(service.planes, "aplicar_cambios_programados", falla_para_uno)
    assert await db.run_sync(service.generar_cuotas, date(2026, 2, 8)) == 1
    assert len(await _cuotas(db, sano)) == 2

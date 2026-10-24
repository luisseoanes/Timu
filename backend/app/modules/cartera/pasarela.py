"""F1-CAR-08 Cobro recurrente y F1-CAR-09 conciliacion por webhook de la pasarela."""

import hashlib
import json
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import EstadoAfiliacion
from app.core.errores import NoEncontrado, ReglaNegocio
from app.core.eventos import EventoDominio
from app.core.outbox import publicar
from app.core.tiempo import ahora, hoy
from app.integrations.payments import ClienteWompi, ErrorPasarela
from app.modules.cartera import service as cartera
from app.modules.cartera.models import (
    Contrato,
    Cuota,
    EventoPasarela,
    IntentoCobro,
    MedioPagoRecurrente,
    Pago,
)
from app.modules.cartera.periodos import centavos, dinero
from app.modules.familias.models import Familia

logger = structlog.get_logger(__name__)

TAREA_PROCESAR_EVENTO = "cartera.procesar_evento_pasarela"
EVENTO_RECIBIDO = "pasarela.evento_recibido"

_ESTADOS_WOMPI = {
    "APPROVED": "aprobado",
    "DECLINED": "rechazado",
    "VOIDED": "reversado",
    "ERROR": "rechazado",
    "PENDING": "pendiente",
}

# Acciones al aprobarse un pago segun el prefijo de su referencia (p. ej. afiliacion).
AlAprobar = Callable[[Session, Pago], None]
_AL_APROBAR: dict[str, AlAprobar] = {}


def al_aprobar(prefijo: str) -> Callable[[AlAprobar], AlAprobar]:
    def registrar(fn: AlAprobar) -> AlAprobar:
        _AL_APROBAR[prefijo] = fn
        return fn

    return registrar


# --- F1-CAR-09 Eventos ------------------------------------------------------------------------


def _id_evento(evento: dict[str, Any]) -> str:
    checksum = (evento.get("signature") or {}).get("checksum")
    if checksum:
        return str(checksum)
    return hashlib.sha256(json.dumps(evento, sort_keys=True).encode()).hexdigest()


def registrar_evento(
    db: Session, evento: dict[str, Any], *, id_evento: str | None = None
) -> tuple[EventoPasarela, bool]:
    """Guarda el evento. Si ya llego antes devuelve el existente y `False`: un evento
    repetido no se vuelve a procesar."""
    clave = id_evento or _id_evento(evento)
    existente = db.scalar(select(EventoPasarela).where(EventoPasarela.id_evento == clave))
    if existente:
        return existente, False
    transaccion = (evento.get("data") or {}).get("transaction") or {}
    registro = EventoPasarela(
        id=uuid4(),
        proveedor="wompi",
        id_evento=clave,
        tipo=str(evento.get("event", "desconocido")),
        referencia=transaccion.get("reference"),
        payload=evento,
    )
    db.add(registro)
    db.flush()
    publicar(db, EventoDominio(EVENTO_RECIBIDO, {"evento_id": str(registro.id)}))
    return registro, True


def procesar_evento(db: Session, evento_id: UUID, *, forzar: bool = False) -> str:
    evento = db.get(EventoPasarela, evento_id, with_for_update=True)
    if evento is None:
        raise NoEncontrado("Evento no encontrado")
    if evento.estado == "procesado" and not forzar:
        return evento.estado
    evento.intentos += 1
    try:
        evento.estado = _aplicar_transaccion(db, evento.payload)
        evento.error = None
    except ReglaNegocio as e:
        evento.estado, evento.error = "error", e.mensaje
    evento.procesado_en = ahora()
    db.flush()
    return evento.estado


def _aplicar_transaccion(db: Session, evento: dict[str, Any]) -> str:
    if evento.get("event") != "transaction.updated":
        return "ignorado"
    tx = evento["data"]["transaction"]
    pago = db.scalar(select(Pago).where(Pago.referencia_externa == tx.get("reference")))
    if pago is None:
        raise ReglaNegocio(f"No hay un pago con referencia {tx.get('reference')}")
    nuevo = _ESTADOS_WOMPI.get(tx.get("status", ""), "pendiente")
    pago.id_transaccion = tx.get("id") or pago.id_transaccion
    pago.medio = tx.get("payment_method_type") or pago.medio
    pago.payload = json.dumps(tx)[:10_000]
    if pago.estado == "aprobado":
        return "procesado"  # un aprobado no retrocede por un evento tardio
    if nuevo == "aprobado" and int(tx.get("amount_in_cents", -1)) != centavos(pago.valor):
        raise ReglaNegocio(
            f"El monto aprobado ({tx.get('amount_in_cents')}) no coincide con el pago "
            f"({centavos(pago.valor)})"
        )
    pago.estado = nuevo
    intento = db.scalar(select(IntentoCobro).where(IntentoCobro.pago_id == pago.id))
    if intento:
        intento.estado = nuevo
    if nuevo == "aprobado":
        pago.fecha_pago = ahora()
        _al_aprobarse(db, pago)
    db.flush()
    return "procesado"


def _al_aprobarse(db: Session, pago: Pago) -> None:
    for prefijo, accion in _AL_APROBAR.items():
        if pago.referencia_externa.startswith(prefijo):
            accion(db, pago)
            return
    cartera.aplicar_pago(db, pago)


def recuperar_transaccion(
    db: Session, transaccion_id: str, cliente: ClienteWompi | None = None
) -> EventoPasarela:
    """Evento perdido: se consulta la transaccion a la pasarela y se procesa como si hubiera
    llegado por webhook."""
    cliente = cliente or ClienteWompi()
    try:
        tx = cliente.consultar_transaccion(transaccion_id)
    except ErrorPasarela as e:
        raise ReglaNegocio(f"No se pudo consultar la transaccion: {e}") from e
    evento = {"event": "transaction.updated", "data": {"transaction": tx}, "origen": "consulta"}
    registro, _ = registrar_evento(
        db, evento, id_evento=f"consulta:{transaccion_id}:{tx.get('status')}"
    )
    procesar_evento(db, registro.id, forzar=True)
    return registro


# --- F1-CAR-08 Cobro recurrente ---------------------------------------------------------------


def registrar_medio(
    db: Session,
    familia: Familia,
    *,
    token_tarjeta: str,
    email: str,
    marca: str | None,
    ultimos4: str | None,
    cliente: ClienteWompi | None = None,
) -> MedioPagoRecurrente:
    """La familia autoriza una vez: la pasarela guarda la tarjeta y aqui queda la fuente."""
    cliente = cliente or ClienteWompi()
    try:
        aceptacion = cliente.token_aceptacion()
        fuente = cliente.crear_fuente_pago(token_tarjeta, email, aceptacion)
    except ErrorPasarela as e:
        raise ReglaNegocio(f"La pasarela no autorizo la tarjeta: {e}") from e
    anteriores = db.scalars(
        select(MedioPagoRecurrente).where(
            MedioPagoRecurrente.familia_id == familia.id, MedioPagoRecurrente.activo.is_(True)
        )
    )
    for medio in anteriores:
        medio.activo = False
    medio = MedioPagoRecurrente(
        familia_id=familia.id,
        proveedor="wompi",
        fuente_id=fuente,
        marca=marca,
        ultimos4=ultimos4,
        email_titular=email,
        autorizado_en=ahora(),
    )
    db.add(medio)
    db.flush()
    return medio


Abrir = Callable[[], AbstractContextManager[Session]]
"""Abre una transaccion propia (en el worker, `sesion_worker`). El cobro recurrente usa
varias por cuota a proposito: ver `cobrar_recurrentes`."""


@dataclass(frozen=True)
class Cobro:
    medio_id: UUID
    cuota_id: UUID
    numero: int


def planear_cobros(db: Session, dia: date) -> tuple[list[Cobro], int]:
    """Cuotas vencidas de familias con tarjeta autorizada a las que les toca intento hoy.

    Cada cuota tiene tantos intentos como dias en COBRO_RECURRENTE_REINTENTOS_DIAS
    (contados desde el vencimiento); agotados, se crea una tarea de cartera.
    """
    from app.modules.tareas import service as tareas

    calendario = settings.COBRO_RECURRENTE_REINTENTOS_DIAS
    cobros: list[Cobro] = []
    agotados = 0
    medios = list(
        db.scalars(select(MedioPagoRecurrente).where(MedioPagoRecurrente.activo.is_(True)))
    )
    for medio in medios:
        contrato = db.scalar(
            select(Contrato).where(
                Contrato.familia_id == medio.familia_id,
                Contrato.estado != EstadoAfiliacion.CANCELADA,
            )
        )
        if contrato is None:
            continue
        for cuota in cartera.cuotas_abiertas(db, contrato.id):
            if cuota.fecha_vencimiento > dia:
                continue
            intentos = list(
                db.scalars(select(IntentoCobro).where(IntentoCobro.cuota_id == cuota.id))
            )
            if any(i.estado == "pendiente" for i in intentos):
                continue
            numero = len(intentos) + 1
            if numero > len(calendario):
                creada = tareas.crear(
                    db,
                    titulo="Cobro automatico rechazado: contactar a la familia",
                    area="cartera",
                    prioridad="alta",
                    vence_en_dias=1,
                    familia_id=contrato.familia_id,
                    contrato_id=contrato.id,
                    origen="cobro_recurrente",
                    clave=f"cobro_agotado:{cuota.id}",
                )
                agotados += creada is not None
                continue
            if (dia - cuota.fecha_vencimiento).days < calendario[numero - 1]:
                continue
            cobros.append(Cobro(medio.id, cuota.id, numero))
    return cobros, agotados


def preparar_intento(db: Session, cobro: Cobro) -> dict[str, Any]:
    """Registra el pago pendiente y el intento. Quien llama confirma esto ANTES de cobrar:
    asi el webhook de la pasarela siempre encuentra el pago, y un fallo posterior no borra
    el rastro de un cobro que ya ocurrio."""
    medio = db.get(MedioPagoRecurrente, cobro.medio_id)
    cuota = db.get(Cuota, cobro.cuota_id)
    assert medio is not None and cuota is not None
    contrato = db.get(Contrato, cuota.contrato_id)
    assert contrato is not None
    valor = dinero(cuota.valor) - dinero(cuota.valor_pagado)
    pago = Pago(
        id=uuid4(),
        familia_id=contrato.familia_id,
        contrato_id=contrato.id,
        cuota_id=cuota.id,
        referencia_externa=f"REC-{cuota.id.hex[:16]}-{cobro.numero}",
        proveedor="wompi",
        medio="CARD",
        valor=valor,
        estado="pendiente",
    )
    # Sin relationship, SQLAlchemy no ordena los insert por la llave foranea: el pago va primero.
    db.add(pago)
    db.flush()
    db.add(IntentoCobro(cuota_id=cuota.id, medio_id=medio.id, numero=cobro.numero, pago_id=pago.id))
    db.flush()
    return {
        "pago_id": pago.id,
        "referencia": pago.referencia_externa,
        "valor_centavos": centavos(valor),
        "email": medio.email_titular,
        "fuente_id": medio.fuente_id,
    }


def registrar_resultado(
    db: Session, pago_id: UUID, tx: dict[str, Any] | None, error: str | None = None
) -> str:
    """Anota lo que respondio la pasarela. Lo normal es PENDING: la confirmacion llega por
    webhook y la aplica `procesar_evento`."""
    pago = db.get(Pago, pago_id, with_for_update=True)
    assert pago is not None
    intento = db.scalar(select(IntentoCobro).where(IntentoCobro.pago_id == pago.id))
    assert intento is not None
    if pago.estado != "pendiente":
        return pago.estado  # el webhook llego primero y ya lo resolvio
    if tx is None:
        pago.estado = intento.estado = "rechazado"
        intento.error = error
        db.flush()
        return "rechazado"
    estado = _ESTADOS_WOMPI.get(tx.get("status", ""), "pendiente")
    pago.id_transaccion = tx.get("id")
    pago.estado = intento.estado = estado
    if estado == "aprobado":
        pago.fecha_pago = ahora()
        cartera.aplicar_pago(db, pago)
    db.flush()
    return estado


def cobrar_recurrentes(
    abrir: Abrir, dia: date | None = None, cliente: ClienteWompi | None = None
) -> dict[str, int]:
    """F1-CAR-08 Cobra las cuotas vencidas con tarjeta autorizada.

    Cada cobro usa transacciones propias y cortas, nunca una sola para todo el lote:
    1. se registra el intento y se confirma;
    2. se llama a la pasarela, fuera de cualquier transaccion;
    3. se anota el resultado.
    Un error en una familia no revierte los cobros de las demas, que ya ocurrieron en la
    pasarela, y el webhook que llegue mientras tanto encuentra el pago registrado.
    """
    dia = dia or hoy()
    cliente = cliente or ClienteWompi()
    conteo = {"intentados": 0, "aprobados": 0, "rechazados": 0, "agotados": 0, "errores": 0}
    with abrir() as db:
        cobros, conteo["agotados"] = planear_cobros(db, dia)
    for cobro in cobros:
        try:
            with abrir() as db:
                datos = preparar_intento(db, cobro)
            tx: dict[str, Any] | None = None
            error = None
            try:
                tx = cliente.cobrar_fuente(
                    referencia=datos["referencia"],
                    valor_centavos=datos["valor_centavos"],
                    email=datos["email"],
                    fuente_id=datos["fuente_id"],
                )
            except ErrorPasarela as e:
                error = str(e)
            with abrir() as db:
                resultado = registrar_resultado(db, datos["pago_id"], tx, error)
        except Exception:  # noqa: BLE001  una familia no detiene el cobro de las demas
            logger.exception("Cobro recurrente fallido para la cuota %s", cobro.cuota_id)
            conteo["errores"] += 1
            continue
        conteo["intentados"] += 1
        if resultado in ("aprobado", "rechazado"):
            conteo[f"{resultado}s"] += 1
    return conteo


def conciliar_pendientes(
    db: Session, cliente: ClienteWompi | None = None, antiguedad: timedelta = timedelta(hours=2)
) -> dict[str, int]:
    """Intentos que siguen pendientes mucho despues del cobro: el webhook no llego o fallo.

    Se consulta la transaccion a la pasarela; si ni siquiera se conoce su id (el proceso
    murio entre el cobro y el registro), se deja una tarea para revisarlo a mano.
    """
    from app.modules.tareas import service as tareas

    cliente = cliente or ClienteWompi()
    resumen = {"conciliados": 0, "sin_transaccion": 0, "errores": 0}
    limite = ahora() - antiguedad
    pendientes = db.scalars(
        select(Pago)
        .join(IntentoCobro, IntentoCobro.pago_id == Pago.id)
        .where(Pago.estado == "pendiente", Pago.created_at < limite)
    )
    for pago in list(pendientes):
        if not pago.id_transaccion:
            creada = tareas.crear(
                db,
                titulo=f"Cobro {pago.referencia_externa} sin confirmar: revisar en Wompi",
                area="cartera",
                prioridad="alta",
                vence_en_dias=1,
                familia_id=pago.familia_id,
                contrato_id=pago.contrato_id,
                origen="cobro_recurrente",
                clave=f"cobro_sin_transaccion:{pago.id}",
            )
            resumen["sin_transaccion"] += creada is not None
            continue
        try:
            with db.begin_nested():
                recuperar_transaccion(db, pago.id_transaccion, cliente)
            resumen["conciliados"] += 1
        except Exception:  # noqa: BLE001
            logger.exception("No se pudo conciliar el pago %s", pago.id)
            resumen["errores"] += 1
    return resumen

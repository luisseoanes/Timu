"""6.2 / 6.4 Automatizaciones de cartera. La logica vive en los servicios del modulo."""

from dataclasses import asdict
from typing import Any
from uuid import UUID

import structlog

# Registra la finalizacion de afiliaciones al aprobarse un pago con prefijo AFI-.
import app.modules.afiliaciones.service  # noqa: F401
from app.core.database import sesion_worker
from app.core.eventos import EventoDominio, al_ocurrir
from app.modules.cartera import pasarela, service
from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@al_ocurrir(pasarela.EVENTO_RECIBIDO)
def _al_recibir_evento(evento: EventoDominio) -> None:
    celery_app.send_task(pasarela.TAREA_PROCESAR_EVENTO, args=[evento.datos["evento_id"]])


@celery_app.task(name="cartera.generar_cuotas")
def generar_cuotas() -> dict[str, int]:
    """F1-CAR-02 Emision de cuotas del periodo. Repetible sin duplicar."""
    with sesion_worker() as db:
        return {"emitidas": service.generar_cuotas(db)}


@celery_app.task(name="cartera.revisar_mora")
def revisar_mora() -> dict[str, Any]:
    """F1-CAR-03 / 04 / 05 Estados de cartera, avisos, congelamiento y reactivacion."""
    with sesion_worker() as db:
        return asdict(service.revisar_cartera(db))


@celery_app.task(name="cartera.detectar_renovaciones")
def detectar_renovaciones() -> dict[str, int]:
    """F1-CAR-07 Tareas comerciales para contratos proximos a renovar."""
    with sesion_worker() as db:
        return {"tareas_creadas": service.detectar_renovaciones(db)}


@celery_app.task(name="cartera.cobrar_recurrentes")
def cobrar_recurrentes() -> dict[str, int]:
    """F1-CAR-08 Cobro automatico de cuotas vencidas con tarjeta autorizada. Abre una
    transaccion por paso de cada cobro (ver pasarela.cobrar_recurrentes)."""
    return pasarela.cobrar_recurrentes(sesion_worker)


@celery_app.task(name="cartera.conciliar_pendientes")
def conciliar_pendientes() -> dict[str, int]:
    """F1-CAR-09 Cobros que siguen pendientes porque el webhook no llego."""
    with sesion_worker() as db:
        return pasarela.conciliar_pendientes(db)


@celery_app.task(
    name=pasarela.TAREA_PROCESAR_EVENTO, autoretry_for=(OSError,), max_retries=5, retry_backoff=True
)
def procesar_evento_pasarela(evento_id: str) -> str:
    """F1-CAR-09 Conciliacion del evento guardado por el webhook."""
    with sesion_worker() as db:
        return pasarela.procesar_evento(db, UUID(evento_id))

"""6.18 / 6.19 Envio y procesamiento de mensajes. La logica vive en el servicio del modulo;
aqui solo se ejecuta y se reprograma."""

from datetime import timedelta
from typing import Any
from uuid import UUID

import structlog

from app.core.database import sesion_worker
from app.core.eventos import EventoDominio, al_ocurrir
from app.modules.comunicaciones import service
from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)

# Espera creciente entre intentos: 30 s, 2 min, 8 min, 32 min.
_ESPERAS = (30, 120, 480, 1920)
TAREA_WEBHOOK = "comunicaciones.procesar_evento_whatsapp"


@al_ocurrir(service.EVENTO_ENCOLADO)
def _al_encolar(evento: EventoDominio) -> None:
    celery_app.send_task(service.TAREA_ENVIO, args=[evento.datos["mensaje_id"]])


@al_ocurrir("whatsapp.webhook_recibido")
def _al_recibir_webhook(evento: EventoDominio) -> None:
    celery_app.send_task(TAREA_WEBHOOK, args=[evento.datos["payload"]])


@celery_app.task(name=service.TAREA_ENVIO, bind=True, max_retries=len(_ESPERAS))
def enviar_mensaje(self: Any, mensaje_id: str) -> str:
    with sesion_worker() as db:
        estado = service.procesar_envio(db, UUID(mensaje_id))
    if estado == "reintentar":
        espera = _ESPERAS[min(self.request.retries, len(_ESPERAS) - 1)]
        raise self.retry(countdown=espera)
    return estado


@celery_app.task(name=TAREA_WEBHOOK)
def procesar_evento_whatsapp(payload: dict[str, Any]) -> dict[str, int]:
    with sesion_worker() as db:
        return service.procesar_evento_whatsapp(db, payload)


@celery_app.task(name="comunicaciones.reencolar_pendientes")
def reencolar_pendientes() -> dict[str, int]:
    """Barrido: mensajes encolados cuya tarea se perdio (p. ej. un worker que murio a
    mitad del envio). La espera supera la del ultimo reintento para no duplicar."""
    with sesion_worker() as db:
        ids = service.pendientes_por_reencolar(db, timedelta(minutes=45))
    for mensaje_id in ids:
        celery_app.send_task(service.TAREA_ENVIO, args=[str(mensaje_id)])
    return {"reencolados": len(ids)}

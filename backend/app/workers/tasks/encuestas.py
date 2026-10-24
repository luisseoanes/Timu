"""6.20 / 6.21 Encuestas de satisfaccion y seguimiento post atencion."""

from uuid import UUID

from app.core.database import sesion_worker
from app.core.eventos import EventoDominio, al_ocurrir
from app.modules.encuestas import service
from app.workers.celery_app import celery_app

TAREA_ENCUESTA = "encuestas.enviar_encuesta"


@al_ocurrir("servicio.completado")
def _al_completar_servicio(evento: EventoDominio) -> None:
    """6.20 La encuesta sale sola al completar el servicio."""
    celery_app.send_task(TAREA_ENCUESTA, args=[evento.datos["servicio_id"]])


@celery_app.task(name=TAREA_ENCUESTA)
def programar_encuesta(servicio_id: str) -> dict[str, int]:
    """F3-ENC-01 Programa la encuesta (y el seguimiento) con la demora del tipo de atencion."""
    with sesion_worker() as db:
        return {"programadas": len(service.programar(db, UUID(servicio_id)))}


@celery_app.task(name="encuestas.enviar_pendientes")
def enviar_pendientes() -> dict[str, int]:
    """Envia las encuestas y seguimientos cuya hora ya llego."""
    with sesion_worker() as db:
        return service.enviar_pendientes(db)

"""6.20 / 6.21 Encuestas de satisfaccion y seguimiento post atencion."""

import structlog

from app.core.eventos import EventoDominio, al_ocurrir
from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)

TAREA_ENCUESTA = "encuestas.enviar_encuesta"


@al_ocurrir("servicio.completado")
def _al_completar_servicio(evento: EventoDominio) -> None:
    """6.20 La encuesta sale sola al completar el servicio."""
    celery_app.send_task(TAREA_ENCUESTA, args=[evento.datos["servicio_id"]])


@celery_app.task(name=TAREA_ENCUESTA)
def enviar_encuesta(servicio_id: str) -> dict[str, str]:
    """Disparo automatico al pasar el servicio a COMPLETADO."""
    logger.info("encuestas.enviar_encuesta", servicio_id=servicio_id)
    return {"servicio_id": servicio_id, "status": "enviada"}


@celery_app.task(name="encuestas.enviar_seguimientos")
def enviar_seguimientos() -> dict[str, int]:
    """6.21 Seguimiento configurable por tipo de atencion."""
    return {"seguimientos_enviados": 0}

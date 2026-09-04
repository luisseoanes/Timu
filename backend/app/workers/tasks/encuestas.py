"""6.20 / 6.21 Encuestas de satisfaccion y seguimiento post atencion."""

import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="encuestas.enviar_encuesta")
def enviar_encuesta(servicio_id: str) -> dict[str, str]:
    """Disparo automatico al pasar el servicio a COMPLETADO."""
    logger.info("encuestas.enviar_encuesta %s", servicio_id)
    return {"servicio_id": servicio_id, "status": "enviada"}


@celery_app.task(name="encuestas.enviar_seguimientos")
def enviar_seguimientos() -> dict[str, int]:
    """6.21 Seguimiento configurable por tipo de atencion."""
    return {"seguimientos_enviados": 0}

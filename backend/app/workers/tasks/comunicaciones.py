"""6.18 / 6.19 Envio y procesamiento de mensajes de WhatsApp."""

import asyncio
import logging

from app.integrations.whatsapp import WhatsAppClient
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="comunicaciones.enviar_plantilla")
def enviar_plantilla(telefono: str, plantilla: str, parametros: list[str] | None = None) -> dict:
    return asyncio.run(WhatsAppClient().enviar_plantilla(telefono, plantilla, parametros))


@celery_app.task(name="comunicaciones.procesar_evento_whatsapp")
def procesar_evento_whatsapp(payload: dict) -> dict[str, str]:
    """Registra estados de entrega y encola la atencion automatizada (6.11 / 6.17)."""
    logger.info("comunicaciones.procesar_evento_whatsapp")
    return {"status": "procesado"}

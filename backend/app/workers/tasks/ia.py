"""F4-IAA Consultas de IA en el worker: nunca dentro de un endpoint async."""

from uuid import UUID

import structlog

from app.core.database import sesion_worker
from app.core.eventos import EventoDominio, al_ocurrir
from app.modules.ia import service
from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)

TAREA_BORRADOR = "ia.borrador_veterinario"
TAREA_EVALUAR = "ia.evaluar_prompt"


@al_ocurrir("ia.borrador_solicitado")
def _al_pedir_borrador(evento: EventoDominio) -> None:
    celery_app.send_task(TAREA_BORRADOR, args=[evento.datos["solicitud_id"]])


@al_ocurrir("ia.evaluacion_solicitada")
def _al_pedir_evaluacion(evento: EventoDominio) -> None:
    celery_app.send_task(TAREA_EVALUAR, args=[evento.datos["prompt_id"]])


@celery_app.task(name=TAREA_BORRADOR)
def borrador_veterinario(solicitud_id: str) -> dict[str, object]:
    with sesion_worker() as db:
        try:
            return service.borrador_veterinario(db, UUID(solicitud_id))
        except service.IANoDisponible as e:
            # El profesional responde sin borrador; la consulta quedo registrada.
            logger.warning("Borrador no disponible para %s: %s", solicitud_id, e)
            return {"disponible": False}


@celery_app.task(name=TAREA_EVALUAR)
def evaluar_prompt(prompt_id: str) -> dict[str, object]:
    with sesion_worker() as db:
        return service.evaluar(db, service.obtener_prompt(db, UUID(prompt_id)))

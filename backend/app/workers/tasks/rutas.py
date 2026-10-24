"""F2-RUT-01..03 Planeacion de rutas en el worker: OR-Tools es CPU-bound."""

from uuid import UUID

import structlog

from app.core.database import sesion_worker
from app.core.eventos import EventoDominio, al_ocurrir
from app.modules.rutas import service
from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)

TAREA_PLANIFICAR = "rutas.planificar"


@al_ocurrir(service.EVENTO_PLANIFICACION)
def _al_solicitar(evento: EventoDominio) -> None:
    celery_app.send_task(TAREA_PLANIFICAR, args=[evento.datos["planificacion_id"]])


@celery_app.task(name=TAREA_PLANIFICAR)
def planificar(planificacion_id: str) -> dict[str, object]:
    try:
        with sesion_worker() as db:
            return dict(service.planificar(db, UUID(planificacion_id)).resultado)
    except Exception as exc:
        # La planificacion queda marcada como fallida (en otra transaccion: la primera se
        # revirtio) para que el panel no la muestre pendiente para siempre.
        logger.exception("Planificacion %s fallida", planificacion_id)
        with sesion_worker() as db:
            service.fallo_planificacion(db, UUID(planificacion_id), str(exc))
        raise

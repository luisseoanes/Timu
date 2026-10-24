"""F1-FAM-05 Geocodificacion en segundo plano: el guardado no espera al proveedor de mapas."""

from uuid import UUID

from app.core.database import sesion_worker
from app.core.eventos import EventoDominio, al_ocurrir
from app.modules.familias import service
from app.workers.celery_app import celery_app

TAREA_GEOCODIFICAR = "familias.geocodificar"


@al_ocurrir(service.EVENTO_UBICACION)
def _al_cambiar_ubicacion(evento: EventoDominio) -> None:
    celery_app.send_task(TAREA_GEOCODIFICAR, args=[evento.datos["familia_id"]])


@celery_app.task(name=TAREA_GEOCODIFICAR, autoretry_for=(OSError,), max_retries=3)
def geocodificar(familia_id: str) -> str | None:
    with sesion_worker() as db:
        return service.geocodificar(db, UUID(familia_id))

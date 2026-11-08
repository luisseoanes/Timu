"""F1-FAM-05 Geocodificacion en segundo plano: el guardado no espera al proveedor de mapas."""

from uuid import UUID

from app.core.database import sesion_worker
from app.core.eventos import EventoDominio, al_ocurrir
from app.integrations import storage
from app.modules.familias import service
from app.workers.celery_app import celery_app

TAREA_GEOCODIFICAR = "familias.geocodificar"
TAREA_PURGAR_ARCHIVOS = "familias.purgar_archivos"


@al_ocurrir(service.EVENTO_UBICACION)
def _al_cambiar_ubicacion(evento: EventoDominio) -> None:
    celery_app.send_task(TAREA_GEOCODIFICAR, args=[evento.datos["familia_id"]])


@celery_app.task(name=TAREA_GEOCODIFICAR, autoretry_for=(OSError,), max_retries=3)
def geocodificar(familia_id: str) -> str | None:
    with sesion_worker() as db:
        return service.geocodificar(db, UUID(familia_id))


@al_ocurrir(service.EVENTO_ANONIMIZADA)
def _al_anonimizar(evento: EventoDominio) -> None:
    celery_app.send_task(TAREA_PURGAR_ARCHIVOS, args=[evento.datos["claves"]])


@celery_app.task(name=TAREA_PURGAR_ARCHIVOS, autoretry_for=(OSError,), max_retries=5)
def purgar_archivos(claves: list[str]) -> int:
    """Borra del almacenamiento las fotos y los PDF de una familia anonimizada. Borrar un
    objeto que ya no existe no es un error, asi que se puede reintentar sin riesgo."""
    for clave in claves:
        storage.eliminar(clave)
    return len(claves)

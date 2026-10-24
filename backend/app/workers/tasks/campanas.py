"""F3-CAM-02 / 04 Campanas: lanzamiento de las programadas y despacho al ritmo permitido."""

from app.core.database import sesion_worker
from app.modules.campanas import service
from app.workers.celery_app import celery_app


@celery_app.task(name="campanas.lanzar_programadas")
def lanzar_programadas() -> dict[str, int]:
    with sesion_worker() as db:
        return {"lanzadas": service.lanzar_programadas(db)}


@celery_app.task(name="campanas.despachar")
def despachar() -> dict[str, int]:
    with sesion_worker() as db:
        return service.despachar(db)

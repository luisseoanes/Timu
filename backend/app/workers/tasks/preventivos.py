"""6.8 / 6.13 Agenda preventiva diaria. La logica vive en el servicio del modulo."""

from app.core.database import sesion_worker
from app.modules.preventivos import service
from app.workers.celery_app import celery_app


@celery_app.task(name="preventivos.generar_agenda")
def generar_agenda() -> dict[str, int]:
    """F2-PRE-04 Avisa a las familias de los preventivos que se acercan para agendarlos."""
    with sesion_worker() as db:
        return service.agenda_diaria(db)

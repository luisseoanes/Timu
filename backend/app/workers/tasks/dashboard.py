"""F4-DAS-03 Envio de reportes programados."""

from app.core.database import sesion_worker
from app.modules.dashboard import reportes
from app.workers.celery_app import celery_app


@celery_app.task(name="dashboard.enviar_reportes")
def enviar_reportes() -> dict[str, object]:
    with sesion_worker() as db:
        return reportes.enviar_programados(db)

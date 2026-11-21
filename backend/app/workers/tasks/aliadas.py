"""6.22 Clinicas aliadas: las remisiones que vencen sin usarse liberan el cupo del beneficio."""

from app.core.database import sesion_worker
from app.modules.aliadas import service
from app.workers.celery_app import celery_app


@celery_app.task(name="aliadas.vencer_remisiones")
def vencer_remisiones() -> dict[str, int]:
    """Pasado el plazo para reportar, la remision sin usar vence y su servicio se cancela."""
    with sesion_worker() as db:
        return {"vencidas": service.vencer_sin_uso(db)}

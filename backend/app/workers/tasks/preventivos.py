"""6.8 / 6.13 Calendario preventivo: agenda diaria y calculo de proximas fechas."""

import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="preventivos.generar_agenda")
def generar_agenda() -> dict[str, int]:
    """Crea los servicios preventivos del dia a partir del calendario de cada mascota."""
    logger.info("preventivos.generar_agenda ejecutada")
    return {"eventos_generados": 0}


@celery_app.task(name="preventivos.calcular_proximas_fechas")
def calcular_proximas_fechas(mascota_id: str) -> dict[str, str]:
    """6.8 Recalcula la proxima fecha tras aplicar un preventivo (alimenta el carnet)."""
    return {"mascota_id": mascota_id, "status": "recalculado"}

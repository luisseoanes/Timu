"""6.2 / 6.4 Automatizaciones de cartera: mora, congelamiento y renovacion anual."""

import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="cartera.revisar_mora")
def revisar_mora() -> dict[str, int]:
    """Marca cuotas vencidas, actualiza dias de mora y dispara alertas/congelamiento."""
    # TODO: consultar cuotas vencidas, actualizar estado y encolar notificaciones
    logger.info("cartera.revisar_mora ejecutada")
    return {"cuotas_revisadas": 0}


@celery_app.task(name="cartera.detectar_renovaciones")
def detectar_renovaciones() -> dict[str, int]:
    """6.4 Detecta contratos proximos a renovar y genera las tareas comerciales."""
    logger.info("cartera.detectar_renovaciones ejecutada")
    return {"contratos_detectados": 0}


@celery_app.task(name="cartera.conciliar_pago")
def conciliar_pago(payload: dict) -> dict[str, str]:
    """Concilia el evento de la pasarela contra la cuota y reactiva si corresponde."""
    logger.info("cartera.conciliar_pago: %s", payload.get("event"))
    return {"status": "procesado"}

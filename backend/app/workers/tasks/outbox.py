"""Drena la tabla de eventos salientes (ver app/core/outbox.py).

Corre en el worker, con sesion SINCRONA: Celery no es async y mezclar asyncio.run()
con sesiones async dentro de una tarea trae mas problemas que soluciones.
"""

from datetime import UTC, datetime

import structlog
from sqlalchemy import select

from app.core.database import sesion_worker
from app.core.eventos import EventoDominio, manejadores
from app.core.outbox import EventoSaliente
from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)

LOTE = 100
MAX_INTENTOS = 5


@celery_app.task(name="outbox.drenar")
def drenar() -> dict[str, int]:
    """Despacha los eventos pendientes y los marca como procesados.

    `with_for_update(skip_locked=True)` permite que varios workers drenen a la vez
    sin pisarse: cada uno se lleva las filas que el otro no bloqueo.
    """
    despachados = fallidos = 0
    with sesion_worker() as db:
        pendientes = db.scalars(
            select(EventoSaliente)
            .where(EventoSaliente.procesado_en.is_(None))
            .where(EventoSaliente.intentos < MAX_INTENTOS)
            .order_by(EventoSaliente.created_at)
            .limit(LOTE)
            .with_for_update(skip_locked=True)
        ).all()

        for fila in pendientes:
            evento = EventoDominio(nombre=fila.nombre, datos=fila.datos)
            try:
                for manejador in manejadores(fila.nombre):
                    manejador(evento)
                fila.procesado_en = datetime.now(UTC)
                despachados += 1
            except Exception as exc:  # noqa: BLE001  se reintenta hasta MAX_INTENTOS
                fila.intentos += 1
                fila.ultimo_error = str(exc)[:2000]
                fallidos += 1
                logger.warning("outbox.fallo", evento=fila.nombre, error=str(exc))

    return {"despachados": despachados, "fallidos": fallidos}

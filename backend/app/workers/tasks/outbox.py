"""Drena la tabla de eventos salientes (ver app/core/outbox.py).

Corre en el worker, con sesion SINCRONA: Celery no es async y mezclar asyncio.run()
con sesiones async dentro de una tarea trae mas problemas que soluciones. La logica
vive en `procesar_pendientes`, que recibe la sesion: asi la prueban las pruebas y la
usa el fixture `tareas`, en vez de una copia.
"""

from app.core.database import sesion_worker
from app.core.outbox import procesar_pendientes
from app.workers.celery_app import celery_app


@celery_app.task(name="outbox.drenar")
def drenar() -> dict[str, int]:
    """Despacha un lote de eventos pendientes y confirma el resultado."""
    with sesion_worker() as db:
        return procesar_pendientes(db)

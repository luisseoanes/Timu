"""6.1 Registro en linea: recordatorio y tarea para quien pago y no completo el formulario."""

from app.core.database import sesion_worker
from app.modules.afiliaciones import registro
from app.workers.celery_app import celery_app


@celery_app.task(name="afiliaciones.recordar_registros")
def recordar_registros() -> dict[str, int]:
    """A las 24 horas se reenvia el enlace del formulario; a las 48, tarea comercial."""
    with sesion_worker() as db:
        recordados, tareas = registro.recordar(db)
        return {"recordados": recordados, "tareas": tareas}

"""6.1 Registro en linea: recordatorio a quien pago y no completo el formulario, cierre de lo
que no se paga y borrado de su contacto pasado el plazo (Ley 1581)."""

from app.core.database import sesion_worker
from app.modules.afiliaciones import altas, registro
from app.workers.celery_app import celery_app


@celery_app.task(name="afiliaciones.recordar_registros")
def recordar_registros() -> dict[str, int]:
    """A las 24 horas se reenvia el enlace del formulario; a las 48, tarea comercial."""
    with sesion_worker() as db:
        recordados, tareas = registro.recordar(db)
        return {"recordados": recordados, "tareas": tareas}


@celery_app.task(name="afiliaciones.cerrar_registros_sin_pago")
def cerrar_registros_sin_pago() -> dict[str, int]:
    """A las 48 horas del ultimo enlace sin pago se cancela: el registro, con una tarea comercial,
    y el alta de un peludo desde el portal."""
    with sesion_worker() as db:
        canceladas, tareas = registro.cerrar_sin_pago(db)
        return {
            "canceladas": canceladas,
            "tareas": tareas,
            "altas_canceladas": altas.cerrar_sin_pago(db),
        }


@celery_app.task(name="afiliaciones.anonimizar_registros_abandonados")
def anonimizar_registros_abandonados() -> dict[str, int]:
    """Ley 1581: el contacto de un registro que nunca se pago se borra a los seis meses."""
    with sesion_worker() as db:
        return {"anonimizados": registro.anonimizar_abandonados(db)}

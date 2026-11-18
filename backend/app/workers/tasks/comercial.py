"""R3-PUB-04 Lo que sigue al formulario de contacto de la portada."""

from uuid import UUID

from app.core.database import sesion_worker
from app.core.eventos import EventoDominio, al_ocurrir
from app.modules.comercial import service
from app.workers.celery_app import celery_app

TAREA_CONTACTO_WEB = "comercial.tarea_contacto_web"


@al_ocurrir(service.EVENTO_CONTACTO_WEB)
def _al_escribir_desde_la_web(evento: EventoDominio) -> None:
    celery_app.send_task(
        TAREA_CONTACTO_WEB, args=[evento.datos["interesado_id"], evento.datos["fecha"]]
    )


@celery_app.task(name=TAREA_CONTACTO_WEB)
def tarea_contacto_web(interesado_id: str, fecha: str) -> None:
    with sesion_worker() as db:
        service.tarea_contacto_web(db, UUID(interesado_id), fecha)

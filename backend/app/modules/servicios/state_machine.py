"""6.10 Maquina de estados de los servicios.

Centraliza las transiciones validas para que rutas, portal y comunicaciones no
reimplementen la logica de estados.
"""

from typing import Any
from uuid import UUID

from app.core.enums import EstadoServicio as E
from app.core.eventos import EventoDominio
from app.core.outbox import publicar

TRANSICIONES: dict[E, set[E]] = {
    E.SOLICITADO: {E.AGENDADO, E.PENDIENTE_AUTORIZACION, E.CANCELADO},
    E.PENDIENTE_AUTORIZACION: {E.AGENDADO, E.CANCELADO},
    E.AGENDADO: {E.EN_RUTA, E.EN_ATENCION, E.REPROGRAMADO, E.CANCELADO},
    E.EN_RUTA: {E.EN_ATENCION, E.REPROGRAMADO, E.CANCELADO},
    E.EN_ATENCION: {E.COMPLETADO, E.CANCELADO},
    E.REPROGRAMADO: {E.AGENDADO, E.CANCELADO},
    E.COMPLETADO: set(),
    E.CANCELADO: set(),
}


class TransicionInvalida(ValueError):
    pass


def puede_transicionar(actual: E, destino: E) -> bool:
    return destino in TRANSICIONES[actual]


def transicionar(actual: E, destino: E) -> E:
    if not puede_transicionar(actual, destino):
        raise TransicionInvalida(f"Transicion no permitida: {actual} -> {destino}")
    return destino


def aplicar(db: Any, servicio: Any, destino: E, *, actor_id: UUID | None = None) -> EventoDominio:
    """Transiciona el servicio Y deja publicado el evento correspondiente.

    Es la unica forma admitida de cambiar el estado de un servicio: `transicionar`
    solo valida, y usarla suelta deja los disparadores de 6.10 sin ejecutar. El
    evento se escribe en el outbox dentro de esta misma transaccion.
    """
    anterior = servicio.estado
    servicio.estado = transicionar(anterior, destino)
    evento = EventoDominio(
        nombre=f"servicio.{destino.value}",
        datos={
            "servicio_id": str(servicio.id),
            "estado_anterior": anterior.value,
            "estado_nuevo": destino.value,
            "actor_id": str(actor_id) if actor_id else None,
        },
    )
    publicar(db, evento)
    return evento

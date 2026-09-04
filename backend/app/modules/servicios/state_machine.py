"""6.10 Maquina de estados de los servicios.

Centraliza las transiciones validas para que rutas, portal y comunicaciones no
reimplementen la logica de estados.
"""

from app.core.enums import EstadoServicio as E

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

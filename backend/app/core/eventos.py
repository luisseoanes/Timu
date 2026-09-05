"""Eventos de dominio.

6.10 pide una maquina de estados "con disparadores de tareas": completar un servicio
crea pendientes, notifica por WhatsApp y alimenta el carnet. Si cada router dispara
sus propios efectos, en seis meses nadie sabe que ocurre al cambiar un estado.

Aqui se declara el evento; en `outbox.py` se persiste dentro de la misma transaccion
que lo origina; en `app/workers/tasks/outbox.py` se despacha. Los modulos publican
eventos, nunca llaman a `.delay()` directamente.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EventoDominio:
    """Algo que ya ocurrio. El nombre va en pasado y en punto: `servicio.completado`."""

    nombre: str
    datos: dict[str, Any] = field(default_factory=dict)


# nombre de evento -> manejadores. Se registran al importar el modulo de cada dominio.
_MANEJADORES: dict[str, list[Callable[[EventoDominio], None]]] = {}


def al_ocurrir(nombre: str) -> Callable[[Callable[[EventoDominio], None]], Callable]:
    """Registra un manejador. Uso:

    @al_ocurrir("servicio.completado")
    def notificar(evento): ...
    """

    def decorador(fn: Callable[[EventoDominio], None]) -> Callable:
        _MANEJADORES.setdefault(nombre, []).append(fn)
        return fn

    return decorador


def manejadores(nombre: str) -> list[Callable[[EventoDominio], None]]:
    return _MANEJADORES.get(nombre, [])

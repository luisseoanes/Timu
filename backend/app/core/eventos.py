"""Eventos de dominio.

6.10 pide una maquina de estados "con disparadores de tareas": completar un servicio
crea pendientes, notifica por WhatsApp y alimenta el carnet. Si cada router dispara
sus propios efectos, en seis meses nadie sabe que ocurre al cambiar un estado.

Aqui se declara el evento; en `outbox.py` se persiste dentro de la misma transaccion
que lo origina; en `app/workers/tasks/outbox.py` se despacha. Los modulos publican
eventos, nunca llaman a `.delay()` directamente.

Cada dominio declara los eventos que publica con `declarar_evento` y usa la constante que
devuelve. Publicar o suscribirse a un nombre sin declarar falla en el acto: un error de
tipeo dejaba el evento procesado sin manejador y el efecto (un mensaje, un cobro) no
ocurria, sin que nada fallara. `eventos_declarados()` es el catalogo de lo que el sistema
emite, el punto de partida de cualquier integracion que quiera enterarse.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


class EventoNoDeclarado(LookupError):
    """Un evento que ningun dominio declaro: casi siempre, un nombre mal escrito."""


# Nombres que algun dominio publica. Se llenan al importar el modulo que los declara.
_DECLARADOS: set[str] = set()


def declarar_evento(nombre: str) -> str:
    """Declara un evento que el dominio publica y devuelve su nombre para usarlo como
    constante: `EVENTO_UBICACION = declarar_evento("familia.ubicacion_cambiada")`."""
    _DECLARADOS.add(nombre)
    return nombre


def eventos_declarados() -> frozenset[str]:
    return frozenset(_DECLARADOS)


def _exigir_declarado(nombre: str) -> None:
    if nombre not in _DECLARADOS:
        raise EventoNoDeclarado(f"Evento sin declarar: {nombre!r} (ver declarar_evento)")


@dataclass(frozen=True)
class EventoDominio:
    """Algo que ya ocurrio. El nombre va en pasado y en punto: `servicio.completado`."""

    nombre: str
    datos: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _exigir_declarado(self.nombre)


# nombre de evento -> manejadores. Se registran al importar el modulo de cada dominio.
_MANEJADORES: dict[str, list[Callable[[EventoDominio], None]]] = {}


def al_ocurrir(nombre: str) -> Callable[[Callable[[EventoDominio], None]], Callable]:
    """Registra un manejador. Uso:

    @al_ocurrir("servicio.completado")
    def notificar(evento): ...
    """

    _exigir_declarado(nombre)

    def decorador(fn: Callable[[EventoDominio], None]) -> Callable:
        _MANEJADORES.setdefault(nombre, []).append(fn)
        return fn

    return decorador


def manejadores(nombre: str) -> list[Callable[[EventoDominio], None]]:
    return _MANEJADORES.get(nombre, [])

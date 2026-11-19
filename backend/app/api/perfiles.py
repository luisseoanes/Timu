"""Seccion 12 Que perfiles admite cada ruta, leido de sus guardas (`require_roles`).

La usan la prueba de la matriz (tests/test_permisos.py) y los scripts de demostracion, que
hablan con la API como el perfil al que le toca cada ruta (docs/perfiles-y-permisos.md).
"""

from collections.abc import Callable, Iterator
from typing import Any

from fastapi import FastAPI
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute, iter_route_contexts

from app.api.deps import publico
from app.core.enums import Rol


def _llamables(dep: Dependant) -> Iterator[Callable[..., Any]]:
    for sub in dep.dependencies:
        if sub.call is not None:
            yield sub.call
        yield from _llamables(sub)


def rutas(app: FastAPI) -> dict[str, Any]:
    """clave -> ruta efectiva, con el prefijo y las dependencias de los routers que la
    incluyen. Desde FastAPI 0.137 `app.routes` no las lista: cada `include_router` queda
    como un unico elemento que se resuelve al atender, y recorrerlo dejaba fuera de esta
    guarda casi todos los endpoints sin que fallara nada."""
    return {
        f"{','.join(sorted(ruta.methods or ()))} {ruta.path}": ruta
        for ruta in iter_route_contexts(app.routes)
        if isinstance(ruta.original_route, APIRoute) and not (ruta.path or "").startswith("/__")
    }


def matriz(app: FastAPI) -> dict[str, frozenset[Rol] | str]:
    """ruta -> perfiles permitidos, o 'publico'. Una ruta puede combinar varios guards
    (p. ej. el del router y el del endpoint): aplica la interseccion."""
    resultado: dict[str, frozenset[Rol] | str] = {}
    for clave, ruta in rutas(app).items():
        llamables = list(_llamables(ruta.dependant))
        if publico in llamables:
            resultado[clave] = "publico"
            continue
        conjuntos = [c.roles for c in llamables if hasattr(c, "roles")]
        if conjuntos:
            resultado[clave] = frozenset.intersection(*conjuntos)
    return resultado

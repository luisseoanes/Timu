"""F1-AUT-02 Matriz de permisos: ningun endpoint queda abierto por omision."""

import re
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute, iter_route_contexts
from httpx import AsyncClient

from app.core.deps import publico
from app.core.enums import Rol
from app.main import app
from tests.conftest import crear_usuario, login


def _llamables(dep: Dependant) -> Iterator[Callable[..., Any]]:
    for sub in dep.dependencies:
        if sub.call is not None:
            yield sub.call
        yield from _llamables(sub)


def rutas() -> dict[str, Any]:
    """clave -> ruta efectiva, con el prefijo y las dependencias de los routers que la
    incluyen. Desde FastAPI 0.137 `app.routes` no las lista: cada `include_router` queda
    como un unico elemento que se resuelve al atender, y recorrerlo dejaba fuera de esta
    guarda casi todos los endpoints sin que fallara nada."""
    return {
        f"{','.join(sorted(ruta.methods))} {ruta.path}": ruta
        for ruta in iter_route_contexts(app.routes)
        if isinstance(ruta.original_route, APIRoute) and not ruta.path.startswith("/__")
    }


def matriz() -> dict[str, frozenset[Rol] | str]:
    """ruta -> perfiles permitidos, o 'publico'. Una ruta puede combinar varios guards
    (p. ej. el del router y el del endpoint): aplica la interseccion."""
    resultado: dict[str, frozenset[Rol] | str] = {}
    for clave, ruta in rutas().items():
        llamables = list(_llamables(ruta.dependant))
        if publico in llamables:
            resultado[clave] = "publico"
            continue
        conjuntos = [c.roles for c in llamables if hasattr(c, "roles")]
        if conjuntos:
            resultado[clave] = frozenset.intersection(*conjuntos)
    return resultado


def test_la_guarda_recorre_todas_las_rutas_de_la_api():
    """Si FastAPI vuelve a cambiar como guarda las rutas, esta guarda no puede quedarse
    mirando un subconjunto: todo lo que publica el OpenAPI tiene que estar en `rutas()`."""
    publicadas = {
        f"{metodo.upper()} {ruta}"
        for ruta, operaciones in app.openapi()["paths"].items()
        for metodo in operaciones
        if not ruta.startswith("/__")  # las que montan las propias pruebas
    }
    recorridas = {f"{metodo} {ruta.path}" for ruta in rutas().values() for metodo in ruta.methods}
    assert publicadas - recorridas == set()


def test_toda_ruta_declara_permisos():
    declaradas = matriz()
    sin_declarar = [clave for clave in rutas() if clave not in declaradas]
    assert not sin_declarar, f"Rutas sin permisos declarados: {sin_declarar}"


# Unico conjunto de rutas abiertas admitido. Agregar aqui exige una razon.
PUBLICAS_ESPERADAS = {
    "GET /health",
    "GET /health/live",
    "POST /api/v1/auth/login",
    "POST /api/v1/auth/refresh",
    "POST /api/v1/auth/recuperar",
    "POST /api/v1/auth/restablecer",
    "POST /api/v1/auth/codigo",  # F3-POR-07 ingreso del portal por WhatsApp
    "POST /api/v1/auth/codigo/verificacion",
    "POST /api/v1/formularios/familia",
    "POST /api/v1/afiliaciones",  # formulario publico de afiliacion
    "GET /api/v1/webhooks/whatsapp",
    "POST /api/v1/webhooks/whatsapp",  # autorizada por firma de Meta
    "POST /api/v1/webhooks/pagos",  # autorizada por firma de la pasarela
    "GET /api/v1/verificacion/carnets/{codigo}",  # F2-PRE-06 la valida un tercero
    "GET /api/v1/encuestas/respuesta/{token}",  # F3-ENC-02 autorizada por el token
    "POST /api/v1/encuestas/respuesta/{token}",
}


def test_rutas_publicas_son_exactamente_las_esperadas():
    publicas = {k for k, v in matriz().items() if v == "publico"}
    assert publicas == PUBLICAS_ESPERADAS


# Lecturas compartidas con el portal: las acota el alcance por fila (app/core/scope.py),
# que tiene su propia prueba en test_alcance.py.
LECTURAS_CON_ALCANCE = {"GET /api/v1/familias", "GET /api/v1/familias/{familia_id}"}


def test_ninguna_ruta_interna_admite_al_portal():
    """El rol familia solo entra a /portal, /auth, a los catalogos de lectura y a las
    lecturas acotadas por alcance."""
    permitidas_familia = ("/api/v1/portal", "/api/v1/auth", "/api/v1/catalogos")
    for clave, roles in matriz().items():
        if roles == "publico" or Rol.FAMILIA not in roles or clave in LECTURAS_CON_ALCANCE:
            continue
        ruta = clave.split(" ", 1)[1]
        assert ruta.startswith(permitidas_familia), f"{clave} admite al rol familia"


def _ejemplo(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "00000000-0000-0000-0000-000000000000", path)


PROTEGIDAS = sorted(k for k, v in matriz().items() if v != "publico")


@pytest.mark.parametrize("clave", PROTEGIDAS)
async def test_sin_token_responde_401(client: AsyncClient, clave: str):
    metodos, ruta = clave.split(" ", 1)
    metodo = metodos.split(",")[0]
    resp = await client.request(metodo, _ejemplo(ruta))
    assert resp.status_code == 401, f"{clave} respondio {resp.status_code}"


async def test_perfil_no_autorizado_recibe_403(client: AsyncClient, db):
    await crear_usuario(db, "medico@timu.co", Rol.MEDICO)
    headers = await login(client, "medico@timu.co")
    resp = await client.post(
        "/api/v1/auth/usuarios",
        json={"email": "x@timu.co", "nombre": "X", "password": "12345678"},
        headers=headers,
    )
    assert resp.status_code == 403
    assert resp.json()["codigo"] == "prohibido"

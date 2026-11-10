"""La transaccion de la peticion se confirma antes de responder.

Desde FastAPI 0.118 el codigo tras el `yield` de una dependencia corre, por defecto, despues
de enviar la respuesta. Con `get_db` asi, el cliente recibia el 200 antes del commit: una
peticion inmediata (el primer GET tras el login) no veia la sesion recien creada y daba 401,
y un commit fallido llegaba al cliente como exito.
"""

from typing import Any

import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DbSession

pytestmark = pytest.mark.unit


async def test_el_commit_ocurre_antes_de_enviar_la_respuesta(monkeypatch):
    orden: list[str] = []

    async def commit(self: AsyncSession) -> None:
        orden.append("commit")

    monkeypatch.setattr(AsyncSession, "commit", commit)
    app = FastAPI()

    @app.get("/x")
    async def ruta(db: DbSession) -> dict[str, bool]:
        return {"ok": True}

    async def recibir() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def enviar(mensaje: dict[str, Any]) -> None:
        orden.append(mensaje["type"])

    alcance = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/x",
        "raw_path": b"/x",
        "root_path": "",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 1),
        "server": ("test", 80),
    }
    await app(alcance, recibir, enviar)
    assert orden.index("commit") < orden.index("http.response.start"), orden

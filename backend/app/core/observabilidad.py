"""F0-08 Observabilidad: registro estructurado, identificador de peticion y errores.

Sin esto, depurar catorce dominios mas Celery es adivinar. El identificador de
peticion (F0-02) viaja en la cabecera X-Request-ID y aparece en cada linea de log,
para poder seguir una peticion de punta a punta.
"""

import logging
import uuid
from contextvars import ContextVar
from typing import Any

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

id_peticion: ContextVar[str] = ContextVar("id_peticion", default="-")


def _inyectar_id(_logger, _metodo, evento: dict) -> dict:
    evento["request_id"] = id_peticion.get()
    return evento


def configurar_logging(*, json: bool, debug: bool) -> None:
    procesadores: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _inyectar_id,
    ]
    procesadores.append(
        structlog.processors.JSONRenderer() if json else structlog.dev.ConsoleRenderer()
    )
    structlog.configure(
        processors=procesadores,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if debug else logging.INFO
        ),
        cache_logger_on_first_use=True,
    )


def configurar_sentry(dsn: str, entorno: str) -> None:
    """Solo se activa si hay DSN: en local no molesta y en produccion no se olvida."""
    if not dsn:
        return
    import sentry_sdk

    sentry_sdk.init(dsn=dsn, environment=entorno, traces_sample_rate=0.1)


class MiddlewareIdPeticion(BaseHTTPMiddleware):
    """Asigna (o respeta) el X-Request-ID y lo devuelve en la respuesta."""

    async def dispatch(self, request: Request, call_next):
        valor = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        token = id_peticion.set(valor)
        try:
            respuesta = await call_next(request)
            respuesta.headers["X-Request-ID"] = valor
            return respuesta
        finally:
            id_peticion.reset(token)

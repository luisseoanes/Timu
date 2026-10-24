"""F0-02 / F0-08 Observabilidad: registro estructurado, identificador de peticion y errores.

Sin esto, depurar catorce dominios mas Celery es adivinar. El identificador de
peticion viaja en la cabecera X-Request-ID y aparece en cada linea de log, para poder
seguir una peticion de punta a punta.

Los modulos registran con `structlog.get_logger(__name__)`. Lo que escriben las
librerias por `logging` (uvicorn, SQLAlchemy, Celery) pasa por los mismos
procesadores, asi que tambien lleva el identificador y sale en JSON cuando toca.
"""

import logging
import re
import time
import uuid
from contextvars import ContextVar
from typing import Any

import structlog
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

HEADER_REQUEST_ID = "X-Request-ID"

id_peticion: ContextVar[str] = ContextVar("id_peticion", default="-")

_REQUEST_ID_VALIDO = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


def _inyectar_id(_logger: Any, _metodo: str, evento: dict[str, Any]) -> dict[str, Any]:
    evento["request_id"] = id_peticion.get()
    return evento


def configurar_logging(*, json: bool, debug: bool) -> None:
    compartidos: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _inyectar_id,
    ]
    render: Any = structlog.processors.JSONRenderer() if json else structlog.dev.ConsoleRenderer()
    structlog.configure(
        processors=[
            *compartidos,
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if debug else logging.INFO
        ),
        cache_logger_on_first_use=True,
    )
    handler = logging.StreamHandler()
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=compartidos,
            processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, render],
        )
    )
    raiz = logging.getLogger()
    raiz.handlers = [handler]
    raiz.setLevel(logging.DEBUG if debug else logging.INFO)
    # El eco SQL se controla con DEBUG en el engine, no aqui.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def configurar_sentry(dsn: str, entorno: str, *, celery: bool = False) -> None:
    """Solo se activa si hay DSN: en local no molesta y en produccion no se olvida.

    Los workers tambien lo llaman: un error en una tarea programada (cobros, avisos de
    mora) es tan grave como uno en un endpoint y nadie lo esta mirando.
    """
    if not dsn:
        return
    import sentry_sdk

    integraciones: list[Any] = []
    if celery:
        from sentry_sdk.integrations.celery import CeleryIntegration

        integraciones.append(CeleryIntegration())
    sentry_sdk.init(
        dsn=dsn, environment=entorno, traces_sample_rate=0.1, integrations=integraciones
    )


class MiddlewareIdPeticion:
    """Asigna (o respeta, si es valido) el X-Request-ID, lo devuelve en la respuesta y
    registra cada peticion con su duracion.

    ASGI puro y no BaseHTTPMiddleware: este rompe el streaming y aisla las
    contextvars del resto de la cadena.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.logger = structlog.get_logger("app.http")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        entrante = dict(scope["headers"]).get(HEADER_REQUEST_ID.lower().encode(), b"").decode()
        rid = entrante if _REQUEST_ID_VALIDO.match(entrante) else uuid.uuid4().hex
        scope.setdefault("state", {})["request_id"] = rid
        token = id_peticion.set(rid)

        inicio = time.perf_counter()
        estado = 500

        async def send_con_id(message: Message) -> None:
            nonlocal estado
            if message["type"] == "http.response.start":
                estado = message["status"]
                headers = MutableHeaders(scope=message)
                if HEADER_REQUEST_ID not in headers:
                    headers.append(HEADER_REQUEST_ID, rid)
            await send(message)

        try:
            await self.app(scope, receive, send_con_id)
        finally:
            self.logger.info(
                "peticion",
                metodo=scope["method"],
                ruta=scope["path"],
                estado=estado,
                ms=round((time.perf_counter() - inicio) * 1000, 1),
            )
            id_peticion.reset(token)

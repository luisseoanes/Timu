"""Middlewares ASGI puros (sin BaseHTTPMiddleware, para no romper streaming ni contextvars).

- SecurityHeadersMiddleware (F0-06): encabezados de seguridad en toda respuesta.
- LimiteCargaMiddleware (F0-06): rechaza cuerpos por encima del tope configurado.
- RateLimitMiddleware (F0-06): limite por usuario autenticado o, si no hay, por IP;
  limite estricto por IP en login, renovacion y recuperacion de clave.
"""

from http.cookies import SimpleCookie

from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import settings
from app.core.observabilidad import HEADER_REQUEST_ID, id_peticion
from app.core.rate_limit import Contador, segundos_para_reinicio
from app.core.security import decode_access_token


def _error(scope: Scope, status_code: int, mensaje: str, codigo: str, **headers: str):
    rid = scope.get("state", {}).get("request_id", id_peticion.get())
    return JSONResponse(
        {"detail": mensaje, "codigo": codigo, "request_id": rid},
        status_code=status_code,
        headers={HEADER_REQUEST_ID: rid, **headers},
    )


# Swagger y ReDoc cargan scripts de CDN; el resto de la API no sirve HTML.
_RUTAS_DOCUMENTACION = ("/docs", "/redoc")


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp, *, hsts: bool) -> None:
        self.app = app
        self.hsts = hsts

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        es_docs = scope["path"].startswith(_RUTAS_DOCUMENTACION)

        async def send_con_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                h = MutableHeaders(scope=message)
                h.setdefault("X-Content-Type-Options", "nosniff")
                h.setdefault("X-Frame-Options", "DENY")
                h.setdefault("Referrer-Policy", "no-referrer")
                h.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
                h.setdefault("Cross-Origin-Opener-Policy", "same-origin")
                if not es_docs:
                    h.setdefault(
                        "Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'"
                    )
                if self.hsts:
                    h.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
            await send(message)

        await self.app(scope, receive, send_con_headers)


class _CargaExcedida(Exception):
    pass


class LimiteCargaMiddleware:
    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declarado = Headers(scope=scope).get("content-length")
        if declarado and declarado.isdigit() and int(declarado) > self.max_bytes:
            await self._rechazar(scope, receive, send)
            return

        # Cuerpos sin Content-Length (chunked): se cuentan al vuelo.
        recibidos = 0
        respuesta_iniciada = False

        async def receive_contado() -> Message:
            nonlocal recibidos
            message = await receive()
            if message["type"] == "http.request":
                recibidos += len(message.get("body", b""))
                if recibidos > self.max_bytes:
                    raise _CargaExcedida
            return message

        async def send_marcado(message: Message) -> None:
            nonlocal respuesta_iniciada
            if message["type"] == "http.response.start":
                respuesta_iniciada = True
            await send(message)

        try:
            await self.app(scope, receive_contado, send_marcado)
        except _CargaExcedida:
            if not respuesta_iniciada:
                await self._rechazar(scope, receive, send)

    async def _rechazar(self, scope: Scope, receive: Receive, send: Send) -> None:
        mb = self.max_bytes // (1024 * 1024)
        resp = _error(scope, 413, f"La carga supera el maximo de {mb} MB", "carga_demasiado_grande")
        await resp(scope, receive, send)


class RateLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        contador: Contador,
        por_minuto: int,
        login_por_minuto: int,
        rutas_sensibles: tuple[str, ...],
        exentas: tuple[str, ...] = ("/health",),
    ) -> None:
        self.app = app
        self.contador = contador
        self.por_minuto = por_minuto
        self.login_por_minuto = login_por_minuto
        self.rutas_sensibles = rutas_sensibles
        self.exentas = exentas

    def _identidad(self, scope: Scope) -> str:
        galletas = SimpleCookie(Headers(scope=scope).get("cookie", ""))
        token = galletas.get(settings.COOKIE_NAME)
        if token is not None:
            payload = decode_access_token(token.value)
            if payload and "sub" in payload:
                return f"u:{payload['sub']}"
        cliente = scope.get("client")
        return f"ip:{cliente[0] if cliente else 'desconocida'}"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] in self.exentas:
            await self.app(scope, receive, send)
            return

        if scope["path"] in self.rutas_sensibles:
            # Credenciales y enlaces: limite estricto por IP, compartido entre estas rutas.
            cliente = scope.get("client")
            clave, limite = f"auth:{cliente[0] if cliente else '-'}", self.login_por_minuto
        else:
            clave, limite = self._identidad(scope), self.por_minuto

        if await self.contador.incrementar(clave) > limite:
            resp = _error(
                scope,
                429,
                "Demasiadas peticiones; intente de nuevo en un momento",
                "demasiadas_peticiones",
                **{"Retry-After": str(segundos_para_reinicio())},
            )
            await resp(scope, receive, send)
            return
        await self.app(scope, receive, send)

"""F0-02 Formato unico de errores.

Toda respuesta de error tiene la forma:

    {"detail": "mensaje legible", "codigo": "no_encontrado", "request_id": "...",
     "errores": [{"campo": "body.email", "mensaje": "..."}]}   # errores solo en validacion

`detail` se conserva por compatibilidad con clientes que ya leen el formato de FastAPI.
Los servicios de dominio lanzan `ErrorDominio` (o sus subclases) en vez de HTTPException.
"""

from collections.abc import Mapping
from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.observabilidad import HEADER_REQUEST_ID, id_peticion

logger = structlog.get_logger(__name__)


_CODIGOS_HTTP = {
    400: "peticion_invalida",
    401: "no_autenticado",
    403: "prohibido",
    404: "no_encontrado",
    405: "metodo_no_permitido",
    409: "conflicto",
    413: "carga_demasiado_grande",
    422: "validacion",
    429: "demasiadas_peticiones",
}


class ErrorCampo(BaseModel):
    campo: str
    mensaje: str


class ErrorRespuesta(BaseModel):
    """Esquema documentado en OpenAPI para las respuestas de error."""

    detail: str
    codigo: str
    request_id: str
    errores: list[ErrorCampo] | None = None


class ErrorDominio(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    codigo = "peticion_invalida"

    def __init__(self, mensaje: str, *, codigo: str | None = None) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        if codigo:
            self.codigo = codigo


class NoEncontrado(ErrorDominio):
    status_code = status.HTTP_404_NOT_FOUND
    codigo = "no_encontrado"


class Conflicto(ErrorDominio):
    status_code = status.HTTP_409_CONFLICT
    codigo = "conflicto"


class ReglaNegocio(ErrorDominio):
    """Peticion bien formada que una regla de negocio rechaza (p. ej. cartera en mora)."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    codigo = "regla_negocio"


class Prohibido(ErrorDominio):
    status_code = status.HTTP_403_FORBIDDEN
    codigo = "prohibido"


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or id_peticion.get()


def _respuesta(
    request: Request,
    status_code: int,
    mensaje: str,
    codigo: str,
    errores: list[dict[str, str]] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    rid = _request_id(request)
    cuerpo: dict[str, Any] = {"detail": mensaje, "codigo": codigo, "request_id": rid}
    if errores is not None:
        cuerpo["errores"] = errores
    return JSONResponse(
        cuerpo, status_code=status_code, headers={**(headers or {}), HEADER_REQUEST_ID: rid}
    )


async def _error_dominio(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ErrorDominio)
    return _respuesta(request, exc.status_code, exc.mensaje, exc.codigo)


async def _http_exception(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    codigo = _CODIGOS_HTTP.get(exc.status_code, "error")
    mensaje = exc.detail if isinstance(exc.detail, str) else codigo
    return _respuesta(request, exc.status_code, mensaje, codigo, headers=exc.headers)


async def _validacion(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    errores = [
        {"campo": ".".join(str(p) for p in e["loc"]), "mensaje": e["msg"]} for e in exc.errors()
    ]
    return _respuesta(
        request, 422, "Los datos enviados no son validos", "validacion", errores=errores
    )


async def _integridad(request: Request, exc: Exception) -> JSONResponse:
    # Red de seguridad: los servicios deben validar antes; esto evita un 500 por carrera.
    logger.warning("Violacion de integridad en %s %s: %s", request.method, request.url.path, exc)
    return _respuesta(
        request, 409, "El registro ya existe o entra en conflicto con otro", "conflicto"
    )


async def _no_controlado(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return _respuesta(request, 500, "Error interno del servidor", "error_interno")


def registrar_manejadores(app: FastAPI) -> None:
    app.add_exception_handler(ErrorDominio, _error_dominio)
    app.add_exception_handler(StarletteHTTPException, _http_exception)
    app.add_exception_handler(RequestValidationError, _validacion)
    app.add_exception_handler(IntegrityError, _integridad)
    app.add_exception_handler(Exception, _no_controlado)


RESPUESTAS_ERROR: dict[int | str, dict[str, Any]] = {
    code: {"model": ErrorRespuesta} for code in (400, 401, 403, 404, 409, 422, 429)
}

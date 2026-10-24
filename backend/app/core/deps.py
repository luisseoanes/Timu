"""Dependencias comunes: sesion de base de datos, usuario actual, permisos y alcance.

Dos capas, y las dos hacen falta:

- `require_roles` responde a "que perfil puede llamar a este endpoint" (F1-AUT-02).
- `AlcanceActual` + `app.core.scope.restringir` responden a "que filas ve" (portal).

F1-AUT-02 Todo endpoint declara quien puede usarlo, de una de dos formas:

    @router.get("", dependencies=[Depends(require_roles(*INTERNOS))])   # o el usuario:
    async def f(usuario: Annotated[Usuario, Depends(require_roles(Rol.ADMIN))]): ...

    @router.post("/webhook", dependencies=[Depends(publico)])           # abierto a proposito

`tests/test_permisos.py` recorre todas las rutas y falla si alguna no declara ninguna:
ningun endpoint queda abierto por omision.
"""

from collections.abc import Callable, Coroutine
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auditoria import usuario_actual_ctx
from app.core.config import settings
from app.core.database import get_db
from app.core.enums import Rol
from app.core.scope import Alcance
from app.core.security import decode_access_token
from app.modules.auth.models import Sesion, Usuario

DbSession = Annotated[AsyncSession, Depends(get_db)]

# Perfiles del equipo de TIMU (todo menos el portal de familias).
INTERNOS = (Rol.ADMIN, Rol.COMERCIAL, Rol.OPERACIONES, Rol.MEDICO)
TODOS = (*INTERNOS, Rol.FAMILIA)

# El refresh token solo viaja a las rutas de sesion, no en cada peticion.
RUTA_COOKIE_RENOVACION = f"{settings.API_V1_PREFIX}/auth"

_ERROR_CREDENCIALES = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales invalidas"
)


def establecer_cookie_sesion(response: Response, token: str, renovacion: str | None = None) -> None:
    """Deja el JWT (y el refresh token, si se emite) en cookies httpOnly.

    httpOnly: JavaScript no la puede leer, asi que una XSS no se lleva la sesion.
    Es la razon de no usar localStorage, con historia clinica de por medio.
    SameSite=lax: el navegador no la envia en peticiones cross-site, lo que cubre
    el grueso del CSRF sin necesidad de un token aparte.
    """
    comunes: dict[str, Any] = {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "domain": settings.COOKIE_DOMAIN,
    }
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        **comunes,
    )
    if renovacion is not None:
        response.set_cookie(
            key=settings.COOKIE_REFRESH_NAME,
            value=renovacion,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            path=RUTA_COOKIE_RENOVACION,
            **comunes,
        )


def borrar_cookie_sesion(response: Response) -> None:
    response.delete_cookie(key=settings.COOKIE_NAME, path="/", domain=settings.COOKIE_DOMAIN)
    response.delete_cookie(
        key=settings.COOKIE_REFRESH_NAME,
        path=RUTA_COOKIE_RENOVACION,
        domain=settings.COOKIE_DOMAIN,
    )


async def _sesion_vigente(db: AsyncSession, payload: dict[str, Any]) -> bool:
    """F1-AUT-01 Cerrar sesion revoca el token de inmediato, aunque el JWT no haya vencido."""
    sid = payload.get("sid")
    if not sid:
        return False
    try:
        sesion = await db.get(Sesion, UUID(sid))
    except ValueError:
        return False
    return sesion is not None and sesion.revocada_en is None


async def get_current_user(request: Request, db: DbSession) -> Usuario:
    token = request.cookies.get(settings.COOKIE_NAME)
    if not token:
        raise _ERROR_CREDENCIALES
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload or payload.get("tipo", "acceso") != "acceso":
        raise _ERROR_CREDENCIALES
    if not await _sesion_vigente(db, payload):
        raise _ERROR_CREDENCIALES
    usuario = await db.get(Usuario, UUID(payload["sub"]))
    if usuario is None or not usuario.activo:
        raise _ERROR_CREDENCIALES
    request.state.sid = payload["sid"]
    usuario_actual_ctx.set(usuario.id)
    return usuario


CurrentUser = Annotated[Usuario, Depends(get_current_user)]

Guard = Callable[..., Coroutine[Any, Any, Usuario]]


def require_roles(*roles: Rol) -> Guard:
    """Guard por perfil. Uso: dependencies=[Depends(require_roles(Rol.ADMIN))]

    Responde a "quien puede llamar", no a "que filas ve": para eso esta
    app.core.scope.restringir, y las dos capas son necesarias. Marca la funcion para
    la prueba de la matriz de permisos.
    """

    async def _guard(usuario: CurrentUser) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Permisos insuficientes")
        return usuario

    _guard.roles = frozenset(roles)  # type: ignore[attr-defined]
    return _guard


# Alias corto, usado por los modulos de la fase 1.
requiere = require_roles


async def publico() -> None:
    """Marca explicita de endpoint abierto (webhooks, login, formularios publicos)."""


Interno = Annotated[Usuario, Depends(require_roles(*INTERNOS))]
Admin = Annotated[Usuario, Depends(require_roles(Rol.ADMIN))]


async def get_alcance(usuario: CurrentUser, db: DbSession) -> Alcance:
    """Resuelve que puede ver el sujeto de la peticion.

    Para el personal interno basta el rol. Para el portal hay que averiguar de que
    familia se trata, y si el usuario tiene rol familia pero ninguna familia activa lo
    reclama, no ve nada: se resuelve a familia_id None y `restringir` lo rechaza.
    """
    familia_id: UUID | None = None
    if usuario.rol == Rol.FAMILIA:
        from app.modules.familias.models import Familia

        familia_id = await db.scalar(
            select(Familia.id).where(
                Familia.usuario_portal_id == usuario.id, Familia.dada_de_baja_en.is_(None)
            )
        )
    return Alcance(usuario_id=usuario.id, rol=usuario.rol, familia_id=familia_id)


AlcanceActual = Annotated[Alcance, Depends(get_alcance)]


async def _familia_actual(
    db: DbSession,
    _: Annotated[Usuario, Depends(require_roles(Rol.FAMILIA))],
    alcance: AlcanceActual,
) -> Any:
    """F1-AUT-04 Familia del usuario de portal. Todo endpoint del portal parte de aqui, asi
    que una familia nunca puede pedir datos de otra."""
    from app.core.errores import NoEncontrado
    from app.modules.familias.models import Familia

    familia = await db.get(Familia, alcance.familia_id) if alcance.familia_id else None
    if familia is None:
        raise NoEncontrado("La cuenta no esta vinculada a una familia activa")
    return familia


FamiliaActual = Annotated[Any, Depends(_familia_actual)]

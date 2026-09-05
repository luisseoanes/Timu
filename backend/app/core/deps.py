from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.enums import Rol
from app.core.scope import Alcance
from app.core.security import decode_access_token
from app.modules.auth.models import Usuario

DbSession = Annotated[AsyncSession, Depends(get_db)]

_ERROR_CREDENCIALES = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales invalidas"
)


def establecer_cookie_sesion(response: Response, token: str) -> None:
    """Deja el JWT en una cookie httpOnly.

    httpOnly: JavaScript no la puede leer, asi que una XSS no se lleva la sesion.
    Es la razon de no usar localStorage, con historia clinica de por medio.
    SameSite=lax: el navegador no la envia en peticiones cross-site, lo que cubre
    el grueso del CSRF sin necesidad de un token aparte.
    """
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


def borrar_cookie_sesion(response: Response) -> None:
    response.delete_cookie(key=settings.COOKIE_NAME, path="/", domain=settings.COOKIE_DOMAIN)


async def get_current_user(request: Request, db: DbSession) -> Usuario:
    token = request.cookies.get(settings.COOKIE_NAME)
    if not token:
        raise _ERROR_CREDENCIALES
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise _ERROR_CREDENCIALES
    usuario = await db.get(Usuario, UUID(payload["sub"]))
    if usuario is None or not usuario.activo:
        raise _ERROR_CREDENCIALES
    return usuario


CurrentUser = Annotated[Usuario, Depends(get_current_user)]


async def get_alcance(usuario: CurrentUser, db: DbSession) -> Alcance:
    """Resuelve que puede ver el sujeto de la peticion.

    Para el personal interno basta el rol. Para el portal hay que averiguar de que
    familia se trata, y si el usuario tiene rol familia pero ninguna familia lo
    reclama, no ve nada: se resuelve a familia_id None y `restringir` lo rechaza.
    """
    familia_id: UUID | None = None
    if usuario.rol == Rol.FAMILIA:
        from app.modules.familias.models import Familia

        familia_id = await db.scalar(
            select(Familia.id).where(Familia.usuario_portal_id == usuario.id)
        )
    return Alcance(usuario_id=usuario.id, rol=usuario.rol, familia_id=familia_id)


AlcanceActual = Annotated[Alcance, Depends(get_alcance)]


def require_roles(*roles: Rol):
    """Guard por perfil. Uso: dependencies=[Depends(require_roles(Rol.ADMIN))]

    Responde a "quien puede llamar", no a "que filas ve": para eso esta
    app.core.scope.restringir, y las dos capas son necesarias.
    """

    async def _guard(usuario: CurrentUser) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Permisos insuficientes")
        return usuario

    return _guard

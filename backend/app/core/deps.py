from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.enums import Rol
from app.core.security import decode_access_token
from app.modules.auth.models import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]
) -> Usuario:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_error
    user = await db.get(Usuario, UUID(payload["sub"]))
    if user is None or not user.activo:
        raise credentials_error
    return user


CurrentUser = Annotated[Usuario, Depends(get_current_user)]


def require_roles(*roles: Rol):
    """Guard de autorizacion por perfil. Uso: dependencies=[Depends(require_roles(Rol.ADMIN))]"""

    async def _guard(user: CurrentUser) -> Usuario:
        if user.rol not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Permisos insuficientes")
        return user

    return _guard

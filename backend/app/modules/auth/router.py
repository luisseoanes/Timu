from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import (
    CurrentUser,
    DbSession,
    borrar_cookie_sesion,
    establecer_cookie_sesion,
    require_roles,
)
from app.core.enums import Rol
from app.core.security import create_access_token
from app.modules.auth import service
from app.modules.auth.schemas import Sesion, UsuarioCreate, UsuarioRead
from app.schemas.common import Mensaje

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Sesion)
async def login(
    db: DbSession, response: Response, form: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Sesion:
    """El token se entrega en una cookie httpOnly, no en el cuerpo: el navegador no
    debe poder leerlo desde JavaScript."""
    usuario = await service.authenticate(db, form.username, form.password)
    if usuario is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email o contrasena incorrectos")
    establecer_cookie_sesion(response, create_access_token(str(usuario.id), {"rol": usuario.rol}))
    return Sesion(usuario=UsuarioRead.model_validate(usuario))


@router.post("/logout", response_model=Mensaje)
async def logout(response: Response) -> Mensaje:
    borrar_cookie_sesion(response)
    return Mensaje(detail="Sesion cerrada")


@router.post(
    "/usuarios",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(Rol.ADMIN))],
)
async def crear_usuario(db: DbSession, data: UsuarioCreate) -> UsuarioRead:
    if await service.get_by_email(db, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya esta registrado")
    usuario = await service.create_usuario(db, data)
    return UsuarioRead.model_validate(usuario)


@router.get("/me", response_model=UsuarioRead)
async def me(usuario: CurrentUser) -> UsuarioRead:
    return UsuarioRead.model_validate(usuario)

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import CurrentUser, DbSession, require_roles
from app.core.enums import Rol
from app.core.security import create_access_token
from app.modules.auth import service
from app.modules.auth.schemas import Token, UsuarioCreate, UsuarioRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(db: DbSession, form: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    usuario = await service.authenticate(db, form.username, form.password)
    if usuario is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email o contrasena incorrectos")
    token = create_access_token(str(usuario.id), {"rol": usuario.rol})
    return Token(access_token=token, usuario=UsuarioRead.model_validate(usuario))


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

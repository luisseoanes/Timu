from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import Rol


class UsuarioCreate(BaseModel):
    email: EmailStr
    nombre: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=8, max_length=128)
    rol: Rol = Rol.OPERACIONES


class UsuarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    nombre: str
    rol: Rol
    activo: bool


class Sesion(BaseModel):
    """Respuesta del login. No lleva el token: viaja en la cookie httpOnly."""

    usuario: UsuarioRead

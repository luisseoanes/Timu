from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.core.enums import Rol
from app.core.validaciones import TelefonoCO


class UsuarioCreate(BaseModel):
    email: EmailStr | None = None
    telefono: TelefonoCO | None = None
    nombre: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=8, max_length=128)
    rol: Rol = Rol.OPERACIONES

    @model_validator(mode="after")
    def _con_identificador(self) -> "UsuarioCreate":
        if not self.email and not self.telefono:
            raise ValueError("Se requiere email o telefono")
        return self


class UsuarioUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=160)
    rol: Rol | None = None
    activo: bool | None = None


class UsuarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr | None
    telefono: str | None
    nombre: str
    rol: Rol
    activo: bool


class Sesion(BaseModel):
    """Respuesta del login y de la renovacion. No lleva tokens: viajan en cookies httpOnly."""

    usuario: UsuarioRead


class RecuperarIn(BaseModel):
    identificador: str = Field(description="Email o telefono de la cuenta", max_length=255)


class RestablecerIn(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)

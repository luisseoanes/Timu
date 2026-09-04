from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import EstadoAfiliacion


class MascotaBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    especie: str = Field(max_length=40)
    raza: str | None = None
    sexo: str | None = None
    fecha_nacimiento: date | None = None
    peso_kg: float | None = None


class MascotaCreate(MascotaBase):
    pass


class MascotaRead(MascotaBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    familia_id: UUID


class FamiliaBase(BaseModel):
    titular_nombre: str = Field(min_length=2, max_length=160)
    documento: str = Field(max_length=32)
    email: EmailStr | None = None
    telefono: str = Field(max_length=32)
    ciudad: str = Field(max_length=80)
    direccion: str | None = None
    latitud: float | None = None
    longitud: float | None = None
    notas: str | None = None


class FamiliaCreate(FamiliaBase):
    mascotas: list[MascotaCreate] = []


class FamiliaUpdate(BaseModel):
    titular_nombre: str | None = None
    email: EmailStr | None = None
    telefono: str | None = None
    ciudad: str | None = None
    direccion: str | None = None
    latitud: float | None = None
    longitud: float | None = None
    estado: EstadoAfiliacion | None = None
    notas: str | None = None


class FamiliaRead(FamiliaBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    estado: EstadoAfiliacion
    mascotas: list[MascotaRead] = []

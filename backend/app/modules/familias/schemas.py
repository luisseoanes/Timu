from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.enums import EstadoAfiliacion
from app.core.tiempo import hoy
from app.core.validaciones import DocumentoCO, TelefonoCO, TipoDocumento

Sexo = Literal["macho", "hembra"]


class MascotaBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    especie: str = Field(max_length=40, description="Codigo del catalogo de especies")
    raza: str | None = Field(default=None, max_length=80)
    sexo: Sexo | None = None
    fecha_nacimiento: date | None = None
    peso_kg: float | None = Field(default=None, gt=0, lt=150)
    esterilizada: bool | None = None

    @field_validator("fecha_nacimiento")
    @classmethod
    def _no_futura(cls, v: date | None) -> date | None:
        if v and v > hoy():
            raise ValueError("La fecha de nacimiento no puede ser futura")
        return v


class MascotaCreate(MascotaBase):
    pass


class MascotaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    raza: str | None = Field(default=None, max_length=80)
    sexo: Sexo | None = None
    fecha_nacimiento: date | None = None
    peso_kg: float | None = Field(default=None, gt=0, lt=150)
    esterilizada: bool | None = None


class MascotaRead(MascotaBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    familia_id: UUID
    activa: bool
    motivo_baja: str | None = None
    foto_url: str | None = None


class FamiliaBase(BaseModel):
    titular_nombre: str = Field(min_length=2, max_length=160)
    tipo_documento: TipoDocumento = TipoDocumento.CC
    documento: DocumentoCO
    email: EmailStr | None = None
    telefono: TelefonoCO
    ciudad: str = Field(max_length=80, description="Nombre de una ciudad activa del catalogo")
    direccion: str | None = Field(default=None, max_length=255)
    notas: str | None = None


class FamiliaCreate(FamiliaBase):
    latitud: float | None = Field(default=None, ge=-5, le=14, description="Solo si es manual")
    longitud: float | None = Field(default=None, ge=-82, le=-66)
    mascotas: list[MascotaCreate] = []


class FamiliaUpdate(BaseModel):
    titular_nombre: str | None = Field(default=None, min_length=2, max_length=160)
    email: EmailStr | None = None
    telefono: TelefonoCO | None = None
    ciudad: str | None = Field(default=None, max_length=80)
    direccion: str | None = Field(default=None, max_length=255)
    latitud: float | None = Field(default=None, ge=-5, le=14)
    longitud: float | None = Field(default=None, ge=-82, le=-66)
    # Sin `estado`: el estado de afiliacion solo cambia por POST /estado (comercial o
    # admin) o lo deriva cartera. Aceptarlo aqui saltaba ese permiso.
    notas: str | None = None


class Baja(BaseModel):
    motivo: str = Field(min_length=3, max_length=255)


class FamiliaRead(FamiliaBase):
    model_config = ConfigDict(from_attributes=True)

    # Al leer no se revalida: un dato historico o migrado que no cumpla el formato de hoy
    # no puede tumbar el listado entero con un 500.
    documento: str  # type: ignore[assignment]
    telefono: str  # type: ignore[assignment]
    email: str | None = None  # type: ignore[assignment]
    id: UUID
    estado: EstadoAfiliacion
    latitud: float | None
    longitud: float | None
    geo_precision: str | None
    origen: str
    dada_de_baja_en: datetime | None
    motivo_baja: str | None
    usuario_portal_id: UUID | None
    mascotas: list[MascotaRead] = []


class CambioHistorial(BaseModel):
    fecha: datetime
    accion: str
    usuario_id: UUID | None
    cambios: dict[str, Any]


class FormularioFamilia(BaseModel):
    """F1-FAM-03 Formulario publico (afiliacion, landing, campana)."""

    titular_nombre: str = Field(min_length=2, max_length=160)
    tipo_documento: TipoDocumento = TipoDocumento.CC
    documento: DocumentoCO
    email: EmailStr | None = None
    telefono: TelefonoCO
    ciudad: str = Field(max_length=80)
    direccion: str | None = Field(default=None, max_length=255)
    mascotas: list[MascotaCreate] = Field(default_factory=list, max_length=10)
    origen: str = Field(default="formulario", max_length=32)
    # Campo trampa: los humanos no lo ven ni lo llenan; los bots si.
    sitio_web: str | None = Field(default=None, exclude=True)


class ResultadoFormulario(BaseModel):
    familia_id: UUID
    creada: bool
    campos_completados: list[str]
    mascotas_agregadas: list[str]

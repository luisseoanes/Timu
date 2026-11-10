from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.core.enums import EstadoAfiliacion
from app.core.tiempo import hoy
from app.core.validaciones import DocumentoCO, TelefonoCO, TipoDocumento

Sexo = Literal["macho", "hembra"]


def _fecha_no_futura(v: date | None) -> date | None:
    if v and v > hoy():
        raise ValueError("La fecha de nacimiento no puede ser futura")
    return v


class MascotaBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    especie: str = Field(max_length=40, description="Codigo del catalogo de especies")
    raza: str | None = Field(default=None, max_length=80)
    sexo: Sexo | None = None
    fecha_nacimiento: date | None = None
    peso_kg: float | None = Field(default=None, gt=0, lt=150)
    esterilizada: bool | None = None

    _no_futura = field_validator("fecha_nacimiento")(_fecha_no_futura)


class MascotaCreate(MascotaBase):
    pass


class MascotaAlta(MascotaCreate):
    """6.1 Alta de una mascota desde el panel: el peso y la fecha de nacimiento son
    obligatorios. Si no se conoce la fecha exacta, se pone una aproximada.

    La base los admite vacios a proposito: el registro en linea crea la mascota al pagar,
    con solo nombre y especie, y la familia los completa despues, y hay mascotas anteriores
    a esta regla sin ellos."""

    fecha_nacimiento: date  # type: ignore[assignment]
    peso_kg: float = Field(gt=0, lt=150)  # type: ignore[assignment]


class MascotaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    raza: str | None = Field(default=None, max_length=80)
    sexo: Sexo | None = None
    fecha_nacimiento: date | None = None
    peso_kg: float | None = Field(default=None, gt=0, lt=150)
    esterilizada: bool | None = None

    _no_futura = field_validator("fecha_nacimiento")(_fecha_no_futura)

    @model_validator(mode="after")
    def _sin_vaciar(self) -> "MascotaUpdate":
        vaciados = [
            c
            for c in ("nombre", "fecha_nacimiento", "peso_kg")
            if c in self.model_fields_set and getattr(self, c) is None
        ]
        if vaciados:
            raise ValueError(f"No se puede dejar vacio: {', '.join(vaciados)}")
        return self


class MascotaRead(MascotaBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    familia_id: UUID
    activa: bool
    motivo_baja: str | None = None
    foto_url: str | None = None


class ContactoIn(BaseModel):
    """Contacto adicional: solo consulta, sin acceso ni mensajes de la plataforma."""

    nombre: str = Field(min_length=2, max_length=160)
    telefono: TelefonoCO
    relacion: str | None = Field(default=None, max_length=60, description="Opcional: pareja, hijo…")
    email: EmailStr | None = None


class ContactoUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=160)
    telefono: TelefonoCO | None = None
    relacion: str | None = Field(default=None, max_length=60)
    email: EmailStr | None = None


class ContactoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    posicion: int
    nombre: str
    telefono: str
    relacion: str | None = None
    email: str | None = None


class FamiliaBase(BaseModel):
    titular_nombre: str = Field(min_length=2, max_length=160)
    tipo_documento: TipoDocumento = TipoDocumento.CC
    documento: DocumentoCO
    email: EmailStr | None = None
    telefono: TelefonoCO
    ciudad: str = Field(max_length=80, description="Nombre de una ciudad activa del catalogo")
    barrio: str = Field(min_length=2, max_length=120)
    direccion: str | None = Field(default=None, max_length=255)
    complemento: str | None = Field(
        default=None, max_length=255, description="Torre, apartamento o indicaciones"
    )
    notas: str | None = Field(default=None, description="Nota interna del equipo")


class FamiliaCreate(FamiliaBase):
    latitud: float | None = Field(default=None, ge=-5, le=14, description="Solo si es manual")
    longitud: float | None = Field(default=None, ge=-82, le=-66)
    mascotas: list[MascotaCreate] = []


class FamiliaAlta(FamiliaCreate):
    """Alta desde el panel: sus mascotas llegan con peso y fecha de nacimiento (`MascotaAlta`).
    El formulario publico crea la familia con `FamiliaCreate`, sin ellos."""

    mascotas: list[MascotaAlta] = []  # type: ignore[assignment]


class FamiliaUpdate(BaseModel):
    titular_nombre: str | None = Field(default=None, min_length=2, max_length=160)
    email: EmailStr | None = None
    telefono: TelefonoCO | None = None
    ciudad: str | None = Field(default=None, max_length=80)
    barrio: str | None = Field(default=None, min_length=2, max_length=120)
    direccion: str | None = Field(default=None, max_length=255)
    complemento: str | None = Field(default=None, max_length=255)
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
    barrio: str  # type: ignore[assignment]
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
    contactos: list[ContactoRead] = []


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
    barrio: str = Field(min_length=2, max_length=120)
    direccion: str | None = Field(default=None, max_length=255)
    complemento: str | None = Field(default=None, max_length=255)
    mascotas: list[MascotaCreate] = Field(default_factory=list, max_length=10)
    origen: str = Field(default="formulario", max_length=32)
    # Campo trampa: los humanos no lo ven ni lo llenan; los bots si.
    sitio_web: str | None = Field(default=None, exclude=True)


class ResultadoFormulario(BaseModel):
    familia_id: UUID
    creada: bool
    campos_completados: list[str]
    mascotas_agregadas: list[str]

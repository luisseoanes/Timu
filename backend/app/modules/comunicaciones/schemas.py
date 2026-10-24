from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.core.validaciones import TelefonoCO

EstadoAprobacion = Literal["borrador", "enviada", "aprobada", "rechazada", "pausada"]


class PlantillaCreate(BaseModel):
    nombre: str = Field(pattern=r"^[a-z0-9_]{1,120}$", description="Nombre exacto en Meta")
    idioma: str = "es"
    categoria: Literal["utility", "marketing", "authentication"] = "utility"
    cuerpo: str = Field(min_length=1, max_length=1024)
    variables: list[str] = Field(default_factory=list, description="Nombre de cada {{n}}")

    @model_validator(mode="after")
    def _variables_coinciden(self) -> "PlantillaCreate":
        import re

        usadas = {int(n) for n in re.findall(r"\{\{(\d+)\}\}", self.cuerpo)}
        if usadas != set(range(1, len(self.variables) + 1)):
            raise ValueError("El cuerpo debe usar {{1}}..{{n}}, una por cada variable declarada")
        return self


class PlantillaEstado(BaseModel):
    estado_aprobacion: EstadoAprobacion
    activa: bool | None = None


class PlantillaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    idioma: str
    version: int
    categoria: str
    cuerpo: str
    variables: list[str]
    estado_aprobacion: str
    activa: bool


class EnvioPlantilla(BaseModel):
    telefono: TelefonoCO
    plantilla: str
    variables: list[str] = Field(default_factory=list)
    familia_id: UUID | None = None


class EnvioTexto(BaseModel):
    telefono: TelefonoCO
    texto: str = Field(min_length=1, max_length=4096)
    familia_id: UUID | None = None


class MensajeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    familia_id: UUID | None
    canal: str
    direccion: str
    destino: str | None
    plantilla: str | None
    contenido: str | None
    estado: str
    intentos: int
    error: str | None
    masivo: bool
    enviado_en: datetime | None
    entregado_en: datetime | None
    leido_en: datetime | None
    created_at: datetime


class BajaCreate(BaseModel):
    telefono: TelefonoCO | None = None
    email: EmailStr | None = None
    motivo: str | None = None

    @model_validator(mode="after")
    def _un_destino(self) -> "BajaCreate":
        if bool(self.telefono) == bool(self.email):
            raise ValueError("Indique telefono o email, uno de los dos")
        return self


class BajaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    destino: str
    canal: str
    motivo: str | None
    created_at: datetime

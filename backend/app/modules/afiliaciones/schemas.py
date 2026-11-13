"""Lectura de la linea de la familia (R2-PAN-02): la comparten el panel y el portal."""

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import ColorPlan

TipoEstacion = Literal["cuota", "preventivo", "servicio"]
EstadoEstacion = Literal["hecha", "vencida", "proxima", "futura"]


class EstacionRead(BaseModel):
    """Una estacion de la linea de la familia: una cuota, un preventivo o un servicio."""

    model_config = ConfigDict(from_attributes=True)

    tipo: TipoEstacion
    referencia_id: UUID
    fecha: date
    estado: EstadoEstacion
    titulo: str
    mascota: str | None
    mascota_id: UUID | None


class PlanDeFamiliaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan_id: UUID
    nombre: str
    color: ColorPlan
    mascotas: list[str]


class LineaFamiliaRead(BaseModel):
    """La linea de la familia y sus planes vigentes: lo que el listado muestra en cada fila."""

    familia_id: UUID
    planes: list[PlanDeFamiliaRead]
    estaciones: list[EstacionRead]

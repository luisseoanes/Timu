"""Schemas de planes que usan otros dominios: el registro en linea muestra tarifas y cotiza
con el mismo formato que el panel."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import Periodicidad
from app.modules.planes.service import Cotizacion


class TarifaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    peludos: int
    valor: Decimal


class TarifaPeriodicidadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    periodicidad: Periodicidad
    valor: Decimal


class PeludoCotizadoRead(BaseModel):
    especie: str
    plan_id: UUID
    plan_nombre: str
    valor_mensual: Decimal


class CotizacionRead(BaseModel):
    """Lo que pagaria la afiliacion con cada periodicidad. `valor_periodo` es lo que cobra
    cada cuota; `ahorro`, lo que se ahorra frente a pagar el mensual por los mismos meses."""

    periodicidad: Periodicidad
    meses: int
    tarifa_de: int = Field(description="Peludos cuya tarifa se aplica (de 1 a 4)")
    peludos: list[PeludoCotizadoRead]
    valor_mensual: Decimal
    valor_periodo: Decimal
    descuento: bool
    ahorro: Decimal


def cotizacion_read(c: Cotizacion) -> CotizacionRead:
    return CotizacionRead(
        periodicidad=Periodicidad(c.periodicidad),
        meses=c.meses,
        tarifa_de=c.tarifa_de,
        peludos=[
            PeludoCotizadoRead(
                especie=p.especie,
                plan_id=p.plan.id,
                plan_nombre=p.plan.nombre,
                valor_mensual=p.valor_mensual,
            )
            for p in c.peludos
        ],
        valor_mensual=c.valor_mensual,
        valor_periodo=c.valor_periodo,
        descuento=c.descuento,
        ahorro=c.ahorro,
    )


class BeneficioPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tipo_servicio_codigo: str
    cupo: int | None
    periodo_cupo: str


class PlanPublico(BaseModel):
    """Lo que ve quien se afilia, o la familia que suma un peludo: precios, especies y
    beneficios, sin datos internos."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    codigo: str
    nombre: str
    descripcion: str | None
    especies: list[str]
    tarifas: list[TarifaRead]
    tarifas_periodicidad: list[TarifaPeriodicidadRead]
    beneficios: list[BeneficioPublico]

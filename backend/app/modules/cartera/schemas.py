from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ContratoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    numero: str
    familia_id: UUID
    plan_id: UUID
    fecha_inicio: date
    fecha_renovacion: date
    fecha_fin: date | None
    dia_corte: int
    valor_plan: Decimal
    mascotas_adicionales: int
    valor_adicional_mascota: Decimal
    valor_mensual: Decimal
    saldo_a_favor: Decimal
    estado: str
    aceptado_en: datetime | None
    medio_aceptacion: str | None


class CuotaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    periodo: str
    tipo: str
    fecha_vencimiento: date
    valor: Decimal
    valor_pagado: Decimal
    estado: str
    dias_mora: int
    descripcion: str | None


class PagoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    familia_id: UUID
    cuota_id: UUID | None
    referencia_externa: str
    proveedor: str
    medio: str | None
    valor: Decimal
    estado: str
    fecha_pago: datetime | None
    aplicado: bool


class PlanResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    codigo: str
    nombre: str


class ProximoCobro(BaseModel):
    fecha: date
    valor: Decimal


class EstadoCuenta(BaseModel):
    contrato: ContratoRead
    plan: PlanResumen
    estado: str
    saldo_pendiente: Decimal
    saldo_vencido: Decimal
    saldo_a_favor: Decimal
    dias_mora: int
    proximo_cobro: ProximoCobro | None
    cuotas: list[CuotaRead]
    pagos: list[PagoRead]


class ContratoCreate(BaseModel):
    familia_id: UUID
    plan_id: UUID
    fecha_inicio: date | None = None


class PagoManual(BaseModel):
    familia_id: UUID
    valor: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    medio: Literal["efectivo", "transferencia", "consignacion", "datafono", "otro"]
    referencia: str = Field(
        min_length=3, max_length=120, description="Comprobante o numero de operacion"
    )
    fecha_pago: datetime | None = None
    cuota_id: UUID | None = None
    notas: str | None = None


class Cancelacion(BaseModel):
    motivo: str = Field(min_length=3, max_length=255)


class MedioPagoCreate(BaseModel):
    """El token viene del widget de Wompi en el navegador: la tarjeta nunca pasa por aqui."""

    familia_id: UUID
    token_tarjeta: str = Field(min_length=5)
    email: str
    marca: str | None = Field(default=None, max_length=24)
    ultimos4: str | None = Field(default=None, pattern=r"^\d{4}$")


class MedioPagoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    familia_id: UUID
    proveedor: str
    marca: str | None
    ultimos4: str | None
    autorizado_en: datetime
    activo: bool


class EventoPasarelaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    proveedor: str
    tipo: str
    referencia: str | None
    estado: str
    intentos: int
    error: str | None
    procesado_en: datetime | None
    created_at: datetime

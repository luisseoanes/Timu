from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import Periodicidad


class ContratoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    numero: str
    familia_id: UUID
    fecha_inicio: date
    fecha_renovacion: date
    fecha_fin: date | None
    dia_corte: int
    periodicidad: Periodicidad
    valor_mensual: Decimal = Field(description="Lo que pagan al mes todos sus peludos")
    valor_periodo: Decimal = Field(description="Lo que cobra cada cuota")
    saldo_a_favor: Decimal
    estado: str
    aceptado_en: datetime | None
    medio_aceptacion: str | None


class ContratoListado(BaseModel):
    """Fila del listado de cartera: el contrato con lo que hace falta para gestionarlo."""

    id: UUID
    numero: str
    familia_id: UUID
    titular: str
    ciudad: str
    plan: str = Field(description="Los planes de sus peludos, separados por comas")
    estado: str
    periodicidad: Periodicidad
    valor_mensual: Decimal
    valor_periodo: Decimal
    saldo_vencido: Decimal
    dias_mora: int
    fecha_renovacion: date


class CuotaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    periodo: str
    tipo: str
    meses: int = Field(description="Meses que cubre desde el periodo")
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


class PeludoContratoRead(BaseModel):
    """Un peludo del contrato con su plan y lo que paga al mes."""

    mascota_id: UUID
    nombre: str
    especie: str
    plan_id: UUID
    plan_nombre: str
    valor_mensual: Decimal


class ProximoCobro(BaseModel):
    fecha: date
    valor: Decimal


class EstadoCuenta(BaseModel):
    contrato: ContratoRead
    mascotas: list[PeludoContratoRead]
    estado: str
    saldo_pendiente: Decimal
    saldo_vencido: Decimal
    saldo_a_favor: Decimal
    dias_mora: int
    proximo_cobro: ProximoCobro | None
    cuotas: list[CuotaRead]
    pagos: list[PagoRead]


class PlanDeMascota(BaseModel):
    mascota_id: UUID
    plan_id: UUID


class ContratoCreate(BaseModel):
    """Todos los peludos activos de la familia, cada uno con su plan."""

    familia_id: UUID
    peludos: list[PlanDeMascota] = Field(min_length=1)
    periodicidad: Periodicidad = Periodicidad.MENSUAL
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

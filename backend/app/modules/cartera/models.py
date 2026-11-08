from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum, nonmember
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, EnumDb, JSONTipo, TimestampMixin, UUIDMixin
from app.core.enums import (
    EstadoAfiliacion,
    EstadoEventoPasarela,
    EstadoPago,
    MedioAceptacion,
    ProveedorPago,
)


class EstadoCuota(StrEnum):
    PENDIENTE = "pendiente"
    PARCIAL = "parcial"
    PAGADA = "pagada"
    ANULADA = "anulada"
    ABIERTAS = nonmember((PENDIENTE, PARCIAL))


class Contrato(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.2 / 6.4 Contrato de afiliacion: base de cartera y de la renovacion anual."""

    __tablename__ = "contratos"
    __checks__ = {
        "dia_corte_rango": "dia_corte BETWEEN 1 AND 28",
        "valores_no_negativos": (
            "valor_mensual >= 0 AND valor_plan >= 0 AND valor_adicional_mascota >= 0"
            " AND saldo_a_favor >= 0 AND mascotas_adicionales >= 0"
        ),
        "renovacion_posterior": "fecha_renovacion > fecha_inicio",
        "fin_posterior": "fecha_fin IS NULL OR fecha_fin >= fecha_inicio",
    }
    __unicos__ = {
        "familia_vigente": (["familia_id"], "estado IN ('activa', 'en_mora', 'congelada')"),
    }
    __columna_familia__ = "familia_id"

    numero: Mapped[str] = mapped_column(String(20), unique=True)
    familia_id: Mapped[UUID] = mapped_column(ForeignKey("familias.id"), index=True)
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("planes.id"), index=True)
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_renovacion: Mapped[date] = mapped_column(Date, index=True)
    fecha_fin: Mapped[date | None] = mapped_column(Date)
    dia_corte: Mapped[int] = mapped_column(Integer, default=1)
    valor_plan: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    mascotas_adicionales: Mapped[int] = mapped_column(Integer, default=0)
    valor_adicional_mascota: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    valor_mensual: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    saldo_a_favor: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    estado: Mapped[EstadoAfiliacion] = mapped_column(
        EnumDb(EstadoAfiliacion), default=EstadoAfiliacion.ACTIVA, index=True
    )
    # F1-AFI-02 Aceptacion del contrato
    aceptado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    medio_aceptacion: Mapped[str | None] = mapped_column(EnumDb(MedioAceptacion))
    evidencia_aceptacion: Mapped[dict[str, Any]] = mapped_column(JSONTipo, default=dict)
    documento_archivo_id: Mapped[UUID | None] = mapped_column(ForeignKey("archivos.id"), index=True)


class Cuota(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.2 Cuota del periodo. Unica por contrato, periodo y tipo: generarla dos veces no duplica."""

    __tablename__ = "cuotas"
    __checks__ = {
        "valores_no_negativos": "valor >= 0 AND valor_pagado >= 0 AND dias_mora >= 0",
        "periodo_formato": "periodo ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'",
        "tipo_formato": "tipo ~ '^(mensual|ajuste[0-9]*)$'",
        "pagada_cubre": "estado <> 'pagada' OR valor_pagado >= valor",
        "parcial_entre": "estado <> 'parcial' OR (valor_pagado > 0 AND valor_pagado < valor)",
    }
    __table_args__ = (UniqueConstraint("contrato_id", "periodo", "tipo"),)

    contrato_id: Mapped[UUID] = mapped_column(ForeignKey("contratos.id"), index=True)
    periodo: Mapped[str] = mapped_column(String(7), index=True)  # YYYY-MM
    tipo: Mapped[str] = mapped_column(String(16), default="mensual")  # mensual | ajuste
    fecha_vencimiento: Mapped[date] = mapped_column(Date, index=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    valor_pagado: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    estado: Mapped[str] = mapped_column(
        EnumDb(EstadoCuota), default=EstadoCuota.PENDIENTE, index=True
    )
    dias_mora: Mapped[int] = mapped_column(Integer, default=0)
    descripcion: Mapped[str | None] = mapped_column(String(255))


class Pago(Base, UUIDMixin, TimestampMixin, Auditable):
    """Pago manual o de la pasarela. Se aplica a una o varias cuotas (AplicacionPago)."""

    __tablename__ = "pagos"
    __checks__ = {
        "valor_positivo": "valor > 0",
    }
    __columna_familia__ = "familia_id"

    familia_id: Mapped[UUID] = mapped_column(ForeignKey("familias.id"), index=True)
    contrato_id: Mapped[UUID | None] = mapped_column(ForeignKey("contratos.id"), index=True)
    cuota_id: Mapped[UUID | None] = mapped_column(ForeignKey("cuotas.id"), index=True)
    referencia_externa: Mapped[str] = mapped_column(String(120), unique=True)
    proveedor: Mapped[str] = mapped_column(EnumDb(ProveedorPago), default="manual")
    medio: Mapped[str | None] = mapped_column(String(32))
    id_transaccion: Mapped[str | None] = mapped_column(String(120), index=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    estado: Mapped[str] = mapped_column(EnumDb(EstadoPago), default="pendiente", index=True)
    fecha_pago: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    aplicado: Mapped[bool] = mapped_column(Boolean, default=False)
    registrado_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"), index=True)
    notas: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[str | None] = mapped_column(Text)


class AplicacionPago(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "aplicaciones_pago"
    __checks__ = {
        "valor_positivo": "valor > 0",
    }

    pago_id: Mapped[UUID] = mapped_column(ForeignKey("pagos.id", ondelete="CASCADE"), index=True)
    cuota_id: Mapped[UUID] = mapped_column(ForeignKey("cuotas.id"), index=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))


class AvisoCartera(Base, UUIDMixin, TimestampMixin):
    """F1-CAR-04 Traza de cada aviso de mora: un mismo aviso no se repite por cuota."""

    __tablename__ = "avisos_cartera"
    __table_args__ = (UniqueConstraint("cuota_id", "clave"),)

    cuota_id: Mapped[UUID] = mapped_column(ForeignKey("cuotas.id"), index=True)
    clave: Mapped[str] = mapped_column(String(40))
    regla_codigo: Mapped[str | None] = mapped_column(
        String(60), ForeignKey("reglas.codigo", onupdate="CASCADE"), index=True
    )
    mensaje_id: Mapped[UUID | None] = mapped_column(ForeignKey("mensajes.id"), index=True)
    omitido: Mapped[bool] = mapped_column(Boolean, default=False)


class EventoPasarela(Base, UUIDMixin, TimestampMixin):
    """F1-CAR-09 Evento de la pasarela, guardado antes de procesarlo: idempotente y
    reprocesable."""

    __tablename__ = "eventos_pasarela"
    __checks__ = {
        "intentos_no_negativos": "intentos >= 0",
    }

    proveedor: Mapped[str] = mapped_column(EnumDb(ProveedorPago))
    id_evento: Mapped[str] = mapped_column(String(128), unique=True)
    tipo: Mapped[str] = mapped_column(String(60))
    referencia: Mapped[str | None] = mapped_column(String(120), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONTipo)
    estado: Mapped[str] = mapped_column(
        EnumDb(EstadoEventoPasarela), default="recibido", index=True
    )
    intentos: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    procesado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MedioPagoRecurrente(Base, UUIDMixin, TimestampMixin, Auditable):
    """F1-CAR-08 Tarjeta tokenizada en la pasarela. Nunca se guardan datos de la tarjeta."""

    __tablename__ = "medios_pago_recurrente"
    __checks__ = {
        "ultimos4_formato": "ultimos4 IS NULL OR ultimos4 ~ '^[0-9]{4}$'",
    }
    __unicos__ = {
        "familia_activo": (["familia_id"], "activo"),
    }
    __columna_familia__ = "familia_id"

    familia_id: Mapped[UUID] = mapped_column(ForeignKey("familias.id"), index=True)
    proveedor: Mapped[str] = mapped_column(EnumDb(ProveedorPago), default="wompi")
    fuente_id: Mapped[str] = mapped_column(String(64))  # payment_source_id de la pasarela
    marca: Mapped[str | None] = mapped_column(String(24))
    ultimos4: Mapped[str | None] = mapped_column(String(4))
    email_titular: Mapped[str] = mapped_column(String(255))
    autorizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class IntentoCobro(Base, UUIDMixin, TimestampMixin):
    """F1-CAR-08 Cada intento de cobro automatico de una cuota."""

    __tablename__ = "intentos_cobro"
    __checks__ = {
        "numero_minimo": "numero >= 1",
    }
    __table_args__ = (UniqueConstraint("cuota_id", "numero"),)

    cuota_id: Mapped[UUID] = mapped_column(ForeignKey("cuotas.id"), index=True)
    medio_id: Mapped[UUID] = mapped_column(ForeignKey("medios_pago_recurrente.id"), index=True)
    numero: Mapped[int] = mapped_column(Integer)
    pago_id: Mapped[UUID | None] = mapped_column(ForeignKey("pagos.id"), index=True)
    estado: Mapped[str] = mapped_column(EnumDb(EstadoPago), default="pendiente")
    error: Mapped[str | None] = mapped_column(Text)

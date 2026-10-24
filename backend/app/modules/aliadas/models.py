from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, TimestampMixin, UUIDMixin


class ClinicaAliada(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.22 Clinica aliada: atiende lo que TIMU no hace en casa, con convenio por plan."""

    __tablename__ = "clinicas_aliadas"

    nombre: Mapped[str] = mapped_column(String(160))
    nit: Mapped[str | None] = mapped_column(String(20), unique=True)
    ciudad: Mapped[str] = mapped_column(String(80), index=True)
    direccion: Mapped[str | None] = mapped_column(String(255))
    telefono: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(255))
    servicios: Mapped[str | None] = mapped_column(Text)  # especialidades, horario
    activa: Mapped[bool] = mapped_column(Boolean, default=True)


class ConvenioAliada(Base, UUIDMixin, TimestampMixin, Auditable):
    """F2-ALI-01 Lo que la aliada cubre para un plan (o para todos, sin plan), con su
    tarifa y vigencia. La remision solo se emite contra un convenio vigente."""

    __tablename__ = "convenios_aliadas"

    clinica_id: Mapped[UUID] = mapped_column(ForeignKey("clinicas_aliadas.id"), index=True)
    plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("planes.id"), index=True)
    beneficio: Mapped[str] = mapped_column(String(160))  # "Consulta especializada"
    cobertura_pct: Mapped[int] = mapped_column(Integer, default=100)
    tarifa: Mapped[Decimal] = mapped_column(Numeric(12, 2))  # valor convenido por atencion
    tope_cubierto: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    vigente_desde: Mapped[date] = mapped_column(Date)
    vigente_hasta: Mapped[date | None] = mapped_column(Date)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class RemisionAliada(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.22 Remision: se emite solo con plan vigente, cartera al dia y beneficio
    disponible. La aliada la valida con el codigo y reporta la atencion sobre ella."""

    __tablename__ = "remisiones_aliadas"
    __columna_familia__ = "familia_id"

    codigo: Mapped[str] = mapped_column(String(12), unique=True)
    clinica_id: Mapped[UUID] = mapped_column(ForeignKey("clinicas_aliadas.id"), index=True)
    convenio_id: Mapped[UUID] = mapped_column(ForeignKey("convenios_aliadas.id"))
    familia_id: Mapped[UUID] = mapped_column(ForeignKey("familias.id"), index=True)
    mascota_id: Mapped[UUID] = mapped_column(ForeignKey("mascotas.id"))
    servicio_id: Mapped[UUID] = mapped_column(ForeignKey("servicios.id"), index=True)
    motivo: Mapped[str] = mapped_column(Text)
    beneficio_aplicado: Mapped[str | None] = mapped_column(String(160))
    cobertura_pct: Mapped[int] = mapped_column(Integer)
    tope_cubierto: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    vence_en: Mapped[date] = mapped_column(Date)
    # emitida | utilizada | anulada
    estado: Mapped[str] = mapped_column(String(24), default="emitida", index=True)
    emitida_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))
    # F2-ALI-03 Lo que reporta la aliada.
    fecha_atencion: Mapped[date | None] = mapped_column(Date, index=True)
    valor_atencion: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    valor_cubierto: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    resumen_atencion: Mapped[str | None] = mapped_column(Text)
    reportada_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))
    reportada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_anulacion: Mapped[str | None] = mapped_column(String(255))

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.auditoria import Auditable
from app.core.database import Base, JSONTipo, TimestampMixin, UUIDMixin


class Plan(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.3 Plan grupal. `ciudad` vacia = disponible en todas las ciudades."""

    __tablename__ = "planes"

    codigo: Mapped[str] = mapped_column(String(40), unique=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    ciudad: Mapped[str | None] = mapped_column(String(80), index=True)
    valor_mensual: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    cupos_mascotas: Mapped[int] = mapped_column(Integer, default=1)
    especies: Mapped[list[str]] = mapped_column(JSONTipo, default=list)  # vacio = todas
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    beneficios: Mapped[list["Beneficio"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", lazy="selectin"
    )


class Beneficio(Base, UUIDMixin, TimestampMixin, Auditable):
    """F1-PLA-01 Lo que cubre el plan por tipo de servicio. `cupo` vacio = ilimitado."""

    __tablename__ = "beneficios_plan"
    __table_args__ = (UniqueConstraint("plan_id", "tipo_servicio_codigo"),)

    plan_id: Mapped[UUID] = mapped_column(ForeignKey("planes.id", ondelete="CASCADE"), index=True)
    tipo_servicio_codigo: Mapped[str] = mapped_column(ForeignKey("tipos_servicio.codigo"))
    cupo: Mapped[int | None] = mapped_column(Integer)
    periodo_cupo: Mapped[str] = mapped_column(String(12), default="anual")  # mensual | anual
    cobertura_pct: Mapped[int] = mapped_column(Integer, default=100)
    copago: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    plan: Mapped[Plan] = relationship(back_populates="beneficios")


class CambioPlan(Base, UUIDMixin, TimestampMixin):
    """F1-PLA-02 / F1-PLA-03 Registro de cada cambio de plan o de cupo y su efecto en el valor."""

    __tablename__ = "cambios_plan"

    contrato_id: Mapped[UUID] = mapped_column(ForeignKey("contratos.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(24))  # cambio_plan | mascota_alta | mascota_baja
    plan_anterior_id: Mapped[UUID | None] = mapped_column(ForeignKey("planes.id"))
    plan_nuevo_id: Mapped[UUID | None] = mapped_column(ForeignKey("planes.id"))
    valor_anterior: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    valor_nuevo: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    ajuste: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)  # + cobro, - credito
    modo: Mapped[str | None] = mapped_column(String(24))
    regla_codigo: Mapped[str | None] = mapped_column(String(60))
    fecha_efectiva: Mapped[date] = mapped_column(Date)
    aplicado: Mapped[bool] = mapped_column(Boolean, default=True)
    registrado_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))

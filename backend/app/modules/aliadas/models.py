from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDMixin


class ClinicaAliada(Base, UUIDMixin, TimestampMixin):
    """6.22 Clinica aliada."""

    __tablename__ = "clinicas_aliadas"

    nombre: Mapped[str] = mapped_column(String(160))
    ciudad: Mapped[str] = mapped_column(String(80), index=True)
    direccion: Mapped[str | None] = mapped_column(String(255))
    telefono: Mapped[str | None] = mapped_column(String(32))
    activa: Mapped[bool] = mapped_column(Boolean, default=True)


class RemisionAliada(Base, UUIDMixin, TimestampMixin):
    """6.22 Remision: valida plan, pago y beneficio antes de autorizar la atencion."""

    __tablename__ = "remisiones_aliadas"

    clinica_id: Mapped[UUID] = mapped_column(ForeignKey("clinicas_aliadas.id"), index=True)
    servicio_id: Mapped[UUID] = mapped_column(ForeignKey("servicios.id"), index=True)
    beneficio_aplicado: Mapped[str | None] = mapped_column(String(120))
    valor_cubierto: Mapped[float | None] = mapped_column(Numeric(12, 2))
    estado: Mapped[str] = mapped_column(String(24), default="emitida", index=True)

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, JSONTipo, TimestampMixin, UUIDMixin


class Plan(Base, UUIDMixin, TimestampMixin):
    """6.3 Planes grupales. El motor de reglas (reglas JSON) evita tocar codigo base."""

    __tablename__ = "planes"

    nombre: Mapped[str] = mapped_column(String(120), unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    ciudad: Mapped[str | None] = mapped_column(String(80), index=True)
    valor_mensual: Mapped[float] = mapped_column(Numeric(12, 2))
    cupos_mascotas: Mapped[int] = mapped_column(Integer, default=1)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class ReglaPlan(Base, UUIDMixin, TimestampMixin):
    """6.3 / 6.11 Regla configurable: condicion -> accion, evaluada por el motor de reglas."""

    __tablename__ = "reglas_plan"

    plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("planes.id", ondelete="CASCADE"))
    nombre: Mapped[str] = mapped_column(String(160))
    condicion: Mapped[dict] = mapped_column(JSONTipo, default=dict)
    accion: Mapped[dict] = mapped_column(JSONTipo, default=dict)
    prioridad: Mapped[int] = mapped_column(Integer, default=100)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)

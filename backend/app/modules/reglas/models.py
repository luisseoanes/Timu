from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, JSONTipo, TimestampMixin, UUIDMixin


class Regla(Base, UUIDMixin, TimestampMixin, Auditable):
    """F0-12 Regla configurable: cuando ocurre `evento` y se cumple `condicion`, el modulo
    dueno del evento ejecuta `accion`. Se evalua en orden de prioridad (menor primero)."""

    __tablename__ = "reglas"

    codigo: Mapped[str] = mapped_column(String(60), unique=True)
    nombre: Mapped[str] = mapped_column(String(160))
    descripcion: Mapped[str | None] = mapped_column(Text)
    evento: Mapped[str] = mapped_column(String(60), index=True)
    condicion: Mapped[dict[str, Any]] = mapped_column(JSONTipo, default=dict)
    accion: Mapped[dict[str, Any]] = mapped_column(JSONTipo, default=dict)
    prioridad: Mapped[int] = mapped_column(Integer, default=100)
    # Si aplica, las reglas de menor prioridad del mismo evento ya no se evaluan.
    detener: Mapped[bool] = mapped_column(Boolean, default=False)
    plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("planes.id", ondelete="CASCADE"))
    vigente_desde: Mapped[date | None] = mapped_column(Date)
    vigente_hasta: Mapped[date | None] = mapped_column(Date)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

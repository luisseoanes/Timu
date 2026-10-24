from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, TimestampMixin, UUIDMixin


class Tarea(Base, UUIDMixin, TimestampMixin, Auditable):
    """F1-SER-06 Tarea interna. `clave` evita que un proceso diario cree la misma dos veces."""

    __tablename__ = "tareas"
    __columna_familia__ = "familia_id"

    titulo: Mapped[str] = mapped_column(String(200))
    descripcion: Mapped[str | None] = mapped_column(Text)
    area: Mapped[str] = mapped_column(String(24), index=True)
    prioridad: Mapped[str] = mapped_column(String(8), default="media", index=True)
    estado: Mapped[str] = mapped_column(String(16), default="abierta", index=True)
    vence_el: Mapped[date | None] = mapped_column(Date, index=True)
    asignada_a_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"), index=True)
    familia_id: Mapped[UUID | None] = mapped_column(ForeignKey("familias.id"), index=True)
    servicio_id: Mapped[UUID | None] = mapped_column(ForeignKey("servicios.id"), index=True)
    contrato_id: Mapped[UUID | None] = mapped_column(ForeignKey("contratos.id"), index=True)
    origen: Mapped[str | None] = mapped_column(String(60))  # codigo de la regla o 'manual'
    clave: Mapped[str | None] = mapped_column(String(160), unique=True)
    cerrada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolucion: Mapped[str | None] = mapped_column(Text)

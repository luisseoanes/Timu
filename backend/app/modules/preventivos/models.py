from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, TimestampMixin, UUIDMixin


class EventoPreventivo(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.8 / 6.13 / 6.15 Calendario preventivo. Al aplicarse alimenta el carnet digital."""

    __tablename__ = "eventos_preventivos"

    mascota_id: Mapped[UUID] = mapped_column(ForeignKey("mascotas.id"), index=True)
    esquema_codigo: Mapped[str | None] = mapped_column(
        ForeignKey("esquemas_preventivos.codigo"), index=True
    )
    tipo: Mapped[str] = mapped_column(String(60), index=True)
    dosis_numero: Mapped[int] = mapped_column(Integer, default=1)
    # programado | aplicado | cancelado. "Vencido" se deriva: programado con fecha pasada.
    estado: Mapped[str] = mapped_column(String(16), default="programado", index=True)
    producto: Mapped[str | None] = mapped_column(String(120))
    fecha_programada: Mapped[date] = mapped_column(Date, index=True)
    fecha_aplicacion: Mapped[date | None] = mapped_column(Date)
    proxima_fecha: Mapped[date | None] = mapped_column(Date, index=True)
    requiere_autorizacion: Mapped[bool] = mapped_column(Boolean, default=True)
    autorizado: Mapped[bool] = mapped_column(Boolean, default=False)
    servicio_id: Mapped[UUID | None] = mapped_column(ForeignKey("servicios.id"))

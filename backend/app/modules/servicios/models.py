from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDMixin
from app.core.enums import EstadoServicio, TipoServicio


class Servicio(Base, UUIDMixin, TimestampMixin):
    """6.5 / 6.10 Servicio agendado, con maquina de estados y disparadores de tareas."""

    __tablename__ = "servicios"

    familia_id: Mapped[UUID] = mapped_column(ForeignKey("familias.id"), index=True)
    mascota_id: Mapped[UUID | None] = mapped_column(ForeignKey("mascotas.id"), index=True)
    tipo: Mapped[TipoServicio] = mapped_column(String(24), index=True)
    estado: Mapped[EstadoServicio] = mapped_column(
        String(32), default=EstadoServicio.SOLICITADO, index=True
    )
    programado_para: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    ruta_id: Mapped[UUID | None] = mapped_column(ForeignKey("rutas.id"), index=True)
    requiere_autorizacion: Mapped[bool] = mapped_column(Boolean, default=False)
    autorizado: Mapped[bool] = mapped_column(Boolean, default=False)
    observaciones: Mapped[str | None] = mapped_column(Text)


class Pendiente(Base, UUIDMixin, TimestampMixin):
    """6.6 Pendiente derivado de una atencion, con control de autorizacion previa."""

    __tablename__ = "pendientes"

    servicio_origen_id: Mapped[UUID] = mapped_column(ForeignKey("servicios.id"), index=True)
    descripcion: Mapped[str] = mapped_column(Text)
    requiere_autorizacion: Mapped[bool] = mapped_column(Boolean, default=True)
    autorizado: Mapped[bool] = mapped_column(Boolean, default=False)
    resuelto: Mapped[bool] = mapped_column(Boolean, default=False)

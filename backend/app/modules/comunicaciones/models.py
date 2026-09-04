from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDMixin


class Mensaje(Base, UUIDMixin, TimestampMixin):
    """6.18 / 6.19 Trazabilidad de cada mensaje enviado o recibido (WhatsApp, email)."""

    __tablename__ = "mensajes"

    familia_id: Mapped[UUID | None] = mapped_column(ForeignKey("familias.id"), index=True)
    canal: Mapped[str] = mapped_column(String(24), default="whatsapp", index=True)
    direccion: Mapped[str] = mapped_column(String(12), default="saliente")
    plantilla: Mapped[str | None] = mapped_column(String(120))
    contenido: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(24), default="encolado", index=True)
    id_externo: Mapped[str | None] = mapped_column(String(120), index=True)
    enviado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    campana_id: Mapped[UUID | None] = mapped_column(ForeignKey("campanas.id"), index=True)

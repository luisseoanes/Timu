from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDMixin


class Encuesta(Base, UUIDMixin, TimestampMixin):
    """6.20 / 6.21 Encuesta disparada al cierre de la atencion y su seguimiento."""

    __tablename__ = "encuestas"

    servicio_id: Mapped[UUID] = mapped_column(ForeignKey("servicios.id"), index=True)
    familia_id: Mapped[UUID] = mapped_column(ForeignKey("familias.id"), index=True)
    enviada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    respondida_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    puntaje: Mapped[int | None] = mapped_column(Integer)
    comentario: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(24), default="pendiente", index=True)

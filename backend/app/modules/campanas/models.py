from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDMixin


class Campana(Base, UUIDMixin, TimestampMixin):
    """6.16 / 6.18 Campana masiva: segmento + plantilla + envio con trazabilidad."""

    __tablename__ = "campanas"

    nombre: Mapped[str] = mapped_column(String(160))
    canal: Mapped[str] = mapped_column(String(24), default="whatsapp")
    plantilla: Mapped[str | None] = mapped_column(String(120))
    contenido: Mapped[str | None] = mapped_column(Text)
    segmento: Mapped[dict] = mapped_column(JSON, default=dict)
    estado: Mapped[str] = mapped_column(String(24), default="borrador", index=True)
    programada_para: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    creada_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))

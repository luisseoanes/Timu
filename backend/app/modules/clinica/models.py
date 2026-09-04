from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDMixin


class HistoriaClinica(Base, UUIDMixin, TimestampMixin):
    """6.14 Registro clinico estructurado. Solo lectura desde el portal de familias."""

    __tablename__ = "historias_clinicas"

    mascota_id: Mapped[UUID] = mapped_column(ForeignKey("mascotas.id"), index=True)
    servicio_id: Mapped[UUID | None] = mapped_column(ForeignKey("servicios.id"))
    profesional_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))
    fecha: Mapped[date] = mapped_column(Date, index=True)
    motivo: Mapped[str] = mapped_column(Text)
    anamnesis: Mapped[str | None] = mapped_column(Text)
    diagnostico: Mapped[str | None] = mapped_column(Text)
    tratamiento: Mapped[str | None] = mapped_column(Text)


class AdjuntoClinico(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "adjuntos_clinicos"

    historia_id: Mapped[UUID] = mapped_column(
        ForeignKey("historias_clinicas.id", ondelete="CASCADE"), index=True
    )
    nombre_archivo: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str | None] = mapped_column(String(120))

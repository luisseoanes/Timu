from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDMixin


class Ruta(Base, UUIDMixin, TimestampMixin):
    """6.7 Ruta domiciliaria del dia, con secuencia optimizada (OR-Tools + Maps)."""

    __tablename__ = "rutas"

    fecha: Mapped[date] = mapped_column(Date, index=True)
    ciudad: Mapped[str] = mapped_column(String(80), index=True)
    responsable_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))
    estado: Mapped[str] = mapped_column(String(24), default="planificada", index=True)
    distancia_km: Mapped[float | None] = mapped_column()
    duracion_min: Mapped[int | None] = mapped_column(Integer)


class ParadaRuta(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "paradas_ruta"

    ruta_id: Mapped[UUID] = mapped_column(ForeignKey("rutas.id", ondelete="CASCADE"), index=True)
    servicio_id: Mapped[UUID] = mapped_column(ForeignKey("servicios.id"), index=True)
    orden: Mapped[int] = mapped_column(Integer)
    latitud: Mapped[float | None] = mapped_column()
    longitud: Mapped[float | None] = mapped_column()

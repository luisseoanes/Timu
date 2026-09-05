from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDMixin
from app.core.enums import EstadoAfiliacion


class Familia(Base, UUIDMixin, TimestampMixin):
    """6.1 Gestion de familias. Titular + contacto + ubicacion (usada por rutas 6.7)."""

    __tablename__ = "familias"
    # Una familia se ata a si misma: el portal solo ve su propia ficha (ver core/scope.py).
    __columna_familia__ = "id"

    titular_nombre: Mapped[str] = mapped_column(String(160))
    documento: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    telefono: Mapped[str] = mapped_column(String(32), index=True)
    ciudad: Mapped[str] = mapped_column(String(80), index=True)
    direccion: Mapped[str | None] = mapped_column(String(255))
    latitud: Mapped[float | None] = mapped_column()
    longitud: Mapped[float | None] = mapped_column()
    estado: Mapped[EstadoAfiliacion] = mapped_column(
        String(32), default=EstadoAfiliacion.PROSPECTO, index=True
    )
    notas: Mapped[str | None] = mapped_column(Text)

    usuario_portal_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))

    mascotas: Mapped[list["Mascota"]] = relationship(
        back_populates="familia", cascade="all, delete-orphan", lazy="selectin"
    )


class Mascota(Base, UUIDMixin, TimestampMixin):
    """6.1 Gestion de mascotas. Ancla de historia clinica (6.14) y carnet digital (6.15)."""

    __tablename__ = "mascotas"
    __columna_familia__ = "familia_id"

    familia_id: Mapped[UUID] = mapped_column(
        ForeignKey("familias.id", ondelete="CASCADE"), index=True
    )
    nombre: Mapped[str] = mapped_column(String(120))
    especie: Mapped[str] = mapped_column(String(40))
    raza: Mapped[str | None] = mapped_column(String(80))
    sexo: Mapped[str | None] = mapped_column(String(16))
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)
    peso_kg: Mapped[float | None] = mapped_column()

    familia: Mapped[Familia] = relationship(back_populates="mascotas")

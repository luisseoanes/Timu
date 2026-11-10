from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.auditoria import Auditable
from app.core.database import Base, EnumDb, TimestampMixin, UUIDMixin
from app.core.enums import EstadoAfiliacion, GeoPrecision, SexoMascota
from app.core.validaciones import TipoDocumento


class Familia(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.1 Gestion de familias. Titular + contacto + ubicacion (usada por rutas 6.7)."""

    __tablename__ = "familias"
    __checks__ = {
        "telefono_formato": "telefono ~ '^\\+[1-9][0-9]{7,14}$'",
        "email_formato": "email IS NULL OR email ~ '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$'",
        "titular_no_vacio": "btrim(titular_nombre) <> ''",
        "barrio_no_vacio": "btrim(barrio) <> ''",
        "documento_formato": "documento ~ '^[0-9A-Z]+$'",
        "latitud_rango": "latitud IS NULL OR latitud BETWEEN -90 AND 90",
        "longitud_rango": "longitud IS NULL OR longitud BETWEEN -180 AND 180",
        "coordenadas_juntas": "(latitud IS NULL) = (longitud IS NULL)",
        "baja_cancelada": "dada_de_baja_en IS NULL OR estado = 'cancelada'",
    }
    __unicos__ = {
        "usuario_portal": (["usuario_portal_id"], None),
    }
    # Una familia se ata a si misma: el portal solo ve su propia ficha (ver core/scope.py).
    __columna_familia__ = "id"
    __table_args__ = (UniqueConstraint("tipo_documento", "documento"),)

    titular_nombre: Mapped[str] = mapped_column(String(160))
    tipo_documento: Mapped[str] = mapped_column(EnumDb(TipoDocumento), default="CC")
    documento: Mapped[str] = mapped_column(String(32), index=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    telefono: Mapped[str] = mapped_column(String(32), index=True)
    ciudad: Mapped[str] = mapped_column(
        String(80), ForeignKey("ciudades.nombre", onupdate="CASCADE"), index=True
    )
    # 6.1 Zona/sector: el barrio, texto libre y obligatorio. El complemento (torre,
    # apartamento, indicaciones) es opcional y no se mezcla con las notas internas.
    barrio: Mapped[str] = mapped_column(String(120))
    direccion: Mapped[str | None] = mapped_column(String(255))
    complemento: Mapped[str | None] = mapped_column(String(255))
    latitud: Mapped[float | None] = mapped_column()
    longitud: Mapped[float | None] = mapped_column()
    # direccion | ciudad (aproximada) | manual
    geo_precision: Mapped[str | None] = mapped_column(EnumDb(GeoPrecision))
    estado: Mapped[EstadoAfiliacion] = mapped_column(
        EnumDb(EstadoAfiliacion), default=EstadoAfiliacion.PROSPECTO, index=True
    )
    origen: Mapped[str] = mapped_column(String(32), default="panel")  # panel | formulario | ...
    notas: Mapped[str | None] = mapped_column(Text)
    dada_de_baja_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    motivo_baja: Mapped[str | None] = mapped_column(String(255))
    # Habeas data (Ley 1581): los datos personales se sustituyen con la funcion
    # anonimizar_familia() de la base. Las filas se conservan; nada se borra.
    anonimizada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    usuario_portal_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))

    mascotas: Mapped[list["Mascota"]] = relationship(
        back_populates="familia",
        cascade="save-update, merge",
        lazy="selectin",
        order_by="Mascota.created_at",
    )


class Mascota(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.1 Gestion de mascotas. Ancla de historia clinica (6.14) y carnet digital (6.15)."""

    __tablename__ = "mascotas"
    __checks__ = {
        "nombre_no_vacio": "btrim(nombre) <> ''",
        "peso_positivo": "peso_kg IS NULL OR peso_kg > 0",
        "baja_coherente": "activa = (dada_de_baja_en IS NULL)",
    }
    __columna_familia__ = "familia_id"

    familia_id: Mapped[UUID] = mapped_column(
        ForeignKey("familias.id", ondelete="CASCADE"), index=True
    )
    nombre: Mapped[str] = mapped_column(String(120))
    especie: Mapped[str] = mapped_column(
        String(40), ForeignKey("especies.codigo", onupdate="CASCADE"), index=True
    )
    raza: Mapped[str | None] = mapped_column(String(80))
    sexo: Mapped[str | None] = mapped_column(EnumDb(SexoMascota))
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)
    peso_kg: Mapped[float | None] = mapped_column()
    esterilizada: Mapped[bool | None] = mapped_column(Boolean)
    foto_archivo_id: Mapped[UUID | None] = mapped_column(ForeignKey("archivos.id"), index=True)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    dada_de_baja_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_baja: Mapped[str | None] = mapped_column(String(255))

    familia: Mapped[Familia] = relationship(back_populates="mascotas")

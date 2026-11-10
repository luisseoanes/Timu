from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, ForeignKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, EnumDb, TimestampMixin, UUIDMixin
from app.core.enums import CategoriaDocumento


class DocumentoFamilia(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.1 Documento que el equipo adjunta a la familia o a una de sus mascotas. El fichero
    vive en el almacenamiento (`archivos`); la familia solo lo ve si el equipo lo marca
    visible. Quitarlo es una marca: nada se borra.

    La clave compuesta (mascota_id, familia_id) hace que la base rechace la mascota de otra
    familia, ademas del mensaje que da Python."""

    __tablename__ = "documentos_familia"
    __checks__ = {
        "descripcion_no_vacia": "descripcion IS NULL OR btrim(descripcion) <> ''",
        "baja_coherente": "activo = (dado_de_baja_en IS NULL)",
    }
    __table_args__ = (
        ForeignKeyConstraint(
            ["mascota_id", "familia_id"],
            ["mascotas.id", "mascotas.familia_id"],
            name="fk_documentos_familia_mascota_de_la_familia",
        ),
    )
    __columna_familia__ = "familia_id"

    familia_id: Mapped[UUID] = mapped_column(ForeignKey("familias.id"), index=True)
    mascota_id: Mapped[UUID | None] = mapped_column(index=True)
    archivo_id: Mapped[UUID] = mapped_column(ForeignKey("archivos.id"), unique=True)
    categoria: Mapped[str] = mapped_column(EnumDb(CategoriaDocumento))
    descripcion: Mapped[str | None] = mapped_column(String(255))
    visible_familia: Mapped[bool] = mapped_column(Boolean, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    dado_de_baja_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

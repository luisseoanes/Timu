from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, EnumDb, TimestampMixin, UUIDMixin
from app.core.enums import PropositoArchivo


class Archivo(Base, UUIDMixin, TimestampMixin):
    """F0-11 Metadatos de un archivo guardado fuera del servidor. El contenido vive en el
    almacenamiento bajo `clave`; la URL se genera firmada en cada consulta."""

    __tablename__ = "archivos"
    __checks__ = {
        "tamano_no_negativo": "tamano_bytes >= 0",
        "sha256_formato": "sha256 ~ '^[0-9a-f]{64}$'",
    }

    clave: Mapped[str] = mapped_column(String(255), unique=True)
    proposito: Mapped[str] = mapped_column(
        EnumDb(PropositoArchivo), index=True
    )  # foto_mascota, adjunto_clinico
    nombre_original: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120))
    tamano_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    subido_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"), index=True)
    # El objeto se borro del almacenamiento (anonimizacion). La fila queda como constancia.
    purgado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

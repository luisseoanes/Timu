from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDMixin


class Archivo(Base, UUIDMixin, TimestampMixin):
    """F0-11 Metadatos de un archivo guardado fuera del servidor. El contenido vive en el
    almacenamiento bajo `clave`; la URL se genera firmada en cada consulta."""

    __tablename__ = "archivos"

    clave: Mapped[str] = mapped_column(String(255), unique=True)
    proposito: Mapped[str] = mapped_column(String(40), index=True)  # foto_mascota, adjunto_clinico
    nombre_original: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120))
    tamano_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    subido_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))

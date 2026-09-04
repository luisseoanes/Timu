from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDMixin
from app.core.enums import Rol


class Usuario(Base, UUIDMixin, TimestampMixin):
    """Usuario del panel operativo o del portal de familias (rol FAMILIA)."""

    __tablename__ = "usuarios"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(160))
    hashed_password: Mapped[str] = mapped_column(String(255))
    rol: Mapped[Rol] = mapped_column(String(32), default=Rol.OPERACIONES)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

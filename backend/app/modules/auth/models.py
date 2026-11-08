from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, EnumDb, TimestampMixin, UUIDMixin
from app.core.enums import PropositoToken, Rol


class Usuario(Base, UUIDMixin, TimestampMixin, Auditable):
    """Usuario del panel operativo o del portal de familias (rol FAMILIA).

    Se identifica por email o por telefono: muchas familias solo tienen WhatsApp.
    """

    __tablename__ = "usuarios"
    __checks__ = {
        "aliada_con_clinica": "(rol = 'aliada') = (clinica_aliada_id IS NOT NULL)",
        "email_formato": "email IS NULL OR email ~ '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$'",
        "telefono_formato": "telefono IS NULL OR telefono ~ '^\\+[1-9][0-9]{7,14}$'",
        "nombre_no_vacio": "btrim(nombre) <> ''",
    }
    __table_args__ = (
        CheckConstraint("email IS NOT NULL OR telefono IS NOT NULL", name="con_identificador"),
    )

    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    telefono: Mapped[str | None] = mapped_column(String(32), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(160))
    hashed_password: Mapped[str] = mapped_column(String(255))
    rol: Mapped[Rol] = mapped_column(EnumDb(Rol), default=Rol.OPERACIONES)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    # F2-ALI-03 Solo para el rol aliada: la clinica cuyas remisiones puede ver.
    clinica_aliada_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("clinicas_aliadas.id"), index=True
    )


class Sesion(Base, UUIDMixin, TimestampMixin):
    """F1-AUT-01 Sesion renovable. El refresh token solo se guarda como hash."""

    __tablename__ = "sesiones"

    usuario_id: Mapped[UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True
    )
    refresh_hash: Mapped[str] = mapped_column(String(64), unique=True)
    # Hash del refresh ya rotado: si alguien lo vuelve a presentar, fue robado.
    refresh_hash_anterior: Mapped[str | None] = mapped_column(String(64), index=True)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revocada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(255))


class TokenUsoUnico(Base, UUIDMixin, TimestampMixin):
    """F1-AUT-03 / F1-AUT-04 Enlaces de recuperacion y de activacion del portal."""

    __tablename__ = "tokens_uso_unico"
    __checks__ = {
        "intentos_no_negativos": "intentos >= 0",
    }

    usuario_id: Mapped[UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True
    )
    proposito: Mapped[str] = mapped_column(
        EnumDb(PropositoToken)
    )  # recuperacion | activacion | codigo_ingreso
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    usado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # F3-POR-07 Intentos fallidos con un codigo de ingreso; al tope, el codigo se invalida.
    intentos: Mapped[int] = mapped_column(Integer, default=0)

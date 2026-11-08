from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, EnumDb, JSONTipo, TimestampMixin, UUIDMixin
from app.core.enums import EstadoConversacion, EtapaInteresado


class Interesado(Base, UUIDMixin, TimestampMixin, Auditable):
    """F3-COM-01 Persona en el embudo comercial, venga de donde venga, con su origen y su
    responsable. Al afiliarse queda atada a la familia."""

    __tablename__ = "interesados"
    __checks__ = {
        "telefono_formato": "telefono IS NULL OR telefono ~ '^\\+[1-9][0-9]{7,14}$'",
        "email_formato": "email IS NULL OR email ~ '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$'",
    }

    nombre: Mapped[str | None] = mapped_column(String(160))
    telefono: Mapped[str | None] = mapped_column(String(32), unique=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    ciudad: Mapped[str | None] = mapped_column(String(80), index=True)
    # whatsapp | formulario | afiliacion | panel | referido | campana
    origen: Mapped[str] = mapped_column(String(24), index=True)
    # nuevo | contactado | cotizado | en_afiliacion | afiliado | perdido
    etapa: Mapped[str] = mapped_column(EnumDb(EtapaInteresado), default="nuevo", index=True)
    responsable_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"), index=True)
    familia_id: Mapped[UUID | None] = mapped_column(ForeignKey("familias.id"), index=True)
    plan_sugerido: Mapped[str | None] = mapped_column(
        String(40), ForeignKey("planes.codigo", onupdate="CASCADE"), index=True
    )
    datos: Mapped[dict[str, Any]] = mapped_column(JSONTipo, default=dict)
    motivo_perdida: Mapped[str | None] = mapped_column(String(255))
    ultimo_contacto: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ArbolConversacion(Base, UUIDMixin, TimestampMixin, Auditable):
    """F3-COM-02 Arbol de la conversacion comercial, versionado. Se edita como dato: un
    cambio en las respuestas no exige desplegar codigo."""

    __tablename__ = "arboles_conversacion"
    __checks__ = {
        "version_minimo": "version >= 1",
    }
    __unicos__ = {
        "activo": (["activo"], "activo"),
    }

    version: Mapped[int] = mapped_column(Integer, unique=True)
    nodos: Mapped[dict[str, Any]] = mapped_column(JSONTipo)
    activo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    nota: Mapped[str | None] = mapped_column(Text)


class ConversacionComercial(Base, UUIDMixin, TimestampMixin):
    """Estado de la conversacion automatizada con un numero."""

    __tablename__ = "conversaciones_comerciales"
    __checks__ = {
        "telefono_formato": "telefono ~ '^\\+[1-9][0-9]{7,14}$'",
    }

    telefono: Mapped[str] = mapped_column(String(32), unique=True)
    interesado_id: Mapped[UUID | None] = mapped_column(ForeignKey("interesados.id"), index=True)
    nodo: Mapped[str] = mapped_column(String(40), default="inicio")
    datos: Mapped[dict[str, Any]] = mapped_column(JSONTipo, default=dict)
    # automatica | con_asesor
    estado: Mapped[str] = mapped_column(
        EnumDb(EstadoConversacion), default="automatica", index=True
    )
    fallos: Mapped[int] = mapped_column(Integer, default=0)
    asesor_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"), index=True)
    tarea_id: Mapped[UUID | None] = mapped_column(ForeignKey("tareas.id"), index=True)

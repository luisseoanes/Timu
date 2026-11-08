from datetime import datetime
from enum import StrEnum, nonmember
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, EnumDb, JSONTipo, TimestampMixin, UUIDMixin
from app.core.enums import (
    CanalComunicacion,
    CategoriaPlantilla,
    DireccionMensaje,
    EstadoAprobacionPlantilla,
)


class EstadoMensaje(StrEnum):
    ENCOLADO = "encolado"
    ENVIADO = "enviado"
    ENTREGADO = "entregado"
    LEIDO = "leido"
    FALLIDO = "fallido"
    RECIBIDO = "recibido"  # entrante
    OMITIDO = "omitido"  # destinatario dado de baja de envios masivos

    # Orden de avance: un estado de entrega atrasado no retrocede el mensaje.
    ORDEN = nonmember({ENCOLADO: 0, ENVIADO: 1, ENTREGADO: 2, LEIDO: 3})


class Mensaje(Base, UUIDMixin, TimestampMixin):
    """6.18 / 6.19 Trazabilidad de cada mensaje enviado o recibido (WhatsApp, email)."""

    __tablename__ = "mensajes"
    __checks__ = {
        "intentos_no_negativos": "intentos >= 0",
    }
    __columna_familia__ = "familia_id"

    familia_id: Mapped[UUID | None] = mapped_column(ForeignKey("familias.id"), index=True)
    canal: Mapped[str] = mapped_column(EnumDb(CanalComunicacion), default="whatsapp", index=True)
    direccion: Mapped[str] = mapped_column(EnumDb(DireccionMensaje), default="saliente")
    destino: Mapped[str | None] = mapped_column(String(255), index=True)
    plantilla: Mapped[str | None] = mapped_column(String(120))
    variables: Mapped[list[str]] = mapped_column(JSONTipo, default=list)
    asunto: Mapped[str | None] = mapped_column(String(255))
    contenido: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(
        EnumDb(EstadoMensaje), default=EstadoMensaje.ENCOLADO, index=True
    )
    id_externo: Mapped[str | None] = mapped_column(String(120), index=True)
    intentos: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    masivo: Mapped[bool] = mapped_column(Boolean, default=False)
    enviado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    entregado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    leido_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    campana_id: Mapped[UUID | None] = mapped_column(ForeignKey("campanas.id"), index=True)


class PlantillaWhatsApp(Base, UUIDMixin, TimestampMixin):
    """F1-WHA-03 Plantilla registrada en Meta. Cada cambio de texto es una version nueva,
    porque Meta vuelve a revisarla; solo la version aprobada y activa se usa para enviar."""

    __tablename__ = "plantillas_whatsapp"
    __checks__ = {
        "version_minimo": "version >= 1",
        "activa_aprobada": "NOT activa OR estado_aprobacion = 'aprobada'",
        "idioma_formato": "idioma ~ '^[a-z]{2}(_[A-Z]{2})?$'",
    }
    __unicos__ = {
        "activa": (["nombre", "idioma"], "activa"),
    }
    __table_args__ = (UniqueConstraint("nombre", "idioma", "version"),)

    nombre: Mapped[str] = mapped_column(String(120), index=True)
    idioma: Mapped[str] = mapped_column(String(10), default="es")
    version: Mapped[int] = mapped_column(Integer, default=1)
    categoria: Mapped[str] = mapped_column(EnumDb(CategoriaPlantilla), default="utility")
    cuerpo: Mapped[str] = mapped_column(Text)
    variables: Mapped[list[str]] = mapped_column(JSONTipo, default=list)
    estado_aprobacion: Mapped[str] = mapped_column(
        EnumDb(EstadoAprobacionPlantilla), default="borrador"
    )
    activa: Mapped[bool] = mapped_column(Boolean, default=False)


class ConversacionWhatsApp(Base, UUIDMixin, TimestampMixin):
    """F1-WHA-04 Ultimo mensaje entrante por numero: define la ventana de 24 horas."""

    __tablename__ = "conversaciones_whatsapp"
    __checks__ = {
        "telefono_formato": "telefono ~ '^\\+[1-9][0-9]{7,14}$'",
    }
    __columna_familia__ = "familia_id"

    telefono: Mapped[str] = mapped_column(String(32), unique=True)
    familia_id: Mapped[UUID | None] = mapped_column(ForeignKey("familias.id"), index=True)
    ultimo_entrante_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class BajaComunicaciones(Base, UUIDMixin, TimestampMixin):
    """F1-WHA-04 Quien pidio no recibir mas envios masivos (campanas, promociones)."""

    __tablename__ = "bajas_comunicaciones"
    __unicos__ = {"destino_activa": (["destino"], "reactivada_en IS NULL")}

    destino: Mapped[str] = mapped_column(String(255), index=True)
    canal: Mapped[str] = mapped_column(EnumDb(CanalComunicacion), default="whatsapp")
    motivo: Mapped[str | None] = mapped_column(String(255))
    # Reactivar los envios cierra la baja en vez de borrarla: queda constancia de que la
    # persona pidio no recibir mensajes y de cuando se levanto.
    reactivada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

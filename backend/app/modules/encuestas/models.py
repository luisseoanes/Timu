from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, EnumDb, TimestampMixin, UUIDMixin
from app.core.enums import CanalRespuestaEncuesta, EstadoEncuesta, TipoEncuesta


class Encuesta(Base, UUIDMixin, TimestampMixin):
    """6.20 / 6.21 Encuesta al cierre de la atencion (satisfaccion) o seguimiento posterior.

    El puntaje queda atado al servicio y a quien lo atendio (F3-ENC-02).
    """

    __tablename__ = "encuestas"
    __checks__ = {
        "puntaje_rango": "puntaje IS NULL OR puntaje BETWEEN 1 AND 5",
        "respondida_completa": (
            "estado <> 'respondida' OR (respondida_en IS NOT NULL" " AND puntaje IS NOT NULL)"
        ),
        "enviada_con_fecha": "estado NOT IN ('enviada', 'respondida') OR enviada_en IS NOT NULL",
    }
    __unicos__ = {
        "servicio_tipo": (["servicio_id", "tipo"], None),
    }
    __columna_familia__ = "familia_id"

    servicio_id: Mapped[UUID] = mapped_column(ForeignKey("servicios.id"), index=True)
    familia_id: Mapped[UUID] = mapped_column(ForeignKey("familias.id"), index=True)
    responsable_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"), index=True)
    tipo: Mapped[str] = mapped_column(EnumDb(TipoEncuesta), default="satisfaccion")  # | seguimiento
    # Secreto del enlace de respuesta: quien lo tiene responde sin iniciar sesion.
    token: Mapped[str] = mapped_column(String(64), unique=True)
    programada_para: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    enviada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    respondida_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canal_respuesta: Mapped[str | None] = mapped_column(
        EnumDb(CanalRespuestaEncuesta)
    )  # enlace | whatsapp
    puntaje: Mapped[int | None] = mapped_column(Integer)
    comentario: Mapped[str | None] = mapped_column(Text)
    # pendiente | enviada | respondida | vencida | omitida
    estado: Mapped[str] = mapped_column(EnumDb(EstadoEncuesta), default="pendiente", index=True)
    tarea_id: Mapped[UUID | None] = mapped_column(ForeignKey("tareas.id"), index=True)


class ConfiguracionEncuesta(Base, UUIDMixin, TimestampMixin, Auditable):
    """F3-ENC-01 / 03 Por tipo de atencion: cuando sale la encuesta, si hay seguimiento y
    desde que puntaje se alerta. Sin `tipo_servicio_codigo` es la configuracion general."""

    __tablename__ = "configuraciones_encuesta"
    __checks__ = {
        "demora_no_negativa": "demora_horas >= 0",
        "seguimiento_rango": "seguimiento_dias IS NULL OR seguimiento_dias BETWEEN 1 AND 180",
        "umbral_rango": "umbral_alerta BETWEEN 1 AND 5",
    }

    tipo_servicio_codigo: Mapped[str | None] = mapped_column(
        ForeignKey("tipos_servicio.codigo"), unique=True
    )
    encuesta_activa: Mapped[bool] = mapped_column(Boolean, default=True)
    demora_horas: Mapped[int] = mapped_column(Integer, default=2)
    plantilla_encuesta: Mapped[str] = mapped_column(String(120), default="encuesta_satisfaccion")
    seguimiento_dias: Mapped[int | None] = mapped_column(Integer)
    plantilla_seguimiento: Mapped[str] = mapped_column(String(120), default="seguimiento_post")
    # Puntaje igual o menor que este crea una tarea de servicio al cliente (F3-ENC-04).
    umbral_alerta: Mapped[int] = mapped_column(Integer, default=3)
    comentario: Mapped[str | None] = mapped_column(Text)

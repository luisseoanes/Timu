from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, TimestampMixin, UUIDMixin


class Encuesta(Base, UUIDMixin, TimestampMixin):
    """6.20 / 6.21 Encuesta al cierre de la atencion (satisfaccion) o seguimiento posterior.

    El puntaje queda atado al servicio y a quien lo atendio (F3-ENC-02).
    """

    __tablename__ = "encuestas"
    __columna_familia__ = "familia_id"

    servicio_id: Mapped[UUID] = mapped_column(ForeignKey("servicios.id"), index=True)
    familia_id: Mapped[UUID] = mapped_column(ForeignKey("familias.id"), index=True)
    responsable_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(16), default="satisfaccion")  # | seguimiento
    # Secreto del enlace de respuesta: quien lo tiene responde sin iniciar sesion.
    token: Mapped[str] = mapped_column(String(64), unique=True)
    programada_para: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    enviada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    respondida_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canal_respuesta: Mapped[str | None] = mapped_column(String(16))  # enlace | whatsapp
    puntaje: Mapped[int | None] = mapped_column(Integer)
    comentario: Mapped[str | None] = mapped_column(Text)
    # pendiente | enviada | respondida | vencida | omitida
    estado: Mapped[str] = mapped_column(String(24), default="pendiente", index=True)
    tarea_id: Mapped[UUID | None] = mapped_column(ForeignKey("tareas.id"))


class ConfiguracionEncuesta(Base, UUIDMixin, TimestampMixin, Auditable):
    """F3-ENC-01 / 03 Por tipo de atencion: cuando sale la encuesta, si hay seguimiento y
    desde que puntaje se alerta. Sin `tipo_servicio_codigo` es la configuracion general."""

    __tablename__ = "configuraciones_encuesta"

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

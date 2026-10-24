from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, JSONTipo, TimestampMixin, UUIDMixin


class Segmento(Base, UUIDMixin, TimestampMixin, Auditable):
    """F3-SEG-01 Filtros combinables guardados con nombre, reutilizables en campanas y
    reportes. Se evaluan al usarse: el segmento sigue a los datos, no es una lista fija."""

    __tablename__ = "segmentos"

    nombre: Mapped[str] = mapped_column(String(160), unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    filtros: Mapped[dict[str, Any]] = mapped_column(JSONTipo, default=dict)
    creado_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))


class Campana(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.16 / 6.18 Campana masiva: segmento + plantilla aprobada + programacion."""

    __tablename__ = "campanas"

    nombre: Mapped[str] = mapped_column(String(160))
    canal: Mapped[str] = mapped_column(String(24), default="whatsapp")
    plantilla: Mapped[str | None] = mapped_column(String(120))
    # De donde sale cada variable de la plantilla, en orden: "titular_nombre",
    # "mascota_nombre", "ciudad", "plan" o "texto:<valor fijo>".
    variables: Mapped[list[str]] = mapped_column(JSONTipo, default=list)
    contenido: Mapped[str | None] = mapped_column(Text)
    segmento_id: Mapped[UUID | None] = mapped_column(ForeignKey("segmentos.id"))
    segmento: Mapped[dict[str, Any]] = mapped_column(JSONTipo, default=dict)
    # borrador | programada | en_envio | finalizada | cancelada
    estado: Mapped[str] = mapped_column(String(24), default="borrador", index=True)
    programada_para: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # F3-CAM-04 ninguna | diaria | semanal | mensual
    recurrencia: Mapped[str] = mapped_column(String(16), default="ninguna")
    proxima_ejecucion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    creada_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))


class EjecucionCampana(Base, UUIDMixin, TimestampMixin):
    """Una salida de la campana. La audiencia se congela al iniciar (lo que hoy cumple el
    segmento), y los resultados se cuentan por ejecucion."""

    __tablename__ = "ejecuciones_campana"

    campana_id: Mapped[UUID] = mapped_column(ForeignKey("campanas.id"), index=True)
    iniciada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    terminada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # en_envio | terminada | cancelada
    estado: Mapped[str] = mapped_column(String(16), default="en_envio", index=True)
    audiencia: Mapped[int] = mapped_column(Integer, default=0)
    excluidos: Mapped[int] = mapped_column(Integer, default=0)


class DestinatarioCampana(Base, UUIDMixin, TimestampMixin):
    """F3-CAM-02 Traza por destinatario: cuando se encolo y con que mensaje, o por que se
    excluyo."""

    __tablename__ = "destinatarios_campana"
    __table_args__ = (UniqueConstraint("ejecucion_id", "familia_id"),)
    __columna_familia__ = "familia_id"

    ejecucion_id: Mapped[UUID] = mapped_column(
        ForeignKey("ejecuciones_campana.id", ondelete="CASCADE"), index=True
    )
    familia_id: Mapped[UUID] = mapped_column(ForeignKey("familias.id"), index=True)
    telefono: Mapped[str] = mapped_column(String(32))
    # pendiente | encolado | excluido
    estado: Mapped[str] = mapped_column(String(16), default="pendiente", index=True)
    motivo_exclusion: Mapped[str | None] = mapped_column(String(120))
    mensaje_id: Mapped[UUID | None] = mapped_column(ForeignKey("mensajes.id"))
    encolado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, JSONTipo, TimestampMixin, UUIDMixin


class EventoPreventivo(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.8 / 6.13 / 6.15 Calendario preventivo. Al aplicarse alimenta el carnet digital."""

    __tablename__ = "eventos_preventivos"

    mascota_id: Mapped[UUID] = mapped_column(ForeignKey("mascotas.id"), index=True)
    esquema_codigo: Mapped[str | None] = mapped_column(
        ForeignKey("esquemas_preventivos.codigo"), index=True
    )
    tipo: Mapped[str] = mapped_column(String(60), index=True)
    dosis_numero: Mapped[int] = mapped_column(Integer, default=1)
    # Dosis de refuerzo periodico (no de la serie inicial): define como se calcula la siguiente.
    es_refuerzo: Mapped[bool] = mapped_column(Boolean, default=False)
    # programado | aplicado | cancelado. "Vencido" se deriva: programado con fecha pasada.
    estado: Mapped[str] = mapped_column(String(16), default="programado", index=True)
    producto: Mapped[str | None] = mapped_column(String(120))
    lote: Mapped[str | None] = mapped_column(String(60))
    fecha_programada: Mapped[date] = mapped_column(Date, index=True)
    fecha_aplicacion: Mapped[date | None] = mapped_column(Date)
    proxima_fecha: Mapped[date | None] = mapped_column(Date, index=True)
    aplicado_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))
    # F2-PRE-03 Autorizacion previa de la familia: quien la registro, cuando y por que medio.
    requiere_autorizacion: Mapped[bool] = mapped_column(Boolean, default=True)
    autorizado: Mapped[bool] = mapped_column(Boolean, default=False)
    autorizado_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))
    autorizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    medio_autorizacion: Mapped[str | None] = mapped_column(String(24))
    motivo_cancelacion: Mapped[str | None] = mapped_column(String(255))
    # F2-PRE-04 Aviso a la familia de que se acerca la fecha (una sola vez por evento).
    notificado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    servicio_id: Mapped[UUID | None] = mapped_column(ForeignKey("servicios.id"))


class CarnetEmitido(Base, UUIDMixin, TimestampMixin):
    """F2-PRE-06 Carnet descargado. El codigo lo valida un tercero (otra clinica, un
    hotel canino) sin entrar al sistema: ve lo que el carnet decia al emitirse y nada de
    la familia."""

    __tablename__ = "carnets_emitidos"

    codigo: Mapped[str] = mapped_column(String(16), unique=True)
    mascota_id: Mapped[UUID] = mapped_column(ForeignKey("mascotas.id"), index=True)
    archivo_id: Mapped[UUID | None] = mapped_column(ForeignKey("archivos.id"))
    sha256: Mapped[str] = mapped_column(String(64))
    # Foto de lo aplicado al momento de emitir: el carnet no cambia aunque luego se corrija.
    contenido: Mapped[dict[str, Any]] = mapped_column(JSONTipo, default=dict)
    emitido_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, EnumDb, JSONTipo, TimestampMixin, UUIDMixin
from app.core.enums import EstadoEventoPreventivo, MedioAutorizacion, TipoPreventivo


class EventoPreventivo(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.8 / 6.13 / 6.15 Calendario preventivo. Al aplicarse alimenta el carnet digital."""

    __tablename__ = "eventos_preventivos"
    __checks__ = {
        "dosis_minimo": "dosis_numero >= 1",
        "aplicado_con_fecha": "estado <> 'aplicado' OR fecha_aplicacion IS NOT NULL",
        "peso_positivo": "peso_kg IS NULL OR peso_kg > 0",
    }

    mascota_id: Mapped[UUID] = mapped_column(ForeignKey("mascotas.id"), index=True)
    esquema_codigo: Mapped[str | None] = mapped_column(
        ForeignKey("esquemas_preventivos.codigo"), index=True
    )
    tipo: Mapped[str] = mapped_column(EnumDb(TipoPreventivo), index=True)
    dosis_numero: Mapped[int] = mapped_column(Integer, default=1)
    # Dosis de refuerzo periodico (no de la serie inicial): define como se calcula la siguiente.
    es_refuerzo: Mapped[bool] = mapped_column(Boolean, default=False)
    # programado | aplicado | cancelado. "Vencido" se deriva: programado con fecha pasada.
    estado: Mapped[str] = mapped_column(
        EnumDb(EstadoEventoPreventivo), default="programado", index=True
    )
    producto: Mapped[str | None] = mapped_column(String(120))
    lote: Mapped[str | None] = mapped_column(String(60))
    # 6.8 «Registrar peso cuando sea pertinente» (F2-PRE-07): el de la mascota el dia de la
    # aplicacion. Va en el carnet junto a cada desparasitacion, como en el carnet impreso.
    peso_kg: Mapped[float | None] = mapped_column()
    fecha_programada: Mapped[date] = mapped_column(Date, index=True)
    fecha_aplicacion: Mapped[date | None] = mapped_column(Date)
    proxima_fecha: Mapped[date | None] = mapped_column(Date, index=True)
    aplicado_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"), index=True)
    # F2-PRE-03 Autorizacion previa de la familia: quien la registro, cuando y por que medio.
    requiere_autorizacion: Mapped[bool] = mapped_column(Boolean, default=True)
    autorizado: Mapped[bool] = mapped_column(Boolean, default=False)
    autorizado_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"), index=True)
    autorizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    medio_autorizacion: Mapped[str | None] = mapped_column(EnumDb(MedioAutorizacion))
    motivo_cancelacion: Mapped[str | None] = mapped_column(String(255))
    # F2-PRE-04 Aviso a la familia de que se acerca la fecha (una sola vez por evento).
    notificado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    servicio_id: Mapped[UUID | None] = mapped_column(ForeignKey("servicios.id"), index=True)


class CarnetEmitido(Base, UUIDMixin, TimestampMixin):
    """F2-PRE-06 Carnet descargado. El codigo lo valida un tercero (otra clinica, un
    hotel canino) sin entrar al sistema: ve lo que el carnet decia al emitirse y nada de
    la familia."""

    __tablename__ = "carnets_emitidos"
    __checks__ = {
        "sha256_formato": "sha256 ~ '^[0-9a-f]{64}$'",
    }

    codigo: Mapped[str] = mapped_column(String(16), unique=True)
    mascota_id: Mapped[UUID] = mapped_column(ForeignKey("mascotas.id"), index=True)
    archivo_id: Mapped[UUID | None] = mapped_column(ForeignKey("archivos.id"), index=True)
    sha256: Mapped[str] = mapped_column(String(64))
    # Foto de lo aplicado al momento de emitir: el carnet no cambia aunque luego se corrija.
    contenido: Mapped[dict[str, Any]] = mapped_column(JSONTipo, default=dict)
    emitido_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"), index=True)

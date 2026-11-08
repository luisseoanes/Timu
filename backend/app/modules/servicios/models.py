from datetime import date, datetime, time
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, EnumDb, JSONTipo, TimestampMixin, UUIDMixin
from app.core.enums import EstadoServicio, MedioAutorizacion, TipoServicio


class Franja(Base, UUIDMixin, TimestampMixin, Auditable):
    """F1-SER-01 Disponibilidad semanal por ciudad y modalidad. `capacidad` = atenciones
    simultaneas posibles (profesionales o vehiculos disponibles en esa franja)."""

    __tablename__ = "franjas_agenda"
    __checks__ = {
        "dia_semana_rango": "dia_semana BETWEEN 0 AND 6",
        "horario": "hora_fin > hora_inicio",
        "capacidad_positiva": "capacidad > 0",
    }

    ciudad: Mapped[str] = mapped_column(
        String(80), ForeignKey("ciudades.nombre", onupdate="CASCADE"), index=True
    )
    modalidad: Mapped[str] = mapped_column(EnumDb(TipoServicio), index=True)
    dia_semana: Mapped[int] = mapped_column(Integer)  # 0 = lunes
    hora_inicio: Mapped[time] = mapped_column(Time)
    hora_fin: Mapped[time] = mapped_column(Time)
    capacidad: Mapped[int] = mapped_column(Integer, default=1)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)


class BloqueoAgenda(Base, UUIDMixin, TimestampMixin):
    """Dias sin atencion (festivos, capacitaciones) por ciudad; ciudad vacia = todas."""

    __tablename__ = "bloqueos_agenda"

    fecha: Mapped[date] = mapped_column(Date, index=True)
    ciudad: Mapped[str | None] = mapped_column(
        String(80), ForeignKey("ciudades.nombre", onupdate="CASCADE"), index=True
    )
    modalidad: Mapped[str | None] = mapped_column(EnumDb(TipoServicio))
    motivo: Mapped[str] = mapped_column(String(160))


class Servicio(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.5 / 6.10 Servicio agendado, con maquina de estados y disparadores de tareas."""

    __tablename__ = "servicios"
    __checks__ = {
        "horario": "termina_en IS NULL OR programado_para IS NULL OR termina_en > programado_para",
        "cancelado_con_motivo": "estado <> 'cancelado' OR motivo_estado IS NOT NULL",
    }
    __columna_familia__ = "familia_id"

    familia_id: Mapped[UUID] = mapped_column(ForeignKey("familias.id"), index=True)
    mascota_id: Mapped[UUID | None] = mapped_column(ForeignKey("mascotas.id"), index=True)
    tipo_codigo: Mapped[str] = mapped_column(ForeignKey("tipos_servicio.codigo"), index=True)
    tipo: Mapped[TipoServicio] = mapped_column(EnumDb(TipoServicio), index=True)  # modalidad
    estado: Mapped[EstadoServicio] = mapped_column(
        EnumDb(EstadoServicio), default=EstadoServicio.SOLICITADO, index=True
    )
    ciudad: Mapped[str] = mapped_column(
        String(80), ForeignKey("ciudades.nombre", onupdate="CASCADE"), index=True
    )
    programado_para: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    termina_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    franja_id: Mapped[UUID | None] = mapped_column(ForeignKey("franjas_agenda.id"), index=True)
    profesional_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"), index=True)
    ruta_id: Mapped[UUID | None] = mapped_column(ForeignKey("rutas.id"), index=True)
    requiere_autorizacion: Mapped[bool] = mapped_column(Boolean, default=False)
    autorizado: Mapped[bool] = mapped_column(Boolean, default=False)
    autorizado_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"), index=True)
    autorizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pendiente_origen_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("pendientes.id"), index=True
    )
    observaciones: Mapped[str | None] = mapped_column(Text)
    motivo_estado: Mapped[str | None] = mapped_column(String(255))


class ServicioPaso(Base, UUIDMixin, TimestampMixin, Auditable):
    """F1-SER-02 Paso del flujo del tipo de servicio, completado en esta atencion."""

    __tablename__ = "servicio_pasos"
    __table_args__ = (UniqueConstraint("servicio_id", "paso_codigo"),)

    servicio_id: Mapped[UUID] = mapped_column(
        ForeignKey("servicios.id", ondelete="CASCADE"), index=True
    )
    paso_codigo: Mapped[str] = mapped_column(String(40))
    completado_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"), index=True)
    datos: Mapped[dict[str, Any]] = mapped_column(JSONTipo, default=dict)


class EstadoPendiente(StrEnum):
    PENDIENTE_AUTORIZACION = "pendiente_autorizacion"
    AUTORIZADO = "autorizado"
    EN_GESTION = "en_gestion"
    RESUELTO = "resuelto"
    RECHAZADO = "rechazado"


class Pendiente(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.6 Pendiente derivado de una atencion. Si requiere autorizacion, no avanza sin ella."""

    __tablename__ = "pendientes"
    __table_args__ = (Index("ix_pendientes_created_at", "created_at"),)

    servicio_origen_id: Mapped[UUID] = mapped_column(ForeignKey("servicios.id"), index=True)
    descripcion: Mapped[str] = mapped_column(Text)
    requiere_autorizacion: Mapped[bool] = mapped_column(Boolean, default=True)
    estado: Mapped[str] = mapped_column(
        EnumDb(EstadoPendiente), default=EstadoPendiente.PENDIENTE_AUTORIZACION, index=True
    )
    autorizado_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"), index=True)
    autorizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    medio_autorizacion: Mapped[str | None] = mapped_column(EnumDb(MedioAutorizacion))
    resolucion: Mapped[str | None] = mapped_column(Text)
    resuelto_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

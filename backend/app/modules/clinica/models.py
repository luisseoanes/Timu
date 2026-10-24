from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, JSONTipo, TimestampMixin, UUIDMixin


class HistoriaClinica(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.14 Entrada de historia clinica por atencion. Solo lectura desde el portal.

    F2-CLI-01 Una entrada firmada no se edita: se corrige con una nueva version que la
    reemplaza (`reemplaza_id`); la anterior queda como `corregida` y sigue consultable.
    """

    __tablename__ = "historias_clinicas"
    __columna_familia__ = "familia_id"

    mascota_id: Mapped[UUID] = mapped_column(ForeignKey("mascotas.id"), index=True)
    # Denormalizado para que el alcance del portal filtre sin unir con mascotas.
    familia_id: Mapped[UUID] = mapped_column(ForeignKey("familias.id"), index=True)
    servicio_id: Mapped[UUID | None] = mapped_column(ForeignKey("servicios.id"))
    profesional_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))
    # presencial | domiciliaria | virtual
    tipo: Mapped[str] = mapped_column(String(16), default="presencial")
    plantilla_codigo: Mapped[str | None] = mapped_column(String(40))
    fecha: Mapped[date] = mapped_column(Date, index=True)
    motivo: Mapped[str] = mapped_column(Text)
    anamnesis: Mapped[str | None] = mapped_column(Text)
    examen_fisico: Mapped[str | None] = mapped_column(Text)
    diagnostico: Mapped[str | None] = mapped_column(Text)
    tratamiento: Mapped[str | None] = mapped_column(Text)
    # Uso interno del equipo medico: nunca sale al portal de la familia.
    notas_internas: Mapped[str | None] = mapped_column(Text)
    # borrador | firmada | corregida
    estado: Mapped[str] = mapped_column(String(16), default="borrador", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    reemplaza_id: Mapped[UUID | None] = mapped_column(ForeignKey("historias_clinicas.id"))
    firmada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    firmada_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))


class AdjuntoClinico(Base, UUIDMixin, TimestampMixin, Auditable):
    """F2-CLI-02 Examen o imagen. El contenido vive en el almacenamiento: se abre solo con
    URL firmada emitida a quien tiene permiso."""

    __tablename__ = "adjuntos_clinicos"

    historia_id: Mapped[UUID] = mapped_column(
        ForeignKey("historias_clinicas.id", ondelete="CASCADE"), index=True
    )
    archivo_id: Mapped[UUID] = mapped_column(ForeignKey("archivos.id"))
    nombre_archivo: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str | None] = mapped_column(String(120))
    descripcion: Mapped[str | None] = mapped_column(String(255))
    subido_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))


class PlantillaConsulta(Base, UUIDMixin, TimestampMixin, Auditable):
    """F2-CLI-03 Punto de partida del profesional por tipo de atencion: textos sugeridos
    para cada campo de la historia, que se editan en la consulta."""

    __tablename__ = "plantillas_consulta"

    codigo: Mapped[str] = mapped_column(String(40), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    tipo_servicio_codigo: Mapped[str | None] = mapped_column(
        ForeignKey("tipos_servicio.codigo"), index=True
    )
    # {"motivo": "...", "anamnesis": "...", "examen_fisico": "...", ...}
    campos: Mapped[dict[str, str]] = mapped_column(JSONTipo, default=dict)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)


class Formula(Base, UUIDMixin, TimestampMixin, Auditable):
    """F2-CLI-03 Formula medica generada desde la historia, con su PDF."""

    __tablename__ = "formulas"

    historia_id: Mapped[UUID] = mapped_column(ForeignKey("historias_clinicas.id"), index=True)
    # [{"medicamento", "presentacion", "dosis", "frecuencia", "duracion", "indicaciones"}]
    items: Mapped[list[dict[str, Any]]] = mapped_column(JSONTipo, default=list)
    indicaciones: Mapped[str | None] = mapped_column(Text)
    archivo_id: Mapped[UUID | None] = mapped_column(ForeignKey("archivos.id"))
    emitida_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))


class RespuestaVirtual(Base, UUIDMixin, TimestampMixin, Auditable):
    """F2-CLI-04 Respuesta tipo de la atencion virtual. Solo una aprobada se usa: el
    profesional elige y completa, no redacta libre lo que sale al usuario."""

    __tablename__ = "respuestas_virtuales"

    codigo: Mapped[str] = mapped_column(String(40), unique=True)
    titulo: Mapped[str] = mapped_column(String(160))
    # Texto con variables {{1}}, {{2}}... como las plantillas de WhatsApp.
    cuerpo: Mapped[str] = mapped_column(Text)
    variables: Mapped[list[str]] = mapped_column(JSONTipo, default=list)
    # borrador | aprobada | retirada
    estado: Mapped[str] = mapped_column(String(16), default="borrador", index=True)
    aprobada_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))
    aprobada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SolicitudVirtual(Base, UUIDMixin, TimestampMixin, Auditable):
    """F2-CLI-04 Consulta de orientacion virtual: entra a una cola que atiende el equipo
    medico; la respuesta queda registrada en la historia de la mascota."""

    __tablename__ = "solicitudes_virtuales"
    __columna_familia__ = "familia_id"

    familia_id: Mapped[UUID] = mapped_column(ForeignKey("familias.id"), index=True)
    mascota_id: Mapped[UUID] = mapped_column(ForeignKey("mascotas.id"), index=True)
    canal: Mapped[str] = mapped_column(String(16), default="portal")  # portal | whatsapp | panel
    motivo: Mapped[str] = mapped_column(Text)
    # en_cola | en_atencion | respondida | cerrada
    estado: Mapped[str] = mapped_column(String(16), default="en_cola", index=True)
    prioridad: Mapped[str] = mapped_column(String(8), default="media")
    asignada_a_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"), index=True)
    tomada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    respuesta_codigo: Mapped[str | None] = mapped_column(String(40))
    respuesta: Mapped[str | None] = mapped_column(Text)
    respondida_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    historia_id: Mapped[UUID | None] = mapped_column(ForeignKey("historias_clinicas.id"))

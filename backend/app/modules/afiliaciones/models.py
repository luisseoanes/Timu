from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.auditoria import Auditable
from app.core.database import Base, EnumDb, JSONTipo, TimestampMixin, UUIDMixin
from app.core.enums import OrigenSolicitudAfiliacion, Periodicidad


class EstadoSolicitud(StrEnum):
    PENDIENTE_PAGO = "pendiente_pago"
    # Registro en linea: el pago llego y falta el formulario con los datos de la familia.
    PAGADA = "pagada"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"
    ERROR = "error"


class SolicitudAfiliacion(Base, UUIDMixin, TimestampMixin, Auditable):
    """F1-AFI-01 Ciclo cotizacion -> pago -> contrato -> perfil. La solicitud guarda lo que
    la familia acepto y el pago que la completa.

    En el registro en linea (6.1) se paga antes de que exista la familia: la solicitud lleva
    la ciudad, el contacto del titular y los peludos con su plan, y la familia se crea con el
    formulario posterior al pago. Ese formulario se abre con un token: el del navegador que
    pago (`token_hash`) o el del enlace que se le envia (`token_enlace_hash`); se guardan
    solo como SHA-256."""

    __tablename__ = "solicitudes_afiliacion"
    __checks__ = {
        "valor_no_negativo": "valor_inicial >= 0",
        "familia_o_contacto": (
            "familia_id IS NOT NULL"
            " OR (contacto_nombre IS NOT NULL AND contacto_telefono IS NOT NULL)"
        ),
        # Como texto: el valor nuevo del enum no se puede usar en la transaccion que lo crea.
        "pagada_con_fecha": "estado::text <> 'pagada' OR pagada_en IS NOT NULL",
        "contacto_telefono_formato": (
            "contacto_telefono IS NULL OR contacto_telefono ~ '^\\+[1-9][0-9]{7,14}$'"
        ),
    }
    __columna_familia__ = "familia_id"

    familia_id: Mapped[UUID | None] = mapped_column(ForeignKey("familias.id"), index=True)
    ciudad: Mapped[str] = mapped_column(
        String(80), ForeignKey("ciudades.nombre", onupdate="CASCADE"), index=True
    )
    contacto_nombre: Mapped[str | None] = mapped_column(String(160))
    contacto_telefono: Mapped[str | None] = mapped_column(String(32))
    contacto_email: Mapped[str | None] = mapped_column(String(255))
    token_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    token_enlace_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    pagada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recordada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    periodicidad: Mapped[str] = mapped_column(EnumDb(Periodicidad), default=Periodicidad.MENSUAL)
    # Lo que cobra la primera cuota, cotizado al iniciar: el pago debe coincidir.
    valor_inicial: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    referencia_pago: Mapped[str] = mapped_column(String(60), unique=True)
    pago_id: Mapped[UUID | None] = mapped_column(ForeignKey("pagos.id"), index=True)
    contrato_id: Mapped[UUID | None] = mapped_column(ForeignKey("contratos.id"), index=True)
    estado: Mapped[str] = mapped_column(
        EnumDb(EstadoSolicitud), default=EstadoSolicitud.PENDIENTE_PAGO, index=True
    )
    origen: Mapped[str] = mapped_column(EnumDb(OrigenSolicitudAfiliacion))  # formulario | asistida
    # F1-AFI-02 Evidencia de aceptacion: medio, version de terminos, fecha, ip, agente.
    aceptacion: Mapped[dict[str, Any]] = mapped_column(JSONTipo, default=dict)
    completada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)

    peludos: Mapped[list["PeludoSolicitud"]] = relationship(
        order_by="PeludoSolicitud.posicion", lazy="selectin", cascade="save-update, merge"
    )


class PeludoSolicitud(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.3 Cada peludo de una solicitud con el plan elegido y lo que paga al mes, tal como
    se cotizo y la familia lo acepto. `mascota_id` falta cuando el pago llega antes de la
    ficha (registro en linea): la mascota se crea al completar el formulario."""

    __tablename__ = "peludos_solicitud"
    __checks__ = {
        "posicion_positiva": "posicion >= 1",
        "nombre_no_vacio": "btrim(nombre) <> ''",
        "valor_no_negativo": "valor_mensual >= 0",
    }
    __unicos__ = {"posicion": (["solicitud_id", "posicion"], None)}
    __columna_familia__ = "familia_id"

    solicitud_id: Mapped[UUID] = mapped_column(ForeignKey("solicitudes_afiliacion.id"), index=True)
    # Vacia hasta que el registro en linea crea la familia.
    familia_id: Mapped[UUID | None] = mapped_column(ForeignKey("familias.id"), index=True)
    posicion: Mapped[int] = mapped_column(Integer)
    mascota_id: Mapped[UUID | None] = mapped_column(ForeignKey("mascotas.id"), index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    especie: Mapped[str] = mapped_column(
        String(40), ForeignKey("especies.codigo", onupdate="CASCADE"), index=True
    )
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("planes.id"), index=True)
    valor_mensual: Mapped[Decimal] = mapped_column(Numeric(12, 2))

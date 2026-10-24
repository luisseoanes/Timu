from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, JSONTipo, TimestampMixin, UUIDMixin


class EstadoSolicitud:
    PENDIENTE_PAGO = "pendiente_pago"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"
    ERROR = "error"


class SolicitudAfiliacion(Base, UUIDMixin, TimestampMixin, Auditable):
    """F1-AFI-01 Ciclo formulario -> pago -> contrato -> perfil. La solicitud guarda lo que
    la familia acepto y el pago que la completa."""

    __tablename__ = "solicitudes_afiliacion"
    __columna_familia__ = "familia_id"

    familia_id: Mapped[UUID] = mapped_column(ForeignKey("familias.id"), index=True)
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("planes.id"))
    valor_inicial: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    referencia_pago: Mapped[str] = mapped_column(String(60), unique=True)
    pago_id: Mapped[UUID | None] = mapped_column(ForeignKey("pagos.id"))
    contrato_id: Mapped[UUID | None] = mapped_column(ForeignKey("contratos.id"))
    estado: Mapped[str] = mapped_column(
        String(24), default=EstadoSolicitud.PENDIENTE_PAGO, index=True
    )
    origen: Mapped[str] = mapped_column(String(24))  # formulario | asistida
    # F1-AFI-02 Evidencia de aceptacion: medio, version de terminos, fecha, ip, agente.
    aceptacion: Mapped[dict[str, Any]] = mapped_column(JSONTipo, default=dict)
    completada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)

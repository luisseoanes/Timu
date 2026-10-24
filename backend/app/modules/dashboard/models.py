from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, JSONTipo, TimestampMixin, UUIDMixin


class ReporteProgramado(Base, UUIDMixin, TimestampMixin, Auditable):
    """F4-DAS-03 Reporte que llega solo por correo, con el periodo anterior en Excel."""

    __tablename__ = "reportes_programados"

    nombre: Mapped[str] = mapped_column(String(160))
    # diaria | semanal (lunes) | mensual (dia 1)
    periodicidad: Mapped[str] = mapped_column(String(12))
    destinatarios: Mapped[list[str]] = mapped_column(JSONTipo, default=list)
    indicadores: Mapped[list[str]] = mapped_column(JSONTipo, default=list)  # vacio = todos
    ciudad: Mapped[str | None] = mapped_column(String(80))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    ultimo_envio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ultimo_error: Mapped[str | None] = mapped_column(Text)
    creado_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))

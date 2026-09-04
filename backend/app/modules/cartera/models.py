from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDMixin
from app.core.enums import EstadoAfiliacion, EstadoPago


class Contrato(Base, UUIDMixin, TimestampMixin):
    """6.2 / 6.4 Contrato de afiliacion: base de cartera y de la renovacion anual."""

    __tablename__ = "contratos"

    familia_id: Mapped[UUID] = mapped_column(ForeignKey("familias.id"), index=True)
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("planes.id"), index=True)
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_renovacion: Mapped[date] = mapped_column(Date, index=True)
    valor_mensual: Mapped[float] = mapped_column(Numeric(12, 2))
    dia_corte: Mapped[int] = mapped_column(default=1)
    estado: Mapped[EstadoAfiliacion] = mapped_column(
        String(32), default=EstadoAfiliacion.ACTIVA, index=True
    )


class Cuota(Base, UUIDMixin, TimestampMixin):
    """6.2 Cuota mensual. El worker de cartera marca mora y dispara congelamiento."""

    __tablename__ = "cuotas"

    contrato_id: Mapped[UUID] = mapped_column(ForeignKey("contratos.id"), index=True)
    periodo: Mapped[str] = mapped_column(String(7), index=True)  # YYYY-MM
    fecha_vencimiento: Mapped[date] = mapped_column(Date, index=True)
    valor: Mapped[float] = mapped_column(Numeric(12, 2))
    estado: Mapped[EstadoPago] = mapped_column(String(24), default=EstadoPago.PENDIENTE, index=True)
    dias_mora: Mapped[int] = mapped_column(default=0)


class Pago(Base, UUIDMixin, TimestampMixin):
    """Pago conciliado desde el webhook de la pasarela (Wompi / PayU)."""

    __tablename__ = "pagos"

    cuota_id: Mapped[UUID | None] = mapped_column(ForeignKey("cuotas.id"), index=True)
    familia_id: Mapped[UUID] = mapped_column(ForeignKey("familias.id"), index=True)
    referencia_externa: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    proveedor: Mapped[str] = mapped_column(String(32), default="wompi")
    valor: Mapped[float] = mapped_column(Numeric(12, 2))
    estado: Mapped[EstadoPago] = mapped_column(String(24), default=EstadoPago.PENDIENTE, index=True)
    payload: Mapped[str | None] = mapped_column(Text)

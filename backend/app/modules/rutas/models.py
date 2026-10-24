from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.auditoria import Auditable
from app.core.database import Base, JSONTipo, TimestampMixin, UUIDMixin


class Ruta(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.7 Ruta domiciliaria del dia de un tecnico, con secuencia optimizada."""

    __tablename__ = "rutas"

    fecha: Mapped[date] = mapped_column(Date, index=True)
    ciudad: Mapped[str] = mapped_column(String(80), index=True)
    responsable_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"), index=True)
    planificacion_id: Mapped[UUID | None] = mapped_column(ForeignKey("planificaciones_ruta.id"))
    # planificada | en_curso | finalizada | cancelada
    estado: Mapped[str] = mapped_column(String(24), default="planificada", index=True)
    distancia_km: Mapped[float | None] = mapped_column()
    duracion_min: Mapped[int | None] = mapped_column(Integer)
    inicio_real: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fin_real: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    paradas: Mapped[list["ParadaRuta"]] = relationship(
        back_populates="ruta",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ParadaRuta.orden",
    )


class ParadaRuta(Base, UUIDMixin, TimestampMixin, Auditable):
    """Una visita de la ruta. F2-RUT-04 registra llegada, salida y evidencia."""

    __tablename__ = "paradas_ruta"

    ruta_id: Mapped[UUID] = mapped_column(ForeignKey("rutas.id", ondelete="CASCADE"), index=True)
    servicio_id: Mapped[UUID] = mapped_column(ForeignKey("servicios.id"), index=True)
    orden: Mapped[int] = mapped_column(Integer)
    latitud: Mapped[float | None] = mapped_column()
    longitud: Mapped[float | None] = mapped_column()
    # pendiente | en_camino | en_sitio | completada | omitida
    estado: Mapped[str] = mapped_column(String(16), default="pendiente", index=True)
    llegada_estimada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    llegada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    salida_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidencia_archivo_id: Mapped[UUID | None] = mapped_column(ForeignKey("archivos.id"))
    nota: Mapped[str | None] = mapped_column(Text)
    motivo_omision: Mapped[str | None] = mapped_column(String(255))
    # F2-RUT-06 Avisos a la familia (una sola vez cada uno).
    aviso_ventana_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    aviso_en_camino_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    ruta: Mapped[Ruta] = relationship(back_populates="paradas")


class PlanificacionRuta(Base, UUIDMixin, TimestampMixin):
    """F2-RUT-01 Solicitud de planear el dia de una ciudad. La optimizacion corre en el
    worker; aqui queda su estado y lo que no se pudo asignar, con el motivo."""

    __tablename__ = "planificaciones_ruta"

    fecha: Mapped[date] = mapped_column(Date, index=True)
    ciudad: Mapped[str] = mapped_column(String(80))
    responsables: Mapped[list[str]] = mapped_column(JSONTipo, default=list)
    # pendiente | lista | fallida
    estado: Mapped[str] = mapped_column(String(16), default="pendiente", index=True)
    resultado: Mapped[dict[str, Any]] = mapped_column(JSONTipo, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    solicitada_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))


class DistanciaCache(Base, UUIDMixin, TimestampMixin):
    """F2-RUT-02 Tiempo de viaje real entre dos puntos (redondeados a ~10 m). Distance
    Matrix se factura por consulta: un par ya conocido no se vuelve a pedir."""

    __tablename__ = "distancias_cache"
    __table_args__ = (UniqueConstraint("origen", "destino"),)

    origen: Mapped[str] = mapped_column(String(32))
    destino: Mapped[str] = mapped_column(String(32))
    metros: Mapped[int] = mapped_column(Integer)
    segundos: Mapped[int] = mapped_column(Integer)


class ConsumoMapas(Base, UUIDMixin, TimestampMixin):
    """F2-RUT-02 Elementos consultados por dia, contra MAPS_TOPE_DIARIO."""

    __tablename__ = "consumo_mapas"

    fecha: Mapped[date] = mapped_column(Date, unique=True)
    elementos: Mapped[int] = mapped_column(Integer, default=0)

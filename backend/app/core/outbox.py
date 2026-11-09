"""Patron outbox: el efecto externo no se dispara hasta que la transaccion existe.

El problema que resuelve: si un servicio hace `tarea.delay()` y despues la transaccion
revienta, el WhatsApp ya salio y el dato no existe. Con pagos y mensajeria a clientes
reales eso son incidencias, no teoria.

La solucion: el evento se ESCRIBE en esta tabla dentro de la misma transaccion que el
cambio de datos. Si la transaccion revienta, el evento se va con ella. Un worker drena
la tabla despues con `procesar_pendientes` (la tarea `outbox.drenar` la invoca).
"""

from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import DateTime, Integer, String, Text, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.database import Base, JSONTipo, TimestampMixin, UUIDMixin
from app.core.eventos import EventoDominio, manejadores

logger = structlog.get_logger(__name__)

LOTE = 100
MAX_INTENTOS = 5


class EventoSaliente(Base, UUIDMixin, TimestampMixin):
    """Evento pendiente de despachar. Se inserta en la transaccion que lo origina."""

    __tablename__ = "eventos_salientes"
    __checks__ = {
        "intentos_no_negativos": "intentos >= 0",
    }

    nombre: Mapped[str] = mapped_column(String(80), index=True)
    datos: Mapped[dict[str, Any]] = mapped_column(JSONTipo, default=dict)
    procesado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    intentos: Mapped[int] = mapped_column(Integer, default=0)
    ultimo_error: Mapped[str | None] = mapped_column(Text)


def publicar(db: Any, evento: EventoDominio) -> EventoSaliente:
    """Encola el evento en la transaccion en curso. NO lo despacha.

    Sirve igual con sesion async (endpoints) o sincrona (workers): solo hace `add`,
    que no es una operacion de entrada/salida. El commit lo cierra quien corresponda:
    `get_db` en una peticion, `sesion_worker` en una tarea.
    """
    fila = EventoSaliente(nombre=evento.nombre, datos=evento.datos)
    db.add(fila)
    return fila


def procesar_pendientes(db: Session, lote: int = LOTE) -> dict[str, int]:
    """Despacha los eventos pendientes con sus manejadores y los marca como procesados.

    `with_for_update(skip_locked=True)` permite que varios workers drenen a la vez sin
    pisarse: cada uno se lleva las filas que el otro no bloqueo. Un manejador que falla
    deja la fila pendiente con el error anotado y se reintenta en el siguiente drenado,
    hasta MAX_INTENTOS. La entrega es al menos una vez: si un evento tiene dos manejadores
    y falla el segundo, el primero se repite en el reintento.

    No confirma: lo hace quien abre la sesion (`sesion_worker` en la tarea).
    """
    despachados = fallidos = 0
    pendientes = db.scalars(
        select(EventoSaliente)
        .where(EventoSaliente.procesado_en.is_(None))
        .where(EventoSaliente.intentos < MAX_INTENTOS)
        .order_by(EventoSaliente.created_at)
        .limit(lote)
        .with_for_update(skip_locked=True)
    ).all()

    for fila in pendientes:
        evento = EventoDominio(nombre=fila.nombre, datos=fila.datos)
        try:
            for manejador in manejadores(fila.nombre):
                manejador(evento)
            fila.procesado_en = datetime.now(UTC)
            despachados += 1
        except Exception as exc:  # noqa: BLE001  se reintenta hasta MAX_INTENTOS
            fila.intentos += 1
            fila.ultimo_error = str(exc)[:2000]
            fallidos += 1
            if fila.intentos >= MAX_INTENTOS:
                # No se vuelve a intentar: el efecto no ocurre si nadie lo mira. Como error
                # llega a Sentry; la fila queda con su `ultimo_error` para reprocesarla.
                logger.error(
                    "outbox.abandonado", evento=fila.nombre, evento_id=str(fila.id), error=str(exc)
                )
            else:
                logger.warning("outbox.fallo", evento=fila.nombre, error=str(exc))
    db.flush()
    return {"despachados": despachados, "fallidos": fallidos}

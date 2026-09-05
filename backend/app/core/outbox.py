"""Patron outbox: el efecto externo no se dispara hasta que la transaccion existe.

El problema que resuelve: si un servicio hace `tarea.delay()` y despues la transaccion
revienta, el WhatsApp ya salio y el dato no existe. Con pagos y mensajeria a clientes
reales eso son incidencias, no teoria.

La solucion: el evento se ESCRIBE en esta tabla dentro de la misma transaccion que el
cambio de datos. Si la transaccion revienta, el evento se va con ella. Un worker drena
la tabla despues (ver app/workers/tasks/outbox.py).
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, JSONTipo, TimestampMixin, UUIDMixin
from app.core.eventos import EventoDominio


class EventoSaliente(Base, UUIDMixin, TimestampMixin):
    """Evento pendiente de despachar. Se inserta en la transaccion que lo origina."""

    __tablename__ = "eventos_salientes"

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

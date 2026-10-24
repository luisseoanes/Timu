"""F0-04 Bitacora de auditoria.

Todo modelo que herede `Auditable` deja rastro de cada alta, edicion, cambio de estado o
borrado: quien (usuario autenticado), cuando, desde que peticion y el valor anterior y
nuevo de cada campo modificado. Se registra en el mismo flush, dentro de la misma
transaccion: si la operacion se revierte, su rastro tambien.
"""

import enum
from contextvars import ContextVar
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy import DateTime, Index, String, event, func, insert, inspect
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.database import Base, JSONTipo
from app.core.observabilidad import id_peticion

logger = structlog.get_logger(__name__)

usuario_actual_ctx: ContextVar[UUID | None] = ContextVar("usuario_actual", default=None)

# Columnas que cambian solas y no aportan al rastro.
_IGNORADAS = {"created_at", "updated_at", "hashed_password"}


class Accion(enum.StrEnum):
    CREAR = "crear"
    EDITAR = "editar"
    CAMBIO_ESTADO = "cambio_estado"
    ELIMINAR = "eliminar"


class Auditable:
    """Marca un modelo para la bitacora. Debe tener columna `id`."""


class RegistroAuditoria(Base):
    __tablename__ = "auditoria"
    __table_args__ = (Index("ix_auditoria_entidad", "entidad", "entidad_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # Sin llave foranea a usuarios: el rastro sobrevive aunque el usuario se elimine.
    usuario_id: Mapped[UUID | None] = mapped_column(index=True)
    request_id: Mapped[str | None] = mapped_column(String(64))
    entidad: Mapped[str] = mapped_column(String(64))
    entidad_id: Mapped[str] = mapped_column(String(64))
    accion: Mapped[Accion] = mapped_column(String(24))
    cambios: Mapped[dict[str, Any]] = mapped_column(JSONTipo, default=dict)


def _serializar(valor: Any) -> Any:
    if isinstance(valor, enum.Enum):
        return valor.value
    if valor is None or isinstance(valor, bool | int | float | str):
        return valor
    if isinstance(valor, UUID | Decimal):
        return str(valor)
    if isinstance(valor, datetime | date):
        return valor.isoformat()
    if isinstance(valor, list | tuple):
        return [_serializar(v) for v in valor]
    if isinstance(valor, dict):
        return {str(k): _serializar(v) for k, v in valor.items()}
    return str(valor)


def _columnas(obj: Any) -> list[str]:
    return [c.key for c in inspect(obj).mapper.column_attrs if c.key not in _IGNORADAS]


def _cambios_edicion(obj: Any) -> dict[str, list[Any]]:
    estado = inspect(obj)
    cambios = {}
    for clave in _columnas(obj):
        hist = estado.attrs[clave].history
        if not hist.has_changes():
            continue
        antes = hist.deleted[0] if hist.deleted else None
        despues = hist.added[0] if hist.added else None
        if _serializar(antes) != _serializar(despues):
            cambios[clave] = [_serializar(antes), _serializar(despues)]
    return cambios


def _fila(obj: Any, accion: Accion, cambios: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": uuid4(),
        # Reloj de pared y no el server_default: en PostgreSQL now() es la hora de inicio
        # de la transaccion, y varios cambios de una misma peticion quedarian empatados.
        "created_at": datetime.now(UTC),
        "usuario_id": usuario_actual_ctx.get(),
        "request_id": id_peticion.get() if id_peticion.get() != "-" else None,
        "entidad": obj.__tablename__,
        "entidad_id": str(obj.id),
        "accion": accion.value,
        "cambios": cambios,
    }


@event.listens_for(Session, "after_flush")
def _registrar(session: Session, _flush_context: Any) -> None:
    filas: list[dict[str, Any]] = []
    for obj in session.new:
        if isinstance(obj, Auditable):
            valores = {c: [None, _serializar(getattr(obj, c))] for c in _columnas(obj)}
            filas.append(_fila(obj, Accion.CREAR, valores))
    for obj in session.dirty:
        if isinstance(obj, Auditable) and session.is_modified(obj, include_collections=False):
            cambios = _cambios_edicion(obj)
            if cambios:
                accion = Accion.CAMBIO_ESTADO if "estado" in cambios else Accion.EDITAR
                filas.append(_fila(obj, accion, cambios))
    for obj in session.deleted:
        if isinstance(obj, Auditable):
            valores = {c: [_serializar(getattr(obj, c)), None] for c in _columnas(obj)}
            filas.append(_fila(obj, Accion.ELIMINAR, valores))
    if filas:
        # Insert directo sobre la conexion del flush: agregar objetos a la sesion aqui
        # no esta soportado por SQLAlchemy.
        session.connection().execute(insert(RegistroAuditoria), filas)

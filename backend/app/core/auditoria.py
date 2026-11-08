"""F0-04 Bitacora de auditoria, escrita por la base (fase 2g de docs/plan-persistencia.md).

Todo modelo que herede `Auditable` lleva el trigger `tr_<tabla>_auditoria`: cada alta,
edicion, cambio de estado o borrado deja rastro de quien (`app.usuario_id` del contexto de
la transaccion), cuando, desde que peticion (`app.request_id`) y el valor anterior y nuevo
de cada campo. Lo escribe la funcion `auditar()` de la base, asi que tambien queda rastro de
un UPDATE por SQL, de un script o de una migracion: nada lo salta. Va en la misma
transaccion; si la operacion se revierte, su rastro tambien.

La bitacora solo admite inserciones. La aplicacion puede leerla pero no escribirla, editarla
ni borrarla (la escribe `auditar()` como dueno del esquema), y un trigger rechaza cualquier
UPDATE o DELETE que no venga del dueno.

Formato de `cambios`, el mismo que tenia cuando lo escribia Python: `{"campo": [antes,
despues]}`, con todos los campos al crear o borrar y solo los que cambian al editar. Los
importes van como texto ("45000.00"); `created_at`, `updated_at` y `hashed_password` no se
registran.
"""

import enum
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, EnumDb, JSONTipo, UUIDMixin


class Accion(enum.StrEnum):
    CREAR = "crear"
    EDITAR = "editar"
    CAMBIO_ESTADO = "cambio_estado"
    ELIMINAR = "eliminar"


class Auditable:
    """Marca un modelo para la bitacora: su tabla lleva el trigger de auditoria. Debe tener
    columna `id`. `test_persistencia` falla si un modelo Auditable no tiene su trigger."""


# Tablas cuyas filas no cambian una vez escritas (trigger `inmutable`), con las columnas
# que si pueden cambiar. La historia clinica tiene su propia regla: inmutable desde que se
# firma, salvo pasar a `corregida` (`historia_firmada_inmutable`).
INMUTABLES: dict[str, tuple[str, ...]] = {
    "auditoria": (),
    "carnets_emitidos": (),
    "aplicaciones_pago": (),
    "formulas": (),
    "adjuntos_clinicos": (),
    "cambios_plan": ("aplicado",),
}


class RegistroAuditoria(Base, UUIDMixin):
    __tablename__ = "auditoria"
    __table_args__ = (Index("ix_auditoria_entidad", "entidad", "entidad_id", "created_at"),)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # Sin llave foranea a usuarios: el rastro sobrevive aunque el usuario se elimine.
    usuario_id: Mapped[UUID | None] = mapped_column(index=True)
    request_id: Mapped[str | None] = mapped_column(String(64))
    entidad: Mapped[str] = mapped_column(String(64))
    entidad_id: Mapped[str] = mapped_column(String(64))
    accion: Mapped[Accion] = mapped_column(EnumDb(Accion))
    cambios: Mapped[dict[str, Any]] = mapped_column(JSONTipo, default=dict)

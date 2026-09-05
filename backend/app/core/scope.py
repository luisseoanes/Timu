"""Autorizacion a nivel de fila.

`require_roles` responde a "que perfil puede llamar a este endpoint". Esto responde
a la otra pregunta, la del portal de familias (6.x, F1-AUT-04): "que filas puede ver
ESTE usuario". Son cosas distintas y las dos hacen falta.

Regla: **todo listado y toda lectura por id pasa por `restringir()`**. Un servicio que
consulte sin alcance es un defecto de seguridad, no un descuido de estilo.

Como se declara: cada modelo visible desde el portal expone `__columna_familia__` con
el nombre de la columna que lo ata a una familia. Un modelo que no lo declare hace
fallar la consulta cuando el sujeto es una familia — se falla cerrado, nunca abierto.
"""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import Select

from app.core.enums import Rol


class AlcanceNoDefinido(Exception):
    """El modelo no declara `__columna_familia__` y el sujeto es una familia."""


@dataclass(frozen=True)
class Alcance:
    """Sujeto de la peticion, ya resuelto: quien es y que puede ver."""

    usuario_id: UUID
    rol: Rol
    familia_id: UUID | None = None

    @property
    def es_interno(self) -> bool:
        """El personal de TIMU ve toda la operacion; la familia solo lo suyo."""
        return self.rol != Rol.FAMILIA


def restringir(stmt: Select[Any], modelo: type, alcance: Alcance) -> Select[Any]:
    """Anade al SELECT el filtro de fila que corresponde al sujeto.

    Para un usuario interno devuelve la consulta intacta. Para una familia la limita
    a sus propias filas, y si el modelo no declara como atarse a una familia, levanta
    AlcanceNoDefinido en vez de devolver datos de mas.
    """
    if alcance.es_interno:
        return stmt

    if alcance.familia_id is None:
        raise AlcanceNoDefinido(
            f"Usuario {alcance.usuario_id} tiene rol familia pero no hay familia asociada"
        )

    nombre_columna = getattr(modelo, "__columna_familia__", None)
    if nombre_columna is None:
        raise AlcanceNoDefinido(
            f"{modelo.__name__} no declara __columna_familia__: no se puede acotar "
            f"la consulta al portal de familias"
        )
    return stmt.where(getattr(modelo, nombre_columna) == alcance.familia_id)


def permite(obj: object, alcance: Alcance) -> bool:
    """Comprueba un objeto ya cargado (lecturas por id, que no pasan por un SELECT
    filtrado). Misma politica: interno si, familia solo lo suyo."""
    if alcance.es_interno:
        return True
    nombre_columna = getattr(type(obj), "__columna_familia__", None)
    if nombre_columna is None:
        raise AlcanceNoDefinido(f"{type(obj).__name__} no declara __columna_familia__")
    return getattr(obj, nombre_columna) == alcance.familia_id

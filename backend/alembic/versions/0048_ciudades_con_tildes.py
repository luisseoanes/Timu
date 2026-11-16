"""catalogos: las ciudades y departamentos con sus tildes

Las ciudades se sembraron sin tildes («Bogota», «Medellin») y son la clave por la que se guarda
la ciudad de familias, planes, servicios, franjas, rutas y aliadas. Decidido con el usuario el
2026-11-16: llevan sus tildes. Las llaves foraneas tienen ON UPDATE CASCADE, asi que renombrar
la ciudad del catalogo la propaga sola. Lo que no es llave foranea se corrige aqui: la ciudad
del interesado (texto libre) y las listas de ciudades de segmentos, campanas y reglas, que
guardan el nombre dentro de un JSON. Como en la 0045, solo se cambia lo que sigue igual que se
sembro. `datos.py` ya trae los nombres nuevos.

Revision ID: 0048
Revises: 0047
Create Date: 2026-11-16 20:00:00
"""

import json
from typing import Any

import sqlalchemy as sa

from alembic import op

revision = "0048"
down_revision = "0047"
branch_labels = None
depends_on = None

# codigo DANE: (nombre sembrado, nombre con tildes)
CIUDADES = {
    "11001": ("Bogota", "Bogotá"),
    "05001": ("Medellin", "Medellín"),
    "54001": ("Cucuta", "Cúcuta"),
    "73001": ("Ibague", "Ibagué"),
    "05360": ("Itagui", "Itagüí"),
    "25175": ("Chia", "Chía"),
}
DEPARTAMENTOS = {
    "Bogota D.C.": "Bogotá D.C.",
    "Atlantico": "Atlántico",
    "Bolivar": "Bolívar",
    "Quindio": "Quindío",
    "Narino": "Nariño",
}
# Columnas JSON que pueden nombrar una ciudad.
JSON = [("segmentos", "filtros"), ("campanas", "segmento"), ("reglas", "condicion")]


def _cambiar(valor: Any, nombres: dict[str, str]) -> Any:
    """El mismo JSON con cada texto que sea exactamente un nombre viejo cambiado."""
    if isinstance(valor, str):
        return nombres.get(valor, valor)
    if isinstance(valor, list):
        return [_cambiar(v, nombres) for v in valor]
    if isinstance(valor, dict):
        return {k: _cambiar(v, nombres) for k, v in valor.items()}
    return valor


def _aplicar(hacia_nuevo: bool) -> None:
    conexion = op.get_bind()
    nombres = {(v if hacia_nuevo else n): (n if hacia_nuevo else v) for v, n in CIUDADES.values()}
    for codigo, (viejo, nuevo) in CIUDADES.items():
        desde, hacia = (viejo, nuevo) if hacia_nuevo else (nuevo, viejo)
        conexion.execute(
            sa.text("UPDATE ciudades SET nombre = :hacia WHERE codigo = :c AND nombre = :desde"),
            {"hacia": hacia, "c": codigo, "desde": desde},
        )
    for viejo, nuevo in DEPARTAMENTOS.items():
        desde, hacia = (viejo, nuevo) if hacia_nuevo else (nuevo, viejo)
        conexion.execute(
            sa.text("UPDATE ciudades SET departamento = :hacia WHERE departamento = :desde"),
            {"hacia": hacia, "desde": desde},
        )
    for desde, hacia in nombres.items():
        conexion.execute(
            sa.text("UPDATE interesados SET ciudad = :hacia WHERE ciudad = :desde"),
            {"hacia": hacia, "desde": desde},
        )
    for tabla, columna in JSON:
        filas = conexion.execute(
            sa.text(f"SELECT id, {columna} FROM {tabla} WHERE {columna} IS NOT NULL")  # noqa: S608
        ).all()
        for fila_id, valor in filas:
            cambiado = _cambiar(valor, nombres)
            if cambiado != valor:
                conexion.execute(
                    sa.text(
                        f"UPDATE {tabla} SET {columna} = CAST(:v AS jsonb) WHERE id = :i"  # noqa: S608
                    ),
                    {"v": json.dumps(cambiado, ensure_ascii=False), "i": fila_id},
                )


def upgrade() -> None:
    _aplicar(hacia_nuevo=True)


def downgrade() -> None:
    _aplicar(hacia_nuevo=False)

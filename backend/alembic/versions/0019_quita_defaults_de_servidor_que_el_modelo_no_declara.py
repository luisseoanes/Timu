"""quita defaults de servidor que el modelo no declara

Diecinueve columnas conservaban un DEFAULT de servidor que solo sirvio para rellenar las
filas existentes al anadir la columna. El modelo no los declara (los valores por defecto
van en Python), asi que el esquema y el modelo decian cosas distintas y la prueba de
deriva no lo veia: no comparaba los defaults de servidor. Ahora los compara. Algunos eran
peligrosos para un INSERT por SQL: contratos.valor_plan = 0 creaba un contrato con el plan
gratis. Igual que en la 0015, se eliminan y el downgrade los repone.

Revision ID: 0019
Revises: 0018
Create Date: 2026-11-04 22:00:00
"""

from alembic import op

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None

# (tabla, columna, DEFAULT anterior)
DEFAULTS_ANTERIORES: list[tuple[str, str, str]] = [
    ("campanas", "variables", "'[]'::jsonb"),
    ("contratos", "evidencia_aceptacion", "'{}'::jsonb"),
    ("contratos", "mascotas_adicionales", "0"),
    ("contratos", "saldo_a_favor", "'0'::numeric"),
    ("contratos", "valor_adicional_mascota", "'0'::numeric"),
    ("contratos", "valor_plan", "'0'::numeric"),
    ("cuotas", "tipo", "'mensual'::character varying"),
    ("cuotas", "valor_pagado", "'0'::numeric"),
    ("eventos_preventivos", "dosis_numero", "1"),
    ("eventos_preventivos", "es_refuerzo", "false"),
    ("familias", "origen", "'panel'::character varying"),
    ("historias_clinicas", "version", "1"),
    ("mascotas", "activa", "true"),
    ("mensajes", "intentos", "0"),
    ("mensajes", "masivo", "false"),
    ("mensajes", "variables", "'[]'::jsonb"),
    ("pagos", "aplicado", "false"),
    ("planes", "especies", "'[]'::jsonb"),
    ("tokens_uso_unico", "intentos", "0"),
]


def upgrade() -> None:
    for tabla, columna, _ in DEFAULTS_ANTERIORES:
        op.execute(f"ALTER TABLE {tabla} ALTER COLUMN {columna} DROP DEFAULT")


def downgrade() -> None:
    for tabla, columna, valor in DEFAULTS_ANTERIORES:
        op.execute(f"ALTER TABLE {tabla} ALTER COLUMN {columna} SET DEFAULT {valor}")

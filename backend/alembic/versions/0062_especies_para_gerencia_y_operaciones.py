# ruff: noqa: E501  (politicas congeladas: expresiones SQL largas)
"""catalogos: Gerencia y Operaciones leen las especies

Seccion 12: el catalogo de especies es configuracion, no datos de nadie, pero la matriz de
app/core/permisos_db.py no se lo daba a Gerencia ni a Operaciones. La base no les negaba la
lectura: les devolvia el catalogo vacio, y el panel decia «canino» en vez de «Canino» y dejaba sin
opciones el selector de especie. Lo encontro la revision por perfiles del 2026-11-20. Politica
escrita aqui, congelada.

Revision ID: 0062
Revises: 0061
Create Date: 2026-11-20 18:00:00
"""

from alembic import op

revision = "0062"
down_revision = "0061"
branch_labels = None
depends_on = None

ANTES = "app_rol() IN ('sistema', 'admin', 'aliada', 'atencion_cliente', 'comercial', 'familia', 'medico', 'publico')"
DESPUES = "app_rol() IN ('sistema', 'admin', 'aliada', 'atencion_cliente', 'comercial', 'familia', 'gerencia', 'medico', 'operaciones', 'publico')"


def _literal(texto: str) -> str:
    return "'" + texto.replace("'", "''") + "'"


def _alterar(usar: str) -> None:
    op.execute(f"ALTER POLICY p_especies_select ON especies USING ({usar})")
    texto = f"USING ({usar}) WITH CHECK (None)"
    op.execute(f"COMMENT ON POLICY p_especies_select ON especies IS {_literal(texto)}")


def upgrade() -> None:
    _alterar(DESPUES)


def downgrade() -> None:
    _alterar(ANTES)

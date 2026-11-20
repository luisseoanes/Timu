# ruff: noqa: E501  (politicas congeladas: expresiones SQL largas)
"""cartera: Atencion al cliente crea la cuota de ajuste de un cambio de plan

6.3 El cambio de plan de un peludo es de Atencion al cliente (`POST /planes/contratos/{id}/cambio`),
y cuando el plan sube con prorrateo diario el servicio crea una cuota de ajuste. La matriz de
app/core/permisos_db.py no le daba INSERT sobre `cuotas` y el cambio terminaba en un 500. Lo
encontro la revision por perfiles del 2026-11-20. Politica escrita aqui, congelada.

Revision ID: 0063
Revises: 0062
Create Date: 2026-11-20 19:00:00
"""

from alembic import op

revision = "0063"
down_revision = "0062"
branch_labels = None
depends_on = None

ANTES = "app_rol() IN ('sistema', 'comercial')"
DESPUES = "app_rol() IN ('sistema', 'atencion_cliente', 'comercial')"


def _literal(texto: str) -> str:
    return "'" + texto.replace("'", "''") + "'"


def _alterar(comprobar: str) -> None:
    op.execute(f"ALTER POLICY p_cuotas_insert ON cuotas WITH CHECK ({comprobar})")
    texto = f"USING (None) WITH CHECK ({comprobar})"
    op.execute(f"COMMENT ON POLICY p_cuotas_insert ON cuotas IS {_literal(texto)}")


def upgrade() -> None:
    _alterar(DESPUES)


def downgrade() -> None:
    _alterar(ANTES)

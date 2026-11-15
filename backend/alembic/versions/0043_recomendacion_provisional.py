"""reglas: apaga las recomendaciones de planes que ya no existen

Las reglas `plan.recomendacion` sembradas recomendaban `familiar` e `individual`, planes que ya
no existen, y el bot caia siempre en el de menor valor. Mientras TIMU no diga el criterio, la
recomendacion provisional es Mi Amigo Fiel (`recomendar_mi_amigo_fiel`, que inserta
`inicializar` desde `reglas/datos.py`). Aqui se apagan las dos viejas, solo si siguen
apuntando a esos planes: si alguien ya las edito, son de TIMU y se respetan.

Revision ID: 0043
Revises: 0042
Create Date: 2026-11-15 12:00:00
"""

from alembic import op

revision = "0043"
down_revision = "0042"
branch_labels = None
depends_on = None

_VIEJAS = (
    "(codigo = 'recomendar_familiar' AND accion->>'plan_codigo' = 'familiar')"
    " OR (codigo = 'recomendar_individual' AND accion->>'plan_codigo' = 'individual')"
)


def upgrade() -> None:
    op.execute(f"UPDATE reglas SET activa = false WHERE {_VIEJAS}")


def downgrade() -> None:
    op.execute(f"UPDATE reglas SET activa = true WHERE {_VIEJAS}")

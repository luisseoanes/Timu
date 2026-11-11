"""eventos_preventivos: peso de la mascota el dia de la aplicacion

6.8 pide registrar el peso cuando sea pertinente (F2-PRE-07). Se guarda en cada aplicacion y
el carnet lo muestra junto a cada desparasitacion. Opcional: las filas ya aplicadas quedan sin
peso, y el CHECK solo exige que, si lo hay, sea positivo.

Revision ID: 0039
Revises: 0038
Create Date: 2026-11-11 20:10:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0039"
down_revision = "0038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("eventos_preventivos", sa.Column("peso_kg", sa.Float(), nullable=True))
    op.execute(
        "ALTER TABLE eventos_preventivos ADD CONSTRAINT ck_eventos_preventivos_peso_positivo "
        "CHECK (peso_kg IS NULL OR peso_kg > 0)"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE eventos_preventivos DROP CONSTRAINT ck_eventos_preventivos_peso_positivo"
    )
    op.drop_column("eventos_preventivos", "peso_kg")

"""eventos_preventivos: nombre de quien aplico, como el sello del carnet

El carnet muestra quien aplico cada preventivo, como el sello del veterinario del carnet
impreso. Se guarda el nombre al aplicar, como constancia: no cambia si el usuario cambia de
nombre o se va, y la familia lo ve en su portal sin leer la tabla de usuarios. Las aplicaciones
anteriores lo toman del usuario que las registro.

Revision ID: 0040
Revises: 0039
Create Date: 2026-11-11 21:30:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0040"
down_revision = "0039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "eventos_preventivos",
        sa.Column("aplicado_por_nombre", sa.String(length=160), nullable=True),
    )
    op.execute(
        "UPDATE eventos_preventivos e SET aplicado_por_nombre = u.nombre"
        " FROM usuarios u WHERE u.id = e.aplicado_por_id"
    )


def downgrade() -> None:
    op.drop_column("eventos_preventivos", "aplicado_por_nombre")

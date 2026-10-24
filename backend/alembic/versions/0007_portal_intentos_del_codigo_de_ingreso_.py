"""portal: intentos del codigo de ingreso por whatsapp

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-23 21:33:45.676562
"""

import sqlalchemy as sa

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tokens_uso_unico", sa.Column("intentos", sa.Integer(), nullable=False, server_default="0")
    )


def downgrade() -> None:
    op.drop_column("tokens_uso_unico", "intentos")

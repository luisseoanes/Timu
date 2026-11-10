"""planes: color con el que la interfaz reconoce cada plan

Rediseno del panel (R1-PLA-01, docs/hoja-de-ruta-rediseno.md). Cada plan toma uno de los
colores del logo (docs/manual-de-marca.md, secciones 4 y 10) y la interfaz lo lee de aqui, no
del nombre del plan. Los tres planes de TIMU quedan con el color que propone el manual; uno
creado a mano queda en verde hasta que el administrador lo cambie.

Revision ID: 0038
Revises: 0037
Create Date: 2026-11-10 23:30:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0038"
down_revision = "0037"
branch_labels = None
depends_on = None

COLOR_PLAN = postgresql.ENUM("verde", "naranja", "azul", name="color_plan")


def upgrade() -> None:
    COLOR_PLAN.create(op.get_bind())
    op.add_column(
        "planes",
        sa.Column(
            "color",
            postgresql.ENUM(name="color_plan", create_type=False),
            server_default="verde",
            nullable=False,
        ),
    )
    op.execute("UPDATE planes SET color = 'naranja' WHERE codigo = 'colita_feliz'")
    op.execute("UPDATE planes SET color = 'azul' WHERE codigo = 'amigos_por_siempre'")
    op.alter_column("planes", "color", server_default=None)


def downgrade() -> None:
    op.drop_column("planes", "color")
    COLOR_PLAN.drop(op.get_bind())

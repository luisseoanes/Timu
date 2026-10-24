"""dashboard: reportes programados

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-23 22:11:39.502922
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reportes_programados",
        sa.Column("nombre", sa.String(length=160), nullable=False),
        sa.Column("periodicidad", sa.String(length=12), nullable=False),
        sa.Column(
            "destinatarios",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "indicadores",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("ciudad", sa.String(length=80), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("ultimo_envio", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ultimo_error", sa.Text(), nullable=True),
        sa.Column("creado_por_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["creado_por_id"],
            ["usuarios.id"],
            name=op.f("fk_reportes_programados_creado_por_id_usuarios"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reportes_programados")),
    )


def downgrade() -> None:
    op.drop_table("reportes_programados")

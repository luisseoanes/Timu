"""ia: prompts versionados, registro de consultas y casos de prueba

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-23 22:24:11.939242
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "casos_prueba_ia",
        sa.Column("prompt_codigo", sa.String(length=40), nullable=False),
        sa.Column("nombre", sa.String(length=160), nullable=False),
        sa.Column("entrada", sa.Text(), nullable=False),
        sa.Column(
            "esperado",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_casos_prueba_ia")),
    )
    op.create_index(
        op.f("ix_casos_prueba_ia_prompt_codigo"), "casos_prueba_ia", ["prompt_codigo"], unique=False
    )
    op.create_table(
        "consultas_ia",
        sa.Column("prompt_codigo", sa.String(length=40), nullable=False),
        sa.Column("prompt_version", sa.Integer(), nullable=True),
        sa.Column("modelo", sa.String(length=60), nullable=True),
        sa.Column("estado", sa.String(length=24), nullable=False),
        sa.Column("contexto", sa.String(length=120), nullable=True),
        sa.Column("tokens_entrada", sa.Integer(), nullable=False),
        sa.Column("tokens_salida", sa.Integer(), nullable=False),
        sa.Column("tokens_cache_lectura", sa.Integer(), nullable=False),
        sa.Column("tokens_cache_escritura", sa.Integer(), nullable=False),
        sa.Column("costo_usd", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column("latencia_ms", sa.Integer(), nullable=True),
        sa.Column("request_id", sa.String(length=80), nullable=True),
        sa.Column("entrada", sa.Text(), nullable=True),
        sa.Column("salida", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_consultas_ia")),
    )
    op.create_index(op.f("ix_consultas_ia_contexto"), "consultas_ia", ["contexto"], unique=False)
    op.create_index(op.f("ix_consultas_ia_estado"), "consultas_ia", ["estado"], unique=False)
    op.create_index(
        op.f("ix_consultas_ia_prompt_codigo"), "consultas_ia", ["prompt_codigo"], unique=False
    )
    op.create_table(
        "prompts_ia",
        sa.Column("codigo", sa.String(length=40), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("sistema", sa.Text(), nullable=False),
        sa.Column("estado", sa.String(length=12), nullable=False),
        sa.Column("nota", sa.Text(), nullable=True),
        sa.Column("evaluado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "evaluacion",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("activado_por_id", sa.Uuid(), nullable=True),
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
            ["activado_por_id"],
            ["usuarios.id"],
            name=op.f("fk_prompts_ia_activado_por_id_usuarios"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prompts_ia")),
        sa.UniqueConstraint("codigo", "version", name=op.f("uq_prompts_ia_codigo")),
    )
    op.create_index(op.f("ix_prompts_ia_codigo"), "prompts_ia", ["codigo"], unique=False)
    op.create_index(op.f("ix_prompts_ia_estado"), "prompts_ia", ["estado"], unique=False)
    op.add_column(
        "solicitudes_virtuales",
        sa.Column(
            "borrador_ia",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
    )
    op.add_column(
        "solicitudes_virtuales", sa.Column("borrador_en", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("solicitudes_virtuales", "borrador_en")
    op.drop_column("solicitudes_virtuales", "borrador_ia")
    op.drop_index(op.f("ix_prompts_ia_estado"), table_name="prompts_ia")
    op.drop_index(op.f("ix_prompts_ia_codigo"), table_name="prompts_ia")
    op.drop_table("prompts_ia")
    op.drop_index(op.f("ix_consultas_ia_prompt_codigo"), table_name="consultas_ia")
    op.drop_index(op.f("ix_consultas_ia_estado"), table_name="consultas_ia")
    op.drop_index(op.f("ix_consultas_ia_contexto"), table_name="consultas_ia")
    op.drop_table("consultas_ia")
    op.drop_index(op.f("ix_casos_prueba_ia_prompt_codigo"), table_name="casos_prueba_ia")
    op.drop_table("casos_prueba_ia")

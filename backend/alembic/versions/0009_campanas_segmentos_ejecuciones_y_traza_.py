"""campanas: segmentos, ejecuciones y traza por destinatario

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-23 21:48:05.794092
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "segmentos",
        sa.Column("nombre", sa.String(length=160), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column(
            "filtros",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
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
            ["creado_por_id"], ["usuarios.id"], name=op.f("fk_segmentos_creado_por_id_usuarios")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_segmentos")),
        sa.UniqueConstraint("nombre", name=op.f("uq_segmentos_nombre")),
    )
    op.create_table(
        "ejecuciones_campana",
        sa.Column("campana_id", sa.Uuid(), nullable=False),
        sa.Column("iniciada_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("terminada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estado", sa.String(length=16), nullable=False),
        sa.Column("audiencia", sa.Integer(), nullable=False),
        sa.Column("excluidos", sa.Integer(), nullable=False),
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
            ["campana_id"], ["campanas.id"], name=op.f("fk_ejecuciones_campana_campana_id_campanas")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ejecuciones_campana")),
    )
    op.create_index(
        op.f("ix_ejecuciones_campana_campana_id"),
        "ejecuciones_campana",
        ["campana_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ejecuciones_campana_estado"), "ejecuciones_campana", ["estado"], unique=False
    )
    op.create_table(
        "destinatarios_campana",
        sa.Column("ejecucion_id", sa.Uuid(), nullable=False),
        sa.Column("familia_id", sa.Uuid(), nullable=False),
        sa.Column("telefono", sa.String(length=32), nullable=False),
        sa.Column("estado", sa.String(length=16), nullable=False),
        sa.Column("motivo_exclusion", sa.String(length=120), nullable=True),
        sa.Column("mensaje_id", sa.Uuid(), nullable=True),
        sa.Column("encolado_en", sa.DateTime(timezone=True), nullable=True),
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
            ["ejecucion_id"],
            ["ejecuciones_campana.id"],
            name=op.f("fk_destinatarios_campana_ejecucion_id_ejecuciones_campana"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["familia_id"],
            ["familias.id"],
            name=op.f("fk_destinatarios_campana_familia_id_familias"),
        ),
        sa.ForeignKeyConstraint(
            ["mensaje_id"],
            ["mensajes.id"],
            name=op.f("fk_destinatarios_campana_mensaje_id_mensajes"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_destinatarios_campana")),
        sa.UniqueConstraint(
            "ejecucion_id", "familia_id", name=op.f("uq_destinatarios_campana_ejecucion_id")
        ),
    )
    op.create_index(
        op.f("ix_destinatarios_campana_ejecucion_id"),
        "destinatarios_campana",
        ["ejecucion_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_destinatarios_campana_estado"), "destinatarios_campana", ["estado"], unique=False
    )
    op.create_index(
        op.f("ix_destinatarios_campana_familia_id"),
        "destinatarios_campana",
        ["familia_id"],
        unique=False,
    )
    op.add_column(
        "campanas",
        sa.Column(
            "variables",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column("campanas", sa.Column("segmento_id", sa.Uuid(), nullable=True))
    op.add_column(
        "campanas",
        sa.Column("recurrencia", sa.String(length=16), nullable=False, server_default="ninguna"),
    )
    op.add_column(
        "campanas", sa.Column("proxima_ejecucion", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(
        op.f("ix_campanas_proxima_ejecucion"), "campanas", ["proxima_ejecucion"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_campanas_segmento_id_segmentos"), "campanas", "segmentos", ["segmento_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_campanas_segmento_id_segmentos"), "campanas", type_="foreignkey")
    op.drop_index(op.f("ix_campanas_proxima_ejecucion"), table_name="campanas")
    op.drop_column("campanas", "proxima_ejecucion")
    op.drop_column("campanas", "recurrencia")
    op.drop_column("campanas", "segmento_id")
    op.drop_column("campanas", "variables")
    op.drop_index(op.f("ix_destinatarios_campana_familia_id"), table_name="destinatarios_campana")
    op.drop_index(op.f("ix_destinatarios_campana_estado"), table_name="destinatarios_campana")
    op.drop_index(op.f("ix_destinatarios_campana_ejecucion_id"), table_name="destinatarios_campana")
    op.drop_table("destinatarios_campana")
    op.drop_index(op.f("ix_ejecuciones_campana_estado"), table_name="ejecuciones_campana")
    op.drop_index(op.f("ix_ejecuciones_campana_campana_id"), table_name="ejecuciones_campana")
    op.drop_table("ejecuciones_campana")
    op.drop_table("segmentos")

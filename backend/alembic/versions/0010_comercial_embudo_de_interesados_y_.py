"""comercial: embudo de interesados y conversacion automatizada

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-23 21:58:04.664480
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "arboles_conversacion",
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "nodos",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("nota", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_arboles_conversacion")),
        sa.UniqueConstraint("version", name=op.f("uq_arboles_conversacion_version")),
    )
    op.create_index(
        op.f("ix_arboles_conversacion_activo"), "arboles_conversacion", ["activo"], unique=False
    )
    op.create_table(
        "interesados",
        sa.Column("nombre", sa.String(length=160), nullable=True),
        sa.Column("telefono", sa.String(length=32), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("ciudad", sa.String(length=80), nullable=True),
        sa.Column("origen", sa.String(length=24), nullable=False),
        sa.Column("etapa", sa.String(length=16), nullable=False),
        sa.Column("responsable_id", sa.Uuid(), nullable=True),
        sa.Column("familia_id", sa.Uuid(), nullable=True),
        sa.Column("plan_sugerido", sa.String(length=40), nullable=True),
        sa.Column(
            "datos",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("motivo_perdida", sa.String(length=255), nullable=True),
        sa.Column("ultimo_contacto", sa.DateTime(timezone=True), nullable=True),
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
            ["familia_id"], ["familias.id"], name=op.f("fk_interesados_familia_id_familias")
        ),
        sa.ForeignKeyConstraint(
            ["responsable_id"], ["usuarios.id"], name=op.f("fk_interesados_responsable_id_usuarios")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_interesados")),
        sa.UniqueConstraint("telefono", name=op.f("uq_interesados_telefono")),
    )
    op.create_index(op.f("ix_interesados_ciudad"), "interesados", ["ciudad"], unique=False)
    op.create_index(op.f("ix_interesados_email"), "interesados", ["email"], unique=False)
    op.create_index(op.f("ix_interesados_etapa"), "interesados", ["etapa"], unique=False)
    op.create_index(op.f("ix_interesados_familia_id"), "interesados", ["familia_id"], unique=False)
    op.create_index(op.f("ix_interesados_origen"), "interesados", ["origen"], unique=False)
    op.create_index(
        op.f("ix_interesados_responsable_id"), "interesados", ["responsable_id"], unique=False
    )
    op.create_table(
        "conversaciones_comerciales",
        sa.Column("telefono", sa.String(length=32), nullable=False),
        sa.Column("interesado_id", sa.Uuid(), nullable=True),
        sa.Column("nodo", sa.String(length=40), nullable=False),
        sa.Column(
            "datos",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("estado", sa.String(length=16), nullable=False),
        sa.Column("fallos", sa.Integer(), nullable=False),
        sa.Column("asesor_id", sa.Uuid(), nullable=True),
        sa.Column("tarea_id", sa.Uuid(), nullable=True),
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
            ["asesor_id"],
            ["usuarios.id"],
            name=op.f("fk_conversaciones_comerciales_asesor_id_usuarios"),
        ),
        sa.ForeignKeyConstraint(
            ["interesado_id"],
            ["interesados.id"],
            name=op.f("fk_conversaciones_comerciales_interesado_id_interesados"),
        ),
        sa.ForeignKeyConstraint(
            ["tarea_id"], ["tareas.id"], name=op.f("fk_conversaciones_comerciales_tarea_id_tareas")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversaciones_comerciales")),
        sa.UniqueConstraint("telefono", name=op.f("uq_conversaciones_comerciales_telefono")),
    )
    op.create_index(
        op.f("ix_conversaciones_comerciales_estado"),
        "conversaciones_comerciales",
        ["estado"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_conversaciones_comerciales_estado"), table_name="conversaciones_comerciales"
    )
    op.drop_table("conversaciones_comerciales")
    op.drop_index(op.f("ix_interesados_responsable_id"), table_name="interesados")
    op.drop_index(op.f("ix_interesados_origen"), table_name="interesados")
    op.drop_index(op.f("ix_interesados_familia_id"), table_name="interesados")
    op.drop_index(op.f("ix_interesados_etapa"), table_name="interesados")
    op.drop_index(op.f("ix_interesados_email"), table_name="interesados")
    op.drop_index(op.f("ix_interesados_ciudad"), table_name="interesados")
    op.drop_table("interesados")
    op.drop_index(op.f("ix_arboles_conversacion_activo"), table_name="arboles_conversacion")
    op.drop_table("arboles_conversacion")

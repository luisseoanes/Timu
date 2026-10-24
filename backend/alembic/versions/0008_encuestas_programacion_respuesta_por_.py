"""encuestas: programacion, respuesta por enlace o whatsapp y configuracion

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-23 21:40:36.667532
"""

import sqlalchemy as sa

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "configuraciones_encuesta",
        sa.Column("tipo_servicio_codigo", sa.String(length=40), nullable=True),
        sa.Column("encuesta_activa", sa.Boolean(), nullable=False),
        sa.Column("demora_horas", sa.Integer(), nullable=False),
        sa.Column("plantilla_encuesta", sa.String(length=120), nullable=False),
        sa.Column("seguimiento_dias", sa.Integer(), nullable=True),
        sa.Column("plantilla_seguimiento", sa.String(length=120), nullable=False),
        sa.Column("umbral_alerta", sa.Integer(), nullable=False),
        sa.Column("comentario", sa.Text(), nullable=True),
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
            ["tipo_servicio_codigo"],
            ["tipos_servicio.codigo"],
            name=op.f("fk_configuraciones_encuesta_tipo_servicio_codigo_tipos_servicio"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_configuraciones_encuesta")),
        sa.UniqueConstraint(
            "tipo_servicio_codigo", name=op.f("uq_configuraciones_encuesta_tipo_servicio_codigo")
        ),
    )
    op.add_column("encuestas", sa.Column("responsable_id", sa.Uuid(), nullable=True))
    # La tabla encuestas existia sin endpoint que la llenara: no hay filas que rellenar.
    op.add_column(
        "encuestas",
        sa.Column("tipo", sa.String(length=16), nullable=False, server_default="satisfaccion"),
    )
    op.add_column("encuestas", sa.Column("token", sa.String(length=64), nullable=False))
    op.add_column(
        "encuestas", sa.Column("programada_para", sa.DateTime(timezone=True), nullable=False)
    )
    op.add_column("encuestas", sa.Column("canal_respuesta", sa.String(length=16), nullable=True))
    op.add_column("encuestas", sa.Column("tarea_id", sa.Uuid(), nullable=True))
    op.create_index(
        op.f("ix_encuestas_programada_para"), "encuestas", ["programada_para"], unique=False
    )
    op.create_index(
        op.f("ix_encuestas_responsable_id"), "encuestas", ["responsable_id"], unique=False
    )
    op.create_unique_constraint(op.f("uq_encuestas_token"), "encuestas", ["token"])
    op.create_foreign_key(
        op.f("fk_encuestas_tarea_id_tareas"), "encuestas", "tareas", ["tarea_id"], ["id"]
    )
    op.create_foreign_key(
        op.f("fk_encuestas_responsable_id_usuarios"),
        "encuestas",
        "usuarios",
        ["responsable_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_encuestas_responsable_id_usuarios"), "encuestas", type_="foreignkey"
    )
    op.drop_constraint(op.f("fk_encuestas_tarea_id_tareas"), "encuestas", type_="foreignkey")
    op.drop_constraint(op.f("uq_encuestas_token"), "encuestas", type_="unique")
    op.drop_index(op.f("ix_encuestas_responsable_id"), table_name="encuestas")
    op.drop_index(op.f("ix_encuestas_programada_para"), table_name="encuestas")
    op.drop_column("encuestas", "tarea_id")
    op.drop_column("encuestas", "canal_respuesta")
    op.drop_column("encuestas", "programada_para")
    op.drop_column("encuestas", "token")
    op.drop_column("encuestas", "tipo")
    op.drop_column("encuestas", "responsable_id")
    op.drop_table("configuraciones_encuesta")

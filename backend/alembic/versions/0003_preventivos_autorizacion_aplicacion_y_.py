"""preventivos: autorizacion, aplicacion y carnets verificables

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-23 20:58:18.181778
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "carnets_emitidos",
        sa.Column("codigo", sa.String(length=16), nullable=False),
        sa.Column("mascota_id", sa.Uuid(), nullable=False),
        sa.Column("archivo_id", sa.Uuid(), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "contenido",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("emitido_por_id", sa.Uuid(), nullable=True),
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
            ["archivo_id"], ["archivos.id"], name=op.f("fk_carnets_emitidos_archivo_id_archivos")
        ),
        sa.ForeignKeyConstraint(
            ["emitido_por_id"],
            ["usuarios.id"],
            name=op.f("fk_carnets_emitidos_emitido_por_id_usuarios"),
        ),
        sa.ForeignKeyConstraint(
            ["mascota_id"], ["mascotas.id"], name=op.f("fk_carnets_emitidos_mascota_id_mascotas")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_carnets_emitidos")),
        sa.UniqueConstraint("codigo", name=op.f("uq_carnets_emitidos_codigo")),
    )
    op.create_index(
        op.f("ix_carnets_emitidos_mascota_id"), "carnets_emitidos", ["mascota_id"], unique=False
    )
    op.add_column(
        "eventos_preventivos",
        sa.Column("es_refuerzo", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("eventos_preventivos", sa.Column("lote", sa.String(length=60), nullable=True))
    op.add_column("eventos_preventivos", sa.Column("aplicado_por_id", sa.Uuid(), nullable=True))
    op.add_column("eventos_preventivos", sa.Column("autorizado_por_id", sa.Uuid(), nullable=True))
    op.add_column(
        "eventos_preventivos", sa.Column("autorizado_en", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "eventos_preventivos", sa.Column("medio_autorizacion", sa.String(length=24), nullable=True)
    )
    op.add_column(
        "eventos_preventivos", sa.Column("motivo_cancelacion", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "eventos_preventivos", sa.Column("notificado_en", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_foreign_key(
        op.f("fk_eventos_preventivos_autorizado_por_id_usuarios"),
        "eventos_preventivos",
        "usuarios",
        ["autorizado_por_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_eventos_preventivos_aplicado_por_id_usuarios"),
        "eventos_preventivos",
        "usuarios",
        ["aplicado_por_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_eventos_preventivos_aplicado_por_id_usuarios"),
        "eventos_preventivos",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_eventos_preventivos_autorizado_por_id_usuarios"),
        "eventos_preventivos",
        type_="foreignkey",
    )
    op.drop_column("eventos_preventivos", "notificado_en")
    op.drop_column("eventos_preventivos", "motivo_cancelacion")
    op.drop_column("eventos_preventivos", "medio_autorizacion")
    op.drop_column("eventos_preventivos", "autorizado_en")
    op.drop_column("eventos_preventivos", "autorizado_por_id")
    op.drop_column("eventos_preventivos", "aplicado_por_id")
    op.drop_column("eventos_preventivos", "lote")
    op.drop_column("eventos_preventivos", "es_refuerzo")
    op.drop_index(op.f("ix_carnets_emitidos_mascota_id"), table_name="carnets_emitidos")
    op.drop_table("carnets_emitidos")

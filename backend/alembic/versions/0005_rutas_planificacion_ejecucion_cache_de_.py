"""rutas: planificacion, ejecucion, cache de distancias y avisos

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-23 21:15:46.553132
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "consumo_mapas",
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("elementos", sa.Integer(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_consumo_mapas")),
        sa.UniqueConstraint("fecha", name=op.f("uq_consumo_mapas_fecha")),
    )
    op.create_table(
        "distancias_cache",
        sa.Column("origen", sa.String(length=32), nullable=False),
        sa.Column("destino", sa.String(length=32), nullable=False),
        sa.Column("metros", sa.Integer(), nullable=False),
        sa.Column("segundos", sa.Integer(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_distancias_cache")),
        sa.UniqueConstraint("origen", "destino", name=op.f("uq_distancias_cache_origen")),
    )
    op.create_table(
        "planificaciones_ruta",
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("ciudad", sa.String(length=80), nullable=False),
        sa.Column(
            "responsables",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("estado", sa.String(length=16), nullable=False),
        sa.Column(
            "resultado",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("solicitada_por_id", sa.Uuid(), nullable=True),
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
            ["solicitada_por_id"],
            ["usuarios.id"],
            name=op.f("fk_planificaciones_ruta_solicitada_por_id_usuarios"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_planificaciones_ruta")),
    )
    op.create_index(
        op.f("ix_planificaciones_ruta_estado"), "planificaciones_ruta", ["estado"], unique=False
    )
    op.create_index(
        op.f("ix_planificaciones_ruta_fecha"), "planificaciones_ruta", ["fecha"], unique=False
    )
    op.add_column(
        "paradas_ruta",
        sa.Column("estado", sa.String(length=16), nullable=False, server_default="pendiente"),
    )
    op.add_column(
        "paradas_ruta", sa.Column("llegada_estimada", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "paradas_ruta", sa.Column("llegada_en", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("paradas_ruta", sa.Column("salida_en", sa.DateTime(timezone=True), nullable=True))
    op.add_column("paradas_ruta", sa.Column("evidencia_archivo_id", sa.Uuid(), nullable=True))
    op.add_column("paradas_ruta", sa.Column("nota", sa.Text(), nullable=True))
    op.add_column("paradas_ruta", sa.Column("motivo_omision", sa.String(length=255), nullable=True))
    op.add_column(
        "paradas_ruta", sa.Column("aviso_ventana_en", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "paradas_ruta", sa.Column("aviso_en_camino_en", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(op.f("ix_paradas_ruta_estado"), "paradas_ruta", ["estado"], unique=False)
    op.create_foreign_key(
        op.f("fk_paradas_ruta_evidencia_archivo_id_archivos"),
        "paradas_ruta",
        "archivos",
        ["evidencia_archivo_id"],
        ["id"],
    )
    op.add_column("rutas", sa.Column("planificacion_id", sa.Uuid(), nullable=True))
    op.add_column("rutas", sa.Column("inicio_real", sa.DateTime(timezone=True), nullable=True))
    op.add_column("rutas", sa.Column("fin_real", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_rutas_responsable_id"), "rutas", ["responsable_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_rutas_planificacion_id_planificaciones_ruta"),
        "rutas",
        "planificaciones_ruta",
        ["planificacion_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_rutas_planificacion_id_planificaciones_ruta"), "rutas", type_="foreignkey"
    )
    op.drop_index(op.f("ix_rutas_responsable_id"), table_name="rutas")
    op.drop_column("rutas", "fin_real")
    op.drop_column("rutas", "inicio_real")
    op.drop_column("rutas", "planificacion_id")
    op.drop_constraint(
        op.f("fk_paradas_ruta_evidencia_archivo_id_archivos"), "paradas_ruta", type_="foreignkey"
    )
    op.drop_index(op.f("ix_paradas_ruta_estado"), table_name="paradas_ruta")
    op.drop_column("paradas_ruta", "aviso_en_camino_en")
    op.drop_column("paradas_ruta", "aviso_ventana_en")
    op.drop_column("paradas_ruta", "motivo_omision")
    op.drop_column("paradas_ruta", "nota")
    op.drop_column("paradas_ruta", "evidencia_archivo_id")
    op.drop_column("paradas_ruta", "salida_en")
    op.drop_column("paradas_ruta", "llegada_en")
    op.drop_column("paradas_ruta", "llegada_estimada")
    op.drop_column("paradas_ruta", "estado")
    op.drop_index(op.f("ix_planificaciones_ruta_fecha"), table_name="planificaciones_ruta")
    op.drop_index(op.f("ix_planificaciones_ruta_estado"), table_name="planificaciones_ruta")
    op.drop_table("planificaciones_ruta")
    op.drop_table("distancias_cache")
    op.drop_table("consumo_mapas")

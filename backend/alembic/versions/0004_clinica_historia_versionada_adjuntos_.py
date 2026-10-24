"""clinica: historia versionada, adjuntos, formulas y atencion virtual

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-23 21:04:50.770807
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plantillas_consulta",
        sa.Column("codigo", sa.String(length=40), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("tipo_servicio_codigo", sa.String(length=40), nullable=True),
        sa.Column(
            "campos",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("activa", sa.Boolean(), nullable=False),
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
            name=op.f("fk_plantillas_consulta_tipo_servicio_codigo_tipos_servicio"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plantillas_consulta")),
        sa.UniqueConstraint("codigo", name=op.f("uq_plantillas_consulta_codigo")),
    )
    op.create_index(
        op.f("ix_plantillas_consulta_tipo_servicio_codigo"),
        "plantillas_consulta",
        ["tipo_servicio_codigo"],
        unique=False,
    )
    op.create_table(
        "respuestas_virtuales",
        sa.Column("codigo", sa.String(length=40), nullable=False),
        sa.Column("titulo", sa.String(length=160), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column(
            "variables",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("estado", sa.String(length=16), nullable=False),
        sa.Column("aprobada_por_id", sa.Uuid(), nullable=True),
        sa.Column("aprobada_en", sa.DateTime(timezone=True), nullable=True),
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
            ["aprobada_por_id"],
            ["usuarios.id"],
            name=op.f("fk_respuestas_virtuales_aprobada_por_id_usuarios"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_respuestas_virtuales")),
        sa.UniqueConstraint("codigo", name=op.f("uq_respuestas_virtuales_codigo")),
    )
    op.create_index(
        op.f("ix_respuestas_virtuales_estado"), "respuestas_virtuales", ["estado"], unique=False
    )
    op.create_table(
        "formulas",
        sa.Column("historia_id", sa.Uuid(), nullable=False),
        sa.Column(
            "items",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("indicaciones", sa.Text(), nullable=True),
        sa.Column("archivo_id", sa.Uuid(), nullable=True),
        sa.Column("emitida_por_id", sa.Uuid(), nullable=True),
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
            ["archivo_id"], ["archivos.id"], name=op.f("fk_formulas_archivo_id_archivos")
        ),
        sa.ForeignKeyConstraint(
            ["emitida_por_id"], ["usuarios.id"], name=op.f("fk_formulas_emitida_por_id_usuarios")
        ),
        sa.ForeignKeyConstraint(
            ["historia_id"],
            ["historias_clinicas.id"],
            name=op.f("fk_formulas_historia_id_historias_clinicas"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_formulas")),
    )
    op.create_index(op.f("ix_formulas_historia_id"), "formulas", ["historia_id"], unique=False)
    op.create_table(
        "solicitudes_virtuales",
        sa.Column("familia_id", sa.Uuid(), nullable=False),
        sa.Column("mascota_id", sa.Uuid(), nullable=False),
        sa.Column("canal", sa.String(length=16), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("estado", sa.String(length=16), nullable=False),
        sa.Column("prioridad", sa.String(length=8), nullable=False),
        sa.Column("asignada_a_id", sa.Uuid(), nullable=True),
        sa.Column("tomada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("respuesta_codigo", sa.String(length=40), nullable=True),
        sa.Column("respuesta", sa.Text(), nullable=True),
        sa.Column("respondida_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("historia_id", sa.Uuid(), nullable=True),
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
            ["asignada_a_id"],
            ["usuarios.id"],
            name=op.f("fk_solicitudes_virtuales_asignada_a_id_usuarios"),
        ),
        sa.ForeignKeyConstraint(
            ["familia_id"],
            ["familias.id"],
            name=op.f("fk_solicitudes_virtuales_familia_id_familias"),
        ),
        sa.ForeignKeyConstraint(
            ["historia_id"],
            ["historias_clinicas.id"],
            name=op.f("fk_solicitudes_virtuales_historia_id_historias_clinicas"),
        ),
        sa.ForeignKeyConstraint(
            ["mascota_id"],
            ["mascotas.id"],
            name=op.f("fk_solicitudes_virtuales_mascota_id_mascotas"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_solicitudes_virtuales")),
    )
    op.create_index(
        op.f("ix_solicitudes_virtuales_asignada_a_id"),
        "solicitudes_virtuales",
        ["asignada_a_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_solicitudes_virtuales_estado"), "solicitudes_virtuales", ["estado"], unique=False
    )
    op.create_index(
        op.f("ix_solicitudes_virtuales_familia_id"),
        "solicitudes_virtuales",
        ["familia_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_solicitudes_virtuales_mascota_id"),
        "solicitudes_virtuales",
        ["mascota_id"],
        unique=False,
    )
    op.add_column("adjuntos_clinicos", sa.Column("archivo_id", sa.Uuid(), nullable=False))
    op.add_column(
        "adjuntos_clinicos", sa.Column("descripcion", sa.String(length=255), nullable=True)
    )
    op.add_column("adjuntos_clinicos", sa.Column("subido_por_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f("fk_adjuntos_clinicos_archivo_id_archivos"),
        "adjuntos_clinicos",
        "archivos",
        ["archivo_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_adjuntos_clinicos_subido_por_id_usuarios"),
        "adjuntos_clinicos",
        "usuarios",
        ["subido_por_id"],
        ["id"],
    )
    op.drop_column("adjuntos_clinicos", "url")
    op.add_column("historias_clinicas", sa.Column("familia_id", sa.Uuid(), nullable=True))
    op.execute(
        "UPDATE historias_clinicas h SET familia_id = m.familia_id "
        "FROM mascotas m WHERE m.id = h.mascota_id"
    )
    op.alter_column("historias_clinicas", "familia_id", nullable=False)
    op.add_column(
        "historias_clinicas",
        sa.Column("tipo", sa.String(length=16), nullable=False, server_default="presencial"),
    )
    op.add_column(
        "historias_clinicas", sa.Column("plantilla_codigo", sa.String(length=40), nullable=True)
    )
    op.add_column("historias_clinicas", sa.Column("examen_fisico", sa.Text(), nullable=True))
    op.add_column("historias_clinicas", sa.Column("notas_internas", sa.Text(), nullable=True))
    op.add_column(
        "historias_clinicas",
        sa.Column("estado", sa.String(length=16), nullable=False, server_default="firmada"),
    )
    op.add_column(
        "historias_clinicas", sa.Column("version", sa.Integer(), nullable=False, server_default="1")
    )
    op.add_column("historias_clinicas", sa.Column("reemplaza_id", sa.Uuid(), nullable=True))
    op.add_column(
        "historias_clinicas", sa.Column("firmada_en", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("historias_clinicas", sa.Column("firmada_por_id", sa.Uuid(), nullable=True))
    op.create_index(
        op.f("ix_historias_clinicas_estado"), "historias_clinicas", ["estado"], unique=False
    )
    op.create_index(
        op.f("ix_historias_clinicas_familia_id"), "historias_clinicas", ["familia_id"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_historias_clinicas_reemplaza_id_historias_clinicas"),
        "historias_clinicas",
        "historias_clinicas",
        ["reemplaza_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_historias_clinicas_familia_id_familias"),
        "historias_clinicas",
        "familias",
        ["familia_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_historias_clinicas_firmada_por_id_usuarios"),
        "historias_clinicas",
        "usuarios",
        ["firmada_por_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_historias_clinicas_firmada_por_id_usuarios"),
        "historias_clinicas",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_historias_clinicas_familia_id_familias"), "historias_clinicas", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_historias_clinicas_reemplaza_id_historias_clinicas"),
        "historias_clinicas",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_historias_clinicas_familia_id"), table_name="historias_clinicas")
    op.drop_index(op.f("ix_historias_clinicas_estado"), table_name="historias_clinicas")
    op.drop_column("historias_clinicas", "firmada_por_id")
    op.drop_column("historias_clinicas", "firmada_en")
    op.drop_column("historias_clinicas", "reemplaza_id")
    op.drop_column("historias_clinicas", "version")
    op.drop_column("historias_clinicas", "estado")
    op.drop_column("historias_clinicas", "notas_internas")
    op.drop_column("historias_clinicas", "examen_fisico")
    op.drop_column("historias_clinicas", "plantilla_codigo")
    op.drop_column("historias_clinicas", "tipo")
    op.drop_column("historias_clinicas", "familia_id")
    op.add_column(
        "adjuntos_clinicos",
        sa.Column("url", sa.VARCHAR(length=500), autoincrement=False, nullable=False),
    )
    op.drop_constraint(
        op.f("fk_adjuntos_clinicos_subido_por_id_usuarios"), "adjuntos_clinicos", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_adjuntos_clinicos_archivo_id_archivos"), "adjuntos_clinicos", type_="foreignkey"
    )
    op.drop_column("adjuntos_clinicos", "subido_por_id")
    op.drop_column("adjuntos_clinicos", "descripcion")
    op.drop_column("adjuntos_clinicos", "archivo_id")
    op.drop_index(op.f("ix_solicitudes_virtuales_mascota_id"), table_name="solicitudes_virtuales")
    op.drop_index(op.f("ix_solicitudes_virtuales_familia_id"), table_name="solicitudes_virtuales")
    op.drop_index(op.f("ix_solicitudes_virtuales_estado"), table_name="solicitudes_virtuales")
    op.drop_index(
        op.f("ix_solicitudes_virtuales_asignada_a_id"), table_name="solicitudes_virtuales"
    )
    op.drop_table("solicitudes_virtuales")
    op.drop_index(op.f("ix_formulas_historia_id"), table_name="formulas")
    op.drop_table("formulas")
    op.drop_index(op.f("ix_respuestas_virtuales_estado"), table_name="respuestas_virtuales")
    op.drop_table("respuestas_virtuales")
    op.drop_index(
        op.f("ix_plantillas_consulta_tipo_servicio_codigo"), table_name="plantillas_consulta"
    )
    op.drop_table("plantillas_consulta")

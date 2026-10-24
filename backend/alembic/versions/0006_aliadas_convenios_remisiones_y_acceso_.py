"""aliadas: convenios, remisiones y acceso de la clinica

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-23 21:24:50.139201
"""

import sqlalchemy as sa

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "convenios_aliadas",
        sa.Column("clinica_id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=True),
        sa.Column("beneficio", sa.String(length=160), nullable=False),
        sa.Column("cobertura_pct", sa.Integer(), nullable=False),
        sa.Column("tarifa", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("tope_cubierto", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("vigente_desde", sa.Date(), nullable=False),
        sa.Column("vigente_hasta", sa.Date(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False),
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
            ["clinica_id"],
            ["clinicas_aliadas.id"],
            name=op.f("fk_convenios_aliadas_clinica_id_clinicas_aliadas"),
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["planes.id"], name=op.f("fk_convenios_aliadas_plan_id_planes")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_convenios_aliadas")),
    )
    op.create_index(
        op.f("ix_convenios_aliadas_clinica_id"), "convenios_aliadas", ["clinica_id"], unique=False
    )
    op.create_index(
        op.f("ix_convenios_aliadas_plan_id"), "convenios_aliadas", ["plan_id"], unique=False
    )
    op.add_column("clinicas_aliadas", sa.Column("nit", sa.String(length=20), nullable=True))
    op.add_column("clinicas_aliadas", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("clinicas_aliadas", sa.Column("servicios", sa.Text(), nullable=True))
    op.create_unique_constraint(op.f("uq_clinicas_aliadas_nit"), "clinicas_aliadas", ["nit"])
    # remisiones_aliadas no tenia endpoint antes de esta version: no hay filas que rellenar.
    op.add_column("remisiones_aliadas", sa.Column("codigo", sa.String(length=12), nullable=False))
    op.add_column("remisiones_aliadas", sa.Column("convenio_id", sa.Uuid(), nullable=False))
    op.add_column("remisiones_aliadas", sa.Column("familia_id", sa.Uuid(), nullable=False))
    op.add_column("remisiones_aliadas", sa.Column("mascota_id", sa.Uuid(), nullable=False))
    op.add_column("remisiones_aliadas", sa.Column("motivo", sa.Text(), nullable=False))
    op.add_column("remisiones_aliadas", sa.Column("cobertura_pct", sa.Integer(), nullable=False))
    op.add_column(
        "remisiones_aliadas",
        sa.Column("tope_cubierto", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.add_column("remisiones_aliadas", sa.Column("vence_en", sa.Date(), nullable=False))
    op.add_column("remisiones_aliadas", sa.Column("emitida_por_id", sa.Uuid(), nullable=True))
    op.add_column("remisiones_aliadas", sa.Column("fecha_atencion", sa.Date(), nullable=True))
    op.add_column(
        "remisiones_aliadas",
        sa.Column("valor_atencion", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.add_column("remisiones_aliadas", sa.Column("resumen_atencion", sa.Text(), nullable=True))
    op.add_column("remisiones_aliadas", sa.Column("reportada_por_id", sa.Uuid(), nullable=True))
    op.add_column(
        "remisiones_aliadas", sa.Column("reportada_en", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "remisiones_aliadas", sa.Column("motivo_anulacion", sa.String(length=255), nullable=True)
    )
    op.alter_column(
        "remisiones_aliadas",
        "beneficio_aplicado",
        existing_type=sa.VARCHAR(length=120),
        type_=sa.String(length=160),
        existing_nullable=True,
    )
    op.create_index(
        op.f("ix_remisiones_aliadas_familia_id"), "remisiones_aliadas", ["familia_id"], unique=False
    )
    op.create_index(
        op.f("ix_remisiones_aliadas_fecha_atencion"),
        "remisiones_aliadas",
        ["fecha_atencion"],
        unique=False,
    )
    op.create_unique_constraint(
        op.f("uq_remisiones_aliadas_codigo"), "remisiones_aliadas", ["codigo"]
    )
    op.create_foreign_key(
        op.f("fk_remisiones_aliadas_emitida_por_id_usuarios"),
        "remisiones_aliadas",
        "usuarios",
        ["emitida_por_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_remisiones_aliadas_mascota_id_mascotas"),
        "remisiones_aliadas",
        "mascotas",
        ["mascota_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_remisiones_aliadas_reportada_por_id_usuarios"),
        "remisiones_aliadas",
        "usuarios",
        ["reportada_por_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_remisiones_aliadas_convenio_id_convenios_aliadas"),
        "remisiones_aliadas",
        "convenios_aliadas",
        ["convenio_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_remisiones_aliadas_familia_id_familias"),
        "remisiones_aliadas",
        "familias",
        ["familia_id"],
        ["id"],
    )
    op.add_column("usuarios", sa.Column("clinica_aliada_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f("fk_usuarios_clinica_aliada_id_clinicas_aliadas"),
        "usuarios",
        "clinicas_aliadas",
        ["clinica_aliada_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_usuarios_clinica_aliada_id_clinicas_aliadas"), "usuarios", type_="foreignkey"
    )
    op.drop_column("usuarios", "clinica_aliada_id")
    op.drop_constraint(
        op.f("fk_remisiones_aliadas_familia_id_familias"), "remisiones_aliadas", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_remisiones_aliadas_convenio_id_convenios_aliadas"),
        "remisiones_aliadas",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_remisiones_aliadas_reportada_por_id_usuarios"),
        "remisiones_aliadas",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_remisiones_aliadas_mascota_id_mascotas"), "remisiones_aliadas", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_remisiones_aliadas_emitida_por_id_usuarios"),
        "remisiones_aliadas",
        type_="foreignkey",
    )
    op.drop_constraint(op.f("uq_remisiones_aliadas_codigo"), "remisiones_aliadas", type_="unique")
    op.drop_index(op.f("ix_remisiones_aliadas_fecha_atencion"), table_name="remisiones_aliadas")
    op.drop_index(op.f("ix_remisiones_aliadas_familia_id"), table_name="remisiones_aliadas")
    op.alter_column(
        "remisiones_aliadas",
        "beneficio_aplicado",
        existing_type=sa.String(length=160),
        type_=sa.VARCHAR(length=120),
        existing_nullable=True,
    )
    op.drop_column("remisiones_aliadas", "motivo_anulacion")
    op.drop_column("remisiones_aliadas", "reportada_en")
    op.drop_column("remisiones_aliadas", "reportada_por_id")
    op.drop_column("remisiones_aliadas", "resumen_atencion")
    op.drop_column("remisiones_aliadas", "valor_atencion")
    op.drop_column("remisiones_aliadas", "fecha_atencion")
    op.drop_column("remisiones_aliadas", "emitida_por_id")
    op.drop_column("remisiones_aliadas", "vence_en")
    op.drop_column("remisiones_aliadas", "tope_cubierto")
    op.drop_column("remisiones_aliadas", "cobertura_pct")
    op.drop_column("remisiones_aliadas", "motivo")
    op.drop_column("remisiones_aliadas", "mascota_id")
    op.drop_column("remisiones_aliadas", "familia_id")
    op.drop_column("remisiones_aliadas", "convenio_id")
    op.drop_column("remisiones_aliadas", "codigo")
    op.drop_constraint(op.f("uq_clinicas_aliadas_nit"), "clinicas_aliadas", type_="unique")
    op.drop_column("clinicas_aliadas", "servicios")
    op.drop_column("clinicas_aliadas", "email")
    op.drop_column("clinicas_aliadas", "nit")
    op.drop_index(op.f("ix_convenios_aliadas_plan_id"), table_name="convenios_aliadas")
    op.drop_index(op.f("ix_convenios_aliadas_clinica_id"), table_name="convenios_aliadas")
    op.drop_table("convenios_aliadas")

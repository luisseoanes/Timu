# ruff: noqa: E501  (politicas congeladas de app/core/permisos_db.py: expresiones SQL largas)
"""planes: tarifas por numero de peludos, por periodicidad y ciudades

6.2 y 6.3: cada peludo paga la tarifa de su plan segun cuantos peludos tiene la afiliacion
(de 1 a 4; con mas, la de 4), y con un solo peludo los periodos largos tienen su propio precio.
Un plan se vende en varias ciudades. Los valores se guardan tal cual, no como porcentajes.

Los planes existentes reciben sus cuatro tarifas con su valor mensual y sus ciudades: la suya
o, si no tenia (vacia era todas), todas las activas del catalogo. Las tablas llevan auditoria y RLS
con las politicas de app/core/permisos_db.py, escritas aqui y congeladas.

Revision ID: 0032
Revises: 0031
Create Date: 2026-11-09 23:37:07.141658
"""

import sqlalchemy as sa

from alembic import op

revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None

# (nombre, tabla, comando, rol, USING, WITH CHECK), de politicas(['ciudades_plan', 'tarifas_periodicidad', 'tarifas_plan'])
POLITICAS = [
    (
        "p_ciudades_plan_select",
        "ciudades_plan",
        "SELECT",
        "timu_app",
        "app_rol() IN ('sistema', 'admin', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
        None,
    ),
    (
        "p_ciudades_plan_insert",
        "ciudades_plan",
        "INSERT",
        "timu_app",
        None,
        "app_rol() IN ('sistema', 'admin')",
    ),
    (
        "p_ciudades_plan_update",
        "ciudades_plan",
        "UPDATE",
        "timu_app",
        "app_rol() IN ('sistema', 'admin')",
        "app_rol() IN ('sistema', 'admin')",
    ),
    (
        "p_ciudades_plan_delete",
        "ciudades_plan",
        "DELETE",
        "timu_app",
        "app_rol() IN ('sistema')",
        None,
    ),
    (
        "p_tarifas_periodicidad_select",
        "tarifas_periodicidad",
        "SELECT",
        "timu_app",
        "app_rol() IN ('sistema', 'admin', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
        None,
    ),
    (
        "p_tarifas_periodicidad_insert",
        "tarifas_periodicidad",
        "INSERT",
        "timu_app",
        None,
        "app_rol() IN ('sistema', 'admin')",
    ),
    (
        "p_tarifas_periodicidad_update",
        "tarifas_periodicidad",
        "UPDATE",
        "timu_app",
        "app_rol() IN ('sistema', 'admin')",
        "app_rol() IN ('sistema', 'admin')",
    ),
    (
        "p_tarifas_periodicidad_delete",
        "tarifas_periodicidad",
        "DELETE",
        "timu_app",
        "app_rol() IN ('sistema')",
        None,
    ),
    (
        "p_tarifas_plan_select",
        "tarifas_plan",
        "SELECT",
        "timu_app",
        "app_rol() IN ('sistema', 'admin', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
        None,
    ),
    (
        "p_tarifas_plan_insert",
        "tarifas_plan",
        "INSERT",
        "timu_app",
        None,
        "app_rol() IN ('sistema', 'admin')",
    ),
    (
        "p_tarifas_plan_update",
        "tarifas_plan",
        "UPDATE",
        "timu_app",
        "app_rol() IN ('sistema', 'admin')",
        "app_rol() IN ('sistema', 'admin')",
    ),
    (
        "p_tarifas_plan_delete",
        "tarifas_plan",
        "DELETE",
        "timu_app",
        "app_rol() IN ('sistema')",
        None,
    ),
]


def _literal(texto: str) -> str:
    return "'" + texto.replace("'", "''") + "'"


def upgrade() -> None:
    op.create_table(
        "ciudades_plan",
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("ciudad", sa.String(length=80), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
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
        sa.CheckConstraint("uuid_extract_version(id) = 7", name=op.f("ck_ciudades_plan_id_uuidv7")),
        sa.ForeignKeyConstraint(
            ["ciudad"],
            ["ciudades.nombre"],
            name=op.f("fk_ciudades_plan_ciudad_ciudades"),
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["planes.id"], name=op.f("fk_ciudades_plan_plan_id_planes")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ciudades_plan")),
    )
    op.create_index(op.f("ix_ciudades_plan_ciudad"), "ciudades_plan", ["ciudad"], unique=False)
    op.create_index(op.f("ix_ciudades_plan_plan_id"), "ciudades_plan", ["plan_id"], unique=False)
    op.create_index(
        "uq_ciudades_plan_plan_ciudad",
        "ciudades_plan",
        ["plan_id", "ciudad"],
        unique=True,
        postgresql_where=None,
    )
    op.create_table(
        "tarifas_periodicidad",
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column(
            "periodicidad",
            sa.Enum("mensual", "trimestral", "semestral", "anual", name="periodicidad"),
            nullable=False,
        ),
        sa.Column("valor", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
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
        sa.CheckConstraint(
            "periodicidad <> 'mensual'", name=op.f("ck_tarifas_periodicidad_periodo_largo")
        ),
        sa.CheckConstraint(
            "uuid_extract_version(id) = 7", name=op.f("ck_tarifas_periodicidad_id_uuidv7")
        ),
        sa.CheckConstraint("valor > 0", name=op.f("ck_tarifas_periodicidad_valor_positivo")),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["planes.id"], name=op.f("fk_tarifas_periodicidad_plan_id_planes")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tarifas_periodicidad")),
    )
    op.create_index(
        op.f("ix_tarifas_periodicidad_plan_id"), "tarifas_periodicidad", ["plan_id"], unique=False
    )
    op.create_index(
        "uq_tarifas_periodicidad_plan_periodicidad",
        "tarifas_periodicidad",
        ["plan_id", "periodicidad"],
        unique=True,
        postgresql_where=None,
    )
    op.create_table(
        "tarifas_plan",
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("peludos", sa.Integer(), nullable=False),
        sa.Column("valor", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
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
        sa.CheckConstraint("peludos BETWEEN 1 AND 4", name=op.f("ck_tarifas_plan_peludos_rango")),
        sa.CheckConstraint("uuid_extract_version(id) = 7", name=op.f("ck_tarifas_plan_id_uuidv7")),
        sa.CheckConstraint("valor > 0", name=op.f("ck_tarifas_plan_valor_positivo")),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["planes.id"], name=op.f("fk_tarifas_plan_plan_id_planes")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tarifas_plan")),
    )
    op.create_index(op.f("ix_tarifas_plan_plan_id"), "tarifas_plan", ["plan_id"], unique=False)
    op.create_index(
        "uq_tarifas_plan_plan_peludos",
        "tarifas_plan",
        ["plan_id", "peludos"],
        unique=True,
        postgresql_where=None,
    )
    for tabla in ("ciudades_plan", "tarifas_periodicidad", "tarifas_plan"):
        op.execute(
            f"CREATE TRIGGER tr_{tabla}_auditoria AFTER INSERT OR UPDATE OR DELETE"
            f" ON {tabla} FOR EACH ROW EXECUTE FUNCTION auditar()"
        )
        op.execute(f"ALTER TABLE {tabla} ENABLE ROW LEVEL SECURITY")
    for nombre, tabla, comando, rol, usar, comprobar in POLITICAS:
        sql = f"CREATE POLICY {nombre} ON {tabla} FOR {comando} TO {rol}"
        if usar is not None:
            sql += f" USING ({usar})"
        if comprobar is not None:
            sql += f" WITH CHECK ({comprobar})"
        op.execute(sql)
        texto = f"USING ({usar}) WITH CHECK ({comprobar})"
        op.execute(f"COMMENT ON POLICY {nombre} ON {tabla} IS {_literal(texto)}")
    # Los planes existentes: cuatro tarifas con su valor mensual y sus ciudades.
    op.execute(
        "INSERT INTO tarifas_plan (plan_id, peludos, valor)"
        " SELECT p.id, n, p.valor_mensual FROM planes p CROSS JOIN generate_series(1, 4) AS n"
        " WHERE p.valor_mensual > 0"
    )
    op.execute(
        "INSERT INTO ciudades_plan (plan_id, ciudad, activa)"
        " SELECT p.id, c.nombre, true FROM planes p JOIN ciudades c"
        " ON c.nombre = p.ciudad OR (p.ciudad IS NULL AND c.activa)"
    )


def downgrade() -> None:
    op.drop_index("uq_tarifas_plan_plan_peludos", table_name="tarifas_plan", postgresql_where=None)
    op.drop_index(op.f("ix_tarifas_plan_plan_id"), table_name="tarifas_plan")
    op.drop_table("tarifas_plan")
    op.drop_index(
        "uq_tarifas_periodicidad_plan_periodicidad",
        table_name="tarifas_periodicidad",
        postgresql_where=None,
    )
    op.drop_index(op.f("ix_tarifas_periodicidad_plan_id"), table_name="tarifas_periodicidad")
    op.drop_table("tarifas_periodicidad")
    op.execute("DROP TYPE periodicidad")
    op.drop_index("uq_ciudades_plan_plan_ciudad", table_name="ciudades_plan", postgresql_where=None)
    op.drop_index(op.f("ix_ciudades_plan_plan_id"), table_name="ciudades_plan")
    op.drop_index(op.f("ix_ciudades_plan_ciudad"), table_name="ciudades_plan")
    op.drop_table("ciudades_plan")

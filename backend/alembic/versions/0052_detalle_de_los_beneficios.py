# ruff: noqa: E501  (politicas congeladas: expresiones SQL largas)
"""planes: tope, carencia y detalle de cada beneficio, y los beneficios adicionales del plan

R3-PUB-04 (decidido con el usuario el 2026-11-17): todas las caracteristicas de un plan se
editan en Administracion y la portada, el registro y el contrato dicen lo mismo. El beneficio
por tipo de servicio gana hasta cuanto cubre por episodio, desde cuantos dias de afiliada aplica
y su detalle; el plan gana `beneficios_adicionales_plan`, lo que da sin ser un tipo de servicio
que se agenda (servicio funebre, desparasitante externo, beneficios de terceros), con su
auditoria y RLS con las politicas de app/core/permisos_db.py (escritas aqui, congeladas): un
catalogo que leen todos los perfiles que leen planes y solo administracion escribe.

Revision ID: 0052
Revises: 0051
Create Date: 2026-11-17 19:00:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0052"
down_revision = "0051"
branch_labels = None
depends_on = None

# (nombre, tabla, comando, rol, USING, WITH CHECK), de politicas(['beneficios_adicionales_plan'])
POLITICAS = [
    (
        "p_beneficios_adicionales_plan_select",
        "beneficios_adicionales_plan",
        "SELECT",
        "timu_app",
        "app_rol() IN ('sistema', 'admin', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
        None,
    ),
    (
        "p_beneficios_adicionales_plan_insert",
        "beneficios_adicionales_plan",
        "INSERT",
        "timu_app",
        None,
        "app_rol() IN ('sistema', 'admin')",
    ),
    (
        "p_beneficios_adicionales_plan_update",
        "beneficios_adicionales_plan",
        "UPDATE",
        "timu_app",
        "app_rol() IN ('sistema', 'admin')",
        "app_rol() IN ('sistema', 'admin')",
    ),
    (
        "p_beneficios_adicionales_plan_delete",
        "beneficios_adicionales_plan",
        "DELETE",
        "timu_app",
        "app_rol() IN ('sistema')",
        None,
    ),
]


def _literal(texto: str) -> str:
    return "'" + texto.replace("'", "''") + "'"


def upgrade() -> None:
    op.add_column("beneficios_plan", sa.Column("tope_episodio", sa.Numeric(12, 2), nullable=True))
    op.add_column("beneficios_plan", sa.Column("carencia_dias", sa.Integer(), nullable=True))
    op.add_column("beneficios_plan", sa.Column("detalle", sa.Text(), nullable=True))
    op.execute(
        "ALTER TABLE beneficios_plan ADD CONSTRAINT ck_beneficios_plan_tope_positivo"
        " CHECK (tope_episodio IS NULL OR tope_episodio > 0)"
    )
    op.execute(
        "ALTER TABLE beneficios_plan ADD CONSTRAINT ck_beneficios_plan_carencia_no_negativa"
        " CHECK (carencia_dias IS NULL OR carencia_dias >= 0)"
    )
    op.create_table(
        "beneficios_adicionales_plan",
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(length=160), nullable=False),
        sa.Column("cubre", sa.String(length=160), nullable=False),
        sa.Column("detalle", sa.Text(), nullable=True),
        sa.Column("carencia_dias", sa.Integer(), nullable=True),
        sa.Column("tercero", sa.Boolean(), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
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
            "btrim(nombre) <> ''", name=op.f("ck_beneficios_adicionales_plan_nombre_no_vacio")
        ),
        sa.CheckConstraint(
            "btrim(cubre) <> ''", name=op.f("ck_beneficios_adicionales_plan_cubre_no_vacio")
        ),
        sa.CheckConstraint(
            "carencia_dias IS NULL OR carencia_dias >= 0",
            name=op.f("ck_beneficios_adicionales_plan_carencia_no_negativa"),
        ),
        sa.CheckConstraint(
            "orden >= 0", name=op.f("ck_beneficios_adicionales_plan_orden_no_negativo")
        ),
        sa.CheckConstraint(
            "uuid_extract_version(id) = 7", name=op.f("ck_beneficios_adicionales_plan_id_uuidv7")
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["planes.id"],
            name=op.f("fk_beneficios_adicionales_plan_plan_id_planes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_beneficios_adicionales_plan")),
    )
    op.create_index(
        "ix_beneficios_adicionales_plan_plan_id", "beneficios_adicionales_plan", ["plan_id"]
    )
    op.execute(
        "CREATE TRIGGER tr_beneficios_adicionales_plan_auditoria AFTER INSERT OR UPDATE OR DELETE"
        " ON beneficios_adicionales_plan FOR EACH ROW EXECUTE FUNCTION auditar()"
    )
    op.execute("ALTER TABLE beneficios_adicionales_plan ENABLE ROW LEVEL SECURITY")
    for nombre, tabla, comando, rol, usar, comprobar in POLITICAS:
        sql = f"CREATE POLICY {nombre} ON {tabla} FOR {comando} TO {rol}"
        if usar is not None:
            sql += f" USING ({usar})"
        if comprobar is not None:
            sql += f" WITH CHECK ({comprobar})"
        op.execute(sql)
        texto = f"USING ({usar}) WITH CHECK ({comprobar})"
        op.execute(f"COMMENT ON POLICY {nombre} ON {tabla} IS {_literal(texto)}")


def downgrade() -> None:
    op.drop_table("beneficios_adicionales_plan")
    op.execute(
        "ALTER TABLE beneficios_plan DROP CONSTRAINT ck_beneficios_plan_carencia_no_negativa"
    )
    op.execute("ALTER TABLE beneficios_plan DROP CONSTRAINT ck_beneficios_plan_tope_positivo")
    op.drop_column("beneficios_plan", "detalle")
    op.drop_column("beneficios_plan", "carencia_dias")
    op.drop_column("beneficios_plan", "tope_episodio")

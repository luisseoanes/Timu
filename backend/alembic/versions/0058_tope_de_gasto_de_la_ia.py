# ruff: noqa: E501  (politicas congeladas: expresiones SQL largas)
"""ia: el tope de gasto mensual de la IA, que edita Administracion

Seccion 14 (decidido con el usuario el 2026-11-20): el tope de gasto mensual de la IA, que era la
variable de entorno IA_PRESUPUESTO_MENSUAL_USD, lo cambia Administracion sin desplegar. Siempre
hay tope (CHECK >= 1): al llegar a el, la IA se apaga hasta el mes siguiente; para gastar mas se
sube, y la auditoria guarda quien y cuando. Una sola fila (`unica`), que esta migracion crea con
el valor que tenia la variable (US$ 50, provisional: docs/pendientes-externos.md). RLS con las
politicas de app/core/permisos_db.py (escritas aqui, congeladas): la lee y la cambia
administracion; el sistema, que hace las consultas, la lee.

Revision ID: 0058
Revises: 0057
Create Date: 2026-11-20 06:00:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0058"
down_revision = "0057"
branch_labels = None
depends_on = None

# (nombre, tabla, comando, rol, USING, WITH CHECK), de politicas(['configuracion_ia'])
POLITICAS = [
    (
        "p_configuracion_ia_select",
        "configuracion_ia",
        "SELECT",
        "timu_app",
        "app_rol() IN ('sistema', 'admin')",
        None,
    ),
    (
        "p_configuracion_ia_insert",
        "configuracion_ia",
        "INSERT",
        "timu_app",
        None,
        "app_rol() IN ('sistema')",
    ),
    (
        "p_configuracion_ia_update",
        "configuracion_ia",
        "UPDATE",
        "timu_app",
        "app_rol() IN ('sistema', 'admin')",
        "app_rol() IN ('sistema', 'admin')",
    ),
    (
        "p_configuracion_ia_delete",
        "configuracion_ia",
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
        "configuracion_ia",
        sa.Column("unica", sa.Boolean(), nullable=False),
        sa.Column("presupuesto_mensual_usd", sa.Numeric(precision=10, scale=2), nullable=False),
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
        sa.CheckConstraint("unica", name=op.f("ck_configuracion_ia_una_sola_fila")),
        sa.CheckConstraint(
            "presupuesto_mensual_usd >= 1", name=op.f("ck_configuracion_ia_presupuesto_minimo")
        ),
        sa.CheckConstraint(
            "uuid_extract_version(id) = 7", name=op.f("ck_configuracion_ia_id_uuidv7")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_configuracion_ia")),
    )
    op.create_index("uq_configuracion_ia_unica", "configuracion_ia", ["unica"], unique=True)
    op.execute(
        "CREATE TRIGGER tr_configuracion_ia_auditoria AFTER INSERT OR UPDATE OR DELETE"
        " ON configuracion_ia FOR EACH ROW EXECUTE FUNCTION auditar()"
    )
    op.execute("ALTER TABLE configuracion_ia ENABLE ROW LEVEL SECURITY")
    for nombre, tabla, comando, rol, usar, comprobar in POLITICAS:
        sql = f"CREATE POLICY {nombre} ON {tabla} FOR {comando} TO {rol}"
        if usar is not None:
            sql += f" USING ({usar})"
        if comprobar is not None:
            sql += f" WITH CHECK ({comprobar})"
        op.execute(sql)
        texto = f"USING ({usar}) WITH CHECK ({comprobar})"
        op.execute(f"COMMENT ON POLICY {nombre} ON {tabla} IS {_literal(texto)}")
    op.execute("INSERT INTO configuracion_ia (unica, presupuesto_mensual_usd) VALUES (true, 50)")


def downgrade() -> None:
    op.drop_table("configuracion_ia")

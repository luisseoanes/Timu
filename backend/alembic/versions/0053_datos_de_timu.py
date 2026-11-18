# ruff: noqa: E501  (politicas congeladas: expresiones SQL largas)
"""institucional: los datos de TIMU que dice la portada y edita Administracion

R3-PUB-04 (decidido con el usuario el 2026-11-17): lo institucional y de contacto de TIMU
(quienes son, su clinica, sus telefonos, su WhatsApp, sus redes) se edita en Administracion y lo
lee la portada publica, sin desplegar. Una sola fila (`unica`, que solo admite verdadero y es
unica), que esta migracion crea vacia; el WhatsApp de contacto del registro en linea, que era una
variable de entorno, vive aqui. Auditoria y RLS de catalogo con las politicas de
app/core/permisos_db.py (escritas aqui, congeladas): la leen todos, la escribe administracion.

Revision ID: 0053
Revises: 0052
Create Date: 2026-11-17 20:00:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0053"
down_revision = "0052"
branch_labels = None
depends_on = None

# (nombre, tabla, comando, rol, USING, WITH CHECK), de politicas(['datos_timu'])
POLITICAS = [
    (
        "p_datos_timu_select",
        "datos_timu",
        "SELECT",
        "timu_app",
        "app_rol() IN ('sistema', 'admin', 'aliada', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
        None,
    ),
    (
        "p_datos_timu_insert",
        "datos_timu",
        "INSERT",
        "timu_app",
        None,
        "app_rol() IN ('sistema', 'admin')",
    ),
    (
        "p_datos_timu_update",
        "datos_timu",
        "UPDATE",
        "timu_app",
        "app_rol() IN ('sistema', 'admin')",
        "app_rol() IN ('sistema', 'admin')",
    ),
    ("p_datos_timu_delete", "datos_timu", "DELETE", "timu_app", "app_rol() IN ('sistema')", None),
]


def _literal(texto: str) -> str:
    return "'" + texto.replace("'", "''") + "'"


def upgrade() -> None:
    op.create_table(
        "datos_timu",
        sa.Column("unica", sa.Boolean(), nullable=False),
        sa.Column("razon_social", sa.String(length=160), nullable=True),
        sa.Column("nit", sa.String(length=20), nullable=True),
        sa.Column("presentacion", sa.Text(), nullable=True),
        sa.Column("mision", sa.Text(), nullable=True),
        sa.Column("vision", sa.Text(), nullable=True),
        sa.Column(
            "valores",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("clinica_nombre", sa.String(length=160), nullable=True),
        sa.Column("clinica_direccion", sa.String(length=255), nullable=True),
        sa.Column("clinica_barrio", sa.String(length=120), nullable=True),
        sa.Column("clinica_ciudad", sa.String(length=80), nullable=True),
        sa.Column("clinica_horario", sa.String(length=255), nullable=True),
        sa.Column("horario_atencion", sa.Text(), nullable=True),
        sa.Column(
            "telefonos",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("whatsapp", sa.String(length=32), nullable=True),
        sa.Column("correo", sa.String(length=255), nullable=True),
        sa.Column(
            "redes",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
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
        sa.CheckConstraint("unica", name=op.f("ck_datos_timu_una_sola_fila")),
        sa.CheckConstraint(
            "whatsapp IS NULL OR whatsapp ~ '^\\+[1-9][0-9]{7,14}$'",
            name=op.f("ck_datos_timu_whatsapp_formato"),
        ),
        sa.CheckConstraint(
            "correo IS NULL OR correo ~ '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$'",
            name=op.f("ck_datos_timu_correo_formato"),
        ),
        sa.CheckConstraint("uuid_extract_version(id) = 7", name=op.f("ck_datos_timu_id_uuidv7")),
        sa.ForeignKeyConstraint(
            ["clinica_ciudad"],
            ["ciudades.nombre"],
            name=op.f("fk_datos_timu_clinica_ciudad_ciudades"),
            onupdate="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_datos_timu")),
    )
    op.create_index("ix_datos_timu_clinica_ciudad", "datos_timu", ["clinica_ciudad"])
    op.create_index("uq_datos_timu_unica", "datos_timu", ["unica"], unique=True)
    op.execute(
        "CREATE TRIGGER tr_datos_timu_auditoria AFTER INSERT OR UPDATE OR DELETE"
        " ON datos_timu FOR EACH ROW EXECUTE FUNCTION auditar()"
    )
    op.execute("ALTER TABLE datos_timu ENABLE ROW LEVEL SECURITY")
    for nombre, tabla, comando, rol, usar, comprobar in POLITICAS:
        sql = f"CREATE POLICY {nombre} ON {tabla} FOR {comando} TO {rol}"
        if usar is not None:
            sql += f" USING ({usar})"
        if comprobar is not None:
            sql += f" WITH CHECK ({comprobar})"
        op.execute(sql)
        texto = f"USING ({usar}) WITH CHECK ({comprobar})"
        op.execute(f"COMMENT ON POLICY {nombre} ON {tabla} IS {_literal(texto)}")
    op.execute(
        "INSERT INTO datos_timu (unica, valores, telefonos, redes) VALUES (true, '[]', '[]', '[]')"
    )


def downgrade() -> None:
    op.drop_table("datos_timu")

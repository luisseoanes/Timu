# ruff: noqa: E501  (politicas congeladas: expresiones SQL largas)
"""aliadas: lo que dice de cada aliada la portada, y su logo

R3-PUB-04 (decidido con el usuario el 2026-11-17): las aliadas de la portada salen de
Administracion -> Aliadas. Cada una dice que es (no todas son clinicas: `tipo_aliada`), si se
muestra en la portada y en que orden de la red, si atiende las 24 horas, su barrio, su horario,
su presentacion y su logo (un archivo con el proposito `logo_aliada`). `publico` lee las que se
muestran y sus logos: las politicas de lectura de las dos tablas cambian (escritas aqui,
congeladas, como las genera app/core/permisos_db.py).

Revision ID: 0054
Revises: 0053
Create Date: 2026-11-17 21:00:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0054"
down_revision = "0053"
branch_labels = None
depends_on = None

TIPOS = ("clinica", "especialista", "peluqueria", "farmacia", "hospedaje", "funeraria", "otro")
_PROPOSITOS_ANTERIORES = (
    "foto_mascota",
    "adjunto_clinico",
    "contrato",
    "formula",
    "carnet",
    "documento_familia",
)

# (nombre, tabla, (USING, WITH CHECK) anteriores, (USING, WITH CHECK) nuevos)
CAMBIOS = [
    (
        "p_archivos_select",
        "archivos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (subido_por_id = app_usuario() OR id IN (SELECT foto_archivo_id FROM mascotas WHERE familia_id = app_familia()) OR id IN (SELECT documento_archivo_id FROM contratos WHERE familia_id = app_familia()) OR id IN (SELECT archivo_id FROM adjuntos_clinicos WHERE historia_id IN (SELECT id FROM historias_clinicas WHERE familia_id = app_familia() AND estado <> 'borrador')) OR id IN (SELECT archivo_id FROM carnets_emitidos WHERE mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia())) OR id IN (SELECT archivo_id FROM documentos_familia WHERE familia_id = app_familia() AND visible_familia AND activo)))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (subido_por_id = app_usuario() OR id IN (SELECT foto_archivo_id FROM mascotas WHERE familia_id = app_familia()) OR id IN (SELECT documento_archivo_id FROM contratos WHERE familia_id = app_familia()) OR id IN (SELECT archivo_id FROM adjuntos_clinicos WHERE historia_id IN (SELECT id FROM historias_clinicas WHERE familia_id = app_familia() AND estado <> 'borrador')) OR id IN (SELECT archivo_id FROM carnets_emitidos WHERE mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia())) OR id IN (SELECT archivo_id FROM documentos_familia WHERE familia_id = app_familia() AND visible_familia AND activo))) OR (app_rol() = 'publico' AND (proposito::text = 'logo_aliada' AND id IN (SELECT logo_archivo_id FROM clinicas_aliadas WHERE en_portada AND activa)))",
            None,
        ),
    ),
    (
        "p_clinicas_aliadas_select",
        "clinicas_aliadas",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (id = app_clinica()))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (id = app_clinica())) OR (app_rol() = 'publico' AND (en_portada AND activa))",
            None,
        ),
    ),
]


def _literal(texto: str) -> str:
    return "'" + texto.replace("'", "''") + "'"


def _alterar(nombre: str, tabla: str, usar: str | None, comprobar: str | None) -> None:
    sql = f"ALTER POLICY {nombre} ON {tabla}"
    if usar is not None:
        sql += f" USING ({usar})"
    if comprobar is not None:
        sql += f" WITH CHECK ({comprobar})"
    op.execute(sql)
    texto = f"USING ({usar}) WITH CHECK ({comprobar})"
    op.execute(f"COMMENT ON POLICY {nombre} ON {tabla} IS {_literal(texto)}")


def upgrade() -> None:
    # El valor nuevo no se usa en esta migracion: ADD VALUE admite la transaccion.
    op.execute("ALTER TYPE proposito_archivo ADD VALUE 'logo_aliada'")
    tipo = sa.Enum(*TIPOS, name="tipo_aliada")
    tipo.create(op.get_bind())
    op.add_column(
        "clinicas_aliadas",
        sa.Column("tipo", tipo, nullable=False, server_default="clinica"),
    )
    for columna in ("en_portada", "atiende_24h"):
        op.add_column(
            "clinicas_aliadas",
            sa.Column(columna, sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    op.add_column("clinicas_aliadas", sa.Column("barrio", sa.String(120), nullable=True))
    op.add_column("clinicas_aliadas", sa.Column("horario", sa.String(255), nullable=True))
    op.add_column("clinicas_aliadas", sa.Column("presentacion", sa.Text(), nullable=True))
    op.add_column(
        "clinicas_aliadas",
        sa.Column("orden_portada", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("clinicas_aliadas", sa.Column("logo_archivo_id", sa.Uuid(), nullable=True))
    # Las filas ya existentes tienen su valor: el valor por defecto lo declara el modelo.
    for columna in ("tipo", "en_portada", "atiende_24h", "orden_portada"):
        op.alter_column("clinicas_aliadas", columna, server_default=None)
    op.create_foreign_key(
        op.f("fk_clinicas_aliadas_logo_archivo_id_archivos"),
        "clinicas_aliadas",
        "archivos",
        ["logo_archivo_id"],
        ["id"],
    )
    op.create_index("ix_clinicas_aliadas_logo_archivo_id", "clinicas_aliadas", ["logo_archivo_id"])
    op.execute(
        "ALTER TABLE clinicas_aliadas ADD CONSTRAINT ck_clinicas_aliadas_orden_no_negativo"
        " CHECK (orden_portada >= 0)"
    )
    for nombre, tabla, _, (usar, comprobar) in CAMBIOS:
        _alterar(nombre, tabla, usar, comprobar)


def downgrade() -> None:
    for nombre, tabla, (usar, comprobar), _ in CAMBIOS:
        _alterar(nombre, tabla, usar, comprobar)
    op.execute("ALTER TABLE clinicas_aliadas DROP CONSTRAINT ck_clinicas_aliadas_orden_no_negativo")
    op.drop_index("ix_clinicas_aliadas_logo_archivo_id", table_name="clinicas_aliadas")
    op.drop_constraint(
        op.f("fk_clinicas_aliadas_logo_archivo_id_archivos"), "clinicas_aliadas", type_="foreignkey"
    )
    for columna in (
        "logo_archivo_id",
        "orden_portada",
        "presentacion",
        "horario",
        "barrio",
        "atiende_24h",
        "en_portada",
        "tipo",
    ):
        op.drop_column("clinicas_aliadas", columna)
    op.execute("DROP TYPE tipo_aliada")
    # PostgreSQL no quita un valor de un enum: se recrea el tipo sin el. Si queda algun logo,
    # la conversion falla y el downgrade se detiene sin perderlo.
    op.execute("ALTER TYPE proposito_archivo RENAME TO proposito_archivo_anterior")
    valores = ", ".join(f"'{v}'" for v in _PROPOSITOS_ANTERIORES)
    op.execute(f"CREATE TYPE proposito_archivo AS ENUM ({valores})")
    op.execute(
        "ALTER TABLE archivos ALTER COLUMN proposito TYPE proposito_archivo"
        " USING proposito::text::proposito_archivo"
    )
    op.execute("DROP TYPE proposito_archivo_anterior")

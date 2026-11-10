# ruff: noqa: E501  (politicas congeladas de app/core/permisos_db.py: expresiones SQL largas)
"""rls: la familia cambia la foto de sus mascotas

6.1: la familia sube y administra las fotos de sus mascotas desde el portal. Para eso su perfil
puede actualizar las filas de sus propias mascotas; que solo cambie la foto lo garantiza la
ruta del portal, que no toca otra columna (RLS filtra filas, no columnas).

Esta la politica cambiada con su expresion anterior y la nueva.

Revision ID: 0031
Revises: 0030
Create Date: 2026-11-10 22:00:00
"""

from alembic import op

revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None

# (politica, tabla, (USING, WITH CHECK) anterior, (USING, WITH CHECK) nuevo)
CAMBIOS = [
    (
        "p_mascotas_update",
        "mascotas",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
        ),
    )
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
    for nombre, tabla, _, (usar, comprobar) in CAMBIOS:
        _alterar(nombre, tabla, usar, comprobar)


def downgrade() -> None:
    for nombre, tabla, (usar, comprobar), _ in CAMBIOS:
        _alterar(nombre, tabla, usar, comprobar)

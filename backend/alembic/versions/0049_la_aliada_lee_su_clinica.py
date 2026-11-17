# ruff: noqa: E501  (politicas congeladas: expresiones SQL largas)
"""clinicas_aliadas y especies: la clinica aliada lee su propia fila y el catalogo

R3-ALI-01: el espacio de la aliada dice en que clinica esta (en un computador compartido de
recepcion no basta el nombre del usuario) y la especie de la mascota remitida en palabras. La
matriz de app/core/permisos_db.py no le dejaba leer `clinicas_aliadas` ni `especies`; ahora lee
solo su clinica (`id = app_clinica()`) y el catalogo de especies. Estan la expresion anterior y
la nueva de cada politica (congeladas).

Revision ID: 0049
Revises: 0048
Create Date: 2026-11-16 20:00:00
"""

from alembic import op

revision = "0049"
down_revision = "0048"
branch_labels = None
depends_on = None

_EQUIPO = "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')"
_CON_ALIADA = _EQUIPO + " OR (app_rol() = 'aliada' AND (id = app_clinica()))"
_ESPECIES = (
    "app_rol() IN ('sistema', 'admin', 'comercial', 'familia', 'medico', 'operaciones', 'publico')"
)
_ESPECIES_CON_ALIADA = "app_rol() IN ('sistema', 'admin', 'aliada', 'comercial', 'familia', 'medico', 'operaciones', 'publico')"

# (nombre, tabla, (USING, WITH CHECK) anterior, (USING, WITH CHECK) nueva)
CAMBIOS = [
    ("p_clinicas_aliadas_select", "clinicas_aliadas", (_EQUIPO, None), (_CON_ALIADA, None)),
    ("p_especies_select", "especies", (_ESPECIES, None), (_ESPECIES_CON_ALIADA, None)),
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

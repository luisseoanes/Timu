# ruff: noqa: E501  (politicas congeladas: expresiones SQL largas)
"""clinica: el equipo medico edita y retira las plantillas de consulta (DEU-15)

Hasta ahora una plantilla solo se creaba: `PATCH /clinica/plantillas/{codigo}` corrige su
texto o la desactiva, y la matriz de app/core/permisos_db.py da `U` en plantillas_consulta a
quien las crea (medico y admin). No se borran (nada de negocio se borra) y la bitacora
(tr_plantillas_consulta_auditoria) guarda cada version; la consulta copia los textos al
crearse, asi que lo ya registrado no cambia. Estan la expresion anterior y la nueva de la
politica (congeladas).

Revision ID: 0056
Revises: 0055
Create Date: 2026-11-18 22:00:00
"""

from alembic import op

revision = "0056"
down_revision = "0055"
branch_labels = None
depends_on = None

_GESTION = "app_rol() IN ('sistema', 'admin', 'medico')"
_SISTEMA = "app_rol() IN ('sistema')"

# (nombre, tabla, (USING, WITH CHECK) anterior, (USING, WITH CHECK) nueva)
CAMBIOS = [
    (
        "p_plantillas_consulta_update",
        "plantillas_consulta",
        (_SISTEMA, _SISTEMA),
        (_GESTION, _GESTION),
    ),
]


def _literal(texto: str) -> str:
    return "'" + texto.replace("'", "''") + "'"


def _alterar(nombre: str, tabla: str, usar: str, comprobar: str) -> None:
    op.execute(f"ALTER POLICY {nombre} ON {tabla} USING ({usar}) WITH CHECK ({comprobar})")
    texto = f"USING ({usar}) WITH CHECK ({comprobar})"
    op.execute(f"COMMENT ON POLICY {nombre} ON {tabla} IS {_literal(texto)}")


def upgrade() -> None:
    for nombre, tabla, _, (usar, comprobar) in CAMBIOS:
        _alterar(nombre, tabla, usar, comprobar)


def downgrade() -> None:
    for nombre, tabla, (usar, comprobar), _ in CAMBIOS:
        _alterar(nombre, tabla, usar, comprobar)

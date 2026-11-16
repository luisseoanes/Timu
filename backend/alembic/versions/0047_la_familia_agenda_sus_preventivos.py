# ruff: noqa: E501  (politicas congeladas: expresiones SQL largas)
"""eventos_preventivos: la familia agenda desde el portal la visita de un preventivo suyo

DEU-3: el portal agendaba una visita de vacunacion sin decir cual, y al completarla no se
aplicaba nada. Ahora la familia elige el preventivo y agendarlo es su autorizacion (medio
«portal»): eso escribe en su fila (`servicio_id` y la autorizacion), que la matriz de
app/core/permisos_db.py solo le dejaba leer. La familia actualiza los de sus mascotas, la misma
condicion con que los lee. Estan la expresion anterior y la nueva de la politica (congeladas).

Revision ID: 0047
Revises: 0046
Create Date: 2026-11-16 12:00:00
"""

from alembic import op

revision = "0047"
down_revision = "0046"
branch_labels = None
depends_on = None

_EQUIPO = "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')"
_CON_FAMILIA = (
    _EQUIPO
    + " OR (app_rol() = 'familia' AND (mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia())))"
)

# (nombre, tabla, (USING, WITH CHECK) anterior, (USING, WITH CHECK) nueva)
CAMBIOS = [
    (
        "p_eventos_preventivos_update",
        "eventos_preventivos",
        (_EQUIPO, _EQUIPO),
        (_CON_FAMILIA, _CON_FAMILIA),
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

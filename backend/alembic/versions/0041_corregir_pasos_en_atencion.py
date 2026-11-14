# ruff: noqa: E501  (politicas congeladas: expresiones SQL largas)
"""servicios: el equipo corrige un paso registrado mientras el servicio esta en atencion

La ficha del servicio ofrece editar un paso ya registrado y `completar_paso` lo actualiza,
pero la matriz de app/core/permisos_db.py solo daba leer e insertar en servicio_pasos: la
base rechazaba el UPDATE y la API respondia 500. Los perfiles que insertan pasos ahora
tambien los actualizan. El servicio solo admite registrar pasos en atencion, asi que al
completarse el paso queda fijo, y la bitacora (tr_servicio_pasos_auditoria) guarda cada
version. Estan la expresion anterior y la nueva de la politica (congeladas).

Revision ID: 0041
Revises: 0040
Create Date: 2026-11-14 15:00:00
"""

from alembic import op

revision = "0041"
down_revision = "0040"
branch_labels = None
depends_on = None

_EQUIPO = "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')"
_SISTEMA = "app_rol() IN ('sistema')"

# (nombre, tabla, (USING, WITH CHECK) anterior, (USING, WITH CHECK) nueva)
CAMBIOS = [
    ("p_servicio_pasos_update", "servicio_pasos", (_SISTEMA, _SISTEMA), (_EQUIPO, _EQUIPO)),
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

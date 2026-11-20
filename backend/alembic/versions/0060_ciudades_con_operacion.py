"""catalogos: solo las ciudades con operacion de TIMU quedan activas

Decidido con el usuario el 2026-11-20, antes de que los clientes empiecen a usar el sistema: activas
Bogota y Medellin con su area metropolitana (el Valle de Aburra, donde estan las aliadas de TIMU);
las demas, desactivadas. Una familia solo se afilia en una ciudad activa, y el administrador puede
activar otra en Catalogos cuando TIMU abra operacion alli. Valor provisional hasta que TIMU lo
confirme (docs/pendientes-externos.md). En una base nueva lo dicen los datos de arranque
(`catalogos/datos.py`); esta migracion lo aplica a las que ya existen.

Revision ID: 0060
Revises: 0059
Create Date: 2026-11-20 14:00:00
"""

from alembic import op

revision = "0060"
down_revision = "0059"
branch_labels = None
depends_on = None

ACTIVAS = (
    "Bogotá",
    "Medellín",
    "Envigado",
    "Itagüí",
    "Sabaneta",
    "Bello",
    "La Estrella",
    "Caldas",
    "Copacabana",
    "Girardota",
    "Barbosa",
)


def upgrade() -> None:
    lista = ", ".join("'" + nombre.replace("'", "''") + "'" for nombre in ACTIVAS)
    op.execute(f"UPDATE ciudades SET activa = (nombre IN ({lista}))")  # noqa: S608 - lista fija


def downgrade() -> None:
    # Antes, todas las del catalogo estaban activas.
    op.execute("UPDATE ciudades SET activa = true")

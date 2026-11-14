"""usuarios: indice por perfil y estado para las vistas de Administracion

La pestana Usuarios separa al equipo, las clinicas aliadas, las familias y los inactivos, con
el recuento de cada vista (R2-PAN-10). La tabla crece con cada familia que entra al portal: el
indice compuesto sirve el filtro y el recuento sin recorrerla entera.

Revision ID: 0042
Revises: 0041
Create Date: 2026-11-14 18:00:00
"""

from alembic import op

revision = "0042"
down_revision = "0041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_usuarios_rol_activo", "usuarios", ["rol", "activo"])


def downgrade() -> None:
    op.drop_index("ix_usuarios_rol_activo", table_name="usuarios")

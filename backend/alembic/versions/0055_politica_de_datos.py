"""institucional: el enlace a la politica de tratamiento de datos

R3-PUB-04: el formulario de contacto de la portada recoge datos personales, y la Ley 1581 obliga
a informar de la politica de tratamiento. La web actual de TIMU la enlaza; Administracion escribe
aqui su enlace (solo https) y el formulario lo muestra.

Revision ID: 0055
Revises: 0054
Create Date: 2026-11-17 22:00:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0055"
down_revision = "0054"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("datos_timu", sa.Column("politica_datos_url", sa.String(500), nullable=True))
    op.execute(
        "ALTER TABLE datos_timu ADD CONSTRAINT ck_datos_timu_politica_https"
        " CHECK (politica_datos_url IS NULL OR politica_datos_url ~ '^https://')"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE datos_timu DROP CONSTRAINT ck_datos_timu_politica_https")
    op.drop_column("datos_timu", "politica_datos_url")

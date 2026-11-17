"""planes: carencia, exclusiones y enlace de terminos que el registro dice de frente

R3-PUB-02 (decidido con el usuario el 2026-11-17): el registro en linea muestra cada plan con
sus condiciones de frente (manual de marca: «exclusiones y carencias, de frente»), y el catalogo
no las guardaba. Los tres campos son opcionales: los escribe TIMU desde Administracion, y
mientras tanto la siembra local pone valores provisionales (docs/pendientes-externos.md). El
enlace de terminos solo admite https.

Revision ID: 0051
Revises: 0050
Create Date: 2026-11-17 10:00:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0051"
down_revision = "0050"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("planes", sa.Column("carencia", sa.Text(), nullable=True))
    op.add_column("planes", sa.Column("exclusiones", sa.Text(), nullable=True))
    op.add_column("planes", sa.Column("terminos_url", sa.String(500), nullable=True))
    op.execute(
        "ALTER TABLE planes ADD CONSTRAINT ck_planes_terminos_https"
        " CHECK (terminos_url IS NULL OR terminos_url ~ '^https://')"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE planes DROP CONSTRAINT ck_planes_terminos_https")
    op.drop_column("planes", "terminos_url")
    op.drop_column("planes", "exclusiones")
    op.drop_column("planes", "carencia")

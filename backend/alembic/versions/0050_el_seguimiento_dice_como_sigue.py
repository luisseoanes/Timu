"""encuestas: el seguimiento se responde con como sigue la mascota, no con un puntaje

R3-PUB-03 (decidido con el usuario el 2026-11-16): el enlace del seguimiento post atencion
(6.21) preguntaba «¿Como te fue?» del 1 al 5, como la encuesta de satisfaccion, y su puntaje se
mezclaba con el de la satisfaccion. Ahora pregunta como sigue la mascota (bien, con una duda o
con una novedad) en `como_sigue`, y el puntaje queda solo para la satisfaccion.

Un seguimiento ya respondido con puntaje pasa a `como_sigue`: hasta el umbral de alerta por
defecto (3) era una novedad, por encima, «bien». El `downgrade` lo devuelve a un puntaje (bien
5, duda 3, novedad 1).

Revision ID: 0050
Revises: 0049
Create Date: 2026-11-16 23:30:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0050"
down_revision = "0049"
branch_labels = None
depends_on = None

COMO_SIGUE = postgresql.ENUM("bien", "duda", "novedad", name="como_sigue_mascota")

_RESPONDIDA_ANTES = "estado <> 'respondida' OR (respondida_en IS NOT NULL AND puntaje IS NOT NULL)"
_RESPONDIDA = (
    "estado <> 'respondida' OR (respondida_en IS NOT NULL"
    " AND (puntaje IS NOT NULL OR como_sigue IS NOT NULL))"
)
_SEGUN_TIPO = (
    "(tipo = 'satisfaccion' AND como_sigue IS NULL)"
    " OR (tipo = 'seguimiento' AND puntaje IS NULL)"
)


def upgrade() -> None:
    COMO_SIGUE.create(op.get_bind())
    op.add_column(
        "encuestas",
        sa.Column(
            "como_sigue",
            postgresql.ENUM(name="como_sigue_mascota", create_type=False),
            nullable=True,
        ),
    )
    op.execute("ALTER TABLE encuestas DROP CONSTRAINT ck_encuestas_respondida_completa")
    op.execute(
        "UPDATE encuestas SET como_sigue = CASE WHEN puntaje <= 3 THEN 'novedad'"
        " ELSE 'bien' END::como_sigue_mascota, puntaje = NULL"
        " WHERE tipo = 'seguimiento' AND puntaje IS NOT NULL"
    )
    op.execute(
        f"ALTER TABLE encuestas ADD CONSTRAINT ck_encuestas_respondida_completa"
        f" CHECK ({_RESPONDIDA})"
    )
    op.execute(
        f"ALTER TABLE encuestas ADD CONSTRAINT ck_encuestas_respuesta_segun_tipo"
        f" CHECK ({_SEGUN_TIPO})"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE encuestas DROP CONSTRAINT ck_encuestas_respuesta_segun_tipo")
    op.execute("ALTER TABLE encuestas DROP CONSTRAINT ck_encuestas_respondida_completa")
    op.execute(
        "UPDATE encuestas SET puntaje = CASE como_sigue WHEN 'bien' THEN 5"
        " WHEN 'duda' THEN 3 ELSE 1 END WHERE como_sigue IS NOT NULL"
    )
    op.drop_column("encuestas", "como_sigue")
    COMO_SIGUE.drop(op.get_bind())
    op.execute(
        f"ALTER TABLE encuestas ADD CONSTRAINT ck_encuestas_respondida_completa"
        f" CHECK ({_RESPONDIDA_ANTES})"
    )

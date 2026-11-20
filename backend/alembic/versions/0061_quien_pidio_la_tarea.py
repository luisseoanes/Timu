"""tareas: quien pidio cada tarea

Decidido con el usuario el 2026-11-20: una tarea guarda quien la pidio desde el panel, para decirlo
en la bandeja y para que quien la pidio la siga en «Pedidas por mi» aunque sea de otra area. Vacio
en las que crea una regla o el sistema, y en las anteriores a esta migracion.

Revision ID: 0061
Revises: 0060
Create Date: 2026-11-20 16:00:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0061"
down_revision = "0060"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tareas", sa.Column("creada_por_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f("fk_tareas_creada_por_id_usuarios"), "tareas", "usuarios", ["creada_por_id"], ["id"]
    )
    op.create_index(op.f("ix_tareas_creada_por_id"), "tareas", ["creada_por_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_tareas_creada_por_id"), table_name="tareas")
    op.drop_constraint(op.f("fk_tareas_creada_por_id_usuarios"), "tareas", type_="foreignkey")
    op.drop_column("tareas", "creada_por_id")

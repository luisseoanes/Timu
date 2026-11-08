"""indices de los caminos calientes

Fase 5 de docs/plan-persistencia.md. Los que pidio el guarda de EXPLAIN
(test_los_caminos_calientes_no_recorren_tablas_enteras) sobre los listados del panel y las
tareas periodicas: afiliaciones por periodo del dashboard, embudo de interesados, pendientes
y la bandeja de tareas, que ahora ordena por el enum de prioridad para poder usar el indice.

Revision ID: 0025
Revises: 0024
Create Date: 2026-11-04 22:44:15.122995
"""

from alembic import op

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(op.f("ix_contratos_fecha_inicio"), "contratos", ["fecha_inicio"], unique=False)
    op.create_index("ix_interesados_created_at", "interesados", ["created_at"], unique=False)
    op.create_index("ix_pendientes_created_at", "pendientes", ["created_at"], unique=False)
    op.create_index(
        "ix_tareas_bandeja", "tareas", ["prioridad", "vence_el", "created_at", "id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_tareas_bandeja", table_name="tareas")
    op.drop_index("ix_pendientes_created_at", table_name="pendientes")
    op.drop_index("ix_interesados_created_at", table_name="interesados")
    op.drop_index(op.f("ix_contratos_fecha_inicio"), table_name="contratos")

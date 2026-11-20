"""comunicaciones: indices para buscar en los mensajes

Mensajes (Comercial y Atencion al cliente) busca por texto libre en el mensaje o el numero, y por
fechas (pedido por el usuario el 2026-11-20). Buscar «contiene» recorreria la tabla entera, que
crece con cada envio: indices de trigramas (pg_trgm, extension de confianza: la crea el dueno del
esquema sin superusuario) sobre el contenido y el destino, y uno sobre la fecha.

Revision ID: 0059
Revises: 0058
Create Date: 2026-11-20 12:00:00
"""

from alembic import op

revision = "0059"
down_revision = "0058"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_index(
        "ix_mensajes_contenido_trgm",
        "mensajes",
        ["contenido"],
        postgresql_using="gin",
        postgresql_ops={"contenido": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_mensajes_destino_trgm",
        "mensajes",
        ["destino"],
        postgresql_using="gin",
        postgresql_ops={"destino": "gin_trgm_ops"},
    )
    op.create_index("ix_mensajes_created_at", "mensajes", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_mensajes_created_at", table_name="mensajes")
    op.drop_index("ix_mensajes_destino_trgm", table_name="mensajes")
    op.drop_index("ix_mensajes_contenido_trgm", table_name="mensajes")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")

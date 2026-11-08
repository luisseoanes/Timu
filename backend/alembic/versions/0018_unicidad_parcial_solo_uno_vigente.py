"""unicidad parcial: solo uno vigente

Fase 2d de docs/plan-persistencia.md. Las reglas de "solo uno" que el codigo comprobaba
consultando antes de insertar (un contrato vigente por familia, una version activa de cada
prompt y de cada plantilla, un arbol de conversacion publicado, un medio de pago activo por
familia, una encuesta por servicio y tipo, un acceso de portal por familia, un servicio por
ruta salvo paradas omitidas) las garantiza ahora un indice unico. Comprobar y luego insertar
deja una ventana a dos peticiones simultaneas; el indice no.

Revision ID: 0018
Revises: 0017
Create Date: 2026-11-04 21:00:00
"""

from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None

# (tabla, indice, columnas, condicion)
UNICOS: list[tuple[str, str, list[str], str | None]] = [
    ("arboles_conversacion", "uq_arboles_conversacion_activo", ["activo"], "activo"),
    (
        "contratos",
        "uq_contratos_familia_vigente",
        ["familia_id"],
        "estado IN ('activa', 'en_mora', 'congelada')",
    ),
    ("encuestas", "uq_encuestas_servicio_tipo", ["servicio_id", "tipo"], None),
    ("familias", "uq_familias_usuario_portal", ["usuario_portal_id"], None),
    (
        "medios_pago_recurrente",
        "uq_medios_pago_recurrente_familia_activo",
        ["familia_id"],
        "activo",
    ),
    ("paradas_ruta", "uq_paradas_ruta_servicio", ["ruta_id", "servicio_id"], "estado <> 'omitida'"),
    ("plantillas_whatsapp", "uq_plantillas_whatsapp_activa", ["nombre", "idioma"], "activa"),
    ("prompts_ia", "uq_prompts_ia_codigo_activo", ["codigo"], "estado = 'activo'"),
]


def upgrade() -> None:
    for tabla, nombre, columnas, condicion in UNICOS:
        donde = f" WHERE {condicion}" if condicion else ""
        op.execute(f"CREATE UNIQUE INDEX {nombre} ON {tabla} ({', '.join(columnas)}){donde}")


def downgrade() -> None:
    for _, nombre, _, _ in reversed(UNICOS):
        op.execute(f"DROP INDEX {nombre}")

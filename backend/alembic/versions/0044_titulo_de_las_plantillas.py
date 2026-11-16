"""plantillas_whatsapp: el nombre con que el equipo llama a cada plantilla

Las reglas y las campanas ensenaban el codigo con que la plantilla se registra en Meta
(`aviso_mora`). `titulo` es el nombre para el equipo («Aviso de mora»); las plantillas que usa
el codigo lo reciben aqui, y una nueva lo trae del formulario o de su version anterior.

Revision ID: 0044
Revises: 0043
Create Date: 2026-11-15 13:00:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0044"
down_revision = "0043"
branch_labels = None
depends_on = None

TITULOS = {
    "activar_cuenta": "Activación de la cuenta",
    "afiliacion_congelada": "Afiliación congelada",
    "afiliacion_reactivada": "Afiliación reactivada",
    "aviso_congelamiento": "Aviso antes de congelar",
    "aviso_mora": "Aviso de mora",
    "bienvenida": "Bienvenida",
    "codigo_ingreso": "Código para ingresar al portal",
    "completar_afiliacion": "Completar la afiliación",
    "cuota_vencida": "Cuota vencida",
    "encuesta_satisfaccion": "Encuesta de satisfacción",
    "recordatorio_preventivo": "Recordatorio de preventivo",
    "recordatorio_renovacion": "Recordatorio de renovación",
    "recuperar_clave": "Recuperar la contraseña",
    "respuesta_virtual": "Respuesta de la orientación virtual",
    "seguimiento_post": "Seguimiento después de la atención",
    "tecnico_en_camino": "Médico en camino",
    "ventana_llegada": "Franja de llegada",
}


def upgrade() -> None:
    op.add_column("plantillas_whatsapp", sa.Column("titulo", sa.String(120), nullable=True))
    tabla = sa.table("plantillas_whatsapp", sa.column("nombre"), sa.column("titulo"))
    for nombre, titulo in TITULOS.items():
        op.execute(tabla.update().where(tabla.c.nombre == nombre).values(titulo=titulo))


def downgrade() -> None:
    op.drop_column("plantillas_whatsapp", "titulo")

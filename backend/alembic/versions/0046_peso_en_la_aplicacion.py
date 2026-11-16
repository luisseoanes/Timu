"""tipos_servicio: el peso, opcional, en la aplicacion de una desparasitacion

F2-PRE-07 pide el peso de cada desparasitacion en el carnet, pero el paso «Aplicacion» de la
visita solo pedia producto y lote, y todos sus campos eran obligatorios. Los pasos ganan
`opcionales` (campos que se aceptan sin exigirlos, con su nombre y si son una cifra); aqui se
le da el peso al paso de la desparasitacion de las bases ya creadas. `datos.py` ya lo trae.

Revision ID: 0046
Revises: 0045
Create Date: 2026-11-16 10:00:00
"""

import json

import sqlalchemy as sa

from alembic import op

revision = "0046"
down_revision = "0045"
branch_labels = None
depends_on = None

PESO = {"campo": "peso_kg", "nombre": "Peso de la mascota (kg)", "numerico": True}


def _cambiar(con_peso: bool) -> None:
    conexion = op.get_bind()
    fila = conexion.execute(
        sa.text("SELECT id, pasos FROM tipos_servicio WHERE codigo = 'desparasitacion'")
    ).first()
    if fila is None:
        return
    pasos = []
    for paso in fila.pasos or []:
        if paso.get("codigo") == "aplicacion":
            opcionales = [o for o in paso.get("opcionales", []) if o.get("campo") != "peso_kg"]
            paso = {**paso, "opcionales": [*opcionales, PESO] if con_peso else opcionales}
            if not paso["opcionales"]:
                paso.pop("opcionales")
        pasos.append(paso)
    conexion.execute(
        sa.text("UPDATE tipos_servicio SET pasos = CAST(:p AS jsonb) WHERE id = :i"),
        {"p": json.dumps(pasos, ensure_ascii=False), "i": fila.id},
    )


def upgrade() -> None:
    _cambiar(con_peso=True)


def downgrade() -> None:
    _cambiar(con_peso=False)

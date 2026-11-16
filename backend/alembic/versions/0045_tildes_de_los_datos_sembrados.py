"""catalogos y reglas: las tildes de los textos sembrados

Los nombres del catalogo (tipos de servicio, sus pasos y los esquemas preventivos) y los de las
reglas de arranque se sembraron sin tildes («Vacunacion», «Aviso de mora a los 25 dias») y se
ven asi en la linea, los botones y Administracion. Solo se corrige lo que sigue igual que se
sembro: si TIMU ya lo edito, es suyo y se respeta. `datos.py` ya los trae con tildes.

Revision ID: 0045
Revises: 0044
Create Date: 2026-11-16 09:00:00
"""

import json

import sqlalchemy as sa

from alembic import op

revision = "0045"
down_revision = "0044"
branch_labels = None
depends_on = None

TIPOS = {
    "vacunacion": ("Vacunacion", "Vacunación"),
    "desparasitacion": ("Desparasitacion", "Desparasitación"),
    "consulta_clinica": ("Consulta clinica", "Consulta clínica"),
    "control_post": ("Control post atencion", "Control post atención"),
    "orientacion_virtual": ("Orientacion veterinaria virtual", "Orientación veterinaria virtual"),
    "atencion_aliada": ("Atencion en clinica aliada", "Atención en clínica aliada"),
}
PASOS = {
    "valoracion": ("Valoracion clinica", "Valoración clínica"),
    "aplicacion": ("Aplicacion", "Aplicación"),
    "evidencia": ("Evidencia fotografica", "Evidencia fotográfica"),
}
ESQUEMAS = {
    "can_rabia": ("Antirrabica canina", "Antirrábica canina"),
    "can_desp_interna": ("Desparasitacion interna canina", "Desparasitación interna canina"),
    "can_desp_externa": ("Desparasitacion externa canina", "Desparasitación externa canina"),
    "fel_rabia": ("Antirrabica felina", "Antirrábica felina"),
    "fel_desp_interna": ("Desparasitacion interna felina", "Desparasitación interna felina"),
}
REGLAS = [
    ("Congelar a los 30 dias de mora", "Congelar a los 30 días de mora"),
    ("En mora desde 5 dias de vencida la cuota", "En mora desde 5 días de vencida la cuota"),
    ("Al dia", "Al día"),
    ("Aviso de mora a los 1 dias", "Aviso de mora a 1 día"),
    *((f"Aviso de mora a los {d} dias", f"Aviso de mora a los {d} días") for d in (5, 15, 25)),
    ("Gestionar renovacion 30 dias antes", "Gestionar renovación 30 días antes"),
]
ACCIONES = {
    "titulo": ("Gestionar renovacion del contrato", "Gestionar renovación del contrato"),
    "motivo": (
        "La familia debe estar al dia para cambiar de plan",
        "La familia debe estar al día para cambiar de plan",
    ),
}


def _aplicar(hacia_nuevo: bool) -> None:
    def par(viejo: str, nuevo: str) -> tuple[str, str]:
        return (viejo, nuevo) if hacia_nuevo else (nuevo, viejo)

    conexion = op.get_bind()
    for tabla, cambios in (("tipos_servicio", TIPOS), ("esquemas_preventivos", ESQUEMAS)):
        for codigo, (viejo, nuevo) in cambios.items():
            desde, hacia = par(viejo, nuevo)
            conexion.execute(
                sa.text(
                    f"UPDATE {tabla} SET nombre = :hacia WHERE codigo = :c AND nombre = :desde"
                ),  # noqa: S608
                {"hacia": hacia, "c": codigo, "desde": desde},
            )
    # Los pasos viven en el JSON de cada tipo de servicio.
    for tipo_id, pasos in conexion.execute(sa.text("SELECT id, pasos FROM tipos_servicio")).all():
        nuevos = []
        for paso in pasos or []:
            viejo, nuevo = PASOS.get(paso.get("codigo"), (None, None))
            desde, hacia = par(viejo, nuevo) if viejo else (None, None)
            nuevos.append(
                {**paso, "nombre": hacia} if desde and paso.get("nombre") == desde else paso
            )
        if nuevos != (pasos or []):
            conexion.execute(
                sa.text("UPDATE tipos_servicio SET pasos = CAST(:p AS jsonb) WHERE id = :i"),
                {"p": json.dumps(nuevos, ensure_ascii=False), "i": tipo_id},
            )
    for viejo, nuevo in REGLAS:
        desde, hacia = par(viejo, nuevo)
        conexion.execute(
            sa.text("UPDATE reglas SET nombre = :hacia WHERE nombre = :desde"),
            {"hacia": hacia, "desde": desde},
        )
    for clave, (viejo, nuevo) in ACCIONES.items():
        desde, hacia = par(viejo, nuevo)
        conexion.execute(
            sa.text(
                "UPDATE reglas SET accion = jsonb_set(accion, CAST(:ruta AS text[]), to_jsonb("
                "CAST(:hacia AS text))) WHERE accion->>:clave = :desde"
            ),
            {"ruta": [clave], "hacia": hacia, "clave": clave, "desde": desde},
        )


def upgrade() -> None:
    _aplicar(hacia_nuevo=True)


def downgrade() -> None:
    _aplicar(hacia_nuevo=False)

"""aliadas: una remision sin usar vence pasado el plazo para reportar

6.22 Una remision que vencia sin usarse dejaba su servicio agendado para siempre y, con el, ocupado
el cupo del beneficio (encontrado el 2026-11-16). Ahora, pasado el plazo para reportar
(`REMISION_GRACIA_REPORTE_DIAS` tras la vigencia), el proceso diario la pasa a `vencida` y cancela
su servicio. Estado nuevo, su arista en el grafo y que una vencida no tenga reporte.

Revision ID: 0064
Revises: 0063
Create Date: 2026-11-21 18:00:00
"""

from alembic import op

revision = "0064"
down_revision = "0063"
branch_labels = None
depends_on = None

ESTADOS_ANTERIORES = ("emitida", "utilizada", "anulada")
ARISTA = ("remisiones_aliadas", "estado", "emitida", "vencida")
# Compara como texto: el enum aun no admite el valor recien anadido dentro de la transaccion.
CHECK = (
    "ck_remisiones_aliadas_vencida_sin_reporte",
    "estado::text <> 'vencida' OR reportada_en IS NULL",
)
# Los que ya existian y comparan el estado (los del modelo, congelados aqui).
CHECKS_DEL_ESTADO = {
    "ck_remisiones_aliadas_utilizada_reportada": (
        "estado <> 'utilizada' OR (fecha_atencion IS NOT NULL AND reportada_en IS NOT NULL)"
    ),
    "ck_remisiones_aliadas_anulada_con_motivo": (
        "estado <> 'anulada' OR motivo_anulacion IS NOT NULL"
    ),
}


def upgrade() -> None:
    # El valor nuevo no se usa como dato en esta migracion: ADD VALUE admite la transaccion.
    op.execute("ALTER TYPE estado_remision ADD VALUE 'vencida'")
    tabla, columna, desde, hacia = ARISTA
    op.execute(
        "INSERT INTO transiciones_estado (tabla, columna, desde, hacia)"
        f" VALUES ('{tabla}', '{columna}', '{desde}', '{hacia}')"
    )
    nombre, expresion = CHECK
    op.execute(f"ALTER TABLE remisiones_aliadas ADD CONSTRAINT {nombre} CHECK ({expresion})")


def downgrade() -> None:
    # Una remision vencida no tiene forma en el modelo anterior: el downgrade falla con ellas en
    # vez de perderlas o hacerlas pasar por otro estado.
    op.execute(f"ALTER TABLE remisiones_aliadas DROP CONSTRAINT {CHECK[0]}")
    tabla, columna, desde, hacia = ARISTA
    op.execute(
        f"DELETE FROM transiciones_estado WHERE tabla = '{tabla}' AND columna = '{columna}'"
        f" AND desde = '{desde}' AND hacia = '{hacia}'"
    )
    # PostgreSQL no quita un valor de un enum: se recrea el tipo sin el.
    op.execute("ALTER TYPE estado_remision RENAME TO estado_remision_anterior")
    valores = ", ".join(f"'{v}'" for v in ESTADOS_ANTERIORES)
    op.execute(f"CREATE TYPE estado_remision AS ENUM ({valores})")
    # El trigger de transiciones y los CHECK que comparan el estado con el tipo viejo usan la
    # columna: se quitan mientras cambia de tipo y se vuelven a crear igual.
    op.execute("DROP TRIGGER tr_remisiones_aliadas_transicion_estado ON remisiones_aliadas")
    for nombre in CHECKS_DEL_ESTADO:
        op.execute(f"ALTER TABLE remisiones_aliadas DROP CONSTRAINT {nombre}")
    op.execute(
        "ALTER TABLE remisiones_aliadas ALTER COLUMN estado TYPE estado_remision"
        " USING estado::text::estado_remision"
    )
    op.execute("DROP TYPE estado_remision_anterior")
    for nombre, expresion in CHECKS_DEL_ESTADO.items():
        op.execute(f"ALTER TABLE remisiones_aliadas ADD CONSTRAINT {nombre} CHECK ({expresion})")
    op.execute(
        "CREATE TRIGGER tr_remisiones_aliadas_transicion_estado"
        " BEFORE UPDATE OF estado ON remisiones_aliadas FOR EACH ROW"
        " WHEN (old.estado IS DISTINCT FROM new.estado)"
        " EXECUTE FUNCTION validar_transicion('estado')"
    )

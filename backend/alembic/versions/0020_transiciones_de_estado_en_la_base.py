"""transiciones de estado en la base

Fase 2e de docs/plan-persistencia.md. Cada servicio validaba sus cambios de estado en Python;
ahora un trigger los valida en la base contra la tabla transiciones_estado, asi que ni un
UPDATE por SQL ni un error de codigo pueden saltarse el grafo (por ejemplo, reabrir una
historia clinica firmada o descompletar un servicio). La tabla solo la escribe el dueno del
esquema: la aplicacion no puede ampliar sus propios grafos. Las aristas estan escritas aqui;
app/core/transiciones.py es la fuente y test_persistencia compara las dos.

Revision ID: 0020
Revises: 0019
Create Date: 2026-11-04 23:00:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None

# (tabla, columna) con trigger de transicion
GRAFOS: list[tuple[str, str]] = [
    ("campanas", "estado"),
    ("destinatarios_campana", "estado"),
    ("ejecuciones_campana", "estado"),
    ("encuestas", "estado"),
    ("eventos_preventivos", "estado"),
    ("historias_clinicas", "estado"),
    ("paradas_ruta", "estado"),
    ("pendientes", "estado"),
    ("planificaciones_ruta", "estado"),
    ("prompts_ia", "estado"),
    ("remisiones_aliadas", "estado"),
    ("respuestas_virtuales", "estado"),
    ("rutas", "estado"),
    ("servicios", "estado"),
    ("solicitudes_afiliacion", "estado"),
    ("solicitudes_virtuales", "estado"),
    ("tareas", "estado"),
]

# (tabla, columna, desde, hacia)
ARISTAS: list[tuple[str, str, str, str]] = [
    ("campanas", "estado", "borrador", "cancelada"),
    ("campanas", "estado", "borrador", "en_envio"),
    ("campanas", "estado", "borrador", "programada"),
    ("campanas", "estado", "en_envio", "cancelada"),
    ("campanas", "estado", "en_envio", "finalizada"),
    ("campanas", "estado", "en_envio", "programada"),
    ("campanas", "estado", "programada", "cancelada"),
    ("campanas", "estado", "programada", "en_envio"),
    ("destinatarios_campana", "estado", "pendiente", "encolado"),
    ("destinatarios_campana", "estado", "pendiente", "excluido"),
    ("ejecuciones_campana", "estado", "en_envio", "cancelada"),
    ("ejecuciones_campana", "estado", "en_envio", "terminada"),
    ("encuestas", "estado", "enviada", "respondida"),
    ("encuestas", "estado", "pendiente", "enviada"),
    ("encuestas", "estado", "pendiente", "omitida"),
    ("eventos_preventivos", "estado", "programado", "aplicado"),
    ("eventos_preventivos", "estado", "programado", "cancelado"),
    ("historias_clinicas", "estado", "borrador", "firmada"),
    ("historias_clinicas", "estado", "firmada", "corregida"),
    ("paradas_ruta", "estado", "en_camino", "en_sitio"),
    ("paradas_ruta", "estado", "en_sitio", "completada"),
    ("paradas_ruta", "estado", "pendiente", "en_camino"),
    ("paradas_ruta", "estado", "pendiente", "en_sitio"),
    ("paradas_ruta", "estado", "pendiente", "omitida"),
    ("pendientes", "estado", "autorizado", "en_gestion"),
    ("pendientes", "estado", "autorizado", "resuelto"),
    ("pendientes", "estado", "en_gestion", "resuelto"),
    ("pendientes", "estado", "pendiente_autorizacion", "autorizado"),
    ("pendientes", "estado", "pendiente_autorizacion", "rechazado"),
    ("planificaciones_ruta", "estado", "pendiente", "fallida"),
    ("planificaciones_ruta", "estado", "pendiente", "lista"),
    ("prompts_ia", "estado", "activo", "retirado"),
    ("prompts_ia", "estado", "borrador", "activo"),
    ("prompts_ia", "estado", "retirado", "activo"),
    ("remisiones_aliadas", "estado", "emitida", "anulada"),
    ("remisiones_aliadas", "estado", "emitida", "utilizada"),
    ("respuestas_virtuales", "estado", "borrador", "aprobada"),
    ("rutas", "estado", "en_curso", "finalizada"),
    ("rutas", "estado", "planificada", "cancelada"),
    ("rutas", "estado", "planificada", "en_curso"),
    ("rutas", "estado", "planificada", "finalizada"),
    ("servicios", "estado", "agendado", "cancelado"),
    ("servicios", "estado", "agendado", "en_atencion"),
    ("servicios", "estado", "agendado", "en_ruta"),
    ("servicios", "estado", "agendado", "reprogramado"),
    ("servicios", "estado", "en_atencion", "cancelado"),
    ("servicios", "estado", "en_atencion", "completado"),
    ("servicios", "estado", "en_ruta", "cancelado"),
    ("servicios", "estado", "en_ruta", "en_atencion"),
    ("servicios", "estado", "en_ruta", "reprogramado"),
    ("servicios", "estado", "pendiente_autorizacion", "agendado"),
    ("servicios", "estado", "pendiente_autorizacion", "cancelado"),
    ("servicios", "estado", "reprogramado", "agendado"),
    ("servicios", "estado", "reprogramado", "cancelado"),
    ("servicios", "estado", "solicitado", "agendado"),
    ("servicios", "estado", "solicitado", "cancelado"),
    ("servicios", "estado", "solicitado", "pendiente_autorizacion"),
    ("solicitudes_afiliacion", "estado", "error", "completada"),
    ("solicitudes_afiliacion", "estado", "pendiente_pago", "cancelada"),
    ("solicitudes_afiliacion", "estado", "pendiente_pago", "completada"),
    ("solicitudes_afiliacion", "estado", "pendiente_pago", "error"),
    ("solicitudes_virtuales", "estado", "en_atencion", "respondida"),
    ("solicitudes_virtuales", "estado", "en_cola", "en_atencion"),
    ("solicitudes_virtuales", "estado", "respondida", "cerrada"),
    ("tareas", "estado", "abierta", "cerrada"),
    ("tareas", "estado", "abierta", "en_progreso"),
    ("tareas", "estado", "en_progreso", "cerrada"),
]


def upgrade() -> None:
    op.create_table(
        "transiciones_estado",
        sa.Column("tabla", sa.String(length=64), nullable=False),
        sa.Column("columna", sa.String(length=64), nullable=False),
        sa.Column("desde", sa.String(length=40), nullable=False),
        sa.Column("hacia", sa.String(length=40), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.CheckConstraint(
            "uuid_extract_version(id) = 7", name=op.f("ck_transiciones_estado_id_uuidv7")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transiciones_estado")),
    )
    op.create_index(
        "uq_transiciones_estado_arista",
        "transiciones_estado",
        ["tabla", "columna", "desde", "hacia"],
        unique=True,
    )
    # La aplicacion no lee ni escribe los grafos: los consulta el trigger como dueno.
    op.execute("REVOKE ALL ON transiciones_estado FROM timu_app")
    op.bulk_insert(
        sa.table(
            "transiciones_estado",
            sa.column("tabla", sa.String),
            sa.column("columna", sa.String),
            sa.column("desde", sa.String),
            sa.column("hacia", sa.String),
        ),
        [{"tabla": t, "columna": c, "desde": d, "hacia": h} for t, c, d, h in ARISTAS],
    )
    op.execute(
        """
        CREATE FUNCTION validar_transicion() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
        DECLARE
            v_columna text := TG_ARGV[0];
            v_desde text;
            v_hacia text;
        BEGIN
            EXECUTE format('SELECT ($1).%I::text, ($2).%I::text', v_columna, v_columna)
                INTO v_desde, v_hacia USING OLD, NEW;
            IF v_desde IS DISTINCT FROM v_hacia AND NOT EXISTS (
                SELECT 1 FROM transiciones_estado t
                WHERE t.tabla = TG_TABLE_NAME AND t.columna = v_columna
                  AND t.desde = v_desde AND t.hacia = v_hacia
            ) THEN
                RAISE EXCEPTION 'Transicion no permitida en %.%: % -> %',
                    TG_TABLE_NAME, v_columna, v_desde, v_hacia
                    USING ERRCODE = 'check_violation',
                          CONSTRAINT = 'transicion_' || TG_TABLE_NAME || '_' || v_columna;
            END IF;
            RETURN NEW;
        END
        $$
        """
    )
    for tabla, columna in GRAFOS:
        op.execute(
            f"CREATE TRIGGER tr_{tabla}_transicion_{columna} BEFORE UPDATE OF {columna}"
            f" ON {tabla} FOR EACH ROW WHEN (OLD.{columna} IS DISTINCT FROM NEW.{columna})"
            f" EXECUTE FUNCTION validar_transicion('{columna}')"
        )


def downgrade() -> None:
    for tabla, columna in GRAFOS:
        op.execute(f"DROP TRIGGER tr_{tabla}_transicion_{columna} ON {tabla}")
    op.execute("DROP FUNCTION validar_transicion()")
    op.drop_index("uq_transiciones_estado_arista", table_name="transiciones_estado")
    op.drop_table("transiciones_estado")

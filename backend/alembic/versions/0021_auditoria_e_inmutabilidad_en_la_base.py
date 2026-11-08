"""auditoria e inmutabilidad en la base

Fases 2f y 2g de docs/plan-persistencia.md.

Auditoria: la escribia un listener de SQLAlchemy, asi que un UPDATE por SQL, un script o una
migracion no dejaban rastro, y la tabla se podia editar y borrar. Ahora la escribe auditar(),
un trigger AFTER en cada tabla auditable, con el usuario y la peticion del contexto de la
transaccion (app.usuario_id, app.request_id). El formato de `cambios` es el mismo que tenia.
La aplicacion solo puede leer la bitacora.

Inmutabilidad: una historia clinica firmada no se edita (solo pasa a corregida), y los
registros que son constancia de algo (carnet emitido, formula, adjunto clinico, aplicacion de
un pago, cambio de plan salvo su marca de aplicado, la propia bitacora) no cambian una vez
escritos. Solo el dueno del esquema puede tocarlos, para la anonimizacion de la fase 3.

Revision ID: 0021
Revises: 0020
Create Date: 2026-11-04 23:30:00
"""

from alembic import op

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None

AUDITABLES: list[str] = [
    "adjuntos_clinicos",
    "arboles_conversacion",
    "beneficios_plan",
    "campanas",
    "casos_prueba_ia",
    "clinicas_aliadas",
    "configuraciones_encuesta",
    "contratos",
    "convenios_aliadas",
    "cuotas",
    "eventos_preventivos",
    "familias",
    "formulas",
    "franjas_agenda",
    "historias_clinicas",
    "interesados",
    "mascotas",
    "medios_pago_recurrente",
    "pagos",
    "paradas_ruta",
    "pendientes",
    "planes",
    "plantillas_consulta",
    "prompts_ia",
    "reglas",
    "remisiones_aliadas",
    "reportes_programados",
    "respuestas_virtuales",
    "rutas",
    "segmentos",
    "servicio_pasos",
    "servicios",
    "solicitudes_afiliacion",
    "solicitudes_virtuales",
    "tareas",
    "usuarios",
]

# tabla -> columnas que si pueden cambiar
INMUTABLES: dict[str, list[str]] = {
    "adjuntos_clinicos": [],
    "aplicaciones_pago": [],
    "auditoria": [],
    "cambios_plan": ["aplicado"],
    "carnets_emitidos": [],
    "formulas": [],
}

_DUENO = "current_user = (SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid = TG_RELID)"


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION auditar() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
        DECLARE
            v_antes jsonb := CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE to_jsonb(OLD) END;
            v_despues jsonb := CASE WHEN TG_OP = 'DELETE' THEN NULL ELSE to_jsonb(NEW) END;
            v_numericas text[];
            v_cambios jsonb := '{}'::jsonb;
            v_clave text;
            v_a jsonb;
            v_d jsonb;
        BEGIN
            -- Los importes se guardan como texto ("45000.00"), como hacia la aplicacion.
            SELECT coalesce(array_agg(attname::text), '{}') INTO v_numericas
            FROM pg_attribute
            WHERE attrelid = TG_RELID AND atttypid = 'numeric'::regtype
              AND attnum > 0 AND NOT attisdropped;
            FOR v_clave IN
                SELECT k FROM jsonb_object_keys(coalesce(v_despues, v_antes)) AS k
                WHERE k NOT IN ('created_at', 'updated_at', 'hashed_password')
            LOOP
                v_a := v_antes -> v_clave;
                v_d := v_despues -> v_clave;
                IF v_clave = ANY (v_numericas) THEN
                    v_a := to_jsonb(v_antes ->> v_clave);
                    v_d := to_jsonb(v_despues ->> v_clave);
                END IF;
                IF TG_OP <> 'UPDATE' OR v_a IS DISTINCT FROM v_d THEN
                    v_cambios := v_cambios
                        || jsonb_build_object(v_clave, jsonb_build_array(v_a, v_d));
                END IF;
            END LOOP;
            IF TG_OP = 'UPDATE' AND v_cambios = '{}'::jsonb THEN
                RETURN NULL;
            END IF;
            INSERT INTO auditoria
                (created_at, usuario_id, request_id, entidad, entidad_id, accion, cambios)
            VALUES (
                clock_timestamp(),
                nullif(current_setting('app.usuario_id', true), '')::uuid,
                nullif(current_setting('app.request_id', true), ''),
                TG_TABLE_NAME,
                coalesce(v_despues, v_antes) ->> 'id',
                CASE TG_OP
                    WHEN 'INSERT' THEN 'crear'
                    WHEN 'DELETE' THEN 'eliminar'
                    ELSE CASE WHEN v_cambios ? 'estado' THEN 'cambio_estado' ELSE 'editar' END
                END::accion,
                v_cambios
            );
            RETURN NULL;
        END
        $$
        """
    )
    for tabla in AUDITABLES:
        op.execute(
            f"CREATE TRIGGER tr_{tabla}_auditoria AFTER INSERT OR UPDATE OR DELETE ON {tabla}"
            " FOR EACH ROW EXECUTE FUNCTION auditar()"
        )

    op.execute(
        f"""
        CREATE FUNCTION inmutable() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE
            v_libres text[] := TG_ARGV || ARRAY['updated_at'];
        BEGIN
            IF {_DUENO} THEN
                RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
            END IF;
            IF TG_OP = 'DELETE'
               OR (to_jsonb(NEW) - v_libres) IS DISTINCT FROM (to_jsonb(OLD) - v_libres) THEN
                RAISE EXCEPTION 'Las filas de % no se modifican una vez escritas', TG_TABLE_NAME
                    USING ERRCODE = 'check_violation', CONSTRAINT = 'inmutable_' || TG_TABLE_NAME;
            END IF;
            RETURN NEW;
        END
        $$
        """
    )
    for tabla, libres in INMUTABLES.items():
        operaciones = "UPDATE OR DELETE" if tabla == "auditoria" else "UPDATE"
        argumentos = ", ".join(f"'{c}'" for c in libres)
        op.execute(
            f"CREATE TRIGGER tr_{tabla}_inmutable BEFORE {operaciones} ON {tabla}"
            f" FOR EACH ROW EXECUTE FUNCTION inmutable({argumentos})"
        )
    # La bitacora solo la escribe auditar(), como dueno.
    op.execute("REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON auditoria FROM timu_app")

    op.execute(
        f"""
        CREATE FUNCTION historia_firmada_inmutable() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF {_DUENO} THEN
                RETURN NEW;
            END IF;
            IF OLD.estado <> 'borrador'
               AND (to_jsonb(NEW) - ARRAY['estado', 'updated_at'])
                   IS DISTINCT FROM (to_jsonb(OLD) - ARRAY['estado', 'updated_at']) THEN
                RAISE EXCEPTION
                    'Una historia clinica firmada no se edita: se corrige con una nueva version'
                    USING ERRCODE = 'check_violation', CONSTRAINT = 'inmutable_historias_clinicas';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )
    op.execute(
        "CREATE TRIGGER tr_historias_clinicas_firmada BEFORE UPDATE ON historias_clinicas"
        " FOR EACH ROW EXECUTE FUNCTION historia_firmada_inmutable()"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER tr_historias_clinicas_firmada ON historias_clinicas")
    op.execute("DROP FUNCTION historia_firmada_inmutable()")
    op.execute("GRANT INSERT, UPDATE, DELETE ON auditoria TO timu_app")
    for tabla in INMUTABLES:
        op.execute(f"DROP TRIGGER tr_{tabla}_inmutable ON {tabla}")
    op.execute("DROP FUNCTION inmutable()")
    for tabla in AUDITABLES:
        op.execute(f"DROP TRIGGER tr_{tabla}_auditoria ON {tabla}")
    op.execute("DROP FUNCTION auditar()")

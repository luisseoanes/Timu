"""sin borrado fisico y anonimizacion

Fase 3 de docs/plan-persistencia.md.

- La aplicacion pierde DELETE en todas las tablas salvo las de estado tecnico (BORRABLES en
  app/core/database.py). Los dos sitios que borraban pasan a estados: reactivar los envios
  cierra la baja (reactivada_en) y reemplazar los beneficios de un plan desactiva los
  anteriores (activo). La unicidad de ambas pasa a ser entre filas vigentes.
- anonimizar_familia(id) es el unico borrado: habeas data (Ley 1581). Sustituye los datos
  personales de la familia y de lo que la identifica, limpia su rastro en la bitacora y
  devuelve las claves de almacenamiento de las fotos y los PDF que la aplicacion borra
  despues de confirmar. Lo clinico y lo contable se conserva. Solo la ejecuta un contexto
  de administrador y se niega con un contrato vigente.

Revision ID: 0022
Revises: 0021
Create Date: 2026-11-04 18:23:02.062082
"""

import sqlalchemy as sa

from alembic import op

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None

# Tablas de estado tecnico en las que la aplicacion conserva DELETE (copia de BORRABLES).
BORRABLES = (
    "consumo_mapas",
    "distancias_cache",
    "eventos_salientes",
    "sesiones",
    "tokens_uso_unico",
)

_ANONIMIZAR = """
CREATE FUNCTION anonimizar_familia(p_familia uuid) RETURNS SETOF text
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE
    f familias%ROWTYPE;
    v_ids text[];
    v_anonimo constant text := '[anonimizado]';
    -- Prefijo internacional 999: no esta asignado a ningun pais.
    v_telefono constant text := '+99900000000';
    v_quitar constant text[] :=
        ARRAY['ip', 'user_agent', 'nombre', 'documento', 'email', 'telefono'];
    v_personales constant text[] := ARRAY[
        'titular_nombre', 'documento', 'email', 'telefono', 'direccion', 'latitud', 'longitud',
        'notas', 'motivo_baja', 'nombre', 'destino', 'contenido', 'asunto', 'variables',
        'email_titular', 'ultimos4', 'comentario', 'aceptacion', 'evidencia_aceptacion', 'datos'
    ];
BEGIN
    IF current_setting('app.rol', true) IS DISTINCT FROM 'admin' THEN
        RAISE EXCEPTION 'Solo un administrador anonimiza una familia'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    SELECT * INTO f FROM familias WHERE id = p_familia FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Familia % no encontrada', p_familia USING ERRCODE = 'no_data_found';
    END IF;
    IF f.anonimizada_en IS NOT NULL THEN
        RAISE EXCEPTION 'La familia ya esta anonimizada' USING ERRCODE = 'check_violation';
    END IF;
    IF EXISTS (
        SELECT 1 FROM contratos
        WHERE familia_id = p_familia AND estado IN ('activa', 'en_mora', 'congelada')
    ) THEN
        RAISE EXCEPTION 'La familia tiene un contrato vigente' USING ERRCODE = 'check_violation';
    END IF;

    -- Ficheros con datos personales: fotos de las mascotas y PDF de contratos y carnets.
    RETURN QUERY
        WITH purgados AS (
            UPDATE archivos a SET purgado_en = now()
            WHERE a.purgado_en IS NULL AND a.id IN (
                SELECT foto_archivo_id FROM mascotas WHERE familia_id = p_familia
                UNION SELECT documento_archivo_id FROM contratos WHERE familia_id = p_familia
                UNION SELECT c.archivo_id FROM carnets_emitidos c
                      JOIN mascotas m ON m.id = c.mascota_id WHERE m.familia_id = p_familia
            )
            RETURNING a.clave
        )
        SELECT clave::text FROM purgados;

    UPDATE mascotas SET nombre = 'Mascota', foto_archivo_id = NULL WHERE familia_id = p_familia;
    IF f.usuario_portal_id IS NOT NULL THEN
        UPDATE usuarios
        SET nombre = 'Anonimizado', email = 'anonimizado-' || id || '@invalid.local',
            telefono = NULL, activo = false
        WHERE id = f.usuario_portal_id;
        UPDATE sesiones SET revocada_en = coalesce(revocada_en, now())
        WHERE usuario_id = f.usuario_portal_id;
        UPDATE tokens_uso_unico SET expira_en = least(expira_en, now())
        WHERE usuario_id = f.usuario_portal_id;
    END IF;
    DELETE FROM conversaciones_comerciales
    WHERE telefono = f.telefono
       OR interesado_id IN (SELECT id FROM interesados WHERE familia_id = p_familia);
    DELETE FROM conversaciones_whatsapp WHERE familia_id = p_familia OR telefono = f.telefono;
    UPDATE interesados SET nombre = NULL, telefono = NULL, email = NULL, datos = '{}'
    WHERE familia_id = p_familia;
    UPDATE mensajes SET destino = NULL, contenido = NULL, asunto = NULL, variables = '[]'
    WHERE familia_id = p_familia;
    UPDATE solicitudes_afiliacion SET aceptacion = aceptacion - v_quitar
    WHERE familia_id = p_familia;
    UPDATE contratos SET evidencia_aceptacion = evidencia_aceptacion - v_quitar
    WHERE familia_id = p_familia;
    UPDATE medios_pago_recurrente
    SET email_titular = 'anonimizado@invalid.local', ultimos4 = NULL, activo = false
    WHERE familia_id = p_familia;
    UPDATE encuestas SET comentario = NULL WHERE familia_id = p_familia;
    UPDATE destinatarios_campana SET telefono = v_telefono WHERE familia_id = p_familia;
    UPDATE familias
    SET titular_nombre = 'Anonimizado',
        documento = 'ANON' || upper(substr(replace(id::text, '-', ''), 1, 28)),
        email = NULL, telefono = v_telefono, direccion = NULL, latitud = NULL,
        longitud = NULL, geo_precision = NULL, notas = NULL, estado = 'cancelada',
        dada_de_baja_en = coalesce(dada_de_baja_en, now()),
        motivo_baja = 'Anonimizada (habeas data)', anonimizada_en = now()
    WHERE id = p_familia;

    -- El rastro en la bitacora, incluido el que acaba de dejar esta misma funcion.
    v_ids := ARRAY(
        SELECT p_familia::text
        UNION SELECT f.usuario_portal_id::text WHERE f.usuario_portal_id IS NOT NULL
        UNION SELECT id::text FROM mascotas WHERE familia_id = p_familia
        UNION SELECT id::text FROM interesados WHERE familia_id = p_familia
        UNION SELECT id::text FROM mensajes WHERE familia_id = p_familia
        UNION SELECT id::text FROM solicitudes_afiliacion WHERE familia_id = p_familia
        UNION SELECT id::text FROM medios_pago_recurrente WHERE familia_id = p_familia
        UNION SELECT id::text FROM encuestas WHERE familia_id = p_familia
        UNION SELECT id::text FROM contratos WHERE familia_id = p_familia
    );
    UPDATE auditoria a
    SET cambios = (
        SELECT jsonb_object_agg(
            e.k, CASE WHEN e.k = ANY (v_personales) THEN jsonb_build_array(v_anonimo, v_anonimo)
                      ELSE e.v END)
        FROM jsonb_each(a.cambios) AS e(k, v)
    )
    WHERE a.entidad_id = ANY (v_ids)
      AND EXISTS (SELECT 1 FROM jsonb_object_keys(a.cambios) AS k WHERE k = ANY (v_personales));
    RETURN;
END
$$
"""


def upgrade() -> None:
    op.add_column("archivos", sa.Column("purgado_en", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "bajas_comunicaciones",
        sa.Column("reactivada_en", sa.DateTime(timezone=True), nullable=True),
    )
    op.drop_constraint("uq_bajas_comunicaciones_destino", "bajas_comunicaciones", type_="unique")
    op.create_index(
        op.f("ix_bajas_comunicaciones_destino"), "bajas_comunicaciones", ["destino"], unique=False
    )
    op.create_index(
        "uq_bajas_comunicaciones_destino_activa",
        "bajas_comunicaciones",
        ["destino"],
        unique=True,
        postgresql_where=sa.text("reactivada_en IS NULL"),
    )
    # Los beneficios existentes estan vigentes; el default solo sirve para rellenarlos.
    op.add_column(
        "beneficios_plan",
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column("beneficios_plan", "activo", server_default=None)
    op.drop_constraint("uq_beneficios_plan_plan_id", "beneficios_plan", type_="unique")
    op.create_index(
        "uq_beneficios_plan_tipo_vigente",
        "beneficios_plan",
        ["plan_id", "tipo_servicio_codigo"],
        unique=True,
        postgresql_where=sa.text("activo"),
    )
    op.add_column(
        "familias", sa.Column("anonimizada_en", sa.DateTime(timezone=True), nullable=True)
    )

    op.execute(
        "DO $$ DECLARE t text; BEGIN"
        " FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        " AND tablename <> ALL (ARRAY[" + ", ".join(f"'{t}'" for t in sorted(BORRABLES)) + "])"
        " LOOP EXECUTE format('REVOKE DELETE ON %I FROM timu_app', t); END LOOP; END $$"
    )
    # Las tablas que creen las migraciones siguientes tampoco dan DELETE a la aplicacion.
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE DELETE ON TABLES FROM timu_app")
    op.execute(_ANONIMIZAR)
    op.execute("REVOKE ALL ON FUNCTION anonimizar_familia(uuid) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION anonimizar_familia(uuid) TO timu_app")


def downgrade() -> None:
    op.drop_column("familias", "anonimizada_en")
    op.drop_index(
        "uq_beneficios_plan_tipo_vigente",
        table_name="beneficios_plan",
        postgresql_where=sa.text("activo"),
    )
    op.create_unique_constraint(
        "uq_beneficios_plan_plan_id", "beneficios_plan", ["plan_id", "tipo_servicio_codigo"]
    )
    op.drop_column("beneficios_plan", "activo")
    op.drop_index(
        "uq_bajas_comunicaciones_destino_activa",
        table_name="bajas_comunicaciones",
        postgresql_where=sa.text("reactivada_en IS NULL"),
    )
    op.drop_index(op.f("ix_bajas_comunicaciones_destino"), table_name="bajas_comunicaciones")
    op.create_unique_constraint(
        "uq_bajas_comunicaciones_destino", "bajas_comunicaciones", ["destino"]
    )
    op.drop_column("bajas_comunicaciones", "reactivada_en")
    op.drop_column("archivos", "purgado_en")
    op.execute("DROP FUNCTION anonimizar_familia(uuid)")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT DELETE ON TABLES TO timu_app")
    op.execute(
        "DO $$ DECLARE t text; BEGIN"
        " FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        " AND tablename NOT IN ('alembic_version', 'transiciones_estado', 'auditoria')"
        " LOOP EXECUTE format('GRANT DELETE ON %I TO timu_app', t); END LOOP; END $$"
    )

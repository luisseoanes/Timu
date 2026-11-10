# ruff: noqa: E501  (politicas y funcion congeladas: expresiones SQL largas)
"""familias: contactos adicionales

6.1 pide los usuarios asociados de cada familia; TIMU los quiere como contactos adicionales
sin acceso a la plataforma ni mensajes: nombre, telefono, relacion y correo opcionales.
Como mucho tres vigentes: cada uno ocupa una posicion del 1 al 3, unica entre los vigentes,
asi que la base rechaza el cuarto aunque lleguen dos altas a la vez.

La tabla lleva su auditoria, RLS con las politicas de app/core/permisos_db.py (escritas aqui,
congeladas) y entra en anonimizar_familia(): las dos versiones de la funcion estan aqui.

Revision ID: 0029
Revises: 0028
Create Date: 2026-11-10 19:00:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None

# (nombre, tabla, comando, rol, USING, WITH CHECK), de politicas(['contactos_familia'])
POLITICAS = [
    (
        "p_contactos_familia_select",
        "contactos_familia",
        "SELECT",
        "timu_app",
        "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
        None,
    ),
    (
        "p_contactos_familia_insert",
        "contactos_familia",
        "INSERT",
        "timu_app",
        None,
        "app_rol() IN ('sistema', 'admin', 'comercial', 'operaciones')",
    ),
    (
        "p_contactos_familia_update",
        "contactos_familia",
        "UPDATE",
        "timu_app",
        "app_rol() IN ('sistema', 'admin', 'comercial', 'operaciones')",
        "app_rol() IN ('sistema', 'admin', 'comercial', 'operaciones')",
    ),
    (
        "p_contactos_familia_delete",
        "contactos_familia",
        "DELETE",
        "timu_app",
        "app_rol() IN ('sistema')",
        None,
    ),
]

_ANONIMIZAR_ANTERIOR = "\nCREATE OR REPLACE FUNCTION anonimizar_familia(p_familia uuid) RETURNS SETOF text\nLANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$\nDECLARE\n    f familias%ROWTYPE;\n    v_ids text[];\n    v_anonimo constant text := '[anonimizado]';\n    -- Prefijo internacional 999: no esta asignado a ningun pais.\n    v_telefono constant text := '+99900000000';\n    v_quitar constant text[] :=\n        ARRAY['ip', 'user_agent', 'nombre', 'documento', 'email', 'telefono'];\n    v_personales constant text[] := ARRAY[\n        'titular_nombre', 'documento', 'email', 'telefono', 'barrio', 'direccion',\n        'complemento', 'latitud', 'longitud',\n        'notas', 'motivo_baja', 'nombre', 'destino', 'contenido', 'asunto', 'variables',\n        'email_titular', 'ultimos4', 'comentario', 'aceptacion', 'evidencia_aceptacion', 'datos'\n    ];\nBEGIN\n    IF current_setting('app.rol', true) IS DISTINCT FROM 'admin' THEN\n        RAISE EXCEPTION 'Solo un administrador anonimiza una familia'\n            USING ERRCODE = 'insufficient_privilege';\n    END IF;\n    SELECT * INTO f FROM familias WHERE id = p_familia FOR UPDATE;\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'Familia % no encontrada', p_familia USING ERRCODE = 'no_data_found';\n    END IF;\n    IF f.anonimizada_en IS NOT NULL THEN\n        RAISE EXCEPTION 'La familia ya esta anonimizada' USING ERRCODE = 'check_violation';\n    END IF;\n    IF EXISTS (\n        SELECT 1 FROM contratos\n        WHERE familia_id = p_familia AND estado IN ('activa', 'en_mora', 'congelada')\n    ) THEN\n        RAISE EXCEPTION 'La familia tiene un contrato vigente' USING ERRCODE = 'check_violation';\n    END IF;\n\n    -- Ficheros con datos personales: fotos de las mascotas y PDF de contratos y carnets.\n    RETURN QUERY\n        WITH purgados AS (\n            UPDATE archivos a SET purgado_en = now()\n            WHERE a.purgado_en IS NULL AND a.id IN (\n                SELECT foto_archivo_id FROM mascotas WHERE familia_id = p_familia\n                UNION SELECT documento_archivo_id FROM contratos WHERE familia_id = p_familia\n                UNION SELECT c.archivo_id FROM carnets_emitidos c\n                      JOIN mascotas m ON m.id = c.mascota_id WHERE m.familia_id = p_familia\n            )\n            RETURNING a.clave\n        )\n        SELECT clave::text FROM purgados;\n\n    UPDATE mascotas SET nombre = 'Mascota', foto_archivo_id = NULL WHERE familia_id = p_familia;\n    IF f.usuario_portal_id IS NOT NULL THEN\n        UPDATE usuarios\n        SET nombre = 'Anonimizado', email = 'anonimizado-' || id || '@invalid.local',\n            telefono = NULL, activo = false\n        WHERE id = f.usuario_portal_id;\n        UPDATE sesiones SET revocada_en = coalesce(revocada_en, now())\n        WHERE usuario_id = f.usuario_portal_id;\n        UPDATE tokens_uso_unico SET expira_en = least(expira_en, now())\n        WHERE usuario_id = f.usuario_portal_id;\n    END IF;\n    DELETE FROM conversaciones_comerciales\n    WHERE telefono = f.telefono\n       OR interesado_id IN (SELECT id FROM interesados WHERE familia_id = p_familia);\n    DELETE FROM conversaciones_whatsapp WHERE familia_id = p_familia OR telefono = f.telefono;\n    UPDATE interesados SET nombre = NULL, telefono = NULL, email = NULL, datos = '{}'\n    WHERE familia_id = p_familia;\n    UPDATE mensajes SET destino = NULL, contenido = NULL, asunto = NULL, variables = '[]'\n    WHERE familia_id = p_familia;\n    UPDATE solicitudes_afiliacion SET aceptacion = aceptacion - v_quitar\n    WHERE familia_id = p_familia;\n    UPDATE contratos SET evidencia_aceptacion = evidencia_aceptacion - v_quitar\n    WHERE familia_id = p_familia;\n    UPDATE medios_pago_recurrente\n    SET email_titular = 'anonimizado@invalid.local', ultimos4 = NULL, activo = false\n    WHERE familia_id = p_familia;\n    UPDATE encuestas SET comentario = NULL WHERE familia_id = p_familia;\n    UPDATE destinatarios_campana SET telefono = v_telefono WHERE familia_id = p_familia;\n    UPDATE familias\n    SET titular_nombre = 'Anonimizado',\n        documento = 'ANON' || upper(substr(replace(id::text, '-', ''), 1, 28)),\n        email = NULL, telefono = v_telefono, barrio = 'Anonimizado', direccion = NULL,\n        complemento = NULL, latitud = NULL,\n        longitud = NULL, geo_precision = NULL, notas = NULL, estado = 'cancelada',\n        dada_de_baja_en = coalesce(dada_de_baja_en, now()),\n        motivo_baja = 'Anonimizada (habeas data)', anonimizada_en = now()\n    WHERE id = p_familia;\n\n    -- El rastro en la bitacora, incluido el que acaba de dejar esta misma funcion.\n    v_ids := ARRAY(\n        SELECT p_familia::text\n        UNION SELECT f.usuario_portal_id::text WHERE f.usuario_portal_id IS NOT NULL\n        UNION SELECT id::text FROM mascotas WHERE familia_id = p_familia\n        UNION SELECT id::text FROM interesados WHERE familia_id = p_familia\n        UNION SELECT id::text FROM mensajes WHERE familia_id = p_familia\n        UNION SELECT id::text FROM solicitudes_afiliacion WHERE familia_id = p_familia\n        UNION SELECT id::text FROM medios_pago_recurrente WHERE familia_id = p_familia\n        UNION SELECT id::text FROM encuestas WHERE familia_id = p_familia\n        UNION SELECT id::text FROM contratos WHERE familia_id = p_familia\n    );\n    UPDATE auditoria a\n    SET cambios = (\n        SELECT jsonb_object_agg(\n            e.k, CASE WHEN e.k = ANY (v_personales) THEN jsonb_build_array(v_anonimo, v_anonimo)\n                      ELSE e.v END)\n        FROM jsonb_each(a.cambios) AS e(k, v)\n    )\n    WHERE a.entidad_id = ANY (v_ids)\n      AND EXISTS (SELECT 1 FROM jsonb_object_keys(a.cambios) AS k WHERE k = ANY (v_personales));\n    RETURN;\nEND\n$$\n"

_ANONIMIZAR = "\nCREATE OR REPLACE FUNCTION anonimizar_familia(p_familia uuid) RETURNS SETOF text\nLANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$\nDECLARE\n    f familias%ROWTYPE;\n    v_ids text[];\n    v_anonimo constant text := '[anonimizado]';\n    -- Prefijo internacional 999: no esta asignado a ningun pais.\n    v_telefono constant text := '+99900000000';\n    v_quitar constant text[] :=\n        ARRAY['ip', 'user_agent', 'nombre', 'documento', 'email', 'telefono'];\n    v_personales constant text[] := ARRAY[\n        'titular_nombre', 'documento', 'email', 'telefono', 'barrio', 'direccion', 'relacion',\n        'complemento', 'latitud', 'longitud',\n        'notas', 'motivo_baja', 'nombre', 'destino', 'contenido', 'asunto', 'variables',\n        'email_titular', 'ultimos4', 'comentario', 'aceptacion', 'evidencia_aceptacion', 'datos'\n    ];\nBEGIN\n    IF current_setting('app.rol', true) IS DISTINCT FROM 'admin' THEN\n        RAISE EXCEPTION 'Solo un administrador anonimiza una familia'\n            USING ERRCODE = 'insufficient_privilege';\n    END IF;\n    SELECT * INTO f FROM familias WHERE id = p_familia FOR UPDATE;\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'Familia % no encontrada', p_familia USING ERRCODE = 'no_data_found';\n    END IF;\n    IF f.anonimizada_en IS NOT NULL THEN\n        RAISE EXCEPTION 'La familia ya esta anonimizada' USING ERRCODE = 'check_violation';\n    END IF;\n    IF EXISTS (\n        SELECT 1 FROM contratos\n        WHERE familia_id = p_familia AND estado IN ('activa', 'en_mora', 'congelada')\n    ) THEN\n        RAISE EXCEPTION 'La familia tiene un contrato vigente' USING ERRCODE = 'check_violation';\n    END IF;\n\n    -- Ficheros con datos personales: fotos de las mascotas y PDF de contratos y carnets.\n    RETURN QUERY\n        WITH purgados AS (\n            UPDATE archivos a SET purgado_en = now()\n            WHERE a.purgado_en IS NULL AND a.id IN (\n                SELECT foto_archivo_id FROM mascotas WHERE familia_id = p_familia\n                UNION SELECT documento_archivo_id FROM contratos WHERE familia_id = p_familia\n                UNION SELECT c.archivo_id FROM carnets_emitidos c\n                      JOIN mascotas m ON m.id = c.mascota_id WHERE m.familia_id = p_familia\n            )\n            RETURNING a.clave\n        )\n        SELECT clave::text FROM purgados;\n\n    UPDATE mascotas SET nombre = 'Mascota', foto_archivo_id = NULL WHERE familia_id = p_familia;\n    IF f.usuario_portal_id IS NOT NULL THEN\n        UPDATE usuarios\n        SET nombre = 'Anonimizado', email = 'anonimizado-' || id || '@invalid.local',\n            telefono = NULL, activo = false\n        WHERE id = f.usuario_portal_id;\n        UPDATE sesiones SET revocada_en = coalesce(revocada_en, now())\n        WHERE usuario_id = f.usuario_portal_id;\n        UPDATE tokens_uso_unico SET expira_en = least(expira_en, now())\n        WHERE usuario_id = f.usuario_portal_id;\n    END IF;\n    DELETE FROM conversaciones_comerciales\n    WHERE telefono = f.telefono\n       OR interesado_id IN (SELECT id FROM interesados WHERE familia_id = p_familia);\n    DELETE FROM conversaciones_whatsapp WHERE familia_id = p_familia OR telefono = f.telefono;\n    UPDATE interesados SET nombre = NULL, telefono = NULL, email = NULL, datos = '{}'\n    WHERE familia_id = p_familia;\n    UPDATE mensajes SET destino = NULL, contenido = NULL, asunto = NULL, variables = '[]'\n    WHERE familia_id = p_familia;\n    UPDATE solicitudes_afiliacion SET aceptacion = aceptacion - v_quitar\n    WHERE familia_id = p_familia;\n    UPDATE contratos SET evidencia_aceptacion = evidencia_aceptacion - v_quitar\n    WHERE familia_id = p_familia;\n    UPDATE medios_pago_recurrente\n    SET email_titular = 'anonimizado@invalid.local', ultimos4 = NULL, activo = false\n    WHERE familia_id = p_familia;\n    UPDATE encuestas SET comentario = NULL WHERE familia_id = p_familia;\n    UPDATE destinatarios_campana SET telefono = v_telefono WHERE familia_id = p_familia;\n    UPDATE contactos_familia\n    SET nombre = 'Anonimizado', telefono = v_telefono, email = NULL, relacion = NULL\n    WHERE familia_id = p_familia;\n    UPDATE familias\n    SET titular_nombre = 'Anonimizado',\n        documento = 'ANON' || upper(substr(replace(id::text, '-', ''), 1, 28)),\n        email = NULL, telefono = v_telefono, barrio = 'Anonimizado', direccion = NULL,\n        complemento = NULL, latitud = NULL,\n        longitud = NULL, geo_precision = NULL, notas = NULL, estado = 'cancelada',\n        dada_de_baja_en = coalesce(dada_de_baja_en, now()),\n        motivo_baja = 'Anonimizada (habeas data)', anonimizada_en = now()\n    WHERE id = p_familia;\n\n    -- El rastro en la bitacora, incluido el que acaba de dejar esta misma funcion.\n    v_ids := ARRAY(\n        SELECT p_familia::text\n        UNION SELECT f.usuario_portal_id::text WHERE f.usuario_portal_id IS NOT NULL\n        UNION SELECT id::text FROM mascotas WHERE familia_id = p_familia\n        UNION SELECT id::text FROM contactos_familia WHERE familia_id = p_familia\n        UNION SELECT id::text FROM interesados WHERE familia_id = p_familia\n        UNION SELECT id::text FROM mensajes WHERE familia_id = p_familia\n        UNION SELECT id::text FROM solicitudes_afiliacion WHERE familia_id = p_familia\n        UNION SELECT id::text FROM medios_pago_recurrente WHERE familia_id = p_familia\n        UNION SELECT id::text FROM encuestas WHERE familia_id = p_familia\n        UNION SELECT id::text FROM contratos WHERE familia_id = p_familia\n    );\n    UPDATE auditoria a\n    SET cambios = (\n        SELECT jsonb_object_agg(\n            e.k, CASE WHEN e.k = ANY (v_personales) THEN jsonb_build_array(v_anonimo, v_anonimo)\n                      ELSE e.v END)\n        FROM jsonb_each(a.cambios) AS e(k, v)\n    )\n    WHERE a.entidad_id = ANY (v_ids)\n      AND EXISTS (SELECT 1 FROM jsonb_object_keys(a.cambios) AS k WHERE k = ANY (v_personales));\n    RETURN;\nEND\n$$\n"


def _literal(texto: str) -> str:
    return "'" + texto.replace("'", "''") + "'"


def upgrade() -> None:
    op.create_table(
        "contactos_familia",
        sa.Column("familia_id", sa.Uuid(), nullable=False),
        sa.Column("posicion", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=160), nullable=False),
        sa.Column("telefono", sa.String(length=32), nullable=False),
        sa.Column("relacion", sa.String(length=60), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("dado_de_baja_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "btrim(nombre) <> ''", name=op.f("ck_contactos_familia_nombre_no_vacio")
        ),
        sa.CheckConstraint(
            "email IS NULL OR email ~ '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$'",
            name=op.f("ck_contactos_familia_email_formato"),
        ),
        sa.CheckConstraint(
            "telefono ~ '^\\+[1-9][0-9]{7,14}$'", name=op.f("ck_contactos_familia_telefono_formato")
        ),
        sa.CheckConstraint(
            "activo = (dado_de_baja_en IS NULL)", name=op.f("ck_contactos_familia_baja_coherente")
        ),
        sa.CheckConstraint(
            "posicion BETWEEN 1 AND 3", name=op.f("ck_contactos_familia_posicion_rango")
        ),
        sa.CheckConstraint(
            "uuid_extract_version(id) = 7", name=op.f("ck_contactos_familia_id_uuidv7")
        ),
        sa.ForeignKeyConstraint(
            ["familia_id"], ["familias.id"], name=op.f("fk_contactos_familia_familia_id_familias")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contactos_familia")),
    )
    op.create_index(
        op.f("ix_contactos_familia_familia_id"), "contactos_familia", ["familia_id"], unique=False
    )
    op.create_index(
        "uq_contactos_familia_posicion_vigente",
        "contactos_familia",
        ["familia_id", "posicion"],
        unique=True,
        postgresql_where=sa.text("activo"),
    )
    op.execute(
        "CREATE TRIGGER tr_contactos_familia_auditoria AFTER INSERT OR UPDATE OR DELETE"
        " ON contactos_familia FOR EACH ROW EXECUTE FUNCTION auditar()"
    )
    op.execute("ALTER TABLE contactos_familia ENABLE ROW LEVEL SECURITY")
    for nombre, tabla, comando, rol, usar, comprobar in POLITICAS:
        sql = f"CREATE POLICY {nombre} ON {tabla} FOR {comando} TO {rol}"
        if usar is not None:
            sql += f" USING ({usar})"
        if comprobar is not None:
            sql += f" WITH CHECK ({comprobar})"
        op.execute(sql)
        texto = f"USING ({usar}) WITH CHECK ({comprobar})"
        op.execute(f"COMMENT ON POLICY {nombre} ON {tabla} IS {_literal(texto)}")
    op.execute(_ANONIMIZAR)


def downgrade() -> None:
    op.execute(_ANONIMIZAR_ANTERIOR)
    op.drop_index(
        "uq_contactos_familia_posicion_vigente",
        table_name="contactos_familia",
        postgresql_where=sa.text("activo"),
    )
    op.drop_index(op.f("ix_contactos_familia_familia_id"), table_name="contactos_familia")
    op.drop_table("contactos_familia")

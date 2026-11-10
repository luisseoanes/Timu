# ruff: noqa: E501  (politicas y funcion congeladas: expresiones SQL largas)
"""documentos: documentos de la familia y de sus mascotas

6.1 pide los documentos asociados a la familia y a cada mascota. El equipo los sube (PDF o
imagen de hasta 10 MB, con categoria y descripcion) y decide cuales ve la familia en su
portal. La clave compuesta (mascota_id, familia_id) hace que la base rechace la mascota de
otra familia; por eso mascotas gana un indice unico en (id, familia_id).

La tabla lleva su auditoria y RLS con las politicas de app/core/permisos_db.py (escritas aqui,
congeladas). La politica de lectura de archivos se amplia para que la familia vea los ficheros
de los documentos visibles: estan la expresion anterior y la nueva. anonimizar_familia()
purga los documentos subidos salvo los examenes externos (clinicos), vacia sus
descripciones y quita el nombre original de cada fichero purgado: las dos versiones de
la funcion estan aqui.

Revision ID: 0030
Revises: 0029
Create Date: 2026-11-09 20:05:02.438637
"""

import sqlalchemy as sa

from alembic import op

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None

# (nombre, tabla, comando, rol, USING, WITH CHECK), de politicas(['documentos_familia'])
POLITICAS = [
    (
        "p_documentos_familia_select",
        "documentos_familia",
        "SELECT",
        "timu_app",
        "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia() AND visible_familia AND activo))",
        None,
    ),
    (
        "p_documentos_familia_insert",
        "documentos_familia",
        "INSERT",
        "timu_app",
        None,
        "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
    ),
    (
        "p_documentos_familia_update",
        "documentos_familia",
        "UPDATE",
        "timu_app",
        "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
        "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
    ),
    (
        "p_documentos_familia_delete",
        "documentos_familia",
        "DELETE",
        "timu_app",
        "app_rol() IN ('sistema')",
        None,
    ),
]

# (politica, tabla, (USING, WITH CHECK) anterior, (USING, WITH CHECK) nuevo)
CAMBIOS = [
    (
        "p_archivos_insert",
        "archivos",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (subido_por_id = app_usuario() OR id IN (SELECT foto_archivo_id FROM mascotas WHERE familia_id = app_familia()) OR id IN (SELECT documento_archivo_id FROM contratos WHERE familia_id = app_familia()) OR id IN (SELECT archivo_id FROM adjuntos_clinicos WHERE historia_id IN (SELECT id FROM historias_clinicas WHERE familia_id = app_familia() AND estado <> 'borrador')) OR id IN (SELECT archivo_id FROM carnets_emitidos WHERE mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia()))))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (subido_por_id = app_usuario() OR id IN (SELECT foto_archivo_id FROM mascotas WHERE familia_id = app_familia()) OR id IN (SELECT documento_archivo_id FROM contratos WHERE familia_id = app_familia()) OR id IN (SELECT archivo_id FROM adjuntos_clinicos WHERE historia_id IN (SELECT id FROM historias_clinicas WHERE familia_id = app_familia() AND estado <> 'borrador')) OR id IN (SELECT archivo_id FROM carnets_emitidos WHERE mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia())) OR id IN (SELECT archivo_id FROM documentos_familia WHERE familia_id = app_familia() AND visible_familia AND activo)))",
        ),
    ),
    (
        "p_archivos_select",
        "archivos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (subido_por_id = app_usuario() OR id IN (SELECT foto_archivo_id FROM mascotas WHERE familia_id = app_familia()) OR id IN (SELECT documento_archivo_id FROM contratos WHERE familia_id = app_familia()) OR id IN (SELECT archivo_id FROM adjuntos_clinicos WHERE historia_id IN (SELECT id FROM historias_clinicas WHERE familia_id = app_familia() AND estado <> 'borrador')) OR id IN (SELECT archivo_id FROM carnets_emitidos WHERE mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia()))))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (subido_por_id = app_usuario() OR id IN (SELECT foto_archivo_id FROM mascotas WHERE familia_id = app_familia()) OR id IN (SELECT documento_archivo_id FROM contratos WHERE familia_id = app_familia()) OR id IN (SELECT archivo_id FROM adjuntos_clinicos WHERE historia_id IN (SELECT id FROM historias_clinicas WHERE familia_id = app_familia() AND estado <> 'borrador')) OR id IN (SELECT archivo_id FROM carnets_emitidos WHERE mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia())) OR id IN (SELECT archivo_id FROM documentos_familia WHERE familia_id = app_familia() AND visible_familia AND activo)))",
            None,
        ),
    ),
]

_ANONIMIZAR_ANTERIOR = "\nCREATE OR REPLACE FUNCTION anonimizar_familia(p_familia uuid) RETURNS SETOF text\nLANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$\nDECLARE\n    f familias%ROWTYPE;\n    v_ids text[];\n    v_anonimo constant text := '[anonimizado]';\n    -- Prefijo internacional 999: no esta asignado a ningun pais.\n    v_telefono constant text := '+99900000000';\n    v_quitar constant text[] :=\n        ARRAY['ip', 'user_agent', 'nombre', 'documento', 'email', 'telefono'];\n    v_personales constant text[] := ARRAY[\n        'titular_nombre', 'documento', 'email', 'telefono', 'barrio', 'direccion', 'relacion',\n        'complemento', 'latitud', 'longitud',\n        'notas', 'motivo_baja', 'nombre', 'destino', 'contenido', 'asunto', 'variables',\n        'email_titular', 'ultimos4', 'comentario', 'aceptacion', 'evidencia_aceptacion', 'datos'\n    ];\nBEGIN\n    IF current_setting('app.rol', true) IS DISTINCT FROM 'admin' THEN\n        RAISE EXCEPTION 'Solo un administrador anonimiza una familia'\n            USING ERRCODE = 'insufficient_privilege';\n    END IF;\n    SELECT * INTO f FROM familias WHERE id = p_familia FOR UPDATE;\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'Familia % no encontrada', p_familia USING ERRCODE = 'no_data_found';\n    END IF;\n    IF f.anonimizada_en IS NOT NULL THEN\n        RAISE EXCEPTION 'La familia ya esta anonimizada' USING ERRCODE = 'check_violation';\n    END IF;\n    IF EXISTS (\n        SELECT 1 FROM contratos\n        WHERE familia_id = p_familia AND estado IN ('activa', 'en_mora', 'congelada')\n    ) THEN\n        RAISE EXCEPTION 'La familia tiene un contrato vigente' USING ERRCODE = 'check_violation';\n    END IF;\n\n    -- Ficheros con datos personales: fotos de las mascotas y PDF de contratos y carnets.\n    RETURN QUERY\n        WITH purgados AS (\n            UPDATE archivos a SET purgado_en = now()\n            WHERE a.purgado_en IS NULL AND a.id IN (\n                SELECT foto_archivo_id FROM mascotas WHERE familia_id = p_familia\n                UNION SELECT documento_archivo_id FROM contratos WHERE familia_id = p_familia\n                UNION SELECT c.archivo_id FROM carnets_emitidos c\n                      JOIN mascotas m ON m.id = c.mascota_id WHERE m.familia_id = p_familia\n            )\n            RETURNING a.clave\n        )\n        SELECT clave::text FROM purgados;\n\n    UPDATE mascotas SET nombre = 'Mascota', foto_archivo_id = NULL WHERE familia_id = p_familia;\n    IF f.usuario_portal_id IS NOT NULL THEN\n        UPDATE usuarios\n        SET nombre = 'Anonimizado', email = 'anonimizado-' || id || '@invalid.local',\n            telefono = NULL, activo = false\n        WHERE id = f.usuario_portal_id;\n        UPDATE sesiones SET revocada_en = coalesce(revocada_en, now())\n        WHERE usuario_id = f.usuario_portal_id;\n        UPDATE tokens_uso_unico SET expira_en = least(expira_en, now())\n        WHERE usuario_id = f.usuario_portal_id;\n    END IF;\n    DELETE FROM conversaciones_comerciales\n    WHERE telefono = f.telefono\n       OR interesado_id IN (SELECT id FROM interesados WHERE familia_id = p_familia);\n    DELETE FROM conversaciones_whatsapp WHERE familia_id = p_familia OR telefono = f.telefono;\n    UPDATE interesados SET nombre = NULL, telefono = NULL, email = NULL, datos = '{}'\n    WHERE familia_id = p_familia;\n    UPDATE mensajes SET destino = NULL, contenido = NULL, asunto = NULL, variables = '[]'\n    WHERE familia_id = p_familia;\n    UPDATE solicitudes_afiliacion SET aceptacion = aceptacion - v_quitar\n    WHERE familia_id = p_familia;\n    UPDATE contratos SET evidencia_aceptacion = evidencia_aceptacion - v_quitar\n    WHERE familia_id = p_familia;\n    UPDATE medios_pago_recurrente\n    SET email_titular = 'anonimizado@invalid.local', ultimos4 = NULL, activo = false\n    WHERE familia_id = p_familia;\n    UPDATE encuestas SET comentario = NULL WHERE familia_id = p_familia;\n    UPDATE destinatarios_campana SET telefono = v_telefono WHERE familia_id = p_familia;\n    UPDATE contactos_familia\n    SET nombre = 'Anonimizado', telefono = v_telefono, email = NULL, relacion = NULL\n    WHERE familia_id = p_familia;\n    UPDATE familias\n    SET titular_nombre = 'Anonimizado',\n        documento = 'ANON' || upper(substr(replace(id::text, '-', ''), 1, 28)),\n        email = NULL, telefono = v_telefono, barrio = 'Anonimizado', direccion = NULL,\n        complemento = NULL, latitud = NULL,\n        longitud = NULL, geo_precision = NULL, notas = NULL, estado = 'cancelada',\n        dada_de_baja_en = coalesce(dada_de_baja_en, now()),\n        motivo_baja = 'Anonimizada (habeas data)', anonimizada_en = now()\n    WHERE id = p_familia;\n\n    -- El rastro en la bitacora, incluido el que acaba de dejar esta misma funcion.\n    v_ids := ARRAY(\n        SELECT p_familia::text\n        UNION SELECT f.usuario_portal_id::text WHERE f.usuario_portal_id IS NOT NULL\n        UNION SELECT id::text FROM mascotas WHERE familia_id = p_familia\n        UNION SELECT id::text FROM contactos_familia WHERE familia_id = p_familia\n        UNION SELECT id::text FROM interesados WHERE familia_id = p_familia\n        UNION SELECT id::text FROM mensajes WHERE familia_id = p_familia\n        UNION SELECT id::text FROM solicitudes_afiliacion WHERE familia_id = p_familia\n        UNION SELECT id::text FROM medios_pago_recurrente WHERE familia_id = p_familia\n        UNION SELECT id::text FROM encuestas WHERE familia_id = p_familia\n        UNION SELECT id::text FROM contratos WHERE familia_id = p_familia\n    );\n    UPDATE auditoria a\n    SET cambios = (\n        SELECT jsonb_object_agg(\n            e.k, CASE WHEN e.k = ANY (v_personales) THEN jsonb_build_array(v_anonimo, v_anonimo)\n                      ELSE e.v END)\n        FROM jsonb_each(a.cambios) AS e(k, v)\n    )\n    WHERE a.entidad_id = ANY (v_ids)\n      AND EXISTS (SELECT 1 FROM jsonb_object_keys(a.cambios) AS k WHERE k = ANY (v_personales));\n    RETURN;\nEND\n$$\n"

_ANONIMIZAR = "\nCREATE OR REPLACE FUNCTION anonimizar_familia(p_familia uuid) RETURNS SETOF text\nLANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$\nDECLARE\n    f familias%ROWTYPE;\n    v_ids text[];\n    v_anonimo constant text := '[anonimizado]';\n    -- Prefijo internacional 999: no esta asignado a ningun pais.\n    v_telefono constant text := '+99900000000';\n    v_quitar constant text[] :=\n        ARRAY['ip', 'user_agent', 'nombre', 'documento', 'email', 'telefono'];\n    v_personales constant text[] := ARRAY[\n        'titular_nombre', 'documento', 'email', 'telefono', 'barrio', 'direccion', 'relacion',\n        'descripcion',\n        'complemento', 'latitud', 'longitud',\n        'notas', 'motivo_baja', 'nombre', 'destino', 'contenido', 'asunto', 'variables',\n        'email_titular', 'ultimos4', 'comentario', 'aceptacion', 'evidencia_aceptacion', 'datos'\n    ];\nBEGIN\n    IF current_setting('app.rol', true) IS DISTINCT FROM 'admin' THEN\n        RAISE EXCEPTION 'Solo un administrador anonimiza una familia'\n            USING ERRCODE = 'insufficient_privilege';\n    END IF;\n    SELECT * INTO f FROM familias WHERE id = p_familia FOR UPDATE;\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'Familia % no encontrada', p_familia USING ERRCODE = 'no_data_found';\n    END IF;\n    IF f.anonimizada_en IS NOT NULL THEN\n        RAISE EXCEPTION 'La familia ya esta anonimizada' USING ERRCODE = 'check_violation';\n    END IF;\n    IF EXISTS (\n        SELECT 1 FROM contratos\n        WHERE familia_id = p_familia AND estado IN ('activa', 'en_mora', 'congelada')\n    ) THEN\n        RAISE EXCEPTION 'La familia tiene un contrato vigente' USING ERRCODE = 'check_violation';\n    END IF;\n\n    -- Ficheros con datos personales: fotos de las mascotas, PDF de contratos y carnets y\n    -- los documentos que subio el equipo, salvo los examenes externos, que son clinicos.\n    RETURN QUERY\n        WITH purgados AS (\n            UPDATE archivos a SET purgado_en = now(), nombre_original = 'anonimizado'\n            WHERE a.purgado_en IS NULL AND a.id IN (\n                SELECT foto_archivo_id FROM mascotas WHERE familia_id = p_familia\n                UNION SELECT documento_archivo_id FROM contratos WHERE familia_id = p_familia\n                UNION SELECT c.archivo_id FROM carnets_emitidos c\n                      JOIN mascotas m ON m.id = c.mascota_id WHERE m.familia_id = p_familia\n                UNION SELECT archivo_id FROM documentos_familia\n                      WHERE familia_id = p_familia AND categoria <> 'examen_externo'\n            )\n            RETURNING a.clave\n        )\n        SELECT clave::text FROM purgados;\n\n    UPDATE mascotas SET nombre = 'Mascota', foto_archivo_id = NULL WHERE familia_id = p_familia;\n    IF f.usuario_portal_id IS NOT NULL THEN\n        UPDATE usuarios\n        SET nombre = 'Anonimizado', email = 'anonimizado-' || id || '@invalid.local',\n            telefono = NULL, activo = false\n        WHERE id = f.usuario_portal_id;\n        UPDATE sesiones SET revocada_en = coalesce(revocada_en, now())\n        WHERE usuario_id = f.usuario_portal_id;\n        UPDATE tokens_uso_unico SET expira_en = least(expira_en, now())\n        WHERE usuario_id = f.usuario_portal_id;\n    END IF;\n    DELETE FROM conversaciones_comerciales\n    WHERE telefono = f.telefono\n       OR interesado_id IN (SELECT id FROM interesados WHERE familia_id = p_familia);\n    DELETE FROM conversaciones_whatsapp WHERE familia_id = p_familia OR telefono = f.telefono;\n    UPDATE interesados SET nombre = NULL, telefono = NULL, email = NULL, datos = '{}'\n    WHERE familia_id = p_familia;\n    UPDATE mensajes SET destino = NULL, contenido = NULL, asunto = NULL, variables = '[]'\n    WHERE familia_id = p_familia;\n    UPDATE solicitudes_afiliacion SET aceptacion = aceptacion - v_quitar\n    WHERE familia_id = p_familia;\n    UPDATE contratos SET evidencia_aceptacion = evidencia_aceptacion - v_quitar\n    WHERE familia_id = p_familia;\n    UPDATE medios_pago_recurrente\n    SET email_titular = 'anonimizado@invalid.local', ultimos4 = NULL, activo = false\n    WHERE familia_id = p_familia;\n    UPDATE encuestas SET comentario = NULL WHERE familia_id = p_familia;\n    UPDATE destinatarios_campana SET telefono = v_telefono WHERE familia_id = p_familia;\n    UPDATE documentos_familia SET descripcion = NULL WHERE familia_id = p_familia;\n    -- Tambien los que se conservan: el nombre original puede llevar datos personales.\n    UPDATE archivos SET nombre_original = 'anonimizado'\n    WHERE id IN (SELECT archivo_id FROM documentos_familia WHERE familia_id = p_familia);\n    UPDATE contactos_familia\n    SET nombre = 'Anonimizado', telefono = v_telefono, email = NULL, relacion = NULL\n    WHERE familia_id = p_familia;\n    UPDATE familias\n    SET titular_nombre = 'Anonimizado',\n        documento = 'ANON' || upper(substr(replace(id::text, '-', ''), 1, 28)),\n        email = NULL, telefono = v_telefono, barrio = 'Anonimizado', direccion = NULL,\n        complemento = NULL, latitud = NULL,\n        longitud = NULL, geo_precision = NULL, notas = NULL, estado = 'cancelada',\n        dada_de_baja_en = coalesce(dada_de_baja_en, now()),\n        motivo_baja = 'Anonimizada (habeas data)', anonimizada_en = now()\n    WHERE id = p_familia;\n\n    -- El rastro en la bitacora, incluido el que acaba de dejar esta misma funcion.\n    v_ids := ARRAY(\n        SELECT p_familia::text\n        UNION SELECT f.usuario_portal_id::text WHERE f.usuario_portal_id IS NOT NULL\n        UNION SELECT id::text FROM mascotas WHERE familia_id = p_familia\n        UNION SELECT id::text FROM contactos_familia WHERE familia_id = p_familia\n        UNION SELECT id::text FROM documentos_familia WHERE familia_id = p_familia\n        UNION SELECT id::text FROM interesados WHERE familia_id = p_familia\n        UNION SELECT id::text FROM mensajes WHERE familia_id = p_familia\n        UNION SELECT id::text FROM solicitudes_afiliacion WHERE familia_id = p_familia\n        UNION SELECT id::text FROM medios_pago_recurrente WHERE familia_id = p_familia\n        UNION SELECT id::text FROM encuestas WHERE familia_id = p_familia\n        UNION SELECT id::text FROM contratos WHERE familia_id = p_familia\n    );\n    UPDATE auditoria a\n    SET cambios = (\n        SELECT jsonb_object_agg(\n            e.k, CASE WHEN e.k = ANY (v_personales) THEN jsonb_build_array(v_anonimo, v_anonimo)\n                      ELSE e.v END)\n        FROM jsonb_each(a.cambios) AS e(k, v)\n    )\n    WHERE a.entidad_id = ANY (v_ids)\n      AND EXISTS (SELECT 1 FROM jsonb_object_keys(a.cambios) AS k WHERE k = ANY (v_personales));\n    RETURN;\nEND\n$$\n"

_PROPOSITOS_ANTERIORES = ("foto_mascota", "adjunto_clinico", "contrato", "formula", "carnet")


def _literal(texto: str) -> str:
    return "'" + texto.replace("'", "''") + "'"


def _alterar(nombre: str, tabla: str, usar: str | None, comprobar: str | None) -> None:
    sql = f"ALTER POLICY {nombre} ON {tabla}"
    if usar is not None:
        sql += f" USING ({usar})"
    if comprobar is not None:
        sql += f" WITH CHECK ({comprobar})"
    op.execute(sql)
    texto = f"USING ({usar}) WITH CHECK ({comprobar})"
    op.execute(f"COMMENT ON POLICY {nombre} ON {tabla} IS {_literal(texto)}")


def upgrade() -> None:
    # El valor nuevo no se usa en esta migracion: ADD VALUE admite la transaccion.
    op.execute("ALTER TYPE proposito_archivo ADD VALUE 'documento_familia'")
    # Destino de la clave compuesta: antes que la tabla que la usa.
    op.create_index("uq_mascotas_id_familia", "mascotas", ["id", "familia_id"], unique=True)
    op.create_table(
        "documentos_familia",
        sa.Column("familia_id", sa.Uuid(), nullable=False),
        sa.Column("mascota_id", sa.Uuid(), nullable=True),
        sa.Column("archivo_id", sa.Uuid(), nullable=False),
        sa.Column(
            "categoria",
            sa.Enum("identificacion", "examen_externo", "otro", name="categoria_documento"),
            nullable=False,
        ),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.Column("visible_familia", sa.Boolean(), nullable=False),
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
            "descripcion IS NULL OR btrim(descripcion) <> ''",
            name=op.f("ck_documentos_familia_descripcion_no_vacia"),
        ),
        sa.CheckConstraint(
            "activo = (dado_de_baja_en IS NULL)", name=op.f("ck_documentos_familia_baja_coherente")
        ),
        sa.CheckConstraint(
            "uuid_extract_version(id) = 7", name=op.f("ck_documentos_familia_id_uuidv7")
        ),
        sa.ForeignKeyConstraint(
            ["archivo_id"], ["archivos.id"], name=op.f("fk_documentos_familia_archivo_id_archivos")
        ),
        sa.ForeignKeyConstraint(
            ["familia_id"], ["familias.id"], name=op.f("fk_documentos_familia_familia_id_familias")
        ),
        sa.ForeignKeyConstraint(
            ["mascota_id", "familia_id"],
            ["mascotas.id", "mascotas.familia_id"],
            name="fk_documentos_familia_mascota_de_la_familia",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documentos_familia")),
        sa.UniqueConstraint("archivo_id", name=op.f("uq_documentos_familia_archivo_id")),
    )
    op.create_index(
        op.f("ix_documentos_familia_familia_id"), "documentos_familia", ["familia_id"], unique=False
    )
    op.create_index(
        op.f("ix_documentos_familia_mascota_id"), "documentos_familia", ["mascota_id"], unique=False
    )
    op.execute(
        "CREATE TRIGGER tr_documentos_familia_auditoria AFTER INSERT OR UPDATE OR DELETE"
        " ON documentos_familia FOR EACH ROW EXECUTE FUNCTION auditar()"
    )
    op.execute("ALTER TABLE documentos_familia ENABLE ROW LEVEL SECURITY")
    for nombre, tabla, comando, rol, usar, comprobar in POLITICAS:
        sql = f"CREATE POLICY {nombre} ON {tabla} FOR {comando} TO {rol}"
        if usar is not None:
            sql += f" USING ({usar})"
        if comprobar is not None:
            sql += f" WITH CHECK ({comprobar})"
        op.execute(sql)
        texto = f"USING ({usar}) WITH CHECK ({comprobar})"
        op.execute(f"COMMENT ON POLICY {nombre} ON {tabla} IS {_literal(texto)}")
    for nombre, tabla, _, (usar, comprobar) in CAMBIOS:
        _alterar(nombre, tabla, usar, comprobar)
    op.execute(_ANONIMIZAR)


def downgrade() -> None:
    op.execute(_ANONIMIZAR_ANTERIOR)
    for nombre, tabla, (usar, comprobar), _ in CAMBIOS:
        _alterar(nombre, tabla, usar, comprobar)
    op.drop_index(op.f("ix_documentos_familia_mascota_id"), table_name="documentos_familia")
    op.drop_index(op.f("ix_documentos_familia_familia_id"), table_name="documentos_familia")
    op.drop_table("documentos_familia")
    op.execute("DROP TYPE categoria_documento")
    op.drop_index("uq_mascotas_id_familia", table_name="mascotas")
    # PostgreSQL no quita un valor de un enum: se recrea el tipo sin el. Si queda algun
    # archivo con ese proposito, la conversion falla y el downgrade se detiene sin perderlo.
    op.execute("ALTER TYPE proposito_archivo RENAME TO proposito_archivo_anterior")
    valores = ", ".join(f"'{v}'" for v in _PROPOSITOS_ANTERIORES)
    op.execute(f"CREATE TYPE proposito_archivo AS ENUM ({valores})")
    op.execute(
        "ALTER TABLE archivos ALTER COLUMN proposito TYPE proposito_archivo"
        " USING proposito::text::proposito_archivo"
    )
    op.execute("DROP TYPE proposito_archivo_anterior")

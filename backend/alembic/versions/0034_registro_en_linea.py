# ruff: noqa: E501  (politicas congeladas de app/core/permisos_db.py: expresiones SQL largas)
"""afiliaciones: registro en linea, con el pago antes que la familia

6.1. La familia elige ciudad, peludos y plan de cada uno, paga y despues completa sus datos.
La solicitud de afiliacion puede existir sin familia: guarda la ciudad, el contacto del
titular (para el comprobante y el enlace del formulario) y los tokens del formulario, solo
como SHA-256. Un CHECK exige familia o contacto. El estado `pagada` marca el pago recibido
sin formulario, con sus aristas en el grafo de la base. Los peludos de la solicitud y el pago
tambien pueden ir sin familia; el pago solo si es de una afiliacion (referencia AFI-).

El perfil `publico` ve y escribe esas filas solo con las llaves que fija quien las crea
(`registro`, `referencia_pago`) o quien abre el formulario con su token (`token_registro`):
estan las politicas anteriores y las nuevas. anonimizar_familia() borra el contacto de sus
solicitudes: las dos versiones de la funcion estan aqui.

Revision ID: 0034
Revises: 0033
Create Date: 2026-11-10 14:00:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0034"
down_revision = "0033"
branch_labels = None
depends_on = None

# (politica, tabla, (USING, WITH CHECK) anterior, (USING, WITH CHECK) nuevo)
CAMBIOS = [
    (
        "p_pagos_select",
        "pagos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR referencia_externa = app_llave('referencia_pago')))",
            None,
        ),
    ),
    (
        "p_pagos_insert",
        "pagos",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR referencia_externa = app_llave('referencia_pago')))",
        ),
    ),
    (
        "p_pagos_update",
        "pagos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR referencia_externa = app_llave('referencia_pago')))",
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR referencia_externa = app_llave('referencia_pago')))",
        ),
    ),
    (
        "p_peludos_solicitud_select",
        "peludos_solicitud",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR solicitud_id = app_llave('registro')::uuid))",
            None,
        ),
    ),
    (
        "p_peludos_solicitud_insert",
        "peludos_solicitud",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR solicitud_id = app_llave('registro')::uuid))",
        ),
    ),
    (
        "p_peludos_solicitud_update",
        "peludos_solicitud",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR solicitud_id = app_llave('registro')::uuid))",
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR solicitud_id = app_llave('registro')::uuid))",
        ),
    ),
    (
        "p_solicitudes_afiliacion_select",
        "solicitudes_afiliacion",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR id = app_llave('registro')::uuid OR token_hash = app_llave('token_registro') OR token_enlace_hash = app_llave('token_registro')))",
            None,
        ),
    ),
    (
        "p_solicitudes_afiliacion_insert",
        "solicitudes_afiliacion",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR id = app_llave('registro')::uuid OR token_hash = app_llave('token_registro') OR token_enlace_hash = app_llave('token_registro')))",
        ),
    ),
    (
        "p_solicitudes_afiliacion_update",
        "solicitudes_afiliacion",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR id = app_llave('registro')::uuid OR token_hash = app_llave('token_registro') OR token_enlace_hash = app_llave('token_registro')))",
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR id = app_llave('registro')::uuid OR token_hash = app_llave('token_registro') OR token_enlace_hash = app_llave('token_registro')))",
        ),
    ),
]

ARISTAS = [
    ("solicitudes_afiliacion", "estado", "pendiente_pago", "pagada"),
    ("solicitudes_afiliacion", "estado", "pagada", "completada"),
    ("solicitudes_afiliacion", "estado", "pagada", "error"),
]

CHECKS = {
    "solicitudes_afiliacion": {
        "familia_o_contacto": (
            "familia_id IS NOT NULL"
            " OR (contacto_nombre IS NOT NULL AND contacto_telefono IS NOT NULL)"
        ),
        # Como texto: el valor nuevo del enum no se puede usar en la transaccion que lo crea.
        "pagada_con_fecha": "estado::text <> 'pagada' OR pagada_en IS NOT NULL",
        "contacto_telefono_formato": (
            "contacto_telefono IS NULL OR contacto_telefono ~ '^\\+[1-9][0-9]{7,14}$'"
        ),
    },
    "pagos": {
        "familia_salvo_registro": "familia_id IS NOT NULL OR referencia_externa LIKE 'AFI-%'",
    },
}

_ANONIMIZAR_ANTERIOR = "\nCREATE OR REPLACE FUNCTION anonimizar_familia(p_familia uuid) RETURNS SETOF text\nLANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$\nDECLARE\n    f familias%ROWTYPE;\n    v_ids text[];\n    v_anonimo constant text := '[anonimizado]';\n    -- Prefijo internacional 999: no esta asignado a ningun pais.\n    v_telefono constant text := '+99900000000';\n    v_quitar constant text[] :=\n        ARRAY['ip', 'user_agent', 'nombre', 'documento', 'email', 'telefono'];\n    v_personales constant text[] := ARRAY[\n        'titular_nombre', 'documento', 'email', 'telefono', 'barrio', 'direccion', 'relacion',\n        'descripcion',\n        'complemento', 'latitud', 'longitud',\n        'notas', 'motivo_baja', 'nombre', 'destino', 'contenido', 'asunto', 'variables',\n        'email_titular', 'ultimos4', 'comentario', 'aceptacion', 'evidencia_aceptacion', 'datos'\n    ];\nBEGIN\n    IF current_setting('app.rol', true) IS DISTINCT FROM 'admin' THEN\n        RAISE EXCEPTION 'Solo un administrador anonimiza una familia'\n            USING ERRCODE = 'insufficient_privilege';\n    END IF;\n    SELECT * INTO f FROM familias WHERE id = p_familia FOR UPDATE;\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'Familia % no encontrada', p_familia USING ERRCODE = 'no_data_found';\n    END IF;\n    IF f.anonimizada_en IS NOT NULL THEN\n        RAISE EXCEPTION 'La familia ya esta anonimizada' USING ERRCODE = 'check_violation';\n    END IF;\n    IF EXISTS (\n        SELECT 1 FROM contratos\n        WHERE familia_id = p_familia AND estado IN ('activa', 'en_mora', 'congelada')\n    ) THEN\n        RAISE EXCEPTION 'La familia tiene un contrato vigente' USING ERRCODE = 'check_violation';\n    END IF;\n\n    -- Ficheros con datos personales: fotos de las mascotas, PDF de contratos y carnets y\n    -- los documentos que subio el equipo, salvo los examenes externos, que son clinicos.\n    RETURN QUERY\n        WITH purgados AS (\n            UPDATE archivos a SET purgado_en = now(), nombre_original = 'anonimizado'\n            WHERE a.purgado_en IS NULL AND a.id IN (\n                SELECT foto_archivo_id FROM mascotas WHERE familia_id = p_familia\n                UNION SELECT documento_archivo_id FROM contratos WHERE familia_id = p_familia\n                UNION SELECT c.archivo_id FROM carnets_emitidos c\n                      JOIN mascotas m ON m.id = c.mascota_id WHERE m.familia_id = p_familia\n                UNION SELECT archivo_id FROM documentos_familia\n                      WHERE familia_id = p_familia AND categoria <> 'examen_externo'\n            )\n            RETURNING a.clave\n        )\n        SELECT clave::text FROM purgados;\n\n    UPDATE mascotas SET nombre = 'Mascota', foto_archivo_id = NULL WHERE familia_id = p_familia;\n    UPDATE peludos_solicitud SET nombre = 'Mascota' WHERE familia_id = p_familia;\n    IF f.usuario_portal_id IS NOT NULL THEN\n        UPDATE usuarios\n        SET nombre = 'Anonimizado', email = 'anonimizado-' || id || '@invalid.local',\n            telefono = NULL, activo = false\n        WHERE id = f.usuario_portal_id;\n        UPDATE sesiones SET revocada_en = coalesce(revocada_en, now())\n        WHERE usuario_id = f.usuario_portal_id;\n        UPDATE tokens_uso_unico SET expira_en = least(expira_en, now())\n        WHERE usuario_id = f.usuario_portal_id;\n    END IF;\n    DELETE FROM conversaciones_comerciales\n    WHERE telefono = f.telefono\n       OR interesado_id IN (SELECT id FROM interesados WHERE familia_id = p_familia);\n    DELETE FROM conversaciones_whatsapp WHERE familia_id = p_familia OR telefono = f.telefono;\n    UPDATE interesados SET nombre = NULL, telefono = NULL, email = NULL, datos = '{}'\n    WHERE familia_id = p_familia;\n    UPDATE mensajes SET destino = NULL, contenido = NULL, asunto = NULL, variables = '[]'\n    WHERE familia_id = p_familia;\n    UPDATE solicitudes_afiliacion SET aceptacion = aceptacion - v_quitar\n    WHERE familia_id = p_familia;\n    UPDATE contratos SET evidencia_aceptacion = evidencia_aceptacion - v_quitar\n    WHERE familia_id = p_familia;\n    UPDATE medios_pago_recurrente\n    SET email_titular = 'anonimizado@invalid.local', ultimos4 = NULL, activo = false\n    WHERE familia_id = p_familia;\n    UPDATE encuestas SET comentario = NULL WHERE familia_id = p_familia;\n    UPDATE destinatarios_campana SET telefono = v_telefono WHERE familia_id = p_familia;\n    UPDATE documentos_familia SET descripcion = NULL WHERE familia_id = p_familia;\n    -- Tambien los que se conservan: el nombre original puede llevar datos personales.\n    UPDATE archivos SET nombre_original = 'anonimizado'\n    WHERE id IN (SELECT archivo_id FROM documentos_familia WHERE familia_id = p_familia);\n    UPDATE contactos_familia\n    SET nombre = 'Anonimizado', telefono = v_telefono, email = NULL, relacion = NULL\n    WHERE familia_id = p_familia;\n    UPDATE familias\n    SET titular_nombre = 'Anonimizado',\n        documento = 'ANON' || upper(substr(replace(id::text, '-', ''), 1, 28)),\n        email = NULL, telefono = v_telefono, barrio = 'Anonimizado', direccion = NULL,\n        complemento = NULL, latitud = NULL,\n        longitud = NULL, geo_precision = NULL, notas = NULL, estado = 'cancelada',\n        dada_de_baja_en = coalesce(dada_de_baja_en, now()),\n        motivo_baja = 'Anonimizada (habeas data)', anonimizada_en = now()\n    WHERE id = p_familia;\n\n    -- El rastro en la bitacora, incluido el que acaba de dejar esta misma funcion.\n    v_ids := ARRAY(\n        SELECT p_familia::text\n        UNION SELECT f.usuario_portal_id::text WHERE f.usuario_portal_id IS NOT NULL\n        UNION SELECT id::text FROM mascotas WHERE familia_id = p_familia\n        UNION SELECT id::text FROM contactos_familia WHERE familia_id = p_familia\n        UNION SELECT id::text FROM documentos_familia WHERE familia_id = p_familia\n        UNION SELECT id::text FROM peludos_solicitud WHERE familia_id = p_familia\n        UNION SELECT id::text FROM interesados WHERE familia_id = p_familia\n        UNION SELECT id::text FROM mensajes WHERE familia_id = p_familia\n        UNION SELECT id::text FROM solicitudes_afiliacion WHERE familia_id = p_familia\n        UNION SELECT id::text FROM medios_pago_recurrente WHERE familia_id = p_familia\n        UNION SELECT id::text FROM encuestas WHERE familia_id = p_familia\n        UNION SELECT id::text FROM contratos WHERE familia_id = p_familia\n    );\n    UPDATE auditoria a\n    SET cambios = (\n        SELECT jsonb_object_agg(\n            e.k, CASE WHEN e.k = ANY (v_personales) THEN jsonb_build_array(v_anonimo, v_anonimo)\n                      ELSE e.v END)\n        FROM jsonb_each(a.cambios) AS e(k, v)\n    )\n    WHERE a.entidad_id = ANY (v_ids)\n      AND EXISTS (SELECT 1 FROM jsonb_object_keys(a.cambios) AS k WHERE k = ANY (v_personales));\n    RETURN;\nEND\n$$\n"

_ANONIMIZAR = "\nCREATE OR REPLACE FUNCTION anonimizar_familia(p_familia uuid) RETURNS SETOF text\nLANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$\nDECLARE\n    f familias%ROWTYPE;\n    v_ids text[];\n    v_anonimo constant text := '[anonimizado]';\n    -- Prefijo internacional 999: no esta asignado a ningun pais.\n    v_telefono constant text := '+99900000000';\n    v_quitar constant text[] :=\n        ARRAY['ip', 'user_agent', 'nombre', 'documento', 'email', 'telefono'];\n    v_personales constant text[] := ARRAY[\n        'titular_nombre', 'documento', 'email', 'telefono', 'barrio', 'direccion', 'relacion',\n        'descripcion',\n        'complemento', 'latitud', 'longitud',\n        'notas', 'motivo_baja', 'nombre', 'destino', 'contenido', 'asunto', 'variables',\n        'email_titular', 'ultimos4', 'comentario', 'aceptacion', 'evidencia_aceptacion', 'datos',\n        'contacto_nombre', 'contacto_telefono', 'contacto_email'\n    ];\nBEGIN\n    IF current_setting('app.rol', true) IS DISTINCT FROM 'admin' THEN\n        RAISE EXCEPTION 'Solo un administrador anonimiza una familia'\n            USING ERRCODE = 'insufficient_privilege';\n    END IF;\n    SELECT * INTO f FROM familias WHERE id = p_familia FOR UPDATE;\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'Familia % no encontrada', p_familia USING ERRCODE = 'no_data_found';\n    END IF;\n    IF f.anonimizada_en IS NOT NULL THEN\n        RAISE EXCEPTION 'La familia ya esta anonimizada' USING ERRCODE = 'check_violation';\n    END IF;\n    IF EXISTS (\n        SELECT 1 FROM contratos\n        WHERE familia_id = p_familia AND estado IN ('activa', 'en_mora', 'congelada')\n    ) THEN\n        RAISE EXCEPTION 'La familia tiene un contrato vigente' USING ERRCODE = 'check_violation';\n    END IF;\n\n    -- Ficheros con datos personales: fotos de las mascotas, PDF de contratos y carnets y\n    -- los documentos que subio el equipo, salvo los examenes externos, que son clinicos.\n    RETURN QUERY\n        WITH purgados AS (\n            UPDATE archivos a SET purgado_en = now(), nombre_original = 'anonimizado'\n            WHERE a.purgado_en IS NULL AND a.id IN (\n                SELECT foto_archivo_id FROM mascotas WHERE familia_id = p_familia\n                UNION SELECT documento_archivo_id FROM contratos WHERE familia_id = p_familia\n                UNION SELECT c.archivo_id FROM carnets_emitidos c\n                      JOIN mascotas m ON m.id = c.mascota_id WHERE m.familia_id = p_familia\n                UNION SELECT archivo_id FROM documentos_familia\n                      WHERE familia_id = p_familia AND categoria <> 'examen_externo'\n            )\n            RETURNING a.clave\n        )\n        SELECT clave::text FROM purgados;\n\n    UPDATE mascotas SET nombre = 'Mascota', foto_archivo_id = NULL WHERE familia_id = p_familia;\n    UPDATE peludos_solicitud SET nombre = 'Mascota' WHERE familia_id = p_familia;\n    IF f.usuario_portal_id IS NOT NULL THEN\n        UPDATE usuarios\n        SET nombre = 'Anonimizado', email = 'anonimizado-' || id || '@invalid.local',\n            telefono = NULL, activo = false\n        WHERE id = f.usuario_portal_id;\n        UPDATE sesiones SET revocada_en = coalesce(revocada_en, now())\n        WHERE usuario_id = f.usuario_portal_id;\n        UPDATE tokens_uso_unico SET expira_en = least(expira_en, now())\n        WHERE usuario_id = f.usuario_portal_id;\n    END IF;\n    DELETE FROM conversaciones_comerciales\n    WHERE telefono = f.telefono\n       OR interesado_id IN (SELECT id FROM interesados WHERE familia_id = p_familia);\n    DELETE FROM conversaciones_whatsapp WHERE familia_id = p_familia OR telefono = f.telefono;\n    UPDATE interesados SET nombre = NULL, telefono = NULL, email = NULL, datos = '{}'\n    WHERE familia_id = p_familia;\n    UPDATE mensajes SET destino = NULL, contenido = NULL, asunto = NULL, variables = '[]'\n    WHERE familia_id = p_familia;\n    UPDATE solicitudes_afiliacion SET aceptacion = aceptacion - v_quitar,\n        contacto_nombre = CASE WHEN contacto_nombre IS NULL THEN NULL ELSE 'Anonimizado' END,\n        contacto_telefono = CASE WHEN contacto_telefono IS NULL THEN NULL ELSE v_telefono END,\n        contacto_email = NULL\n    WHERE familia_id = p_familia;\n    UPDATE contratos SET evidencia_aceptacion = evidencia_aceptacion - v_quitar\n    WHERE familia_id = p_familia;\n    UPDATE medios_pago_recurrente\n    SET email_titular = 'anonimizado@invalid.local', ultimos4 = NULL, activo = false\n    WHERE familia_id = p_familia;\n    UPDATE encuestas SET comentario = NULL WHERE familia_id = p_familia;\n    UPDATE destinatarios_campana SET telefono = v_telefono WHERE familia_id = p_familia;\n    UPDATE documentos_familia SET descripcion = NULL WHERE familia_id = p_familia;\n    -- Tambien los que se conservan: el nombre original puede llevar datos personales.\n    UPDATE archivos SET nombre_original = 'anonimizado'\n    WHERE id IN (SELECT archivo_id FROM documentos_familia WHERE familia_id = p_familia);\n    UPDATE contactos_familia\n    SET nombre = 'Anonimizado', telefono = v_telefono, email = NULL, relacion = NULL\n    WHERE familia_id = p_familia;\n    UPDATE familias\n    SET titular_nombre = 'Anonimizado',\n        documento = 'ANON' || upper(substr(replace(id::text, '-', ''), 1, 28)),\n        email = NULL, telefono = v_telefono, barrio = 'Anonimizado', direccion = NULL,\n        complemento = NULL, latitud = NULL,\n        longitud = NULL, geo_precision = NULL, notas = NULL, estado = 'cancelada',\n        dada_de_baja_en = coalesce(dada_de_baja_en, now()),\n        motivo_baja = 'Anonimizada (habeas data)', anonimizada_en = now()\n    WHERE id = p_familia;\n\n    -- El rastro en la bitacora, incluido el que acaba de dejar esta misma funcion.\n    v_ids := ARRAY(\n        SELECT p_familia::text\n        UNION SELECT f.usuario_portal_id::text WHERE f.usuario_portal_id IS NOT NULL\n        UNION SELECT id::text FROM mascotas WHERE familia_id = p_familia\n        UNION SELECT id::text FROM contactos_familia WHERE familia_id = p_familia\n        UNION SELECT id::text FROM documentos_familia WHERE familia_id = p_familia\n        UNION SELECT id::text FROM peludos_solicitud WHERE familia_id = p_familia\n        UNION SELECT id::text FROM interesados WHERE familia_id = p_familia\n        UNION SELECT id::text FROM mensajes WHERE familia_id = p_familia\n        UNION SELECT id::text FROM solicitudes_afiliacion WHERE familia_id = p_familia\n        UNION SELECT id::text FROM medios_pago_recurrente WHERE familia_id = p_familia\n        UNION SELECT id::text FROM encuestas WHERE familia_id = p_familia\n        UNION SELECT id::text FROM contratos WHERE familia_id = p_familia\n    );\n    UPDATE auditoria a\n    SET cambios = (\n        SELECT jsonb_object_agg(\n            e.k, CASE WHEN e.k = ANY (v_personales) THEN jsonb_build_array(v_anonimo, v_anonimo)\n                      ELSE e.v END)\n        FROM jsonb_each(a.cambios) AS e(k, v)\n    )\n    WHERE a.entidad_id = ANY (v_ids)\n      AND EXISTS (SELECT 1 FROM jsonb_object_keys(a.cambios) AS k WHERE k = ANY (v_personales));\n    RETURN;\nEND\n$$\n"

ESTADOS_ANTERIORES = ("pendiente_pago", "completada", "cancelada", "error")


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
    op.execute("ALTER TYPE estado_solicitud ADD VALUE 'pagada' AFTER 'pendiente_pago'")
    for tabla, columna, desde, hacia in ARISTAS:
        op.execute(
            "INSERT INTO transiciones_estado (tabla, columna, desde, hacia)"
            f" VALUES ('{tabla}', '{columna}', '{desde}', '{hacia}')"
        )

    op.add_column("solicitudes_afiliacion", sa.Column("ciudad", sa.String(80), nullable=True))
    op.execute(
        "UPDATE solicitudes_afiliacion s SET ciudad = f.ciudad FROM familias f"
        " WHERE f.id = s.familia_id"
    )
    op.alter_column("solicitudes_afiliacion", "ciudad", nullable=False)
    op.create_index("ix_solicitudes_afiliacion_ciudad", "solicitudes_afiliacion", ["ciudad"])
    op.create_foreign_key(
        "fk_solicitudes_afiliacion_ciudad_ciudades",
        "solicitudes_afiliacion",
        "ciudades",
        ["ciudad"],
        ["nombre"],
        onupdate="CASCADE",
    )
    for columna, tipo in (
        ("contacto_nombre", sa.String(160)),
        ("contacto_telefono", sa.String(32)),
        ("contacto_email", sa.String(255)),
        ("token_hash", sa.String(64)),
        ("token_enlace_hash", sa.String(64)),
        ("pagada_en", sa.DateTime(timezone=True)),
        ("recordada_en", sa.DateTime(timezone=True)),
    ):
        op.add_column("solicitudes_afiliacion", sa.Column(columna, tipo, nullable=True))
    for columna in ("token_hash", "token_enlace_hash"):
        op.create_unique_constraint(
            f"uq_solicitudes_afiliacion_{columna}", "solicitudes_afiliacion", [columna]
        )
    for tabla in ("solicitudes_afiliacion", "peludos_solicitud", "pagos"):
        op.alter_column(tabla, "familia_id", nullable=True)
    for tabla, checks in CHECKS.items():
        for nombre, expresion in checks.items():
            op.execute(
                f"ALTER TABLE {tabla} ADD CONSTRAINT ck_{tabla}_{nombre} CHECK ({expresion})"
            )
    for nombre, tabla, _, (usar, comprobar) in CAMBIOS:
        _alterar(nombre, tabla, usar, comprobar)
    op.execute(_ANONIMIZAR)


def downgrade() -> None:
    op.execute(_ANONIMIZAR_ANTERIOR)
    # Un registro sin familia no tiene forma en el modelo anterior: el downgrade falla con
    # ellos en vez de perderlos.
    for nombre, tabla, (usar, comprobar), _ in CAMBIOS:
        _alterar(nombre, tabla, usar, comprobar)
    for tabla, checks in CHECKS.items():
        for nombre in checks:
            op.execute(f"ALTER TABLE {tabla} DROP CONSTRAINT ck_{tabla}_{nombre}")
    for tabla in ("solicitudes_afiliacion", "peludos_solicitud", "pagos"):
        op.alter_column(tabla, "familia_id", nullable=False)
    for columna in ("token_hash", "token_enlace_hash"):
        op.drop_constraint(
            f"uq_solicitudes_afiliacion_{columna}", "solicitudes_afiliacion", type_="unique"
        )
    for columna in (
        "contacto_nombre",
        "contacto_telefono",
        "contacto_email",
        "token_hash",
        "token_enlace_hash",
        "pagada_en",
        "recordada_en",
    ):
        op.drop_column("solicitudes_afiliacion", columna)
    op.drop_constraint(
        "fk_solicitudes_afiliacion_ciudad_ciudades", "solicitudes_afiliacion", type_="foreignkey"
    )
    op.drop_index("ix_solicitudes_afiliacion_ciudad", table_name="solicitudes_afiliacion")
    op.drop_column("solicitudes_afiliacion", "ciudad")
    for tabla, columna, desde, hacia in ARISTAS:
        op.execute(
            f"DELETE FROM transiciones_estado WHERE tabla = '{tabla}' AND columna = '{columna}'"
            f" AND desde = '{desde}' AND hacia = '{hacia}'"
        )
    # PostgreSQL no quita un valor de un enum: se recrea el tipo sin el.
    op.execute("ALTER TYPE estado_solicitud RENAME TO estado_solicitud_anterior")
    valores = ", ".join(f"'{v}'" for v in ESTADOS_ANTERIORES)
    op.execute(f"CREATE TYPE estado_solicitud AS ENUM ({valores})")
    # El trigger de transiciones usa la columna: se quita mientras cambia de tipo.
    op.execute("DROP TRIGGER tr_solicitudes_afiliacion_transicion_estado ON solicitudes_afiliacion")
    op.execute(
        "ALTER TABLE solicitudes_afiliacion ALTER COLUMN estado TYPE estado_solicitud"
        " USING estado::text::estado_solicitud"
    )
    op.execute("DROP TYPE estado_solicitud_anterior")
    op.execute(
        "CREATE TRIGGER tr_solicitudes_afiliacion_transicion_estado"
        " BEFORE UPDATE OF estado ON solicitudes_afiliacion FOR EACH ROW"
        " WHEN (old.estado IS DISTINCT FROM new.estado)"
        " EXECUTE FUNCTION validar_transicion('estado')"
    )

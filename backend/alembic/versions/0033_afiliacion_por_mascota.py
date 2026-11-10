# ruff: noqa: E501  (politicas y funcion congeladas: expresiones SQL largas)
"""cartera: cada peludo con su plan dentro del contrato, y periodicidad de pago

6.2 y 6.3. El contrato sigue siendo uno por familia, pero cada peludo tiene su plan
(afiliaciones_mascota) y paga la tarifa de ese plan para el numero de peludos del contrato.
El contrato gana la periodicidad y el valor que cobra cada cuota; la cuota regular pasa a
llamarse `cuota` y dice cuantos meses cubre. La solicitud de afiliacion guarda sus peludos
con el plan y el valor cotizados (peludos_solicitud), tambien antes de que existan las
mascotas. El plan pierde su valor, su cupo y su ciudad: los sustituyen las tarifas y las
ciudades de la 0032. Las reglas `plan.mascota` (cupo y mascotas adicionales) se desactivan.

Datos existentes: cada contrato recibe una linea por mascota de la familia con el plan que
tenia; en los vigentes, las de las mascotas activas, con el valor mensual del contrato
repartido entre ellas para que nadie cambie de precio sin un recalculo. Las solicitudes
reciben sus peludos del mismo modo. Las tablas nuevas llevan auditoria y RLS (politicas de
app/core/permisos_db.py, congeladas aqui) y anonimizar_familia() cubre los nombres de los
peludos de las solicitudes: las dos versiones de la funcion estan aqui.

Es destructiva (borra columnas): no esta en produccion, asi que va en un solo despliegue.

Revision ID: 0033
Revises: 0032
Create Date: 2026-11-10 12:00:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None

PERIODICIDAD = postgresql.ENUM(name="periodicidad", create_type=False)

# (nombre, tabla, comando, rol, USING, WITH CHECK), de politicas(['afiliaciones_mascota', 'peludos_solicitud'])
POLITICAS = [
    (
        "p_afiliaciones_mascota_select",
        "afiliaciones_mascota",
        "SELECT",
        "timu_app",
        "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        None,
    ),
    (
        "p_afiliaciones_mascota_insert",
        "afiliaciones_mascota",
        "INSERT",
        "timu_app",
        None,
        "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
    ),
    (
        "p_afiliaciones_mascota_update",
        "afiliaciones_mascota",
        "UPDATE",
        "timu_app",
        "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
        "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
    ),
    (
        "p_afiliaciones_mascota_delete",
        "afiliaciones_mascota",
        "DELETE",
        "timu_app",
        "app_rol() IN ('sistema')",
        None,
    ),
    (
        "p_peludos_solicitud_select",
        "peludos_solicitud",
        "SELECT",
        "timu_app",
        "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        None,
    ),
    (
        "p_peludos_solicitud_insert",
        "peludos_solicitud",
        "INSERT",
        "timu_app",
        None,
        "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
    ),
    (
        "p_peludos_solicitud_update",
        "peludos_solicitud",
        "UPDATE",
        "timu_app",
        "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
    ),
    (
        "p_peludos_solicitud_delete",
        "peludos_solicitud",
        "DELETE",
        "timu_app",
        "app_rol() IN ('sistema')",
        None,
    ),
]

_ANONIMIZAR_ANTERIOR = "\nCREATE OR REPLACE FUNCTION anonimizar_familia(p_familia uuid) RETURNS SETOF text\nLANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$\nDECLARE\n    f familias%ROWTYPE;\n    v_ids text[];\n    v_anonimo constant text := '[anonimizado]';\n    -- Prefijo internacional 999: no esta asignado a ningun pais.\n    v_telefono constant text := '+99900000000';\n    v_quitar constant text[] :=\n        ARRAY['ip', 'user_agent', 'nombre', 'documento', 'email', 'telefono'];\n    v_personales constant text[] := ARRAY[\n        'titular_nombre', 'documento', 'email', 'telefono', 'barrio', 'direccion', 'relacion',\n        'descripcion',\n        'complemento', 'latitud', 'longitud',\n        'notas', 'motivo_baja', 'nombre', 'destino', 'contenido', 'asunto', 'variables',\n        'email_titular', 'ultimos4', 'comentario', 'aceptacion', 'evidencia_aceptacion', 'datos'\n    ];\nBEGIN\n    IF current_setting('app.rol', true) IS DISTINCT FROM 'admin' THEN\n        RAISE EXCEPTION 'Solo un administrador anonimiza una familia'\n            USING ERRCODE = 'insufficient_privilege';\n    END IF;\n    SELECT * INTO f FROM familias WHERE id = p_familia FOR UPDATE;\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'Familia % no encontrada', p_familia USING ERRCODE = 'no_data_found';\n    END IF;\n    IF f.anonimizada_en IS NOT NULL THEN\n        RAISE EXCEPTION 'La familia ya esta anonimizada' USING ERRCODE = 'check_violation';\n    END IF;\n    IF EXISTS (\n        SELECT 1 FROM contratos\n        WHERE familia_id = p_familia AND estado IN ('activa', 'en_mora', 'congelada')\n    ) THEN\n        RAISE EXCEPTION 'La familia tiene un contrato vigente' USING ERRCODE = 'check_violation';\n    END IF;\n\n    -- Ficheros con datos personales: fotos de las mascotas, PDF de contratos y carnets y\n    -- los documentos que subio el equipo, salvo los examenes externos, que son clinicos.\n    RETURN QUERY\n        WITH purgados AS (\n            UPDATE archivos a SET purgado_en = now(), nombre_original = 'anonimizado'\n            WHERE a.purgado_en IS NULL AND a.id IN (\n                SELECT foto_archivo_id FROM mascotas WHERE familia_id = p_familia\n                UNION SELECT documento_archivo_id FROM contratos WHERE familia_id = p_familia\n                UNION SELECT c.archivo_id FROM carnets_emitidos c\n                      JOIN mascotas m ON m.id = c.mascota_id WHERE m.familia_id = p_familia\n                UNION SELECT archivo_id FROM documentos_familia\n                      WHERE familia_id = p_familia AND categoria <> 'examen_externo'\n            )\n            RETURNING a.clave\n        )\n        SELECT clave::text FROM purgados;\n\n    UPDATE mascotas SET nombre = 'Mascota', foto_archivo_id = NULL WHERE familia_id = p_familia;\n    IF f.usuario_portal_id IS NOT NULL THEN\n        UPDATE usuarios\n        SET nombre = 'Anonimizado', email = 'anonimizado-' || id || '@invalid.local',\n            telefono = NULL, activo = false\n        WHERE id = f.usuario_portal_id;\n        UPDATE sesiones SET revocada_en = coalesce(revocada_en, now())\n        WHERE usuario_id = f.usuario_portal_id;\n        UPDATE tokens_uso_unico SET expira_en = least(expira_en, now())\n        WHERE usuario_id = f.usuario_portal_id;\n    END IF;\n    DELETE FROM conversaciones_comerciales\n    WHERE telefono = f.telefono\n       OR interesado_id IN (SELECT id FROM interesados WHERE familia_id = p_familia);\n    DELETE FROM conversaciones_whatsapp WHERE familia_id = p_familia OR telefono = f.telefono;\n    UPDATE interesados SET nombre = NULL, telefono = NULL, email = NULL, datos = '{}'\n    WHERE familia_id = p_familia;\n    UPDATE mensajes SET destino = NULL, contenido = NULL, asunto = NULL, variables = '[]'\n    WHERE familia_id = p_familia;\n    UPDATE solicitudes_afiliacion SET aceptacion = aceptacion - v_quitar\n    WHERE familia_id = p_familia;\n    UPDATE contratos SET evidencia_aceptacion = evidencia_aceptacion - v_quitar\n    WHERE familia_id = p_familia;\n    UPDATE medios_pago_recurrente\n    SET email_titular = 'anonimizado@invalid.local', ultimos4 = NULL, activo = false\n    WHERE familia_id = p_familia;\n    UPDATE encuestas SET comentario = NULL WHERE familia_id = p_familia;\n    UPDATE destinatarios_campana SET telefono = v_telefono WHERE familia_id = p_familia;\n    UPDATE documentos_familia SET descripcion = NULL WHERE familia_id = p_familia;\n    -- Tambien los que se conservan: el nombre original puede llevar datos personales.\n    UPDATE archivos SET nombre_original = 'anonimizado'\n    WHERE id IN (SELECT archivo_id FROM documentos_familia WHERE familia_id = p_familia);\n    UPDATE contactos_familia\n    SET nombre = 'Anonimizado', telefono = v_telefono, email = NULL, relacion = NULL\n    WHERE familia_id = p_familia;\n    UPDATE familias\n    SET titular_nombre = 'Anonimizado',\n        documento = 'ANON' || upper(substr(replace(id::text, '-', ''), 1, 28)),\n        email = NULL, telefono = v_telefono, barrio = 'Anonimizado', direccion = NULL,\n        complemento = NULL, latitud = NULL,\n        longitud = NULL, geo_precision = NULL, notas = NULL, estado = 'cancelada',\n        dada_de_baja_en = coalesce(dada_de_baja_en, now()),\n        motivo_baja = 'Anonimizada (habeas data)', anonimizada_en = now()\n    WHERE id = p_familia;\n\n    -- El rastro en la bitacora, incluido el que acaba de dejar esta misma funcion.\n    v_ids := ARRAY(\n        SELECT p_familia::text\n        UNION SELECT f.usuario_portal_id::text WHERE f.usuario_portal_id IS NOT NULL\n        UNION SELECT id::text FROM mascotas WHERE familia_id = p_familia\n        UNION SELECT id::text FROM contactos_familia WHERE familia_id = p_familia\n        UNION SELECT id::text FROM documentos_familia WHERE familia_id = p_familia\n        UNION SELECT id::text FROM interesados WHERE familia_id = p_familia\n        UNION SELECT id::text FROM mensajes WHERE familia_id = p_familia\n        UNION SELECT id::text FROM solicitudes_afiliacion WHERE familia_id = p_familia\n        UNION SELECT id::text FROM medios_pago_recurrente WHERE familia_id = p_familia\n        UNION SELECT id::text FROM encuestas WHERE familia_id = p_familia\n        UNION SELECT id::text FROM contratos WHERE familia_id = p_familia\n    );\n    UPDATE auditoria a\n    SET cambios = (\n        SELECT jsonb_object_agg(\n            e.k, CASE WHEN e.k = ANY (v_personales) THEN jsonb_build_array(v_anonimo, v_anonimo)\n                      ELSE e.v END)\n        FROM jsonb_each(a.cambios) AS e(k, v)\n    )\n    WHERE a.entidad_id = ANY (v_ids)\n      AND EXISTS (SELECT 1 FROM jsonb_object_keys(a.cambios) AS k WHERE k = ANY (v_personales));\n    RETURN;\nEND\n$$\n"

_ANONIMIZAR = "\nCREATE OR REPLACE FUNCTION anonimizar_familia(p_familia uuid) RETURNS SETOF text\nLANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$\nDECLARE\n    f familias%ROWTYPE;\n    v_ids text[];\n    v_anonimo constant text := '[anonimizado]';\n    -- Prefijo internacional 999: no esta asignado a ningun pais.\n    v_telefono constant text := '+99900000000';\n    v_quitar constant text[] :=\n        ARRAY['ip', 'user_agent', 'nombre', 'documento', 'email', 'telefono'];\n    v_personales constant text[] := ARRAY[\n        'titular_nombre', 'documento', 'email', 'telefono', 'barrio', 'direccion', 'relacion',\n        'descripcion',\n        'complemento', 'latitud', 'longitud',\n        'notas', 'motivo_baja', 'nombre', 'destino', 'contenido', 'asunto', 'variables',\n        'email_titular', 'ultimos4', 'comentario', 'aceptacion', 'evidencia_aceptacion', 'datos'\n    ];\nBEGIN\n    IF current_setting('app.rol', true) IS DISTINCT FROM 'admin' THEN\n        RAISE EXCEPTION 'Solo un administrador anonimiza una familia'\n            USING ERRCODE = 'insufficient_privilege';\n    END IF;\n    SELECT * INTO f FROM familias WHERE id = p_familia FOR UPDATE;\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'Familia % no encontrada', p_familia USING ERRCODE = 'no_data_found';\n    END IF;\n    IF f.anonimizada_en IS NOT NULL THEN\n        RAISE EXCEPTION 'La familia ya esta anonimizada' USING ERRCODE = 'check_violation';\n    END IF;\n    IF EXISTS (\n        SELECT 1 FROM contratos\n        WHERE familia_id = p_familia AND estado IN ('activa', 'en_mora', 'congelada')\n    ) THEN\n        RAISE EXCEPTION 'La familia tiene un contrato vigente' USING ERRCODE = 'check_violation';\n    END IF;\n\n    -- Ficheros con datos personales: fotos de las mascotas, PDF de contratos y carnets y\n    -- los documentos que subio el equipo, salvo los examenes externos, que son clinicos.\n    RETURN QUERY\n        WITH purgados AS (\n            UPDATE archivos a SET purgado_en = now(), nombre_original = 'anonimizado'\n            WHERE a.purgado_en IS NULL AND a.id IN (\n                SELECT foto_archivo_id FROM mascotas WHERE familia_id = p_familia\n                UNION SELECT documento_archivo_id FROM contratos WHERE familia_id = p_familia\n                UNION SELECT c.archivo_id FROM carnets_emitidos c\n                      JOIN mascotas m ON m.id = c.mascota_id WHERE m.familia_id = p_familia\n                UNION SELECT archivo_id FROM documentos_familia\n                      WHERE familia_id = p_familia AND categoria <> 'examen_externo'\n            )\n            RETURNING a.clave\n        )\n        SELECT clave::text FROM purgados;\n\n    UPDATE mascotas SET nombre = 'Mascota', foto_archivo_id = NULL WHERE familia_id = p_familia;\n    UPDATE peludos_solicitud SET nombre = 'Mascota' WHERE familia_id = p_familia;\n    IF f.usuario_portal_id IS NOT NULL THEN\n        UPDATE usuarios\n        SET nombre = 'Anonimizado', email = 'anonimizado-' || id || '@invalid.local',\n            telefono = NULL, activo = false\n        WHERE id = f.usuario_portal_id;\n        UPDATE sesiones SET revocada_en = coalesce(revocada_en, now())\n        WHERE usuario_id = f.usuario_portal_id;\n        UPDATE tokens_uso_unico SET expira_en = least(expira_en, now())\n        WHERE usuario_id = f.usuario_portal_id;\n    END IF;\n    DELETE FROM conversaciones_comerciales\n    WHERE telefono = f.telefono\n       OR interesado_id IN (SELECT id FROM interesados WHERE familia_id = p_familia);\n    DELETE FROM conversaciones_whatsapp WHERE familia_id = p_familia OR telefono = f.telefono;\n    UPDATE interesados SET nombre = NULL, telefono = NULL, email = NULL, datos = '{}'\n    WHERE familia_id = p_familia;\n    UPDATE mensajes SET destino = NULL, contenido = NULL, asunto = NULL, variables = '[]'\n    WHERE familia_id = p_familia;\n    UPDATE solicitudes_afiliacion SET aceptacion = aceptacion - v_quitar\n    WHERE familia_id = p_familia;\n    UPDATE contratos SET evidencia_aceptacion = evidencia_aceptacion - v_quitar\n    WHERE familia_id = p_familia;\n    UPDATE medios_pago_recurrente\n    SET email_titular = 'anonimizado@invalid.local', ultimos4 = NULL, activo = false\n    WHERE familia_id = p_familia;\n    UPDATE encuestas SET comentario = NULL WHERE familia_id = p_familia;\n    UPDATE destinatarios_campana SET telefono = v_telefono WHERE familia_id = p_familia;\n    UPDATE documentos_familia SET descripcion = NULL WHERE familia_id = p_familia;\n    -- Tambien los que se conservan: el nombre original puede llevar datos personales.\n    UPDATE archivos SET nombre_original = 'anonimizado'\n    WHERE id IN (SELECT archivo_id FROM documentos_familia WHERE familia_id = p_familia);\n    UPDATE contactos_familia\n    SET nombre = 'Anonimizado', telefono = v_telefono, email = NULL, relacion = NULL\n    WHERE familia_id = p_familia;\n    UPDATE familias\n    SET titular_nombre = 'Anonimizado',\n        documento = 'ANON' || upper(substr(replace(id::text, '-', ''), 1, 28)),\n        email = NULL, telefono = v_telefono, barrio = 'Anonimizado', direccion = NULL,\n        complemento = NULL, latitud = NULL,\n        longitud = NULL, geo_precision = NULL, notas = NULL, estado = 'cancelada',\n        dada_de_baja_en = coalesce(dada_de_baja_en, now()),\n        motivo_baja = 'Anonimizada (habeas data)', anonimizada_en = now()\n    WHERE id = p_familia;\n\n    -- El rastro en la bitacora, incluido el que acaba de dejar esta misma funcion.\n    v_ids := ARRAY(\n        SELECT p_familia::text\n        UNION SELECT f.usuario_portal_id::text WHERE f.usuario_portal_id IS NOT NULL\n        UNION SELECT id::text FROM mascotas WHERE familia_id = p_familia\n        UNION SELECT id::text FROM contactos_familia WHERE familia_id = p_familia\n        UNION SELECT id::text FROM documentos_familia WHERE familia_id = p_familia\n        UNION SELECT id::text FROM peludos_solicitud WHERE familia_id = p_familia\n        UNION SELECT id::text FROM interesados WHERE familia_id = p_familia\n        UNION SELECT id::text FROM mensajes WHERE familia_id = p_familia\n        UNION SELECT id::text FROM solicitudes_afiliacion WHERE familia_id = p_familia\n        UNION SELECT id::text FROM medios_pago_recurrente WHERE familia_id = p_familia\n        UNION SELECT id::text FROM encuestas WHERE familia_id = p_familia\n        UNION SELECT id::text FROM contratos WHERE familia_id = p_familia\n    );\n    UPDATE auditoria a\n    SET cambios = (\n        SELECT jsonb_object_agg(\n            e.k, CASE WHEN e.k = ANY (v_personales) THEN jsonb_build_array(v_anonimo, v_anonimo)\n                      ELSE e.v END)\n        FROM jsonb_each(a.cambios) AS e(k, v)\n    )\n    WHERE a.entidad_id = ANY (v_ids)\n      AND EXISTS (SELECT 1 FROM jsonb_object_keys(a.cambios) AS k WHERE k = ANY (v_personales));\n    RETURN;\nEND\n$$\n"

VALORES_CONTRATO = "valor_mensual >= 0 AND valor_periodo >= 0 AND saldo_a_favor >= 0"
VALORES_CONTRATO_ANTERIOR = (
    "valor_mensual >= 0 AND valor_plan >= 0 AND valor_adicional_mascota >= 0"
    " AND saldo_a_favor >= 0 AND mascotas_adicionales >= 0"
)


def _literal(texto: str) -> str:
    return "'" + texto.replace("'", "''") + "'"


def upgrade() -> None:
    # Destino de la clave compuesta de afiliaciones_mascota: antes que la tabla que la usa.
    op.create_index("uq_contratos_id_familia", "contratos", ["id", "familia_id"], unique=True)
    op.create_table(
        "afiliaciones_mascota",
        sa.Column("familia_id", sa.Uuid(), nullable=False),
        sa.Column("contrato_id", sa.Uuid(), nullable=False),
        sa.Column("mascota_id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("valor_mensual", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False),
        sa.Column("dada_de_baja_en", sa.DateTime(timezone=True), nullable=True),
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
            "activa = (dada_de_baja_en IS NULL)",
            name=op.f("ck_afiliaciones_mascota_baja_coherente"),
        ),
        sa.CheckConstraint(
            "uuid_extract_version(id) = 7", name=op.f("ck_afiliaciones_mascota_id_uuidv7")
        ),
        sa.CheckConstraint(
            "valor_mensual >= 0", name=op.f("ck_afiliaciones_mascota_valor_no_negativo")
        ),
        sa.ForeignKeyConstraint(
            ["contrato_id", "familia_id"],
            ["contratos.id", "contratos.familia_id"],
            name="fk_afiliaciones_mascota_contrato_de_la_familia",
        ),
        sa.ForeignKeyConstraint(
            ["familia_id"],
            ["familias.id"],
            name=op.f("fk_afiliaciones_mascota_familia_id_familias"),
        ),
        sa.ForeignKeyConstraint(
            ["mascota_id", "familia_id"],
            ["mascotas.id", "mascotas.familia_id"],
            name="fk_afiliaciones_mascota_mascota_de_la_familia",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["planes.id"], name=op.f("fk_afiliaciones_mascota_plan_id_planes")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_afiliaciones_mascota")),
    )
    op.create_index(
        op.f("ix_afiliaciones_mascota_contrato_id"),
        "afiliaciones_mascota",
        ["contrato_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_afiliaciones_mascota_familia_id"),
        "afiliaciones_mascota",
        ["familia_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_afiliaciones_mascota_mascota_id"),
        "afiliaciones_mascota",
        ["mascota_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_afiliaciones_mascota_plan_id"), "afiliaciones_mascota", ["plan_id"], unique=False
    )
    op.create_index(
        "uq_afiliaciones_mascota_mascota_vigente",
        "afiliaciones_mascota",
        ["mascota_id"],
        unique=True,
        postgresql_where=sa.text("activa"),
    )
    op.create_table(
        "peludos_solicitud",
        sa.Column("solicitud_id", sa.Uuid(), nullable=False),
        sa.Column("familia_id", sa.Uuid(), nullable=False),
        sa.Column("posicion", sa.Integer(), nullable=False),
        sa.Column("mascota_id", sa.Uuid(), nullable=True),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("especie", sa.String(length=40), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("valor_mensual", sa.Numeric(precision=12, scale=2), nullable=False),
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
            "btrim(nombre) <> ''", name=op.f("ck_peludos_solicitud_nombre_no_vacio")
        ),
        sa.CheckConstraint("posicion >= 1", name=op.f("ck_peludos_solicitud_posicion_positiva")),
        sa.CheckConstraint(
            "uuid_extract_version(id) = 7", name=op.f("ck_peludos_solicitud_id_uuidv7")
        ),
        sa.CheckConstraint(
            "valor_mensual >= 0", name=op.f("ck_peludos_solicitud_valor_no_negativo")
        ),
        sa.ForeignKeyConstraint(
            ["especie"],
            ["especies.codigo"],
            name=op.f("fk_peludos_solicitud_especie_especies"),
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["familia_id"], ["familias.id"], name=op.f("fk_peludos_solicitud_familia_id_familias")
        ),
        sa.ForeignKeyConstraint(
            ["mascota_id"], ["mascotas.id"], name=op.f("fk_peludos_solicitud_mascota_id_mascotas")
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["planes.id"], name=op.f("fk_peludos_solicitud_plan_id_planes")
        ),
        sa.ForeignKeyConstraint(
            ["solicitud_id"],
            ["solicitudes_afiliacion.id"],
            name=op.f("fk_peludos_solicitud_solicitud_id_solicitudes_afiliacion"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_peludos_solicitud")),
    )
    op.create_index(
        op.f("ix_peludos_solicitud_especie"), "peludos_solicitud", ["especie"], unique=False
    )
    op.create_index(
        op.f("ix_peludos_solicitud_familia_id"), "peludos_solicitud", ["familia_id"], unique=False
    )
    op.create_index(
        op.f("ix_peludos_solicitud_mascota_id"), "peludos_solicitud", ["mascota_id"], unique=False
    )
    op.create_index(
        op.f("ix_peludos_solicitud_plan_id"), "peludos_solicitud", ["plan_id"], unique=False
    )
    op.create_index(
        op.f("ix_peludos_solicitud_solicitud_id"),
        "peludos_solicitud",
        ["solicitud_id"],
        unique=False,
    )
    op.create_index(
        "uq_peludos_solicitud_posicion",
        "peludos_solicitud",
        ["solicitud_id", "posicion"],
        unique=True,
        postgresql_where=None,
    )
    for tabla in ("afiliaciones_mascota", "peludos_solicitud"):
        op.execute(
            f"CREATE TRIGGER tr_{tabla}_auditoria AFTER INSERT OR UPDATE OR DELETE"
            f" ON {tabla} FOR EACH ROW EXECUTE FUNCTION auditar()"
        )
        op.execute(f"ALTER TABLE {tabla} ENABLE ROW LEVEL SECURITY")
    for nombre, tabla, comando, rol, usar, comprobar in POLITICAS:
        sql = f"CREATE POLICY {nombre} ON {tabla} FOR {comando} TO {rol}"
        if usar is not None:
            sql += f" USING ({usar})"
        if comprobar is not None:
            sql += f" WITH CHECK ({comprobar})"
        op.execute(sql)
        texto = f"USING ({usar}) WITH CHECK ({comprobar})"
        op.execute(f"COMMENT ON POLICY {nombre} ON {tabla} IS {_literal(texto)}")

    # Contrato: periodicidad y valor de cada cuota (hasta hoy, todo mensual).
    op.add_column("contratos", sa.Column("periodicidad", PERIODICIDAD, nullable=True))
    op.add_column("contratos", sa.Column("valor_periodo", sa.Numeric(12, 2), nullable=True))
    op.execute("UPDATE contratos SET periodicidad = 'mensual', valor_periodo = valor_mensual")
    op.alter_column("contratos", "periodicidad", nullable=False)
    op.alter_column("contratos", "valor_periodo", nullable=False)

    # Cada contrato, una linea por mascota con el plan que tenia. En los vigentes, las
    # mascotas activas y el valor mensual repartido entre ellas (el resto, en la primera).
    op.execute(
        """
        WITH lineas AS (
            SELECT c.id AS contrato_id, c.familia_id, m.id AS mascota_id, c.plan_id,
                   c.valor_mensual, c.estado IN ('activa', 'en_mora', 'congelada') AS vigente,
                   coalesce(c.fecha_fin::timestamptz, c.updated_at) AS fin,
                   row_number() OVER (PARTITION BY c.id ORDER BY m.created_at, m.id) AS n,
                   count(*) OVER (PARTITION BY c.id) AS total
            FROM contratos c
            JOIN mascotas m ON m.familia_id = c.familia_id
            WHERE m.activa OR c.estado NOT IN ('activa', 'en_mora', 'congelada')
        )
        INSERT INTO afiliaciones_mascota
            (familia_id, contrato_id, mascota_id, plan_id, valor_mensual, activa, dada_de_baja_en)
        SELECT familia_id, contrato_id, mascota_id, plan_id,
               CASE WHEN n = 1
                    THEN valor_mensual - round(valor_mensual / total, 2) * (total - 1)
                    ELSE round(valor_mensual / total, 2) END,
               vigente, CASE WHEN vigente THEN NULL ELSE fin END
        FROM lineas
        """
    )
    # Las solicitudes: sus peludos con el plan elegido y el valor repartido igual.
    op.execute(
        """
        WITH peludos AS (
            SELECT s.id AS solicitud_id, s.familia_id, m.id AS mascota_id, m.nombre,
                   m.especie, s.plan_id, s.valor_inicial,
                   row_number() OVER (PARTITION BY s.id ORDER BY m.created_at, m.id) AS n,
                   count(*) OVER (PARTITION BY s.id) AS total
            FROM solicitudes_afiliacion s
            JOIN mascotas m ON m.familia_id = s.familia_id AND m.activa
        )
        INSERT INTO peludos_solicitud
            (solicitud_id, familia_id, posicion, mascota_id, nombre, especie, plan_id,
             valor_mensual)
        SELECT solicitud_id, familia_id, n, mascota_id, nombre, especie, plan_id,
               CASE WHEN n = 1
                    THEN valor_inicial - round(valor_inicial / total, 2) * (total - 1)
                    ELSE round(valor_inicial / total, 2) END
        FROM peludos
        """
    )
    op.add_column("solicitudes_afiliacion", sa.Column("periodicidad", PERIODICIDAD, nullable=True))
    op.execute("UPDATE solicitudes_afiliacion SET periodicidad = 'mensual'")
    op.alter_column("solicitudes_afiliacion", "periodicidad", nullable=False)
    op.drop_index("ix_solicitudes_afiliacion_plan_id", table_name="solicitudes_afiliacion")
    op.drop_constraint(
        "fk_solicitudes_afiliacion_plan_id_planes", "solicitudes_afiliacion", type_="foreignkey"
    )
    op.drop_column("solicitudes_afiliacion", "plan_id")

    # El cambio de plan es de un peludo.
    op.add_column("cambios_plan", sa.Column("mascota_id", sa.Uuid(), nullable=True))
    op.create_index("ix_cambios_plan_mascota_id", "cambios_plan", ["mascota_id"], unique=False)
    op.create_foreign_key(
        "fk_cambios_plan_mascota_id_mascotas", "cambios_plan", "mascotas", ["mascota_id"], ["id"]
    )

    # Cuota regular: `cuota`, con los meses que cubre.
    op.add_column("cuotas", sa.Column("meses", sa.Integer(), server_default="1", nullable=False))
    op.alter_column("cuotas", "meses", server_default=None)
    op.execute("ALTER TABLE cuotas DROP CONSTRAINT ck_cuotas_tipo_formato")
    op.execute("UPDATE cuotas SET tipo = 'cuota' WHERE tipo = 'mensual'")
    op.execute(
        "ALTER TABLE cuotas ADD CONSTRAINT ck_cuotas_tipo_formato"
        " CHECK (tipo ~ '^(cuota|ajuste[0-9]*)$')"
    )
    op.execute(
        "ALTER TABLE cuotas ADD CONSTRAINT ck_cuotas_meses_periodicidad CHECK (meses IN (1, 3, 6, 12))"
    )

    # Fuera lo que sustituyen las lineas y las tarifas. Borrar valor_plan se lleva el CHECK
    # de valores del contrato: se crea de nuevo con las columnas que quedan.
    op.drop_index("ix_contratos_plan_id", table_name="contratos")
    op.drop_constraint("fk_contratos_plan_id_planes", "contratos", type_="foreignkey")
    for columna in ("plan_id", "mascotas_adicionales", "valor_adicional_mascota", "valor_plan"):
        op.drop_column("contratos", columna)
    op.execute(
        f"ALTER TABLE contratos ADD CONSTRAINT ck_contratos_valores_no_negativos CHECK ({VALORES_CONTRATO})"
    )
    op.drop_index("ix_planes_ciudad", table_name="planes")
    op.drop_constraint("fk_planes_ciudad_ciudades", "planes", type_="foreignkey")
    for columna in ("ciudad", "cupos_mascotas", "valor_mensual"):
        op.drop_column("planes", columna)

    op.execute("UPDATE reglas SET activa = false WHERE evento = 'plan.mascota'")
    op.execute(_ANONIMIZAR)


def downgrade() -> None:
    op.execute(_ANONIMIZAR_ANTERIOR)
    # El plan vuelve a tener un valor (el de un peludo) y cupo para todos sus peludos.
    op.add_column("planes", sa.Column("valor_mensual", sa.Numeric(12, 2), nullable=True))
    op.add_column("planes", sa.Column("cupos_mascotas", sa.Integer(), nullable=True))
    op.add_column("planes", sa.Column("ciudad", sa.String(80), nullable=True))
    op.execute(
        "UPDATE planes p SET cupos_mascotas = 10, valor_mensual = coalesce("
        "(SELECT valor FROM tarifas_plan t WHERE t.plan_id = p.id AND t.peludos = 1), 0)"
    )
    op.alter_column("planes", "valor_mensual", nullable=False)
    op.alter_column("planes", "cupos_mascotas", nullable=False)
    op.create_foreign_key(
        "fk_planes_ciudad_ciudades",
        "planes",
        "ciudades",
        ["ciudad"],
        ["nombre"],
        onupdate="CASCADE",
    )
    op.create_index("ix_planes_ciudad", "planes", ["ciudad"], unique=False)
    op.execute(
        "ALTER TABLE planes ADD CONSTRAINT ck_planes_valor_no_negativo CHECK (valor_mensual >= 0)"
    )
    op.execute(
        "ALTER TABLE planes ADD CONSTRAINT ck_planes_cupos_minimo CHECK (cupos_mascotas >= 1)"
    )

    # El contrato vuelve a un plan: el de su primera linea, con todo el valor en el plan.
    for columna, tipo in (
        ("plan_id", sa.Uuid()),
        ("valor_plan", sa.Numeric(12, 2)),
        ("mascotas_adicionales", sa.Integer()),
        ("valor_adicional_mascota", sa.Numeric(12, 2)),
    ):
        op.add_column("contratos", sa.Column(columna, tipo, nullable=True))
    op.execute(
        "UPDATE contratos c SET valor_plan = c.valor_mensual, mascotas_adicionales = 0,"
        " valor_adicional_mascota = 0, plan_id = coalesce("
        "(SELECT a.plan_id FROM afiliaciones_mascota a WHERE a.contrato_id = c.id"
        " ORDER BY a.created_at, a.id LIMIT 1), (SELECT id FROM planes ORDER BY codigo LIMIT 1))"
    )
    for columna in ("plan_id", "valor_plan", "mascotas_adicionales", "valor_adicional_mascota"):
        op.alter_column("contratos", columna, nullable=False)
    op.create_foreign_key("fk_contratos_plan_id_planes", "contratos", "planes", ["plan_id"], ["id"])
    op.create_index("ix_contratos_plan_id", "contratos", ["plan_id"], unique=False)
    op.execute("ALTER TABLE contratos DROP CONSTRAINT ck_contratos_valores_no_negativos")
    op.drop_column("contratos", "valor_periodo")
    op.drop_column("contratos", "periodicidad")
    op.execute(
        f"ALTER TABLE contratos ADD CONSTRAINT ck_contratos_valores_no_negativos CHECK ({VALORES_CONTRATO_ANTERIOR})"
    )

    # Las cuotas de varios meses no tienen forma en el modelo anterior: quedan como mensuales.
    op.execute("ALTER TABLE cuotas DROP CONSTRAINT ck_cuotas_meses_periodicidad")
    op.execute("ALTER TABLE cuotas DROP CONSTRAINT ck_cuotas_tipo_formato")
    op.execute("UPDATE cuotas SET tipo = 'mensual' WHERE tipo = 'cuota'")
    op.execute(
        "ALTER TABLE cuotas ADD CONSTRAINT ck_cuotas_tipo_formato"
        " CHECK (tipo ~ '^(mensual|ajuste[0-9]*)$')"
    )
    op.drop_column("cuotas", "meses")

    op.drop_constraint("fk_cambios_plan_mascota_id_mascotas", "cambios_plan", type_="foreignkey")
    op.drop_index("ix_cambios_plan_mascota_id", table_name="cambios_plan")
    op.drop_column("cambios_plan", "mascota_id")

    op.add_column("solicitudes_afiliacion", sa.Column("plan_id", sa.Uuid(), nullable=True))
    op.execute(
        "UPDATE solicitudes_afiliacion s SET plan_id = coalesce("
        "(SELECT p.plan_id FROM peludos_solicitud p WHERE p.solicitud_id = s.id"
        " ORDER BY p.posicion LIMIT 1), (SELECT id FROM planes ORDER BY codigo LIMIT 1))"
    )
    op.alter_column("solicitudes_afiliacion", "plan_id", nullable=False)
    op.create_foreign_key(
        "fk_solicitudes_afiliacion_plan_id_planes",
        "solicitudes_afiliacion",
        "planes",
        ["plan_id"],
        ["id"],
    )
    op.create_index(
        "ix_solicitudes_afiliacion_plan_id", "solicitudes_afiliacion", ["plan_id"], unique=False
    )
    op.drop_column("solicitudes_afiliacion", "periodicidad")

    op.drop_table("peludos_solicitud")
    op.drop_table("afiliaciones_mascota")
    op.drop_index("uq_contratos_id_familia", table_name="contratos")
    # Las reglas plan.mascota quedan desactivadas: sin regla activa, el modelo anterior
    # rechaza las mascotas sobre el cupo, que es lo que hacia la regla sembrada.

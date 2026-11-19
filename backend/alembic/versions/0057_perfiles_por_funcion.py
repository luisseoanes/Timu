# ruff: noqa: E501  (politicas congeladas: expresiones SQL largas)
"""usuarios y RLS: los perfiles de gerencia y de atencion al cliente, y cada perfil con lo suyo

Seccion 12: "cada perfil debera contar con permisos diferenciados de acuerdo con sus
funciones", y nombra entre ellos gerencia y atencion al cliente, que no existian. Decidido con
el usuario el 2026-11-19 (docs/perfiles-y-permisos.md): cada perfil hace lo suyo y nada mas, y
la base lo hace cumplir: la matriz de app/core/permisos_db.py da a cada perfil solo las tablas
que tocan sus rutas (derivadas con TIMU_REGISTRO_ACCESOS). Estan la expresion anterior y la
nueva de cada politica que cambia (congeladas).

Revision ID: 0057
Revises: 0056
Create Date: 2026-11-19 12:00:00
"""

from alembic import op

revision = "0057"
down_revision = "0056"
branch_labels = None
depends_on = None

_ROLES_ANTERIORES = ["admin", "comercial", "operaciones", "medico", "familia", "aliada"]

# (nombre, tabla, (USING, WITH CHECK) anterior, (USING, WITH CHECK) nueva)
CAMBIOS = [
    (
        "p_adjuntos_clinicos_select",
        "adjuntos_clinicos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (historia_id IN (SELECT id FROM historias_clinicas WHERE familia_id = app_familia() AND estado <> 'borrador')))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'medico') OR (app_rol() = 'familia' AND (historia_id IN (SELECT id FROM historias_clinicas WHERE familia_id = app_familia() AND estado <> 'borrador')))",
            None,
        ),
    ),
    (
        "p_afiliaciones_mascota_insert",
        "afiliaciones_mascota",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')"),
        (None, "app_rol() IN ('sistema', 'atencion_cliente', 'comercial')"),
    ),
    (
        "p_afiliaciones_mascota_select",
        "afiliaciones_mascota",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'atencion_cliente', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            None,
        ),
    ),
    (
        "p_afiliaciones_mascota_update",
        "afiliaciones_mascota",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial')",
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial')",
        ),
    ),
    (
        "p_altas_peludo_insert",
        "altas_peludo",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
        ),
    ),
    (
        "p_altas_peludo_select",
        "altas_peludo",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            None,
        ),
    ),
    (
        "p_altas_peludo_update",
        "altas_peludo",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
        ),
    ),
    (
        "p_aplicaciones_pago_insert",
        "aplicaciones_pago",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial')"),
        (None, "app_rol() IN ('sistema', 'atencion_cliente', 'comercial')"),
    ),
    (
        "p_aplicaciones_pago_select",
        "aplicaciones_pago",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'familia' AND (pago_id IN (SELECT id FROM pagos WHERE familia_id = app_familia())))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'gerencia') OR (app_rol() = 'familia' AND (pago_id IN (SELECT id FROM pagos WHERE familia_id = app_familia())))",
            None,
        ),
    ),
    (
        "p_archivos_insert",
        "archivos",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (subido_por_id = app_usuario() OR id IN (SELECT foto_archivo_id FROM mascotas WHERE familia_id = app_familia()) OR id IN (SELECT documento_archivo_id FROM contratos WHERE familia_id = app_familia()) OR id IN (SELECT archivo_id FROM adjuntos_clinicos WHERE historia_id IN (SELECT id FROM historias_clinicas WHERE familia_id = app_familia() AND estado <> 'borrador')) OR id IN (SELECT archivo_id FROM carnets_emitidos WHERE mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia())) OR id IN (SELECT archivo_id FROM documentos_familia WHERE familia_id = app_familia() AND visible_familia AND activo)))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (subido_por_id = app_usuario() OR id IN (SELECT foto_archivo_id FROM mascotas WHERE familia_id = app_familia()) OR id IN (SELECT documento_archivo_id FROM contratos WHERE familia_id = app_familia()) OR id IN (SELECT archivo_id FROM adjuntos_clinicos WHERE historia_id IN (SELECT id FROM historias_clinicas WHERE familia_id = app_familia() AND estado <> 'borrador')) OR id IN (SELECT archivo_id FROM carnets_emitidos WHERE mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia())) OR id IN (SELECT archivo_id FROM documentos_familia WHERE familia_id = app_familia() AND visible_familia AND activo)))",
        ),
    ),
    (
        "p_archivos_select",
        "archivos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (subido_por_id = app_usuario() OR id IN (SELECT foto_archivo_id FROM mascotas WHERE familia_id = app_familia()) OR id IN (SELECT documento_archivo_id FROM contratos WHERE familia_id = app_familia()) OR id IN (SELECT archivo_id FROM adjuntos_clinicos WHERE historia_id IN (SELECT id FROM historias_clinicas WHERE familia_id = app_familia() AND estado <> 'borrador')) OR id IN (SELECT archivo_id FROM carnets_emitidos WHERE mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia())) OR id IN (SELECT archivo_id FROM documentos_familia WHERE familia_id = app_familia() AND visible_familia AND activo))) OR (app_rol() = 'publico' AND (proposito::text = 'logo_aliada' AND id IN (SELECT logo_archivo_id FROM clinicas_aliadas WHERE en_portada AND activa)))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'atencion_cliente', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (subido_por_id = app_usuario() OR id IN (SELECT foto_archivo_id FROM mascotas WHERE familia_id = app_familia()) OR id IN (SELECT documento_archivo_id FROM contratos WHERE familia_id = app_familia()) OR id IN (SELECT archivo_id FROM adjuntos_clinicos WHERE historia_id IN (SELECT id FROM historias_clinicas WHERE familia_id = app_familia() AND estado <> 'borrador')) OR id IN (SELECT archivo_id FROM carnets_emitidos WHERE mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia())) OR id IN (SELECT archivo_id FROM documentos_familia WHERE familia_id = app_familia() AND visible_familia AND activo))) OR (app_rol() = 'publico' AND (proposito::text = 'logo_aliada' AND id IN (SELECT logo_archivo_id FROM clinicas_aliadas WHERE en_portada AND activa)))",
            None,
        ),
    ),
    (
        "p_auditoria_select",
        "auditoria",
        ("app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')", None),
        ("app_rol() IN ('sistema', 'atencion_cliente', 'comercial')", None),
    ),
    (
        "p_bajas_comunicaciones_insert",
        "bajas_comunicaciones",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')"),
        (
            None,
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'medico', 'operaciones')",
        ),
    ),
    (
        "p_bajas_comunicaciones_select",
        "bajas_comunicaciones",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (destino IN (SELECT telefono FROM familias WHERE id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()) UNION SELECT email FROM familias WHERE id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica())))) OR (app_rol() = 'familia' AND (destino IN (SELECT telefono FROM familias WHERE id IN (app_familia()) UNION SELECT email FROM familias WHERE id IN (app_familia()))))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (destino IN (SELECT telefono FROM familias WHERE id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()) UNION SELECT email FROM familias WHERE id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica())))) OR (app_rol() = 'familia' AND (destino IN (SELECT telefono FROM familias WHERE id IN (app_familia()) UNION SELECT email FROM familias WHERE id IN (app_familia()))))",
            None,
        ),
    ),
    (
        "p_bajas_comunicaciones_update",
        "bajas_comunicaciones",
        ("app_rol() IN ('sistema', 'admin')", "app_rol() IN ('sistema', 'admin')"),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial')",
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial')",
        ),
    ),
    (
        "p_beneficios_adicionales_plan_select",
        "beneficios_adicionales_plan",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'atencion_cliente', 'comercial', 'familia', 'gerencia', 'medico', 'operaciones', 'publico')",
            None,
        ),
    ),
    (
        "p_beneficios_plan_select",
        "beneficios_plan",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'atencion_cliente', 'comercial', 'familia', 'gerencia', 'medico', 'operaciones', 'publico')",
            None,
        ),
    ),
    (
        "p_bloqueos_agenda_insert",
        "bloqueos_agenda",
        (None, "app_rol() IN ('sistema', 'admin', 'operaciones')"),
        (None, "app_rol() IN ('sistema', 'operaciones')"),
    ),
    (
        "p_bloqueos_agenda_select",
        "bloqueos_agenda",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'familia', 'medico', 'operaciones')",
            None,
        ),
        ("app_rol() IN ('sistema', 'atencion_cliente', 'familia', 'operaciones')", None),
    ),
    (
        "p_cambios_plan_insert",
        "cambios_plan",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')"),
        (None, "app_rol() IN ('sistema', 'atencion_cliente', 'comercial')"),
    ),
    (
        "p_cambios_plan_select",
        "cambios_plan",
        ("app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')", None),
        ("app_rol() IN ('sistema', 'atencion_cliente', 'comercial')", None),
    ),
    (
        "p_campanas_insert",
        "campanas",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial')"),
        (None, "app_rol() IN ('sistema', 'comercial')"),
    ),
    (
        "p_campanas_select",
        "campanas",
        ("app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')", None),
        ("app_rol() IN ('sistema', 'comercial')", None),
    ),
    (
        "p_campanas_update",
        "campanas",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial')",
            "app_rol() IN ('sistema', 'admin', 'comercial')",
        ),
        ("app_rol() IN ('sistema', 'comercial')", "app_rol() IN ('sistema', 'comercial')"),
    ),
    (
        "p_carnets_emitidos_insert",
        "carnets_emitidos",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia())))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'atencion_cliente', 'medico') OR (app_rol() = 'familia' AND (mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia())))",
        ),
    ),
    (
        "p_carnets_emitidos_select",
        "carnets_emitidos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia()))) OR (app_rol() = 'publico' AND (codigo = app_llave('carnet')))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'medico') OR (app_rol() = 'familia' AND (mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia()))) OR (app_rol() = 'publico' AND (codigo = app_llave('carnet')))",
            None,
        ),
    ),
    (
        "p_ciudades_plan_select",
        "ciudades_plan",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'atencion_cliente', 'comercial', 'familia', 'gerencia', 'medico', 'operaciones', 'publico')",
            None,
        ),
    ),
    (
        "p_ciudades_select",
        "ciudades",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'atencion_cliente', 'comercial', 'familia', 'gerencia', 'medico', 'operaciones', 'publico')",
            None,
        ),
    ),
    (
        "p_clinicas_aliadas_insert",
        "clinicas_aliadas",
        (None, "app_rol() IN ('sistema', 'admin')"),
        (None, "app_rol() IN ('sistema', 'operaciones')"),
    ),
    (
        "p_clinicas_aliadas_select",
        "clinicas_aliadas",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (id = app_clinica())) OR (app_rol() = 'publico' AND (en_portada AND activa))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'gerencia', 'operaciones') OR (app_rol() = 'aliada' AND (id = app_clinica())) OR (app_rol() = 'publico' AND (en_portada AND activa))",
            None,
        ),
    ),
    (
        "p_clinicas_aliadas_update",
        "clinicas_aliadas",
        ("app_rol() IN ('sistema', 'admin')", "app_rol() IN ('sistema', 'admin')"),
        ("app_rol() IN ('sistema', 'operaciones')", "app_rol() IN ('sistema', 'operaciones')"),
    ),
    (
        "p_contactos_familia_insert",
        "contactos_familia",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial', 'operaciones')"),
        (None, "app_rol() IN ('sistema', 'atencion_cliente')"),
    ),
    (
        "p_contactos_familia_select",
        "contactos_familia",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'atencion_cliente', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            None,
        ),
    ),
    (
        "p_contactos_familia_update",
        "contactos_familia",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'operaciones')",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'operaciones')",
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente')",
            "app_rol() IN ('sistema', 'atencion_cliente')",
        ),
    ),
    (
        "p_contratos_insert",
        "contratos",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial')"),
        (None, "app_rol() IN ('sistema', 'comercial')"),
    ),
    (
        "p_contratos_select",
        "contratos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'atencion_cliente', 'comercial', 'gerencia', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            None,
        ),
    ),
    (
        "p_contratos_update",
        "contratos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial')",
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial')",
        ),
    ),
    (
        "p_convenios_aliadas_insert",
        "convenios_aliadas",
        (None, "app_rol() IN ('sistema', 'admin')"),
        (None, "app_rol() IN ('sistema', 'operaciones')"),
    ),
    (
        "p_convenios_aliadas_select",
        "convenios_aliadas",
        ("app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')", None),
        ("app_rol() IN ('sistema', 'atencion_cliente', 'operaciones')", None),
    ),
    (
        "p_conversaciones_comerciales_select",
        "conversaciones_comerciales",
        ("app_rol() IN ('sistema', 'admin', 'comercial')", None),
        ("app_rol() IN ('sistema', 'comercial')", None),
    ),
    (
        "p_conversaciones_comerciales_update",
        "conversaciones_comerciales",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial')",
            "app_rol() IN ('sistema', 'admin', 'comercial')",
        ),
        ("app_rol() IN ('sistema', 'comercial')", "app_rol() IN ('sistema', 'comercial')"),
    ),
    (
        "p_conversaciones_whatsapp_select",
        "conversaciones_whatsapp",
        ("app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')", None),
        ("app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'medico')", None),
    ),
    (
        "p_cuotas_insert",
        "cuotas",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial')"),
        (None, "app_rol() IN ('sistema', 'comercial')"),
    ),
    (
        "p_cuotas_select",
        "cuotas",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (contrato_id IN (SELECT id FROM contratos WHERE familia_id = app_familia())))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'gerencia', 'operaciones') OR (app_rol() = 'familia' AND (contrato_id IN (SELECT id FROM contratos WHERE familia_id = app_familia())))",
            None,
        ),
    ),
    (
        "p_cuotas_update",
        "cuotas",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial')",
            "app_rol() IN ('sistema', 'admin', 'comercial')",
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial')",
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial')",
        ),
    ),
    (
        "p_datos_timu_insert",
        "datos_timu",
        (None, "app_rol() IN ('sistema', 'admin')"),
        (None, "app_rol() IN ('sistema')"),
    ),
    (
        "p_datos_timu_select",
        "datos_timu",
        (
            "app_rol() IN ('sistema', 'admin', 'aliada', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'aliada', 'atencion_cliente', 'comercial', 'familia', 'gerencia', 'medico', 'operaciones', 'publico')",
            None,
        ),
    ),
    (
        "p_destinatarios_campana_select",
        "destinatarios_campana",
        ("app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')", None),
        ("app_rol() IN ('sistema', 'comercial')", None),
    ),
    (
        "p_destinatarios_campana_update",
        "destinatarios_campana",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial')",
            "app_rol() IN ('sistema', 'admin', 'comercial')",
        ),
        ("app_rol() IN ('sistema', 'comercial')", "app_rol() IN ('sistema', 'comercial')"),
    ),
    (
        "p_distancias_cache_select",
        "distancias_cache",
        ("app_rol() IN ('sistema', 'admin', 'medico', 'operaciones')", None),
        ("app_rol() IN ('sistema', 'medico', 'operaciones')", None),
    ),
    (
        "p_documentos_familia_insert",
        "documentos_familia",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')"),
        (None, "app_rol() IN ('sistema', 'atencion_cliente')"),
    ),
    (
        "p_documentos_familia_select",
        "documentos_familia",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia() AND visible_familia AND activo))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente') OR (app_rol() = 'familia' AND (familia_id = app_familia() AND visible_familia AND activo))",
            None,
        ),
    ),
    (
        "p_documentos_familia_update",
        "documentos_familia",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente')",
            "app_rol() IN ('sistema', 'atencion_cliente')",
        ),
    ),
    (
        "p_ejecuciones_campana_select",
        "ejecuciones_campana",
        ("app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')", None),
        ("app_rol() IN ('sistema', 'comercial')", None),
    ),
    (
        "p_ejecuciones_campana_update",
        "ejecuciones_campana",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial')",
            "app_rol() IN ('sistema', 'admin', 'comercial')",
        ),
        ("app_rol() IN ('sistema', 'comercial')", "app_rol() IN ('sistema', 'comercial')"),
    ),
    (
        "p_encuestas_select",
        "encuestas",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'publico' AND (token = app_llave('encuesta')))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'gerencia', 'operaciones') OR (app_rol() = 'publico' AND (token = app_llave('encuesta')))",
            None,
        ),
    ),
    (
        "p_especies_select",
        "especies",
        (
            "app_rol() IN ('sistema', 'admin', 'aliada', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'aliada', 'atencion_cliente', 'comercial', 'familia', 'medico', 'publico')",
            None,
        ),
    ),
    (
        "p_esquemas_preventivos_select",
        "esquemas_preventivos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'familia', 'medico', 'operaciones')",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'atencion_cliente', 'comercial', 'familia', 'gerencia', 'medico', 'operaciones')",
            None,
        ),
    ),
    (
        "p_eventos_pasarela_insert",
        "eventos_pasarela",
        (None, "app_rol() IN ('sistema', 'admin')"),
        (None, "app_rol() IN ('sistema', 'atencion_cliente')"),
    ),
    (
        "p_eventos_pasarela_select",
        "eventos_pasarela",
        ("app_rol() IN ('sistema', 'admin')", None),
        ("app_rol() IN ('sistema', 'atencion_cliente')", None),
    ),
    (
        "p_eventos_pasarela_update",
        "eventos_pasarela",
        ("app_rol() IN ('sistema', 'admin')", "app_rol() IN ('sistema', 'admin')"),
        (
            "app_rol() IN ('sistema', 'atencion_cliente')",
            "app_rol() IN ('sistema', 'atencion_cliente')",
        ),
    ),
    (
        "p_eventos_preventivos_insert",
        "eventos_preventivos",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')"),
        (
            None,
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'medico', 'operaciones')",
        ),
    ),
    (
        "p_eventos_preventivos_select",
        "eventos_preventivos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia())))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia())))",
            None,
        ),
    ),
    (
        "p_eventos_preventivos_update",
        "eventos_preventivos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia())))",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia())))",
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia())))",
            "app_rol() IN ('sistema', 'atencion_cliente', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia())))",
        ),
    ),
    (
        "p_eventos_salientes_insert",
        "eventos_salientes",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'aliada', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'aliada', 'atencion_cliente', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
        ),
    ),
    (
        "p_eventos_salientes_select",
        "eventos_salientes",
        (
            "app_rol() IN ('sistema', 'admin', 'aliada', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'aliada', 'atencion_cliente', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
            None,
        ),
    ),
    (
        "p_familias_insert",
        "familias",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'publico' AND (id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'publico' AND (id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))))",
        ),
    ),
    (
        "p_familias_select",
        "familias",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (id = app_familia() OR usuario_portal_id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'atencion_cliente', 'comercial', 'gerencia', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (id = app_familia() OR usuario_portal_id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))))",
            None,
        ),
    ),
    (
        "p_familias_update",
        "familias",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (id = app_familia() OR usuario_portal_id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))))",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (id = app_familia() OR usuario_portal_id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))))",
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (id = app_familia() OR usuario_portal_id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))))",
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (id = app_familia() OR usuario_portal_id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))))",
        ),
    ),
    (
        "p_formulas_select",
        "formulas",
        ("app_rol() IN ('sistema', 'medico')", None),
        ("app_rol() IN ('sistema', 'atencion_cliente', 'medico')", None),
    ),
    (
        "p_franjas_agenda_insert",
        "franjas_agenda",
        (None, "app_rol() IN ('sistema', 'admin', 'operaciones')"),
        (None, "app_rol() IN ('sistema', 'operaciones')"),
    ),
    (
        "p_franjas_agenda_select",
        "franjas_agenda",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'familia', 'medico', 'operaciones')",
            None,
        ),
        ("app_rol() IN ('sistema', 'atencion_cliente', 'familia', 'operaciones')", None),
    ),
    (
        "p_franjas_agenda_update",
        "franjas_agenda",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'familia', 'medico', 'operaciones')",
            "app_rol() IN ('sistema', 'admin', 'operaciones')",
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'familia', 'operaciones')",
            "app_rol() IN ('sistema', 'operaciones')",
        ),
    ),
    (
        "p_historias_clinicas_select",
        "historias_clinicas",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia() AND estado <> 'borrador'))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'medico') OR (app_rol() = 'familia' AND (familia_id = app_familia() AND estado <> 'borrador'))",
            None,
        ),
    ),
    (
        "p_intentos_cobro_select",
        "intentos_cobro",
        ("app_rol() IN ('sistema', 'admin')", None),
        ("app_rol() IN ('sistema', 'atencion_cliente')", None),
    ),
    (
        "p_interesados_insert",
        "interesados",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (telefono = app_llave('contacto_telefono') OR email = app_llave('contacto_email') OR familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'comercial') OR (app_rol() = 'publico' AND (telefono = app_llave('contacto_telefono') OR email = app_llave('contacto_email') OR familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        ),
    ),
    (
        "p_interesados_select",
        "interesados",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (telefono = app_llave('contacto_telefono') OR email = app_llave('contacto_email') OR familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'comercial') OR (app_rol() = 'publico' AND (telefono = app_llave('contacto_telefono') OR email = app_llave('contacto_email') OR familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            None,
        ),
    ),
    (
        "p_interesados_update",
        "interesados",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (telefono = app_llave('contacto_telefono') OR email = app_llave('contacto_email') OR familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (telefono = app_llave('contacto_telefono') OR email = app_llave('contacto_email') OR familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        ),
        (
            "app_rol() IN ('sistema', 'comercial') OR (app_rol() = 'publico' AND (telefono = app_llave('contacto_telefono') OR email = app_llave('contacto_email') OR familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            "app_rol() IN ('sistema', 'comercial') OR (app_rol() = 'publico' AND (telefono = app_llave('contacto_telefono') OR email = app_llave('contacto_email') OR familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        ),
    ),
    (
        "p_mascotas_insert",
        "mascotas",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR id IN (SELECT mascota_id FROM servicios WHERE id IN (SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta')))))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR id IN (SELECT mascota_id FROM servicios WHERE id IN (SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta')))))",
        ),
    ),
    (
        "p_mascotas_select",
        "mascotas",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR id IN (SELECT mascota_id FROM servicios WHERE id IN (SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta')))))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'atencion_cliente', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR id IN (SELECT mascota_id FROM servicios WHERE id IN (SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta')))))",
            None,
        ),
    ),
    (
        "p_mascotas_update",
        "mascotas",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            "app_rol() IN ('sistema', 'atencion_cliente', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
        ),
    ),
    (
        "p_medios_pago_recurrente_insert",
        "medios_pago_recurrente",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial')"),
        (None, "app_rol() IN ('sistema', 'atencion_cliente')"),
    ),
    (
        "p_medios_pago_recurrente_select",
        "medios_pago_recurrente",
        ("app_rol() IN ('sistema', 'admin', 'comercial')", None),
        ("app_rol() IN ('sistema', 'atencion_cliente')", None),
    ),
    (
        "p_medios_pago_recurrente_update",
        "medios_pago_recurrente",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial')",
            "app_rol() IN ('sistema', 'admin', 'comercial')",
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente')",
            "app_rol() IN ('sistema', 'atencion_cliente')",
        ),
    ),
    (
        "p_mensajes_insert",
        "mensajes",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (destino IN (SELECT email FROM usuarios WHERE id = app_llave('usuario')::uuid UNION SELECT telefono FROM usuarios WHERE id = app_llave('usuario')::uuid)))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (destino IN (SELECT email FROM usuarios WHERE id = app_llave('usuario')::uuid UNION SELECT telefono FROM usuarios WHERE id = app_llave('usuario')::uuid)))",
        ),
    ),
    (
        "p_mensajes_select",
        "mensajes",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (destino IN (SELECT email FROM usuarios WHERE id = app_llave('usuario')::uuid UNION SELECT telefono FROM usuarios WHERE id = app_llave('usuario')::uuid)))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (destino IN (SELECT email FROM usuarios WHERE id = app_llave('usuario')::uuid UNION SELECT telefono FROM usuarios WHERE id = app_llave('usuario')::uuid)))",
            None,
        ),
    ),
    (
        "p_pagos_insert",
        "pagos",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR referencia_externa = app_llave('referencia_pago')))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial') OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR referencia_externa = app_llave('referencia_pago')))",
        ),
    ),
    (
        "p_pagos_select",
        "pagos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR referencia_externa = app_llave('referencia_pago')))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'gerencia') OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR referencia_externa = app_llave('referencia_pago')))",
            None,
        ),
    ),
    (
        "p_pagos_update",
        "pagos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR referencia_externa = app_llave('referencia_pago')))",
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR referencia_externa = app_llave('referencia_pago')))",
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR referencia_externa = app_llave('referencia_pago')))",
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR referencia_externa = app_llave('referencia_pago')))",
        ),
    ),
    (
        "p_paradas_ruta_insert",
        "paradas_ruta",
        (None, "app_rol() IN ('sistema', 'admin', 'operaciones')"),
        (None, "app_rol() IN ('sistema', 'operaciones')"),
    ),
    (
        "p_paradas_ruta_select",
        "paradas_ruta",
        ("app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')", None),
        ("app_rol() IN ('sistema', 'gerencia', 'medico', 'operaciones')", None),
    ),
    (
        "p_paradas_ruta_update",
        "paradas_ruta",
        (
            "app_rol() IN ('sistema', 'admin', 'medico', 'operaciones')",
            "app_rol() IN ('sistema', 'admin', 'medico', 'operaciones')",
        ),
        (
            "app_rol() IN ('sistema', 'medico', 'operaciones')",
            "app_rol() IN ('sistema', 'medico', 'operaciones')",
        ),
    ),
    (
        "p_peludos_solicitud_insert",
        "peludos_solicitud",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR solicitud_id = app_llave('registro')::uuid))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR solicitud_id = app_llave('registro')::uuid))",
        ),
    ),
    (
        "p_peludos_solicitud_select",
        "peludos_solicitud",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR solicitud_id = app_llave('registro')::uuid))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR solicitud_id = app_llave('registro')::uuid))",
            None,
        ),
    ),
    (
        "p_peludos_solicitud_update",
        "peludos_solicitud",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR solicitud_id = app_llave('registro')::uuid))",
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR solicitud_id = app_llave('registro')::uuid))",
        ),
        (
            "app_rol() IN ('sistema', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR solicitud_id = app_llave('registro')::uuid))",
            "app_rol() IN ('sistema', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR solicitud_id = app_llave('registro')::uuid))",
        ),
    ),
    (
        "p_pendientes_insert",
        "pendientes",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')"),
        (None, "app_rol() IN ('sistema', 'medico')"),
    ),
    (
        "p_pendientes_select",
        "pendientes",
        ("app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')", None),
        ("app_rol() IN ('sistema', 'atencion_cliente', 'medico', 'operaciones')", None),
    ),
    (
        "p_pendientes_update",
        "pendientes",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'operaciones')",
            "app_rol() IN ('sistema', 'atencion_cliente', 'operaciones')",
        ),
    ),
    (
        "p_planes_select",
        "planes",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'atencion_cliente', 'comercial', 'familia', 'gerencia', 'medico', 'operaciones', 'publico')",
            None,
        ),
    ),
    (
        "p_planificaciones_ruta_insert",
        "planificaciones_ruta",
        (None, "app_rol() IN ('sistema', 'admin', 'operaciones')"),
        (None, "app_rol() IN ('sistema', 'operaciones')"),
    ),
    (
        "p_planificaciones_ruta_select",
        "planificaciones_ruta",
        ("app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')", None),
        ("app_rol() IN ('sistema', 'operaciones')", None),
    ),
    (
        "p_plantillas_consulta_insert",
        "plantillas_consulta",
        (None, "app_rol() IN ('sistema', 'admin', 'medico')"),
        (None, "app_rol() IN ('sistema', 'medico')"),
    ),
    (
        "p_plantillas_consulta_select",
        "plantillas_consulta",
        ("app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')", None),
        ("app_rol() IN ('sistema', 'medico')", None),
    ),
    (
        "p_plantillas_consulta_update",
        "plantillas_consulta",
        (
            "app_rol() IN ('sistema', 'admin', 'medico')",
            "app_rol() IN ('sistema', 'admin', 'medico')",
        ),
        ("app_rol() IN ('sistema', 'medico')", "app_rol() IN ('sistema', 'medico')"),
    ),
    (
        "p_plantillas_whatsapp_insert",
        "plantillas_whatsapp",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial')"),
        (None, "app_rol() IN ('sistema', 'admin')"),
    ),
    (
        "p_plantillas_whatsapp_select",
        "plantillas_whatsapp",
        (
            "app_rol() IN ('sistema', 'admin', 'aliada', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'aliada', 'atencion_cliente', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
            None,
        ),
    ),
    (
        "p_plantillas_whatsapp_update",
        "plantillas_whatsapp",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial')",
            "app_rol() IN ('sistema', 'admin', 'comercial')",
        ),
        ("app_rol() IN ('sistema', 'admin')", "app_rol() IN ('sistema', 'admin')"),
    ),
    (
        "p_reglas_select",
        "reglas",
        (
            "app_rol() IN ('sistema', 'admin', 'aliada', 'comercial', 'familia', 'medico', 'operaciones')",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'aliada', 'atencion_cliente', 'comercial', 'familia', 'medico', 'operaciones')",
            None,
        ),
    ),
    (
        "p_remisiones_aliadas_insert",
        "remisiones_aliadas",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')"),
        (None, "app_rol() IN ('sistema', 'atencion_cliente')"),
    ),
    (
        "p_remisiones_aliadas_select",
        "remisiones_aliadas",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (clinica_id = app_clinica()))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'gerencia', 'operaciones') OR (app_rol() = 'aliada' AND (clinica_id = app_clinica()))",
            None,
        ),
    ),
    (
        "p_remisiones_aliadas_update",
        "remisiones_aliadas",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (clinica_id = app_clinica()))",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (clinica_id = app_clinica()))",
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente') OR (app_rol() = 'aliada' AND (clinica_id = app_clinica()))",
            "app_rol() IN ('sistema', 'atencion_cliente') OR (app_rol() = 'aliada' AND (clinica_id = app_clinica()))",
        ),
    ),
    (
        "p_reportes_programados_insert",
        "reportes_programados",
        (None, "app_rol() IN ('sistema', 'admin')"),
        (None, "app_rol() IN ('sistema', 'gerencia')"),
    ),
    (
        "p_reportes_programados_select",
        "reportes_programados",
        ("app_rol() IN ('sistema', 'admin')", None),
        ("app_rol() IN ('sistema', 'gerencia')", None),
    ),
    (
        "p_reportes_programados_update",
        "reportes_programados",
        ("app_rol() IN ('sistema', 'admin')", "app_rol() IN ('sistema', 'admin')"),
        ("app_rol() IN ('sistema', 'gerencia')", "app_rol() IN ('sistema', 'gerencia')"),
    ),
    (
        "p_respuestas_virtuales_insert",
        "respuestas_virtuales",
        (None, "app_rol() IN ('sistema', 'admin', 'medico')"),
        (None, "app_rol() IN ('sistema', 'medico')"),
    ),
    (
        "p_respuestas_virtuales_select",
        "respuestas_virtuales",
        ("app_rol() IN ('sistema', 'admin', 'medico')", None),
        ("app_rol() IN ('sistema', 'medico')", None),
    ),
    (
        "p_respuestas_virtuales_update",
        "respuestas_virtuales",
        ("app_rol() IN ('sistema', 'admin')", "app_rol() IN ('sistema', 'admin')"),
        ("app_rol() IN ('sistema', 'medico')", "app_rol() IN ('sistema', 'medico')"),
    ),
    (
        "p_rutas_select",
        "rutas",
        ("app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')", None),
        ("app_rol() IN ('sistema', 'gerencia', 'medico', 'operaciones')", None),
    ),
    (
        "p_rutas_update",
        "rutas",
        (
            "app_rol() IN ('sistema', 'admin', 'medico', 'operaciones')",
            "app_rol() IN ('sistema', 'admin', 'medico', 'operaciones')",
        ),
        (
            "app_rol() IN ('sistema', 'medico', 'operaciones')",
            "app_rol() IN ('sistema', 'medico', 'operaciones')",
        ),
    ),
    (
        "p_segmentos_insert",
        "segmentos",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial')"),
        (None, "app_rol() IN ('sistema', 'comercial')"),
    ),
    (
        "p_segmentos_select",
        "segmentos",
        ("app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')", None),
        ("app_rol() IN ('sistema', 'comercial')", None),
    ),
    (
        "p_servicio_pasos_insert",
        "servicio_pasos",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')"),
        (None, "app_rol() IN ('sistema', 'medico')"),
    ),
    (
        "p_servicio_pasos_select",
        "servicio_pasos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (servicio_id IN (SELECT servicio_id FROM remisiones_aliadas WHERE clinica_id = app_clinica())))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (servicio_id IN (SELECT servicio_id FROM remisiones_aliadas WHERE clinica_id = app_clinica())))",
            None,
        ),
    ),
    (
        "p_servicio_pasos_update",
        "servicio_pasos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
        ),
        ("app_rol() IN ('sistema', 'medico')", "app_rol() IN ('sistema', 'medico')"),
    ),
    (
        "p_servicios_insert",
        "servicios",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'atencion_cliente', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
        ),
    ),
    (
        "p_servicios_select",
        "servicios",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (id IN (SELECT servicio_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (id IN (SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta'))))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'gerencia', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (id IN (SELECT servicio_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (id IN (SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta'))))",
            None,
        ),
    ),
    (
        "p_servicios_update",
        "servicios",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (id IN (SELECT servicio_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (id IN (SELECT servicio_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (id IN (SELECT servicio_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            "app_rol() IN ('sistema', 'atencion_cliente', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (id IN (SELECT servicio_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
        ),
    ),
    (
        "p_sesiones_select",
        "sesiones",
        (
            "app_rol() IN ('sistema', 'admin') OR (app_rol() = 'aliada' AND (usuario_id = app_usuario())) OR (app_rol() = 'comercial' AND (usuario_id = app_usuario())) OR (app_rol() = 'familia' AND (usuario_id = app_usuario())) OR (app_rol() = 'medico' AND (usuario_id = app_usuario())) OR (app_rol() = 'operaciones' AND (usuario_id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('sesion')::uuid OR refresh_hash = app_llave('renovacion') OR refresh_hash_anterior = app_llave('renovacion') OR usuario_id = app_llave('autenticado')::uuid OR usuario_id = app_llave('revocar')::uuid))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin') OR (app_rol() = 'aliada' AND (usuario_id = app_usuario())) OR (app_rol() = 'atencion_cliente' AND (usuario_id = app_usuario())) OR (app_rol() = 'comercial' AND (usuario_id = app_usuario())) OR (app_rol() = 'familia' AND (usuario_id = app_usuario())) OR (app_rol() = 'gerencia' AND (usuario_id = app_usuario())) OR (app_rol() = 'medico' AND (usuario_id = app_usuario())) OR (app_rol() = 'operaciones' AND (usuario_id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('sesion')::uuid OR refresh_hash = app_llave('renovacion') OR refresh_hash_anterior = app_llave('renovacion') OR usuario_id = app_llave('autenticado')::uuid OR usuario_id = app_llave('revocar')::uuid))",
            None,
        ),
    ),
    (
        "p_sesiones_update",
        "sesiones",
        (
            "app_rol() IN ('sistema', 'admin') OR (app_rol() = 'aliada' AND (usuario_id = app_usuario())) OR (app_rol() = 'comercial' AND (usuario_id = app_usuario())) OR (app_rol() = 'familia' AND (usuario_id = app_usuario())) OR (app_rol() = 'medico' AND (usuario_id = app_usuario())) OR (app_rol() = 'operaciones' AND (usuario_id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('sesion')::uuid OR refresh_hash = app_llave('renovacion') OR refresh_hash_anterior = app_llave('renovacion') OR usuario_id = app_llave('autenticado')::uuid OR usuario_id = app_llave('revocar')::uuid))",
            "app_rol() IN ('sistema', 'admin') OR (app_rol() = 'aliada' AND (usuario_id = app_usuario())) OR (app_rol() = 'comercial' AND (usuario_id = app_usuario())) OR (app_rol() = 'familia' AND (usuario_id = app_usuario())) OR (app_rol() = 'medico' AND (usuario_id = app_usuario())) OR (app_rol() = 'operaciones' AND (usuario_id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('sesion')::uuid OR refresh_hash = app_llave('renovacion') OR refresh_hash_anterior = app_llave('renovacion') OR usuario_id = app_llave('autenticado')::uuid OR usuario_id = app_llave('revocar')::uuid))",
        ),
        (
            "app_rol() IN ('sistema', 'admin') OR (app_rol() = 'aliada' AND (usuario_id = app_usuario())) OR (app_rol() = 'atencion_cliente' AND (usuario_id = app_usuario())) OR (app_rol() = 'comercial' AND (usuario_id = app_usuario())) OR (app_rol() = 'familia' AND (usuario_id = app_usuario())) OR (app_rol() = 'gerencia' AND (usuario_id = app_usuario())) OR (app_rol() = 'medico' AND (usuario_id = app_usuario())) OR (app_rol() = 'operaciones' AND (usuario_id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('sesion')::uuid OR refresh_hash = app_llave('renovacion') OR refresh_hash_anterior = app_llave('renovacion') OR usuario_id = app_llave('autenticado')::uuid OR usuario_id = app_llave('revocar')::uuid))",
            "app_rol() IN ('sistema', 'admin') OR (app_rol() = 'aliada' AND (usuario_id = app_usuario())) OR (app_rol() = 'atencion_cliente' AND (usuario_id = app_usuario())) OR (app_rol() = 'comercial' AND (usuario_id = app_usuario())) OR (app_rol() = 'familia' AND (usuario_id = app_usuario())) OR (app_rol() = 'gerencia' AND (usuario_id = app_usuario())) OR (app_rol() = 'medico' AND (usuario_id = app_usuario())) OR (app_rol() = 'operaciones' AND (usuario_id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('sesion')::uuid OR refresh_hash = app_llave('renovacion') OR refresh_hash_anterior = app_llave('renovacion') OR usuario_id = app_llave('autenticado')::uuid OR usuario_id = app_llave('revocar')::uuid))",
        ),
    ),
    (
        "p_solicitudes_afiliacion_insert",
        "solicitudes_afiliacion",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR id = app_llave('registro')::uuid OR token_hash = app_llave('token_registro') OR token_enlace_hash = app_llave('token_registro')))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR id = app_llave('registro')::uuid OR token_hash = app_llave('token_registro') OR token_enlace_hash = app_llave('token_registro')))",
        ),
    ),
    (
        "p_solicitudes_afiliacion_select",
        "solicitudes_afiliacion",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR id = app_llave('registro')::uuid OR token_hash = app_llave('token_registro') OR token_enlace_hash = app_llave('token_registro')))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR id = app_llave('registro')::uuid OR token_hash = app_llave('token_registro') OR token_enlace_hash = app_llave('token_registro')))",
            None,
        ),
    ),
    (
        "p_solicitudes_afiliacion_update",
        "solicitudes_afiliacion",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR id = app_llave('registro')::uuid OR token_hash = app_llave('token_registro') OR token_enlace_hash = app_llave('token_registro')))",
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR id = app_llave('registro')::uuid OR token_hash = app_llave('token_registro') OR token_enlace_hash = app_llave('token_registro')))",
        ),
        (
            "app_rol() IN ('sistema', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR id = app_llave('registro')::uuid OR token_hash = app_llave('token_registro') OR token_enlace_hash = app_llave('token_registro')))",
            "app_rol() IN ('sistema', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR id = app_llave('registro')::uuid OR token_hash = app_llave('token_registro') OR token_enlace_hash = app_llave('token_registro')))",
        ),
    ),
    (
        "p_solicitudes_virtuales_insert",
        "solicitudes_virtuales",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'medico') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
        ),
    ),
    (
        "p_solicitudes_virtuales_select",
        "solicitudes_virtuales",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'medico') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            None,
        ),
    ),
    (
        "p_solicitudes_virtuales_update",
        "solicitudes_virtuales",
        (
            "app_rol() IN ('sistema', 'admin', 'medico')",
            "app_rol() IN ('sistema', 'admin', 'medico')",
        ),
        ("app_rol() IN ('sistema', 'medico')", "app_rol() IN ('sistema', 'medico')"),
    ),
    (
        "p_tareas_insert",
        "tareas",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (servicio_id IN (SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta'))))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (servicio_id IN (SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta'))))",
        ),
    ),
    (
        "p_tareas_select",
        "tareas",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (servicio_id IN (SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta'))))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (servicio_id IN (SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta'))))",
            None,
        ),
    ),
    (
        "p_tareas_update",
        "tareas",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones')",
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'medico', 'operaciones')",
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial', 'medico', 'operaciones')",
        ),
    ),
    (
        "p_tarifas_periodicidad_select",
        "tarifas_periodicidad",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'atencion_cliente', 'comercial', 'familia', 'gerencia', 'medico', 'operaciones', 'publico')",
            None,
        ),
    ),
    (
        "p_tarifas_plan_select",
        "tarifas_plan",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'atencion_cliente', 'comercial', 'familia', 'gerencia', 'medico', 'operaciones', 'publico')",
            None,
        ),
    ),
    (
        "p_tipos_servicio_select",
        "tipos_servicio",
        (
            "app_rol() IN ('sistema', 'admin', 'aliada', 'comercial', 'familia', 'medico', 'operaciones', 'publico')",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'aliada', 'atencion_cliente', 'comercial', 'familia', 'gerencia', 'medico', 'operaciones', 'publico')",
            None,
        ),
    ),
    (
        "p_tokens_uso_unico_insert",
        "tokens_uso_unico",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (token_hash = app_llave('token') OR usuario_id = app_llave('usuario')::uuid))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial') OR (app_rol() = 'publico' AND (token_hash = app_llave('token') OR usuario_id = app_llave('usuario')::uuid))",
        ),
    ),
    (
        "p_tokens_uso_unico_select",
        "tokens_uso_unico",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (token_hash = app_llave('token') OR usuario_id = app_llave('usuario')::uuid))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial') OR (app_rol() = 'publico' AND (token_hash = app_llave('token') OR usuario_id = app_llave('usuario')::uuid))",
            None,
        ),
    ),
    (
        "p_tokens_uso_unico_update",
        "tokens_uso_unico",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (token_hash = app_llave('token') OR usuario_id = app_llave('usuario')::uuid))",
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (token_hash = app_llave('token') OR usuario_id = app_llave('usuario')::uuid))",
        ),
        (
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial') OR (app_rol() = 'publico' AND (token_hash = app_llave('token') OR usuario_id = app_llave('usuario')::uuid))",
            "app_rol() IN ('sistema', 'atencion_cliente', 'comercial') OR (app_rol() = 'publico' AND (token_hash = app_llave('token') OR usuario_id = app_llave('usuario')::uuid))",
        ),
    ),
    (
        "p_usuarios_insert",
        "usuarios",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial')"),
        (None, "app_rol() IN ('sistema', 'admin', 'atencion_cliente', 'comercial')"),
    ),
    (
        "p_usuarios_select",
        "usuarios",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (id = app_usuario())) OR (app_rol() = 'familia' AND (id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('usuario')::uuid OR id = app_llave('autenticado')::uuid OR email = app_llave('ingreso_email') OR telefono = app_llave('ingreso_telefono') OR id IN (SELECT profesional_id FROM servicios WHERE id IN (SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta')))))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'atencion_cliente', 'comercial', 'gerencia', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (id = app_usuario())) OR (app_rol() = 'familia' AND (id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('usuario')::uuid OR id = app_llave('autenticado')::uuid OR email = app_llave('ingreso_email') OR telefono = app_llave('ingreso_telefono') OR id IN (SELECT profesional_id FROM servicios WHERE id IN (SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta')))))",
            None,
        ),
    ),
]


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
    # Los valores nuevos no se usan en esta migracion: ADD VALUE admite la transaccion.
    op.execute("ALTER TYPE rol ADD VALUE 'gerencia' AFTER 'admin'")
    op.execute("ALTER TYPE rol ADD VALUE 'atencion_cliente' AFTER 'comercial'")
    # Las politicas comparan app_rol() con texto: no usan el enum, asi que los valores nuevos
    # ya sirven en esta misma transaccion.
    for nombre, tabla, _, (usar, comprobar) in CAMBIOS:
        _alterar(nombre, tabla, usar, comprobar)


def downgrade() -> None:
    for nombre, tabla, (usar, comprobar), _ in CAMBIOS:
        _alterar(nombre, tabla, usar, comprobar)
    # PostgreSQL no quita un valor de un enum: se recrea el tipo sin ellos. Si queda algun
    # usuario con uno de los perfiles nuevos, la conversion falla y el downgrade se detiene
    # sin perderlo.
    # El CHECK de la aliada compara la columna con un valor del tipo: se quita y se recrea.
    op.execute("ALTER TABLE usuarios DROP CONSTRAINT ck_usuarios_aliada_con_clinica")
    op.execute("ALTER TYPE rol RENAME TO rol_anterior")
    valores = ", ".join(f"'{v}'" for v in _ROLES_ANTERIORES)
    op.execute(f"CREATE TYPE rol AS ENUM ({valores})")
    op.execute("ALTER TABLE usuarios ALTER COLUMN rol TYPE rol USING rol::text::rol")
    op.execute("DROP TYPE rol_anterior")
    op.execute(
        "ALTER TABLE usuarios ADD CONSTRAINT ck_usuarios_aliada_con_clinica"
        " CHECK ((rol = 'aliada') = (clinica_aliada_id IS NOT NULL))"
    )

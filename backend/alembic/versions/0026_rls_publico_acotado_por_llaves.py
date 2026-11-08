# ruff: noqa: E501  (datos congelados de app/core/permisos_db.py: expresiones SQL largas)
"""rls: publico solo ve las filas de quien declara la peticion

Fase 4 de docs/plan-persistencia.md, mejora pendiente. El perfil `publico` (peticiones sin
sesion y el comienzo de cada peticion autenticada) leia las tablas de autenticacion y de los
formularios publicos sin condicion de fila. Ahora solo admite las filas que casan con las
llaves que la peticion fija con `acotar_publico` (`app.llaves` del contexto, leidas con
app_llave()): la cuenta del email o telefono de ingreso, la sesion del token, la familia del
documento del formulario, la encuesta del enlace, el carnet del codigo. Crear una sesion o
cambiar una contrasena exige la llave `autenticado`.

El reparto de interesados por carga cuenta los de todos los comerciales, que `publico` ya no
ve: pasa a comercial_con_menos_carga(), SECURITY DEFINER, que solo devuelve el id elegido.

Las politicas cambiadas estan escritas aqui con su expresion anterior y la nueva.

Revision ID: 0026
Revises: 0025
Create Date: 2026-11-05 12:00:00
"""

from alembic import op

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None

# (politica, tabla, (USING, WITH CHECK) anterior, (USING, WITH CHECK) nuevo)
CAMBIOS: list[tuple[str, str, tuple[str | None, str | None], tuple[str | None, str | None]]] = [
    (
        "p_carnets_emitidos_select",
        "carnets_emitidos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones', 'publico') OR (app_rol() = 'familia' AND (mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia())))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (mascota_id IN (SELECT id FROM mascotas WHERE familia_id = app_familia()))) OR (app_rol() = 'publico' AND (codigo = app_llave('carnet')))",
            None,
        ),
    ),
    (
        "p_contratos_select",
        "contratos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones', 'publico') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            None,
        ),
    ),
    (
        "p_encuestas_select",
        "encuestas",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones', 'publico')",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'publico' AND (token = app_llave('encuesta')))",
            None,
        ),
    ),
    (
        "p_encuestas_update",
        "encuestas",
        ("app_rol() IN ('sistema', 'publico')", "app_rol() IN ('sistema', 'publico')"),
        (
            "app_rol() IN ('sistema') OR (app_rol() = 'publico' AND (token = app_llave('encuesta')))",
            "app_rol() IN ('sistema') OR (app_rol() = 'publico' AND (token = app_llave('encuesta')))",
        ),
    ),
    (
        "p_familias_select",
        "familias",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones', 'publico') OR (app_rol() = 'aliada' AND (id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (id = app_familia() OR usuario_portal_id = app_usuario()))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (id = app_familia() OR usuario_portal_id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))))",
            None,
        ),
    ),
    (
        "p_familias_insert",
        "familias",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones', 'publico')",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'publico' AND (id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))))",
        ),
    ),
    (
        "p_familias_update",
        "familias",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones', 'publico') OR (app_rol() = 'familia' AND (id = app_familia() OR usuario_portal_id = app_usuario()))",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones', 'publico') OR (app_rol() = 'familia' AND (id = app_familia() OR usuario_portal_id = app_usuario()))",
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (id = app_familia() OR usuario_portal_id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))))",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (id = app_familia() OR usuario_portal_id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))))",
        ),
    ),
    (
        "p_interesados_select",
        "interesados",
        ("app_rol() IN ('sistema', 'admin', 'comercial', 'publico')", None),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (telefono = app_llave('contacto_telefono') OR email = app_llave('contacto_email') OR familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            None,
        ),
    ),
    (
        "p_interesados_insert",
        "interesados",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial', 'publico')"),
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (telefono = app_llave('contacto_telefono') OR email = app_llave('contacto_email') OR familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        ),
    ),
    (
        "p_interesados_update",
        "interesados",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'publico')",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'publico')",
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (telefono = app_llave('contacto_telefono') OR email = app_llave('contacto_email') OR familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (telefono = app_llave('contacto_telefono') OR email = app_llave('contacto_email') OR familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        ),
    ),
    (
        "p_mascotas_select",
        "mascotas",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones', 'publico') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR id IN (SELECT mascota_id FROM servicios WHERE id IN (SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta')))))",
            None,
        ),
    ),
    (
        "p_mascotas_insert",
        "mascotas",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones', 'publico')",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento'))) OR id IN (SELECT mascota_id FROM servicios WHERE id IN (SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta')))))",
        ),
    ),
    (
        "p_mensajes_select",
        "mensajes",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones', 'publico') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (destino IN (SELECT email FROM usuarios WHERE id = app_llave('usuario')::uuid UNION SELECT telefono FROM usuarios WHERE id = app_llave('usuario')::uuid)))",
            None,
        ),
    ),
    (
        "p_mensajes_insert",
        "mensajes",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones', 'publico') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (destino IN (SELECT email FROM usuarios WHERE id = app_llave('usuario')::uuid UNION SELECT telefono FROM usuarios WHERE id = app_llave('usuario')::uuid)))",
        ),
    ),
    (
        "p_pagos_select",
        "pagos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones', 'publico') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            None,
        ),
    ),
    (
        "p_pagos_insert",
        "pagos",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'publico') OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        ),
    ),
    (
        "p_pagos_update",
        "pagos",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'publico')",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'publico')",
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        ),
    ),
    (
        "p_servicios_select",
        "servicios",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones', 'publico') OR (app_rol() = 'aliada' AND (id IN (SELECT servicio_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (id IN (SELECT servicio_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (id IN (SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta'))))",
            None,
        ),
    ),
    (
        "p_sesiones_select",
        "sesiones",
        (
            "app_rol() IN ('sistema', 'admin', 'publico') OR (app_rol() = 'aliada' AND (usuario_id = app_usuario())) OR (app_rol() = 'comercial' AND (usuario_id = app_usuario())) OR (app_rol() = 'familia' AND (usuario_id = app_usuario())) OR (app_rol() = 'medico' AND (usuario_id = app_usuario())) OR (app_rol() = 'operaciones' AND (usuario_id = app_usuario()))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin') OR (app_rol() = 'aliada' AND (usuario_id = app_usuario())) OR (app_rol() = 'comercial' AND (usuario_id = app_usuario())) OR (app_rol() = 'familia' AND (usuario_id = app_usuario())) OR (app_rol() = 'medico' AND (usuario_id = app_usuario())) OR (app_rol() = 'operaciones' AND (usuario_id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('sesion')::uuid OR refresh_hash = app_llave('renovacion') OR refresh_hash_anterior = app_llave('renovacion') OR usuario_id = app_llave('autenticado')::uuid OR usuario_id = app_llave('revocar')::uuid))",
            None,
        ),
    ),
    (
        "p_sesiones_insert",
        "sesiones",
        (None, "app_rol() IN ('sistema', 'publico')"),
        (
            None,
            "app_rol() IN ('sistema') OR (app_rol() = 'publico' AND (usuario_id = app_llave('autenticado')::uuid))",
        ),
    ),
    (
        "p_sesiones_update",
        "sesiones",
        (
            "app_rol() IN ('sistema', 'admin', 'publico') OR (app_rol() = 'aliada' AND (usuario_id = app_usuario())) OR (app_rol() = 'comercial' AND (usuario_id = app_usuario())) OR (app_rol() = 'familia' AND (usuario_id = app_usuario())) OR (app_rol() = 'medico' AND (usuario_id = app_usuario())) OR (app_rol() = 'operaciones' AND (usuario_id = app_usuario()))",
            "app_rol() IN ('sistema', 'admin', 'publico') OR (app_rol() = 'aliada' AND (usuario_id = app_usuario())) OR (app_rol() = 'comercial' AND (usuario_id = app_usuario())) OR (app_rol() = 'familia' AND (usuario_id = app_usuario())) OR (app_rol() = 'medico' AND (usuario_id = app_usuario())) OR (app_rol() = 'operaciones' AND (usuario_id = app_usuario()))",
        ),
        (
            "app_rol() IN ('sistema', 'admin') OR (app_rol() = 'aliada' AND (usuario_id = app_usuario())) OR (app_rol() = 'comercial' AND (usuario_id = app_usuario())) OR (app_rol() = 'familia' AND (usuario_id = app_usuario())) OR (app_rol() = 'medico' AND (usuario_id = app_usuario())) OR (app_rol() = 'operaciones' AND (usuario_id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('sesion')::uuid OR refresh_hash = app_llave('renovacion') OR refresh_hash_anterior = app_llave('renovacion') OR usuario_id = app_llave('autenticado')::uuid OR usuario_id = app_llave('revocar')::uuid))",
            "app_rol() IN ('sistema', 'admin') OR (app_rol() = 'aliada' AND (usuario_id = app_usuario())) OR (app_rol() = 'comercial' AND (usuario_id = app_usuario())) OR (app_rol() = 'familia' AND (usuario_id = app_usuario())) OR (app_rol() = 'medico' AND (usuario_id = app_usuario())) OR (app_rol() = 'operaciones' AND (usuario_id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('sesion')::uuid OR refresh_hash = app_llave('renovacion') OR refresh_hash_anterior = app_llave('renovacion') OR usuario_id = app_llave('autenticado')::uuid OR usuario_id = app_llave('revocar')::uuid))",
        ),
    ),
    (
        "p_solicitudes_afiliacion_select",
        "solicitudes_afiliacion",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones', 'publico')",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            None,
        ),
    ),
    (
        "p_solicitudes_afiliacion_insert",
        "solicitudes_afiliacion",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial', 'publico')"),
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        ),
    ),
    (
        "p_solicitudes_afiliacion_update",
        "solicitudes_afiliacion",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'publico')",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'publico')",
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (familia_id IN (SELECT id FROM familias WHERE id = app_llave('familia')::uuid OR (tipo_documento = app_llave('tipo_documento')::tipo_documento AND documento = app_llave('documento')))))",
        ),
    ),
    (
        "p_tareas_select",
        "tareas",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones', 'publico') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (servicio_id IN (SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta'))))",
            None,
        ),
    ),
    (
        "p_tareas_insert",
        "tareas",
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones', 'publico') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia()))",
        ),
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (familia_id IN (SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica()))) OR (app_rol() = 'familia' AND (familia_id = app_familia())) OR (app_rol() = 'publico' AND (servicio_id IN (SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta'))))",
        ),
    ),
    (
        "p_tokens_uso_unico_select",
        "tokens_uso_unico",
        ("app_rol() IN ('sistema', 'admin', 'comercial', 'publico')", None),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (token_hash = app_llave('token') OR usuario_id = app_llave('usuario')::uuid))",
            None,
        ),
    ),
    (
        "p_tokens_uso_unico_insert",
        "tokens_uso_unico",
        (None, "app_rol() IN ('sistema', 'admin', 'comercial', 'publico')"),
        (
            None,
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (token_hash = app_llave('token') OR usuario_id = app_llave('usuario')::uuid))",
        ),
    ),
    (
        "p_tokens_uso_unico_update",
        "tokens_uso_unico",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'publico')",
            "app_rol() IN ('sistema', 'admin', 'comercial', 'publico')",
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (token_hash = app_llave('token') OR usuario_id = app_llave('usuario')::uuid))",
            "app_rol() IN ('sistema', 'admin', 'comercial') OR (app_rol() = 'publico' AND (token_hash = app_llave('token') OR usuario_id = app_llave('usuario')::uuid))",
        ),
    ),
    (
        "p_usuarios_select",
        "usuarios",
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones', 'publico') OR (app_rol() = 'aliada' AND (id = app_usuario())) OR (app_rol() = 'familia' AND (id = app_usuario()))",
            None,
        ),
        (
            "app_rol() IN ('sistema', 'admin', 'comercial', 'medico', 'operaciones') OR (app_rol() = 'aliada' AND (id = app_usuario())) OR (app_rol() = 'familia' AND (id = app_usuario())) OR (app_rol() = 'publico' AND (id = app_llave('usuario')::uuid OR id = app_llave('autenticado')::uuid OR email = app_llave('ingreso_email') OR telefono = app_llave('ingreso_telefono') OR id IN (SELECT profesional_id FROM servicios WHERE id IN (SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta')))))",
            None,
        ),
    ),
    (
        "p_usuarios_update",
        "usuarios",
        (
            "app_rol() IN ('sistema', 'admin', 'publico')",
            "app_rol() IN ('sistema', 'admin', 'publico')",
        ),
        (
            "app_rol() IN ('sistema', 'admin') OR (app_rol() = 'publico' AND (id = app_llave('autenticado')::uuid))",
            "app_rol() IN ('sistema', 'admin') OR (app_rol() = 'publico' AND (id = app_llave('autenticado')::uuid))",
        ),
    ),
]

APP_LLAVE = """
CREATE FUNCTION app_llave(nombre text) RETURNS text LANGUAGE sql STABLE
AS $$ SELECT nullif(current_setting('app.llaves', true), '')::jsonb ->> nombre $$
"""

# El comercial activo con menos interesados en `etapas` (reparto por carga). La logica que
# decide que etapas cuentan sigue en Python (comercial.ABIERTAS).
COMERCIAL_CON_MENOS_CARGA = """
CREATE FUNCTION comercial_con_menos_carga(etapas text[]) RETURNS uuid
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, pg_temp AS $$
    SELECT u.id
    FROM usuarios u
    LEFT JOIN (
        SELECT responsable_id, count(*) AS n FROM interesados
        WHERE etapa::text = ANY (etapas) GROUP BY responsable_id
    ) carga ON carga.responsable_id = u.id
    WHERE u.rol = 'comercial' AND u.activo
    ORDER BY coalesce(carga.n, 0), u.created_at
    LIMIT 1
$$
"""


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
    op.execute(APP_LLAVE)
    op.execute(COMERCIAL_CON_MENOS_CARGA)
    op.execute("REVOKE ALL ON FUNCTION comercial_con_menos_carga(text[]) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION comercial_con_menos_carga(text[]) TO timu_app")
    for nombre, tabla, _, (usar, comprobar) in CAMBIOS:
        _alterar(nombre, tabla, usar, comprobar)


def downgrade() -> None:
    for nombre, tabla, (usar, comprobar), _ in CAMBIOS:
        _alterar(nombre, tabla, usar, comprobar)
    op.execute("DROP FUNCTION comercial_con_menos_carga(text[])")
    op.execute("DROP FUNCTION app_llave(text)")

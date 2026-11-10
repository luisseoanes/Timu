"""Permisos por perfil en la base: la matriz de RLS (fase 4 de docs/plan-persistencia.md).

Cada perfil (`app.rol` del contexto de la transaccion) solo ve y escribe las tablas y
operaciones que tiene aqui; la migracion 0023 genera de esta matriz una politica por tabla y
operacion. `sistema` (workers, scripts, webhooks validados por firma) tiene todas.

Origen: lo que hace cada ruta de la API, observado sentencia a sentencia con la suite
completa (TIMU_REGISTRO_ACCESOS en tests/conftest.py), repartido entre los perfiles que la
ruta admite (`require_roles`), mas las rutas que ninguna prueba recorre, revisadas a mano.
Toda escritura incluye la lectura: PostgreSQL exige que la fila nueva pase la politica de
lectura en un INSERT ... RETURNING o un UPDATE ... WHERE.

Una ruta nueva, o una ruta que pasa a tocar otra tabla, exige actualizar esta matriz y
escribir la migracion que cambia la politica. Si no, la propia prueba de esa ruta falla con
la base negando el acceso: es el aviso.

`familia`, `aliada` y `publico` ademas solo ven sus filas (CONDICIONES). Los catalogos
(CATALOGOS) los leen sin condicion.

`publico` es toda peticion sin sesion, y tambien el comienzo de cada peticion autenticada,
hasta que `get_current_user` reconoce al usuario. Solo ve las filas de quien la peticion
declaro con `acotar_publico` (app/core/database.py): la cuenta del email o el telefono con
que se ingresa, la sesion del token, la familia del documento del formulario, la encuesta
del enlace, el carnet del codigo. Sin llaves no ve nada. Crear una sesion o cambiar una
contrasena exige la llave `autenticado`, que solo se fija tras probar una credencial: un
error en una ruta que solo identifica (recuperar la contrasena, pedir un codigo) no puede
abrir una sesion ajena.

Limite de este modelo: el contexto lo fija la aplicacion con set_config, que cualquier
sentencia puede llamar. Protege de errores de la aplicacion (una consulta sin filtro, un id
equivocado), no de quien logre ejecutar SQL arbitrario con la conexion de la aplicacion.
"""

# perfil -> tabla -> operaciones (S select, I insert, U update, D delete, L bloquear).
# L: SELECT ... FOR UPDATE sin poder modificar. PostgreSQL exige la politica de UPDATE para
# bloquear una fila; con L el perfil pasa su USING pero no su WITH CHECK (agendar bloquea la
# franja para no sobrevender un cupo, y quien agenda no edita franjas).
#
# Efectos de cambiar el estado de un servicio: la misma peticion ejecuta las reglas de
# `servicio.transicion`, que la administracion configura en la base y que pueden crear
# tareas y notificar a la familia (familias, reglas, tareas, mensajes, plantillas_whatsapp,
# bajas_comunicaciones, eventos_salientes). Todo perfil que cambia ese estado los tiene,
# aunque hoy ninguna regla de su flujo los use: una regla nueva no puede romper el flujo.
PERMISOS: dict[str, dict[str, str]] = {
    "admin": {
        "adjuntos_clinicos": "S",
        "aplicaciones_pago": "SI",
        "arboles_conversacion": "SIU",
        "archivos": "SI",
        "auditoria": "S",
        "bajas_comunicaciones": "SIU",
        "beneficios_plan": "SIU",
        "bloqueos_agenda": "SI",
        "cambios_plan": "SI",
        "campanas": "SIU",
        "carnets_emitidos": "SI",
        "casos_prueba_ia": "SI",
        "ciudades": "SIU",
        "ciudades_plan": "SIU",
        "clinicas_aliadas": "SIU",
        "configuraciones_encuesta": "SIU",
        "consultas_ia": "S",
        "contactos_familia": "SIU",
        "contratos": "SIU",
        "convenios_aliadas": "SI",
        "conversaciones_comerciales": "SU",
        "conversaciones_whatsapp": "S",
        "cuotas": "SIU",
        "destinatarios_campana": "SU",
        "distancias_cache": "S",
        "documentos_familia": "SIU",
        "ejecuciones_campana": "SU",
        "encuestas": "S",
        "especies": "SIU",
        "esquemas_preventivos": "SIU",
        "eventos_pasarela": "SIU",
        "eventos_preventivos": "SIU",
        "eventos_salientes": "SI",
        "familias": "SIU",
        "franjas_agenda": "SIU",
        "historias_clinicas": "S",
        "intentos_cobro": "S",
        "interesados": "SIU",
        "mascotas": "SIU",
        "medios_pago_recurrente": "SIU",
        "mensajes": "SI",
        "pagos": "SIU",
        "paradas_ruta": "SIU",
        "pendientes": "SIU",
        "planes": "SIU",
        "planificaciones_ruta": "SI",
        "plantillas_consulta": "SI",
        "plantillas_whatsapp": "SIU",
        "prompts_ia": "SIU",
        "reglas": "SIU",
        "remisiones_aliadas": "SIU",
        "reportes_programados": "SIU",
        "respuestas_virtuales": "SIU",
        "rutas": "SU",
        "segmentos": "SI",
        "servicio_pasos": "SI",
        "servicios": "SIU",
        "sesiones": "SU",
        "solicitudes_afiliacion": "SIU",
        "solicitudes_virtuales": "SIU",
        "tareas": "SIU",
        "tarifas_periodicidad": "SIU",
        "tarifas_plan": "SIU",
        "tipos_servicio": "SIU",
        "tokens_uso_unico": "SIU",
        "usuarios": "SIU",
    },
    "aliada": {
        "bajas_comunicaciones": "S",
        "eventos_salientes": "SI",
        "familias": "S",
        "mascotas": "S",
        "mensajes": "SI",
        "plantillas_whatsapp": "S",
        "reglas": "S",
        "remisiones_aliadas": "SU",
        "servicio_pasos": "S",
        "servicios": "SU",
        "sesiones": "SU",
        "tareas": "SI",
        "tipos_servicio": "S",
        "usuarios": "S",
    },
    "comercial": {
        "adjuntos_clinicos": "S",
        "aplicaciones_pago": "SI",
        "arboles_conversacion": "S",
        "archivos": "SI",
        "auditoria": "S",
        "bajas_comunicaciones": "SI",
        "beneficios_plan": "S",
        "bloqueos_agenda": "S",
        "cambios_plan": "SI",
        "campanas": "SIU",
        "carnets_emitidos": "SI",
        "ciudades": "S",
        "ciudades_plan": "S",
        "clinicas_aliadas": "S",
        "contactos_familia": "SIU",
        "contratos": "SIU",
        "convenios_aliadas": "S",
        "conversaciones_comerciales": "SU",
        "conversaciones_whatsapp": "S",
        "cuotas": "SIU",
        "destinatarios_campana": "SU",
        "documentos_familia": "SIU",
        "ejecuciones_campana": "SU",
        "encuestas": "S",
        "especies": "S",
        "esquemas_preventivos": "S",
        "eventos_preventivos": "SIU",
        "eventos_salientes": "SI",
        "familias": "SIU",
        "franjas_agenda": "SL",
        "historias_clinicas": "S",
        "interesados": "SIU",
        "mascotas": "SIU",
        "medios_pago_recurrente": "SIU",
        "mensajes": "SI",
        "pagos": "SIU",
        "paradas_ruta": "S",
        "pendientes": "SIU",
        "planes": "S",
        "planificaciones_ruta": "S",
        "plantillas_consulta": "S",
        "plantillas_whatsapp": "SIU",
        "reglas": "S",
        "remisiones_aliadas": "SIU",
        "rutas": "S",
        "segmentos": "SI",
        "servicio_pasos": "SI",
        "servicios": "SIU",
        "sesiones": "SU",
        "solicitudes_afiliacion": "SIU",
        "solicitudes_virtuales": "SI",
        "tareas": "SIU",
        "tarifas_periodicidad": "S",
        "tarifas_plan": "S",
        "tipos_servicio": "S",
        "tokens_uso_unico": "SIU",
        "usuarios": "SI",
    },
    "familia": {
        "adjuntos_clinicos": "S",
        "aplicaciones_pago": "S",
        "archivos": "SI",
        "bajas_comunicaciones": "S",
        "beneficios_plan": "S",
        "bloqueos_agenda": "S",
        "carnets_emitidos": "SI",
        "ciudades": "S",
        "ciudades_plan": "S",
        "contactos_familia": "S",
        "contratos": "S",
        "cuotas": "S",
        "documentos_familia": "S",
        "especies": "S",
        "esquemas_preventivos": "S",
        "eventos_preventivos": "S",
        "eventos_salientes": "SI",
        "familias": "SU",
        "franjas_agenda": "SL",
        "historias_clinicas": "S",
        # Solo cambia la foto: la ruta del portal no toca otra columna.
        "mascotas": "SU",
        "mensajes": "SI",
        "pagos": "SI",
        "planes": "S",
        "plantillas_whatsapp": "S",
        "reglas": "S",
        "servicios": "SIU",
        "sesiones": "SU",
        "solicitudes_virtuales": "SI",
        "tareas": "SI",
        "tarifas_periodicidad": "S",
        "tarifas_plan": "S",
        "tipos_servicio": "S",
        "usuarios": "S",
    },
    "medico": {
        "adjuntos_clinicos": "SI",
        "archivos": "SI",
        "auditoria": "S",
        "bajas_comunicaciones": "SI",
        "beneficios_plan": "S",
        "bloqueos_agenda": "S",
        "cambios_plan": "SI",
        "campanas": "S",
        "carnets_emitidos": "SI",
        "ciudades": "S",
        "ciudades_plan": "S",
        "clinicas_aliadas": "S",
        "contactos_familia": "S",
        "contratos": "SU",
        "convenios_aliadas": "S",
        "conversaciones_whatsapp": "S",
        "cuotas": "S",
        "destinatarios_campana": "S",
        "distancias_cache": "S",
        "documentos_familia": "SIU",
        "ejecuciones_campana": "S",
        "encuestas": "S",
        "especies": "S",
        "esquemas_preventivos": "S",
        "eventos_preventivos": "SIU",
        "eventos_salientes": "SI",
        "familias": "SIU",
        "formulas": "SI",
        "franjas_agenda": "SL",
        "historias_clinicas": "SIU",
        "mascotas": "SIU",
        "mensajes": "SI",
        "pagos": "S",
        "paradas_ruta": "SU",
        "pendientes": "SIU",
        "planes": "S",
        "planificaciones_ruta": "S",
        "plantillas_consulta": "SI",
        "plantillas_whatsapp": "S",
        "reglas": "S",
        "remisiones_aliadas": "SIU",
        "respuestas_virtuales": "SI",
        "rutas": "SU",
        "segmentos": "S",
        "servicio_pasos": "SI",
        "servicios": "SIU",
        "sesiones": "SU",
        "solicitudes_afiliacion": "S",
        "solicitudes_virtuales": "SIU",
        "tareas": "SIU",
        "tarifas_periodicidad": "S",
        "tarifas_plan": "S",
        "tipos_servicio": "S",
        "usuarios": "S",
    },
    "operaciones": {
        "adjuntos_clinicos": "S",
        "archivos": "SI",
        "auditoria": "S",
        "bajas_comunicaciones": "SI",
        "beneficios_plan": "S",
        "bloqueos_agenda": "SI",
        "cambios_plan": "SI",
        "campanas": "S",
        "carnets_emitidos": "SI",
        "ciudades": "S",
        "ciudades_plan": "S",
        "clinicas_aliadas": "S",
        "contactos_familia": "SIU",
        "contratos": "SU",
        "convenios_aliadas": "S",
        "conversaciones_whatsapp": "S",
        "cuotas": "S",
        "destinatarios_campana": "S",
        "distancias_cache": "S",
        "documentos_familia": "SIU",
        "ejecuciones_campana": "S",
        "encuestas": "S",
        "especies": "S",
        "esquemas_preventivos": "S",
        "eventos_preventivos": "SIU",
        "eventos_salientes": "SI",
        "familias": "SIU",
        "franjas_agenda": "SIU",
        "historias_clinicas": "S",
        "mascotas": "SIU",
        "mensajes": "SI",
        "pagos": "S",
        "paradas_ruta": "SIU",
        "pendientes": "SIU",
        "planes": "S",
        "planificaciones_ruta": "SI",
        "plantillas_consulta": "S",
        "plantillas_whatsapp": "S",
        "reglas": "S",
        "remisiones_aliadas": "SIU",
        "rutas": "SU",
        "segmentos": "S",
        "servicio_pasos": "SI",
        "servicios": "SIU",
        "sesiones": "SU",
        "solicitudes_afiliacion": "S",
        "solicitudes_virtuales": "SI",
        "tareas": "SIU",
        "tarifas_periodicidad": "S",
        "tarifas_plan": "S",
        "tipos_servicio": "S",
        "usuarios": "S",
    },
    "publico": {
        "beneficios_plan": "S",
        "carnets_emitidos": "S",
        "ciudades": "S",
        "ciudades_plan": "S",
        "configuraciones_encuesta": "S",
        "contratos": "S",
        "encuestas": "SU",
        "especies": "S",
        "eventos_salientes": "SI",
        "familias": "SIU",
        "interesados": "SIU",
        "mascotas": "SI",
        "mensajes": "SI",
        "pagos": "SIU",
        "planes": "S",
        "plantillas_whatsapp": "S",
        "servicios": "S",
        "sesiones": "SIU",
        "solicitudes_afiliacion": "SIU",
        "tareas": "SI",
        "tarifas_periodicidad": "S",
        "tarifas_plan": "S",
        "tipos_servicio": "S",
        "tokens_uso_unico": "SIU",
        "usuarios": "SU",
    },
}

_F = "app_familia()"
_MASCOTAS = f"(SELECT id FROM mascotas WHERE familia_id = {_F})"
_HISTORIAS = f"(SELECT id FROM historias_clinicas WHERE familia_id = {_F} AND estado <> 'borrador')"
_REMISIONES = "(SELECT servicio_id FROM remisiones_aliadas WHERE clinica_id = app_clinica())"
# Familias con una remision de la clinica aliada: lo minimo para validarla y reportarla.
_FAMILIAS_REMITIDAS = "(SELECT familia_id FROM remisiones_aliadas WHERE clinica_id = app_clinica())"


def _contactos(familias: str) -> str:
    """Destinos (telefono o email) de esas familias, para consultar si pidieron la baja."""
    return (
        f"(SELECT telefono FROM familias WHERE id IN {familias}"
        f" UNION SELECT email FROM familias WHERE id IN {familias})"
    )


# Llaves de `publico` (LLAVES_PUBLICAS en app/core/database.py).
_SUJETO = "app_llave('usuario')::uuid"
_AUTENTICADO = "app_llave('autenticado')::uuid"
_FAMILIA_PUBLICA = (
    "(SELECT id FROM familias WHERE id = app_llave('familia')::uuid"
    " OR (tipo_documento = app_llave('tipo_documento')::tipo_documento"
    " AND documento = app_llave('documento')))"
)
_ATENCION_ENCUESTADA = "(SELECT servicio_id FROM encuestas WHERE token = app_llave('encuesta'))"
_SESIONES_PUBLICAS = (
    "id = app_llave('sesion')::uuid OR refresh_hash = app_llave('renovacion')"
    f" OR refresh_hash_anterior = app_llave('renovacion') OR usuario_id = {_AUTENTICADO}"
    " OR usuario_id = app_llave('revocar')::uuid"
)

# perfil -> tabla -> condicion de fila: una expresion para todas las operaciones, o una por
# letra ({"S": ..., "I": ...}; la que falte usa la de "S"). Una tabla de un perfil acotado
# que no este aqui ni en CATALOGOS no se puede generar: la migracion se niega, nada queda
# abierto por omision.
CONDICIONES: dict[str, dict[str, str | dict[str, str]]] = {
    "familia": {
        "familias": f"id = {_F} OR usuario_portal_id = app_usuario()",
        "mascotas": f"familia_id = {_F}",
        "contactos_familia": f"familia_id = {_F}",
        # Solo lo que el equipo marco visible y sigue vigente.
        "documentos_familia": f"familia_id = {_F} AND visible_familia AND activo",
        "contratos": f"familia_id = {_F}",
        "pagos": f"familia_id = {_F}",
        "servicios": f"familia_id = {_F}",
        "tareas": f"familia_id = {_F}",
        "solicitudes_virtuales": f"familia_id = {_F}",
        # La familia solo ve lo firmado; los borradores son del equipo medico.
        "historias_clinicas": f"familia_id = {_F} AND estado <> 'borrador'",
        "adjuntos_clinicos": f"historia_id IN {_HISTORIAS}",
        "eventos_preventivos": f"mascota_id IN {_MASCOTAS}",
        "carnets_emitidos": f"mascota_id IN {_MASCOTAS}",
        "cuotas": f"contrato_id IN (SELECT id FROM contratos WHERE familia_id = {_F})",
        "aplicaciones_pago": f"pago_id IN (SELECT id FROM pagos WHERE familia_id = {_F})",
        "archivos": (
            "subido_por_id = app_usuario()"
            f" OR id IN (SELECT foto_archivo_id FROM mascotas WHERE familia_id = {_F})"
            f" OR id IN (SELECT documento_archivo_id FROM contratos WHERE familia_id = {_F})"
            " OR id IN (SELECT archivo_id FROM adjuntos_clinicos"
            f" WHERE historia_id IN {_HISTORIAS})"
            f" OR id IN (SELECT archivo_id FROM carnets_emitidos WHERE mascota_id IN {_MASCOTAS})"
            " OR id IN (SELECT archivo_id FROM documentos_familia"
            f" WHERE familia_id = {_F} AND visible_familia AND activo)"
        ),
        "mensajes": f"familia_id = {_F}",
        "bajas_comunicaciones": f"destino IN {_contactos(f'({_F})')}",
        "sesiones": "usuario_id = app_usuario()",
        "usuarios": "id = app_usuario()",
    },
    # El equipo solo ve y cierra sus propias sesiones; la administracion, las de todos.
    "comercial": {"sesiones": "usuario_id = app_usuario()"},
    "operaciones": {"sesiones": "usuario_id = app_usuario()"},
    "medico": {"sesiones": "usuario_id = app_usuario()"},
    "aliada": {
        "remisiones_aliadas": "clinica_id = app_clinica()",
        "servicios": f"id IN {_REMISIONES}",
        "servicio_pasos": f"servicio_id IN {_REMISIONES}",
        "familias": f"id IN {_FAMILIAS_REMITIDAS}",
        "mascotas": f"familia_id IN {_FAMILIAS_REMITIDAS}",
        "tareas": f"familia_id IN {_FAMILIAS_REMITIDAS}",
        "mensajes": f"familia_id IN {_FAMILIAS_REMITIDAS}",
        "bajas_comunicaciones": f"destino IN {_contactos(_FAMILIAS_REMITIDAS)}",
        "sesiones": "usuario_id = app_usuario()",
        "usuarios": "id = app_usuario()",
    },
    "publico": {
        # Ingreso, recuperacion y codigo buscan la cuenta por email o telefono; la encuesta
        # nombra al profesional en la tarea que abre. Cambiar la contrasena exige haber
        # probado el enlace.
        "usuarios": {
            "S": (
                f"id = {_SUJETO} OR id = {_AUTENTICADO}"
                " OR email = app_llave('ingreso_email') OR telefono = app_llave('ingreso_telefono')"
                " OR id IN (SELECT profesional_id FROM servicios"
                f" WHERE id IN {_ATENCION_ENCUESTADA})"
            ),
            "U": f"id = {_AUTENTICADO}",
        },
        # La sesion del JWT, la del token de renovacion y las de la cuenta autenticada o cuyo
        # token se reuso (para revocarlas). Crear una exige credencial.
        "sesiones": {"S": _SESIONES_PUBLICAS, "I": f"usuario_id = {_AUTENTICADO}"},
        "tokens_uso_unico": f"token_hash = app_llave('token') OR usuario_id = {_SUJETO}",
        # El enlace o el codigo solo va a un contacto de la cuenta identificada.
        "mensajes": (
            f"destino IN (SELECT email FROM usuarios WHERE id = {_SUJETO}"
            f" UNION SELECT telefono FROM usuarios WHERE id = {_SUJETO})"
        ),
        # Formularios: la familia del documento y lo suyo.
        "familias": (
            "id = app_llave('familia')::uuid"
            " OR (tipo_documento = app_llave('tipo_documento')::tipo_documento"
            " AND documento = app_llave('documento'))"
        ),
        "mascotas": (
            f"familia_id IN {_FAMILIA_PUBLICA}"
            f" OR id IN (SELECT mascota_id FROM servicios WHERE id IN {_ATENCION_ENCUESTADA})"
        ),
        "contratos": f"familia_id IN {_FAMILIA_PUBLICA}",
        "pagos": f"familia_id IN {_FAMILIA_PUBLICA}",
        "solicitudes_afiliacion": f"familia_id IN {_FAMILIA_PUBLICA}",
        "interesados": (
            "telefono = app_llave('contacto_telefono') OR email = app_llave('contacto_email')"
            f" OR familia_id IN {_FAMILIA_PUBLICA}"
        ),
        # Enlace de encuesta: la encuesta, su atencion y la tarea que abre una mala nota.
        "encuestas": "token = app_llave('encuesta')",
        "servicios": f"id IN {_ATENCION_ENCUESTADA}",
        "tareas": f"servicio_id IN {_ATENCION_ENCUESTADA}",
        "carnets_emitidos": "codigo = app_llave('carnet')",
    },
}

# Lo que cualquier perfil que lo use lee sin condicion de fila: configuracion, no datos de
# nadie. `eventos_salientes` es el outbox: un INSERT ... RETURNING tiene que poder leerse.
CATALOGOS = frozenset(
    {
        "beneficios_plan",
        "bloqueos_agenda",
        "ciudades",
        "ciudades_plan",
        "configuraciones_encuesta",
        "especies",
        "esquemas_preventivos",
        "eventos_salientes",
        "franjas_agenda",
        "planes",
        "plantillas_whatsapp",
        "reglas",
        "tarifas_periodicidad",
        "tarifas_plan",
        "tipos_servicio",
    }
)


# Perfiles cuyas filas se acotan siempre: toda tabla suya lleva condicion o es un catalogo.
_ACOTADOS = ("familia", "aliada", "publico")
_COMANDOS = {"S": "SELECT", "I": "INSERT", "U": "UPDATE", "D": "DELETE"}


def _condicion(rol: str, tabla: str, letra: str) -> str | None:
    condicion = CONDICIONES.get(rol, {}).get(tabla)
    if isinstance(condicion, dict):
        return condicion.get(letra, condicion["S"])
    return condicion


def _expresion(tabla: str, letras: str, operacion: str) -> str:
    """Quien tiene alguna de `letras` sobre `tabla`: `sistema` siempre; el resto, segun la
    matriz, con la condicion de fila de `operacion`."""
    libres = ["sistema"]
    acotados: list[str] = []
    for rol in sorted(PERMISOS):
        if not set(letras) & set(PERMISOS[rol].get(tabla, "")):
            continue
        condicion = _condicion(rol, tabla, operacion)
        if condicion is not None:
            acotados.append(f"(app_rol() = '{rol}' AND ({condicion}))")
        elif rol in _ACOTADOS and tabla not in CATALOGOS:
            raise ValueError(f"{rol} usa {tabla} sin condicion de fila ni ser catalogo")
        else:
            libres.append(rol)
    lista = ", ".join(f"'{r}'" for r in libres)
    return " OR ".join([f"app_rol() IN ({lista})", *acotados])


def politicas(tablas: list[str]) -> list[tuple[str, str, str, str, str | None, str | None]]:
    """(nombre, tabla, comando, roles, USING, WITH CHECK) de cada politica, para todas las
    tablas: la migracion las crea y `test_persistencia` las compara con la base."""
    salida = []
    for tabla in sorted(tablas):
        for letra, comando in _COMANDOS.items():
            # El USING de UPDATE tambien admite a quien solo bloquea (L); el WITH CHECK no.
            usar = (
                None if letra == "I" else _expresion(tabla, "UL" if letra == "U" else letra, letra)
            )
            comprobar = _expresion(tabla, letra, letra) if letra in ("I", "U") else None
            salida.append(
                (f"p_{tabla}_{comando.lower()}", tabla, comando, "timu_app", usar, comprobar)
            )
    return salida


def descripcion(usar: str | None, comprobar: str | None) -> str:
    """Texto del comentario de una politica: lo que la migracion escribio y el guarda compara
    (PostgreSQL guarda las expresiones normalizadas, no como se escribieron)."""
    return f"USING ({usar}) WITH CHECK ({comprobar})"

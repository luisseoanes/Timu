"""enums nativos para los conjuntos cerrados

Fase 2a de docs/plan-persistencia.md. Cada columna que guarda un conjunto cerrado definido
por el codigo (estados, roles, canales, prioridades...) pasa de varchar libre a un enum de
PostgreSQL: la base rechaza cualquier valor fuera del conjunto, lo escriba quien lo escriba.
Los valores estan escritos aqui y no importados de la aplicacion: la migracion tiene que
describir siempre el mismo cambio. Si un dato existente no esta en su enum, la migracion
falla en vez de dejarlo pasar.

Siete de estas columnas conservaban un DEFAULT de servidor que solo sirvio para rellenar las
filas existentes al anadir la columna (0004, 0008, 0005, 0009...) y que el modelo no tiene.
Se eliminan: el de historias_clinicas.estado era 'firmada', asi que un INSERT por SQL sin
estado creaba una historia clinica ya firmada. El downgrade los repone.

Revision ID: 0015
Revises: 0014
Create Date: 2026-11-04 20:00:00
"""

from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

TIPOS: dict[str, list[str]] = {
    "accion": ["crear", "editar", "cambio_estado", "eliminar"],
    "area_tarea": ["comercial", "operaciones", "medico", "cartera", "servicio_cliente"],
    "canal_comunicacion": ["whatsapp", "email"],
    "canal_respuesta_encuesta": ["enlace", "whatsapp"],
    "canal_virtual": ["portal", "whatsapp", "panel"],
    "categoria_plantilla": ["utility", "marketing", "authentication"],
    "direccion_mensaje": ["entrante", "saliente"],
    "estado_afiliacion": ["prospecto", "activa", "en_mora", "congelada", "cancelada"],
    "estado_aprobacion_plantilla": ["borrador", "enviada", "aprobada", "rechazada", "pausada"],
    "estado_campana": ["borrador", "programada", "en_envio", "finalizada", "cancelada"],
    "estado_consulta_ia": ["ok", "rechazo", "error", "presupuesto_agotado", "desactivada"],
    "estado_conversacion": ["automatica", "con_asesor"],
    "estado_cuota": ["pendiente", "parcial", "pagada", "anulada"],
    "estado_destinatario": ["pendiente", "encolado", "excluido"],
    "estado_ejecucion_campana": ["en_envio", "terminada", "cancelada"],
    "estado_encuesta": ["pendiente", "enviada", "respondida", "vencida", "omitida"],
    "estado_evento_pasarela": ["recibido", "procesado", "ignorado", "error"],
    "estado_evento_preventivo": ["programado", "aplicado", "cancelado"],
    "estado_historia": ["borrador", "firmada", "corregida"],
    "estado_mensaje": [
        "encolado",
        "enviado",
        "entregado",
        "leido",
        "fallido",
        "recibido",
        "omitido",
    ],
    "estado_pago": ["pendiente", "aprobado", "rechazado", "reversado", "anulado"],
    "estado_parada": ["pendiente", "en_camino", "en_sitio", "completada", "omitida"],
    "estado_pendiente": [
        "pendiente_autorizacion",
        "autorizado",
        "en_gestion",
        "resuelto",
        "rechazado",
    ],
    "estado_planificacion": ["pendiente", "lista", "fallida"],
    "estado_prompt": ["borrador", "activo", "retirado"],
    "estado_remision": ["emitida", "utilizada", "anulada"],
    "estado_respuesta_virtual": ["borrador", "aprobada", "retirada"],
    "estado_ruta": ["planificada", "en_curso", "finalizada", "cancelada"],
    "estado_servicio": [
        "solicitado",
        "agendado",
        "en_ruta",
        "en_atencion",
        "completado",
        "pendiente_autorizacion",
        "reprogramado",
        "cancelado",
    ],
    "estado_solicitud": ["pendiente_pago", "completada", "cancelada", "error"],
    "estado_solicitud_virtual": ["en_cola", "en_atencion", "respondida", "cerrada"],
    "estado_tarea": ["abierta", "en_progreso", "cerrada"],
    "etapa_interesado": ["nuevo", "contactado", "cotizado", "en_afiliacion", "afiliado", "perdido"],
    "evento_regla": [
        "cartera.estado",
        "cartera.alerta",
        "cartera.renovacion",
        "plan.cambio",
        "plan.mascota",
        "plan.recomendacion",
        "servicio.transicion",
        "servicio.elegibilidad",
    ],
    "geo_precision": ["direccion", "ciudad", "manual"],
    "medio_aceptacion": ["formulario_web", "presencial", "whatsapp", "llamada"],
    "medio_autorizacion": [
        "whatsapp",
        "telefono",
        "llamada",
        "presencial",
        "portal",
        "formulario",
        "correo",
    ],
    "modo_cambio_plan": ["diario", "sin_cargo", "proximo_ciclo", "proxima_cuota"],
    "origen_solicitud_afiliacion": ["formulario", "asistida"],
    "periodicidad_reporte": ["diaria", "semanal", "mensual"],
    "periodo_cupo": ["mensual", "anual"],
    "prioridad": ["alta", "media", "baja"],
    "proposito_archivo": ["foto_mascota", "adjunto_clinico", "contrato", "formula", "carnet"],
    "proposito_token": ["recuperacion", "activacion", "codigo_ingreso"],
    "proveedor_pago": ["manual", "wompi"],
    "recurrencia_campana": ["ninguna", "diaria", "semanal", "mensual"],
    "rol": ["admin", "comercial", "operaciones", "medico", "familia", "aliada"],
    "sexo_mascota": ["macho", "hembra"],
    "tipo_cambio_plan": ["cambio_plan", "mascota_alta", "mascota_baja"],
    "tipo_documento": ["CC", "CE", "TI", "PA", "PPT", "NIT"],
    "tipo_encuesta": ["satisfaccion", "seguimiento"],
    "tipo_historia": ["presencial", "domiciliaria", "virtual"],
    "tipo_preventivo": ["vacuna", "desparasitacion_interna", "desparasitacion_externa"],
    "tipo_servicio": ["domiciliario", "preventivo", "clinico", "virtual", "aliada"],
}

# (tabla, columna, enum, longitud del varchar original)
COLUMNAS: list[tuple[str, str, str, int]] = [
    ("usuarios", "rol", "rol", 32),
    ("familias", "estado", "estado_afiliacion", 32),
    ("contratos", "estado", "estado_afiliacion", 32),
    ("servicios", "estado", "estado_servicio", 32),
    ("servicios", "tipo", "tipo_servicio", 24),
    ("tipos_servicio", "modalidad", "tipo_servicio", 24),
    ("franjas_agenda", "modalidad", "tipo_servicio", 24),
    ("bloqueos_agenda", "modalidad", "tipo_servicio", 24),
    ("pagos", "estado", "estado_pago", 24),
    ("intentos_cobro", "estado", "estado_pago", 16),
    ("pagos", "proveedor", "proveedor_pago", 32),
    ("eventos_pasarela", "proveedor", "proveedor_pago", 32),
    ("medios_pago_recurrente", "proveedor", "proveedor_pago", 32),
    ("eventos_pasarela", "estado", "estado_evento_pasarela", 16),
    ("cuotas", "estado", "estado_cuota", 16),
    ("contratos", "medio_aceptacion", "medio_aceptacion", 24),
    ("solicitudes_afiliacion", "estado", "estado_solicitud", 24),
    ("solicitudes_afiliacion", "origen", "origen_solicitud_afiliacion", 24),
    ("familias", "tipo_documento", "tipo_documento", 8),
    ("mascotas", "sexo", "sexo_mascota", 16),
    ("familias", "geo_precision", "geo_precision", 16),
    ("auditoria", "accion", "accion", 24),
    ("archivos", "proposito", "proposito_archivo", 40),
    ("tokens_uso_unico", "proposito", "proposito_token", 24),
    ("mensajes", "canal", "canal_comunicacion", 24),
    ("bajas_comunicaciones", "canal", "canal_comunicacion", 24),
    ("campanas", "canal", "canal_comunicacion", 24),
    ("mensajes", "direccion", "direccion_mensaje", 12),
    ("mensajes", "estado", "estado_mensaje", 24),
    ("plantillas_whatsapp", "categoria", "categoria_plantilla", 24),
    ("plantillas_whatsapp", "estado_aprobacion", "estado_aprobacion_plantilla", 24),
    ("campanas", "estado", "estado_campana", 24),
    ("campanas", "recurrencia", "recurrencia_campana", 16),
    ("ejecuciones_campana", "estado", "estado_ejecucion_campana", 16),
    ("destinatarios_campana", "estado", "estado_destinatario", 16),
    ("reportes_programados", "periodicidad", "periodicidad_reporte", 12),
    ("encuestas", "tipo", "tipo_encuesta", 16),
    ("encuestas", "canal_respuesta", "canal_respuesta_encuesta", 16),
    ("encuestas", "estado", "estado_encuesta", 24),
    ("historias_clinicas", "tipo", "tipo_historia", 16),
    ("historias_clinicas", "estado", "estado_historia", 16),
    ("respuestas_virtuales", "estado", "estado_respuesta_virtual", 16),
    ("solicitudes_virtuales", "canal", "canal_virtual", 16),
    ("solicitudes_virtuales", "estado", "estado_solicitud_virtual", 16),
    ("solicitudes_virtuales", "prioridad", "prioridad", 8),
    ("tareas", "prioridad", "prioridad", 8),
    ("interesados", "etapa", "etapa_interesado", 16),
    ("conversaciones_comerciales", "estado", "estado_conversacion", 16),
    ("prompts_ia", "estado", "estado_prompt", 12),
    ("consultas_ia", "estado", "estado_consulta_ia", 24),
    ("beneficios_plan", "periodo_cupo", "periodo_cupo", 12),
    ("cambios_plan", "tipo", "tipo_cambio_plan", 24),
    ("cambios_plan", "modo", "modo_cambio_plan", 24),
    ("esquemas_preventivos", "tipo", "tipo_preventivo", 40),
    ("eventos_preventivos", "tipo", "tipo_preventivo", 60),
    ("eventos_preventivos", "estado", "estado_evento_preventivo", 16),
    ("eventos_preventivos", "medio_autorizacion", "medio_autorizacion", 24),
    ("pendientes", "medio_autorizacion", "medio_autorizacion", 24),
    ("pendientes", "estado", "estado_pendiente", 24),
    ("remisiones_aliadas", "estado", "estado_remision", 24),
    ("rutas", "estado", "estado_ruta", 24),
    ("paradas_ruta", "estado", "estado_parada", 16),
    ("planificaciones_ruta", "estado", "estado_planificacion", 16),
    ("tareas", "area", "area_tarea", 24),
    ("tareas", "estado", "estado_tarea", 16),
    ("reglas", "evento", "evento_regla", 60),
]


# DEFAULT de servidor que habia antes de esta migracion, para el downgrade.
DEFAULTS_ANTERIORES: dict[tuple[str, str], str] = {
    ("campanas", "recurrencia"): "ninguna",
    ("encuestas", "tipo"): "satisfaccion",
    ("eventos_preventivos", "estado"): "programado",
    ("familias", "tipo_documento"): "CC",
    ("historias_clinicas", "estado"): "firmada",
    ("historias_clinicas", "tipo"): "presencial",
    ("paradas_ruta", "estado"): "pendiente",
}


def upgrade() -> None:
    for nombre, valores in TIPOS.items():
        etiquetas = ", ".join(f"'{v}'" for v in valores)
        op.execute(f"CREATE TYPE {nombre} AS ENUM ({etiquetas})")
    for tabla, columna in DEFAULTS_ANTERIORES:
        op.execute(f"ALTER TABLE {tabla} ALTER COLUMN {columna} DROP DEFAULT")
    for tabla, columna, nombre, _ in COLUMNAS:
        op.execute(
            f"ALTER TABLE {tabla} ALTER COLUMN {columna} TYPE {nombre}"
            f" USING {columna}::text::{nombre}"
        )


def downgrade() -> None:
    for tabla, columna, _, longitud in COLUMNAS:
        op.execute(
            f"ALTER TABLE {tabla} ALTER COLUMN {columna} TYPE varchar({longitud})"
            f" USING {columna}::text"
        )
    for (tabla, columna), valor in DEFAULTS_ANTERIORES.items():
        op.execute(f"ALTER TABLE {tabla} ALTER COLUMN {columna} SET DEFAULT '{valor}'")
    for nombre in TIPOS:
        op.execute(f"DROP TYPE {nombre}")

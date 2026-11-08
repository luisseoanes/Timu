"""restricciones check: invariantes de cada fila

Fase 2c de docs/plan-persistencia.md. Lo que el codigo garantizaba en Python y la base no
(rangos, formatos, importes no negativos, campos que exige un estado, el CHECK perdido de
usuarios) lo garantiza ahora la base. Cada expresion se valido contra los datos existentes
antes de escribirse; si un dato la viola, la migracion falla en vez de dejarlo pasar.
Las expresiones estan escritas aqui: el modelo puede cambiar, la migracion no.

Revision ID: 0017
Revises: 0016
Create Date: 2026-11-04 21:00:00
"""

from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None

# (tabla, restriccion, expresion)
CHECKS: list[tuple[str, str, str]] = [
    ("aplicaciones_pago", "ck_aplicaciones_pago_valor_positivo", "valor > 0"),
    ("arboles_conversacion", "ck_arboles_conversacion_version_minimo", "version >= 1"),
    ("archivos", "ck_archivos_sha256_formato", "sha256 ~ '^[0-9a-f]{64}$'"),
    ("archivos", "ck_archivos_tamano_no_negativo", "tamano_bytes >= 0"),
    ("beneficios_plan", "ck_beneficios_plan_cobertura_rango", "cobertura_pct BETWEEN 0 AND 100"),
    ("beneficios_plan", "ck_beneficios_plan_copago_no_negativo", "copago >= 0"),
    ("beneficios_plan", "ck_beneficios_plan_cupo_no_negativo", "cupo IS NULL OR cupo >= 0"),
    (
        "cambios_plan",
        "ck_cambios_plan_valores_no_negativos",
        "valor_anterior >= 0 AND valor_nuevo >= 0",
    ),
    ("carnets_emitidos", "ck_carnets_emitidos_sha256_formato", "sha256 ~ '^[0-9a-f]{64}$'"),
    ("ciudades", "ck_ciudades_codigo_no_vacio", "btrim(codigo) <> ''"),
    ("ciudades", "ck_ciudades_latitud_rango", "latitud IS NULL OR latitud BETWEEN -90 AND 90"),
    ("ciudades", "ck_ciudades_longitud_rango", "longitud IS NULL OR longitud BETWEEN -180 AND 180"),
    ("ciudades", "ck_ciudades_nombre_no_vacio", "btrim(nombre) <> ''"),
    (
        "configuraciones_encuesta",
        "ck_configuraciones_encuesta_demora_no_negativa",
        "demora_horas >= 0",
    ),
    (
        "configuraciones_encuesta",
        "ck_configuraciones_encuesta_seguimiento_rango",
        "seguimiento_dias IS NULL OR seguimiento_dias BETWEEN 1 AND 180",
    ),
    (
        "configuraciones_encuesta",
        "ck_configuraciones_encuesta_umbral_rango",
        "umbral_alerta BETWEEN 1 AND 5",
    ),
    (
        "consultas_ia",
        "ck_consultas_ia_metricas_no_negativas",
        "tokens_entrada >= 0 AND tokens_salida >= 0 AND tokens_cache_lectura >= 0 AND "
        "tokens_cache_escritura >= 0 AND costo_usd >= 0 AND (latencia_ms IS NULL OR latencia_ms >= "
        "0)",
    ),
    ("consumo_mapas", "ck_consumo_mapas_elementos_no_negativos", "elementos >= 0"),
    ("contratos", "ck_contratos_dia_corte_rango", "dia_corte BETWEEN 1 AND 28"),
    ("contratos", "ck_contratos_fin_posterior", "fecha_fin IS NULL OR fecha_fin >= fecha_inicio"),
    ("contratos", "ck_contratos_renovacion_posterior", "fecha_renovacion > fecha_inicio"),
    (
        "contratos",
        "ck_contratos_valores_no_negativos",
        "valor_mensual >= 0 AND valor_plan >= 0 AND valor_adicional_mascota >= 0 AND saldo_a_favor "
        ">= 0 AND mascotas_adicionales >= 0",
    ),
    (
        "convenios_aliadas",
        "ck_convenios_aliadas_cobertura_rango",
        "cobertura_pct BETWEEN 0 AND 100",
    ),
    (
        "convenios_aliadas",
        "ck_convenios_aliadas_tarifa_no_negativa",
        "tarifa IS NULL OR tarifa >= 0",
    ),
    (
        "convenios_aliadas",
        "ck_convenios_aliadas_tope_no_negativo",
        "tope_cubierto IS NULL OR tope_cubierto >= 0",
    ),
    (
        "convenios_aliadas",
        "ck_convenios_aliadas_vigencia",
        "vigente_hasta IS NULL OR vigente_hasta >= vigente_desde",
    ),
    (
        "conversaciones_comerciales",
        "ck_conversaciones_comerciales_telefono_formato",
        "telefono ~ '^\\+[1-9][0-9]{7,14}$'",
    ),
    (
        "conversaciones_whatsapp",
        "ck_conversaciones_whatsapp_telefono_formato",
        "telefono ~ '^\\+[1-9][0-9]{7,14}$'",
    ),
    ("cuotas", "ck_cuotas_pagada_cubre", "estado <> 'pagada' OR valor_pagado >= valor"),
    (
        "cuotas",
        "ck_cuotas_parcial_entre",
        "estado <> 'parcial' OR (valor_pagado > 0 AND valor_pagado < valor)",
    ),
    ("cuotas", "ck_cuotas_periodo_formato", "periodo ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'"),
    ("cuotas", "ck_cuotas_tipo_formato", "tipo ~ '^(mensual|ajuste[0-9]*)$'"),
    (
        "cuotas",
        "ck_cuotas_valores_no_negativos",
        "valor >= 0 AND valor_pagado >= 0 AND dias_mora >= 0",
    ),
    (
        "destinatarios_campana",
        "ck_destinatarios_campana_excluido_con_motivo",
        "estado <> 'excluido' OR motivo_exclusion IS NOT NULL",
    ),
    (
        "destinatarios_campana",
        "ck_destinatarios_campana_telefono_formato",
        "telefono ~ '^\\+[1-9][0-9]{7,14}$'",
    ),
    (
        "distancias_cache",
        "ck_distancias_cache_valores_no_negativos",
        "metros >= 0 AND segundos >= 0",
    ),
    (
        "ejecuciones_campana",
        "ck_ejecuciones_campana_conteos",
        "audiencia >= 0 AND excluidos >= 0 AND excluidos <= audiencia",
    ),
    (
        "ejecuciones_campana",
        "ck_ejecuciones_campana_horario",
        "terminada_en IS NULL OR terminada_en >= iniciada_en",
    ),
    (
        "encuestas",
        "ck_encuestas_enviada_con_fecha",
        "estado NOT IN ('enviada', 'respondida') OR enviada_en IS NOT NULL",
    ),
    ("encuestas", "ck_encuestas_puntaje_rango", "puntaje IS NULL OR puntaje BETWEEN 1 AND 5"),
    (
        "encuestas",
        "ck_encuestas_respondida_completa",
        "estado <> 'respondida' OR (respondida_en IS NOT NULL AND puntaje IS NOT NULL)",
    ),
    ("esquemas_preventivos", "ck_esquemas_preventivos_dosis_minimo", "dosis_iniciales >= 1"),
    (
        "esquemas_preventivos",
        "ck_esquemas_preventivos_edad_no_negativa",
        "edad_minima_semanas >= 0",
    ),
    (
        "esquemas_preventivos",
        "ck_esquemas_preventivos_intervalos_no_negativos",
        "(intervalo_inicial_dias IS NULL OR intervalo_inicial_dias >= 0) AND "
        "(intervalo_refuerzo_dias IS NULL OR intervalo_refuerzo_dias >= 0)",
    ),
    (
        "esquemas_preventivos",
        "ck_esquemas_preventivos_serie_con_intervalo",
        "dosis_iniciales = 1 OR intervalo_inicial_dias > 0",
    ),
    ("eventos_pasarela", "ck_eventos_pasarela_intentos_no_negativos", "intentos >= 0"),
    (
        "eventos_preventivos",
        "ck_eventos_preventivos_aplicado_con_fecha",
        "estado <> 'aplicado' OR fecha_aplicacion IS NOT NULL",
    ),
    ("eventos_preventivos", "ck_eventos_preventivos_dosis_minimo", "dosis_numero >= 1"),
    ("eventos_salientes", "ck_eventos_salientes_intentos_no_negativos", "intentos >= 0"),
    ("familias", "ck_familias_baja_cancelada", "dada_de_baja_en IS NULL OR estado = 'cancelada'"),
    ("familias", "ck_familias_coordenadas_juntas", "(latitud IS NULL) = (longitud IS NULL)"),
    ("familias", "ck_familias_documento_formato", "documento ~ '^[0-9A-Z]+$'"),
    (
        "familias",
        "ck_familias_email_formato",
        "email IS NULL OR email ~ '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$'",
    ),
    ("familias", "ck_familias_latitud_rango", "latitud IS NULL OR latitud BETWEEN -90 AND 90"),
    ("familias", "ck_familias_longitud_rango", "longitud IS NULL OR longitud BETWEEN -180 AND 180"),
    ("familias", "ck_familias_telefono_formato", "telefono ~ '^\\+[1-9][0-9]{7,14}$'"),
    ("familias", "ck_familias_titular_no_vacio", "btrim(titular_nombre) <> ''"),
    ("franjas_agenda", "ck_franjas_agenda_capacidad_positiva", "capacidad > 0"),
    ("franjas_agenda", "ck_franjas_agenda_dia_semana_rango", "dia_semana BETWEEN 0 AND 6"),
    ("franjas_agenda", "ck_franjas_agenda_horario", "hora_fin > hora_inicio"),
    (
        "historias_clinicas",
        "ck_historias_clinicas_firmada_completa",
        "estado = 'borrador' OR (firmada_en IS NOT NULL AND firmada_por_id IS NOT NULL AND "
        "diagnostico IS NOT NULL)",
    ),
    ("historias_clinicas", "ck_historias_clinicas_version_minimo", "version >= 1"),
    ("intentos_cobro", "ck_intentos_cobro_numero_minimo", "numero >= 1"),
    (
        "interesados",
        "ck_interesados_email_formato",
        "email IS NULL OR email ~ '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$'",
    ),
    (
        "interesados",
        "ck_interesados_telefono_formato",
        "telefono IS NULL OR telefono ~ '^\\+[1-9][0-9]{7,14}$'",
    ),
    ("mascotas", "ck_mascotas_baja_coherente", "activa = (dada_de_baja_en IS NULL)"),
    ("mascotas", "ck_mascotas_nombre_no_vacio", "btrim(nombre) <> ''"),
    ("mascotas", "ck_mascotas_peso_positivo", "peso_kg IS NULL OR peso_kg > 0"),
    (
        "medios_pago_recurrente",
        "ck_medios_pago_recurrente_ultimos4_formato",
        "ultimos4 IS NULL OR ultimos4 ~ '^[0-9]{4}$'",
    ),
    ("mensajes", "ck_mensajes_intentos_no_negativos", "intentos >= 0"),
    ("pagos", "ck_pagos_valor_positivo", "valor > 0"),
    (
        "paradas_ruta",
        "ck_paradas_ruta_completada_con_salida",
        "estado <> 'completada' OR salida_en IS NOT NULL",
    ),
    (
        "paradas_ruta",
        "ck_paradas_ruta_horario",
        "salida_en IS NULL OR llegada_en IS NULL OR salida_en >= llegada_en",
    ),
    (
        "paradas_ruta",
        "ck_paradas_ruta_latitud_rango",
        "latitud IS NULL OR latitud BETWEEN -90 AND 90",
    ),
    (
        "paradas_ruta",
        "ck_paradas_ruta_longitud_rango",
        "longitud IS NULL OR longitud BETWEEN -180 AND 180",
    ),
    (
        "paradas_ruta",
        "ck_paradas_ruta_omitida_con_motivo",
        "estado <> 'omitida' OR motivo_omision IS NOT NULL",
    ),
    ("paradas_ruta", "ck_paradas_ruta_orden_minimo", "orden >= 1"),
    ("planes", "ck_planes_codigo_no_vacio", "btrim(codigo) <> ''"),
    ("planes", "ck_planes_cupos_minimo", "cupos_mascotas >= 1"),
    ("planes", "ck_planes_nombre_no_vacio", "btrim(nombre) <> ''"),
    ("planes", "ck_planes_valor_no_negativo", "valor_mensual >= 0"),
    (
        "plantillas_whatsapp",
        "ck_plantillas_whatsapp_activa_aprobada",
        "NOT activa OR estado_aprobacion = 'aprobada'",
    ),
    (
        "plantillas_whatsapp",
        "ck_plantillas_whatsapp_idioma_formato",
        "idioma ~ '^[a-z]{2}(_[A-Z]{2})?$'",
    ),
    ("plantillas_whatsapp", "ck_plantillas_whatsapp_version_minimo", "version >= 1"),
    (
        "prompts_ia",
        "ck_prompts_ia_activo_evaluado",
        "estado <> 'activo' OR evaluado_en IS NOT NULL",
    ),
    ("prompts_ia", "ck_prompts_ia_version_minimo", "version >= 1"),
    ("reglas", "ck_reglas_prioridad_no_negativa", "prioridad >= 0"),
    (
        "reglas",
        "ck_reglas_vigencia",
        "vigente_hasta IS NULL OR vigente_desde IS NULL OR vigente_hasta >= vigente_desde",
    ),
    (
        "remisiones_aliadas",
        "ck_remisiones_aliadas_anulada_con_motivo",
        "estado <> 'anulada' OR motivo_anulacion IS NOT NULL",
    ),
    (
        "remisiones_aliadas",
        "ck_remisiones_aliadas_cobertura_rango",
        "cobertura_pct BETWEEN 0 AND 100",
    ),
    (
        "remisiones_aliadas",
        "ck_remisiones_aliadas_utilizada_reportada",
        "estado <> 'utilizada' OR (fecha_atencion IS NOT NULL AND reportada_en IS NOT NULL)",
    ),
    (
        "remisiones_aliadas",
        "ck_remisiones_aliadas_valores_no_negativos",
        "(valor_cubierto IS NULL OR valor_cubierto >= 0)"
        " AND (tope_cubierto IS NULL OR tope_cubierto >= 0)"
        " AND (valor_atencion IS NULL OR valor_atencion >= 0)",
    ),
    (
        "respuestas_virtuales",
        "ck_respuestas_virtuales_aprobada_completa",
        "estado <> 'aprobada' OR (aprobada_en IS NOT NULL AND aprobada_por_id IS NOT NULL)",
    ),
    (
        "rutas",
        "ck_rutas_horario",
        "fin_real IS NULL OR inicio_real IS NULL OR fin_real >= inicio_real",
    ),
    (
        "rutas",
        "ck_rutas_iniciada_con_fecha",
        "estado NOT IN ('en_curso', 'finalizada') OR inicio_real IS NOT NULL",
    ),
    (
        "rutas",
        "ck_rutas_metricas_no_negativas",
        "(distancia_km IS NULL OR distancia_km >= 0) AND (duracion_min IS NULL OR duracion_min >= "
        "0)",
    ),
    (
        "servicios",
        "ck_servicios_cancelado_con_motivo",
        "estado <> 'cancelado' OR motivo_estado IS NOT NULL",
    ),
    (
        "servicios",
        "ck_servicios_horario",
        "termina_en IS NULL OR programado_para IS NULL OR termina_en > programado_para",
    ),
    ("solicitudes_afiliacion", "ck_solicitudes_afiliacion_valor_no_negativo", "valor_inicial >= 0"),
    (
        "solicitudes_virtuales",
        "ck_solicitudes_virtuales_respondida_con_fecha",
        "estado NOT IN ('respondida', 'cerrada') OR respondida_en IS NOT NULL",
    ),
    ("tareas", "ck_tareas_cierre_coherente", "(estado = 'cerrada') = (cerrada_en IS NOT NULL)"),
    ("tareas", "ck_tareas_titulo_no_vacio", "btrim(titulo) <> ''"),
    ("tipos_servicio", "ck_tipos_servicio_duracion_positiva", "duracion_min > 0"),
    ("tokens_uso_unico", "ck_tokens_uso_unico_intentos_no_negativos", "intentos >= 0"),
    (
        "usuarios",
        "ck_usuarios_aliada_con_clinica",
        "(rol = 'aliada') = (clinica_aliada_id IS NOT NULL)",
    ),
    ("usuarios", "ck_usuarios_con_identificador", "email IS NOT NULL OR telefono IS NOT NULL"),
    (
        "usuarios",
        "ck_usuarios_email_formato",
        "email IS NULL OR email ~ '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$'",
    ),
    ("usuarios", "ck_usuarios_nombre_no_vacio", "btrim(nombre) <> ''"),
    (
        "usuarios",
        "ck_usuarios_telefono_formato",
        "telefono IS NULL OR telefono ~ '^\\+[1-9][0-9]{7,14}$'",
    ),
]


def upgrade() -> None:
    for tabla, nombre, expresion in CHECKS:
        op.execute(f"ALTER TABLE {tabla} ADD CONSTRAINT {nombre} CHECK ({expresion})")


def downgrade() -> None:
    for tabla, nombre, _ in reversed(CHECKS):
        op.execute(f"ALTER TABLE {tabla} DROP CONSTRAINT {nombre}")

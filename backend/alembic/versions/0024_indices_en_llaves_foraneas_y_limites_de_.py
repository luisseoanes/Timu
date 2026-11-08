"""indices en llaves foraneas y limites de tiempo

Fase 5 de docs/plan-persistencia.md.

- Indice en las 52 llaves foraneas que no tenian: sin el, cruzar por esa llave (y las
  politicas de RLS que consultan por ella) recorre la tabla entera. test_persistencia falla
  si una llave foranea nueva llega sin indice.
- Limites de tiempo del rol de la aplicacion: ninguna consulta pasa de 30 s, nadie espera
  un bloqueo mas de 10 s y una transaccion abandonada no retiene filas mas de 60 s. Son del
  rol, asi que valen igual con PgBouncer delante.

Revision ID: 0024
Revises: 0023
Create Date: 2026-11-04 21:59:04.911701
"""

from alembic import op

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None

LIMITES = (
    ("statement_timeout", "30s"),
    ("lock_timeout", "10s"),
    ("idle_in_transaction_session_timeout", "60s"),
)


def upgrade() -> None:
    op.create_index(
        op.f("ix_adjuntos_clinicos_archivo_id"), "adjuntos_clinicos", ["archivo_id"], unique=False
    )
    op.create_index(
        op.f("ix_adjuntos_clinicos_subido_por_id"),
        "adjuntos_clinicos",
        ["subido_por_id"],
        unique=False,
    )
    op.create_index(op.f("ix_archivos_subido_por_id"), "archivos", ["subido_por_id"], unique=False)
    op.create_index(
        op.f("ix_avisos_cartera_mensaje_id"), "avisos_cartera", ["mensaje_id"], unique=False
    )
    op.create_index(
        op.f("ix_beneficios_plan_tipo_servicio_codigo"),
        "beneficios_plan",
        ["tipo_servicio_codigo"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cambios_plan_plan_anterior_id"), "cambios_plan", ["plan_anterior_id"], unique=False
    )
    op.create_index(
        op.f("ix_cambios_plan_plan_nuevo_id"), "cambios_plan", ["plan_nuevo_id"], unique=False
    )
    op.create_index(
        op.f("ix_cambios_plan_registrado_por_id"),
        "cambios_plan",
        ["registrado_por_id"],
        unique=False,
    )
    op.create_index(op.f("ix_campanas_creada_por_id"), "campanas", ["creada_por_id"], unique=False)
    op.create_index(op.f("ix_campanas_segmento_id"), "campanas", ["segmento_id"], unique=False)
    op.create_index(
        op.f("ix_carnets_emitidos_archivo_id"), "carnets_emitidos", ["archivo_id"], unique=False
    )
    op.create_index(
        op.f("ix_carnets_emitidos_emitido_por_id"),
        "carnets_emitidos",
        ["emitido_por_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_contratos_documento_archivo_id"),
        "contratos",
        ["documento_archivo_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversaciones_comerciales_asesor_id"),
        "conversaciones_comerciales",
        ["asesor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversaciones_comerciales_interesado_id"),
        "conversaciones_comerciales",
        ["interesado_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversaciones_comerciales_tarea_id"),
        "conversaciones_comerciales",
        ["tarea_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_destinatarios_campana_mensaje_id"),
        "destinatarios_campana",
        ["mensaje_id"],
        unique=False,
    )
    op.create_index(op.f("ix_encuestas_tarea_id"), "encuestas", ["tarea_id"], unique=False)
    op.create_index(
        op.f("ix_eventos_preventivos_aplicado_por_id"),
        "eventos_preventivos",
        ["aplicado_por_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_eventos_preventivos_autorizado_por_id"),
        "eventos_preventivos",
        ["autorizado_por_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_eventos_preventivos_servicio_id"),
        "eventos_preventivos",
        ["servicio_id"],
        unique=False,
    )
    op.create_index(op.f("ix_formulas_archivo_id"), "formulas", ["archivo_id"], unique=False)
    op.create_index(
        op.f("ix_formulas_emitida_por_id"), "formulas", ["emitida_por_id"], unique=False
    )
    op.create_index(
        op.f("ix_historias_clinicas_firmada_por_id"),
        "historias_clinicas",
        ["firmada_por_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_historias_clinicas_profesional_id"),
        "historias_clinicas",
        ["profesional_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_historias_clinicas_reemplaza_id"),
        "historias_clinicas",
        ["reemplaza_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_historias_clinicas_servicio_id"),
        "historias_clinicas",
        ["servicio_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_intentos_cobro_medio_id"), "intentos_cobro", ["medio_id"], unique=False
    )
    op.create_index(op.f("ix_intentos_cobro_pago_id"), "intentos_cobro", ["pago_id"], unique=False)
    op.create_index(
        op.f("ix_mascotas_foto_archivo_id"), "mascotas", ["foto_archivo_id"], unique=False
    )
    op.create_index(
        op.f("ix_pagos_registrado_por_id"), "pagos", ["registrado_por_id"], unique=False
    )
    op.create_index(
        op.f("ix_paradas_ruta_evidencia_archivo_id"),
        "paradas_ruta",
        ["evidencia_archivo_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_pendientes_autorizado_por_id"), "pendientes", ["autorizado_por_id"], unique=False
    )
    op.create_index(
        op.f("ix_planificaciones_ruta_solicitada_por_id"),
        "planificaciones_ruta",
        ["solicitada_por_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prompts_ia_activado_por_id"), "prompts_ia", ["activado_por_id"], unique=False
    )
    op.create_index(op.f("ix_reglas_plan_id"), "reglas", ["plan_id"], unique=False)
    op.create_index(
        op.f("ix_remisiones_aliadas_convenio_id"),
        "remisiones_aliadas",
        ["convenio_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_remisiones_aliadas_emitida_por_id"),
        "remisiones_aliadas",
        ["emitida_por_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_remisiones_aliadas_mascota_id"), "remisiones_aliadas", ["mascota_id"], unique=False
    )
    op.create_index(
        op.f("ix_remisiones_aliadas_reportada_por_id"),
        "remisiones_aliadas",
        ["reportada_por_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reportes_programados_creado_por_id"),
        "reportes_programados",
        ["creado_por_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_respuestas_virtuales_aprobada_por_id"),
        "respuestas_virtuales",
        ["aprobada_por_id"],
        unique=False,
    )
    op.create_index(op.f("ix_rutas_planificacion_id"), "rutas", ["planificacion_id"], unique=False)
    op.create_index(
        op.f("ix_segmentos_creado_por_id"), "segmentos", ["creado_por_id"], unique=False
    )
    op.create_index(
        op.f("ix_servicio_pasos_completado_por_id"),
        "servicio_pasos",
        ["completado_por_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servicios_autorizado_por_id"), "servicios", ["autorizado_por_id"], unique=False
    )
    op.create_index(
        op.f("ix_servicios_pendiente_origen_id"), "servicios", ["pendiente_origen_id"], unique=False
    )
    op.create_index(
        op.f("ix_solicitudes_afiliacion_contrato_id"),
        "solicitudes_afiliacion",
        ["contrato_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_solicitudes_afiliacion_pago_id"),
        "solicitudes_afiliacion",
        ["pago_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_solicitudes_afiliacion_plan_id"),
        "solicitudes_afiliacion",
        ["plan_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_solicitudes_virtuales_historia_id"),
        "solicitudes_virtuales",
        ["historia_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_usuarios_clinica_aliada_id"), "usuarios", ["clinica_aliada_id"], unique=False
    )
    for ajuste, valor in LIMITES:
        op.execute(f"ALTER ROLE timu_app SET {ajuste} = '{valor}'")


def downgrade() -> None:
    op.drop_index(op.f("ix_usuarios_clinica_aliada_id"), table_name="usuarios")
    op.drop_index(op.f("ix_solicitudes_virtuales_historia_id"), table_name="solicitudes_virtuales")
    op.drop_index(op.f("ix_solicitudes_afiliacion_plan_id"), table_name="solicitudes_afiliacion")
    op.drop_index(op.f("ix_solicitudes_afiliacion_pago_id"), table_name="solicitudes_afiliacion")
    op.drop_index(
        op.f("ix_solicitudes_afiliacion_contrato_id"), table_name="solicitudes_afiliacion"
    )
    op.drop_index(op.f("ix_servicios_pendiente_origen_id"), table_name="servicios")
    op.drop_index(op.f("ix_servicios_autorizado_por_id"), table_name="servicios")
    op.drop_index(op.f("ix_servicio_pasos_completado_por_id"), table_name="servicio_pasos")
    op.drop_index(op.f("ix_segmentos_creado_por_id"), table_name="segmentos")
    op.drop_index(op.f("ix_rutas_planificacion_id"), table_name="rutas")
    op.drop_index(
        op.f("ix_respuestas_virtuales_aprobada_por_id"), table_name="respuestas_virtuales"
    )
    op.drop_index(op.f("ix_reportes_programados_creado_por_id"), table_name="reportes_programados")
    op.drop_index(op.f("ix_remisiones_aliadas_reportada_por_id"), table_name="remisiones_aliadas")
    op.drop_index(op.f("ix_remisiones_aliadas_mascota_id"), table_name="remisiones_aliadas")
    op.drop_index(op.f("ix_remisiones_aliadas_emitida_por_id"), table_name="remisiones_aliadas")
    op.drop_index(op.f("ix_remisiones_aliadas_convenio_id"), table_name="remisiones_aliadas")
    op.drop_index(op.f("ix_reglas_plan_id"), table_name="reglas")
    op.drop_index(op.f("ix_prompts_ia_activado_por_id"), table_name="prompts_ia")
    op.drop_index(
        op.f("ix_planificaciones_ruta_solicitada_por_id"), table_name="planificaciones_ruta"
    )
    op.drop_index(op.f("ix_pendientes_autorizado_por_id"), table_name="pendientes")
    op.drop_index(op.f("ix_paradas_ruta_evidencia_archivo_id"), table_name="paradas_ruta")
    op.drop_index(op.f("ix_pagos_registrado_por_id"), table_name="pagos")
    op.drop_index(op.f("ix_mascotas_foto_archivo_id"), table_name="mascotas")
    op.drop_index(op.f("ix_intentos_cobro_pago_id"), table_name="intentos_cobro")
    op.drop_index(op.f("ix_intentos_cobro_medio_id"), table_name="intentos_cobro")
    op.drop_index(op.f("ix_historias_clinicas_servicio_id"), table_name="historias_clinicas")
    op.drop_index(op.f("ix_historias_clinicas_reemplaza_id"), table_name="historias_clinicas")
    op.drop_index(op.f("ix_historias_clinicas_profesional_id"), table_name="historias_clinicas")
    op.drop_index(op.f("ix_historias_clinicas_firmada_por_id"), table_name="historias_clinicas")
    op.drop_index(op.f("ix_formulas_emitida_por_id"), table_name="formulas")
    op.drop_index(op.f("ix_formulas_archivo_id"), table_name="formulas")
    op.drop_index(op.f("ix_eventos_preventivos_servicio_id"), table_name="eventos_preventivos")
    op.drop_index(
        op.f("ix_eventos_preventivos_autorizado_por_id"), table_name="eventos_preventivos"
    )
    op.drop_index(op.f("ix_eventos_preventivos_aplicado_por_id"), table_name="eventos_preventivos")
    op.drop_index(op.f("ix_encuestas_tarea_id"), table_name="encuestas")
    op.drop_index(op.f("ix_destinatarios_campana_mensaje_id"), table_name="destinatarios_campana")
    op.drop_index(
        op.f("ix_conversaciones_comerciales_tarea_id"), table_name="conversaciones_comerciales"
    )
    op.drop_index(
        op.f("ix_conversaciones_comerciales_interesado_id"), table_name="conversaciones_comerciales"
    )
    op.drop_index(
        op.f("ix_conversaciones_comerciales_asesor_id"), table_name="conversaciones_comerciales"
    )
    op.drop_index(op.f("ix_contratos_documento_archivo_id"), table_name="contratos")
    op.drop_index(op.f("ix_carnets_emitidos_emitido_por_id"), table_name="carnets_emitidos")
    op.drop_index(op.f("ix_carnets_emitidos_archivo_id"), table_name="carnets_emitidos")
    op.drop_index(op.f("ix_campanas_segmento_id"), table_name="campanas")
    op.drop_index(op.f("ix_campanas_creada_por_id"), table_name="campanas")
    op.drop_index(op.f("ix_cambios_plan_registrado_por_id"), table_name="cambios_plan")
    op.drop_index(op.f("ix_cambios_plan_plan_nuevo_id"), table_name="cambios_plan")
    op.drop_index(op.f("ix_cambios_plan_plan_anterior_id"), table_name="cambios_plan")
    op.drop_index(op.f("ix_beneficios_plan_tipo_servicio_codigo"), table_name="beneficios_plan")
    op.drop_index(op.f("ix_avisos_cartera_mensaje_id"), table_name="avisos_cartera")
    op.drop_index(op.f("ix_archivos_subido_por_id"), table_name="archivos")
    op.drop_index(op.f("ix_adjuntos_clinicos_subido_por_id"), table_name="adjuntos_clinicos")
    op.drop_index(op.f("ix_adjuntos_clinicos_archivo_id"), table_name="adjuntos_clinicos")
    for ajuste, _ in LIMITES:
        op.execute(f"ALTER ROLE timu_app RESET {ajuste}")

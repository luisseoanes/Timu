"""Modulos de la fase 1: acceso, cartera, servicios, afiliacion y mensajeria (F0 y F1)

Revision ID: 0002
Revises: 57577d1f1c12
Create Date: 2026-10-23 20:32:45.208278
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0002"
down_revision = "57577d1f1c12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Sobre la base del esquema inicial: las columnas obligatorias nuevas llevan un valor
    # por defecto o se rellenan antes de exigirse, para que la migracion corra tambien
    # sobre una base de desarrollo que ya tenga datos (p. ej. los planes del seed).
    op.create_table(
        "auditoria",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("usuario_id", sa.Uuid(), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("entidad", sa.String(length=64), nullable=False),
        sa.Column("entidad_id", sa.String(length=64), nullable=False),
        sa.Column("accion", sa.String(length=24), nullable=False),
        sa.Column(
            "cambios",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auditoria")),
    )
    op.create_index(
        "ix_auditoria_entidad", "auditoria", ["entidad", "entidad_id", "created_at"], unique=False
    )
    op.create_index(op.f("ix_auditoria_usuario_id"), "auditoria", ["usuario_id"], unique=False)
    op.create_table(
        "bajas_comunicaciones",
        sa.Column("destino", sa.String(length=255), nullable=False),
        sa.Column("canal", sa.String(length=24), nullable=False),
        sa.Column("motivo", sa.String(length=255), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bajas_comunicaciones")),
        sa.UniqueConstraint("destino", name=op.f("uq_bajas_comunicaciones_destino")),
    )
    op.create_table(
        "bloqueos_agenda",
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("ciudad", sa.String(length=80), nullable=True),
        sa.Column("modalidad", sa.String(length=24), nullable=True),
        sa.Column("motivo", sa.String(length=160), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bloqueos_agenda")),
    )
    op.create_index(op.f("ix_bloqueos_agenda_fecha"), "bloqueos_agenda", ["fecha"], unique=False)
    op.create_table(
        "ciudades",
        sa.Column("codigo", sa.String(length=8), nullable=False),
        sa.Column("nombre", sa.String(length=80), nullable=False),
        sa.Column("departamento", sa.String(length=80), nullable=False),
        sa.Column("latitud", sa.Float(), nullable=True),
        sa.Column("longitud", sa.Float(), nullable=True),
        sa.Column("activa", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ciudades")),
        sa.UniqueConstraint("codigo", name=op.f("uq_ciudades_codigo")),
    )
    op.create_index(op.f("ix_ciudades_nombre"), "ciudades", ["nombre"], unique=False)
    op.create_table(
        "especies",
        sa.Column("codigo", sa.String(length=24), nullable=False),
        sa.Column("nombre", sa.String(length=60), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_especies")),
        sa.UniqueConstraint("codigo", name=op.f("uq_especies_codigo")),
    )
    op.create_table(
        "eventos_pasarela",
        sa.Column("proveedor", sa.String(length=32), nullable=False),
        sa.Column("id_evento", sa.String(length=128), nullable=False),
        sa.Column("tipo", sa.String(length=60), nullable=False),
        sa.Column("referencia", sa.String(length=120), nullable=True),
        sa.Column(
            "payload",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("estado", sa.String(length=16), nullable=False),
        sa.Column("intentos", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("procesado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_eventos_pasarela")),
        sa.UniqueConstraint("id_evento", name=op.f("uq_eventos_pasarela_id_evento")),
    )
    op.create_index(
        op.f("ix_eventos_pasarela_estado"), "eventos_pasarela", ["estado"], unique=False
    )
    op.create_index(
        op.f("ix_eventos_pasarela_referencia"), "eventos_pasarela", ["referencia"], unique=False
    )
    op.create_table(
        "franjas_agenda",
        sa.Column("ciudad", sa.String(length=80), nullable=False),
        sa.Column("modalidad", sa.String(length=24), nullable=False),
        sa.Column("dia_semana", sa.Integer(), nullable=False),
        sa.Column("hora_inicio", sa.Time(), nullable=False),
        sa.Column("hora_fin", sa.Time(), nullable=False),
        sa.Column("capacidad", sa.Integer(), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_franjas_agenda")),
    )
    op.create_index(op.f("ix_franjas_agenda_ciudad"), "franjas_agenda", ["ciudad"], unique=False)
    op.create_index(
        op.f("ix_franjas_agenda_modalidad"), "franjas_agenda", ["modalidad"], unique=False
    )
    op.create_table(
        "plantillas_whatsapp",
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("idioma", sa.String(length=10), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("categoria", sa.String(length=24), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column(
            "variables",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("estado_aprobacion", sa.String(length=24), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plantillas_whatsapp")),
        sa.UniqueConstraint(
            "nombre", "idioma", "version", name=op.f("uq_plantillas_whatsapp_nombre")
        ),
    )
    op.create_index(
        op.f("ix_plantillas_whatsapp_nombre"), "plantillas_whatsapp", ["nombre"], unique=False
    )
    op.create_table(
        "tipos_servicio",
        sa.Column("codigo", sa.String(length=40), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("modalidad", sa.String(length=24), nullable=False),
        sa.Column("duracion_min", sa.Integer(), nullable=False),
        sa.Column("requiere_autorizacion", sa.Boolean(), nullable=False),
        sa.Column(
            "pasos",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tipos_servicio")),
        sa.UniqueConstraint("codigo", name=op.f("uq_tipos_servicio_codigo")),
    )
    op.create_index(
        op.f("ix_tipos_servicio_modalidad"), "tipos_servicio", ["modalidad"], unique=False
    )
    op.create_table(
        "archivos",
        sa.Column("clave", sa.String(length=255), nullable=False),
        sa.Column("proposito", sa.String(length=40), nullable=False),
        sa.Column("nombre_original", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("tamano_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("subido_por_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["subido_por_id"], ["usuarios.id"], name=op.f("fk_archivos_subido_por_id_usuarios")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_archivos")),
        sa.UniqueConstraint("clave", name=op.f("uq_archivos_clave")),
    )
    op.create_index(op.f("ix_archivos_proposito"), "archivos", ["proposito"], unique=False)
    op.create_table(
        "beneficios_plan",
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("tipo_servicio_codigo", sa.String(length=40), nullable=False),
        sa.Column("cupo", sa.Integer(), nullable=True),
        sa.Column("periodo_cupo", sa.String(length=12), nullable=False),
        sa.Column("cobertura_pct", sa.Integer(), nullable=False),
        sa.Column("copago", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["planes.id"],
            name=op.f("fk_beneficios_plan_plan_id_planes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tipo_servicio_codigo"],
            ["tipos_servicio.codigo"],
            name=op.f("fk_beneficios_plan_tipo_servicio_codigo_tipos_servicio"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_beneficios_plan")),
        sa.UniqueConstraint(
            "plan_id", "tipo_servicio_codigo", name=op.f("uq_beneficios_plan_plan_id")
        ),
    )
    op.create_index(
        op.f("ix_beneficios_plan_plan_id"), "beneficios_plan", ["plan_id"], unique=False
    )
    op.create_table(
        "esquemas_preventivos",
        sa.Column("codigo", sa.String(length=40), nullable=False),
        sa.Column("especie_codigo", sa.String(length=24), nullable=False),
        sa.Column("tipo", sa.String(length=40), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("edad_minima_semanas", sa.Integer(), nullable=False),
        sa.Column("dosis_iniciales", sa.Integer(), nullable=False),
        sa.Column("intervalo_inicial_dias", sa.Integer(), nullable=False),
        sa.Column("intervalo_refuerzo_dias", sa.Integer(), nullable=True),
        sa.Column("requiere_autorizacion", sa.Boolean(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["especie_codigo"],
            ["especies.codigo"],
            name=op.f("fk_esquemas_preventivos_especie_codigo_especies"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_esquemas_preventivos")),
        sa.UniqueConstraint("codigo", name=op.f("uq_esquemas_preventivos_codigo")),
    )
    op.create_index(
        op.f("ix_esquemas_preventivos_especie_codigo"),
        "esquemas_preventivos",
        ["especie_codigo"],
        unique=False,
    )
    op.create_table(
        "reglas",
        sa.Column("codigo", sa.String(length=60), nullable=False),
        sa.Column("nombre", sa.String(length=160), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("evento", sa.String(length=60), nullable=False),
        sa.Column(
            "condicion",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "accion",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("prioridad", sa.Integer(), nullable=False),
        sa.Column("detener", sa.Boolean(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=True),
        sa.Column("vigente_desde", sa.Date(), nullable=True),
        sa.Column("vigente_hasta", sa.Date(), nullable=True),
        sa.Column("activa", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["plan_id"], ["planes.id"], name=op.f("fk_reglas_plan_id_planes"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reglas")),
        sa.UniqueConstraint("codigo", name=op.f("uq_reglas_codigo")),
    )
    op.create_index(op.f("ix_reglas_activa"), "reglas", ["activa"], unique=False)
    op.create_index(op.f("ix_reglas_evento"), "reglas", ["evento"], unique=False)
    op.create_table(
        "servicio_pasos",
        sa.Column("servicio_id", sa.Uuid(), nullable=False),
        sa.Column("paso_codigo", sa.String(length=40), nullable=False),
        sa.Column("completado_por_id", sa.Uuid(), nullable=True),
        sa.Column(
            "datos",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["completado_por_id"],
            ["usuarios.id"],
            name=op.f("fk_servicio_pasos_completado_por_id_usuarios"),
        ),
        sa.ForeignKeyConstraint(
            ["servicio_id"],
            ["servicios.id"],
            name=op.f("fk_servicio_pasos_servicio_id_servicios"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_servicio_pasos")),
        sa.UniqueConstraint(
            "servicio_id", "paso_codigo", name=op.f("uq_servicio_pasos_servicio_id")
        ),
    )
    op.create_index(
        op.f("ix_servicio_pasos_servicio_id"), "servicio_pasos", ["servicio_id"], unique=False
    )
    op.create_table(
        "sesiones",
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("refresh_hash", sa.String(length=64), nullable=False),
        sa.Column("refresh_hash_anterior", sa.String(length=64), nullable=True),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revocada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name=op.f("fk_sesiones_usuario_id_usuarios"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sesiones")),
        sa.UniqueConstraint("refresh_hash", name=op.f("uq_sesiones_refresh_hash")),
    )
    op.create_index(
        op.f("ix_sesiones_refresh_hash_anterior"),
        "sesiones",
        ["refresh_hash_anterior"],
        unique=False,
    )
    op.create_index(op.f("ix_sesiones_usuario_id"), "sesiones", ["usuario_id"], unique=False)
    op.create_table(
        "tokens_uso_unico",
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("proposito", sa.String(length=24), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name=op.f("fk_tokens_uso_unico_usuario_id_usuarios"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tokens_uso_unico")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_tokens_uso_unico_token_hash")),
    )
    op.create_index(
        op.f("ix_tokens_uso_unico_usuario_id"), "tokens_uso_unico", ["usuario_id"], unique=False
    )
    op.create_table(
        "conversaciones_whatsapp",
        sa.Column("telefono", sa.String(length=32), nullable=False),
        sa.Column("familia_id", sa.Uuid(), nullable=True),
        sa.Column("ultimo_entrante_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["familia_id"],
            ["familias.id"],
            name=op.f("fk_conversaciones_whatsapp_familia_id_familias"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversaciones_whatsapp")),
        sa.UniqueConstraint("telefono", name=op.f("uq_conversaciones_whatsapp_telefono")),
    )
    op.create_index(
        op.f("ix_conversaciones_whatsapp_familia_id"),
        "conversaciones_whatsapp",
        ["familia_id"],
        unique=False,
    )
    op.create_table(
        "medios_pago_recurrente",
        sa.Column("familia_id", sa.Uuid(), nullable=False),
        sa.Column("proveedor", sa.String(length=32), nullable=False),
        sa.Column("fuente_id", sa.String(length=64), nullable=False),
        sa.Column("marca", sa.String(length=24), nullable=True),
        sa.Column("ultimos4", sa.String(length=4), nullable=True),
        sa.Column("email_titular", sa.String(length=255), nullable=False),
        sa.Column("autorizado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["familia_id"],
            ["familias.id"],
            name=op.f("fk_medios_pago_recurrente_familia_id_familias"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_medios_pago_recurrente")),
    )
    op.create_index(
        op.f("ix_medios_pago_recurrente_activo"), "medios_pago_recurrente", ["activo"], unique=False
    )
    op.create_index(
        op.f("ix_medios_pago_recurrente_familia_id"),
        "medios_pago_recurrente",
        ["familia_id"],
        unique=False,
    )
    op.create_table(
        "cambios_plan",
        sa.Column("contrato_id", sa.Uuid(), nullable=False),
        sa.Column("tipo", sa.String(length=24), nullable=False),
        sa.Column("plan_anterior_id", sa.Uuid(), nullable=True),
        sa.Column("plan_nuevo_id", sa.Uuid(), nullable=True),
        sa.Column("valor_anterior", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("valor_nuevo", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("ajuste", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("modo", sa.String(length=24), nullable=True),
        sa.Column("regla_codigo", sa.String(length=60), nullable=True),
        sa.Column("fecha_efectiva", sa.Date(), nullable=False),
        sa.Column("aplicado", sa.Boolean(), nullable=False),
        sa.Column("registrado_por_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["contrato_id"], ["contratos.id"], name=op.f("fk_cambios_plan_contrato_id_contratos")
        ),
        sa.ForeignKeyConstraint(
            ["plan_anterior_id"],
            ["planes.id"],
            name=op.f("fk_cambios_plan_plan_anterior_id_planes"),
        ),
        sa.ForeignKeyConstraint(
            ["plan_nuevo_id"], ["planes.id"], name=op.f("fk_cambios_plan_plan_nuevo_id_planes")
        ),
        sa.ForeignKeyConstraint(
            ["registrado_por_id"],
            ["usuarios.id"],
            name=op.f("fk_cambios_plan_registrado_por_id_usuarios"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cambios_plan")),
    )
    op.create_index(
        op.f("ix_cambios_plan_contrato_id"), "cambios_plan", ["contrato_id"], unique=False
    )
    op.create_table(
        "tareas",
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("area", sa.String(length=24), nullable=False),
        sa.Column("prioridad", sa.String(length=8), nullable=False),
        sa.Column("estado", sa.String(length=16), nullable=False),
        sa.Column("vence_el", sa.Date(), nullable=True),
        sa.Column("asignada_a_id", sa.Uuid(), nullable=True),
        sa.Column("familia_id", sa.Uuid(), nullable=True),
        sa.Column("servicio_id", sa.Uuid(), nullable=True),
        sa.Column("contrato_id", sa.Uuid(), nullable=True),
        sa.Column("origen", sa.String(length=60), nullable=True),
        sa.Column("clave", sa.String(length=160), nullable=True),
        sa.Column("cerrada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolucion", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["asignada_a_id"], ["usuarios.id"], name=op.f("fk_tareas_asignada_a_id_usuarios")
        ),
        sa.ForeignKeyConstraint(
            ["contrato_id"], ["contratos.id"], name=op.f("fk_tareas_contrato_id_contratos")
        ),
        sa.ForeignKeyConstraint(
            ["familia_id"], ["familias.id"], name=op.f("fk_tareas_familia_id_familias")
        ),
        sa.ForeignKeyConstraint(
            ["servicio_id"], ["servicios.id"], name=op.f("fk_tareas_servicio_id_servicios")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tareas")),
        sa.UniqueConstraint("clave", name=op.f("uq_tareas_clave")),
    )
    op.create_index(op.f("ix_tareas_area"), "tareas", ["area"], unique=False)
    op.create_index(op.f("ix_tareas_asignada_a_id"), "tareas", ["asignada_a_id"], unique=False)
    op.create_index(op.f("ix_tareas_contrato_id"), "tareas", ["contrato_id"], unique=False)
    op.create_index(op.f("ix_tareas_estado"), "tareas", ["estado"], unique=False)
    op.create_index(op.f("ix_tareas_familia_id"), "tareas", ["familia_id"], unique=False)
    op.create_index(op.f("ix_tareas_prioridad"), "tareas", ["prioridad"], unique=False)
    op.create_index(op.f("ix_tareas_servicio_id"), "tareas", ["servicio_id"], unique=False)
    op.create_index(op.f("ix_tareas_vence_el"), "tareas", ["vence_el"], unique=False)
    op.create_table(
        "avisos_cartera",
        sa.Column("cuota_id", sa.Uuid(), nullable=False),
        sa.Column("clave", sa.String(length=40), nullable=False),
        sa.Column("regla_codigo", sa.String(length=60), nullable=True),
        sa.Column("mensaje_id", sa.Uuid(), nullable=True),
        sa.Column("omitido", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["cuota_id"], ["cuotas.id"], name=op.f("fk_avisos_cartera_cuota_id_cuotas")
        ),
        sa.ForeignKeyConstraint(
            ["mensaje_id"], ["mensajes.id"], name=op.f("fk_avisos_cartera_mensaje_id_mensajes")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_avisos_cartera")),
        sa.UniqueConstraint("cuota_id", "clave", name=op.f("uq_avisos_cartera_cuota_id")),
    )
    op.create_index(
        op.f("ix_avisos_cartera_cuota_id"), "avisos_cartera", ["cuota_id"], unique=False
    )
    op.create_table(
        "aplicaciones_pago",
        sa.Column("pago_id", sa.Uuid(), nullable=False),
        sa.Column("cuota_id", sa.Uuid(), nullable=False),
        sa.Column("valor", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["cuota_id"], ["cuotas.id"], name=op.f("fk_aplicaciones_pago_cuota_id_cuotas")
        ),
        sa.ForeignKeyConstraint(
            ["pago_id"],
            ["pagos.id"],
            name=op.f("fk_aplicaciones_pago_pago_id_pagos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_aplicaciones_pago")),
    )
    op.create_index(
        op.f("ix_aplicaciones_pago_cuota_id"), "aplicaciones_pago", ["cuota_id"], unique=False
    )
    op.create_index(
        op.f("ix_aplicaciones_pago_pago_id"), "aplicaciones_pago", ["pago_id"], unique=False
    )
    op.create_table(
        "intentos_cobro",
        sa.Column("cuota_id", sa.Uuid(), nullable=False),
        sa.Column("medio_id", sa.Uuid(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("pago_id", sa.Uuid(), nullable=True),
        sa.Column("estado", sa.String(length=16), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["cuota_id"], ["cuotas.id"], name=op.f("fk_intentos_cobro_cuota_id_cuotas")
        ),
        sa.ForeignKeyConstraint(
            ["medio_id"],
            ["medios_pago_recurrente.id"],
            name=op.f("fk_intentos_cobro_medio_id_medios_pago_recurrente"),
        ),
        sa.ForeignKeyConstraint(
            ["pago_id"], ["pagos.id"], name=op.f("fk_intentos_cobro_pago_id_pagos")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_intentos_cobro")),
        sa.UniqueConstraint("cuota_id", "numero", name=op.f("uq_intentos_cobro_cuota_id")),
    )
    op.create_index(
        op.f("ix_intentos_cobro_cuota_id"), "intentos_cobro", ["cuota_id"], unique=False
    )
    op.create_table(
        "solicitudes_afiliacion",
        sa.Column("familia_id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("valor_inicial", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("referencia_pago", sa.String(length=60), nullable=False),
        sa.Column("pago_id", sa.Uuid(), nullable=True),
        sa.Column("contrato_id", sa.Uuid(), nullable=True),
        sa.Column("estado", sa.String(length=24), nullable=False),
        sa.Column("origen", sa.String(length=24), nullable=False),
        sa.Column(
            "aceptacion",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("completada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["contrato_id"],
            ["contratos.id"],
            name=op.f("fk_solicitudes_afiliacion_contrato_id_contratos"),
        ),
        sa.ForeignKeyConstraint(
            ["familia_id"],
            ["familias.id"],
            name=op.f("fk_solicitudes_afiliacion_familia_id_familias"),
        ),
        sa.ForeignKeyConstraint(
            ["pago_id"], ["pagos.id"], name=op.f("fk_solicitudes_afiliacion_pago_id_pagos")
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["planes.id"], name=op.f("fk_solicitudes_afiliacion_plan_id_planes")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_solicitudes_afiliacion")),
        sa.UniqueConstraint(
            "referencia_pago", name=op.f("uq_solicitudes_afiliacion_referencia_pago")
        ),
    )
    op.create_index(
        op.f("ix_solicitudes_afiliacion_estado"), "solicitudes_afiliacion", ["estado"], unique=False
    )
    op.create_index(
        op.f("ix_solicitudes_afiliacion_familia_id"),
        "solicitudes_afiliacion",
        ["familia_id"],
        unique=False,
    )
    op.drop_table("reglas_plan")
    op.add_column("contratos", sa.Column("numero", sa.String(length=20), nullable=True))
    op.execute("UPDATE contratos SET numero = 'C-' || left(id::text, 8)")
    op.alter_column("contratos", "numero", nullable=False)
    op.add_column("contratos", sa.Column("fecha_fin", sa.Date(), nullable=True))
    op.add_column(
        "contratos",
        sa.Column(
            "valor_plan", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "contratos",
        sa.Column("mascotas_adicionales", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "contratos",
        sa.Column(
            "valor_adicional_mascota",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "contratos",
        sa.Column(
            "saldo_a_favor", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"
        ),
    )
    op.add_column("contratos", sa.Column("aceptado_en", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contratos", sa.Column("medio_aceptacion", sa.String(length=24), nullable=True))
    op.add_column(
        "contratos",
        sa.Column(
            "evidencia_aceptacion",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column("contratos", sa.Column("documento_archivo_id", sa.Uuid(), nullable=True))
    op.create_unique_constraint(op.f("uq_contratos_numero"), "contratos", ["numero"])
    op.create_foreign_key(
        op.f("fk_contratos_documento_archivo_id_archivos"),
        "contratos",
        "archivos",
        ["documento_archivo_id"],
        ["id"],
    )
    op.add_column(
        "cuotas", sa.Column("tipo", sa.String(length=16), nullable=False, server_default="mensual")
    )
    op.add_column(
        "cuotas",
        sa.Column(
            "valor_pagado", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"
        ),
    )
    op.add_column("cuotas", sa.Column("descripcion", sa.String(length=255), nullable=True))
    op.alter_column(
        "cuotas",
        "estado",
        existing_type=sa.VARCHAR(length=24),
        type_=sa.String(length=16),
        existing_nullable=False,
    )
    op.create_unique_constraint(
        op.f("uq_cuotas_contrato_id"), "cuotas", ["contrato_id", "periodo", "tipo"]
    )
    op.add_column(
        "eventos_preventivos", sa.Column("esquema_codigo", sa.String(length=40), nullable=True)
    )
    op.add_column(
        "eventos_preventivos",
        sa.Column("dosis_numero", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "eventos_preventivos",
        sa.Column("estado", sa.String(length=16), nullable=False, server_default="programado"),
    )
    op.create_index(
        op.f("ix_eventos_preventivos_esquema_codigo"),
        "eventos_preventivos",
        ["esquema_codigo"],
        unique=False,
    )
    op.create_index(
        op.f("ix_eventos_preventivos_estado"), "eventos_preventivos", ["estado"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_eventos_preventivos_esquema_codigo_esquemas_preventivos"),
        "eventos_preventivos",
        "esquemas_preventivos",
        ["esquema_codigo"],
        ["codigo"],
    )
    op.add_column(
        "familias",
        sa.Column("tipo_documento", sa.String(length=8), nullable=False, server_default="CC"),
    )
    op.add_column("familias", sa.Column("geo_precision", sa.String(length=16), nullable=True))
    op.add_column(
        "familias",
        sa.Column("origen", sa.String(length=32), nullable=False, server_default="panel"),
    )
    op.add_column(
        "familias", sa.Column("dada_de_baja_en", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("familias", sa.Column("motivo_baja", sa.String(length=255), nullable=True))
    op.drop_index("ix_familias_documento", table_name="familias")
    op.create_index(op.f("ix_familias_documento"), "familias", ["documento"], unique=False)
    op.create_index(
        op.f("ix_familias_dada_de_baja_en"), "familias", ["dada_de_baja_en"], unique=False
    )
    op.create_unique_constraint(
        op.f("uq_familias_tipo_documento"), "familias", ["tipo_documento", "documento"]
    )
    op.add_column("mascotas", sa.Column("esterilizada", sa.Boolean(), nullable=True))
    op.add_column("mascotas", sa.Column("foto_archivo_id", sa.Uuid(), nullable=True))
    op.add_column(
        "mascotas", sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true())
    )
    op.add_column(
        "mascotas", sa.Column("dada_de_baja_en", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("mascotas", sa.Column("motivo_baja", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_mascotas_activa"), "mascotas", ["activa"], unique=False)
    op.create_foreign_key(
        op.f("fk_mascotas_foto_archivo_id_archivos"),
        "mascotas",
        "archivos",
        ["foto_archivo_id"],
        ["id"],
    )
    op.add_column("mensajes", sa.Column("destino", sa.String(length=255), nullable=True))
    op.add_column(
        "mensajes",
        sa.Column(
            "variables",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column("mensajes", sa.Column("asunto", sa.String(length=255), nullable=True))
    op.add_column(
        "mensajes", sa.Column("intentos", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column("mensajes", sa.Column("error", sa.Text(), nullable=True))
    op.add_column(
        "mensajes", sa.Column("masivo", sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.add_column("mensajes", sa.Column("entregado_en", sa.DateTime(timezone=True), nullable=True))
    op.add_column("mensajes", sa.Column("leido_en", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_mensajes_destino"), "mensajes", ["destino"], unique=False)
    op.add_column("pagos", sa.Column("contrato_id", sa.Uuid(), nullable=True))
    op.add_column("pagos", sa.Column("medio", sa.String(length=32), nullable=True))
    op.add_column("pagos", sa.Column("id_transaccion", sa.String(length=120), nullable=True))
    op.add_column("pagos", sa.Column("fecha_pago", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "pagos", sa.Column("aplicado", sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.add_column("pagos", sa.Column("registrado_por_id", sa.Uuid(), nullable=True))
    op.add_column("pagos", sa.Column("notas", sa.Text(), nullable=True))
    op.drop_index("ix_pagos_referencia_externa", table_name="pagos")
    op.create_index(op.f("ix_pagos_contrato_id"), "pagos", ["contrato_id"], unique=False)
    op.create_index(op.f("ix_pagos_id_transaccion"), "pagos", ["id_transaccion"], unique=False)
    op.create_unique_constraint(
        op.f("uq_pagos_referencia_externa"), "pagos", ["referencia_externa"]
    )
    op.create_foreign_key(
        op.f("fk_pagos_contrato_id_contratos"), "pagos", "contratos", ["contrato_id"], ["id"]
    )
    op.create_foreign_key(
        op.f("fk_pagos_registrado_por_id_usuarios"),
        "pagos",
        "usuarios",
        ["registrado_por_id"],
        ["id"],
    )
    op.add_column("pendientes", sa.Column("estado", sa.String(length=24), nullable=True))
    op.execute(
        "UPDATE pendientes SET estado = CASE WHEN resuelto THEN 'resuelto' "
        "WHEN autorizado THEN 'autorizado' ELSE 'pendiente_autorizacion' END"
    )
    op.alter_column("pendientes", "estado", nullable=False)
    op.add_column("pendientes", sa.Column("autorizado_por_id", sa.Uuid(), nullable=True))
    op.add_column(
        "pendientes", sa.Column("autorizado_en", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "pendientes", sa.Column("medio_autorizacion", sa.String(length=24), nullable=True)
    )
    op.add_column("pendientes", sa.Column("resolucion", sa.Text(), nullable=True))
    op.add_column("pendientes", sa.Column("resuelto_en", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_pendientes_estado"), "pendientes", ["estado"], unique=False)
    op.create_foreign_key(
        op.f("fk_pendientes_autorizado_por_id_usuarios"),
        "pendientes",
        "usuarios",
        ["autorizado_por_id"],
        ["id"],
    )
    op.drop_column("pendientes", "autorizado")
    op.drop_column("pendientes", "resuelto")
    op.add_column("planes", sa.Column("codigo", sa.String(length=40), nullable=True))
    op.execute(
        "UPDATE planes SET codigo = "
        "left(lower(regexp_replace(nombre, '[^a-zA-Z0-9]+', '_', 'g')), 32) "
        "|| '_' || left(id::text, 4)"
    )
    op.alter_column("planes", "codigo", nullable=False)
    op.add_column(
        "planes",
        sa.Column(
            "especies",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default="[]",
        ),
    )
    op.create_unique_constraint(op.f("uq_planes_codigo"), "planes", ["codigo"])
    op.add_column("servicios", sa.Column("tipo_codigo", sa.String(length=40), nullable=True))
    op.execute("UPDATE servicios SET tipo_codigo = tipo")
    op.alter_column("servicios", "tipo_codigo", nullable=False)
    op.add_column("servicios", sa.Column("ciudad", sa.String(length=80), nullable=True))
    op.execute(
        "UPDATE servicios SET ciudad = f.ciudad FROM familias f WHERE f.id = servicios.familia_id"
    )
    op.alter_column("servicios", "ciudad", nullable=False)
    op.add_column("servicios", sa.Column("termina_en", sa.DateTime(timezone=True), nullable=True))
    op.add_column("servicios", sa.Column("franja_id", sa.Uuid(), nullable=True))
    op.add_column("servicios", sa.Column("profesional_id", sa.Uuid(), nullable=True))
    op.add_column("servicios", sa.Column("autorizado_por_id", sa.Uuid(), nullable=True))
    op.add_column(
        "servicios", sa.Column("autorizado_en", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("servicios", sa.Column("pendiente_origen_id", sa.Uuid(), nullable=True))
    op.add_column("servicios", sa.Column("motivo_estado", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_servicios_ciudad"), "servicios", ["ciudad"], unique=False)
    op.create_index(op.f("ix_servicios_franja_id"), "servicios", ["franja_id"], unique=False)
    op.create_index(
        op.f("ix_servicios_profesional_id"), "servicios", ["profesional_id"], unique=False
    )
    op.create_index(op.f("ix_servicios_tipo_codigo"), "servicios", ["tipo_codigo"], unique=False)
    op.create_foreign_key(
        op.f("fk_servicios_franja_id_franjas_agenda"),
        "servicios",
        "franjas_agenda",
        ["franja_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_servicios_profesional_id_usuarios"),
        "servicios",
        "usuarios",
        ["profesional_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_servicios_autorizado_por_id_usuarios"),
        "servicios",
        "usuarios",
        ["autorizado_por_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_servicios_tipo_codigo_tipos_servicio"),
        "servicios",
        "tipos_servicio",
        ["tipo_codigo"],
        ["codigo"],
    )
    op.create_foreign_key(
        op.f("fk_servicios_pendiente_origen_id_pendientes"),
        "servicios",
        "pendientes",
        ["pendiente_origen_id"],
        ["id"],
    )
    op.add_column("usuarios", sa.Column("telefono", sa.String(length=32), nullable=True))
    op.alter_column("usuarios", "email", existing_type=sa.VARCHAR(length=255), nullable=True)
    op.create_index(op.f("ix_usuarios_telefono"), "usuarios", ["telefono"], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_usuarios_telefono"), table_name="usuarios")
    op.alter_column("usuarios", "email", existing_type=sa.VARCHAR(length=255), nullable=False)
    op.drop_column("usuarios", "telefono")
    op.drop_constraint(
        op.f("fk_servicios_pendiente_origen_id_pendientes"), "servicios", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_servicios_tipo_codigo_tipos_servicio"), "servicios", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_servicios_autorizado_por_id_usuarios"), "servicios", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_servicios_profesional_id_usuarios"), "servicios", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_servicios_franja_id_franjas_agenda"), "servicios", type_="foreignkey"
    )
    op.drop_index(op.f("ix_servicios_tipo_codigo"), table_name="servicios")
    op.drop_index(op.f("ix_servicios_profesional_id"), table_name="servicios")
    op.drop_index(op.f("ix_servicios_franja_id"), table_name="servicios")
    op.drop_index(op.f("ix_servicios_ciudad"), table_name="servicios")
    op.drop_column("servicios", "motivo_estado")
    op.drop_column("servicios", "pendiente_origen_id")
    op.drop_column("servicios", "autorizado_en")
    op.drop_column("servicios", "autorizado_por_id")
    op.drop_column("servicios", "profesional_id")
    op.drop_column("servicios", "franja_id")
    op.drop_column("servicios", "termina_en")
    op.drop_column("servicios", "ciudad")
    op.drop_column("servicios", "tipo_codigo")
    op.drop_constraint(op.f("uq_planes_codigo"), "planes", type_="unique")
    op.drop_column("planes", "especies")
    op.drop_column("planes", "codigo")
    op.add_column(
        "pendientes", sa.Column("resuelto", sa.BOOLEAN(), autoincrement=False, nullable=False)
    )
    op.add_column(
        "pendientes", sa.Column("autorizado", sa.BOOLEAN(), autoincrement=False, nullable=False)
    )
    op.drop_constraint(
        op.f("fk_pendientes_autorizado_por_id_usuarios"), "pendientes", type_="foreignkey"
    )
    op.drop_index(op.f("ix_pendientes_estado"), table_name="pendientes")
    op.drop_column("pendientes", "resuelto_en")
    op.drop_column("pendientes", "resolucion")
    op.drop_column("pendientes", "medio_autorizacion")
    op.drop_column("pendientes", "autorizado_en")
    op.drop_column("pendientes", "autorizado_por_id")
    op.drop_column("pendientes", "estado")
    op.drop_constraint(op.f("fk_pagos_registrado_por_id_usuarios"), "pagos", type_="foreignkey")
    op.drop_constraint(op.f("fk_pagos_contrato_id_contratos"), "pagos", type_="foreignkey")
    op.drop_constraint(op.f("uq_pagos_referencia_externa"), "pagos", type_="unique")
    op.drop_index(op.f("ix_pagos_id_transaccion"), table_name="pagos")
    op.drop_index(op.f("ix_pagos_contrato_id"), table_name="pagos")
    op.create_index("ix_pagos_referencia_externa", "pagos", ["referencia_externa"], unique=True)
    op.drop_column("pagos", "notas")
    op.drop_column("pagos", "registrado_por_id")
    op.drop_column("pagos", "aplicado")
    op.drop_column("pagos", "fecha_pago")
    op.drop_column("pagos", "id_transaccion")
    op.drop_column("pagos", "medio")
    op.drop_column("pagos", "contrato_id")
    op.drop_index(op.f("ix_mensajes_destino"), table_name="mensajes")
    op.drop_column("mensajes", "leido_en")
    op.drop_column("mensajes", "entregado_en")
    op.drop_column("mensajes", "masivo")
    op.drop_column("mensajes", "error")
    op.drop_column("mensajes", "intentos")
    op.drop_column("mensajes", "asunto")
    op.drop_column("mensajes", "variables")
    op.drop_column("mensajes", "destino")
    op.drop_constraint(op.f("fk_mascotas_foto_archivo_id_archivos"), "mascotas", type_="foreignkey")
    op.drop_index(op.f("ix_mascotas_activa"), table_name="mascotas")
    op.drop_column("mascotas", "motivo_baja")
    op.drop_column("mascotas", "dada_de_baja_en")
    op.drop_column("mascotas", "activa")
    op.drop_column("mascotas", "foto_archivo_id")
    op.drop_column("mascotas", "esterilizada")
    op.drop_constraint(op.f("uq_familias_tipo_documento"), "familias", type_="unique")
    op.drop_index(op.f("ix_familias_dada_de_baja_en"), table_name="familias")
    op.drop_index(op.f("ix_familias_documento"), table_name="familias")
    op.create_index("ix_familias_documento", "familias", ["documento"], unique=True)
    op.drop_column("familias", "motivo_baja")
    op.drop_column("familias", "dada_de_baja_en")
    op.drop_column("familias", "origen")
    op.drop_column("familias", "geo_precision")
    op.drop_column("familias", "tipo_documento")
    op.drop_constraint(
        op.f("fk_eventos_preventivos_esquema_codigo_esquemas_preventivos"),
        "eventos_preventivos",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_eventos_preventivos_estado"), table_name="eventos_preventivos")
    op.drop_index(op.f("ix_eventos_preventivos_esquema_codigo"), table_name="eventos_preventivos")
    op.drop_column("eventos_preventivos", "estado")
    op.drop_column("eventos_preventivos", "dosis_numero")
    op.drop_column("eventos_preventivos", "esquema_codigo")
    op.drop_constraint(op.f("uq_cuotas_contrato_id"), "cuotas", type_="unique")
    op.alter_column(
        "cuotas",
        "estado",
        existing_type=sa.String(length=16),
        type_=sa.VARCHAR(length=24),
        existing_nullable=False,
    )
    op.drop_column("cuotas", "descripcion")
    op.drop_column("cuotas", "valor_pagado")
    op.drop_column("cuotas", "tipo")
    op.drop_constraint(
        op.f("fk_contratos_documento_archivo_id_archivos"), "contratos", type_="foreignkey"
    )
    op.drop_constraint(op.f("uq_contratos_numero"), "contratos", type_="unique")
    op.drop_column("contratos", "documento_archivo_id")
    op.drop_column("contratos", "evidencia_aceptacion")
    op.drop_column("contratos", "medio_aceptacion")
    op.drop_column("contratos", "aceptado_en")
    op.drop_column("contratos", "saldo_a_favor")
    op.drop_column("contratos", "valor_adicional_mascota")
    op.drop_column("contratos", "mascotas_adicionales")
    op.drop_column("contratos", "valor_plan")
    op.drop_column("contratos", "fecha_fin")
    op.drop_column("contratos", "numero")
    op.create_table(
        "reglas_plan",
        sa.Column("plan_id", sa.UUID(), autoincrement=False, nullable=True),
        sa.Column("nombre", sa.VARCHAR(length=160), autoincrement=False, nullable=False),
        sa.Column(
            "condicion",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "accion", postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False
        ),
        sa.Column("prioridad", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("activa", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["planes.id"], name="fk_reglas_plan_plan_id_planes", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reglas_plan"),
    )
    op.drop_index(op.f("ix_solicitudes_afiliacion_familia_id"), table_name="solicitudes_afiliacion")
    op.drop_index(op.f("ix_solicitudes_afiliacion_estado"), table_name="solicitudes_afiliacion")
    op.drop_table("solicitudes_afiliacion")
    op.drop_index(op.f("ix_intentos_cobro_cuota_id"), table_name="intentos_cobro")
    op.drop_table("intentos_cobro")
    op.drop_index(op.f("ix_aplicaciones_pago_pago_id"), table_name="aplicaciones_pago")
    op.drop_index(op.f("ix_aplicaciones_pago_cuota_id"), table_name="aplicaciones_pago")
    op.drop_table("aplicaciones_pago")
    op.drop_index(op.f("ix_avisos_cartera_cuota_id"), table_name="avisos_cartera")
    op.drop_table("avisos_cartera")
    op.drop_index(op.f("ix_tareas_vence_el"), table_name="tareas")
    op.drop_index(op.f("ix_tareas_servicio_id"), table_name="tareas")
    op.drop_index(op.f("ix_tareas_prioridad"), table_name="tareas")
    op.drop_index(op.f("ix_tareas_familia_id"), table_name="tareas")
    op.drop_index(op.f("ix_tareas_estado"), table_name="tareas")
    op.drop_index(op.f("ix_tareas_contrato_id"), table_name="tareas")
    op.drop_index(op.f("ix_tareas_asignada_a_id"), table_name="tareas")
    op.drop_index(op.f("ix_tareas_area"), table_name="tareas")
    op.drop_table("tareas")
    op.drop_index(op.f("ix_cambios_plan_contrato_id"), table_name="cambios_plan")
    op.drop_table("cambios_plan")
    op.drop_index(op.f("ix_medios_pago_recurrente_familia_id"), table_name="medios_pago_recurrente")
    op.drop_index(op.f("ix_medios_pago_recurrente_activo"), table_name="medios_pago_recurrente")
    op.drop_table("medios_pago_recurrente")
    op.drop_index(
        op.f("ix_conversaciones_whatsapp_familia_id"), table_name="conversaciones_whatsapp"
    )
    op.drop_table("conversaciones_whatsapp")
    op.drop_index(op.f("ix_tokens_uso_unico_usuario_id"), table_name="tokens_uso_unico")
    op.drop_table("tokens_uso_unico")
    op.drop_index(op.f("ix_sesiones_usuario_id"), table_name="sesiones")
    op.drop_index(op.f("ix_sesiones_refresh_hash_anterior"), table_name="sesiones")
    op.drop_table("sesiones")
    op.drop_index(op.f("ix_servicio_pasos_servicio_id"), table_name="servicio_pasos")
    op.drop_table("servicio_pasos")
    op.drop_index(op.f("ix_reglas_evento"), table_name="reglas")
    op.drop_index(op.f("ix_reglas_activa"), table_name="reglas")
    op.drop_table("reglas")
    op.drop_index(op.f("ix_esquemas_preventivos_especie_codigo"), table_name="esquemas_preventivos")
    op.drop_table("esquemas_preventivos")
    op.drop_index(op.f("ix_beneficios_plan_plan_id"), table_name="beneficios_plan")
    op.drop_table("beneficios_plan")
    op.drop_index(op.f("ix_archivos_proposito"), table_name="archivos")
    op.drop_table("archivos")
    op.drop_index(op.f("ix_tipos_servicio_modalidad"), table_name="tipos_servicio")
    op.drop_table("tipos_servicio")
    op.drop_index(op.f("ix_plantillas_whatsapp_nombre"), table_name="plantillas_whatsapp")
    op.drop_table("plantillas_whatsapp")
    op.drop_index(op.f("ix_franjas_agenda_modalidad"), table_name="franjas_agenda")
    op.drop_index(op.f("ix_franjas_agenda_ciudad"), table_name="franjas_agenda")
    op.drop_table("franjas_agenda")
    op.drop_index(op.f("ix_eventos_pasarela_referencia"), table_name="eventos_pasarela")
    op.drop_index(op.f("ix_eventos_pasarela_estado"), table_name="eventos_pasarela")
    op.drop_table("eventos_pasarela")
    op.drop_table("especies")
    op.drop_index(op.f("ix_ciudades_nombre"), table_name="ciudades")
    op.drop_table("ciudades")
    op.drop_index(op.f("ix_bloqueos_agenda_fecha"), table_name="bloqueos_agenda")
    op.drop_table("bloqueos_agenda")
    op.drop_table("bajas_comunicaciones")
    op.drop_index(op.f("ix_auditoria_usuario_id"), table_name="auditoria")
    op.drop_index("ix_auditoria_entidad", table_name="auditoria")
    op.drop_table("auditoria")
    # ### end Alembic commands ###

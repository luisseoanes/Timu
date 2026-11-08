"""llaves foraneas a los catalogos

Fase 2b de docs/plan-persistencia.md. Lo que la aplicacion validaba contra los catalogos
("ciudad tomada del catalogo", especie, plantilla, plan, regla) lo garantiza ahora la base.
Las ciudades se guardan por nombre canonico, asi que ciudades.nombre pasa a ser unico y las
llaves van con ON UPDATE CASCADE: corregir el nombre en el catalogo se propaga. Quedan fuera
interesados.ciudad (un interesado puede venir de una ciudad sin cobertura, y ese dato vale)
y las referencias a plantillas de WhatsApp y prompts versionados (varias filas por nombre).
Los codigos de prompt son un conjunto cerrado: enum codigo_prompt.

Revision ID: 0016
Revises: 0015
Create Date: 2026-11-04 17:09:11.016078
"""

from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None

_COLUMNAS_PROMPT = (
    ("prompts_ia", "codigo"),
    ("consultas_ia", "prompt_codigo"),
    ("casos_prueba_ia", "prompt_codigo"),
)


def upgrade() -> None:
    # El indice unico va primero: las llaves foraneas a ciudades.nombre lo necesitan.
    op.drop_index("ix_ciudades_nombre", table_name="ciudades")
    op.create_index(op.f("ix_ciudades_nombre"), "ciudades", ["nombre"], unique=True)
    op.execute("CREATE TYPE codigo_prompt AS ENUM ('comercial_guion', 'veterinario_borrador')")
    for tabla, columna in _COLUMNAS_PROMPT:
        op.execute(
            f"ALTER TABLE {tabla} ALTER COLUMN {columna} TYPE codigo_prompt"
            f" USING {columna}::text::codigo_prompt"
        )
    op.create_index(
        op.f("ix_avisos_cartera_regla_codigo"), "avisos_cartera", ["regla_codigo"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_avisos_cartera_regla_codigo_reglas"),
        "avisos_cartera",
        "reglas",
        ["regla_codigo"],
        ["codigo"],
        onupdate="CASCADE",
    )
    op.create_index(op.f("ix_bloqueos_agenda_ciudad"), "bloqueos_agenda", ["ciudad"], unique=False)
    op.create_foreign_key(
        op.f("fk_bloqueos_agenda_ciudad_ciudades"),
        "bloqueos_agenda",
        "ciudades",
        ["ciudad"],
        ["nombre"],
        onupdate="CASCADE",
    )
    op.create_index(
        op.f("ix_cambios_plan_regla_codigo"), "cambios_plan", ["regla_codigo"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_cambios_plan_regla_codigo_reglas"),
        "cambios_plan",
        "reglas",
        ["regla_codigo"],
        ["codigo"],
        onupdate="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_clinicas_aliadas_ciudad_ciudades"),
        "clinicas_aliadas",
        "ciudades",
        ["ciudad"],
        ["nombre"],
        onupdate="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_familias_ciudad_ciudades"),
        "familias",
        "ciudades",
        ["ciudad"],
        ["nombre"],
        onupdate="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_franjas_agenda_ciudad_ciudades"),
        "franjas_agenda",
        "ciudades",
        ["ciudad"],
        ["nombre"],
        onupdate="CASCADE",
    )
    op.create_index(
        op.f("ix_historias_clinicas_plantilla_codigo"),
        "historias_clinicas",
        ["plantilla_codigo"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk_historias_clinicas_plantilla_codigo_plantillas_consulta"),
        "historias_clinicas",
        "plantillas_consulta",
        ["plantilla_codigo"],
        ["codigo"],
        onupdate="CASCADE",
    )
    op.create_index(
        op.f("ix_interesados_plan_sugerido"), "interesados", ["plan_sugerido"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_interesados_plan_sugerido_planes"),
        "interesados",
        "planes",
        ["plan_sugerido"],
        ["codigo"],
        onupdate="CASCADE",
    )
    op.create_index(op.f("ix_mascotas_especie"), "mascotas", ["especie"], unique=False)
    op.create_foreign_key(
        op.f("fk_mascotas_especie_especies"),
        "mascotas",
        "especies",
        ["especie"],
        ["codigo"],
        onupdate="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_planes_ciudad_ciudades"),
        "planes",
        "ciudades",
        ["ciudad"],
        ["nombre"],
        onupdate="CASCADE",
    )
    op.create_index(
        op.f("ix_planificaciones_ruta_ciudad"), "planificaciones_ruta", ["ciudad"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_planificaciones_ruta_ciudad_ciudades"),
        "planificaciones_ruta",
        "ciudades",
        ["ciudad"],
        ["nombre"],
        onupdate="CASCADE",
    )
    op.create_index(
        op.f("ix_reportes_programados_ciudad"), "reportes_programados", ["ciudad"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_reportes_programados_ciudad_ciudades"),
        "reportes_programados",
        "ciudades",
        ["ciudad"],
        ["nombre"],
        onupdate="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_rutas_ciudad_ciudades"),
        "rutas",
        "ciudades",
        ["ciudad"],
        ["nombre"],
        onupdate="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_servicios_ciudad_ciudades"),
        "servicios",
        "ciudades",
        ["ciudad"],
        ["nombre"],
        onupdate="CASCADE",
    )
    op.create_index(
        op.f("ix_solicitudes_virtuales_respuesta_codigo"),
        "solicitudes_virtuales",
        ["respuesta_codigo"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk_solicitudes_virtuales_respuesta_codigo_respuestas_virtuales"),
        "solicitudes_virtuales",
        "respuestas_virtuales",
        ["respuesta_codigo"],
        ["codigo"],
        onupdate="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_solicitudes_virtuales_respuesta_codigo_respuestas_virtuales"),
        "solicitudes_virtuales",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_solicitudes_virtuales_respuesta_codigo"), table_name="solicitudes_virtuales"
    )
    op.drop_constraint(op.f("fk_servicios_ciudad_ciudades"), "servicios", type_="foreignkey")
    op.drop_constraint(op.f("fk_rutas_ciudad_ciudades"), "rutas", type_="foreignkey")
    op.drop_constraint(
        op.f("fk_reportes_programados_ciudad_ciudades"), "reportes_programados", type_="foreignkey"
    )
    op.drop_index(op.f("ix_reportes_programados_ciudad"), table_name="reportes_programados")
    op.drop_constraint(
        op.f("fk_planificaciones_ruta_ciudad_ciudades"), "planificaciones_ruta", type_="foreignkey"
    )
    op.drop_index(op.f("ix_planificaciones_ruta_ciudad"), table_name="planificaciones_ruta")
    op.drop_constraint(op.f("fk_planes_ciudad_ciudades"), "planes", type_="foreignkey")
    op.drop_constraint(op.f("fk_mascotas_especie_especies"), "mascotas", type_="foreignkey")
    op.drop_index(op.f("ix_mascotas_especie"), table_name="mascotas")
    op.drop_constraint(
        op.f("fk_interesados_plan_sugerido_planes"), "interesados", type_="foreignkey"
    )
    op.drop_index(op.f("ix_interesados_plan_sugerido"), table_name="interesados")
    op.drop_constraint(
        op.f("fk_historias_clinicas_plantilla_codigo_plantillas_consulta"),
        "historias_clinicas",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_historias_clinicas_plantilla_codigo"), table_name="historias_clinicas")
    op.drop_constraint(
        op.f("fk_franjas_agenda_ciudad_ciudades"), "franjas_agenda", type_="foreignkey"
    )
    op.drop_constraint(op.f("fk_familias_ciudad_ciudades"), "familias", type_="foreignkey")
    op.drop_constraint(
        op.f("fk_clinicas_aliadas_ciudad_ciudades"), "clinicas_aliadas", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_cambios_plan_regla_codigo_reglas"), "cambios_plan", type_="foreignkey"
    )
    op.drop_index(op.f("ix_cambios_plan_regla_codigo"), table_name="cambios_plan")
    op.drop_constraint(
        op.f("fk_bloqueos_agenda_ciudad_ciudades"), "bloqueos_agenda", type_="foreignkey"
    )
    op.drop_index(op.f("ix_bloqueos_agenda_ciudad"), table_name="bloqueos_agenda")
    op.drop_constraint(
        op.f("fk_avisos_cartera_regla_codigo_reglas"), "avisos_cartera", type_="foreignkey"
    )
    op.drop_index(op.f("ix_avisos_cartera_regla_codigo"), table_name="avisos_cartera")
    for tabla, columna in _COLUMNAS_PROMPT:
        op.execute(
            f"ALTER TABLE {tabla} ALTER COLUMN {columna} TYPE varchar(40) USING {columna}::text"
        )
    op.execute("DROP TYPE codigo_prompt")
    op.drop_index(op.f("ix_ciudades_nombre"), table_name="ciudades")
    op.create_index("ix_ciudades_nombre", "ciudades", ["nombre"], unique=False)

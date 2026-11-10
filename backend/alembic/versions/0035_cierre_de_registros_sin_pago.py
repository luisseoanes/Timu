"""afiliaciones: reintento, cierre y anonimizacion de los registros en linea sin pagar

6.1. Reintentar tras un pago rechazado da otro pago, con referencia nueva, a la misma
solicitud: `referencias_anteriores` guarda las de antes para reconocer un aprobado tardio con
ellas. Lo que nunca se paga se cancela a las 48 horas (en Python, `registro.cerrar_sin_pago`)
y, a los seis meses, anonimizar_registros_abandonados() borra su contacto (Ley 1581): el de
la solicitud, el del interesado que creo, la tarea del cierre, los datos del pagador que
guardo la pasarela y su rastro en la bitacora. `anonimizada_en` marca lo ya borrado.

Revision ID: 0035
Revises: 0034
Create Date: 2026-11-10 18:00:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0035"
down_revision = "0034"
branch_labels = None
depends_on = None

_ANONIMIZAR_ABANDONADOS = """
CREATE OR REPLACE FUNCTION anonimizar_registros_abandonados(p_antes timestamptz)
RETURNS integer
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE
    v_solicitudes uuid[];
    v_referencias text[];
    v_interesados uuid[];
    v_tareas text[];
    v_ids text[];
    v_anonimo constant text := '[anonimizado]';
    -- Prefijo internacional 999: no esta asignado a ningun pais.
    v_telefono constant text := '+99900000000';
    v_quitar constant text[] :=
        ARRAY['ip', 'agente', 'user_agent', 'nombre', 'documento', 'email', 'telefono'];
    v_personales constant text[] := ARRAY[
        'contacto_nombre', 'contacto_telefono', 'contacto_email', 'aceptacion', 'nombre',
        'telefono', 'email', 'datos', 'descripcion', 'payload'
    ];
BEGIN
    IF current_setting('app.rol', true) IS DISTINCT FROM 'sistema' THEN
        RAISE EXCEPTION 'Solo el sistema anonimiza los registros abandonados'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    -- Registros en linea que nunca se pagaron: cerrados sin familia ni pago recibido.
    v_solicitudes := ARRAY(
        SELECT id FROM solicitudes_afiliacion
        WHERE estado = 'cancelada' AND familia_id IS NULL AND pagada_en IS NULL
          AND anonimizada_en IS NULL AND created_at < p_antes
    );
    IF cardinality(v_solicitudes) = 0 THEN
        RETURN 0;
    END IF;
    v_referencias := ARRAY(
        SELECT referencia_pago FROM solicitudes_afiliacion WHERE id = ANY (v_solicitudes)
        UNION SELECT jsonb_array_elements_text(referencias_anteriores)
              FROM solicitudes_afiliacion WHERE id = ANY (v_solicitudes)
    );
    v_tareas := ARRAY(SELECT 'registro_sin_pago:' || s::text FROM unnest(v_solicitudes) s);
    -- El interesado que creo el registro, si no avanzo ni se le contacto desde entonces: uno
    -- que llego por otro canal o siguio en conversacion se conserva.
    v_interesados := ARRAY(
        SELECT DISTINCT i.id
        FROM solicitudes_afiliacion s
        JOIN interesados i
          ON i.telefono = s.contacto_telefono OR i.email = lower(s.contacto_email)
        WHERE s.id = ANY (v_solicitudes)
          AND i.familia_id IS NULL AND i.origen = 'afiliacion'
          AND i.etapa IN ('nuevo', 'en_afiliacion')
          AND coalesce(i.ultimo_contacto, i.created_at) < p_antes
    );

    DELETE FROM conversaciones_comerciales WHERE interesado_id = ANY (v_interesados);
    UPDATE interesados SET nombre = NULL, telefono = NULL, email = NULL, datos = '{}'
    WHERE id = ANY (v_interesados);
    UPDATE solicitudes_afiliacion
    SET contacto_nombre = 'Anonimizado', contacto_telefono = v_telefono,
        contacto_email = NULL, aceptacion = aceptacion - v_quitar, anonimizada_en = now()
    WHERE id = ANY (v_solicitudes);
    UPDATE peludos_solicitud SET nombre = 'Mascota' WHERE solicitud_id = ANY (v_solicitudes);
    UPDATE tareas SET descripcion = 'Contacto borrado a los seis meses (Ley 1581)'
    WHERE clave = ANY (v_tareas);
    -- Lo que la pasarela guardo del pagador en los intentos rechazados o anulados.
    UPDATE pagos SET payload = NULL WHERE referencia_externa = ANY (v_referencias);
    UPDATE eventos_pasarela
    SET payload = payload
        #- '{data,transaction,customer_email}' #- '{data,transaction,customer_data}'
        #- '{data,transaction,shipping_address}' #- '{data,transaction,billing_data}'
    WHERE referencia = ANY (v_referencias);

    -- El rastro en la bitacora, incluido el que acaba de dejar esta misma funcion.
    v_ids := ARRAY(
        SELECT s::text FROM unnest(v_solicitudes) s
        UNION SELECT id::text FROM peludos_solicitud WHERE solicitud_id = ANY (v_solicitudes)
        UNION SELECT i::text FROM unnest(v_interesados) i
        UNION SELECT id::text FROM tareas WHERE clave = ANY (v_tareas)
        UNION SELECT id::text FROM pagos WHERE referencia_externa = ANY (v_referencias)
    );
    UPDATE auditoria a
    SET cambios = (
        SELECT jsonb_object_agg(
            e.k, CASE WHEN e.k = ANY (v_personales) THEN jsonb_build_array(v_anonimo, v_anonimo)
                      ELSE e.v END)
        FROM jsonb_each(a.cambios) AS e(k, v)
    )
    WHERE a.entidad IN (
            'solicitudes_afiliacion', 'peludos_solicitud', 'interesados', 'tareas', 'pagos'
          )
      AND a.entidad_id = ANY (v_ids)
      AND EXISTS (SELECT 1 FROM jsonb_object_keys(a.cambios) AS k WHERE k = ANY (v_personales));
    RETURN cardinality(v_solicitudes);
END
$$
"""


def upgrade() -> None:
    op.add_column(
        "solicitudes_afiliacion",
        sa.Column(
            "referencias_anteriores",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    # El valor por defecto lo pone el modelo: el del servidor solo rellena las filas que ya hay.
    op.alter_column("solicitudes_afiliacion", "referencias_anteriores", server_default=None)
    op.add_column(
        "solicitudes_afiliacion",
        sa.Column("anonimizada_en", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(_ANONIMIZAR_ABANDONADOS)
    op.execute("REVOKE ALL ON FUNCTION anonimizar_registros_abandonados(timestamptz) FROM PUBLIC")
    op.execute(
        "GRANT EXECUTE ON FUNCTION anonimizar_registros_abandonados(timestamptz) TO timu_app"
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION anonimizar_registros_abandonados(timestamptz)")
    op.drop_column("solicitudes_afiliacion", "anonimizada_en")
    op.drop_column("solicitudes_afiliacion", "referencias_anteriores")

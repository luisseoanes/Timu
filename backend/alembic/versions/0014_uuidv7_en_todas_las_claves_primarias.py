"""uuidv7 en todas las claves primarias

Toda clave primaria pasa a UUIDv7 (RFC 9562): la base la genera por defecto con uuidv7() y
un CHECK rechaza cualquier otra version. Los IDs que ya existen se reescriben:

1. Cada id que no es v7 recibe uno nuevo con el instante de su created_at, asi que el orden
   cronologico se conserva.
2. Las llaves foraneas pasan un momento a ON UPDATE CASCADE para que los hijos sigan al
   padre, y despues vuelven exactamente a su definicion original.
3. Los IDs escritos como texto (auditoria.entidad_id, claves de idempotencia de tareas,
   contexto de las consultas de IA) o dentro de JSON (auditoria.cambios, eventos del
   outbox, snapshot de carnets) se reemplazan por los nuevos. Solo se toca un UUID si es un
   id reescrito: un UUID ajeno (de un tercero, una clave de almacenamiento) no cambia.
4. Los codigos de un solo uso pendientes caducan: su hash incluye el id, asi que con el id
   nuevo ya no se podrian validar. Las sesiones conservan su refresh token (el hash no
   depende del id); un access token emitido antes deja de valer y se renueva solo.

El downgrade quita el CHECK y el default, pero no devuelve los IDs v4: no hay forma de
recuperarlos ni motivo para hacerlo, y un v7 es un UUID valido para cualquier version.

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-04 19:00:00
"""

from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

_UUID = "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"

# Tablas con clave primaria `id` uuid: las 64 del esquema en esta revision.
_TABLAS_CON_ID = """
    SELECT c.relname
    FROM pg_class c
    JOIN pg_constraint k ON k.conrelid = c.oid AND k.contype = 'p'
    JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = k.conkey[1]
    WHERE c.relnamespace = 'public'::regnamespace
      AND array_length(k.conkey, 1) = 1
      AND a.attname = 'id'
      AND a.atttypid = 'uuid'::regtype
    ORDER BY c.relname
"""


def upgrade() -> None:
    op.execute(
        "CREATE TEMP TABLE _mapa_ids (viejo uuid PRIMARY KEY, nuevo uuid NOT NULL UNIQUE)"
        " ON COMMIT DROP"
    )
    op.execute(
        f"""
        DO $$
        DECLARE t text;
        BEGIN
            FOR t IN {_TABLAS_CON_ID} LOOP
                EXECUTE format(
                    'INSERT INTO _mapa_ids'
                    ' SELECT id, uuidv7(created_at - clock_timestamp()) FROM %I'
                    ' WHERE uuid_extract_version(id) IS DISTINCT FROM 7',
                    t
                );
            END LOOP;
        END
        $$
        """
    )

    # Llaves foraneas en cascada mientras se reescriben los padres.
    op.execute(
        "CREATE TEMP TABLE _fks ON COMMIT DROP AS"
        " SELECT conrelid::regclass::text AS tabla, conname, pg_get_constraintdef(oid) AS def"
        " FROM pg_constraint"
        " WHERE contype = 'f' AND connamespace = 'public'::regnamespace"
    )
    op.execute(
        """
        DO $$
        DECLARE f record;
        BEGIN
            FOR f IN SELECT * FROM _fks LOOP
                EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I', f.tabla, f.conname);
                EXECUTE format(
                    'ALTER TABLE %s ADD CONSTRAINT %I %s ON UPDATE CASCADE',
                    f.tabla, f.conname, f.def
                );
            END LOOP;
        END
        $$
        """
    )
    op.execute(
        f"""
        DO $$
        DECLARE t text;
        BEGIN
            FOR t IN {_TABLAS_CON_ID} LOOP
                EXECUTE format(
                    'UPDATE %I x SET id = m.nuevo FROM _mapa_ids m WHERE x.id = m.viejo', t
                );
            END LOOP;
        END
        $$
        """
    )
    op.execute(
        """
        DO $$
        DECLARE f record;
        BEGIN
            FOR f IN SELECT * FROM _fks LOOP
                EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I', f.tabla, f.conname);
                EXECUTE format('ALTER TABLE %s ADD CONSTRAINT %I %s', f.tabla, f.conname, f.def);
            END LOOP;
        END
        $$
        """
    )

    # IDs escritos como texto o dentro de JSON.
    op.execute(
        f"""
        CREATE FUNCTION pg_temp.remapear(texto text) RETURNS text LANGUAGE plpgsql AS $$
        DECLARE
            u text;
            nuevo_txt text;
            salida text := texto;
        BEGIN
            FOR u IN SELECT DISTINCT m[1] FROM regexp_matches(texto, '({_UUID})', 'g') m LOOP
                SELECT nuevo::text INTO nuevo_txt FROM _mapa_ids WHERE viejo = u::uuid;
                IF FOUND THEN
                    salida := replace(salida, u, nuevo_txt);
                END IF;
            END LOOP;
            RETURN salida;
        END
        $$
        """
    )
    op.execute(
        f"""
        DO $$
        DECLARE c record;
        BEGIN
            FOR c IN
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND data_type IN ('character varying', 'text', 'jsonb')
                  AND table_name <> 'alembic_version'
                  -- Direccion de un objeto en el almacenamiento: opaca, no un id nuestro.
                  AND (table_name, column_name) <> ('archivos', 'clave')
            LOOP
                EXECUTE format(
                    'UPDATE %I SET %I = pg_temp.remapear(%I::text)::%s WHERE %I::text ~ %L',
                    c.table_name, c.column_name, c.column_name,
                    CASE c.data_type WHEN 'jsonb' THEN 'jsonb' ELSE 'text' END,
                    c.column_name, '{_UUID}'
                );
            END LOOP;
        END
        $$
        """
    )
    op.execute(
        "UPDATE tokens_uso_unico SET expira_en = LEAST(expira_en, now())"
        " WHERE usado_en IS NULL AND id IN (SELECT nuevo FROM _mapa_ids)"
    )

    # El estandar a partir de ahora: generado por la base y exigido por un CHECK.
    op.execute(
        f"""
        DO $$
        DECLARE t text;
        BEGIN
            FOR t IN {_TABLAS_CON_ID} LOOP
                EXECUTE format('ALTER TABLE %I ALTER COLUMN id SET DEFAULT uuidv7()', t);
                EXECUTE format(
                    'ALTER TABLE %I ADD CONSTRAINT %I CHECK (uuid_extract_version(id) = 7)',
                    t, 'ck_' || t || '_id_uuidv7'
                );
            END LOOP;
        END
        $$
        """
    )


def downgrade() -> None:
    op.execute(
        f"""
        DO $$
        DECLARE t text;
        BEGIN
            FOR t IN {_TABLAS_CON_ID} LOOP
                EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I', t, 'ck_' || t || '_id_uuidv7');
                EXECUTE format('ALTER TABLE %I ALTER COLUMN id DROP DEFAULT', t);
            END LOOP;
        END
        $$
        """
    )

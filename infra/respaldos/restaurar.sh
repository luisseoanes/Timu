#!/bin/sh
# F0-07 Restauracion probada con evidencia.
#
# Uso: restaurar.sh <archivo.dump | s3://bucket/respaldos/archivo.dump> <base_destino>
#
# Restaura en una base NUEVA (nunca sobre la de produccion), compara el numero de filas de
# cada tabla con el reporte generado al respaldar y deja un informe de evidencia.
# Variables de conexion: PGHOST PGPORT PGUSER PGPASSWORD. Base de origen para comparar:
# ORIGEN_DB (opcional; si no se da, solo se reportan los conteos restaurados).
set -eu

FUENTE="$1"
DESTINO="$2"
DIR="${RESPALDO_DIR:-/respaldos}"
INFORME="$DIR/restauracion-${DESTINO}-$(date -u +%Y%m%dT%H%M%SZ).txt"

case "$FUENTE" in
  s3://*)
    ENDPOINT=""
    [ -n "${S3_ENDPOINT_URL:-}" ] && ENDPOINT="--endpoint-url $S3_ENDPOINT_URL"
    LOCAL="$DIR/$(basename "$FUENTE")"
    # shellcheck disable=SC2086
    aws s3 cp $ENDPOINT "$FUENTE" "$LOCAL"
    # shellcheck disable=SC2086
    aws s3 cp $ENDPOINT "$FUENTE.sha256" "$LOCAL.sha256"
    FUENTE="$LOCAL"
    ;;
esac

if [ -f "$FUENTE.sha256" ]; then
  (cd "$(dirname "$FUENTE")" && sha256sum -c "$(basename "$FUENTE").sha256")
fi

if psql -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DESTINO'" | grep -q 1; then
  echo "La base $DESTINO ya existe: restaure siempre en una base nueva" >&2
  exit 1
fi

# El rol de la aplicacion es del cluster, no de la base: pg_dump no lo lleva, y las politicas
# y los GRANT del respaldo lo nombran. En un servidor nuevo se crea como en la migracion 0013,
# con los limites de la 0024; `inicializar` le da LOGIN y clave al arrancar.
# test_restaurar_crea_el_rol_como_las_migraciones vigila que esto no se separe de ellas.
psql -d postgres -v ON_ERROR_STOP=1 -q <<'SQL'
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'timu_app') THEN
    CREATE ROLE timu_app NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
    ALTER ROLE timu_app SET statement_timeout = '30s';
    ALTER ROLE timu_app SET lock_timeout = '10s';
    ALTER ROLE timu_app SET idle_in_transaction_session_timeout = '60s';
  END IF;
END $$;
SQL

INICIO=$(date +%s)
createdb "$DESTINO"
pg_restore --no-owner --exit-on-error --dbname="$DESTINO" "$FUENTE"
DURACION=$(( $(date +%s) - INICIO ))

# Lo que protege los datos tambien se restaura: permisos de timu_app por tabla, RLS y sus
# politicas, triggers y permisos por defecto. Contar filas no basta: una base sin los GRANT
# tiene todas las filas y la aplicacion no puede leer ninguna.
SEGURIDAD="SELECT 'permisos', md5(string_agg(c.relname || ':' || concat_ws(',',
              CASE WHEN has_table_privilege('timu_app', c.oid, 'SELECT') THEN 'S' END,
              CASE WHEN has_table_privilege('timu_app', c.oid, 'INSERT') THEN 'I' END,
              CASE WHEN has_table_privilege('timu_app', c.oid, 'UPDATE') THEN 'U' END,
              CASE WHEN has_table_privilege('timu_app', c.oid, 'DELETE') THEN 'D' END),
              ';' ORDER BY c.relname))
           FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE n.nspname = 'public' AND c.relkind = 'r'
           UNION ALL
           SELECT 'politicas', count(*) || ' ' || md5(string_agg(tablename || ':' || policyname
              || ':' || cmd || ':' || coalesce(qual, '') || ':' || coalesce(with_check, ''),
              ';' ORDER BY tablename, policyname))
           FROM pg_policies WHERE schemaname = 'public'
           UNION ALL
           SELECT 'tablas_con_rls', count(*)::text FROM pg_class c
           JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relrowsecurity
           UNION ALL
           SELECT 'triggers', count(*)::text FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
           JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE n.nspname = 'public' AND NOT t.tgisinternal
           UNION ALL
           SELECT 'permisos_por_defecto', count(*)::text FROM pg_default_acl
           UNION ALL
           SELECT 'timu_app_lee_familias',
              has_table_privilege('timu_app', 'public.familias', 'SELECT')::text"

CONTEO="SELECT table_name, (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from public.%I', table_name), false, true, '')))[1]::text::int
        FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY 1"

{
  echo "Restauracion de $(basename "$FUENTE") en $DESTINO"
  echo "Fecha: $(date -u +%FT%TZ)  Duracion: ${DURACION}s  Servidor: ${PGHOST:-local}"
  echo "Version de esquema: $(psql -d "$DESTINO" -tAc 'SELECT version_num FROM alembic_version')"
  echo
  echo "tabla|filas_restauradas${ORIGEN_DB:+|filas_origen|coincide}"
} > "$INFORME"

psql -d "$DESTINO" -tA -F'|' -c "$CONTEO" > "$DIR/.destino"
DIFERENCIAS=0
if [ -n "${ORIGEN_DB:-}" ]; then
  psql -d "$ORIGEN_DB" -tA -F'|' -c "$CONTEO" > "$DIR/.origen"
  while IFS='|' read -r tabla filas; do
    origen=$(grep "^$tabla|" "$DIR/.origen" | cut -d'|' -f2)
    if [ "$filas" = "$origen" ]; then ok=si; else ok=NO; DIFERENCIAS=$((DIFERENCIAS + 1)); fi
    echo "$tabla|$filas|$origen|$ok" >> "$INFORME"
  done < "$DIR/.destino"
  rm -f "$DIR/.origen"
else
  cat "$DIR/.destino" >> "$INFORME"
fi
rm -f "$DIR/.destino"

echo >> "$INFORME"
echo "seguridad|restaurada${ORIGEN_DB:+|origen|coincide}" >> "$INFORME"
psql -d "$DESTINO" -tA -F'|' -c "$SEGURIDAD" > "$DIR/.destino"
if [ -n "${ORIGEN_DB:-}" ]; then
  psql -d "$ORIGEN_DB" -tA -F'|' -c "$SEGURIDAD" > "$DIR/.origen"
fi
while IFS='|' read -r aspecto valor; do
  if [ -n "${ORIGEN_DB:-}" ]; then
    origen=$(grep "^$aspecto|" "$DIR/.origen" | cut -d'|' -f2)
    if [ "$valor" = "$origen" ]; then ok=si; else ok=NO; DIFERENCIAS=$((DIFERENCIAS + 1)); fi
    echo "$aspecto|$valor|$origen|$ok" >> "$INFORME"
  else
    echo "$aspecto|$valor" >> "$INFORME"
  fi
done < "$DIR/.destino"
# Sin base de origen con que comparar, al menos la aplicacion tiene que poder leer.
if ! grep -q '^timu_app_lee_familias|true$' "$DIR/.destino"; then
  DIFERENCIAS=$((DIFERENCIAS + 1))
  echo "timu_app no puede leer la base restaurada: faltan los permisos" >> "$INFORME"
fi
rm -f "$DIR/.destino" "$DIR/.origen"

echo >> "$INFORME"
if [ "$DIFERENCIAS" -eq 0 ]; then
  echo "RESULTADO: restauracion completa y verificada" >> "$INFORME"
else
  echo "RESULTADO: $DIFERENCIAS diferencias (filas o seguridad)" >> "$INFORME"
fi
cat "$INFORME"
[ "$DIFERENCIAS" -eq 0 ]

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

INICIO=$(date +%s)
createdb "$DESTINO"
pg_restore --no-owner --no-privileges --exit-on-error --dbname="$DESTINO" "$FUENTE"
DURACION=$(( $(date +%s) - INICIO ))

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
if [ "$DIFERENCIAS" -eq 0 ]; then
  echo "RESULTADO: restauracion completa y verificada" >> "$INFORME"
else
  echo "RESULTADO: $DIFERENCIAS tablas con diferencias" >> "$INFORME"
fi
cat "$INFORME"
[ "$DIFERENCIAS" -eq 0 ]

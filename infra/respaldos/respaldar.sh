#!/bin/sh
# F0-07 Respaldo de PostgreSQL: dump comprimido, copia fuera del servidor y retencion local.
#
# Variables: PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE
#            RESPALDO_DIR (defecto /respaldos)  RETENCION_DIAS (defecto 7)
#            S3_BUCKET S3_ENDPOINT_URL AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY (opcionales)
set -eu

DIR="${RESPALDO_DIR:-/respaldos}"
RETENCION="${RETENCION_DIAS:-7}"
MARCA="$(date -u +%Y%m%dT%H%M%SZ)"
ARCHIVO="$DIR/timu-${PGDATABASE}-${MARCA}.dump"

mkdir -p "$DIR"
echo "[$(date -u +%FT%TZ)] Respaldo de ${PGDATABASE} en ${PGHOST}"

# Formato custom: comprimido y restaurable por tabla con pg_restore.
pg_dump --format=custom --compress=9 --no-owner --no-privileges --file="$ARCHIVO.parcial"
mv "$ARCHIVO.parcial" "$ARCHIVO"
sha256sum "$ARCHIVO" > "$ARCHIVO.sha256"
echo "Respaldo local: $ARCHIVO ($(du -h "$ARCHIVO" | cut -f1))"

if [ -n "${S3_BUCKET:-}" ]; then
  ENDPOINT=""
  [ -n "${S3_ENDPOINT_URL:-}" ] && ENDPOINT="--endpoint-url $S3_ENDPOINT_URL"
  # shellcheck disable=SC2086
  aws s3 cp $ENDPOINT "$ARCHIVO" "s3://$S3_BUCKET/respaldos/$(basename "$ARCHIVO")"
  # shellcheck disable=SC2086
  aws s3 cp $ENDPOINT "$ARCHIVO.sha256" "s3://$S3_BUCKET/respaldos/$(basename "$ARCHIVO").sha256"
  echo "Copia remota: s3://$S3_BUCKET/respaldos/$(basename "$ARCHIVO")"
else
  echo "ADVERTENCIA: S3_BUCKET vacio; el respaldo solo queda en este servidor" >&2
fi

# La retencion remota se define con una regla de ciclo de vida en el bucket.
find "$DIR" -name 'timu-*.dump*' -mtime +"$RETENCION" -print -delete
echo "[$(date -u +%FT%TZ)] Respaldo terminado"

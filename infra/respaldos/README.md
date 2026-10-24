# Respaldo y restauración (F0-07)

El servicio `respaldos` de `docker-compose.yml` corre `respaldar.sh` todos los días a las
2:00 a.m. (hora de Colombia):

1. `pg_dump` en formato custom comprimido, con su suma SHA-256.
2. Copia a almacenamiento S3 compatible (AWS S3 o DigitalOcean Spaces) si `RESPALDO_BUCKET` está
   definido. Sin bucket, el script avisa: un respaldo que solo vive en el mismo servidor no
   protege contra la pérdida del servidor.
3. Borra las copias locales con más de `RETENCION_DIAS` (7 por defecto). La retención
   remota se configura con una regla de ciclo de vida en el bucket (recomendado: 30 diarios).

Respaldo manual:

```bash
docker compose exec respaldos respaldar.sh
```

## Restauración probada

Restaura siempre en una base **nueva** y compara filas por tabla contra la base de origen:

```bash
docker compose exec -e ORIGEN_DB=timu respaldos \
  restaurar.sh s3://<bucket>/respaldos/timu-timu-<marca>.dump timu_prueba_restauracion
```

El informe queda en `/respaldos/restauracion-<base>-<marca>.txt` y termina con
`RESULTADO: restauracion completa y verificada`. Ese archivo es la evidencia que exige el
criterio de aceptación: debe generarse en el ambiente de pruebas antes de cada salida a
producción y guardarse con el acta de la fase.

Para volver a producción desde un respaldo: detener `api`, `worker` y `beat`, restaurar en
una base nueva, verificar el informe, apuntar `POSTGRES_DB` a la base restaurada y
levantar los servicios.

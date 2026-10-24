# F0-07 Contenedor de respaldos: cliente de PostgreSQL 16 + AWS CLI (S3 compatible) + cron.
FROM postgres:16-alpine

RUN apk add --no-cache aws-cli tzdata

ENV TZ=America/Bogota
COPY respaldar.sh restaurar.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/respaldar.sh /usr/local/bin/restaurar.sh \
    && echo "${RESPALDO_CRON:-0 2 * * *} /usr/local/bin/respaldar.sh >> /proc/1/fd/1 2>&1" \
       > /etc/crontabs/root

# crond en primer plano; el respaldo diario corre a las 2:00 a.m. hora de Colombia.
CMD ["crond", "-f", "-l", "8"]

"""Puesta a punto del entorno de desarrollo: lo que corre el servicio `inicializar` de
docker compose antes de arrancar api, worker y beat.

Aplica las migraciones, da LOGIN al rol de la aplicacion, carga los catalogos, crea el
usuario administrador y el bucket de adjuntos en el almacenamiento S3. Cada paso es
idempotente, asi que repetir `docker compose up` no duplica nada. Solo para desarrollo: en
produccion las migraciones son un paso del despliegue y el bucket lo aprovisiona quien
administra la cuenta.

Uso: docker compose run --rm inicializar   (o python -m scripts.inicializar)
"""

import asyncio

from sqlalchemy import create_engine, text

from alembic import command
from alembic.config import Config
from app.core.config import settings
from app.core.database import habilitar_rol_aplicacion
from app.integrations.storage import asegurar_bucket
from scripts import cargar_catalogos, seed


def main() -> None:
    print("Migraciones: alembic upgrade head")
    command.upgrade(Config("alembic.ini"), "head")
    print("Rol de la aplicacion")
    propietario = create_engine(settings.DATABASE_URL_PROPIETARIO.replace("+asyncpg", "+psycopg"))
    with propietario.begin() as conexion:
        habilitar_rol_aplicacion(conexion, settings.APP_DB_PASSWORD)
        # Estadisticas de consultas (el compose la precarga en `db`). En produccion la crea
        # quien administra la base: exige superusuario.
        conexion.execute(text("CREATE EXTENSION IF NOT EXISTS pg_stat_statements"))
    propietario.dispose()
    print("Catalogos y reglas")
    cargar_catalogos.main()
    print("Usuario administrador y planes de ejemplo")
    asyncio.run(seed.main())
    print("Bucket de adjuntos")
    asegurar_bucket()
    print("Inicializacion terminada")


if __name__ == "__main__":
    main()

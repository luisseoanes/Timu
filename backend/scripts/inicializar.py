"""Puesta a punto del entorno de desarrollo: lo que corre el servicio `inicializar` de
docker compose antes de arrancar api, worker y beat.

Aplica las migraciones, carga los catalogos, crea el usuario administrador y el bucket
de adjuntos en MinIO. Cada paso es idempotente, asi que repetir `docker compose up` no
duplica nada. Solo para desarrollo: en produccion las migraciones son un paso del
despliegue y el bucket lo aprovisiona quien administra la cuenta.

Uso: docker compose run --rm inicializar   (o python -m scripts.inicializar)
"""

import asyncio

from alembic import command
from alembic.config import Config
from app.integrations.storage import asegurar_bucket
from scripts import cargar_catalogos, seed


def main() -> None:
    print("Migraciones: alembic upgrade head")
    command.upgrade(Config("alembic.ini"), "head")
    print("Catalogos y reglas")
    cargar_catalogos.main()
    print("Usuario administrador y planes de ejemplo")
    asyncio.run(seed.main())
    print("Bucket de adjuntos")
    asegurar_bucket()
    print("Inicializacion terminada")


if __name__ == "__main__":
    main()

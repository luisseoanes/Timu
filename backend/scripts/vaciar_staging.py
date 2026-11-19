"""Vacia staging para volver a sembrarlo: borra el esquema `public` de la base y los adjuntos
del bucket. Despues, `inicializar` rehace el esquema desde la primera migracion, y
`datos_demo` y `operacion_demo` lo siembran (docs/despliegue-staging.md).

Solo en staging, y pidiendo el nombre del ambiente para que no se corra por descuido:
    python -m scripts.vaciar_staging --confirmar staging

En local no hace falta: `docker compose down -v` borra la base y el almacenamiento. El rol
`timu_app` es del cluster y sobrevive; la migracion 0013 lo reutiliza.
"""

import argparse

from sqlalchemy import create_engine, text

from app.core.config import Settings, settings
from app.integrations.storage import _cliente

AMBIENTE = "staging"


def comprobar(ajustes: Settings, confirmar: str | None) -> None:
    """Se niega fuera de staging o sin la confirmacion escrita."""
    if ajustes.ENVIRONMENT != AMBIENTE:
        raise SystemExit(f"vaciar_staging solo corre en staging, no en {ajustes.ENVIRONMENT}")
    if confirmar != AMBIENTE:
        raise SystemExit(f"Para vaciar staging hay que pasar --confirmar {AMBIENTE}")


def vaciar_base() -> None:
    propietario = create_engine(settings.DATABASE_URL_PROPIETARIO.replace("+asyncpg", "+psycopg"))
    with propietario.begin() as conexion:
        conexion.execute(text("DROP SCHEMA public CASCADE"))
        conexion.execute(text("CREATE SCHEMA public"))
    propietario.dispose()


def vaciar_bucket() -> int:
    cliente = _cliente()
    borrados = 0
    for pagina in cliente.get_paginator("list_objects_v2").paginate(Bucket=settings.STORAGE_BUCKET):
        claves = [{"Key": o["Key"]} for o in pagina.get("Contents", [])]
        if claves:
            cliente.delete_objects(Bucket=settings.STORAGE_BUCKET, Delete={"Objects": claves})
            borrados += len(claves)
    return borrados


def main() -> None:
    argumentos = argparse.ArgumentParser(description="Vacia la base y el bucket de staging")
    argumentos.add_argument("--confirmar", help="el nombre del ambiente: staging")
    comprobar(settings, argumentos.parse_args().confirmar)
    print("Base: se borra el esquema public")
    vaciar_base()
    print(f"Bucket {settings.STORAGE_BUCKET}: {vaciar_bucket()} adjuntos borrados")
    print("Listo. Sigue `python -m scripts.inicializar` (o un despliegue de la API) y el seed.")


if __name__ == "__main__":
    main()

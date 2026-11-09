"""Seed inicial: crea el usuario administrador y un par de planes de ejemplo.

En un ambiente desplegado no hay clave de desarrollo ni planes de ejemplo: el administrador
se crea con ADMIN_PASSWORD_INICIAL, y sin ella el script se niega. Una cuenta de
administrador con una clave publicada en el repositorio es una puerta abierta.

Uso: docker compose exec api python -m scripts.seed (despues de scripts.cargar_catalogos)
"""

import asyncio

from sqlalchemy import select

from app.core.config import Settings, settings
from app.core.database import CLAVE_CONTEXTO, SISTEMA, SessionLocal
from app.core.enums import Rol
from app.core.security import hash_password
from app.models import Plan, Usuario

ADMIN_EMAIL = "admin@timu.co"
ADMIN_PASSWORD = "cambiar123"  # noqa: S105  solo en local
MIN_CLAVE_DESPLEGADA = 12


def clave_inicial(ajustes: Settings) -> str:
    """Clave del administrador que crea el seed. Desplegado, solo la que se configure."""
    if not ajustes.es_desplegado:
        return ajustes.ADMIN_PASSWORD_INICIAL or ADMIN_PASSWORD
    if len(ajustes.ADMIN_PASSWORD_INICIAL) < MIN_CLAVE_DESPLEGADA:
        raise SystemExit(
            f"En {ajustes.ENVIRONMENT} el administrador inicial necesita ADMIN_PASSWORD_INICIAL "
            f"de {MIN_CLAVE_DESPLEGADA} caracteres o mas"
        )
    return ajustes.ADMIN_PASSWORD_INICIAL


async def main() -> None:
    clave = clave_inicial(settings)
    async with SessionLocal(info={CLAVE_CONTEXTO: SISTEMA}) as db:
        existente = await db.scalar(select(Usuario).where(Usuario.email == ADMIN_EMAIL))
        if existente is None:
            db.add(
                Usuario(
                    email=ADMIN_EMAIL,
                    nombre="Administrador TIMU",
                    rol=Rol.ADMIN,
                    hashed_password=hash_password(clave),
                )
            )
            print(
                f"Usuario admin creado: {ADMIN_EMAIL}"
                + ("" if settings.es_desplegado else f" / {clave}")
            )

        # Precios inventados: en un ambiente desplegado los planes los define TIMU.
        if not settings.es_desplegado and not await db.scalar(select(Plan).limit(1)):
            db.add_all(
                [
                    Plan(
                        codigo="individual",
                        nombre="Plan Individual",
                        valor_mensual=45000,
                        cupos_mascotas=1,
                    ),
                    Plan(
                        codigo="familiar",
                        nombre="Plan Familiar",
                        valor_mensual=75000,
                        cupos_mascotas=3,
                    ),
                ]
            )
            print("Planes de ejemplo creados")

        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())

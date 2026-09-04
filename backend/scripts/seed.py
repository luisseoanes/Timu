"""Seed inicial: crea el usuario administrador y un par de planes de ejemplo.

Uso: docker compose exec api python scripts_seed.py
"""

import asyncio

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.enums import Rol
from app.core.security import hash_password
from app.models import Plan, Usuario

ADMIN_EMAIL = "admin@timu.co"
ADMIN_PASSWORD = "cambiar123"


async def main() -> None:
    async with SessionLocal() as db:
        existente = await db.scalar(select(Usuario).where(Usuario.email == ADMIN_EMAIL))
        if existente is None:
            db.add(
                Usuario(
                    email=ADMIN_EMAIL,
                    nombre="Administrador TIMU",
                    rol=Rol.ADMIN,
                    hashed_password=hash_password(ADMIN_PASSWORD),
                )
            )
            print(f"Usuario admin creado: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")

        if not await db.scalar(select(Plan).limit(1)):
            db.add_all(
                [
                    Plan(nombre="Plan Individual", valor_mensual=45000, cupos_mascotas=1),
                    Plan(nombre="Plan Familiar", valor_mensual=75000, cupos_mascotas=3),
                ]
            )
            print("Planes de ejemplo creados")

        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())

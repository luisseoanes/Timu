"""F0-09 Carga repetible de catalogos maestros y de las reglas iniciales (F0-12).

Uso: docker compose exec api python -m scripts.cargar_catalogos
"""

import asyncio

from app.core.database import SessionLocal
from app.models import Base  # noqa: F401  registra todos los modelos
from app.modules.catalogos.service import cargar
from app.modules.reglas.service import sembrar


async def main() -> None:
    async with SessionLocal() as db:
        resultado = await cargar(db)
        reglas = await sembrar(db)
        await db.commit()
    for tabla, conteo in resultado.items():
        print(f"{tabla}: {conteo['creados']} creados, {conteo['actualizados']} actualizados")
    print(f"reglas: {reglas} creadas (las existentes no se modifican)")


if __name__ == "__main__":
    asyncio.run(main())

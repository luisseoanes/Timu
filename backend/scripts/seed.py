"""Seed inicial: crea el usuario administrador y, en local, los planes de TIMU.

En un ambiente desplegado no hay clave de desarrollo ni planes de ejemplo: el administrador
se crea con ADMIN_PASSWORD_INICIAL, y sin ella el script se niega. Una cuenta de
administrador con una clave publicada en el repositorio es una puerta abierta.

Uso: docker compose exec api python -m scripts.seed (despues de scripts.cargar_catalogos)
"""

import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.core.database import CLAVE_CONTEXTO, SISTEMA, SessionLocal
from app.core.enums import ColorPlan, Rol
from app.core.security import hash_password
from app.models import Plan, Usuario
from app.modules.planes import service as planes

ADMIN_EMAIL = "admin@timu.co"
ADMIN_PASSWORD = "cambiar123"  # noqa: S105  solo en local
MIN_CLAVE_DESPLEGADA = 12

# Los planes que publica TIMU: (codigo, nombre, color del manual de marca, ciudades, tarifa
# por peludo con 1 a 4 peludos, precio de cada periodo largo para un peludo). El trimestral
# es tentativo. En un ambiente desplegado los da de alta el administrador desde el panel.
PLANES_TIMU = [
    (
        "colita_feliz",
        "Colita Feliz",
        "naranja",
        ["Bogota", "Medellin"],
        ["35500", "30500", "26000", "24000"],
        {"trimestral": "103800", "semestral": "202350", "anual": "378000"},
    ),
    (
        "mi_amigo_fiel",
        "Mi Amigo Fiel",
        "verde",
        ["Bogota", "Medellin"],
        ["69000", "61000", "57500", "57000"],
        {"trimestral": "201800", "semestral": "393300", "anual": "745200"},
    ),
    (
        "amigos_por_siempre",
        "Amigos por Siempre",
        "azul",
        ["Medellin"],
        ["98000", "88000", "83500", "82000"],
        {"trimestral": "286650", "semestral": "558600", "anual": "1058400"},
    ),
]


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

        if not settings.es_desplegado and not await db.scalar(select(Plan).limit(1)):
            await db.run_sync(crear_planes_timu)
            print("Planes de TIMU creados")

        await db.commit()


def crear_planes_timu(db: Session) -> list[Plan]:
    """Por el mismo servicio que usa la API: con sus tarifas y sus ciudades, listos para
    cotizar y afiliar."""
    return [
        planes.crear(
            db,
            {
                "codigo": codigo,
                "nombre": nombre,
                "color": ColorPlan(color),
                "especies": ["canino", "felino"],
                "tarifas": [Decimal(v) for v in por_peludos],
                "tarifas_periodicidad": {k: Decimal(v) for k, v in largos.items()},
                "ciudades": ciudades,
            },
        )
        for codigo, nombre, color, ciudades, por_peludos, largos in PLANES_TIMU
    ]


if __name__ == "__main__":
    asyncio.run(main())

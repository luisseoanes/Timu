"""F0-08 Chequeo de salud de las dependencias: base de datos, Redis y trabajadores Celery."""

import asyncio
from typing import Literal

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = structlog.get_logger(__name__)

Estado = Literal["ok", "falla"]

TIMEOUT_SEGUNDOS = 2.0


async def revisar_db(db: AsyncSession) -> Estado:
    try:
        await asyncio.wait_for(db.execute(text("SELECT 1")), TIMEOUT_SEGUNDOS)
        return "ok"
    except Exception:  # noqa: BLE001
        logger.warning("Salud: base de datos no responde", exc_info=True)
        return "falla"


async def revisar_redis() -> Estado:
    from redis.asyncio import Redis

    cliente = Redis.from_url(
        settings.REDIS_URL, socket_timeout=TIMEOUT_SEGUNDOS, socket_connect_timeout=TIMEOUT_SEGUNDOS
    )
    try:
        await cliente.ping()
        return "ok"
    except Exception:  # noqa: BLE001
        logger.warning("Salud: Redis no responde", exc_info=True)
        return "falla"
    finally:
        await cliente.aclose()


async def revisar_trabajadores() -> Estado:
    from app.workers.celery_app import celery_app

    try:
        respuestas = await asyncio.wait_for(
            asyncio.to_thread(celery_app.control.ping, timeout=1.0), TIMEOUT_SEGUNDOS + 1
        )
        return "ok" if respuestas else "falla"
    except Exception:  # noqa: BLE001
        logger.warning("Salud: sin respuesta de los trabajadores", exc_info=True)
        return "falla"

"""F0-06 Limite de peticiones por ventana fija de un minuto.

Redis en ambientes desplegados (compartido entre replicas); memoria en local y pruebas.
Si Redis no responde, se deja pasar la peticion y se registra: un limitador caido no
puede tumbar la operacion.
"""

import time
from typing import Protocol

import structlog

logger = structlog.get_logger(__name__)

VENTANA_SEGUNDOS = 60


class Contador(Protocol):
    async def incrementar(self, clave: str) -> int: ...


class ContadorMemoria:
    def __init__(self) -> None:
        self._ventana = 0
        self._conteos: dict[str, int] = {}

    async def incrementar(self, clave: str) -> int:
        ventana = int(time.time() // VENTANA_SEGUNDOS)
        if ventana != self._ventana:
            self._ventana, self._conteos = ventana, {}
        self._conteos[clave] = self._conteos.get(clave, 0) + 1
        return self._conteos[clave]

    def reiniciar(self) -> None:
        self._conteos.clear()


class ContadorRedis:
    def __init__(self, url: str) -> None:
        from redis.asyncio import Redis

        self._redis = Redis.from_url(url, socket_timeout=0.5, socket_connect_timeout=0.5)

    async def incrementar(self, clave: str) -> int:
        ventana = int(time.time() // VENTANA_SEGUNDOS)
        k = f"rl:{clave}:{ventana}"
        try:
            async with self._redis.pipeline(transaction=True) as pipe:
                total, _ = await pipe.incr(k).expire(k, VENTANA_SEGUNDOS).execute()
            return int(total)
        except Exception:  # noqa: BLE001
            logger.warning("Limitador sin Redis; peticion permitida", exc_info=True)
            return 0


def segundos_para_reinicio() -> int:
    return VENTANA_SEGUNDOS - int(time.time()) % VENTANA_SEGUNDOS

"""Cache con vencimiento para consultas costosas (F4-DAS-02).

Redis en ambientes desplegados, compartida entre replicas; memoria en local y pruebas.
Si Redis no responde, se calcula de nuevo: una cache caida no puede tumbar el panel.
"""

import json
import time
from collections.abc import Callable
from typing import Any

import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class CacheMemoria:
    def __init__(self) -> None:
        self._datos: dict[str, tuple[float, str]] = {}

    def leer(self, clave: str) -> str | None:
        valor = self._datos.get(clave)
        if valor is None or valor[0] < time.monotonic():
            self._datos.pop(clave, None)
            return None
        return valor[1]

    def guardar(self, clave: str, valor: str, segundos: int) -> None:
        self._datos[clave] = (time.monotonic() + segundos, valor)

    def limpiar(self, prefijo: str = "") -> None:
        for clave in [k for k in self._datos if k.startswith(prefijo)]:
            del self._datos[clave]


class CacheRedis:
    def __init__(self, url: str) -> None:
        from redis import Redis

        self._redis = Redis.from_url(url, socket_timeout=0.5, socket_connect_timeout=0.5)

    def leer(self, clave: str) -> str | None:
        try:
            valor = self._redis.get(clave)
        except Exception:  # noqa: BLE001
            logger.warning("Cache sin Redis; se recalcula", exc_info=True)
            return None
        if isinstance(valor, bytes):
            return valor.decode()
        return valor if isinstance(valor, str) else None

    def guardar(self, clave: str, valor: str, segundos: int) -> None:
        try:
            self._redis.setex(clave, segundos, valor)
        except Exception:  # noqa: BLE001
            logger.warning("Cache sin Redis; no se guarda", exc_info=True)

    def limpiar(self, prefijo: str = "") -> None:
        try:
            for clave in self._redis.scan_iter(f"{prefijo}*"):
                self._redis.delete(clave)
        except Exception:  # noqa: BLE001
            logger.warning("Cache sin Redis; no se limpia", exc_info=True)


_cache: CacheMemoria | CacheRedis | None = None


def obtener() -> CacheMemoria | CacheRedis:
    global _cache
    if _cache is None:
        _cache = CacheRedis(settings.REDIS_URL) if settings.es_desplegado else CacheMemoria()
    return _cache


def memorizar(clave: str, segundos: int, calcular: Callable[[], Any]) -> Any:
    """Devuelve lo cacheado o lo calcula y lo guarda. El valor debe ser serializable a
    JSON (se usa `default=str` para fechas y decimales)."""
    cache = obtener()
    guardado = cache.leer(clave)
    if guardado is not None:
        return json.loads(guardado)
    valor = calcular()
    # Ida y vuelta por JSON: lo que se devuelve es igual venga o no de la cache.
    serializado = json.dumps(valor, default=str)
    cache.guardar(clave, serializado, segundos)
    return json.loads(serializado)

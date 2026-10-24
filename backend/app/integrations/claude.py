"""F4-IAA-01 Unico punto de contacto con la API de Claude.

Ningun modulo importa el SDK de Anthropic: todos pasan por `app.modules.ia.service`,
que agrega el prompt versionado, el limite de gasto y el registro de cada consulta, y
que llama a `completar` de este modulo.

Es sincrono a proposito: las consultas corren en el worker de Celery (respuestas del
bot, borradores, evaluaciones), nunca dentro de un endpoint async.
"""

from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from typing import Any

import anthropic
from anthropic.types.beta import BetaOutputConfigParam, BetaTextBlockParam

from app.core.config import settings

# USD por millon de tokens: entrada, salida. La lectura de cache cuesta 0,1x la entrada y
# la escritura 1,25x (TTL de 5 minutos).
PRECIOS: dict[str, tuple[Decimal, Decimal]] = {
    "claude-opus-5-5": (Decimal("4"), Decimal("20")),
    "claude-opus-5": (Decimal("5"), Decimal("25")),
    "claude-opus-4-8": (Decimal("5"), Decimal("25")),
    "claude-sonnet-5-5": (Decimal("2"), Decimal("10")),
    "claude-haiku-5-5": (Decimal("0.10"), Decimal("0.50")),
}
PRECIO_DESCONOCIDO = (Decimal("10"), Decimal("50"))  # se asume el mas caro: nunca subestimar
MILLON = Decimal(1_000_000)


class ErrorIA(Exception):
    """Fallo del proveedor (red, limite de peticiones, error del servidor)."""


@dataclass
class Uso:
    entrada: int = 0
    salida: int = 0
    cache_lectura: int = 0
    cache_escritura: int = 0


@dataclass
class Respuesta:
    texto: str
    modelo: str
    uso: Uso
    rechazada: bool
    request_id: str | None


def costo(modelo: str, uso: Uso) -> Decimal:
    entrada, salida = PRECIOS.get(modelo, PRECIO_DESCONOCIDO)
    total = (
        uso.entrada * entrada
        + uso.salida * salida
        + uso.cache_lectura * entrada * Decimal("0.1")
        + uso.cache_escritura * entrada * Decimal("1.25")
    )
    return (total / MILLON).quantize(Decimal("0.000001"))


def configurado() -> bool:
    return bool(settings.ANTHROPIC_API_KEY)


@lru_cache
def _cliente() -> anthropic.Anthropic:
    return anthropic.Anthropic(
        api_key=settings.ANTHROPIC_API_KEY, timeout=settings.IA_TIMEOUT_SEGUNDOS, max_retries=2
    )


def completar(
    sistema: str,
    entrada: str,
    *,
    esquema: dict[str, Any] | None = None,
    max_tokens: int = 2000,
    effort: str = "low",
) -> Respuesta:
    """Una consulta. El prompt de sistema es estable por version y va cacheado; con
    `esquema` la respuesta es JSON valido contra ese JSON Schema.

    Si los clasificadores de seguridad declinan, `fallbacks: "default"` reintenta en el
    servidor con el modelo de respaldo que corresponda; si toda la cadena declina, la
    respuesta llega marcada como rechazada.
    """
    output_config: BetaOutputConfigParam = {"effort": effort}  # type: ignore[typeddict-item]
    if esquema is not None:
        output_config["format"] = {"type": "json_schema", "schema": esquema}
    sistema_cacheado: list[BetaTextBlockParam] = [
        {"type": "text", "text": sistema, "cache_control": {"type": "ephemeral"}}
    ]
    try:
        respuesta = _cliente().beta.messages.create(
            model=settings.IA_MODELO,
            max_tokens=max_tokens,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=sistema_cacheado,
            messages=[{"role": "user", "content": entrada}],
            output_config=output_config,
        )
    except (anthropic.APIConnectionError, anthropic.RateLimitError) as e:
        raise ErrorIA(f"Proveedor no disponible: {e}") from e
    except anthropic.APIStatusError as e:
        raise ErrorIA(f"El proveedor respondio {e.status_code}: {e.message}") from e

    uso = respuesta.usage
    texto = "".join(b.text for b in respuesta.content if b.type == "text")
    return Respuesta(
        texto=texto,
        modelo=respuesta.model,
        uso=Uso(
            entrada=uso.input_tokens or 0,
            salida=uso.output_tokens or 0,
            cache_lectura=uso.cache_read_input_tokens or 0,
            cache_escritura=uso.cache_creation_input_tokens or 0,
        ),
        rechazada=respuesta.stop_reason == "refusal",
        request_id=getattr(respuesta, "_request_id", None),
    )

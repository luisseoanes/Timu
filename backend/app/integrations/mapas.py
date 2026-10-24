"""F2-RUT-02 Google Distance Matrix: distancias y tiempos reales de viaje.

Se factura por elemento (cada par origen-destino), asi que quien llama cachea y respeta
un tope diario (ver app/modules/rutas/distancias.py). Sin API key no consulta nada.
"""

from collections.abc import Sequence

import httpx
import structlog

from app.core.config import settings
from app.integrations.routing import Coordenada

logger = structlog.get_logger(__name__)

URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
# Limites de la API por peticion.
MAX_ORIGENES = 25
MAX_ELEMENTOS = 100


class ErrorMapas(Exception):
    pass


def configurado() -> bool:
    return bool(settings.GOOGLE_MAPS_API_KEY)


def _formato(p: Coordenada) -> str:
    return f"{p[0]:.6f},{p[1]:.6f}"


def consultar(
    origenes: Sequence[Coordenada], destinos: Sequence[Coordenada]
) -> list[list[tuple[int, int] | None]]:
    """(metros, segundos) por par; None si Google no encontro ruta entre esos puntos."""
    if len(origenes) * len(destinos) > MAX_ELEMENTOS or len(origenes) > MAX_ORIGENES:
        raise ValueError("Demasiados elementos para una sola consulta")
    params = {
        "origins": "|".join(_formato(o) for o in origenes),
        "destinations": "|".join(_formato(d) for d in destinos),
        "mode": "driving",
        "units": "metric",
        "key": settings.GOOGLE_MAPS_API_KEY,
    }
    try:
        with httpx.Client(timeout=15) as client:
            datos = client.get(URL, params=params).json()
    except (httpx.HTTPError, ValueError) as e:
        raise ErrorMapas(f"Distance Matrix no disponible: {e}") from e
    if datos.get("status") != "OK":
        raise ErrorMapas(f"Distance Matrix respondio {datos.get('status')}")
    resultado: list[list[tuple[int, int] | None]] = []
    for fila in datos["rows"]:
        celdas: list[tuple[int, int] | None] = []
        for elemento in fila["elements"]:
            if elemento.get("status") == "OK":
                celdas.append(
                    (int(elemento["distance"]["value"]), int(elemento["duration"]["value"]))
                )
            else:
                celdas.append(None)
        resultado.append(celdas)
    return resultado

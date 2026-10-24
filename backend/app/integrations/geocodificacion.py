"""F1-FAM-05 Geocodificacion de direcciones con Google Geocoding API.

Sin API key configurada (desarrollo) no consulta nada y el servicio usa las coordenadas
de la ciudad del catalogo como aproximacion.
"""

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

URL = "https://maps.googleapis.com/maps/api/geocode/json"

# Resultados que no ubican la direccion sino una zona amplia: se descartan.
_TIPOS_IMPRECISOS = {
    "locality",
    "administrative_area_level_1",
    "administrative_area_level_2",
    "country",
    "political",
}


def geocodificar(direccion: str, ciudad: str) -> tuple[float, float] | None:
    if not settings.GOOGLE_MAPS_API_KEY:
        return None
    params = {
        "address": f"{direccion}, {ciudad}, Colombia",
        "region": "co",
        "components": "country:CO",
        "key": settings.GOOGLE_MAPS_API_KEY,
    }
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(URL, params=params)
        datos = resp.json()
    except (httpx.HTTPError, ValueError):
        logger.warning("Geocodificacion no disponible", exc_info=True)
        return None
    if datos.get("status") != "OK" or not datos.get("results"):
        logger.info("Direccion sin resultado de geocodificacion: %s", datos.get("status"))
        return None
    mejor = datos["results"][0]
    if set(mejor.get("types", [])) <= _TIPOS_IMPRECISOS:
        return None
    ubicacion = mejor["geometry"]["location"]
    return float(ubicacion["lat"]), float(ubicacion["lng"])

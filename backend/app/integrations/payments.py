"""Pasarela de pagos Wompi (PayU/Refacil se agregan con la misma interfaz).

- Eventos: `signature.checksum` = SHA256(valores de `signature.properties` + timestamp +
  secreto de eventos). https://docs.wompi.co/docs/colombia/eventos/
- Transacciones: firma de integridad = SHA256(referencia + monto en centavos + moneda +
  secreto de integridad).
- Cobro recurrente: la tarjeta se tokeniza en el navegador (widget de Wompi); aqui solo
  llega el token, con el que se crea una fuente de pago reutilizable.
"""

import hashlib
import hmac
from typing import Any
from urllib.parse import urlencode

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class ErrorPasarela(Exception):
    def __init__(self, mensaje: str, *, temporal: bool) -> None:
        super().__init__(mensaje)
        self.temporal = temporal


def _valor(datos: dict[str, Any], ruta: str) -> str:
    actual: Any = datos
    for parte in ruta.split("."):
        actual = actual.get(parte, "") if isinstance(actual, dict) else ""
    return str(actual)


def verificar_evento_wompi(evento: dict[str, Any]) -> bool:
    """Valida el checksum del evento. Sin secreto configurado se acepta solo en local."""
    if not settings.WOMPI_EVENTS_SECRET:
        logger.warning("WOMPI_EVENTS_SECRET sin configurar; firma no verificada")
        return settings.ENVIRONMENT in ("local", "test")
    firma = evento.get("signature") or {}
    propiedades = firma.get("properties") or []
    datos = evento.get("data") or {}
    cadena = "".join(_valor(datos, p) for p in propiedades)
    cadena += str(evento.get("timestamp", "")) + settings.WOMPI_EVENTS_SECRET
    esperado = hashlib.sha256(cadena.encode()).hexdigest()
    return hmac.compare_digest(esperado, str(firma.get("checksum", "")).lower())


def firma_integridad(referencia: str, valor_centavos: int, moneda: str = "COP") -> str:
    cadena = f"{referencia}{valor_centavos}{moneda}{settings.WOMPI_INTEGRITY_SECRET}"
    return hashlib.sha256(cadena.encode()).hexdigest()


def construir_link_pago(
    referencia: str, valor_centavos: int, email: str | None = None, redireccion: str | None = None
) -> str:
    """Checkout web de Wompi para pagos puntuales (afiliacion, cuota desde el portal)."""
    params = {
        "public-key": settings.WOMPI_PUBLIC_KEY,
        "currency": "COP",
        "amount-in-cents": valor_centavos,
        "reference": referencia,
        "signature:integrity": firma_integridad(referencia, valor_centavos),
    }
    if email:
        params["customer-data:email"] = email
    if redireccion:
        params["redirect-url"] = redireccion
    return f"https://checkout.wompi.co/p/?{urlencode(params)}"


class ClienteWompi:
    def __init__(self, timeout: float = 20.0) -> None:
        self.base = settings.WOMPI_API_URL.rstrip("/")
        self.timeout = timeout

    def _pedir(self, metodo: str, ruta: str, *, privada: bool, **kwargs: Any) -> dict:
        llave = settings.WOMPI_PRIVATE_KEY if privada else settings.WOMPI_PUBLIC_KEY
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.request(
                    metodo,
                    f"{self.base}{ruta}",
                    headers={"Authorization": f"Bearer {llave}"},
                    **kwargs,
                )
        except httpx.TransportError as e:
            raise ErrorPasarela(f"Error de red con Wompi: {e}", temporal=True) from e
        if resp.status_code >= 500 or resp.status_code == 429:
            raise ErrorPasarela(f"Wompi respondio {resp.status_code}", temporal=True)
        if resp.status_code >= 400:
            raise ErrorPasarela(f"Wompi rechazo la operacion: {resp.text[:500]}", temporal=False)
        return dict(resp.json()["data"])

    def token_aceptacion(self) -> str:
        datos = self._pedir("GET", f"/merchants/{settings.WOMPI_PUBLIC_KEY}", privada=False)
        return str(datos["presigned_acceptance"]["acceptance_token"])

    def crear_fuente_pago(self, token_tarjeta: str, email: str, acceptance_token: str) -> str:
        datos = self._pedir(
            "POST",
            "/payment_sources",
            privada=True,
            json={
                "type": "CARD",
                "token": token_tarjeta,
                "customer_email": email,
                "acceptance_token": acceptance_token,
            },
        )
        return str(datos["id"])

    def cobrar_fuente(
        self, *, referencia: str, valor_centavos: int, email: str, fuente_id: str
    ) -> dict[str, Any]:
        return self._pedir(
            "POST",
            "/transactions",
            privada=True,
            json={
                "amount_in_cents": valor_centavos,
                "currency": "COP",
                "customer_email": email,
                "payment_method": {"installments": 1},
                "reference": referencia,
                "payment_source_id": int(fuente_id) if fuente_id.isdigit() else fuente_id,
                "recurrent": True,
                "signature": firma_integridad(referencia, valor_centavos),
            },
        )

    def consultar_transaccion(self, transaccion_id: str) -> dict[str, Any]:
        return self._pedir("GET", f"/transactions/{transaccion_id}", privada=False)

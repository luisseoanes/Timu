"""Pasarela de pagos (Wompi por defecto; PayU/Refacil se agregan con la misma interfaz)."""

import hashlib
import hmac
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def verificar_firma_wompi(raw_body: bytes, firma: str) -> bool:
    """Valida el checksum del evento. Sin secreto configurado se acepta solo en local."""
    if not settings.WOMPI_EVENTS_SECRET:
        logger.warning("WOMPI_EVENTS_SECRET sin configurar; firma no verificada")
        return settings.ENVIRONMENT == "local"
    esperado = hmac.new(
        settings.WOMPI_EVENTS_SECRET.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(esperado, firma)


def construir_link_pago(referencia: str, valor_centavos: int, email: str | None = None) -> str:
    """Genera el link de checkout que se envia a la familia (portal / WhatsApp).

    TODO: reemplazar por la creacion real de transaccion contra la API del proveedor.
    """
    params = (
        f"public-key={settings.WOMPI_PUBLIC_KEY}&currency=COP"
        f"&amount-in-cents={valor_centavos}&reference={referencia}"
    )
    if email:
        params += f"&customer-email={email}"
    return f"https://checkout.wompi.co/p/?{params}"

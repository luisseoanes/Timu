"""6.19 Cliente de Meta Cloud API (WhatsApp) con plantillas aprobadas."""

import hashlib
import hmac
from typing import Any

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class ErrorWhatsApp(Exception):
    """`temporal` indica si vale la pena reintentar (red, 429, 5xx)."""

    def __init__(self, mensaje: str, *, temporal: bool) -> None:
        super().__init__(mensaje)
        self.temporal = temporal


def verificar_firma(raw_body: bytes, firma: str) -> bool:
    """Valida X-Hub-Signature-256 con el secreto de la app. Sin secreto, solo en local."""
    if not settings.WHATSAPP_APP_SECRET:
        return settings.ENVIRONMENT in ("local", "test")
    esperado = (
        "sha256="
        + hmac.new(settings.WHATSAPP_APP_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    )
    return hmac.compare_digest(esperado, firma)


class WhatsAppClient:
    def __init__(self, timeout: float = 15.0) -> None:
        self._base = (
            f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/"
            f"{settings.WHATSAPP_PHONE_NUMBER_ID}"
        )
        self._timeout = timeout

    @property
    def configurado(self) -> bool:
        return bool(settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID)

    def _post(self, payload: dict[str, Any]) -> str:
        """Devuelve el id del mensaje en Meta (wamid)."""
        if not self.configurado:
            logger.warning("WhatsApp sin credenciales; mensaje no enviado a %s", payload["to"])
            return "no_configurado"
        headers = {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(f"{self._base}/messages", json=payload, headers=headers)
        except httpx.TransportError as e:
            raise ErrorWhatsApp(f"Error de red: {e}", temporal=True) from e
        if resp.status_code == 429 or resp.status_code >= 500:
            raise ErrorWhatsApp(f"Meta respondio {resp.status_code}", temporal=True)
        if resp.status_code >= 400:
            raise ErrorWhatsApp(f"Meta rechazo el mensaje: {resp.text[:500]}", temporal=False)
        return str(resp.json()["messages"][0]["id"])

    def enviar_texto(self, telefono: str, texto: str) -> str:
        return self._post(
            {
                "messaging_product": "whatsapp",
                "to": telefono,
                "type": "text",
                "text": {"body": texto},
            }
        )

    def enviar_plantilla(
        self, telefono: str, plantilla: str, parametros: list[str] | None = None, idioma: str = "es"
    ) -> str:
        componentes = (
            [{"type": "body", "parameters": [{"type": "text", "text": p} for p in parametros]}]
            if parametros
            else []
        )
        return self._post(
            {
                "messaging_product": "whatsapp",
                "to": telefono,
                "type": "template",
                "template": {
                    "name": plantilla,
                    "language": {"code": idioma},
                    "components": componentes,
                },
            }
        )

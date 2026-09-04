"""6.19 Cliente de Meta Cloud API (WhatsApp) con plantillas aprobadas."""

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


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

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.configurado:
            logger.warning("WhatsApp sin credenciales; mensaje no enviado: %s", payload)
            return {"status": "no_configurado"}
        headers = {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self._base}/messages", json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def enviar_texto(self, telefono: str, texto: str) -> dict[str, Any]:
        return await self._post(
            {
                "messaging_product": "whatsapp",
                "to": telefono,
                "type": "text",
                "text": {"body": texto},
            }
        )

    async def enviar_plantilla(
        self, telefono: str, plantilla: str, parametros: list[str] | None = None, idioma: str = "es"
    ) -> dict[str, Any]:
        componentes = (
            [{"type": "body", "parameters": [{"type": "text", "text": p} for p in parametros]}]
            if parametros
            else []
        )
        return await self._post(
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

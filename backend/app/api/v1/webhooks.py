"""Webhooks entrantes de terceros: Meta Cloud API (WhatsApp) y pasarela de pagos.

Ambos endpoints son publicos por diseno (los llama el proveedor), asi que la
validacion es por token/firma, no por JWT.
"""

import logging

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.core.config import settings
from app.integrations.payments import verificar_firma_wompi

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("/whatsapp")
async def verificar_whatsapp(request: Request) -> Response:
    """Handshake de verificacion que Meta ejecuta al registrar la URL."""
    params = request.query_params
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == settings.WHATSAPP_VERIFY_TOKEN
    ):
        return Response(content=params.get("hub.challenge", ""), media_type="text/plain")
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Token de verificacion invalido")


@router.post("/whatsapp", status_code=status.HTTP_202_ACCEPTED)
async def recibir_whatsapp(request: Request) -> dict[str, str]:
    """Mensajes entrantes y estados de entrega. Se encolan para no bloquear a Meta."""
    payload = await request.json()
    logger.info("whatsapp.webhook", extra={"payload": payload})
    # TODO: encolar app.workers.tasks.comunicaciones.procesar_evento_whatsapp.delay(payload)
    return {"status": "encolado"}


@router.post("/pagos", status_code=status.HTTP_202_ACCEPTED)
async def recibir_pago(request: Request) -> dict[str, str]:
    """Conciliacion automatica de pagos (seccion C: manejo de webhooks)."""
    raw = await request.body()
    firma = request.headers.get("x-event-checksum", "")
    if not verificar_firma_wompi(raw, firma):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Firma invalida")
    # TODO: encolar app.workers.tasks.cartera.conciliar_pago.delay(payload)
    return {"status": "encolado"}

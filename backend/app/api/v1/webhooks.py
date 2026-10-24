"""Webhooks entrantes de terceros: Meta Cloud API (WhatsApp) y pasarela de pagos.

Ambos endpoints son publicos por diseno (los llama el proveedor), asi que la
validacion es por token/firma, no por JWT. Responden rapido y encolan el procesamiento.
"""

import json

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.core.config import settings
from app.core.deps import DbSession, publico
from app.core.eventos import EventoDominio
from app.core.outbox import publicar
from app.integrations.payments import verificar_evento_wompi
from app.integrations.whatsapp import verificar_firma
from app.modules.cartera import pasarela

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"], dependencies=[Depends(publico)])


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
async def recibir_whatsapp(db: DbSession, request: Request) -> dict[str, str]:
    """Mensajes entrantes y estados de entrega (F1-WHA-02). Se guarda en el outbox y se
    responde: Meta reintenta si tarda, y el procesamiento corre en el worker."""
    raw = await request.body()
    if not verificar_firma(raw, request.headers.get("x-hub-signature-256", "")):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Firma invalida")
    publicar(db, EventoDominio("whatsapp.webhook_recibido", {"payload": json.loads(raw)}))
    return {"status": "encolado"}


@router.post("/pagos", status_code=status.HTTP_200_OK)
async def recibir_pago(db: DbSession, request: Request) -> dict[str, str]:
    """F1-CAR-09 Conciliacion: el evento se guarda (una sola vez aunque llegue repetido) y
    se procesa en segundo plano. Wompi reintenta si no recibe 200."""
    try:
        evento = json.loads(await request.body())
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cuerpo invalido") from e
    if not verificar_evento_wompi(evento):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Firma invalida")
    _, nuevo = await db.run_sync(pasarela.registrar_evento, evento)
    return {"status": "encolado" if nuevo else "duplicado"}

"""6.19 WhatsApp (Meta Cloud API) y trazabilidad de mensajes."""

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.schemas.common import Mensaje

router = APIRouter(prefix="/comunicaciones", tags=["comunicaciones"])


@router.get("", response_model=Mensaje)
async def pendiente_de_implementar(db: DbSession, _: CurrentUser) -> Mensaje:
    """Endpoint placeholder del modulo. Los modelos ya estan definidos en models.py."""
    return Mensaje(detail="Modulo comunicaciones: pendiente de implementar")

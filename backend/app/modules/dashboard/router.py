"""Dashboard gerencial (Fase 4): indicadores de operacion y cartera."""

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.schemas.common import Mensaje

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=Mensaje)
async def pendiente_de_implementar(db: DbSession, _: CurrentUser) -> Mensaje:
    """Endpoint placeholder del modulo. Los modelos ya estan definidos en models.py."""
    return Mensaje(detail="Modulo dashboard: pendiente de implementar")

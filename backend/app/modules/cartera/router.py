"""6.2 / 6.4 Cartera, mora, congelamiento, reactivacion y renovacion anual."""

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.schemas.common import Mensaje

router = APIRouter(prefix="/cartera", tags=["cartera"])


@router.get("", response_model=Mensaje)
async def pendiente_de_implementar(db: DbSession, _: CurrentUser) -> Mensaje:
    """Endpoint placeholder del modulo. Los modelos ya estan definidos en models.py."""
    return Mensaje(detail="Modulo cartera: pendiente de implementar")

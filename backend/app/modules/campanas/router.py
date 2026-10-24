"""6.16 / 6.18 Segmentacion y comunicaciones masivas."""

from fastapi import APIRouter, Depends

from app.core.deps import INTERNOS, requiere
from app.schemas.common import Mensaje

router = APIRouter(prefix="/campanas", tags=["campanas"])


@router.get("", response_model=Mensaje, dependencies=[Depends(requiere(*INTERNOS))])
async def pendiente_de_implementar() -> Mensaje:
    """Endpoint placeholder del modulo. Los modelos ya estan definidos en models.py."""
    return Mensaje(detail="Modulo campanas: pendiente de implementar")

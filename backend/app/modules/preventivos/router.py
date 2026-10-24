"""6.8 / 6.9 / 6.13 / 6.15 Calendario preventivo, autorizacion y carnet."""

from fastapi import APIRouter, Depends

from app.core.deps import INTERNOS, requiere
from app.schemas.common import Mensaje

router = APIRouter(prefix="/preventivos", tags=["preventivos"])


@router.get("", response_model=Mensaje, dependencies=[Depends(requiere(*INTERNOS))])
async def pendiente_de_implementar() -> Mensaje:
    """Endpoint placeholder del modulo. Los modelos ya estan definidos en models.py."""
    return Mensaje(detail="Modulo preventivos: pendiente de implementar")

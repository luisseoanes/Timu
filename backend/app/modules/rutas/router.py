"""6.7 Rutas domiciliarias y optimizacion de secuencia."""

from fastapi import APIRouter, Depends

from app.core.deps import INTERNOS, requiere
from app.schemas.common import Mensaje

router = APIRouter(prefix="/rutas", tags=["rutas"])


@router.get("", response_model=Mensaje, dependencies=[Depends(requiere(*INTERNOS))])
async def pendiente_de_implementar() -> Mensaje:
    """Endpoint placeholder del modulo. Los modelos ya estan definidos en models.py."""
    return Mensaje(detail="Modulo rutas: pendiente de implementar")

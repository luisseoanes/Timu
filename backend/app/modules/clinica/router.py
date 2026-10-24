"""6.14 / 6.17 Gestion clinica veterinaria y atencion virtual."""

from fastapi import APIRouter, Depends

from app.core.deps import INTERNOS, requiere
from app.schemas.common import Mensaje

router = APIRouter(prefix="/clinica", tags=["clinica"])


@router.get("", response_model=Mensaje, dependencies=[Depends(requiere(*INTERNOS))])
async def pendiente_de_implementar() -> Mensaje:
    """Endpoint placeholder del modulo. Los modelos ya estan definidos en models.py."""
    return Mensaje(detail="Modulo clinica: pendiente de implementar")

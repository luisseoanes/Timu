"""Portal de familias: cada endpoint parte de la familia del usuario conectado (F1-AUT-04).

El portal completo (historia, carnet, pagos, autogestion) se construye en la Fase 3.
"""

from typing import Any

from fastapi import APIRouter

from app.core.deps import DbSession, FamiliaActual
from app.modules.cartera import service as cartera
from app.modules.cartera.schemas import EstadoCuenta
from app.modules.familias.models import Familia
from app.modules.familias.schemas import FamiliaRead

router = APIRouter(prefix="/portal", tags=["portal"])


@router.get("/mi-familia", response_model=FamiliaRead)
async def mi_familia(familia: FamiliaActual) -> Familia:
    return familia


@router.get("/contrato")
async def contrato(db: DbSession, familia: FamiliaActual) -> dict[str, str]:
    """F1-AFI-02 PDF del contrato vigente de la familia."""
    from app.modules.planes import service as planes

    vigente = await db.run_sync(planes.contrato_vigente, familia.id)
    if vigente is None:
        from app.core.errores import NoEncontrado

        raise NoEncontrado("La familia no tiene contrato vigente")
    return await db.run_sync(cartera.url_documento, vigente)


@router.get("/estado-cuenta", response_model=EstadoCuenta)
async def estado_cuenta(db: DbSession, familia: FamiliaActual) -> Any:
    """F1-CAR-10 La misma consulta del panel, siempre sobre la familia conectada."""
    return await db.run_sync(cartera.estado_cuenta, familia.id)

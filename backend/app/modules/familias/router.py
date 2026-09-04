from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DbSession
from app.core.enums import EstadoAfiliacion
from app.modules.familias import service
from app.modules.familias.schemas import (
    FamiliaCreate,
    FamiliaRead,
    FamiliaUpdate,
    MascotaCreate,
    MascotaRead,
)
from app.schemas.common import Page

router = APIRouter(prefix="/familias", tags=["familias"])


@router.get("", response_model=Page[FamiliaRead])
async def listar_familias(
    db: DbSession,
    _: CurrentUser,
    q: str | None = None,
    ciudad: str | None = None,
    estado: EstadoAfiliacion | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
) -> Page[FamiliaRead]:
    items, total = await service.listar(
        db, q=q, ciudad=ciudad, estado=estado, limit=limit, offset=offset
    )
    return Page(
        items=[FamiliaRead.model_validate(f) for f in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=FamiliaRead, status_code=status.HTTP_201_CREATED)
async def crear_familia(db: DbSession, _: CurrentUser, data: FamiliaCreate) -> FamiliaRead:
    return FamiliaRead.model_validate(await service.crear(db, data))


@router.get("/{familia_id}", response_model=FamiliaRead)
async def obtener_familia(db: DbSession, _: CurrentUser, familia_id: UUID) -> FamiliaRead:
    familia = await service.obtener(db, familia_id)
    if familia is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Familia no encontrada")
    return FamiliaRead.model_validate(familia)


@router.patch("/{familia_id}", response_model=FamiliaRead)
async def actualizar_familia(
    db: DbSession, _: CurrentUser, familia_id: UUID, data: FamiliaUpdate
) -> FamiliaRead:
    familia = await service.obtener(db, familia_id)
    if familia is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Familia no encontrada")
    return FamiliaRead.model_validate(await service.actualizar(db, familia, data))


@router.post(
    "/{familia_id}/mascotas", response_model=MascotaRead, status_code=status.HTTP_201_CREATED
)
async def agregar_mascota(
    db: DbSession, _: CurrentUser, familia_id: UUID, data: MascotaCreate
) -> MascotaRead:
    familia = await service.obtener(db, familia_id)
    if familia is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Familia no encontrada")
    return MascotaRead.model_validate(await service.agregar_mascota(db, familia, data))

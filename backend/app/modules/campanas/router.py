"""6.16 / 6.18 Segmentacion y campanas masivas."""

import csv
import io
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.core.deps import INTERNOS, DbSession, requiere
from app.core.enums import Rol
from app.core.errores import Conflicto, NoEncontrado
from app.modules.auth.models import Usuario
from app.modules.campanas import segmentos, service
from app.modules.campanas.models import Campana, EjecucionCampana, Segmento

router = APIRouter(prefix="/campanas", tags=["campanas"])
segmentos_router = APIRouter(prefix="/segmentos", tags=["campanas"])

EQUIPO = Depends(requiere(*INTERNOS))
Mercadeo = Annotated[Usuario, Depends(requiere(Rol.ADMIN, Rol.COMERCIAL))]


class SegmentoIn(BaseModel):
    nombre: str = Field(min_length=3, max_length=160)
    descripcion: str | None = None
    filtros: segmentos.FiltrosSegmento


class SegmentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    descripcion: str | None
    filtros: dict[str, Any]


class CampanaIn(BaseModel):
    nombre: str = Field(min_length=3, max_length=160)
    plantilla: str
    variables: list[str] = []
    segmento_id: UUID | None = None
    segmento: segmentos.FiltrosSegmento | None = None


class CampanaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    canal: str
    plantilla: str | None
    variables: list[str]
    segmento_id: UUID | None
    segmento: dict[str, Any]
    estado: str
    programada_para: datetime | None
    recurrencia: str
    proxima_ejecucion: datetime | None


class ProgramacionIn(BaseModel):
    cuando: datetime | None = Field(default=None, description="Vacio: sale de inmediato")
    recurrencia: Literal["ninguna", "diaria", "semanal", "mensual"] = "ninguna"


class EjecucionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    iniciada_en: datetime
    terminada_en: datetime | None
    estado: str
    audiencia: int
    excluidos: int


# --- F3-SEG-01 Segmentos ----------------------------------------------------------------------


@segmentos_router.post("/previsualizacion", dependencies=[EQUIPO])
async def previsualizar_segmento(
    db: DbSession, filtros: segmentos.FiltrosSegmento
) -> dict[str, Any]:
    """Cuantas familias alcanza la combinacion de filtros, con una muestra."""
    return await db.run_sync(segmentos.previsualizar, filtros)


@segmentos_router.get("", response_model=list[SegmentoRead], dependencies=[EQUIPO])
async def listar_segmentos(db: DbSession) -> list[Segmento]:
    return list(await db.scalars(select(Segmento).order_by(Segmento.nombre)))


@segmentos_router.post("", response_model=SegmentoRead, status_code=status.HTTP_201_CREATED)
async def crear_segmento(db: DbSession, usuario: Mercadeo, data: SegmentoIn) -> Segmento:
    if await db.scalar(select(Segmento.id).where(Segmento.nombre == data.nombre)):
        raise Conflicto("Ya existe un segmento con ese nombre")
    segmento = Segmento(
        nombre=data.nombre,
        descripcion=data.descripcion,
        filtros=data.filtros.model_dump(mode="json", exclude_defaults=True),
        creado_por_id=usuario.id,
    )
    db.add(segmento)
    await db.flush()
    return segmento


@segmentos_router.get("/{segmento_id}/conteo", dependencies=[EQUIPO])
async def contar_segmento(db: DbSession, segmento_id: UUID) -> dict[str, Any]:
    segmento = await db.get(Segmento, segmento_id)
    if segmento is None:
        raise NoEncontrado("Segmento no encontrado")
    return await db.run_sync(segmentos.previsualizar, segmentos.FiltrosSegmento(**segmento.filtros))


# --- F3-CAM-01..04 Campanas -------------------------------------------------------------------


def _datos(data: CampanaIn) -> dict[str, Any]:
    datos = data.model_dump(exclude={"segmento"})
    datos["segmento"] = (
        data.segmento.model_dump(mode="json", exclude_defaults=True) if data.segmento else {}
    )
    return datos


@router.get("", response_model=list[CampanaRead], dependencies=[EQUIPO])
async def listar(db: DbSession, estado: str | None = None) -> list[Campana]:
    stmt = select(Campana).order_by(Campana.created_at.desc())
    if estado:
        stmt = stmt.where(Campana.estado == estado)
    return list(await db.scalars(stmt))


@router.post("", response_model=CampanaRead, status_code=status.HTTP_201_CREATED)
async def crear(db: DbSession, usuario: Mercadeo, data: CampanaIn) -> Campana:
    return await db.run_sync(service.guardar, None, _datos(data), usuario.id)


@router.put("/{campana_id}", response_model=CampanaRead)
async def editar(db: DbSession, usuario: Mercadeo, campana_id: UUID, data: CampanaIn) -> Campana:
    campana = await db.run_sync(service.obtener, campana_id)
    return await db.run_sync(service.guardar, campana, _datos(data), usuario.id)


@router.get("/{campana_id}/previsualizacion", dependencies=[EQUIPO])
async def previsualizar(db: DbSession, campana_id: UUID) -> dict[str, Any]:
    """F3-CAM-01 Audiencia, exclusiones y ejemplos del mensaje antes de enviar."""
    return await db.run_sync(lambda s: service.previsualizar(s, service.obtener(s, campana_id)))


@router.post("/{campana_id}/programacion", response_model=CampanaRead)
async def programar(db: DbSession, _: Mercadeo, campana_id: UUID, data: ProgramacionIn) -> Campana:
    """F3-CAM-04 Ahora, en una fecha o de forma recurrente."""
    campana = await db.run_sync(service.obtener, campana_id)
    return await db.run_sync(service.programar, campana, data.cuando, data.recurrencia)


@router.post("/{campana_id}/cancelacion", response_model=CampanaRead)
async def cancelar(db: DbSession, _: Mercadeo, campana_id: UUID) -> Campana:
    campana = await db.run_sync(service.obtener, campana_id)
    return await db.run_sync(service.cancelar, campana)


@router.get("/{campana_id}/ejecuciones", response_model=list[EjecucionRead], dependencies=[EQUIPO])
async def ejecuciones(db: DbSession, campana_id: UUID) -> list[EjecucionCampana]:
    return list(
        await db.scalars(
            select(EjecucionCampana)
            .where(EjecucionCampana.campana_id == campana_id)
            .order_by(EjecucionCampana.iniciada_en.desc())
        )
    )


@router.get("/{campana_id}/resultados", dependencies=[EQUIPO], response_model=None)
async def resultados(
    db: DbSession, campana_id: UUID, ejecucion_id: UUID | None = None, formato: str = "json"
) -> dict[str, Any] | Response:
    """F3-CAM-03 Totales por estado; con formato=csv, una fila por destinatario."""
    if formato != "csv":
        return await db.run_sync(
            lambda s: service.resultados(s, service.obtener(s, campana_id), ejecucion_id)
        )
    filas = await db.run_sync(
        lambda s: service.detalle(s, service.obtener(s, campana_id), ejecucion_id)
    )
    salida = io.StringIO()
    if filas:
        escritor = csv.DictWriter(salida, fieldnames=list(filas[0].keys()))
        escritor.writeheader()
        escritor.writerows(filas)
    return Response(
        salida.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="campana-{campana_id}.csv"'},
    )

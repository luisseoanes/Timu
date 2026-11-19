"""6.16 / 6.18 Segmentacion y campanas masivas."""

import csv
import io
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.api.deps import DbSession, requiere
from app.core.enums import Rol
from app.core.errores import Conflicto, NoEncontrado
from app.modules.auth.models import Usuario
from app.modules.campanas import segmentos, service
from app.modules.campanas.models import Campana, EjecucionCampana, Segmento
from app.modules.comunicaciones import service as comunicaciones

router = APIRouter(prefix="/campanas", tags=["campanas"])
segmentos_router = APIRouter(prefix="/segmentos", tags=["campanas"])

# Perfiles de cada ruta (Seccion 12, docs/perfiles-y-permisos.md).
COMERCIAL = Depends(requiere(Rol.COMERCIAL))
Comercial = Annotated[Usuario, Depends(requiere(Rol.COMERCIAL))]


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
    plantilla_titulo: str | None = Field(
        default=None, description="Como llama el equipo a la plantilla; `plantilla` es su codigo"
    )


async def _leidas(db: DbSession, campanas: list[Campana]) -> list[CampanaRead]:
    """Cada campana con el nombre que da el equipo a su plantilla."""
    titulos = await db.run_sync(comunicaciones.titulos_plantillas)
    return [
        CampanaRead.model_validate(c).model_copy(
            update={"plantilla_titulo": titulos.get(c.plantilla or "")}
        )
        for c in campanas
    ]


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


# --- 6.16 Segmentos ----------------------------------------------------------------------


@segmentos_router.post("/previsualizacion", dependencies=[COMERCIAL])
async def previsualizar_segmento(
    db: DbSession, filtros: segmentos.FiltrosSegmento
) -> dict[str, Any]:
    """Cuantas familias alcanza la combinacion de filtros, con una muestra."""
    return await db.run_sync(segmentos.previsualizar, filtros)


@segmentos_router.get("", response_model=list[SegmentoRead], dependencies=[COMERCIAL])
async def listar_segmentos(db: DbSession) -> list[Segmento]:
    return list(await db.scalars(select(Segmento).order_by(Segmento.nombre)))


@segmentos_router.post("", response_model=SegmentoRead, status_code=status.HTTP_201_CREATED)
async def crear_segmento(db: DbSession, usuario: Comercial, data: SegmentoIn) -> Segmento:
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


@segmentos_router.get("/{segmento_id}/conteo", dependencies=[COMERCIAL])
async def contar_segmento(db: DbSession, segmento_id: UUID) -> dict[str, Any]:
    segmento = await db.get(Segmento, segmento_id)
    if segmento is None:
        raise NoEncontrado("Segmento no encontrado")
    return await db.run_sync(segmentos.previsualizar, segmentos.FiltrosSegmento(**segmento.filtros))


# --- 6.18 Campanas -------------------------------------------------------------------


def _datos(data: CampanaIn) -> dict[str, Any]:
    datos = data.model_dump(exclude={"segmento"})
    datos["segmento"] = (
        data.segmento.model_dump(mode="json", exclude_defaults=True) if data.segmento else {}
    )
    return datos


@router.get("", response_model=list[CampanaRead], dependencies=[COMERCIAL])
async def listar(db: DbSession, estado: str | None = None) -> list[CampanaRead]:
    stmt = select(Campana).order_by(Campana.created_at.desc())
    if estado:
        stmt = stmt.where(Campana.estado == estado)
    return await _leidas(db, list(await db.scalars(stmt)))


@router.post("", response_model=CampanaRead, status_code=status.HTTP_201_CREATED)
async def crear(db: DbSession, usuario: Comercial, data: CampanaIn) -> CampanaRead:
    campana = await db.run_sync(service.guardar, None, _datos(data), usuario.id)
    return (await _leidas(db, [campana]))[0]


@router.put("/{campana_id}", response_model=CampanaRead)
async def editar(
    db: DbSession, usuario: Comercial, campana_id: UUID, data: CampanaIn
) -> CampanaRead:
    campana = await db.run_sync(service.obtener, campana_id)
    guardada = await db.run_sync(service.guardar, campana, _datos(data), usuario.id)
    return (await _leidas(db, [guardada]))[0]


@router.get("/{campana_id}/previsualizacion", dependencies=[COMERCIAL])
async def previsualizar(db: DbSession, campana_id: UUID) -> dict[str, Any]:
    """6.18 Audiencia, exclusiones y ejemplos del mensaje antes de enviar."""
    return await db.run_sync(lambda s: service.previsualizar(s, service.obtener(s, campana_id)))


@router.post("/{campana_id}/programacion", response_model=CampanaRead)
async def programar(
    db: DbSession, _: Comercial, campana_id: UUID, data: ProgramacionIn
) -> CampanaRead:
    """6.18 Ahora, en una fecha o de forma recurrente."""
    campana = await db.run_sync(service.obtener, campana_id)
    programada = await db.run_sync(service.programar, campana, data.cuando, data.recurrencia)
    return (await _leidas(db, [programada]))[0]


@router.post("/{campana_id}/cancelacion", response_model=CampanaRead)
async def cancelar(db: DbSession, _: Comercial, campana_id: UUID) -> CampanaRead:
    campana = await db.run_sync(service.obtener, campana_id)
    cancelada = await db.run_sync(service.cancelar, campana)
    return (await _leidas(db, [cancelada]))[0]


@router.get(
    "/{campana_id}/ejecuciones", response_model=list[EjecucionRead], dependencies=[COMERCIAL]
)
async def ejecuciones(db: DbSession, campana_id: UUID) -> list[EjecucionCampana]:
    return list(
        await db.scalars(
            select(EjecucionCampana)
            .where(EjecucionCampana.campana_id == campana_id)
            .order_by(EjecucionCampana.iniciada_en.desc())
        )
    )


@router.get("/{campana_id}/resultados", dependencies=[COMERCIAL], response_model=None)
async def resultados(
    db: DbSession, campana_id: UUID, ejecucion_id: UUID | None = None, formato: str = "json"
) -> dict[str, Any] | Response:
    """6.18 Totales por estado; con formato=csv, una fila por destinatario."""
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

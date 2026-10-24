"""F1-SER-06 Bandeja unica de tareas internas."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field

from app.core.deps import INTERNOS, DbSession, Interno, requiere
from app.modules.tareas import service
from app.modules.tareas.models import Tarea
from app.schemas.common import Page, ParamsListado, paginar

router = APIRouter(prefix="/tareas", tags=["tareas"], dependencies=[Depends(requiere(*INTERNOS))])

Area = Literal["comercial", "operaciones", "medico", "cartera", "servicio_cliente"]


class TareaCreate(BaseModel):
    titulo: str = Field(min_length=3, max_length=200)
    descripcion: str | None = None
    area: Area
    prioridad: Literal["baja", "media", "alta"] = "media"
    vence_en_dias: int | None = Field(default=None, ge=0)
    familia_id: UUID | None = None
    asignada_a_id: UUID | None = None


class TareaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    descripcion: str | None
    area: str
    prioridad: str
    estado: str
    vence_el: date | None
    asignada_a_id: UUID | None
    familia_id: UUID | None
    servicio_id: UUID | None
    contrato_id: UUID | None
    origen: str | None
    cerrada_en: datetime | None
    resolucion: str | None
    created_at: datetime


class Asignacion(BaseModel):
    usuario_id: UUID | None


class Cierre(BaseModel):
    resolucion: str = Field(min_length=3)


@router.get("", response_model=Page[TareaRead])
async def bandeja(
    db: DbSession,
    usuario: Interno,
    params: ParamsListado,
    area: Area | None = None,
    estado: Literal["abierta", "en_progreso", "cerrada"] | None = None,
    mias: bool = False,
    sin_asignar: bool = False,
    vencidas: bool = False,
    familia_id: UUID | None = None,
) -> Page[TareaRead]:
    """Por defecto: prioridad (alta primero) y luego vencimiento mas cercano."""
    stmt = service.consulta(
        area=area,
        estado=estado,
        asignada_a_id=usuario.id if mias else None,
        sin_asignar=sin_asignar,
        vencidas=vencidas,
        familia_id=familia_id,
    )
    if not params.orden:
        stmt = stmt.order_by(service.ORDEN_PRIORIDAD, Tarea.vence_el.asc().nulls_last())
    return await paginar(
        db,
        stmt,
        params,
        TareaRead,
        campos_orden={"vence_el": Tarea.vence_el, "created_at": Tarea.created_at},
        orden_por_defecto="created_at",
        desempate=Tarea.id,
    )


@router.post("", response_model=TareaRead, status_code=status.HTTP_201_CREATED)
async def crear(db: DbSession, data: TareaCreate) -> Tarea:
    tarea = await db.run_sync(
        service.crear,
        titulo=data.titulo,
        descripcion=data.descripcion,
        area=data.area,
        prioridad=data.prioridad,
        vence_en_dias=data.vence_en_dias,
        familia_id=data.familia_id,
        origen="manual",
    )
    assert tarea is not None
    if data.asignada_a_id:
        await db.run_sync(service.asignar, tarea, data.asignada_a_id)
    return tarea


@router.patch("/{tarea_id}/asignacion", response_model=TareaRead)
async def asignar(db: DbSession, tarea_id: UUID, data: Asignacion) -> Tarea:
    return await db.run_sync(
        service.asignar, await db.run_sync(service.obtener, tarea_id), data.usuario_id
    )


@router.post("/{tarea_id}/iniciar", response_model=TareaRead)
async def iniciar(db: DbSession, tarea_id: UUID) -> Tarea:
    return await db.run_sync(service.iniciar, await db.run_sync(service.obtener, tarea_id))


@router.post("/{tarea_id}/cerrar", response_model=TareaRead)
async def cerrar(db: DbSession, tarea_id: UUID, data: Cierre) -> Tarea:
    return await db.run_sync(
        service.cerrar, await db.run_sync(service.obtener, tarea_id), data.resolucion
    )

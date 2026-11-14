"""F1-SER-06 Bandeja unica de tareas internas."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import INTERNOS, DbSession, Interno, requiere
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


class FamiliaDeTarea(BaseModel):
    id: UUID
    titular_nombre: str


class ServicioDeTarea(BaseModel):
    id: UUID
    tipo_codigo: str
    mascota_nombre: str | None


class TareaListado(TareaRead):
    """Fila de la bandeja: la tarea con a quien afecta (R2-PAN-05)."""

    familia: FamiliaDeTarea | None
    servicio: ServicioDeTarea | None


class Asignacion(BaseModel):
    usuario_id: UUID | None


class Cierre(BaseModel):
    resolucion: str = Field(min_length=3)


@router.get("", response_model=Page[TareaListado])
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
) -> Page[TareaListado]:
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
    pagina = await paginar(
        db,
        stmt,
        params,
        TareaRead,
        campos_orden={"vence_el": Tarea.vence_el, "created_at": Tarea.created_at},
        orden_por_defecto="created_at",
        desempate=Tarea.id,
    )
    familias, servicios = await db.run_sync(
        service.a_quien_afecta,
        {t.familia_id for t in pagina.items if t.familia_id},
        {t.servicio_id for t in pagina.items if t.servicio_id},
    )
    return Page[TareaListado](
        items=[
            TareaListado(
                **t.model_dump(),
                familia=FamiliaDeTarea(**familias[t.familia_id]) if t.familia_id else None,
                servicio=ServicioDeTarea(**servicios[t.servicio_id]) if t.servicio_id else None,
            )
            for t in pagina.items
        ],
        total=pagina.total,
        limit=pagina.limit,
        offset=pagina.offset,
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

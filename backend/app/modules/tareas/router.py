"""6.4 Bandeja unica de tareas internas."""

from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import DbSession, requiere
from app.core.enums import Rol
from app.modules.auth.models import Usuario
from app.modules.tareas import service
from app.modules.tareas.models import Tarea
from app.schemas.common import Page, ParamsListado, paginar

# Perfiles de cada ruta (Seccion 12, docs/perfiles-y-permisos.md): los cuatro perfiles operativos,
# cada uno con las tareas de su area (TAREAS_POR_ROL en el servicio).
_OPERATIVOS = (Rol.COMERCIAL, Rol.ATENCION_CLIENTE, Rol.OPERACIONES, Rol.MEDICO)
Operativo = Annotated[Usuario, Depends(requiere(*_OPERATIVOS))]
router = APIRouter(
    prefix="/tareas", tags=["tareas"], dependencies=[Depends(requiere(*_OPERATIVOS))]
)

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
    usuario: Operativo,
    params: ParamsListado,
    area: Area | None = None,
    estado: Literal["pendiente", "abierta", "en_progreso", "cerrada"] | None = None,
    mias: bool = False,
    sin_asignar: bool = False,
    vencidas: bool = False,
    familia_id: UUID | None = None,
    excluir_origen: str | None = None,
) -> Page[TareaListado]:
    """Por defecto: prioridad (alta primero) y luego vencimiento mas cercano. `pendiente` son
    las abiertas y las en progreso; `excluir_origen` deja fuera las que ya cuenta otra bandeja
    (las de una conversacion, que el Inicio de Comercial dice como conversacion)."""
    stmt = service.consulta(
        areas=service.AREAS_POR_ROL[usuario.rol],
        area=area,
        estado=estado,
        asignada_a_id=usuario.id if mias else None,
        sin_asignar=sin_asignar,
        vencidas=vencidas,
        familia_id=familia_id,
        excluir_origen=excluir_origen,
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


async def _de_su_area(db: DbSession, usuario: Usuario, tarea_id: UUID) -> Tarea:
    return await db.run_sync(service.obtener, tarea_id, service.AREAS_POR_ROL[usuario.rol])


@router.patch("/{tarea_id}/asignacion", response_model=TareaRead)
async def asignar(db: DbSession, usuario: Operativo, tarea_id: UUID, data: Asignacion) -> Tarea:
    return await db.run_sync(
        service.asignar, await _de_su_area(db, usuario, tarea_id), data.usuario_id
    )


@router.post("/{tarea_id}/iniciar", response_model=TareaRead)
async def iniciar(db: DbSession, usuario: Operativo, tarea_id: UUID) -> Tarea:
    return await db.run_sync(service.iniciar, await _de_su_area(db, usuario, tarea_id))


@router.post("/{tarea_id}/cerrar", response_model=TareaRead)
async def cerrar(db: DbSession, usuario: Operativo, tarea_id: UUID, data: Cierre) -> Tarea:
    return await db.run_sync(
        service.cerrar, await _de_su_area(db, usuario, tarea_id), data.resolucion
    )

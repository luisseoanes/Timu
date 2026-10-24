"""6.5 / 6.6 / 6.10 Programacion de servicios, pendientes y estados."""

from datetime import date, datetime, time
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select

from app.core.deps import INTERNOS, DbSession, requiere
from app.core.enums import EstadoServicio, Rol
from app.core.errores import NoEncontrado, ReglaNegocio
from app.modules.auth.models import Usuario
from app.modules.catalogos import service as catalogos
from app.modules.familias import service as familias
from app.modules.servicios import service
from app.modules.servicios.models import (
    BloqueoAgenda,
    EstadoPendiente,
    Franja,
    Pendiente,
    Servicio,
    ServicioPaso,
)
from app.schemas.common import Page, ParamsListado, paginar

router = APIRouter(prefix="/servicios", tags=["servicios"])
agenda_router = APIRouter(prefix="/agenda", tags=["servicios"])
pendientes_router = APIRouter(prefix="/pendientes", tags=["servicios"])

EQUIPO = Depends(requiere(*INTERNOS))
Equipo = Annotated[Usuario, Depends(requiere(*INTERNOS))]
Medico = Annotated[Usuario, Depends(requiere(Rol.ADMIN, Rol.MEDICO))]
GESTION_AGENDA = Depends(requiere(Rol.ADMIN, Rol.OPERACIONES))


class ServicioCreate(BaseModel):
    familia_id: UUID
    mascota_id: UUID | None = None
    tipo_codigo: str
    inicio: datetime = Field(description="Con zona horaria; sin ella se asume hora de Colombia")
    observaciones: str | None = None
    pendiente_id: UUID | None = None


class ServicioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    familia_id: UUID
    mascota_id: UUID | None
    tipo_codigo: str
    tipo: str
    estado: str
    ciudad: str
    programado_para: datetime | None
    termina_en: datetime | None
    requiere_autorizacion: bool
    autorizado: bool
    autorizado_en: datetime | None
    profesional_id: UUID | None
    pendiente_origen_id: UUID | None
    observaciones: str | None
    motivo_estado: str | None


class Transicion(BaseModel):
    estado: EstadoServicio
    motivo: str | None = None


class Reprogramacion(BaseModel):
    inicio: datetime
    motivo: str = Field(min_length=3)


class PasoIn(BaseModel):
    datos: dict[str, Any] = Field(default_factory=dict)


class PasoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    paso_codigo: str
    datos: dict[str, Any]
    completado_por_id: UUID | None
    created_at: datetime


class CupoRead(BaseModel):
    inicio: datetime
    fin: datetime
    disponibles: int


class ElegibilidadRead(BaseModel):
    elegible: bool
    motivos: list[str]


class FranjaIn(BaseModel):
    ciudad: str
    modalidad: Literal["domiciliario", "preventivo", "clinico", "virtual", "aliada"]
    dia_semana: int = Field(ge=0, le=6, description="0 = lunes")
    hora_inicio: time
    hora_fin: time
    capacidad: int = Field(default=1, ge=1, le=100)

    @model_validator(mode="after")
    def _orden(self) -> "FranjaIn":
        if self.hora_fin <= self.hora_inicio:
            raise ValueError("La hora de fin debe ser posterior a la de inicio")
        return self


class FranjaRead(FranjaIn):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    activa: bool


class BloqueoIn(BaseModel):
    fecha: date
    ciudad: str | None = None
    modalidad: str | None = None
    motivo: str = Field(min_length=3, max_length=160)


class PendienteIn(BaseModel):
    descripcion: str = Field(min_length=3)
    requiere_autorizacion: bool = True


class AutorizacionPendiente(BaseModel):
    aprobado: bool = True
    medio: Literal["whatsapp", "llamada", "presencial", "portal", "correo"]


class AvancePendiente(BaseModel):
    estado: Literal["en_gestion", "resuelto"]
    resolucion: str | None = None


class PendienteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    servicio_origen_id: UUID
    descripcion: str
    requiere_autorizacion: bool
    estado: str
    autorizado_por_id: UUID | None
    autorizado_en: datetime | None
    medio_autorizacion: str | None
    resolucion: str | None


# --- Agenda (F1-SER-01) --------------------------------------------------------------------


@agenda_router.get("/disponibilidad", response_model=list[CupoRead], dependencies=[EQUIPO])
async def disponibilidad(db: DbSession, fecha: date, ciudad: str, tipo_codigo: str) -> Any:
    ciudad = await db.run_sync(catalogos.ciudad_valida, ciudad)
    tipo = await db.run_sync(service.tipo_servicio, tipo_codigo)
    return await db.run_sync(service.disponibilidad, fecha, ciudad, tipo)


@agenda_router.get("/franjas", response_model=list[FranjaRead], dependencies=[EQUIPO])
async def franjas(db: DbSession, ciudad: str | None = None) -> list[Franja]:
    stmt = select(Franja).order_by(Franja.ciudad, Franja.dia_semana, Franja.hora_inicio)
    if ciudad:
        stmt = stmt.where(Franja.ciudad == ciudad)
    return list(await db.scalars(stmt))


@agenda_router.post(
    "/franjas",
    response_model=FranjaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GESTION_AGENDA],
)
async def crear_franja(db: DbSession, data: FranjaIn) -> Franja:
    datos = data.model_dump()
    datos["ciudad"] = await db.run_sync(catalogos.ciudad_valida, data.ciudad)
    franja = Franja(**datos)
    db.add(franja)
    await db.flush()
    return franja


@agenda_router.patch(
    "/franjas/{franja_id}", response_model=FranjaRead, dependencies=[GESTION_AGENDA]
)
async def actualizar_franja(
    db: DbSession, franja_id: UUID, capacidad: int | None = None, activa: bool | None = None
) -> Franja:
    """Reducir capacidad no cancela lo ya agendado: solo limita lo nuevo."""
    franja = await db.get(Franja, franja_id)
    if franja is None:
        raise NoEncontrado("Franja no encontrada")
    if capacidad is not None:
        franja.capacidad = capacidad
    if activa is not None:
        franja.activa = activa
    await db.flush()
    return franja


@agenda_router.post("/bloqueos", status_code=status.HTTP_201_CREATED, dependencies=[GESTION_AGENDA])
async def bloquear(db: DbSession, data: BloqueoIn) -> dict[str, str]:
    db.add(BloqueoAgenda(**data.model_dump()))
    return {"detail": f"Agenda bloqueada el {data.fecha:%d/%m/%Y}"}


# --- Servicios -------------------------------------------------------------------------------


@router.get("/elegibilidad", response_model=ElegibilidadRead, dependencies=[EQUIPO])
async def elegibilidad(
    db: DbSession, familia_id: UUID, tipo_codigo: str, mascota_id: UUID | None = None
) -> Any:
    """F1-SER-05 Verifica antes de agendar y explica por que no se puede."""
    familia = await db.run_sync(familias.obtener, familia_id)
    mascota = await db.run_sync(familias.obtener_mascota, mascota_id) if mascota_id else None
    return await db.run_sync(
        service.elegibilidad,
        familia,
        mascota,
        await db.run_sync(service.tipo_servicio, tipo_codigo),
    )


@router.get("", response_model=Page[ServicioRead], dependencies=[EQUIPO])
async def listar(
    db: DbSession,
    params: ParamsListado,
    familia_id: UUID | None = None,
    estado: EstadoServicio | None = None,
    ciudad: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> Page[ServicioRead]:
    from app.core.tiempo import ZONA_NEGOCIO

    stmt = select(Servicio)
    if familia_id:
        stmt = stmt.where(Servicio.familia_id == familia_id)
    if estado:
        stmt = stmt.where(Servicio.estado == estado)
    if ciudad:
        stmt = stmt.where(Servicio.ciudad == ciudad)
    if desde:
        stmt = stmt.where(
            Servicio.programado_para >= datetime.combine(desde, time.min, ZONA_NEGOCIO)
        )
    if hasta:
        stmt = stmt.where(
            Servicio.programado_para <= datetime.combine(hasta, time.max, ZONA_NEGOCIO)
        )
    return await paginar(
        db,
        stmt,
        params,
        ServicioRead,
        campos_orden={"programado_para": Servicio.programado_para, "estado": Servicio.estado},
        orden_por_defecto="programado_para",
        desempate=Servicio.id,
    )


@router.post(
    "", response_model=ServicioRead, status_code=status.HTTP_201_CREATED, dependencies=[EQUIPO]
)
async def agendar(db: DbSession, data: ServicioCreate) -> Servicio:
    """F1-SER-01 Agenda contra disponibilidad real; rechaza cupos tomados y familias no
    elegibles (F1-SER-05) con el motivo."""
    familia = await db.run_sync(familias.obtener, data.familia_id)
    mascota = (
        await db.run_sync(familias.obtener_mascota, data.mascota_id) if data.mascota_id else None
    )
    tipo = await db.run_sync(service.tipo_servicio, data.tipo_codigo)
    pendiente = None
    if data.pendiente_id:
        pendiente = await db.run_sync(service.obtener_pendiente, data.pendiente_id)
        if pendiente.estado not in (EstadoPendiente.AUTORIZADO, EstadoPendiente.EN_GESTION):
            raise ReglaNegocio("El pendiente no esta autorizado")
    return await db.run_sync(
        service.agendar,
        familia=familia,
        mascota=mascota,
        tipo=tipo,
        inicio=data.inicio,
        observaciones=data.observaciones,
        pendiente=pendiente,
    )


@router.get("/{servicio_id}", response_model=ServicioRead, dependencies=[EQUIPO])
async def obtener(db: DbSession, servicio_id: UUID) -> Servicio:
    return await db.run_sync(service.obtener, servicio_id)


@router.post("/{servicio_id}/estado", response_model=ServicioRead, dependencies=[EQUIPO])
async def cambiar_estado(db: DbSession, servicio_id: UUID, data: Transicion) -> Servicio:
    """F1-SER-03 Transicion validada, auditada y con sus disparadores."""
    return await db.run_sync(
        service.cambiar_estado,
        await db.run_sync(service.obtener, servicio_id),
        data.estado,
        data.motivo,
    )


@router.post("/{servicio_id}/reprogramar", response_model=ServicioRead, dependencies=[EQUIPO])
async def reprogramar(db: DbSession, servicio_id: UUID, data: Reprogramacion) -> Servicio:
    return await db.run_sync(
        service.reprogramar,
        await db.run_sync(service.obtener, servicio_id),
        data.inicio,
        data.motivo,
    )


@router.post("/{servicio_id}/autorizar", response_model=ServicioRead)
async def autorizar(db: DbSession, usuario: Medico, servicio_id: UUID) -> Servicio:
    return await db.run_sync(
        service.autorizar, await db.run_sync(service.obtener, servicio_id), usuario.id
    )


@router.get("/{servicio_id}/pasos", response_model=list[PasoRead], dependencies=[EQUIPO])
async def pasos(db: DbSession, servicio_id: UUID) -> list[ServicioPaso]:
    await db.run_sync(service.obtener, servicio_id)
    return list(
        await db.scalars(
            select(ServicioPaso)
            .where(ServicioPaso.servicio_id == servicio_id)
            .order_by(ServicioPaso.created_at)
        )
    )


@router.put("/{servicio_id}/pasos/{paso_codigo}", response_model=PasoRead)
async def completar_paso(
    db: DbSession, usuario: Equipo, servicio_id: UUID, paso_codigo: str, data: PasoIn
) -> ServicioPaso:
    """F1-SER-02 Registra un paso del flujo configurado para el tipo de servicio."""
    servicio = await db.run_sync(service.obtener, servicio_id)
    return await db.run_sync(service.completar_paso, servicio, paso_codigo, data.datos, usuario.id)


@router.post(
    "/{servicio_id}/pendientes",
    response_model=PendienteRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[EQUIPO],
)
async def crear_pendiente(db: DbSession, servicio_id: UUID, data: PendienteIn) -> Pendiente:
    """F1-SER-04 Pendiente derivado de la atencion (examen, control, procedimiento)."""
    servicio = await db.run_sync(service.obtener, servicio_id)
    return await db.run_sync(
        service.crear_pendiente, servicio, data.descripcion, data.requiere_autorizacion
    )


@pendientes_router.get("", response_model=list[PendienteRead], dependencies=[EQUIPO])
async def listar_pendientes(
    db: DbSession, estado: str | None = None, servicio_id: UUID | None = None
) -> list[Pendiente]:
    stmt = select(Pendiente).order_by(Pendiente.created_at)
    if estado:
        stmt = stmt.where(Pendiente.estado == estado)
    if servicio_id:
        stmt = stmt.where(Pendiente.servicio_origen_id == servicio_id)
    return list(await db.scalars(stmt))


@pendientes_router.post("/{pendiente_id}/autorizacion", response_model=PendienteRead)
async def autorizar_pendiente(
    db: DbSession, usuario: Equipo, pendiente_id: UUID, data: AutorizacionPendiente
) -> Pendiente:
    """Registra la autorizacion de la familia: quien la recibio, cuando y por que medio."""
    pendiente = await db.run_sync(service.obtener_pendiente, pendiente_id)
    return await db.run_sync(
        service.autorizar_pendiente, pendiente, usuario.id, data.medio, data.aprobado
    )


@pendientes_router.post(
    "/{pendiente_id}/avance", response_model=PendienteRead, dependencies=[EQUIPO]
)
async def avanzar_pendiente(db: DbSession, pendiente_id: UUID, data: AvancePendiente) -> Pendiente:
    pendiente = await db.run_sync(service.obtener_pendiente, pendiente_id)
    return await db.run_sync(service.avanzar_pendiente, pendiente, data.estado, data.resolucion)

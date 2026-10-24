"""6.7 Rutas domiciliarias: planeacion, ejecucion y cambios en caliente."""

from datetime import date, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.core.deps import INTERNOS, DbSession, requiere
from app.core.enums import Rol
from app.modules.archivos import service as archivos
from app.modules.auth.models import Usuario
from app.modules.rutas import service
from app.modules.rutas.models import PlanificacionRuta, Ruta

router = APIRouter(prefix="/rutas", tags=["rutas"])

EQUIPO = Depends(requiere(*INTERNOS))
# Planear y rehacer rutas es de operaciones; ejecutarlas, de quien sale a campo.
Operaciones = Annotated[Usuario, Depends(requiere(Rol.OPERACIONES, Rol.ADMIN))]
Campo = Annotated[Usuario, Depends(requiere(Rol.MEDICO, Rol.OPERACIONES, Rol.ADMIN))]


class PlanificacionIn(BaseModel):
    fecha: date
    ciudad: str
    responsables: list[UUID] = Field(min_length=1, max_length=30)


class PlanificacionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    fecha: date
    ciudad: str
    responsables: list[str]
    estado: str
    resultado: dict[str, Any]
    error: str | None
    created_at: datetime


class OmisionIn(BaseModel):
    motivo: str = Field(min_length=3, max_length=255)
    cancelar_servicio: bool = False


class AgregarIn(BaseModel):
    servicio_id: UUID


@router.post(
    "/planificaciones", response_model=PlanificacionRead, status_code=status.HTTP_202_ACCEPTED
)
async def planificar(
    db: DbSession, usuario: Operaciones, data: PlanificacionIn
) -> PlanificacionRuta:
    """F2-RUT-01..03 La optimizacion corre en el worker; consulte el estado con GET."""
    return await db.run_sync(
        service.solicitar, data.fecha, data.ciudad, data.responsables, usuario.id
    )


@router.get(
    "/planificaciones/{planificacion_id}",
    response_model=PlanificacionRead,
    dependencies=[EQUIPO],
)
async def planificacion(db: DbSession, planificacion_id: UUID) -> PlanificacionRuta:
    p = await db.get(PlanificacionRuta, planificacion_id)
    if p is None:
        from app.core.errores import NoEncontrado

        raise NoEncontrado("Planificacion no encontrada")
    return p


@router.get("/por-rutear", dependencies=[EQUIPO])
async def por_rutear(db: DbSession, fecha: date, ciudad: str) -> list[dict[str, Any]]:
    servicios = await db.run_sync(service.por_rutear, fecha, ciudad)
    return [
        {"id": s.id, "familia_id": s.familia_id, "programado_para": s.programado_para}
        for s in servicios
    ]


@router.get("", dependencies=[EQUIPO])
async def listar(
    db: DbSession,
    fecha: date,
    ciudad: str | None = None,
    responsable_id: UUID | None = None,
    incluir_canceladas: bool = False,
) -> list[dict[str, Any]]:
    stmt = select(Ruta).where(Ruta.fecha == fecha)
    if ciudad:
        stmt = stmt.where(Ruta.ciudad == ciudad)
    if responsable_id:
        stmt = stmt.where(Ruta.responsable_id == responsable_id)
    if not incluir_canceladas:
        stmt = stmt.where(Ruta.estado != "cancelada")
    return [service.presentar(r) for r in await db.scalars(stmt.order_by(Ruta.created_at))]


@router.get("/{ruta_id}", dependencies=[EQUIPO])
async def obtener(db: DbSession, ruta_id: UUID) -> dict[str, Any]:
    return await db.run_sync(lambda s: service.presentar(service.obtener(s, ruta_id)))


@router.post("/{ruta_id}/cancelacion")
async def cancelar(db: DbSession, _: Operaciones, ruta_id: UUID) -> dict[str, Any]:
    return await db.run_sync(
        lambda s: service.presentar(service.cancelar(s, service.obtener(s, ruta_id)))
    )


# --- F2-RUT-04 Ejecucion ----------------------------------------------------------------------


@router.post("/{ruta_id}/inicio")
async def iniciar(db: DbSession, usuario: Campo, ruta_id: UUID) -> dict[str, Any]:
    return await db.run_sync(
        lambda s: service.presentar(service.iniciar(s, service.obtener(s, ruta_id), usuario.id))
    )


@router.post("/paradas/{parada_id}/en-camino")
async def en_camino(db: DbSession, usuario: Campo, parada_id: UUID) -> dict[str, Any]:
    """El servicio pasa a en ruta y la familia recibe el aviso de que el tecnico va."""
    return await db.run_sync(
        lambda s: service.presentar(
            service.en_camino(s, service.obtener_parada(s, parada_id), usuario.id).ruta
        )
    )


@router.post("/paradas/{parada_id}/llegada")
async def llegada(db: DbSession, usuario: Campo, parada_id: UUID) -> dict[str, Any]:
    return await db.run_sync(
        lambda s: service.presentar(
            service.llegada(s, service.obtener_parada(s, parada_id), usuario.id).ruta
        )
    )


@router.post("/paradas/{parada_id}/salida")
async def salida(
    db: DbSession,
    usuario: Campo,
    parada_id: UUID,
    nota: Annotated[str | None, Form(max_length=2000)] = None,
    evidencia: Annotated[UploadFile | None, File(description="Foto o PDF de la visita")] = None,
) -> dict[str, Any]:
    contenido = await archivos.leer(evidencia, "adjunto_clinico") if evidencia else None
    nombre = evidencia.filename if evidencia else None
    return await db.run_sync(
        lambda s: service.presentar(
            service.salida(
                s,
                service.obtener_parada(s, parada_id),
                usuario.id,
                nota=nota,
                evidencia=contenido,
                nombre_evidencia=nombre,
            ).ruta
        )
    )


# --- F2-RUT-05 Cambios en caliente ------------------------------------------------------------


@router.post("/paradas/{parada_id}/omision")
async def omitir(db: DbSession, usuario: Campo, parada_id: UUID, data: OmisionIn) -> dict[str, Any]:
    """Saca la parada; el resto se renumera y se reestima sin rehacer la ruta."""
    return await db.run_sync(
        lambda s: service.presentar(
            service.omitir(
                s,
                service.obtener_parada(s, parada_id),
                data.motivo,
                cancelar_servicio=data.cancelar_servicio,
                usuario_id=usuario.id,
            ).ruta
        )
    )


@router.post("/{ruta_id}/paradas", status_code=status.HTTP_201_CREATED)
async def agregar(db: DbSession, _: Operaciones, ruta_id: UUID, data: AgregarIn) -> dict[str, Any]:
    """Inserta el servicio donde menos tiempo agrega."""
    return await db.run_sync(
        lambda s: service.presentar(
            service.agregar(s, service.obtener(s, ruta_id), data.servicio_id).ruta
        )
    )

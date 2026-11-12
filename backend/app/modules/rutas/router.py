"""6.7 Rutas domiciliarias: planeacion, ejecucion y cambios en caliente."""

from datetime import date, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.api.deps import INTERNOS, DbSession, requiere
from app.core.enums import EstadoParada, EstadoRuta, Rol
from app.core.errores import NoEncontrado
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


class FamiliaDeParada(BaseModel):
    """A quien se visita y donde. Sin revalidar formatos: es lectura."""

    id: UUID
    titular_nombre: str
    telefono: str
    direccion: str | None
    complemento: str | None
    # None cuando la familia no lo tiene registrado (migracion 0028).
    barrio: str | None


class MascotaDeParada(BaseModel):
    id: UUID
    nombre: str
    especie: str
    fecha_nacimiento: date | None
    peso_kg: float | None


class PorRutearRead(BaseModel):
    """Un servicio a domicilio del dia que aun no esta en ninguna ruta."""

    id: UUID
    familia_id: UUID
    ciudad: str
    programado_para: datetime | None
    tipo_codigo: str
    observaciones: str | None
    ventana_desde: datetime | None
    ventana_hasta: datetime | None
    familia: FamiliaDeParada
    mascota: MascotaDeParada | None


class ParadaRead(BaseModel):
    id: UUID
    servicio_id: UUID
    orden: int
    estado: EstadoParada
    latitud: float | None
    longitud: float | None
    llegada_estimada: datetime | None
    llegada_en: datetime | None
    salida_en: datetime | None
    nota: str | None
    motivo_omision: str | None
    tipo_codigo: str
    observaciones: str | None
    # La ventana acordada con la familia: desde la hora agendada (F2-RUT-03).
    ventana_desde: datetime | None
    ventana_hasta: datetime | None
    familia: FamiliaDeParada
    mascota: MascotaDeParada | None


class RutaRead(BaseModel):
    id: UUID
    fecha: date
    ciudad: str
    responsable_id: UUID | None
    estado: EstadoRuta
    distancia_km: float | None
    duracion_min: int | None
    inicio_real: datetime | None
    fin_real: datetime | None
    paradas: list[ParadaRead]


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
        raise NoEncontrado("Planificacion no encontrada")
    return p


@router.get("/por-rutear", response_model=list[PorRutearRead], dependencies=[EQUIPO])
async def por_rutear(db: DbSession, fecha: date, ciudad: str | None = None) -> list[dict[str, Any]]:
    return await db.run_sync(
        lambda s: service.presentar_por_rutear(s, service.por_rutear(s, fecha, ciudad))
    )


@router.get("", response_model=list[RutaRead], dependencies=[EQUIPO])
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
    rutas = list(await db.scalars(stmt.order_by(Ruta.created_at)))
    return await db.run_sync(service.presentar_varias, rutas)


@router.get("/{ruta_id}", response_model=RutaRead, dependencies=[EQUIPO])
async def obtener(db: DbSession, ruta_id: UUID) -> dict[str, Any]:
    return await db.run_sync(lambda s: service.presentar(s, service.obtener(s, ruta_id)))


@router.post("/{ruta_id}/cancelacion", response_model=RutaRead)
async def cancelar(db: DbSession, _: Operaciones, ruta_id: UUID) -> dict[str, Any]:
    return await db.run_sync(
        lambda s: service.presentar(s, service.cancelar(s, service.obtener(s, ruta_id)))
    )


# --- F2-RUT-04 Ejecucion ----------------------------------------------------------------------


@router.post("/{ruta_id}/inicio", response_model=RutaRead)
async def iniciar(db: DbSession, usuario: Campo, ruta_id: UUID) -> dict[str, Any]:
    return await db.run_sync(
        lambda s: service.presentar(s, service.iniciar(s, service.obtener(s, ruta_id), usuario.id))
    )


@router.post("/paradas/{parada_id}/en-camino", response_model=RutaRead)
async def en_camino(db: DbSession, usuario: Campo, parada_id: UUID) -> dict[str, Any]:
    """El servicio pasa a en ruta y la familia recibe el aviso de que el tecnico va."""
    return await db.run_sync(
        lambda s: service.presentar(
            s, service.en_camino(s, service.obtener_parada(s, parada_id), usuario.id).ruta
        )
    )


@router.post("/paradas/{parada_id}/llegada", response_model=RutaRead)
async def llegada(db: DbSession, usuario: Campo, parada_id: UUID) -> dict[str, Any]:
    return await db.run_sync(
        lambda s: service.presentar(
            s, service.llegada(s, service.obtener_parada(s, parada_id), usuario.id).ruta
        )
    )


@router.post("/paradas/{parada_id}/salida", response_model=RutaRead)
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
            s,
            service.salida(
                s,
                service.obtener_parada(s, parada_id),
                usuario.id,
                nota=nota,
                evidencia=contenido,
                nombre_evidencia=nombre,
            ).ruta,
        )
    )


# --- F2-RUT-05 Cambios en caliente ------------------------------------------------------------


@router.post("/paradas/{parada_id}/omision", response_model=RutaRead)
async def omitir(db: DbSession, usuario: Campo, parada_id: UUID, data: OmisionIn) -> dict[str, Any]:
    """Saca la parada; el resto se renumera y se reestima sin rehacer la ruta."""
    return await db.run_sync(
        lambda s: service.presentar(
            s,
            service.omitir(
                s,
                service.obtener_parada(s, parada_id),
                data.motivo,
                cancelar_servicio=data.cancelar_servicio,
                usuario_id=usuario.id,
            ).ruta,
        )
    )


@router.post("/{ruta_id}/paradas", response_model=RutaRead, status_code=status.HTTP_201_CREATED)
async def agregar(db: DbSession, _: Operaciones, ruta_id: UUID, data: AgregarIn) -> dict[str, Any]:
    """Inserta el servicio donde menos tiempo agrega."""
    return await db.run_sync(
        lambda s: service.presentar(
            s, service.agregar(s, service.obtener(s, ruta_id), data.servicio_id).ruta
        )
    )

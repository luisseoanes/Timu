"""6.8 / 6.9 / 6.13 / 6.15 Calendario preventivo, autorizacion, agenda y carnet."""

from datetime import date, datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field

from app.core.deps import INTERNOS, DbSession, publico, requiere
from app.core.enums import Rol
from app.modules.archivos import service as archivos
from app.modules.archivos.models import Archivo
from app.modules.auth.models import Usuario
from app.modules.preventivos import service
from app.modules.preventivos.models import EventoPreventivo
from app.schemas.common import Page, ParamsListado, paginar

router = APIRouter(prefix="/preventivos", tags=["preventivos"])
verificacion_router = APIRouter(prefix="/verificacion", tags=["preventivos"])

EQUIPO = Depends(requiere(*INTERNOS))
Equipo = Annotated[Usuario, Depends(requiere(*INTERNOS))]
# Aplicar un preventivo es un acto clinico.
Clinico = Annotated[Usuario, Depends(requiere(Rol.MEDICO, Rol.ADMIN))]

ORDEN = {
    "fecha_programada": EventoPreventivo.fecha_programada,
    "created_at": EventoPreventivo.created_at,
}


class EventoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    mascota_id: UUID
    esquema_codigo: str | None
    tipo: str
    dosis_numero: int
    es_refuerzo: bool
    estado: str
    fecha_programada: date
    fecha_aplicacion: date | None
    proxima_fecha: date | None
    producto: str | None
    lote: str | None
    requiere_autorizacion: bool
    autorizado: bool
    medio_autorizacion: str | None
    autorizado_en: datetime | None
    notificado_en: datetime | None
    servicio_id: UUID | None


class AutorizacionIn(BaseModel):
    medio: Literal["whatsapp", "telefono", "presencial", "portal", "formulario"]
    aprobado: bool = True


class AplicacionIn(BaseModel):
    fecha: date
    producto: str = Field(min_length=2, max_length=120)
    lote: str | None = Field(default=None, max_length=60)
    servicio_id: UUID | None = None


class AgendarIn(BaseModel):
    inicio: datetime
    observaciones: str | None = None


class CancelacionIn(BaseModel):
    motivo: str = Field(min_length=3, max_length=255)


class CarnetEmitidoRead(BaseModel):
    codigo: str
    url: str
    sha256: str


@router.get("", response_model=Page[EventoRead], dependencies=[EQUIPO])
async def listar(
    db: DbSession,
    params: ParamsListado,
    mascota_id: UUID | None = None,
    estado: Literal["programado", "aplicado", "cancelado"] | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    pendientes_autorizacion: bool = False,
) -> Page[EventoRead]:
    return await paginar(
        db,
        service.consulta(
            mascota_id=mascota_id,
            estado=estado,
            desde=desde,
            hasta=hasta,
            pendientes_autorizacion=pendientes_autorizacion,
        ),
        params,
        EventoRead,
        campos_orden=ORDEN,
        orden_por_defecto="fecha_programada",
        desempate=EventoPreventivo.id,
    )


@router.post(
    "/mascotas/{mascota_id}/calendario",
    response_model=list[EventoRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[EQUIPO],
)
async def calendarizar(db: DbSession, mascota_id: UUID) -> list[EventoPreventivo]:
    """Programa los esquemas que la mascota aun no tenga (p. ej. tras crear uno nuevo)."""
    mascota = await db.run_sync(service._mascota, mascota_id)
    return await db.run_sync(service.calendario_inicial, mascota, date.today())


@router.post("/{evento_id}/autorizacion", response_model=EventoRead)
async def autorizar(
    db: DbSession, usuario: Equipo, evento_id: UUID, data: AutorizacionIn
) -> EventoPreventivo:
    """F2-PRE-03 Registra la autorizacion de la familia, con quien y por que medio."""
    evento = await db.run_sync(service.obtener, evento_id)
    return await db.run_sync(service.autorizar, evento, usuario.id, data.medio, data.aprobado)


@router.post("/{evento_id}/aplicacion", response_model=EventoRead)
async def aplicar(
    db: DbSession, usuario: Clinico, evento_id: UUID, data: AplicacionIn
) -> EventoPreventivo:
    """F2-PRE-02 Registra la aplicacion y programa la siguiente dosis o refuerzo."""
    evento = await db.run_sync(service.obtener, evento_id)
    return await db.run_sync(
        lambda s: service.aplicar(
            s,
            evento,
            fecha=data.fecha,
            producto=data.producto,
            lote=data.lote,
            usuario_id=usuario.id,
            servicio_id=data.servicio_id,
        )
    )


@router.post("/{evento_id}/agendar", response_model=EventoRead, dependencies=[EQUIPO])
async def agendar(db: DbSession, evento_id: UUID, data: AgendarIn) -> EventoPreventivo:
    """F2-PRE-04 Convierte el evento en un servicio agendado contra la disponibilidad real."""
    evento = await db.run_sync(service.obtener, evento_id)
    return await db.run_sync(service.agendar, evento, data.inicio, data.observaciones)


@router.post("/{evento_id}/cancelacion", response_model=EventoRead, dependencies=[EQUIPO])
async def cancelar(db: DbSession, evento_id: UUID, data: CancelacionIn) -> EventoPreventivo:
    evento = await db.run_sync(service.obtener, evento_id)
    return await db.run_sync(service.cancelar, evento, data.motivo)


@router.get("/mascotas/{mascota_id}/carnet", dependencies=[EQUIPO])
async def carnet(db: DbSession, mascota_id: UUID) -> dict[str, Any]:
    """F2-PRE-05 Lo aplicado, lo vencido y lo proximo."""
    return await db.run_sync(service.carnet, mascota_id)


@router.post(
    "/mascotas/{mascota_id}/carnet/pdf",
    response_model=CarnetEmitidoRead,
    status_code=status.HTTP_201_CREATED,
)
async def emitir_carnet(db: DbSession, usuario: Equipo, mascota_id: UUID) -> CarnetEmitidoRead:
    """F2-PRE-06 PDF con codigo de verificacion; la URL es firmada y de vida corta."""
    registro = await db.run_sync(service.emitir_carnet, mascota_id, usuario.id)
    archivo = await db.get(Archivo, registro.archivo_id)
    assert archivo is not None
    return CarnetEmitidoRead(
        codigo=registro.codigo, url=archivos.url(archivo), sha256=registro.sha256
    )


@verificacion_router.get("/carnets/{codigo}", dependencies=[Depends(publico)])
async def verificar_carnet(db: DbSession, codigo: str) -> dict[str, Any]:
    """Publico a proposito: un tercero confirma que el carnet es autentico con el codigo
    impreso. Solo devuelve lo que el carnet ya mostraba, sin datos de la familia."""
    return await db.run_sync(service.verificar_carnet, codigo)

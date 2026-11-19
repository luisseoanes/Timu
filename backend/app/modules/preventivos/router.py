"""6.8 / 6.9 / 6.13 / 6.15 Calendario preventivo, autorizacion, agenda y carnet."""

from datetime import date, datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import DbSession, publico, requiere
from app.core.enums import Rol
from app.core.tiempo import hoy
from app.modules.archivos import service as archivos
from app.modules.archivos.models import Archivo
from app.modules.auth.models import Usuario
from app.modules.preventivos import service
from app.modules.preventivos.models import EventoPreventivo
from app.schemas.common import Page, ParamsListado, paginar

router = APIRouter(prefix="/preventivos", tags=["preventivos"])
verificacion_router = APIRouter(prefix="/verificacion", tags=["preventivos"])

# Perfiles de cada ruta (Seccion 12, docs/perfiles-y-permisos.md).
ATENCION = Depends(requiere(Rol.ATENCION_CLIENTE))
ATENCION_OPERACIONES_Y_MEDICO = Depends(requiere(Rol.ATENCION_CLIENTE, Rol.OPERACIONES, Rol.MEDICO))
ATENCION_Y_MEDICO = Depends(requiere(Rol.ATENCION_CLIENTE, Rol.MEDICO))
Atencion = Annotated[Usuario, Depends(requiere(Rol.ATENCION_CLIENTE))]
AtencionYMedico = Annotated[Usuario, Depends(requiere(Rol.ATENCION_CLIENTE, Rol.MEDICO))]
AtencionYOperaciones = Annotated[Usuario, Depends(requiere(Rol.ATENCION_CLIENTE, Rol.OPERACIONES))]
Medico = Annotated[Usuario, Depends(requiere(Rol.MEDICO))]
# Aplicar un preventivo es un acto clinico.

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
    peso_kg: float | None
    aplicado_por_nombre: str | None
    requiere_autorizacion: bool
    autorizado: bool
    medio_autorizacion: str | None
    autorizado_en: datetime | None
    notificado_en: datetime | None
    servicio_id: UUID | None
    tipo_servicio_codigo: str = Field(
        description="Con que tipo de servicio se agenda su visita (para pedir las franjas)"
    )


class VisitaPreventivo(BaseModel):
    id: UUID
    programado_para: datetime
    estado: str


class EventoBandeja(EventoRead):
    """Un preventivo en la bandeja: a quien se aplica, que es y que toca hacer con el."""

    nombre: str = Field(description="El nombre del esquema, p. ej. Rabia")
    mascota_nombre: str
    especie: str
    siguiente: Literal["autorizar", "agendar", "visita"]
    visita: VisitaPreventivo | None


class FamiliaBandeja(BaseModel):
    familia_id: UUID
    titular_nombre: str
    ciudad: str
    telefono: str
    eventos: list[EventoBandeja]


class RecuentosBandeja(BaseModel):
    por_autorizar: int
    por_agendar: int
    agendados: int
    todos: int


class AutorizacionIn(BaseModel):
    medio: Literal["whatsapp", "telefono", "presencial", "portal", "formulario"]
    aprobado: bool = True


class AutorizacionesIn(AutorizacionIn):
    eventos: list[UUID] = Field(min_length=1, max_length=50)


class AplicacionIn(BaseModel):
    fecha: date
    producto: str = Field(min_length=2, max_length=120)
    lote: str | None = Field(default=None, max_length=60)
    peso_kg: float | None = Field(default=None, gt=0, lt=150)
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


@router.get("", response_model=Page[EventoRead], dependencies=[ATENCION_OPERACIONES_Y_MEDICO])
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


@router.get(
    "/bandeja", response_model=Page[FamiliaBandeja], dependencies=[ATENCION_OPERACIONES_Y_MEDICO]
)
async def bandeja(
    db: DbSession,
    vista: Literal["por_autorizar", "por_agendar", "agendados", "todos"] = "por_autorizar",
    ciudad: str | None = None,
    q: str | None = None,
    familia_id: UUID | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> Page[FamiliaBandeja]:
    """R2-PAN-08 Lo que falta por autorizar, por agendar o lo ya agendado, por familia y con el
    siguiente paso de cada preventivo. Con `familia_id`, los de una familia (su linea)."""
    grupos, total = await db.run_sync(
        lambda s: service.bandeja(
            s, vista, ciudad=ciudad, q=q, familia_id=familia_id, limit=limit, offset=offset
        )
    )
    return Page(
        items=[
            FamiliaBandeja(
                **{k: v for k, v in g.items() if k != "eventos"},
                eventos=[
                    EventoBandeja(
                        **EventoRead.model_validate(e["evento"]).model_dump(),
                        **{k: v for k, v in e.items() if k != "evento"},
                    )
                    for e in g["eventos"]
                ],
            )
            for g in grupos
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/bandeja/recuentos",
    response_model=RecuentosBandeja,
    dependencies=[ATENCION_OPERACIONES_Y_MEDICO],
)
async def recuentos_bandeja(
    db: DbSession, ciudad: str | None = None, q: str | None = None
) -> dict[str, int]:
    return await db.run_sync(lambda s: service.recuentos_bandeja(s, ciudad=ciudad, q=q))


@router.post("/autorizaciones", response_model=list[EventoRead])
async def autorizar_varios(
    db: DbSession, usuario: Atencion, data: AutorizacionesIn
) -> list[EventoPreventivo]:
    """6.9 La familia autoriza (o no) de una vez varios preventivos."""
    return await db.run_sync(
        service.autorizar_varios, data.eventos, usuario.id, data.medio, data.aprobado
    )


@router.post(
    "/mascotas/{mascota_id}/calendario",
    response_model=list[EventoRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[ATENCION_Y_MEDICO],
)
async def calendarizar(db: DbSession, mascota_id: UUID) -> list[EventoPreventivo]:
    """Programa los esquemas que la mascota aun no tenga (p. ej. tras crear uno nuevo)."""
    mascota = await db.run_sync(service._mascota, mascota_id)
    return await db.run_sync(service.calendario_inicial, mascota, hoy())


@router.post("/{evento_id}/autorizacion", response_model=EventoRead)
async def autorizar(
    db: DbSession, usuario: Atencion, evento_id: UUID, data: AutorizacionIn
) -> EventoPreventivo:
    """6.9 Registra la autorizacion de la familia, con quien y por que medio."""
    evento = await db.run_sync(service.obtener, evento_id)
    return await db.run_sync(service.autorizar, evento, usuario.id, data.medio, data.aprobado)


@router.post("/{evento_id}/aplicacion", response_model=EventoRead)
async def aplicar(
    db: DbSession, usuario: Medico, evento_id: UUID, data: AplicacionIn
) -> EventoPreventivo:
    """6.8 Registra la aplicacion y programa la siguiente dosis o refuerzo."""
    evento = await db.run_sync(service.obtener, evento_id)
    return await db.run_sync(
        lambda s: service.aplicar(
            s,
            evento,
            fecha=data.fecha,
            producto=data.producto,
            lote=data.lote,
            peso_kg=data.peso_kg,
            usuario_id=usuario.id,
            aplicado_por_nombre=usuario.nombre,
            servicio_id=data.servicio_id,
        )
    )


@router.post("/{evento_id}/agendar", response_model=EventoRead)
async def agendar(
    db: DbSession, usuario: AtencionYOperaciones, evento_id: UUID, data: AgendarIn
) -> EventoPreventivo:
    """6.8 Convierte el evento en un servicio agendado contra la disponibilidad real."""
    evento = await db.run_sync(service.obtener, evento_id)
    return await db.run_sync(
        lambda s: service.agendar(s, evento, data.inicio, data.observaciones, usuario_id=usuario.id)
    )


@router.post("/{evento_id}/cancelacion", response_model=EventoRead, dependencies=[ATENCION])
async def cancelar(db: DbSession, evento_id: UUID, data: CancelacionIn) -> EventoPreventivo:
    evento = await db.run_sync(service.obtener, evento_id)
    return await db.run_sync(service.cancelar, evento, data.motivo)


@router.get("/mascotas/{mascota_id}/carnet", dependencies=[ATENCION_Y_MEDICO])
async def carnet(db: DbSession, mascota_id: UUID) -> dict[str, Any]:
    """6.15 Lo aplicado, lo vencido y lo proximo."""
    return await db.run_sync(service.carnet, mascota_id)


@router.post(
    "/mascotas/{mascota_id}/carnet/pdf",
    response_model=CarnetEmitidoRead,
    status_code=status.HTTP_201_CREATED,
)
async def emitir_carnet(
    db: DbSession, usuario: AtencionYMedico, mascota_id: UUID
) -> CarnetEmitidoRead:
    """6.15 PDF con codigo de verificacion; la URL es firmada y de vida corta."""
    registro = await db.run_sync(service.emitir_carnet, mascota_id, usuario.id)
    archivo = await db.get(Archivo, registro.archivo_id)
    assert archivo is not None
    return CarnetEmitidoRead(
        codigo=registro.codigo, url=archivos.url(archivo), sha256=registro.sha256
    )


class MascotaVerificada(BaseModel):
    nombre: str
    especie: str | None
    raza: str | None


class AplicacionVerificada(BaseModel):
    nombre: str
    dosis: str | None  # «Dosis 2, refuerzo»; solo las vacunas
    fecha_aplicacion: date | None
    producto: str | None
    lote: str | None
    peso_kg: float | None
    aplicado_por: str | None
    proxima_fecha: date | None


class SeccionVerificada(BaseModel):
    tipo: Literal["vacuna", "desparasitacion_interna", "desparasitacion_externa"]
    titulo: str
    aplicados: list[AplicacionVerificada]


class PendienteVerificado(BaseModel):
    nombre: str
    dosis: str | None
    fecha_programada: date
    vencido: bool  # ya debia aplicarse el dia que se emitio el carnet


class CarnetVerificadoRead(BaseModel):
    """6.15 Lo que decia el carnet al emitirse: las secciones del PDF y lo pendiente.
    `pendientes` es None en un carnet emitido antes de guardarlo."""

    codigo: str
    emitido_en: datetime
    sha256: str
    mascota: MascotaVerificada
    secciones: list[SeccionVerificada]
    pendientes: list[PendienteVerificado] | None


@verificacion_router.get(
    "/carnets/{codigo}", response_model=CarnetVerificadoRead, dependencies=[Depends(publico)]
)
async def verificar_carnet(db: DbSession, codigo: str) -> dict[str, Any]:
    """Publico a proposito: un tercero confirma que el carnet es autentico con el codigo
    impreso. Solo devuelve lo que el carnet ya mostraba, sin datos de la familia."""
    return await db.run_sync(service.verificar_carnet, codigo)

"""6.11 Comercial automatizado: embudo de interesados y conversacion por WhatsApp."""

from datetime import date, datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import func, or_, select

from app.core.deps import DbSession, requiere
from app.core.enums import Rol
from app.modules.auth.models import Usuario
from app.modules.comercial import conversacion, service
from app.modules.comercial.models import ArbolConversacion, ConversacionComercial, Interesado
from app.schemas.common import Page, ParamsListado, paginar

router = APIRouter(prefix="/comercial", tags=["comercial"])

EQUIPO_COMERCIAL = Depends(requiere(Rol.ADMIN, Rol.COMERCIAL))
Comercial = Annotated[Usuario, Depends(requiere(Rol.ADMIN, Rol.COMERCIAL))]
ADMIN = Depends(requiere(Rol.ADMIN))


class InteresadoIn(BaseModel):
    nombre: str | None = Field(default=None, max_length=160)
    telefono: str | None = None
    email: EmailStr | None = None
    ciudad: str | None = None
    origen: Literal["panel", "referido", "evento", "campana", "whatsapp", "formulario"] = "panel"


class InteresadoUpdate(BaseModel):
    nombre: str | None = Field(default=None, max_length=160)
    ciudad: str | None = None
    responsable_id: UUID | None = None
    etapa: Literal["contactado", "cotizado", "en_afiliacion"] | None = None


class InteresadoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str | None
    telefono: str | None
    email: str | None
    ciudad: str | None
    origen: str
    etapa: str
    responsable_id: UUID | None
    familia_id: UUID | None
    plan_sugerido: str | None
    datos: dict[str, Any]
    motivo_perdida: str | None
    ultimo_contacto: datetime | None
    created_at: datetime


class PerdidaIn(BaseModel):
    motivo: str = Field(min_length=3, max_length=255)


class ConversacionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    telefono: str
    interesado_id: UUID | None
    nodo: str
    datos: dict[str, Any]
    estado: str
    asesor_id: UUID | None
    tarea_id: UUID | None
    updated_at: datetime


class MensajeAsesorIn(BaseModel):
    texto: str = Field(min_length=1, max_length=4000)


class ArbolIn(BaseModel):
    nodos: dict[str, Any]
    nota: str | None = None


ORDEN = {"created_at": Interesado.created_at, "ultimo_contacto": Interesado.ultimo_contacto}


# --- F3-COM-01 Embudo -------------------------------------------------------------------------


@router.get("/interesados", response_model=Page[InteresadoRead], dependencies=[EQUIPO_COMERCIAL])
async def listar(
    db: DbSession,
    params: ParamsListado,
    etapa: str | None = None,
    origen: str | None = None,
    responsable_id: UUID | None = None,
    q: str | None = None,
) -> Page[InteresadoRead]:
    stmt = select(Interesado)
    if etapa:
        stmt = stmt.where(Interesado.etapa == etapa)
    if origen:
        stmt = stmt.where(Interesado.origen == origen)
    if responsable_id:
        stmt = stmt.where(Interesado.responsable_id == responsable_id)
    if q:
        patron = f"%{q}%"
        stmt = stmt.where(or_(Interesado.nombre.ilike(patron), Interesado.telefono.ilike(patron)))
    return await paginar(
        db,
        stmt,
        params,
        InteresadoRead,
        campos_orden=ORDEN,
        orden_por_defecto="-created_at",
        desempate=Interesado.id,
    )


@router.post(
    "/interesados",
    response_model=InteresadoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[EQUIPO_COMERCIAL],
)
async def registrar(db: DbSession, data: InteresadoIn) -> Interesado:
    return await db.run_sync(
        lambda s: service.registrar(
            s,
            origen=data.origen,
            telefono=data.telefono,
            nombre=data.nombre,
            email=str(data.email) if data.email else None,
            ciudad=data.ciudad,
        )
    )


@router.patch(
    "/interesados/{interesado_id}", response_model=InteresadoRead, dependencies=[EQUIPO_COMERCIAL]
)
async def actualizar(db: DbSession, interesado_id: UUID, data: InteresadoUpdate) -> Interesado:
    interesado = await db.run_sync(service.obtener, interesado_id)
    cambios = data.model_dump(exclude_unset=True)
    etapa = cambios.pop("etapa", None)
    for campo, valor in cambios.items():
        setattr(interesado, campo, valor)
    if etapa:
        service.avanzar(interesado, etapa)
    await db.flush()
    return interesado


@router.post(
    "/interesados/{interesado_id}/perdida",
    response_model=InteresadoRead,
    dependencies=[EQUIPO_COMERCIAL],
)
async def perder(db: DbSession, interesado_id: UUID, data: PerdidaIn) -> Interesado:
    interesado = await db.run_sync(service.obtener, interesado_id)
    return await db.run_sync(service.perder, interesado, data.motivo)


@router.post(
    "/interesados/{interesado_id}/reactivacion",
    response_model=InteresadoRead,
    dependencies=[EQUIPO_COMERCIAL],
)
async def reactivar(db: DbSession, interesado_id: UUID) -> Interesado:
    interesado = await db.run_sync(service.obtener, interesado_id)
    return await db.run_sync(service.reactivar, interesado)


@router.get("/embudo", dependencies=[EQUIPO_COMERCIAL])
async def embudo(db: DbSession, desde: date, hasta: date) -> dict[str, Any]:
    return await db.run_sync(service.embudo, desde, hasta)


# --- F3-COM-02 / 04 Conversaciones ------------------------------------------------------------


@router.get(
    "/conversaciones", response_model=list[ConversacionRead], dependencies=[EQUIPO_COMERCIAL]
)
async def conversaciones(
    db: DbSession, estado: Literal["automatica", "con_asesor"] | None = "con_asesor"
) -> list[ConversacionComercial]:
    stmt = select(ConversacionComercial).order_by(ConversacionComercial.updated_at.desc())
    if estado:
        stmt = stmt.where(ConversacionComercial.estado == estado)
    return list(await db.scalars(stmt.limit(200)))


@router.post("/conversaciones/{conversacion_id}/mensajes", status_code=status.HTTP_201_CREATED)
async def responder_como_asesor(
    db: DbSession, usuario: Comercial, conversacion_id: UUID, data: MensajeAsesorIn
) -> dict[str, str]:
    """El asesor contesta por el mismo canal (dentro de la ventana de 24 horas)."""
    from app.modules.comunicaciones import service as comunicaciones

    conv = await db.get(ConversacionComercial, conversacion_id)
    if conv is None:
        from app.core.errores import NoEncontrado

        raise NoEncontrado("Conversacion no encontrada")
    conv.asesor_id = conv.asesor_id or usuario.id
    mensaje = await db.run_sync(
        lambda s: comunicaciones.encolar_texto(s, telefono=conv.telefono, texto=data.texto)
    )
    return {"mensaje_id": str(mensaje.id)}


@router.post(
    "/conversaciones/{conversacion_id}/liberacion",
    response_model=ConversacionRead,
    dependencies=[EQUIPO_COMERCIAL],
)
async def liberar(db: DbSession, conversacion_id: UUID) -> ConversacionRead:
    """El asesor termina: vuelve el asistente para la proxima vez que la persona escriba."""
    conv = await db.get(ConversacionComercial, conversacion_id)
    if conv is None:
        from app.core.errores import NoEncontrado

        raise NoEncontrado("Conversacion no encontrada")
    # Se serializa dentro de la sesion: tras el flush, updated_at queda por recargar.
    return await db.run_sync(
        lambda s: ConversacionRead.model_validate(conversacion.liberar(s, conv))
    )


@router.get("/arbol", dependencies=[EQUIPO_COMERCIAL])
async def arbol(db: DbSession) -> dict[str, Any]:
    return await db.run_sync(conversacion.arbol)


@router.put("/arbol", dependencies=[ADMIN])
async def publicar_arbol(db: DbSession, data: ArbolIn) -> dict[str, Any]:
    """Valida y activa una version nueva del arbol; la anterior queda guardada."""
    conversacion.validar_arbol(data.nodos)
    ultima = await db.scalar(select(func.max(ArbolConversacion.version))) or 0
    for anterior in await db.scalars(
        select(ArbolConversacion).where(ArbolConversacion.activo.is_(True))
    ):
        anterior.activo = False
    nuevo = ArbolConversacion(version=ultima + 1, nodos=data.nodos, activo=True, nota=data.nota)
    db.add(nuevo)
    await db.flush()
    return {"version": nuevo.version}

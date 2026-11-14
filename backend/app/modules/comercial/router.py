"""6.11 Comercial automatizado: embudo de interesados y conversacion por WhatsApp."""

from datetime import date, datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field
from sqlalchemy import func, or_, select

from app.api.deps import DbSession, requiere
from app.core.enums import Rol
from app.core.errores import NoEncontrado
from app.modules.auth.models import Usuario
from app.modules.comercial import conversacion, service
from app.modules.comercial.models import ArbolConversacion, ConversacionComercial, Interesado
from app.modules.comunicaciones import service as comunicaciones
from app.modules.comunicaciones.schemas import MensajeRead
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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def siguiente_etapa(self) -> Literal["contactado", "cotizado", "en_afiliacion"] | None:
        """La etapa a la que el equipo lo pasa ahora: el panel no copia el orden del embudo."""
        return service.SIGUIENTE.get(self.etapa)  # type: ignore[return-value]


class RecuentosEmbudo(BaseModel):
    """Cuantos interesados hay en cada etapa, y abiertos en total."""

    nuevo: int
    contactado: int
    cotizado: int
    en_afiliacion: int
    afiliado: int
    perdido: int
    abiertos: int


class PerdidaIn(BaseModel):
    motivo: str = Field(min_length=3, max_length=255)


EstadoConversacion = Literal["automatica", "con_asesor"]


class ConversacionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    telefono: str
    interesado_id: UUID | None
    nodo: str
    datos: dict[str, Any]
    estado: EstadoConversacion
    asesor_id: UUID | None
    tarea_id: UUID | None
    updated_at: datetime
    interesado_nombre: str | None = Field(
        default=None, description="El nombre del interesado, si lo tiene: la bandeja lo nombra"
    )


class ConversacionDelInteresado(BaseModel):
    conversacion: ConversacionRead | None
    mensajes: list[MensajeRead]


class MensajeAsesorIn(BaseModel):
    texto: str = Field(min_length=1, max_length=4000)


class ArbolIn(BaseModel):
    nodos: dict[str, Any]
    nota: str | None = None


ORDEN = {
    "created_at": Interesado.created_at,
    "ultimo_contacto": Interesado.ultimo_contacto,
    # El enum se declara en el orden del embudo.
    "etapa": Interesado.etapa,
}


# --- F3-COM-01 Embudo -------------------------------------------------------------------------


@router.get("/interesados", response_model=Page[InteresadoRead], dependencies=[EQUIPO_COMERCIAL])
async def listar(
    db: DbSession,
    params: ParamsListado,
    etapa: str | None = None,
    origen: str | None = None,
    responsable_id: UUID | None = None,
    q: str | None = None,
    abiertos: bool = False,
) -> Page[InteresadoRead]:
    """Con `abiertos`, los que siguen en el embudo; con `orden=etapa`, en el orden del embudo."""
    stmt = select(Interesado)
    if etapa:
        stmt = stmt.where(Interesado.etapa == etapa)
    if abiertos:
        stmt = stmt.where(Interesado.etapa.in_(service.ABIERTAS))
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


@router.get(
    "/interesados/recuentos", response_model=RecuentosEmbudo, dependencies=[EQUIPO_COMERCIAL]
)
async def recuentos(db: DbSession, q: str | None = None) -> dict[str, int]:
    return await db.run_sync(service.recuentos, q)


@router.get(
    "/interesados/{interesado_id}", response_model=InteresadoRead, dependencies=[EQUIPO_COMERCIAL]
)
async def obtener(db: DbSession, interesado_id: UUID) -> Interesado:
    return await db.run_sync(service.obtener, interesado_id)


@router.get(
    "/interesados/{interesado_id}/conversacion",
    response_model=ConversacionDelInteresado,
    dependencies=[EQUIPO_COMERCIAL],
)
async def conversacion_del_interesado(
    db: DbSession, interesado_id: UUID
) -> ConversacionDelInteresado:
    """La conversacion de WhatsApp del interesado y sus ultimos mensajes, para su ficha."""

    def leer(s: Any) -> ConversacionDelInteresado:
        conv, mensajes = service.conversacion_de(s, service.obtener(s, interesado_id))
        return ConversacionDelInteresado(
            conversacion=ConversacionRead.model_validate(conv) if conv else None,
            mensajes=[MensajeRead.model_validate(m) for m in mensajes],
        )

    return await db.run_sync(leer)


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
    db: DbSession, estado: EstadoConversacion | None = "con_asesor"
) -> list[ConversacionRead]:
    stmt = select(ConversacionComercial).order_by(ConversacionComercial.updated_at.desc())
    if estado:
        stmt = stmt.where(ConversacionComercial.estado == estado)
    convs = list(await db.scalars(stmt.limit(200)))
    # A quien se atiende, en lote: una consulta por pagina, no por fila.
    ids = {c.interesado_id for c in convs if c.interesado_id}
    nombres = (
        dict(
            (
                await db.execute(
                    select(Interesado.id, Interesado.nombre).where(Interesado.id.in_(ids))
                )
            )
            .tuples()
            .all()
        )
        if ids
        else {}
    )
    return [
        ConversacionRead.model_validate(c).model_copy(
            update={"interesado_nombre": nombres.get(c.interesado_id) if c.interesado_id else None}
        )
        for c in convs
    ]


@router.post("/conversaciones/{conversacion_id}/mensajes", status_code=status.HTTP_201_CREATED)
async def responder_como_asesor(
    db: DbSession, usuario: Comercial, conversacion_id: UUID, data: MensajeAsesorIn
) -> dict[str, str]:
    """El asesor contesta por el mismo canal (dentro de la ventana de 24 horas)."""

    conv = await db.get(ConversacionComercial, conversacion_id)
    if conv is None:
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
    # Primero se retira la anterior: el indice unico parcial no admite dos activas ni un instante.
    await db.flush()
    nuevo = ArbolConversacion(version=ultima + 1, nodos=data.nodos, activo=True, nota=data.nota)
    db.add(nuevo)
    await db.flush()
    return {"version": nuevo.version}

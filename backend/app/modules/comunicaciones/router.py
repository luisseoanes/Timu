"""6.18 / 6.19 Plantillas, envios, traza de mensajes y bajas."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from app.core.deps import INTERNOS, DbSession, requiere
from app.core.enums import Rol
from app.modules.comunicaciones import service
from app.modules.comunicaciones.models import BajaComunicaciones, Mensaje, PlantillaWhatsApp
from app.modules.comunicaciones.schemas import (
    BajaCreate,
    BajaRead,
    EnvioPlantilla,
    EnvioTexto,
    MensajeRead,
    PlantillaCreate,
    PlantillaEstado,
    PlantillaRead,
)
from app.schemas.common import Page, ParamsListado, paginar

router = APIRouter(prefix="/comunicaciones", tags=["comunicaciones"])

GESTION = Depends(requiere(Rol.ADMIN, Rol.COMERCIAL))
EQUIPO = Depends(requiere(*INTERNOS))


@router.get("/plantillas", response_model=list[PlantillaRead], dependencies=[EQUIPO])
async def listar_plantillas(db: DbSession, nombre: str | None = None) -> list[PlantillaWhatsApp]:
    stmt = select(PlantillaWhatsApp).order_by(
        PlantillaWhatsApp.nombre, PlantillaWhatsApp.version.desc()
    )
    if nombre:
        stmt = stmt.where(PlantillaWhatsApp.nombre == nombre)
    return list(await db.scalars(stmt))


@router.post(
    "/plantillas",
    response_model=PlantillaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GESTION],
)
async def crear_plantilla(db: DbSession, data: PlantillaCreate) -> PlantillaWhatsApp:
    """Crea una version nueva en borrador. El texto de una version no se edita: Meta la aprobo
    tal cual, asi que un cambio es otra version que vuelve a revision."""
    return await db.run_sync(service.crear_version_plantilla, data.model_dump())


@router.patch(
    "/plantillas/{plantilla_id}/estado", response_model=PlantillaRead, dependencies=[GESTION]
)
async def cambiar_estado_plantilla(
    db: DbSession, plantilla_id: UUID, data: PlantillaEstado
) -> PlantillaWhatsApp:
    return await db.run_sync(
        service.cambiar_estado_plantilla, plantilla_id, data.estado_aprobacion, data.activa
    )


@router.get("/mensajes", response_model=Page[MensajeRead], dependencies=[EQUIPO])
async def listar_mensajes(
    db: DbSession,
    params: ParamsListado,
    familia_id: UUID | None = None,
    estado: str | None = None,
    canal: str | None = None,
    campana_id: UUID | None = None,
) -> Page[MensajeRead]:
    stmt = select(Mensaje)
    if familia_id:
        stmt = stmt.where(Mensaje.familia_id == familia_id)
    if estado:
        stmt = stmt.where(Mensaje.estado == estado)
    if canal:
        stmt = stmt.where(Mensaje.canal == canal)
    if campana_id:
        stmt = stmt.where(Mensaje.campana_id == campana_id)
    return await paginar(
        db,
        stmt,
        params,
        MensajeRead,
        campos_orden={"created_at": Mensaje.created_at, "estado": Mensaje.estado},
        orden_por_defecto="-created_at",
        desempate=Mensaje.id,
    )


@router.post(
    "/mensajes/plantilla",
    response_model=MensajeRead,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[EQUIPO],
)
async def enviar_plantilla(db: DbSession, data: EnvioPlantilla) -> Mensaje:
    return await db.run_sync(
        service.encolar_plantilla,
        telefono=data.telefono,
        plantilla=data.plantilla,
        variables=data.variables,
        familia_id=data.familia_id,
    )


@router.post(
    "/mensajes/texto",
    response_model=MensajeRead,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[EQUIPO],
)
async def enviar_texto(db: DbSession, data: EnvioTexto) -> Mensaje:
    """Texto libre: solo dentro de las 24 horas desde el ultimo mensaje de la persona."""
    return await db.run_sync(
        service.encolar_texto, telefono=data.telefono, texto=data.texto, familia_id=data.familia_id
    )


@router.get("/bajas", response_model=list[BajaRead], dependencies=[EQUIPO])
async def listar_bajas(db: DbSession) -> list[BajaComunicaciones]:
    return list(
        await db.scalars(select(BajaComunicaciones).order_by(BajaComunicaciones.created_at.desc()))
    )


@router.post(
    "/bajas", response_model=BajaRead, status_code=status.HTTP_201_CREATED, dependencies=[EQUIPO]
)
async def registrar_baja(db: DbSession, data: BajaCreate) -> BajaComunicaciones:
    destino = data.telefono or str(data.email)
    canal = "whatsapp" if data.telefono else "email"
    return await db.run_sync(service.registrar_baja, destino, canal=canal, motivo=data.motivo)


@router.delete(
    "/bajas/{destino}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(requiere(Rol.ADMIN))],
)
async def quitar_baja(db: DbSession, destino: Annotated[str, "Telefono E.164 o email"]) -> None:
    """Solo administracion: reactivar envios masivos exige que la persona lo haya pedido."""
    await db.run_sync(service.quitar_baja, destino)

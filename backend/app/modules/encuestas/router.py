"""6.20 / 6.21 Encuestas de satisfaccion y seguimiento post atencion."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.core.deps import INTERNOS, DbSession, publico, requiere
from app.core.enums import Rol
from app.modules.encuestas import service
from app.modules.encuestas.models import ConfiguracionEncuesta, Encuesta
from app.schemas.common import Page, ParamsListado, paginar

router = APIRouter(prefix="/encuestas", tags=["encuestas"])

EQUIPO = Depends(requiere(*INTERNOS))
ADMIN = Depends(requiere(Rol.ADMIN))


class EncuestaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    servicio_id: UUID
    familia_id: UUID
    responsable_id: UUID | None
    tipo: str
    estado: str
    programada_para: datetime
    enviada_en: datetime | None
    respondida_en: datetime | None
    canal_respuesta: str | None
    puntaje: int | None
    comentario: str | None
    tarea_id: UUID | None


class ConfiguracionIn(BaseModel):
    tipo_servicio_codigo: str | None = None
    encuesta_activa: bool = True
    demora_horas: int = Field(default=2, ge=0, le=24 * 14)
    plantilla_encuesta: str = "encuesta_satisfaccion"
    seguimiento_dias: int | None = Field(default=None, ge=1, le=180)
    plantilla_seguimiento: str = "seguimiento_post"
    umbral_alerta: int = Field(default=3, ge=1, le=5)
    comentario: str | None = None


class ConfiguracionRead(ConfiguracionIn):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class RespuestaIn(BaseModel):
    puntaje: int = Field(ge=1, le=5)
    comentario: str | None = Field(default=None, max_length=2000)


ORDEN = {"programada_para": Encuesta.programada_para, "respondida_en": Encuesta.respondida_en}


@router.get("", response_model=Page[EncuestaRead], dependencies=[EQUIPO])
async def listar(
    db: DbSession,
    params: ParamsListado,
    estado: str | None = None,
    tipo: str | None = None,
    responsable_id: UUID | None = None,
    puntaje_max: int | None = None,
) -> Page[EncuestaRead]:
    stmt = select(Encuesta)
    if estado:
        stmt = stmt.where(Encuesta.estado == estado)
    if tipo:
        stmt = stmt.where(Encuesta.tipo == tipo)
    if responsable_id:
        stmt = stmt.where(Encuesta.responsable_id == responsable_id)
    if puntaje_max is not None:
        stmt = stmt.where(Encuesta.puntaje <= puntaje_max)
    return await paginar(
        db,
        stmt,
        params,
        EncuestaRead,
        campos_orden=ORDEN,
        orden_por_defecto="-programada_para",
        desempate=Encuesta.id,
    )


@router.get("/resumen", dependencies=[EQUIPO])
async def resumen(db: DbSession, desde: date, hasta: date) -> dict[str, Any]:
    return await db.run_sync(service.resumen, desde, hasta)


@router.get("/configuracion", response_model=list[ConfiguracionRead], dependencies=[ADMIN])
async def configuraciones(db: DbSession) -> list[ConfiguracionEncuesta]:
    return list(await db.scalars(select(ConfiguracionEncuesta)))


@router.put("/configuracion", response_model=ConfiguracionRead, dependencies=[ADMIN])
async def guardar_configuracion(db: DbSession, data: ConfiguracionIn) -> ConfiguracionEncuesta:
    """Una por tipo de atencion (o la general, sin tipo). Si existe, se reemplaza."""
    conf = await db.scalar(
        select(ConfiguracionEncuesta).where(
            ConfiguracionEncuesta.tipo_servicio_codigo.is_(None)
            if data.tipo_servicio_codigo is None
            else ConfiguracionEncuesta.tipo_servicio_codigo == data.tipo_servicio_codigo
        )
    )
    if conf is None:
        conf = ConfiguracionEncuesta()
        db.add(conf)
    for campo, valor in data.model_dump().items():
        setattr(conf, campo, valor)
    await db.flush()
    return conf


# --- Respuesta por enlace (publica: la autoriza el token) -------------------------------------


@router.get("/respuesta/{token}", dependencies=[Depends(publico)])
async def contexto(db: DbSession, token: str) -> dict[str, Any]:
    """Publico a proposito: el token del enlace es el secreto. Solo devuelve que se
    pregunta y sobre que atencion."""
    return await db.run_sync(service.contexto, token)


@router.post("/respuesta/{token}", dependencies=[Depends(publico)])
async def responder(db: DbSession, token: str, data: RespuestaIn) -> dict[str, str]:
    encuesta = await db.run_sync(service.por_token, token)
    await db.run_sync(service.responder, encuesta, data.puntaje, data.comentario, "enlace")
    return {"detail": "Gracias por tu respuesta"}

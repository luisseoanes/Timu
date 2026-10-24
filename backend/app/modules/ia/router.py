"""F4-IAA Administracion de la capa de IA: prompts versionados, casos de prueba,
evaluacion, activacion, registro de consultas y consumo del presupuesto."""

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.core.deps import DbSession, requiere
from app.core.enums import Rol
from app.core.eventos import EventoDominio
from app.core.outbox import publicar
from app.modules.auth.models import Usuario
from app.modules.ia import service
from app.modules.ia.models import CasoPruebaIA, ConsultaIA, PromptIA

router = APIRouter(prefix="/ia", tags=["ia"])

ADMIN = Depends(requiere(Rol.ADMIN))
Admin = Annotated[Usuario, Depends(requiere(Rol.ADMIN))]

Codigo = Literal["comercial_guion", "veterinario_borrador"]


class PromptIn(BaseModel):
    codigo: Codigo
    sistema: str = Field(min_length=50, max_length=20000)
    nota: str | None = None


class PromptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    codigo: str
    version: int
    sistema: str
    estado: str
    nota: str | None
    evaluado_en: datetime | None
    evaluacion: dict[str, Any]


class CasoIn(BaseModel):
    prompt_codigo: Codigo
    nombre: str = Field(min_length=3, max_length=160)
    entrada: str = Field(min_length=3)
    esperado: dict[str, Any]


class CasoRead(CasoIn):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class ConsultaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    prompt_codigo: str
    prompt_version: int | None
    modelo: str | None
    estado: str
    contexto: str | None
    tokens_entrada: int
    tokens_salida: int
    tokens_cache_lectura: int
    costo_usd: float
    latencia_ms: int | None
    error: str | None


@router.get("/prompts", response_model=list[PromptRead], dependencies=[ADMIN])
async def prompts(db: DbSession, codigo: str | None = None) -> list[PromptIA]:
    stmt = select(PromptIA).order_by(PromptIA.codigo, PromptIA.version.desc())
    if codigo:
        stmt = stmt.where(PromptIA.codigo == codigo)
    return list(await db.scalars(stmt))


@router.post(
    "/prompts",
    response_model=PromptRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[ADMIN],
)
async def nueva_version(db: DbSession, data: PromptIn) -> PromptIA:
    """Nace en borrador: entra en operacion solo despues de pasar su evaluacion."""
    return await db.run_sync(service.crear_version, data.codigo, data.sistema, data.nota)


@router.post(
    "/prompts/{prompt_id}/evaluacion",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[ADMIN],
)
async def evaluar(db: DbSession, prompt_id: UUID) -> dict[str, str]:
    """F4-IAA-04 Corre los casos de prueba en el worker (cada caso es una consulta real)."""
    prompt = await db.run_sync(service.obtener_prompt, prompt_id)
    publicar(db, EventoDominio("ia.evaluacion_solicitada", {"prompt_id": str(prompt.id)}))
    return {"detail": "Evaluacion en curso; consulte el prompt para ver el resultado"}


@router.post("/prompts/{prompt_id}/activacion", response_model=PromptRead)
async def activar(db: DbSession, usuario: Admin, prompt_id: UUID) -> PromptIA:
    prompt = await db.run_sync(service.obtener_prompt, prompt_id)
    return await db.run_sync(service.activar, prompt, usuario.id)


@router.post("/prompts/sembrar", dependencies=[ADMIN])
async def sembrar(db: DbSession) -> dict[str, int]:
    return {"creados": await db.run_sync(service.sembrar)}


@router.get("/casos", response_model=list[CasoRead], dependencies=[ADMIN])
async def casos(db: DbSession, prompt_codigo: str | None = None) -> list[CasoPruebaIA]:
    stmt = select(CasoPruebaIA).order_by(CasoPruebaIA.prompt_codigo, CasoPruebaIA.nombre)
    if prompt_codigo:
        stmt = stmt.where(CasoPruebaIA.prompt_codigo == prompt_codigo)
    return list(await db.scalars(stmt))


@router.post(
    "/casos",
    response_model=CasoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[ADMIN],
)
async def crear_caso(db: DbSession, data: CasoIn) -> CasoPruebaIA:
    caso = CasoPruebaIA(**data.model_dump())
    db.add(caso)
    await db.flush()
    return caso


@router.get("/consultas", response_model=list[ConsultaRead], dependencies=[ADMIN])
async def consultas(
    db: DbSession, estado: str | None = None, prompt_codigo: str | None = None
) -> list[ConsultaIA]:
    stmt = select(ConsultaIA).order_by(ConsultaIA.created_at.desc()).limit(200)
    if estado:
        stmt = stmt.where(ConsultaIA.estado == estado)
    if prompt_codigo:
        stmt = stmt.where(ConsultaIA.prompt_codigo == prompt_codigo)
    return list(await db.scalars(stmt))


@router.get("/consumo", dependencies=[ADMIN])
async def consumo(db: DbSession) -> dict[str, Any]:
    """Gasto del mes contra el presupuesto, por prompt y resultado."""
    return await db.run_sync(service.consumo)

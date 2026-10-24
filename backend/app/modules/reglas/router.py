"""F0-12 Administracion de reglas: una regla nueva opera en cuanto se guarda."""

from datetime import date
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select

from app.core.deps import INTERNOS, DbSession, requiere
from app.core.enums import Rol
from app.core.errores import Conflicto, NoEncontrado, ReglaNegocio
from app.modules.reglas import motor, service
from app.modules.reglas.models import Regla

router = APIRouter(prefix="/reglas", tags=["reglas"])

ADMIN = Depends(requiere(Rol.ADMIN))
EQUIPO = Depends(requiere(*INTERNOS))


class _Validada(BaseModel):
    @model_validator(mode="after")
    def _validar(self) -> "_Validada":
        evento = getattr(self, "evento", None)
        condicion = getattr(self, "condicion", None)
        accion = getattr(self, "accion", None)
        try:
            if condicion is not None:
                motor.validar_condicion(condicion)
            if evento is not None and accion is not None:
                motor.validar_accion(evento, accion)
        except motor.CondicionInvalida as e:
            raise ValueError(str(e)) from e
        return self


class ReglaCreate(_Validada):
    codigo: str = Field(pattern=r"^[a-z0-9_]{2,60}$")
    nombre: str = Field(min_length=2, max_length=160)
    descripcion: str | None = None
    evento: str
    condicion: dict[str, Any] = Field(default_factory=dict)
    accion: dict[str, Any]
    prioridad: int = Field(default=100, ge=0, le=10_000)
    detener: bool = False
    plan_id: UUID | None = None
    vigente_desde: date | None = None
    vigente_hasta: date | None = None
    activa: bool = True


class ReglaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=160)
    descripcion: str | None = None
    condicion: dict[str, Any] | None = None
    accion: dict[str, Any] | None = None
    prioridad: int | None = Field(default=None, ge=0, le=10_000)
    detener: bool | None = None
    vigente_desde: date | None = None
    vigente_hasta: date | None = None
    activa: bool | None = None


class ReglaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    codigo: str
    nombre: str
    descripcion: str | None
    evento: str
    condicion: dict[str, Any]
    accion: dict[str, Any]
    prioridad: int
    detener: bool
    plan_id: UUID | None
    vigente_desde: date | None
    vigente_hasta: date | None
    activa: bool


class Prueba(BaseModel):
    evento: str
    contexto: dict[str, Any]
    plan_id: UUID | None = None


@router.get("/eventos", dependencies=[EQUIPO])
async def eventos() -> dict[str, str]:
    """Puntos del sistema donde se evaluan reglas y para que sirve cada uno."""
    return {evento: descripcion for evento, (descripcion, _) in motor.EVENTOS.items()}


@router.get("", response_model=list[ReglaRead], dependencies=[EQUIPO])
async def listar(db: DbSession, evento: str | None = None) -> list[Regla]:
    stmt = select(Regla).order_by(Regla.evento, Regla.prioridad, Regla.codigo)
    if evento:
        stmt = stmt.where(Regla.evento == evento)
    return list(await db.scalars(stmt))


@router.post(
    "", response_model=ReglaRead, status_code=status.HTTP_201_CREATED, dependencies=[ADMIN]
)
async def crear(db: DbSession, data: ReglaCreate) -> Regla:
    if await db.scalar(select(Regla.id).where(Regla.codigo == data.codigo)):
        raise Conflicto(f"Ya existe una regla con codigo {data.codigo}")
    datos = data.model_dump()
    datos["accion"] = motor.validar_accion(data.evento, data.accion)
    regla = Regla(**datos)
    db.add(regla)
    await db.flush()
    return regla


@router.patch("/{regla_id}", response_model=ReglaRead, dependencies=[ADMIN])
async def actualizar(db: DbSession, regla_id: UUID, data: ReglaUpdate) -> Regla:
    regla = await db.get(Regla, regla_id)
    if regla is None:
        raise NoEncontrado("Regla no encontrada")
    cambios = data.model_dump(exclude_unset=True)
    try:
        if "condicion" in cambios:
            motor.validar_condicion(cambios["condicion"])
        if "accion" in cambios:
            cambios["accion"] = motor.validar_accion(regla.evento, cambios["accion"])
    except motor.CondicionInvalida as e:
        raise ReglaNegocio(str(e)) from e
    for campo, valor in cambios.items():
        setattr(regla, campo, valor)
    await db.flush()
    return regla


@router.post("/probar", dependencies=[EQUIPO])
async def probar(db: DbSession, data: Prueba) -> list[dict[str, Any]]:
    """Evalua sin ejecutar nada: muestra que reglas aplicarian a un contexto."""
    if data.evento not in motor.EVENTOS:
        raise ReglaNegocio(f"Evento desconocido: {data.evento}")
    resultados = await db.run_sync(
        service.evaluar, data.evento, data.contexto, plan_id=data.plan_id
    )
    return [{"regla": r.regla, "nombre": r.nombre, "accion": r.accion} for r in resultados]

"""6.3 Planes grupales: administracion y recomendacion. El cambio de plan de un contrato
esta en cartera/router.py (vive en el contrato), con la misma ruta bajo /planes."""

from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select

from app.api.deps import INTERNOS, DbSession, requiere
from app.core.enums import Periodicidad, Rol
from app.core.errores import NoEncontrado
from app.modules.auth.models import Usuario
from app.modules.catalogos import service as catalogos
from app.modules.catalogos.models import TipoServicioCatalogo
from app.modules.planes import service
from app.modules.planes.models import CiudadPlan, Plan, TarifaPlan
from app.modules.planes.schemas import (
    CotizacionRead,
    TarifaPeriodicidadRead,
    TarifaRead,
    cotizacion_read,
)

router = APIRouter(prefix="/planes", tags=["planes"])

EQUIPO = Depends(requiere(*INTERNOS))
ADMIN = Depends(requiere(Rol.ADMIN))
Gestion = Annotated[Usuario, Depends(requiere(Rol.ADMIN, Rol.COMERCIAL))]


class BeneficioIn(BaseModel):
    tipo_servicio_codigo: str
    cupo: int | None = Field(default=None, ge=0, description="Vacio = ilimitado")
    periodo_cupo: Literal["mensual", "anual"] = "anual"
    cobertura_pct: int = Field(default=100, ge=0, le=100)
    copago: Decimal = Field(default=Decimal(0), ge=0)


class BeneficioRead(BeneficioIn):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


Valor = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]


class TarifasIn(BaseModel):
    """6.2 / 6.3 Valor mensual por peludo con 1, 2, 3 y 4 o mas peludos, y el precio total de
    cada periodo largo para un solo peludo (vacio = sin descuento por ese periodo)."""

    por_peludos: list[Valor] = Field(min_length=4, max_length=4)
    trimestral: Valor | None = None
    semestral: Valor | None = None
    anual: Valor | None = None

    def periodicidad(self) -> dict[str, Decimal | None]:
        return {
            Periodicidad.TRIMESTRAL: self.trimestral,
            Periodicidad.SEMESTRAL: self.semestral,
            Periodicidad.ANUAL: self.anual,
        }


class PlanCreate(BaseModel):
    codigo: str = Field(pattern=r"^[a-z0-9_]{2,40}$")
    nombre: str = Field(min_length=2, max_length=120)
    descripcion: str | None = None
    ciudades: list[str] = Field(min_length=1, description="Donde se vende")
    tarifas: TarifasIn
    especies: list[str] = Field(default_factory=list, description="Vacio = todas")
    beneficios: list[BeneficioIn] = Field(default_factory=list)


class PlanUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    descripcion: str | None = None
    activo: bool | None = None


class PlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    codigo: str
    nombre: str
    descripcion: str | None
    ciudades: list[str]
    tarifas: list[TarifaRead]
    tarifas_periodicidad: list[TarifaPeriodicidadRead]
    especies: list[str]
    activo: bool
    beneficios: list[BeneficioRead]

    @field_validator("ciudades", mode="before")
    @classmethod
    def _nombres(cls, v: Any) -> list[str]:
        return [c if isinstance(c, str) else c.ciudad for c in v]


class PeludoIn(BaseModel):
    especie: str = Field(max_length=40)
    plan_id: UUID


class CotizacionIn(BaseModel):
    ciudad: str
    peludos: list[PeludoIn] = Field(min_length=1)


class Recomendacion(BaseModel):
    plan: PlanRead
    motivo: str
    regla: str


async def _validar_beneficios(db: DbSession, beneficios: list[BeneficioIn]) -> None:
    codigos = {b.tipo_servicio_codigo for b in beneficios}
    existentes = set(
        await db.scalars(
            select(TipoServicioCatalogo.codigo).where(TipoServicioCatalogo.codigo.in_(codigos))
        )
    )
    if faltantes := codigos - existentes:
        raise NoEncontrado(f"Tipos de servicio inexistentes: {', '.join(sorted(faltantes))}")


@router.get("", response_model=list[PlanRead], dependencies=[EQUIPO])
async def listar(
    db: DbSession, incluir_inactivos: bool = False, ciudad: str | None = None
) -> list[Plan]:
    """Del mas economico al mas caro (tarifa de un peludo). Con `ciudad`, solo los que se
    venden alli."""
    precio = (
        select(TarifaPlan.valor)
        .where(TarifaPlan.plan_id == Plan.id, TarifaPlan.peludos == 1)
        .scalar_subquery()
    )
    stmt = select(Plan).order_by(precio.nulls_last(), Plan.codigo)
    if not incluir_inactivos:
        stmt = stmt.where(Plan.activo.is_(True))
    if ciudad:
        stmt = stmt.where(
            Plan.id.in_(
                select(CiudadPlan.plan_id).where(
                    CiudadPlan.ciudad == ciudad, CiudadPlan.activa.is_(True)
                )
            )
        )
    return list(await db.scalars(stmt))


@router.post("/cotizacion", response_model=list[CotizacionRead], dependencies=[EQUIPO])
async def cotizacion(db: DbSession, data: CotizacionIn) -> list[CotizacionRead]:
    """6.2 / 6.3 Precio de una afiliacion con cada periodicidad: cada peludo con su plan."""
    ciudad = await db.run_sync(catalogos.ciudad_valida, data.ciudad)
    peludos = [(p.especie, p.plan_id) for p in data.peludos]
    return [
        cotizacion_read(await db.run_sync(service.cotizar, ciudad, peludos, periodicidad))
        for periodicidad in Periodicidad
    ]


@router.get("/recomendacion", response_model=Recomendacion, dependencies=[EQUIPO])
async def recomendacion(
    db: DbSession,
    ciudad: str,
    especies: Annotated[list[str], Query(description="Una entrada por mascota")] = ["canino"],  # noqa: B006
) -> Recomendacion:
    """F1-PLA-04 Plan sugerido para la ciudad y las mascotas de la familia, y por que."""
    ciudad = await db.run_sync(catalogos.ciudad_valida, ciudad)
    plan, motivo, regla = await db.run_sync(service.recomendar, ciudad, especies)
    return Recomendacion(plan=PlanRead.model_validate(plan), motivo=motivo, regla=regla)


@router.get("/{plan_id}", response_model=PlanRead, dependencies=[EQUIPO])
async def obtener(db: DbSession, plan_id: UUID) -> Plan:
    plan = await db.run_sync(service.obtener, plan_id)
    return await db.run_sync(service.con_detalle, plan)


@router.post("", response_model=PlanRead, status_code=status.HTTP_201_CREATED, dependencies=[ADMIN])
async def crear(db: DbSession, data: PlanCreate) -> Plan:
    """F1-PLA-01 Plan con sus tarifas, sus ciudades y sus beneficios por tipo de servicio."""
    await _validar_beneficios(db, data.beneficios)
    ciudades = [await db.run_sync(catalogos.ciudad_valida, c) for c in data.ciudades]
    datos = data.model_dump(exclude={"tarifas", "ciudades"})
    datos |= {
        "tarifas": data.tarifas.por_peludos,
        "tarifas_periodicidad": data.tarifas.periodicidad(),
        "ciudades": ciudades,
    }
    return await db.run_sync(service.crear, datos)


@router.patch("/{plan_id}", response_model=PlanRead, dependencies=[ADMIN])
async def actualizar(db: DbSession, plan_id: UUID, data: PlanUpdate) -> Plan:
    """Nombre, descripcion y si se vende. Las tarifas y las ciudades tienen su ruta."""
    plan = await db.run_sync(service.obtener, plan_id)
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(plan, campo, valor)
    await db.flush()
    return await db.run_sync(service.con_detalle, plan)


@router.put("/{plan_id}/tarifas", response_model=PlanRead, dependencies=[ADMIN])
async def reemplazar_tarifas(db: DbSession, plan_id: UUID, data: TarifasIn) -> Plan:
    """Aplica a afiliaciones nuevas y a los recalculos (alta o retiro de un peludo, cambio
    de plan); las cuotas ya emitidas no cambian."""
    plan = await db.run_sync(service.obtener, plan_id)
    return await db.run_sync(
        service.reemplazar_tarifas, plan, data.por_peludos, data.periodicidad()
    )


@router.put("/{plan_id}/ciudades", response_model=PlanRead, dependencies=[ADMIN])
async def fijar_ciudades(
    db: DbSession, plan_id: UUID, ciudades: Annotated[list[str], Body(min_length=1)]
) -> Plan:
    validas = [await db.run_sync(catalogos.ciudad_valida, c) for c in ciudades]
    plan = await db.run_sync(service.obtener, plan_id)
    return await db.run_sync(service.fijar_ciudades, plan, validas)


@router.put("/{plan_id}/beneficios", response_model=PlanRead, dependencies=[ADMIN])
async def reemplazar_beneficios(
    db: DbSession, plan_id: UUID, beneficios: list[BeneficioIn]
) -> Plan:
    await _validar_beneficios(db, beneficios)
    plan = await db.run_sync(service.obtener, plan_id)
    return await db.run_sync(
        service.reemplazar_beneficios, plan, [b.model_dump() for b in beneficios]
    )

"""6.3 Planes grupales: administracion, cambios de plan y recomendacion."""

from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.core.deps import INTERNOS, DbSession, requiere
from app.core.enums import Rol
from app.core.errores import NoEncontrado
from app.modules.auth.models import Usuario
from app.modules.catalogos import service as catalogos
from app.modules.planes import service
from app.modules.planes.models import Plan

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


class PlanCreate(BaseModel):
    codigo: str = Field(pattern=r"^[a-z0-9_]{2,40}$")
    nombre: str = Field(min_length=2, max_length=120)
    descripcion: str | None = None
    ciudad: str | None = Field(default=None, description="Vacio = todas las ciudades")
    valor_mensual: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    cupos_mascotas: int = Field(default=1, ge=1, le=20)
    especies: list[str] = Field(default_factory=list, description="Vacio = todas")
    beneficios: list[BeneficioIn] = Field(default_factory=list)


class PlanUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    descripcion: str | None = None
    valor_mensual: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    cupos_mascotas: int | None = Field(default=None, ge=1, le=20)
    activo: bool | None = None


class PlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    codigo: str
    nombre: str
    descripcion: str | None
    ciudad: str | None
    valor_mensual: Decimal
    cupos_mascotas: int
    especies: list[str]
    activo: bool
    beneficios: list[BeneficioRead]


class CambioPlanIn(BaseModel):
    plan_id: UUID


class CambioPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    contrato_id: UUID
    tipo: str
    plan_anterior_id: UUID | None
    plan_nuevo_id: UUID | None
    valor_anterior: Decimal
    valor_nuevo: Decimal
    ajuste: Decimal
    modo: str | None
    regla_codigo: str | None
    fecha_efectiva: Any
    aplicado: bool


class Recomendacion(BaseModel):
    plan: PlanRead
    motivo: str
    regla: str


async def _validar_beneficios(db: DbSession, beneficios: list[BeneficioIn]) -> None:
    from app.modules.catalogos.models import TipoServicioCatalogo

    codigos = {b.tipo_servicio_codigo for b in beneficios}
    existentes = set(
        await db.scalars(
            select(TipoServicioCatalogo.codigo).where(TipoServicioCatalogo.codigo.in_(codigos))
        )
    )
    if faltantes := codigos - existentes:
        raise NoEncontrado(f"Tipos de servicio inexistentes: {', '.join(sorted(faltantes))}")


@router.get("", response_model=list[PlanRead], dependencies=[EQUIPO])
async def listar(db: DbSession, incluir_inactivos: bool = False) -> list[Plan]:
    stmt = select(Plan).order_by(Plan.valor_mensual)
    if not incluir_inactivos:
        stmt = stmt.where(Plan.activo.is_(True))
    return list(await db.scalars(stmt))


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
    return await db.run_sync(service.obtener, plan_id)


@router.post("", response_model=PlanRead, status_code=status.HTTP_201_CREATED, dependencies=[ADMIN])
async def crear(db: DbSession, data: PlanCreate) -> Plan:
    """F1-PLA-01 Plan con valor, cupos y beneficios por tipo de servicio."""
    await _validar_beneficios(db, data.beneficios)
    if data.ciudad:
        data.ciudad = await db.run_sync(catalogos.ciudad_valida, data.ciudad)
    return await db.run_sync(service.crear, data.model_dump())


@router.patch("/{plan_id}", response_model=PlanRead, dependencies=[ADMIN])
async def actualizar(db: DbSession, plan_id: UUID, data: PlanUpdate) -> Plan:
    """Un nuevo valor aplica a contratos nuevos y a cambios de plan; los contratos vigentes
    conservan su valor hasta la renovacion."""
    plan = await db.run_sync(service.obtener, plan_id)
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(plan, campo, valor)
    await db.flush()
    return plan


@router.put("/{plan_id}/beneficios", response_model=PlanRead, dependencies=[ADMIN])
async def reemplazar_beneficios(
    db: DbSession, plan_id: UUID, beneficios: list[BeneficioIn]
) -> Plan:
    await _validar_beneficios(db, beneficios)
    plan = await db.run_sync(service.obtener, plan_id)
    return await db.run_sync(
        service.reemplazar_beneficios, plan, [b.model_dump() for b in beneficios]
    )


@router.post("/contratos/{contrato_id}/cambio", response_model=CambioPlanRead)
async def cambiar_plan(
    db: DbSession, usuario: Gestion, contrato_id: UUID, data: CambioPlanIn
) -> Any:
    """F1-PLA-02 Cambio de plan con el cobro que defina la regla `plan.cambio`."""
    from app.modules.cartera import service as cartera

    contrato = await db.run_sync(cartera.obtener_contrato, contrato_id)
    plan = await db.run_sync(service.obtener, data.plan_id)
    return await db.run_sync(service.cambiar_plan, contrato, plan, usuario.id)

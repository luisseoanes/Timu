"""Dashboard gerencial (F4-DAS): indicadores, exportables y reportes programados."""

from datetime import date, datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select

from app.core.deps import DbSession, requiere
from app.core.enums import Rol
from app.core.errores import NoEncontrado, ReglaNegocio
from app.modules.dashboard import exportar, service
from app.modules.dashboard.models import ReporteProgramado

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

GERENCIA = Depends(requiere(Rol.ADMIN, Rol.COMERCIAL, Rol.OPERACIONES))
ADMIN = Depends(requiere(Rol.ADMIN))


class ReporteIn(BaseModel):
    nombre: str = Field(min_length=3, max_length=160)
    periodicidad: Literal["diaria", "semanal", "mensual"]
    destinatarios: list[EmailStr] = Field(min_length=1, max_length=20)
    indicadores: list[str] = []
    ciudad: str | None = None
    activo: bool = True


class ReporteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    periodicidad: str
    destinatarios: list[str]
    indicadores: list[str]
    ciudad: str | None
    activo: bool
    ultimo_envio: datetime | None
    ultimo_error: str | None


@router.get("/definiciones", dependencies=[GERENCIA])
async def definiciones() -> list[dict[str, str]]:
    """F4-DAS-01 Formula acordada de cada indicador."""
    return service.definiciones()


@router.get("/indicadores", dependencies=[GERENCIA], response_model=None)
async def indicadores(
    db: DbSession,
    desde: date,
    hasta: date,
    ciudad: str | None = None,
    codigos: Annotated[list[str] | None, Query()] = None,
    formato: Literal["json", "csv", "xlsx"] = "json",
) -> dict[str, Any] | Response:
    """F4-DAS-02 Indicadores del periodo (cacheados unos minutos); F4-DAS-03 en CSV o Excel."""
    resultado = await db.run_sync(service.calcular, desde, hasta, ciudad, codigos)
    if formato == "json":
        return resultado
    nombre = f"indicadores-{desde}-{hasta}"
    if formato == "csv":
        contenido, tipo, extension = exportar.a_csv(resultado), "text/csv; charset=utf-8", "csv"
    else:
        contenido, tipo, extension = exportar.a_xlsx(resultado), exportar.XLSX, "xlsx"
    return Response(
        contenido,
        media_type=tipo,
        headers={"Content-Disposition": f'attachment; filename="{nombre}.{extension}"'},
    )


@router.get("/reportes", response_model=list[ReporteRead], dependencies=[ADMIN])
async def reportes(db: DbSession) -> list[ReporteProgramado]:
    return list(await db.scalars(select(ReporteProgramado).order_by(ReporteProgramado.nombre)))


def _validar(data: ReporteIn) -> None:
    desconocidos = [c for c in data.indicadores if c not in service.INDICADORES]
    if desconocidos:
        raise ReglaNegocio(f"Indicadores desconocidos: {', '.join(desconocidos)}")


@router.post(
    "/reportes",
    response_model=ReporteRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[ADMIN],
)
async def crear_reporte(db: DbSession, data: ReporteIn) -> ReporteProgramado:
    _validar(data)
    reporte = ReporteProgramado(**data.model_dump(mode="json"))
    db.add(reporte)
    await db.flush()
    return reporte


@router.put("/reportes/{reporte_id}", response_model=ReporteRead, dependencies=[ADMIN])
async def editar_reporte(db: DbSession, reporte_id: UUID, data: ReporteIn) -> ReporteProgramado:
    _validar(data)
    reporte = await db.get(ReporteProgramado, reporte_id)
    if reporte is None:
        raise NoEncontrado("Reporte no encontrado")
    for campo, valor in data.model_dump(mode="json").items():
        setattr(reporte, campo, valor)
    await db.flush()
    return reporte

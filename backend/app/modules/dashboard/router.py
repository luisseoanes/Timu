"""Dashboard gerencial (F4-DAS): indicadores, exportables y reportes programados."""

from datetime import date, datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select

from app.api.deps import DbSession, requiere
from app.core.enums import Rol
from app.core.errores import NoEncontrado, Prohibido, ReglaNegocio
from app.modules.auth.models import Usuario
from app.modules.dashboard import exportar, service
from app.modules.dashboard.models import ReporteProgramado

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Perfiles de cada ruta (Seccion 12, docs/perfiles-y-permisos.md).
GERENCIA = Depends(requiere(Rol.GERENCIA))
# Las cifras: Gerencia todas; Comercial, Atencion y Operaciones las de su funcion.
ConCifras = Annotated[
    Usuario, Depends(requiere(Rol.GERENCIA, Rol.COMERCIAL, Rol.ATENCION_CLIENTE, Rol.OPERACIONES))
]


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


@router.get("/definiciones")
async def definiciones(_: ConCifras) -> list[dict[str, str]]:
    """Seccion 8 Formula acordada de cada indicador."""
    return service.definiciones()


@router.get("/indicadores", response_model=None)
async def indicadores(
    db: DbSession,
    usuario: ConCifras,
    desde: date,
    hasta: date,
    ciudad: str | None = None,
    codigos: Annotated[list[str] | None, Query()] = None,
    formato: Literal["json", "csv", "xlsx"] = "json",
) -> dict[str, Any] | Response:
    """Seccion 8 Indicadores del periodo (cacheados unos minutos); Seccion 8 en CSV o Excel."""
    if formato != "json" and usuario.rol != Rol.GERENCIA:
        raise Prohibido("Los exportables son de Gerencia")
    codigos = service.de_su_funcion(usuario.rol, codigos)
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


@router.get("/evolucion")
async def evolucion(
    db: DbSession,
    usuario: ConCifras,
    desde: date,
    hasta: date,
    ciudad: str | None = None,
    codigos: Annotated[list[str] | None, Query()] = None,
) -> dict[str, Any]:
    """Indicadores mes a mes durante 12 meses y en el periodo comparable (series del panel)."""
    codigos = service.de_su_funcion(usuario.rol, codigos)
    return await db.run_sync(service.evolucion, desde, hasta, ciudad, codigos)


@router.get("/reportes", response_model=list[ReporteRead], dependencies=[GERENCIA])
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
    dependencies=[GERENCIA],
)
async def crear_reporte(db: DbSession, data: ReporteIn) -> ReporteProgramado:
    _validar(data)
    reporte = ReporteProgramado(**data.model_dump(mode="json"))
    db.add(reporte)
    await db.flush()
    return reporte


@router.put("/reportes/{reporte_id}", response_model=ReporteRead, dependencies=[GERENCIA])
async def editar_reporte(db: DbSession, reporte_id: UUID, data: ReporteIn) -> ReporteProgramado:
    _validar(data)
    reporte = await db.get(ReporteProgramado, reporte_id)
    if reporte is None:
        raise NoEncontrado("Reporte no encontrado")
    for campo, valor in data.model_dump(mode="json").items():
        setattr(reporte, campo, valor)
    await db.flush()
    return reporte

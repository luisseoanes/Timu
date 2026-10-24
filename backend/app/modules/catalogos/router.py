"""F0-09 Catalogos maestros: lectura para los formularios y administracion por codigo."""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.core.deps import TODOS, DbSession, requiere
from app.core.enums import Rol
from app.core.errores import NoEncontrado
from app.modules.catalogos import service
from app.modules.catalogos.models import Ciudad, Especie, EsquemaPreventivo, TipoServicioCatalogo

router = APIRouter(prefix="/catalogos", tags=["catalogos"])

LECTURA = Depends(requiere(*TODOS))
ADMIN = Depends(requiere(Rol.ADMIN))


class CiudadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    codigo: str
    nombre: str
    departamento: str
    latitud: float | None
    longitud: float | None
    activa: bool


class EspecieRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    codigo: str
    nombre: str
    activa: bool


class TipoServicioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    codigo: str
    nombre: str
    modalidad: str
    duracion_min: int
    requiere_autorizacion: bool
    activo: bool


class EsquemaPreventivoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    codigo: str
    especie_codigo: str
    tipo: str
    nombre: str
    edad_minima_semanas: int
    dosis_iniciales: int
    intervalo_inicial_dias: int
    intervalo_refuerzo_dias: int | None
    requiere_autorizacion: bool
    activo: bool


class Activacion(BaseModel):
    activo: bool


@router.get("/ciudades", response_model=list[CiudadRead], dependencies=[LECTURA])
async def ciudades(db: DbSession, incluir_inactivas: bool = False) -> list[Ciudad]:
    stmt = select(Ciudad).order_by(Ciudad.nombre)
    if not incluir_inactivas:
        stmt = stmt.where(Ciudad.activa.is_(True))
    return list(await db.scalars(stmt))


@router.get("/especies", response_model=list[EspecieRead], dependencies=[LECTURA])
async def especies(db: DbSession) -> list[Especie]:
    return list(await db.scalars(select(Especie).order_by(Especie.nombre)))


@router.get("/tipos-servicio", response_model=list[TipoServicioRead], dependencies=[LECTURA])
async def tipos_servicio(db: DbSession, modalidad: str | None = None) -> list[TipoServicioCatalogo]:
    stmt = select(TipoServicioCatalogo).order_by(TipoServicioCatalogo.nombre)
    if modalidad:
        stmt = stmt.where(TipoServicioCatalogo.modalidad == modalidad)
    return list(await db.scalars(stmt))


@router.get(
    "/esquemas-preventivos", response_model=list[EsquemaPreventivoRead], dependencies=[LECTURA]
)
async def esquemas_preventivos(
    db: DbSession, especie: str | None = None
) -> list[EsquemaPreventivo]:
    stmt = select(EsquemaPreventivo).order_by(
        EsquemaPreventivo.especie_codigo, EsquemaPreventivo.codigo
    )
    if especie:
        stmt = stmt.where(EsquemaPreventivo.especie_codigo == especie)
    return list(await db.scalars(stmt))


_ACTIVABLES: dict[str, tuple[type[Any], str]] = {
    "ciudades": (Ciudad, "activa"),
    "especies": (Especie, "activa"),
    "tipos-servicio": (TipoServicioCatalogo, "activo"),
    "esquemas-preventivos": (EsquemaPreventivo, "activo"),
}


@router.patch("/{catalogo}/{codigo}/activo", dependencies=[ADMIN])
async def activar(db: DbSession, catalogo: str, codigo: str, data: Activacion) -> dict[str, Any]:
    """Los catalogos no se borran (hay registros que los referencian): se desactivan."""
    if catalogo not in _ACTIVABLES:
        raise NoEncontrado("Catalogo inexistente")
    modelo, campo = _ACTIVABLES[catalogo]
    obj = await db.scalar(select(modelo).where(modelo.codigo == codigo))
    if obj is None:
        raise NoEncontrado("Registro no encontrado")
    setattr(obj, campo, data.activo)
    return {"codigo": codigo, campo: data.activo}


@router.post("/cargar", dependencies=[ADMIN])
async def cargar(db: DbSession) -> dict[str, dict[str, int]]:
    """Carga o actualiza los datos iniciales. Repetible: no duplica."""
    return await db.run_sync(service.cargar)

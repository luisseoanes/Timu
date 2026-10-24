"""F0-09 Catalogos maestros: lectura para los formularios y administracion por codigo."""

from typing import Any, Literal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select

from app.core.deps import TODOS, DbSession, requiere
from app.core.enums import Rol
from app.core.errores import Conflicto, NoEncontrado
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


class PasoTipoRead(BaseModel):
    """Paso de la atencion (F1-SER-02): el panel arma con esto el formulario de cada paso."""

    codigo: str
    nombre: str
    obligatorio: bool = True
    campos: list[str] = []


class TipoServicioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    codigo: str
    nombre: str
    modalidad: str
    duracion_min: int
    requiere_autorizacion: bool
    activo: bool
    pasos: list[PasoTipoRead] = []


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


class EsquemaPreventivoIn(BaseModel):
    """F2-PRE-01 Esquema administrado como dato: un esquema nuevo aplica a las mascotas que
    se calendaricen despues, sin desplegar codigo."""

    codigo: str = Field(pattern=r"^[a-z0-9_]{3,40}$")
    especie_codigo: str
    tipo: Literal["vacuna", "desparasitacion_interna", "desparasitacion_externa"]
    nombre: str = Field(min_length=3, max_length=120)
    edad_minima_semanas: int = Field(default=0, ge=0, le=520)
    dosis_iniciales: int = Field(default=1, ge=1, le=10)
    intervalo_inicial_dias: int = Field(default=0, ge=0, le=365)
    intervalo_refuerzo_dias: int | None = Field(default=None, ge=1, le=1095)
    requiere_autorizacion: bool = True

    @model_validator(mode="after")
    def _serie_coherente(self) -> "EsquemaPreventivoIn":
        if self.dosis_iniciales > 1 and self.intervalo_inicial_dias == 0:
            raise ValueError("Una serie de varias dosis necesita intervalo entre dosis")
        return self


class EsquemaPreventivoUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=120)
    edad_minima_semanas: int | None = Field(default=None, ge=0, le=520)
    dosis_iniciales: int | None = Field(default=None, ge=1, le=10)
    intervalo_inicial_dias: int | None = Field(default=None, ge=0, le=365)
    intervalo_refuerzo_dias: int | None = Field(default=None, ge=1, le=1095)
    requiere_autorizacion: bool | None = None


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


@router.post(
    "/esquemas-preventivos",
    response_model=EsquemaPreventivoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[ADMIN],
)
async def crear_esquema(db: DbSession, data: EsquemaPreventivoIn) -> EsquemaPreventivo:
    if await db.scalar(select(EsquemaPreventivo.id).where(EsquemaPreventivo.codigo == data.codigo)):
        raise Conflicto(f"Ya existe el esquema {data.codigo}")
    if not await db.scalar(select(Especie.id).where(Especie.codigo == data.especie_codigo)):
        raise NoEncontrado(f"Especie {data.especie_codigo} inexistente")
    esquema = EsquemaPreventivo(**data.model_dump())
    db.add(esquema)
    await db.flush()
    return esquema


@router.patch(
    "/esquemas-preventivos/{codigo}", response_model=EsquemaPreventivoRead, dependencies=[ADMIN]
)
async def editar_esquema(
    db: DbSession, codigo: str, data: EsquemaPreventivoUpdate
) -> EsquemaPreventivo:
    """Los cambios aplican a los proximos calculos; lo ya programado no se reescribe."""
    esquema = await db.scalar(select(EsquemaPreventivo).where(EsquemaPreventivo.codigo == codigo))
    if esquema is None:
        raise NoEncontrado(f"Esquema {codigo} inexistente")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(esquema, campo, valor)
    await db.flush()
    return esquema


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

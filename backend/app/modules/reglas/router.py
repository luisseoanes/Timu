"""F0-12 Administracion de reglas: una regla nueva opera en cuanto se guarda."""

from datetime import date
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator
from sqlalchemy import String, cast, select

from app.api.deps import INTERNOS, DbSession, requiere
from app.core.enums import Rol
from app.core.errores import Conflicto, NoEncontrado, ReglaNegocio
from app.modules.comunicaciones import service as comunicaciones
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


class CampoCondicion(BaseModel):
    campo: str
    nombre: str
    numerico: bool


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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def condicion_texto(self) -> str:
        """Cuando aplica, en palabras: el panel no descifra el JSON del motor."""
        return motor.describir_condicion(self.condicion)

    # Lo que hace, en palabras. Lo llena `_leidas` con el nombre que da el equipo a cada
    # plantilla; sin ese contexto, el validador lo dice con el codigo de Meta.
    accion_texto: str = ""

    @model_validator(mode="after")
    def _accion_en_palabras(self) -> "ReglaRead":
        if not self.accion_texto:
            self.accion_texto = motor.describir_accion(self.accion)
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def evento_nombre(self) -> str:
        return motor.nombre_evento(self.evento)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def retirada(self) -> str | None:
        """Por que ya no se evalua, si su evento se retiro: no se puede editar."""
        return motor.EVENTOS_RETIRADOS.get(self.evento)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def campos_condicion(self) -> list[CampoCondicion]:
        """Lo que hay que contarle al motor para probar la regla, campo por campo."""
        return [CampoCondicion(**c) for c in motor.campos(self.condicion)]


class Prueba(BaseModel):
    evento: str
    contexto: dict[str, Any]
    plan_id: UUID | None = None


@router.get("/eventos", dependencies=[EQUIPO])
async def eventos() -> dict[str, str]:
    """Puntos del sistema donde se evaluan reglas y para que sirve cada uno."""
    return {evento: descripcion for evento, (descripcion, _) in motor.EVENTOS.items()}


async def _leidas(db: DbSession, reglas: list[Regla]) -> list[ReglaRead]:
    """Cada regla con su accion en palabras, nombrando las plantillas como el equipo."""
    titulos = await db.run_sync(comunicaciones.titulos_plantillas)
    return [
        ReglaRead.model_validate(r).model_copy(
            update={"accion_texto": motor.describir_accion(r.accion, titulos)}
        )
        for r in reglas
    ]


@router.get("", response_model=list[ReglaRead], dependencies=[EQUIPO])
async def listar(db: DbSession, evento: str | None = None) -> list[ReglaRead]:
    stmt = select(Regla).order_by(cast(Regla.evento, String), Regla.prioridad, Regla.codigo)
    if evento:
        stmt = stmt.where(Regla.evento == evento)
    return await _leidas(db, list(await db.scalars(stmt)))


@router.post(
    "", response_model=ReglaRead, status_code=status.HTTP_201_CREATED, dependencies=[ADMIN]
)
async def crear(db: DbSession, data: ReglaCreate) -> ReglaRead:
    if await db.scalar(select(Regla.id).where(Regla.codigo == data.codigo)):
        raise Conflicto(f"Ya existe una regla con codigo {data.codigo}")
    datos = data.model_dump()
    datos["accion"] = motor.validar_accion(data.evento, data.accion)
    regla = Regla(**datos)
    db.add(regla)
    await db.flush()
    return (await _leidas(db, [regla]))[0]


@router.patch("/{regla_id}", response_model=ReglaRead, dependencies=[ADMIN])
async def actualizar(db: DbSession, regla_id: UUID, data: ReglaUpdate) -> ReglaRead:
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
    return (await _leidas(db, [regla]))[0]


@router.post("/probar", dependencies=[EQUIPO])
async def probar(db: DbSession, data: Prueba) -> list[dict[str, Any]]:
    """Evalua sin ejecutar nada: muestra que reglas aplicarian a un contexto."""
    if data.evento not in motor.EVENTOS:
        raise ReglaNegocio(f"Evento desconocido: {data.evento}")
    resultados = await db.run_sync(
        service.evaluar, data.evento, data.contexto, plan_id=data.plan_id
    )
    titulos = await db.run_sync(comunicaciones.titulos_plantillas)
    return [
        {
            "regla": r.regla,
            "nombre": r.nombre,
            "accion": r.accion,
            "accion_texto": motor.describir_accion(r.accion, titulos),
        }
        for r in resultados
    ]

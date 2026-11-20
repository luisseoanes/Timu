"""Seccion 7 Administracion de reglas: una regla nueva opera en cuanto se guarda."""

from datetime import date
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator
from sqlalchemy import String, cast, select

from app.api.deps import DbSession, requiere
from app.core.enums import Rol
from app.core.errores import Conflicto, NoEncontrado, ReglaNegocio
from app.modules.reglas import acciones, motor, service
from app.modules.reglas.contextos import CONTEXTOS, OPERADORES, TipoCampo, campos_del_evento
from app.modules.reglas.models import Regla

router = APIRouter(prefix="/reglas", tags=["reglas"])

# Perfiles de cada ruta (Seccion 12, docs/perfiles-y-permisos.md).
ADMIN = Depends(requiere(Rol.ADMIN))


class _Validada(BaseModel):
    @model_validator(mode="after")
    def _validar(self) -> "_Validada":
        evento = getattr(self, "evento", None)
        condicion = getattr(self, "condicion", None)
        accion = getattr(self, "accion", None)
        try:
            if evento is not None and evento not in motor.EVENTOS:
                raise motor.CondicionInvalida(f"Evento desconocido: {evento}")
            if condicion is not None:
                motor.validar_condicion(condicion, evento)
            if evento is not None and accion is not None:
                motor.validar_accion(evento, accion)
        except motor.CondicionInvalida as e:
            raise ValueError(str(e)) from e
        return self


class ReglaCreate(_Validada):
    # Sin codigo, la API lo saca del nombre (`service.codigo_libre`).
    codigo: str | None = Field(default=None, pattern=r"^[a-z0-9_]{2,60}$")
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
    # Vacio: la regla vale para todos los planes.
    plan_id: UUID | None = None
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

    # Cuando aplica y lo que hace, en palabras: el panel no descifra el JSON del motor. Los
    # llena `_leidas` con el nombre de cada valor de catalogo y de cada plantilla; sin ese
    # contexto, el validador los dice con sus codigos.
    condicion_texto: str = ""
    accion_texto: str = ""

    @model_validator(mode="after")
    def _en_palabras(self) -> "ReglaRead":
        if not self.condicion_texto:
            self.condicion_texto = motor.describir_condicion(self.condicion, self.evento)
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


class OpcionRegla(BaseModel):
    valor: str
    nombre: str


class CampoEvento(BaseModel):
    campo: str
    nombre: str
    tipo: TipoCampo
    # Las comparaciones que admite, la primera es la que se propone.
    operadores: list[OpcionRegla]
    opciones: list[OpcionRegla] | None


class ParametroAccion(BaseModel):
    nombre: str
    etiqueta: str
    tipo: Literal["texto", "numero", "opcion"]
    requerido: bool
    por_defecto: str | int | None
    opciones: list[OpcionRegla] | None


class AccionEvento(BaseModel):
    tipo: str
    nombre: str
    parametros: list[ParametroAccion]


class PlanDeRegla(BaseModel):
    id: UUID
    nombre: str


class EventoDeReglas(BaseModel):
    """Lo que el editor necesita de un evento: cuando se revisa, que datos da a sus reglas y que
    pueden hacer."""

    evento: str
    nombre: str
    cuando: str
    admite_plan: bool
    campos: list[CampoEvento]
    acciones: list[AccionEvento]
    planes: list[PlanDeRegla]


class BorradorRegla(BaseModel):
    evento: str
    condicion: dict[str, Any] = Field(default_factory=dict)
    accion: dict[str, Any] | None = None


class EnPalabras(BaseModel):
    condicion_texto: str
    accion_texto: str | None


def _lista(valores: dict[str, str] | None) -> list[OpcionRegla] | None:
    return None if valores is None else [OpcionRegla(valor=v, nombre=n) for v, n in valores.items()]


class PlantillaFaltante(BaseModel):
    """Una plantilla que envia la plataforma y no esta aprobada y activa: esos mensajes no salen."""

    codigo: str
    titulo: str
    # Las reglas activas que la citan.
    reglas: list[str]
    # Lo que deja de enviarse sin ella, en minuscula («la bienvenida al afiliarse»).
    usos: list[str]
    # False: no esta en el catalogo y hay que registrarla; True: esta, pero sin version aprobada.
    registrada: bool


@router.get("/plantillas-faltantes", response_model=list[PlantillaFaltante], dependencies=[ADMIN])
async def plantillas_faltantes(db: DbSession) -> list[dict[str, Any]]:
    """El Inicio del administrador dice lo que falta configurar (docs/perfiles-y-permisos.md)."""
    return await db.run_sync(service.plantillas_faltantes)


@router.get("/eventos", response_model=list[EventoDeReglas], dependencies=[ADMIN])
async def eventos(db: DbSession) -> list[EventoDeReglas]:
    """Los puntos del sistema donde se evaluan reglas, con los datos que da cada uno y lo que
    puede hacer una regla en el (los eventos retirados no salen: no se crean ni se editan)."""
    opciones = await db.run_sync(service.opciones)
    planes = [PlanDeRegla(id=i, nombre=n) for i, _, n in await db.run_sync(service.planes)]
    salida = []
    for evento, (_, modelos) in acciones.ACCIONES_POR_EVENTO.items():
        campos = [
            CampoEvento(
                campo=c.campo,
                nombre=motor.nombre_campo(c.campo),
                tipo=c.tipo,
                operadores=_lista(OPERADORES[c.tipo]) or [],
                opciones=_lista(opciones[c.opciones.fuente]) if c.opciones else None,
            )
            for c in campos_del_evento(evento).values()
        ]
        de_accion = [
            AccionEvento(
                tipo=acciones.tipo_de_accion(m),
                nombre=acciones.NOMBRES_ACCIONES[acciones.tipo_de_accion(m)],
                parametros=[
                    ParametroAccion(
                        nombre=p.nombre,
                        etiqueta=p.etiqueta,
                        tipo=p.tipo,
                        requerido=p.requerido,
                        por_defecto=p.por_defecto,
                        opciones=_lista(opciones[p.fuente.fuente] if p.fuente else p.valores),
                    )
                    for p in acciones.parametros_de_accion(m)
                ],
            )
            for m in modelos
        ]
        salida.append(
            EventoDeReglas(
                evento=evento,
                nombre=motor.nombre_evento(evento),
                cuando=motor.CUANDO[evento],
                admite_plan=CONTEXTOS[evento].admite_plan,
                campos=campos,
                acciones=de_accion,
                planes=planes if CONTEXTOS[evento].admite_plan else [],
            )
        )
    return salida


@router.post("/describir", response_model=EnPalabras, dependencies=[ADMIN])
async def describir(db: DbSession, data: BorradorRegla) -> EnPalabras:
    """Una regla a medio escribir, en palabras y validada como al guardarla, sin guardar nada:
    el editor la dice mientras se escribe."""
    try:
        if data.evento not in motor.EVENTOS:
            raise motor.CondicionInvalida(f"Evento desconocido: {data.evento}")
        motor.validar_condicion(data.condicion, data.evento)
        accion = motor.validar_accion(data.evento, data.accion) if data.accion else None
    except motor.CondicionInvalida as e:
        raise ReglaNegocio(str(e)) from e
    nombres = await db.run_sync(service.nombres)
    titulos = await db.run_sync(service.titulos_plantillas)
    return EnPalabras(
        condicion_texto=motor.describir_condicion(data.condicion, data.evento, nombres),
        accion_texto=motor.describir_accion(accion, titulos, nombres) if accion else None,
    )


async def _leidas(db: DbSession, reglas: list[Regla]) -> list[ReglaRead]:
    """Cada regla en palabras, nombrando los valores de catalogo y las plantillas como el
    equipo."""
    titulos = await db.run_sync(service.titulos_plantillas)
    nombres = await db.run_sync(service.nombres)
    return [
        ReglaRead.model_validate(r).model_copy(
            update={
                "condicion_texto": motor.describir_condicion(r.condicion, r.evento, nombres),
                "accion_texto": motor.describir_accion(r.accion, titulos, nombres),
            }
        )
        for r in reglas
    ]


@router.get("", response_model=list[ReglaRead], dependencies=[ADMIN])
async def listar(db: DbSession, evento: str | None = None) -> list[ReglaRead]:
    stmt = select(Regla).order_by(cast(Regla.evento, String), Regla.prioridad, Regla.codigo)
    if evento:
        stmt = stmt.where(Regla.evento == evento)
    return await _leidas(db, list(await db.scalars(stmt)))


@router.post(
    "", response_model=ReglaRead, status_code=status.HTTP_201_CREATED, dependencies=[ADMIN]
)
async def crear(db: DbSession, data: ReglaCreate) -> ReglaRead:
    if data.codigo and await db.scalar(select(Regla.id).where(Regla.codigo == data.codigo)):
        raise Conflicto(f"Ya existe una regla con codigo {data.codigo}")
    datos = data.model_dump()
    datos["codigo"] = data.codigo or await db.run_sync(service.codigo_libre, data.nombre)
    datos["accion"] = motor.validar_accion(data.evento, data.accion)
    if datos["accion"]["tipo"] == "notificar":
        datos["accion"].setdefault("clave", datos["codigo"])
    await db.run_sync(
        service.comprobar_valores, data.evento, data.condicion, datos["accion"], data.plan_id
    )
    regla = Regla(**datos)
    db.add(regla)
    await db.flush()
    return (await _leidas(db, [regla]))[0]


@router.patch("/{regla_id}", response_model=ReglaRead, dependencies=[ADMIN])
async def actualizar(db: DbSession, regla_id: UUID, data: ReglaUpdate) -> ReglaRead:
    regla = await db.get(Regla, regla_id)
    if regla is None:
        raise NoEncontrado("Regla no encontrada")
    if regla.evento in motor.EVENTOS_RETIRADOS:
        raise ReglaNegocio("Una regla de un evento retirado no se edita")
    cambios = data.model_dump(exclude_unset=True)
    try:
        if "condicion" in cambios:
            motor.validar_condicion(cambios["condicion"], regla.evento)
        if "accion" in cambios:
            cambios["accion"] = motor.validar_accion(regla.evento, cambios["accion"])
    except motor.CondicionInvalida as e:
        raise ReglaNegocio(str(e)) from e
    nueva = cambios.get("accion")
    if nueva and nueva["tipo"] == "notificar" and "clave" not in nueva:
        # La clave dice que avisos ya se enviaron: cambiarla los repetiria.
        anterior = regla.accion.get("clave") if regla.accion.get("tipo") == "notificar" else None
        nueva["clave"] = anterior or regla.codigo
    await db.run_sync(
        service.comprobar_valores,
        regla.evento,
        cambios.get("condicion", {}),
        nueva,
        cambios.get("plan_id"),
    )
    for campo, valor in cambios.items():
        setattr(regla, campo, valor)
    await db.flush()
    return (await _leidas(db, [regla]))[0]


@router.post("/probar", dependencies=[ADMIN])
async def probar(db: DbSession, data: Prueba) -> list[dict[str, Any]]:
    """Evalua sin ejecutar nada: muestra que reglas aplicarian a un contexto."""
    if data.evento not in motor.EVENTOS:
        raise ReglaNegocio(f"Evento desconocido: {data.evento}")
    declarados = campos_del_evento(data.evento)
    sobran = [c for c in _rutas(data.contexto) if c not in declarados]
    if sobran:
        raise ReglaNegocio(f"{motor.nombre_evento(data.evento)} no da: {', '.join(sobran)}")
    resultados = await db.run_sync(
        service.evaluar_datos, data.evento, data.contexto, plan_id=data.plan_id
    )
    titulos = await db.run_sync(service.titulos_plantillas)
    return [
        {
            "regla": r.regla,
            "nombre": r.nombre,
            "accion": r.accion,
            "accion_texto": motor.describir_accion(r.accion, titulos),
        }
        for r in resultados
    ]


def _rutas(datos: dict[str, Any], prefijo: str = "") -> list[str]:
    """Las rutas con puntos de los datos de una prueba («familia.ciudad»)."""
    salida = []
    for clave, valor in datos.items():
        if isinstance(valor, dict):
            salida.extend(_rutas(valor, f"{prefijo}{clave}."))
        else:
            salida.append(f"{prefijo}{clave}")
    return salida

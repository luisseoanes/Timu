"""Seccion 7 Lo que da cada evento a sus reglas.

Cada evento evalua sus reglas con un contexto de tipo fijo (una dataclass por evento): el modulo
que evalua lo construye con sus campos y mypy rechaza uno que falte o sobre. Asi la lista de
campos que ofrece el editor de reglas y lo que el motor recibe de verdad no se pueden separar,
y una condicion sobre un dato que el evento no da se rechaza al guardarla en lugar de no
cumplirse nunca.
"""

import types
from dataclasses import asdict, dataclass, fields, is_dataclass
from typing import Annotated, Any, ClassVar, Literal, Union, get_args, get_origin, get_type_hints

TipoCampo = Literal["numero", "opcion", "lista", "si_no"]


@dataclass(frozen=True)
class Opciones:
    """De donde salen los valores posibles de un campo: un catalogo o un conjunto cerrado.
    Los resuelve `reglas.service.opciones` con la base."""

    fuente: str


CIUDADES = Opciones("ciudades")
ESPECIES = Opciones("especies")
PLANES = Opciones("planes")
TIPOS_SERVICIO = Opciones("tipos_servicio")
MODALIDADES = Opciones("modalidades")
ESTADOS_AFILIACION = Opciones("estados_afiliacion")
ESTADOS_SERVICIO = Opciones("estados_servicio")
PLANTILLAS = Opciones("plantillas")


# Las comparaciones que admite cada tipo de campo, con su nombre en el editor. El orden es el
# de la lista: la primera es la que se propone.
OPERADORES: dict[TipoCampo, dict[str, str]] = {
    "numero": {
        "gte": "al menos",
        "gt": "más de",
        "lte": "como mucho",
        "lt": "menos de",
        "eq": "igual a",
        "ne": "distinto de",
    },
    "opcion": {"eq": "es", "ne": "no es", "in": "es uno de", "nin": "no es ninguno de"},
    "lista": {"contiene": "incluye"},
    "si_no": {"eq": "es"},
}


# --- Partes comunes ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeLaFamilia:
    ciudad: Annotated[str, CIUDADES]
    estado: Annotated[str, ESTADOS_AFILIACION]


@dataclass(frozen=True)
class DelServicio:
    tipo: Annotated[str, TIPOS_SERVICIO]
    modalidad: Annotated[str, MODALIDADES]


@dataclass(frozen=True)
class DelPlan:
    codigo: Annotated[str, PLANES]


@dataclass(frozen=True)
class PlanDelCambio:
    codigo: Annotated[str, PLANES]
    valor: float


@dataclass(frozen=True)
class DeLaMascota:
    especie: Annotated[str | None, ESPECIES]


@dataclass(frozen=True)
class LosPeludos:
    total: int
    caninos: int
    felinos: int
    especies: Annotated[list[str], ESPECIES]


# --- Un contexto por evento -------------------------------------------------------------------


@dataclass(frozen=True)
class Contexto:
    evento: ClassVar[str]
    # Si el evento evalua tambien las reglas atadas a un plan (las del plan del contrato, de un
    # peludo o del plan nuevo); en los demas, una regla con plan no aplicaria nunca.
    admite_plan: ClassVar[bool] = False

    def datos(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CarteraEstado(Contexto):
    evento: ClassVar[str] = "cartera.estado"
    admite_plan: ClassVar[bool] = True
    dias_mora: int
    cuotas_vencidas: int
    saldo_pendiente: float
    estado_actual: Annotated[str, ESTADOS_AFILIACION]


@dataclass(frozen=True)
class CarteraAlerta(Contexto):
    evento: ClassVar[str] = "cartera.alerta"
    dias_mora: int


@dataclass(frozen=True)
class CarteraRenovacion(Contexto):
    evento: ClassVar[str] = "cartera.renovacion"
    admite_plan: ClassVar[bool] = True
    dias_para_renovacion: int
    estado: Annotated[str, ESTADOS_AFILIACION]


@dataclass(frozen=True)
class PlanCambio(Contexto):
    evento: ClassVar[str] = "plan.cambio"
    admite_plan: ClassVar[bool] = True
    familia: DeLaFamilia
    plan_anterior: PlanDelCambio
    plan_nuevo: PlanDelCambio
    sube: bool


@dataclass(frozen=True)
class PlanRecomendacion(Contexto):
    evento: ClassVar[str] = "plan.recomendacion"
    ciudad: Annotated[str, CIUDADES]
    mascotas: LosPeludos


@dataclass(frozen=True)
class ServicioTransicion(Contexto):
    evento: ClassVar[str] = "servicio.transicion"
    estado_anterior: Annotated[str, ESTADOS_SERVICIO]
    estado_nuevo: Annotated[str, ESTADOS_SERVICIO]
    servicio: DelServicio
    familia: DeLaFamilia


@dataclass(frozen=True)
class ServicioElegibilidad(Contexto):
    evento: ClassVar[str] = "servicio.elegibilidad"
    admite_plan: ClassVar[bool] = True
    familia: DeLaFamilia
    plan: DelPlan
    servicio: DelServicio
    mascota: DeLaMascota


CONTEXTOS: dict[str, type[Contexto]] = {
    c.evento: c
    for c in (
        CarteraEstado,
        CarteraAlerta,
        CarteraRenovacion,
        PlanCambio,
        PlanRecomendacion,
        ServicioTransicion,
        ServicioElegibilidad,
    )
}


# --- Los campos de cada evento, como los lee el editor ----------------------------------------


@dataclass(frozen=True)
class CampoDeclarado:
    campo: str
    tipo: TipoCampo
    opciones: Opciones | None


def _sin_none(tipo: Any) -> Any:
    if get_origin(tipo) in (Union, types.UnionType):
        resto = [a for a in get_args(tipo) if a is not type(None)]
        return resto[0]
    return tipo


def _declarados(clase: type, prefijo: str) -> list[CampoDeclarado]:
    pistas = get_type_hints(clase, include_extras=True)
    salida: list[CampoDeclarado] = []
    for f in fields(clase):
        pista = pistas[f.name]
        opciones = None
        if get_origin(pista) is Annotated:
            pista, *extras = get_args(pista)
            opciones = next((e for e in extras if isinstance(e, Opciones)), None)
        pista = _sin_none(pista)
        ruta = f"{prefijo}{f.name}"
        if is_dataclass(pista):
            salida.extend(_declarados(pista, f"{ruta}."))  # type: ignore[arg-type]
            continue
        tipo: TipoCampo
        if pista is bool:
            tipo = "si_no"
        elif pista in (int, float):
            tipo = "numero"
        elif get_origin(pista) is list:
            tipo = "lista"
        else:
            tipo = "opcion"
        salida.append(CampoDeclarado(ruta, tipo, opciones))
    return salida


def campos_del_evento(evento: str) -> dict[str, CampoDeclarado]:
    """Los campos que da el evento, por su ruta con puntos («familia.ciudad»), en el orden en
    que los declara su contexto."""
    return {c.campo: c for c in _declarados(CONTEXTOS[evento], "")}

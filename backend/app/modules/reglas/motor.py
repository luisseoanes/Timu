"""F0-12 Motor de reglas.

Condiciones (JSON), sin codigo ejecutable:

    {"todas": [c1, c2]}      {"alguna": [c1, c2]}      {"no": c}      {}  (siempre)
    {"campo": "familia.ciudad", "op": "eq", "valor": "Cali"}

Operadores: eq, ne, gt, gte, lt, lte, in, nin, contiene, existe.
`campo` es una ruta con puntos dentro del contexto que entrega el modulo que evalua.

Acciones: cada evento declara que acciones admite y con que parametros (ver
`EVENTOS`), de modo que una regla mal formada se rechaza al guardarla y no en operacion.
"""

import operator
from collections.abc import Callable
from datetime import date
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter, ValidationError

_FALTANTE = object()

_OPERADORES: dict[str, Callable[[Any, Any], bool]] = {
    "eq": operator.eq,
    "ne": operator.ne,
    "gt": operator.gt,
    "gte": operator.ge,
    "lt": operator.lt,
    "lte": operator.le,
    "in": lambda a, b: a in b,
    "nin": lambda a, b: a not in b,
    "contiene": lambda a, b: b in a,
}


class CondicionInvalida(ValueError):
    pass


def resolver(contexto: dict[str, Any], ruta: str) -> Any:
    actual: Any = contexto
    for parte in ruta.split("."):
        if isinstance(actual, dict) and parte in actual:
            actual = actual[parte]
        else:
            return _FALTANTE
    return actual


def cumple(condicion: dict[str, Any], contexto: dict[str, Any]) -> bool:
    if not condicion:
        return True
    if "todas" in condicion:
        return all(cumple(c, contexto) for c in condicion["todas"])
    if "alguna" in condicion:
        return any(cumple(c, contexto) for c in condicion["alguna"])
    if "no" in condicion:
        return not cumple(condicion["no"], contexto)
    valor = resolver(contexto, condicion["campo"])
    op = condicion["op"]
    if op == "existe":
        return (valor is not _FALTANTE and valor is not None) == condicion.get("valor", True)
    if valor is _FALTANTE or valor is None:
        return False
    try:
        return bool(_OPERADORES[op](valor, condicion["valor"]))
    except TypeError:
        # Tipos incomparables (p. ej. texto contra numero): la condicion no se cumple.
        return False


def validar_condicion(condicion: dict[str, Any]) -> None:
    if not isinstance(condicion, dict):
        raise CondicionInvalida("La condicion debe ser un objeto")
    if not condicion:
        return
    compuestas = {"todas", "alguna"} & condicion.keys()
    if compuestas:
        clave = compuestas.pop()
        if not isinstance(condicion[clave], list) or not condicion[clave]:
            raise CondicionInvalida(f"'{clave}' debe ser una lista no vacia")
        for c in condicion[clave]:
            validar_condicion(c)
        return
    if "no" in condicion:
        validar_condicion(condicion["no"])
        return
    if not isinstance(condicion.get("campo"), str) or not condicion["campo"]:
        raise CondicionInvalida("Cada comparacion necesita 'campo'")
    op = condicion.get("op")
    if op != "existe" and op not in _OPERADORES:
        raise CondicionInvalida(f"Operador desconocido: {op}")
    if op != "existe" and "valor" not in condicion:
        raise CondicionInvalida(f"El operador '{op}' necesita 'valor'")
    if op in ("in", "nin") and not isinstance(condicion["valor"], list):
        raise CondicionInvalida(f"El operador '{op}' necesita una lista en 'valor'")


# --- Acciones por evento ------------------------------------------------------------------


class AccionEstadoCartera(BaseModel):
    tipo: Literal["estado"]
    estado: Literal["activa", "en_mora", "congelada"]


class AccionNotificar(BaseModel):
    tipo: Literal["notificar"]
    plantilla: str
    clave: str = Field(description="Identifica el aviso para no repetirlo en el mismo periodo")


class AccionTarea(BaseModel):
    tipo: Literal["tarea"]
    titulo: str
    area: Literal["comercial", "operaciones", "medico", "cartera", "servicio_cliente"]
    prioridad: Literal["baja", "media", "alta"] = "media"
    vence_en_dias: int = Field(default=2, ge=0)


class AccionProrrateo(BaseModel):
    tipo: Literal["prorrateo"]
    modo: Literal["diario", "sin_cargo", "proximo_ciclo"]


class AccionRechazar(BaseModel):
    tipo: Literal["rechazar"]
    motivo: str


class AccionAjusteMascota(BaseModel):
    tipo: Literal["ajuste_mascota"]
    valor_por_mascota_adicional: float = Field(ge=0)
    maximo_adicionales: int = Field(default=0, ge=0)


class AccionRecomendar(BaseModel):
    tipo: Literal["recomendar"]
    plan_codigo: str
    motivo: str


def _union(*modelos: type[BaseModel]) -> TypeAdapter[Any]:
    if len(modelos) == 1:
        return TypeAdapter(modelos[0])
    union = Union[modelos]  # type: ignore[valid-type]  # noqa: UP007
    return TypeAdapter(Annotated[union, Field(discriminator="tipo")])


EVENTOS: dict[str, tuple[str, TypeAdapter[Any]]] = {
    "cartera.estado": (
        "Estado de cartera segun dias de mora (F1-CAR-03)",
        _union(AccionEstadoCartera),
    ),
    "cartera.alerta": ("Avisos escalonados de mora (F1-CAR-04)", _union(AccionNotificar)),
    "cartera.renovacion": (
        "Tarea comercial por contrato proximo a vencer (F1-CAR-07)",
        _union(AccionTarea),
    ),
    "plan.cambio": (
        "Cobro al cambiar de plan (F1-PLA-02)",
        _union(AccionProrrateo, AccionRechazar),
    ),
    "plan.mascota": (
        "Ajustes al agregar mascotas sobre el cupo (F1-PLA-03)",
        _union(AccionAjusteMascota, AccionRechazar),
    ),
    "plan.recomendacion": (
        "Plan sugerido por ciudad y familia (F1-PLA-04)",
        _union(AccionRecomendar),
    ),
    "servicio.transicion": (
        "Disparadores al cambiar de estado un servicio (F1-SER-03)",
        _union(AccionTarea, AccionNotificar),
    ),
    "servicio.elegibilidad": (
        "Restricciones adicionales para agendar (F1-SER-05)",
        _union(AccionRechazar),
    ),
}


def validar_accion(evento: str, accion: dict[str, Any]) -> dict[str, Any]:
    if evento not in EVENTOS:
        raise CondicionInvalida(f"Evento desconocido: {evento}")
    try:
        modelo = EVENTOS[evento][1].validate_python(accion)
    except ValidationError as e:
        tipos = e.errors()[0]
        raise CondicionInvalida(f"Accion invalida para {evento}: {tipos['msg']}") from e
    return dict(modelo.model_dump())


def vigente(desde: date | None, hasta: date | None, dia: date) -> bool:
    return (desde is None or desde <= dia) and (hasta is None or dia <= hasta)

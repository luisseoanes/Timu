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
from collections.abc import Callable, Mapping
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


# --- Acciones por evento ----------------------------------------------------------------------


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


# Eventos que el motor ya no evalua pero siguen en la base (EventoRegla) por las reglas y los
# cambios de plan que los citan. Una regla de un evento retirado no se puede crear ni editar.
EVENTOS_RETIRADOS: dict[str, str] = {
    # Migracion 0033. El motivo se muestra tal cual en Administracion: lleva tildes.
    "plan.mascota": "Lo sustituyen las tarifas por número de peludos",
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


# --- Las reglas en palabras -------------------------------------------------------------------
# La administracion lee cada regla sin descifrar su JSON. Son cadenas que se muestran tal cual:
# llevan tildes. Un campo que no esta aqui se lee por su ruta.

_CAMPOS = {
    "dias_mora": "Días de mora",
    "cuotas_vencidas": "Cuotas vencidas",
    "saldo_pendiente": "Saldo pendiente",
    "estado_actual": "Estado del contrato",
    "estado": "Estado del contrato",
    "dias_para_renovacion": "Días para la renovación",
    "ciudad": "Ciudad",
    "mascotas.total": "Número de mascotas",
    "mascotas.especies": "Especies",
    "familia.ciudad": "Ciudad de la familia",
    "familia.estado": "Estado de la familia",
    "plan.codigo": "Plan",
    "servicio.tipo": "Tipo de servicio",
    "servicio.modalidad": "Modalidad del servicio",
    "mascota.especie": "Especie",
    "estado_anterior": "Estado anterior del servicio",
    "estado_nuevo": "Nuevo estado del servicio",
    "plan_anterior.codigo": "Plan anterior",
    "plan_nuevo.codigo": "Plan nuevo",
    "sube": "Sube de valor",
}


# Los estados de servicio y de afiliacion que citan las reglas, por su nombre en el panel.
_VALORES = {
    "solicitado": "solicitado",
    "agendado": "agendado",
    "en_ruta": "en camino",
    "en_atencion": "en atención",
    "completado": "completado",
    "pendiente_autorizacion": "por autorizar",
    "reprogramado": "reprogramado",
    "cancelado": "cancelado",
    "prospecto": "prospecto",
    "activa": "al día",
    "en_mora": "en mora",
    "congelada": "congelada",
    "cancelada": "cancelada",
    "servicio_cliente": "servicio al cliente",
    "medico": "médico",
}

# El nombre de cada evento, sin la referencia al backlog que lleva su descripcion.
_NOMBRES_EVENTOS = {
    "cartera.estado": "Estado de cartera según los días de mora",
    "cartera.alerta": "Avisos escalonados de mora",
    "cartera.renovacion": "Tarea comercial por contrato próximo a vencer",
    "plan.cambio": "Cobro al cambiar de plan",
    "plan.recomendacion": "Plan sugerido por ciudad y familia",
    "servicio.transicion": "Al cambiar de estado un servicio",
    "servicio.elegibilidad": "Restricciones para agendar",
    "plan.mascota": "Precio por mascota",
}


def nombre_evento(evento: str) -> str:
    return _NOMBRES_EVENTOS.get(evento, evento)


def nombre_campo(campo: str) -> str:
    return _CAMPOS.get(campo, campo.replace(".", " de ").replace("_", " ").capitalize())


def campos(condicion: dict[str, Any]) -> list[dict[str, Any]]:
    """Los campos que mira una condicion, una vez cada uno, con su nombre y si son numericos: lo
    que hay que contarle al motor para probar la regla."""
    vistos: dict[str, dict[str, Any]] = {}

    def recorrer(c: dict[str, Any]) -> None:
        if "no" in c:
            recorrer(c["no"])
        for clave in ("todas", "alguna"):
            for sub in c.get(clave, []):
                recorrer(sub)
        if "campo" in c and c["campo"] not in vistos:
            valor = c.get("valor")
            numerico = isinstance(valor, int | float) and not isinstance(valor, bool)
            vistos[c["campo"]] = {
                "campo": c["campo"],
                "nombre": nombre_campo(c["campo"]),
                "numerico": numerico,
            }

    recorrer(condicion)
    return list(vistos.values())


def _valor(v: Any) -> str:
    if isinstance(v, bool):
        return "sí" if v else "no"
    if isinstance(v, str):
        return _VALORES.get(v, v.replace("_", " "))
    return str(v)


def _lista(valores: list[Any], y: str) -> str:
    textos = [_valor(v) for v in valores]
    return textos[0] if len(textos) == 1 else f"{', '.join(textos[:-1])} {y} {textos[-1]}"


def _simple(c: dict[str, Any]) -> str:
    nombre = nombre_campo(str(c["campo"]))
    op = c["op"]
    valor: Any = c.get("valor")
    frase = {
        "eq": lambda: _valor(valor),
        "ne": lambda: f"distinto de {_valor(valor)}",
        "gt": lambda: f"más de {_valor(valor)}",
        "gte": lambda: f"{_valor(valor)} o más",
        "lt": lambda: f"menos de {_valor(valor)}",
        "lte": lambda: f"{_valor(valor)} o menos",
        "in": lambda: _lista(valor, "o"),
        "nin": lambda: f"ninguno de {_lista(valor, 'y')}",
        "contiene": lambda: f"incluye {_valor(valor)}",
        "existe": lambda: "registrado",
    }[op]()
    return f"{nombre}: {frase}"


def describir_condicion(condicion: dict[str, Any]) -> str:
    """«Días de mora: 25 o más»; las compuestas, unidas con «y» u «o», entre parentesis dentro de
    otra."""

    def texto(c: dict[str, Any], dentro: bool) -> str:
        if not c:
            return "Siempre"
        if "no" in c:
            return f"No se cumple: {texto(c['no'], True)}"
        for clave, union in (("todas", " y "), ("alguna", " o ")):
            if clave in c:
                partes = union.join(texto(sub, True) for sub in c[clave])
                return f"({partes})" if dentro and len(c[clave]) > 1 else partes
        return _simple(c)

    return texto(condicion, False)


_PRORRATEO = {
    "diario": "Cobra la diferencia por los días que faltan del periodo",
    "sin_cargo": "Cambia de plan sin cobrar la diferencia",
    "proximo_ciclo": "Cobra la diferencia desde el próximo periodo",
}


def describir_accion(accion: dict[str, Any], titulos: Mapping[str, str] | None = None) -> str:
    """Lo que hace la regla cuando se cumple, en una frase. `titulos` nombra cada plantilla de
    WhatsApp como la llama el equipo (`comunicaciones.titulos_plantillas`)."""
    tipo = accion.get("tipo")
    if tipo == "estado":
        return f"Pasa el contrato a «{_valor(accion['estado'])}»"
    if tipo == "notificar":
        titulo = (titulos or {}).get(accion["plantilla"])
        if titulo:
            return f"Envía por WhatsApp «{titulo}»"
        # Sin nombre para el equipo, el codigo con que se registra en Meta, como dato secundario.
        return f"Envía un aviso por WhatsApp (plantilla {accion['plantilla']})"
    if tipo == "tarea":
        dias = accion.get("vence_en_dias", 2)
        plazo = f"{dias} {'día' if dias == 1 else 'días'}"
        return (
            f"Crea la tarea «{accion['titulo']}» para {_valor(accion['area'])}, prioridad "
            f"{accion.get('prioridad', 'media')}, que vence en {plazo}"
        )
    if tipo == "prorrateo":
        return _PRORRATEO.get(accion["modo"], _valor(accion["modo"]))
    if tipo == "rechazar":
        return f"No lo permite: {accion['motivo']}"
    if tipo == "recomendar":
        return f"Recomienda el plan «{accion['plan_codigo']}»: {accion['motivo']}"
    return _valor(str(tipo))


def vigente(desde: date | None, hasta: date | None, dia: date) -> bool:
    return (desde is None or desde <= dia) and (hasta is None or dia <= hasta)

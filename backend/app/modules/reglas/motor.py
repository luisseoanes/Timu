"""F0-12 Motor de reglas.

Condiciones (JSON), sin codigo ejecutable:

    {"todas": [c1, c2]}      {"alguna": [c1, c2]}      {"no": c}      {}  (siempre)
    {"campo": "familia.ciudad", "op": "eq", "valor": "Cali"}

Operadores: eq, ne, gt, gte, lt, lte, in, nin, contiene, existe.
`campo` es una ruta con puntos dentro del contexto que entrega el modulo que evalua.

Acciones: cada evento declara que acciones admite y con que parametros (`acciones.py`), y que
datos da a sus reglas (`contextos.py`).
"""

import operator
from collections.abc import Callable, Mapping
from datetime import date
from typing import Any

from pydantic import ValidationError

from app.modules.reglas.acciones import EVENTOS
from app.modules.reglas.contextos import (
    CONTEXTOS,
    OPERADORES,
    PLANES,
    CampoDeclarado,
    Opciones,
    campos_del_evento,
)

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


def validar_condicion(condicion: dict[str, Any], evento: str | None = None) -> None:
    """La forma de la condicion y, con `evento`, que cada campo sea uno de los que da ese evento,
    comparado como admite su tipo y con un valor de ese tipo."""
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
            validar_condicion(c, evento)
        return
    if "no" in condicion:
        validar_condicion(condicion["no"], evento)
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
    if evento is not None:
        _validar_contra_el_evento(condicion, evento)


def _validar_contra_el_evento(c: dict[str, Any], evento: str) -> None:
    declarado = campos_del_evento(evento).get(c["campo"])
    if declarado is None:
        raise CondicionInvalida(f"{nombre_evento(evento)} no da el dato «{c['campo']}»")
    nombre = nombre_campo(c["campo"])
    if c["op"] not in OPERADORES[declarado.tipo]:
        raise CondicionInvalida(f"«{nombre}» no se compara con '{c['op']}'")
    valor = c["valor"]
    if declarado.tipo == "numero":
        valido = isinstance(valor, int | float) and not isinstance(valor, bool)
    elif declarado.tipo == "si_no":
        valido = isinstance(valor, bool)
    elif c["op"] in ("in", "nin"):
        valido = bool(valor) and all(isinstance(v, str) and v for v in valor)
    else:
        valido = isinstance(valor, str) and bool(valor)
    if not valido:
        raise CondicionInvalida(f"Valor no valido para «{nombre}»")


def valores_con_opciones(condicion: dict[str, Any], evento: str) -> list[tuple[Opciones, str]]:
    """Cada valor de la condicion que sale de un catalogo, con su fuente: el router comprueba con
    la base que exista (un plan o una ciudad mal escritos no aplicarian nunca)."""
    declarados = campos_del_evento(evento)
    salida: list[tuple[Opciones, str]] = []

    def recorrer(c: dict[str, Any]) -> None:
        if "no" in c:
            recorrer(c["no"])
        for clave in ("todas", "alguna"):
            for sub in c.get(clave, []):
                recorrer(sub)
        declarado = declarados.get(c.get("campo", ""))
        if declarado is not None and declarado.opciones is not None:
            valores = c["valor"] if isinstance(c["valor"], list) else [c["valor"]]
            salida.extend((declarado.opciones, v) for v in valores)

    recorrer(condicion)
    return salida


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
    return dict(modelo.model_dump(exclude_none=True))


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
    "plan_anterior.valor": "Valor del plan anterior",
    "plan_nuevo.valor": "Valor del plan nuevo",
    "mascotas.caninos": "Perros",
    "mascotas.felinos": "Gatos",
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
    # Modalidades de servicio (enums.TipoServicio), como las nombra el panel.
    "domiciliario": "a domicilio",
    "preventivo": "preventiva",
    "clinico": "en la clínica",
    "aliada": "clínica aliada",
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


# Cuando se revisan las reglas de cada evento y que se hace con las que se cumplen, para quien
# crea una regla.
CUANDO = {
    "cartera.estado": (
        "Cada día, en cada contrato: la primera regla que se cumple fija su estado de cartera."
    ),
    "cartera.alerta": (
        "Cada día, en cada contrato con una cuota vencida: se envía el aviso más avanzado que "
        "se cumpla y aún no se haya enviado por esa cuota."
    ),
    "cartera.renovacion": (
        "Cada día, en cada contrato que renueva en los próximos 90 días: cada regla que se "
        "cumple crea su tarea una vez por renovación."
    ),
    "plan.cambio": (
        "Al cambiar el plan de un peludo: la primera regla que se cumple dice cómo se cobra o "
        "si no se permite."
    ),
    "plan.recomendacion": (
        "Al pedir el plan sugerido para una ciudad y unos peludos: gana la primera regla que se "
        "cumple y cuyo plan se vende allí."
    ),
    "servicio.transicion": (
        "Cada vez que un servicio cambia de estado: aplican todas las que se cumplen."
    ),
    "servicio.elegibilidad": (
        "Al agendar un servicio: cada regla que se cumple lo impide y dice su motivo."
    ),
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


# El nombre de cada valor de un catalogo, por su fuente («planes» → {«mi_amigo_fiel»: «Mi Amigo
# Fiel»}): lo arma `reglas.service.nombres` con la base.
Nombres = Mapping[str, Mapping[str, str]]


def _valor(v: Any, tabla: Mapping[str, str] | None = None) -> str:
    if isinstance(v, bool):
        return "sí" if v else "no"
    if isinstance(v, str):
        if tabla and v in tabla:
            return tabla[v]
        return _VALORES.get(v, v.replace("_", " "))
    return str(v)


def _es_numero(v: Any) -> bool:
    return isinstance(v, int | float) and not isinstance(v, bool)


def _lista(valores: list[Any], y: str, tabla: Mapping[str, str] | None) -> str:
    textos = [_valor(v, tabla) for v in valores]
    return textos[0] if len(textos) == 1 else f"{', '.join(textos[:-1])} {y} {textos[-1]}"


def _simple(c: dict[str, Any], declarados: Mapping[str, CampoDeclarado], nombres: Nombres) -> str:
    nombre = nombre_campo(str(c["campo"]))
    op = c["op"]
    valor: Any = c.get("valor")
    declarado = declarados.get(c["campo"])
    fuente = declarado.opciones.fuente if declarado and declarado.opciones else None
    tabla = nombres.get(fuente) if fuente else None
    frase = {
        # Las mismas palabras que la comparacion en el editor (contextos.OPERADORES).
        "eq": lambda: f"igual a {valor}" if _es_numero(valor) else _valor(valor, tabla),
        "ne": lambda: f"distinto de {_valor(valor, tabla)}",
        "gt": lambda: f"más de {_valor(valor)}",
        "gte": lambda: f"al menos {_valor(valor)}",
        "lt": lambda: f"menos de {_valor(valor)}",
        "lte": lambda: f"como mucho {_valor(valor)}",
        "in": lambda: _lista(valor, "o", tabla),
        "nin": lambda: f"ninguno de {_lista(valor, 'y', tabla)}",
        "contiene": lambda: f"incluye {_valor(valor, tabla)}",
        "existe": lambda: "registrado",
    }[op]()
    return f"{nombre}: {frase}"


def describir_condicion(
    condicion: dict[str, Any], evento: str | None = None, nombres: Nombres | None = None
) -> str:
    """«Días de mora: 25 o más»; las compuestas, unidas con «y» u «o», entre parentesis dentro de
    otra. Con el evento y `nombres`, un valor de catalogo se dice por su nombre («Mi Amigo
    Fiel», no «mi_amigo_fiel»)."""
    declarados = campos_del_evento(evento) if evento in CONTEXTOS else {}

    def texto(c: dict[str, Any], dentro: bool) -> str:
        if not c:
            return "Siempre"
        if "no" in c:
            return f"No se cumple: {texto(c['no'], True)}"
        for clave, union in (("todas", " y "), ("alguna", " o ")):
            if clave in c:
                partes = union.join(texto(sub, True) for sub in c[clave])
                return f"({partes})" if dentro and len(c[clave]) > 1 else partes
        return _simple(c, declarados, nombres or {})

    return texto(condicion, False)


_PRORRATEO = {
    "diario": "Cobra la diferencia por los días que faltan del periodo",
    "sin_cargo": "Cambia de plan sin cobrar la diferencia",
    "proximo_ciclo": "Cobra la diferencia desde el próximo periodo",
}


def describir_accion(
    accion: dict[str, Any],
    titulos: Mapping[str, str] | None = None,
    nombres: Nombres | None = None,
) -> str:
    """Lo que hace la regla cuando se cumple, en una frase. `titulos` nombra cada plantilla de
    WhatsApp como la llama el equipo (`comunicaciones.titulos_plantillas`), y `nombres`, el plan
    que recomienda."""
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
        plan = _valor(accion["plan_codigo"], (nombres or {}).get(PLANES.fuente))
        return f"Recomienda el plan «{plan}»: {accion['motivo']}"
    return _valor(str(tipo))


def vigente(desde: date | None, hasta: date | None, dia: date) -> bool:
    return (desde is None or desde <= dia) and (hasta is None or dia <= hasta)

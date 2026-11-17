"""F0-12 Lo que puede hacer una regla en cada evento.

Cada evento declara que acciones admite y con que parametros, de modo que una regla mal formada
se rechaza al guardarla y no en operacion, y el editor de reglas pide cada parametro con su
nombre y sus valores posibles.
"""

from dataclasses import dataclass
from typing import Annotated, Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel, Field, TypeAdapter

from app.modules.reglas.contextos import CONTEXTOS, PLANES, PLANTILLAS, Opciones


class AccionEstadoCartera(BaseModel):
    tipo: Literal["estado"]
    estado: Literal["activa", "en_mora", "congelada"] = Field(title="Estado")


class AccionNotificar(BaseModel):
    tipo: Literal["notificar"]
    plantilla: Annotated[str, PLANTILLAS] = Field(min_length=1, title="Plantilla de WhatsApp")
    # Identifica el aviso para no repetirlo en el mismo periodo. No es un dato del equipo: el
    # router lo toma del codigo de la regla, y al editarla conserva el que tenia.
    clave: str | None = Field(default=None, min_length=1)


class AccionTarea(BaseModel):
    tipo: Literal["tarea"]
    titulo: str = Field(min_length=1, max_length=200, title="Título de la tarea")
    area: Literal["comercial", "operaciones", "medico", "cartera", "servicio_cliente"] = Field(
        title="Área"
    )
    prioridad: Literal["baja", "media", "alta"] = Field(default="media", title="Prioridad")
    vence_en_dias: int = Field(default=2, ge=0, le=365, title="Vence en (días)")


class AccionProrrateo(BaseModel):
    tipo: Literal["prorrateo"]
    modo: Literal["diario", "sin_cargo", "proximo_ciclo"] = Field(title="Cómo se cobra")


class AccionRechazar(BaseModel):
    tipo: Literal["rechazar"]
    motivo: str = Field(min_length=1, max_length=300, title="Motivo que se le dice al equipo")


class AccionRecomendar(BaseModel):
    tipo: Literal["recomendar"]
    plan_codigo: Annotated[str, PLANES] = Field(min_length=1, title="Plan")
    motivo: str = Field(min_length=1, max_length=300, title="Por qué se recomienda")


# El nombre de cada accion y de los valores cerrados de sus parametros en el editor.
NOMBRES_ACCIONES = {
    "estado": "Cambiar el estado del contrato",
    "notificar": "Avisar por WhatsApp",
    "tarea": "Crear una tarea",
    "prorrateo": "Cobrar el cambio de plan",
    "rechazar": "No permitirlo",
    "recomendar": "Recomendar un plan",
}

NOMBRES_OPCIONES_ACCION: dict[str, dict[str, str]] = {
    "estado": {"activa": "Al día", "en_mora": "En mora", "congelada": "Congelada"},
    "area": {
        "comercial": "Comercial",
        "operaciones": "Operaciones",
        "medico": "Médico",
        "cartera": "Cartera",
        "servicio_cliente": "Servicio al cliente",
    },
    "prioridad": {"baja": "Baja", "media": "Media", "alta": "Alta"},
    "modo": {
        "diario": "La diferencia por los días que faltan del periodo",
        "sin_cargo": "Sin cobrar la diferencia",
        "proximo_ciclo": "La diferencia desde el próximo periodo",
    },
}


def _union(*modelos: type[BaseModel]) -> TypeAdapter[Any]:
    if len(modelos) == 1:
        return TypeAdapter(modelos[0])
    union = Union[modelos]  # type: ignore[valid-type]  # noqa: UP007
    return TypeAdapter(Annotated[union, Field(discriminator="tipo")])


# Cada evento: su descripcion tecnica y las acciones que admite, en el orden en que las ofrece
# el editor.
ACCIONES_POR_EVENTO: dict[str, tuple[str, tuple[type[BaseModel], ...]]] = {
    "cartera.estado": (
        "Estado de cartera segun dias de mora (F1-CAR-03)",
        (AccionEstadoCartera,),
    ),
    "cartera.alerta": ("Avisos escalonados de mora (F1-CAR-04)", (AccionNotificar,)),
    "cartera.renovacion": (
        "Tarea comercial por contrato proximo a vencer (F1-CAR-07)",
        (AccionTarea,),
    ),
    "plan.cambio": ("Cobro al cambiar de plan (F1-PLA-02)", (AccionProrrateo, AccionRechazar)),
    "plan.recomendacion": ("Plan sugerido por ciudad y familia (F1-PLA-04)", (AccionRecomendar,)),
    "servicio.transicion": (
        "Disparadores al cambiar de estado un servicio (F1-SER-03)",
        (AccionTarea, AccionNotificar),
    ),
    "servicio.elegibilidad": (
        "Restricciones adicionales para agendar (F1-SER-05)",
        (AccionRechazar,),
    ),
}

EVENTOS: dict[str, tuple[str, TypeAdapter[Any]]] = {
    evento: (descripcion, _union(*modelos))
    for evento, (descripcion, modelos) in ACCIONES_POR_EVENTO.items()
}
assert EVENTOS.keys() == CONTEXTOS.keys(), "cada evento declara su contexto y sus acciones"


@dataclass(frozen=True)
class ParametroDeclarado:
    nombre: str
    etiqueta: str
    tipo: Literal["texto", "numero", "opcion"]
    requerido: bool
    por_defecto: Any
    # Un catalogo (plantillas, planes) o los valores cerrados del parametro con su nombre.
    fuente: Opciones | None
    valores: dict[str, str] | None


def parametros_de_accion(modelo: type[BaseModel]) -> list[ParametroDeclarado]:
    """Lo que pide una accion en el editor, salvo su tipo y la clave del aviso."""
    salida = []
    for nombre, info in modelo.model_fields.items():
        if nombre in ("tipo", "clave"):
            continue
        fuente = next((m for m in info.metadata if isinstance(m, Opciones)), None)
        valores = None
        if get_origin(info.annotation) is Literal:
            literales = get_args(info.annotation)
            nombres = NOMBRES_OPCIONES_ACCION.get(nombre, {})
            valores = {v: nombres.get(v, v) for v in literales}
        tipo: Literal["texto", "numero", "opcion"] = (
            "opcion" if fuente or valores else "numero" if info.annotation is int else "texto"
        )
        salida.append(
            ParametroDeclarado(
                nombre=nombre,
                etiqueta=info.title or nombre,
                tipo=tipo,
                requerido=info.is_required(),
                por_defecto=None if info.is_required() else info.default,
                fuente=fuente,
                valores=valores,
            )
        )
    return salida


def tipo_de_accion(modelo: type[BaseModel]) -> str:
    return str(get_args(modelo.model_fields["tipo"].annotation)[0])


def valores_de_accion(accion: dict[str, Any]) -> list[tuple[Opciones, str]]:
    """Los valores de la accion que salen de un catalogo, para comprobarlos con la base. La
    plantilla no se comprueba: las de mora siguen pendientes de registrarse en Meta."""
    modelo = next(
        (
            m
            for modelos in (m for _, m in ACCIONES_POR_EVENTO.values())
            for m in modelos
            if tipo_de_accion(m) == accion.get("tipo")
        ),
        None,
    )
    if modelo is None:
        return []
    return [
        (p.fuente, accion[p.nombre])
        for p in parametros_de_accion(modelo)
        if p.fuente is not None and p.fuente != PLANTILLAS and p.nombre in accion
    ]

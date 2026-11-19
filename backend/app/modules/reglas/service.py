"""Seccion 7 Evaluacion de reglas desde la base de datos."""

import re
import unicodedata
from collections.abc import Callable, Collection
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.enums import EstadoAfiliacion, EstadoServicio, TipoServicio
from app.core.errores import ReglaNegocio
from app.core.tiempo import hoy
from app.modules.catalogos.models import Ciudad, Especie, TipoServicioCatalogo
from app.modules.comunicaciones import service as comunicaciones
from app.modules.comunicaciones.models import PlantillaWhatsApp
from app.modules.reglas import acciones, contextos, motor
from app.modules.reglas.contextos import Contexto
from app.modules.reglas.datos import PLANTILLAS_DE_LAS_REGLAS, REGLAS
from app.modules.reglas.models import Regla
from app.modules.reglas.motor import cumple, vigente


@dataclass(frozen=True)
class Resultado:
    regla: str
    nombre: str
    accion: dict[str, Any]


def evaluar(
    db: Session,
    contexto: Contexto,
    *,
    plan_id: UUID | None = None,
    planes: Collection[UUID] = (),
) -> list[Resultado]:
    """Acciones de las reglas activas y vigentes cuyo criterio se cumple, por prioridad.

    Las reglas atadas a un plan solo aplican cuando se evalua para ese plan o, con `planes`,
    para un contrato con algun peludo en el (cada peludo tiene su plan). Las generales (sin
    plan) aplican siempre.
    """
    return evaluar_datos(db, contexto.evento, contexto.datos(), plan_id=plan_id, planes=planes)


def evaluar_datos(
    db: Session,
    evento: str,
    datos: dict[str, Any],
    *,
    plan_id: UUID | None = None,
    planes: Collection[UUID] = (),
) -> list[Resultado]:
    """Como `evaluar`, con los datos sueltos: los de «Probar», que pueden venir incompletos (un
    dato que falta no cumple ninguna comparacion)."""
    aplicables = {*planes, *([plan_id] if plan_id else [])}
    stmt = select(Regla).where(Regla.evento == evento, Regla.activa.is_(True))
    stmt = stmt.where(
        or_(Regla.plan_id.is_(None), Regla.plan_id.in_(aplicables))
        if aplicables
        else Regla.plan_id.is_(None)
    )
    dia = hoy()
    resultados = []
    for regla in db.scalars(stmt.order_by(Regla.prioridad, Regla.codigo)):
        if not vigente(regla.vigente_desde, regla.vigente_hasta, dia):
            continue
        if cumple(regla.condicion, datos):
            resultados.append(Resultado(regla.codigo, regla.nombre, regla.accion))
            if regla.detener:
                break
    return resultados


def primera(
    db: Session,
    contexto: Contexto,
    *,
    plan_id: UUID | None = None,
    planes: Collection[UUID] = (),
) -> Resultado | None:
    resultados = evaluar(db, contexto, plan_id=plan_id, planes=planes)
    return resultados[0] if resultados else None


def sembrar(db: Session) -> int:
    """Crea las reglas iniciales que falten. Nunca modifica las existentes: despues de la
    primera carga, las reglas son de TIMU."""

    existentes = set(db.scalars(select(Regla.codigo)))
    nuevas = [Regla(**r) for r in REGLAS if r["codigo"] not in existentes]
    db.add_all(nuevas)
    db.flush()
    return len(nuevas)


# --- Los valores posibles de cada campo y parametro -------------------------------------------
# planes importa reglas (evalua la recomendacion y el cambio de plan), asi que reglas no puede
# importar planes: planes le conecta, al importar planes/service.py (que la API carga siempre),
# como leer sus planes. Cada uno: (id, codigo, nombre).
LeerPlanes = Callable[[Session], list[tuple[UUID, str, str]]]

_leer_planes: LeerPlanes | None = None


def conectar_planes(leer: LeerPlanes) -> None:
    global _leer_planes
    _leer_planes = leer


def planes(db: Session) -> list[tuple[UUID, str, str]]:
    if _leer_planes is None:
        # Sin conectar, el editor no ofreceria ningun plan y toda regla con plan se rechazaria.
        raise RuntimeError("reglas sin conectar: falta conectar_planes()")
    return _leer_planes(db)


def _nombre_cerrado(valor: str) -> str:
    texto = motor._VALORES.get(valor, valor.replace("_", " "))
    return texto[:1].upper() + texto[1:]


def opciones(db: Session) -> dict[str, dict[str, str]]:
    """Por fuente, cada valor posible con su nombre, en el orden en que se ofrecen."""
    plantillas: dict[str, str] = {}
    for nombre, titulo in db.execute(
        select(PlantillaWhatsApp.nombre, PlantillaWhatsApp.titulo).order_by(
            PlantillaWhatsApp.nombre, PlantillaWhatsApp.version.desc()
        )
    ).tuples():
        plantillas.setdefault(nombre, titulo or nombre)
    # Las que citan las reglas sin estar en el catalogo (las de mora esperan su registro en
    # Meta): se ofrecen igual, para que editar la regla no obligue a cambiarla.
    for accion in db.scalars(select(Regla.accion)):
        codigo = accion.get("plantilla") if accion.get("tipo") == "notificar" else None
        if codigo and codigo not in plantillas:
            nombre = PLANTILLAS_DE_LAS_REGLAS.get(codigo, codigo)
            plantillas[codigo] = f"{nombre} · aún sin registrar"
    return {
        contextos.CIUDADES.fuente: {
            n: n for n in db.scalars(select(Ciudad.nombre).order_by(Ciudad.nombre))
        },
        # `.all()`: el resultado tiene `keys()` y `dict()` lo tomaria por un diccionario.
        contextos.ESPECIES.fuente: dict(
            db.execute(select(Especie.codigo, Especie.nombre).order_by(Especie.nombre))
            .tuples()
            .all()
        ),
        contextos.TIPOS_SERVICIO.fuente: dict(
            db.execute(
                select(TipoServicioCatalogo.codigo, TipoServicioCatalogo.nombre).order_by(
                    TipoServicioCatalogo.nombre
                )
            )
            .tuples()
            .all()
        ),
        contextos.PLANES.fuente: {codigo: nombre for _, codigo, nombre in planes(db)},
        contextos.MODALIDADES.fuente: {m.value: _nombre_cerrado(m.value) for m in TipoServicio},
        contextos.ESTADOS_AFILIACION.fuente: {
            e.value: _nombre_cerrado(e.value) for e in EstadoAfiliacion
        },
        contextos.ESTADOS_SERVICIO.fuente: {
            e.value: _nombre_cerrado(e.value) for e in EstadoServicio
        },
        contextos.PLANTILLAS.fuente: plantillas,
    }


def comprobar_valores(
    db: Session,
    evento: str,
    condicion: dict[str, Any],
    accion: dict[str, Any] | None,
    plan_id: UUID | None,
) -> None:
    """Que cada valor de catalogo de la regla exista y que su plan, si tiene, sirva en el
    evento: una ciudad o un plan mal escritos harian una regla que no aplica nunca."""
    if plan_id is not None:
        if not contextos.CONTEXTOS[evento].admite_plan:
            raise ReglaNegocio(f"{motor.nombre_evento(evento)} no admite reglas de un solo plan")
        if plan_id not in {i for i, _, _ in planes(db)}:
            raise ReglaNegocio("El plan de la regla no existe")
    validos = opciones(db)
    citados = motor.valores_con_opciones(condicion, evento)
    citados += acciones.valores_de_accion(accion or {})
    for fuente, valor in citados:
        if valor not in validos[fuente.fuente]:
            raise ReglaNegocio(f"«{valor}» no está en el catálogo")


def codigo_libre(db: Session, nombre: str) -> str:
    """El codigo interno de una regla nueva, sacado de su nombre: sin tildes, en minusculas y
    unico («Aviso de mora a los 3 días» → «aviso_de_mora_a_los_3_dias»)."""
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-z0-9]+", "_", sin_tildes.lower()).strip("_")[:56] or "regla"
    base = base if len(base) >= 2 else f"regla_{base}"
    existentes = set(db.scalars(select(Regla.codigo).where(Regla.codigo.like(f"{base}%"))))
    codigo, n = base, 2
    while codigo in existentes:
        codigo, n = f"{base}_{n}", n + 1
    return codigo


# Los catalogos de la base, cuyos valores se dicen en una frase por su nombre («Mi Amigo Fiel»).
# Los conjuntos cerrados (estados, modalidades) los dice `motor` en minuscula, a mitad de frase.
_DE_CATALOGO = (
    contextos.CIUDADES.fuente,
    contextos.ESPECIES.fuente,
    contextos.TIPOS_SERVICIO.fuente,
    contextos.PLANES.fuente,
)


def nombres(db: Session) -> dict[str, dict[str, str]]:
    """Los nombres de los valores de catalogo, para decir una regla en palabras."""
    todas = opciones(db)
    return {fuente: todas[fuente] for fuente in _DE_CATALOGO}


def plantillas_faltantes(db: Session) -> list[dict[str, Any]]:
    """Seccion 12 Lo que falta configurar: las plantillas que citan las reglas activas y no tienen
    version aprobada y activa en el catalogo. Sin ella, esos avisos no salen por ningun canal."""
    titulos = titulos_plantillas(db)
    por_plantilla: dict[str, list[str]] = {}
    reglas = db.scalars(select(Regla).where(Regla.activa).order_by(Regla.prioridad, Regla.nombre))
    for regla in reglas:
        codigo = (regla.accion or {}).get("plantilla")
        if codigo:
            por_plantilla.setdefault(codigo, []).append(regla.nombre)
    return [
        {"codigo": codigo, "titulo": titulos.get(codigo, codigo), "reglas": nombres}
        for codigo, nombres in sorted(por_plantilla.items())
        if comunicaciones.plantilla_vigente(db, codigo) is None
    ]


def titulos_plantillas(db: Session) -> dict[str, str]:
    """El nombre de cada plantilla para decir una regla en palabras: el del catalogo y, para las
    de mora que aun no estan en el, el provisional."""
    return {**PLANTILLAS_DE_LAS_REGLAS, **comunicaciones.titulos_plantillas(db)}

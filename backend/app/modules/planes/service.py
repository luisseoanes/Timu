"""6.3 Planes: catalogo de planes y beneficios, y recomendacion.

Lo que vive en el contrato (vigencia, cupo de mascotas, valor, cambio de plan) es de
`cartera.contratos`: planes no conoce los contratos.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import MESES_PERIODICIDAD, Periodicidad
from app.core.errores import Conflicto, NoEncontrado, ReglaNegocio
from app.modules.planes.models import Beneficio, CiudadPlan, Plan, TarifaPeriodicidad, TarifaPlan
from app.modules.reglas import service as reglas


def obtener(db: Session, plan_id: UUID) -> Plan:
    plan = db.get(Plan, plan_id)
    if plan is None:
        raise NoEncontrado("Plan no encontrado")
    return plan


DETALLE = ("beneficios", "ciudades", "tarifas", "tarifas_periodicidad")


def con_detalle(db: Session, plan: Plan) -> Plan:
    """Recarga las colecciones que muestra la respuesta. El router serializa fuera de la
    sesion sincrona, donde una coleccion caducada ya no se puede cargar."""
    db.refresh(plan, list(DETALLE))
    return plan


def por_codigo(db: Session, codigo: str) -> Plan:
    plan = db.scalar(select(Plan).where(Plan.codigo == codigo))
    if plan is None:
        raise NoEncontrado(f"Plan {codigo} no encontrado")
    return plan


def crear(db: Session, datos: dict[str, Any]) -> Plan:
    if db.scalar(
        select(Plan.id).where((Plan.codigo == datos["codigo"]) | (Plan.nombre == datos["nombre"]))
    ):
        raise Conflicto("Ya existe un plan con ese codigo o nombre")
    beneficios = datos.pop("beneficios", [])
    tarifas = datos.pop("tarifas")
    periodicidad = datos.pop("tarifas_periodicidad", {})
    ciudades = datos.pop("ciudades")
    plan = Plan(**datos)
    plan.beneficios = [Beneficio(**b) for b in beneficios]
    db.add(plan)
    db.flush()
    reemplazar_tarifas(db, plan, tarifas, periodicidad)
    fijar_ciudades(db, plan, ciudades)
    return plan


# --- 6.2 / 6.3 Tarifas y disponibilidad -------------------------------------------------------

# Una familia afilia como maximo 10 peludos; desde 4 todos pagan la tarifa de 4.
MAX_PELUDOS = 10
PELUDOS_CON_DESCUENTO = 4


def reemplazar_tarifas(
    db: Session, plan: Plan, tarifas: list[Decimal], periodicidad: dict[str, Decimal | None]
) -> Plan:
    """Las cuatro tarifas por numero de peludos (de 1 a 4) y el precio de cada periodo largo
    para un peludo; `None` retira ese descuento. Se actualiza en su sitio: la bitacora guarda
    el valor anterior y nada se borra."""
    if len(tarifas) != PELUDOS_CON_DESCUENTO:
        raise ReglaNegocio(f"Un plan lleva {PELUDOS_CON_DESCUENTO} tarifas: de 1 a 4 peludos")
    existentes = {
        t.peludos: t for t in db.scalars(select(TarifaPlan).where(TarifaPlan.plan_id == plan.id))
    }
    for peludos, valor in enumerate(tarifas, start=1):
        if peludos in existentes:
            existentes[peludos].valor = valor
        else:
            db.add(TarifaPlan(plan_id=plan.id, peludos=peludos, valor=valor))
    largas = {
        t.periodicidad: t
        for t in db.scalars(select(TarifaPeriodicidad).where(TarifaPeriodicidad.plan_id == plan.id))
    }
    for nombre, precio in periodicidad.items():
        if nombre == Periodicidad.MENSUAL:
            raise ReglaNegocio("El mensual sale de las tarifas por numero de peludos")
        actual = largas.get(nombre)
        if precio is None:
            if actual is not None:
                actual.activa = False
        elif actual is None:
            db.add(TarifaPeriodicidad(plan_id=plan.id, periodicidad=nombre, valor=precio))
        else:
            actual.valor, actual.activa = precio, True
    db.flush()
    con_detalle(db, plan)
    return plan


def fijar_ciudades(db: Session, plan: Plan, ciudades: list[str]) -> Plan:
    """Ciudades donde se vende el plan. La que sale queda inactiva; la que vuelve, activa."""
    if not ciudades:
        raise ReglaNegocio("Un plan se vende al menos en una ciudad")
    actuales = {
        c.ciudad: c for c in db.scalars(select(CiudadPlan).where(CiudadPlan.plan_id == plan.id))
    }
    for nombre, fila in actuales.items():
        fila.activa = nombre in ciudades
    for nombre in set(ciudades) - set(actuales):
        db.add(CiudadPlan(plan_id=plan.id, ciudad=nombre))
    db.flush()
    con_detalle(db, plan)
    return plan


def tarifa(plan: Plan, peludos: int = 1) -> Decimal | None:
    """Lo que paga al mes cada peludo del plan con `peludos` en la afiliacion (desde 4, la
    de 4). Con 1 es el precio de lista del plan."""
    de = min(peludos, PELUDOS_CON_DESCUENTO)
    return next((Decimal(t.valor) for t in plan.tarifas if t.peludos == de), None)


def disponible_en(plan: Plan, ciudad: str) -> bool:
    return any(c.ciudad == ciudad for c in plan.ciudades)


@dataclass
class PeludoCotizado:
    especie: str
    plan: Plan
    valor_mensual: Decimal


@dataclass
class Cotizacion:
    """Lo que paga una afiliacion. `valor_periodo` es lo que cobra cada cuota; con un solo
    peludo y un periodo largo con precio propio, es ese precio (`descuento`)."""

    ciudad: str
    periodicidad: str
    meses: int
    tarifa_de: int  # numero de peludos cuya tarifa se aplica (de 1 a 4)
    peludos: list[PeludoCotizado]
    valor_mensual: Decimal
    valor_periodo: Decimal
    descuento: bool

    @property
    def ahorro(self) -> Decimal:
        return self.valor_mensual * self.meses - self.valor_periodo


def cotizar(
    db: Session,
    ciudad: str,
    peludos: list[tuple[str, UUID]],
    periodicidad: str,
    *,
    validar: set[int] | None = None,
) -> Cotizacion:
    """6.2 / 6.3 Unico calculo del precio de una afiliacion: `peludos` es (especie, plan) de
    cada uno. Cada peludo paga la tarifa de su plan para el numero total de peludos, esten o
    no en el mismo plan (con 4 o mas, la de 4). El descuento por periodo largo solo existe
    con un peludo y no se acumula con el de cantidad: con dos o mas, el mensual por meses.

    `validar` son las posiciones de los peludos cuyo plan debe venderse en la ciudad y
    cubrir su especie (todas si no se dice). Al recalcular un contrato solo se valida el
    peludo que entra o cambia de plan: que un plan deje de venderse en una ciudad no puede
    impedir retirar a otro peludo."""
    if not peludos:
        raise ReglaNegocio("La afiliacion necesita al menos un peludo")
    if len(peludos) > MAX_PELUDOS:
        raise ReglaNegocio(f"Una familia afilia como maximo {MAX_PELUDOS} peludos")
    meses = MESES_PERIODICIDAD[periodicidad]
    tarifa_de = min(len(peludos), PELUDOS_CON_DESCUENTO)
    cotizados: list[PeludoCotizado] = []
    for posicion, (especie, plan_id) in enumerate(peludos):
        plan = obtener(db, plan_id)
        if validar is None or posicion in validar:
            validar_para_familia(plan, ciudad, [especie])
        tarifa = next((t for t in plan.tarifas if t.peludos == tarifa_de), None)
        if tarifa is None:
            raise ReglaNegocio(f"El plan {plan.nombre} no tiene tarifa para {tarifa_de} peludos")
        cotizados.append(PeludoCotizado(especie, plan, Decimal(tarifa.valor)))
    valor_mensual = sum((p.valor_mensual for p in cotizados), Decimal(0))
    valor_periodo = valor_mensual * meses
    descuento = False
    if len(cotizados) == 1 and periodicidad != Periodicidad.MENSUAL:
        largo = next(
            (t for t in cotizados[0].plan.tarifas_periodicidad if t.periodicidad == periodicidad),
            None,
        )
        if largo is not None:
            valor_periodo, descuento = Decimal(largo.valor), True
    return Cotizacion(
        ciudad, periodicidad, meses, tarifa_de, cotizados, valor_mensual, valor_periodo, descuento
    )


def reemplazar_beneficios(db: Session, plan: Plan, beneficios: list[dict[str, Any]]) -> Plan:
    """Los beneficios vigentes pasan a inactivos y se crean los nuevos: nada se borra."""
    for anterior in plan.beneficios:
        anterior.activo = False
    # Antes de crear los nuevos: el indice unico parcial solo admite uno vigente por tipo.
    db.flush()
    db.add_all(Beneficio(plan_id=plan.id, **b) for b in beneficios)
    db.flush()
    con_detalle(db, plan)
    return plan


def validar_para_familia(plan: Plan, ciudad: str, especies: list[str]) -> None:
    if not plan.activo:
        raise ReglaNegocio(f"El plan {plan.nombre} no esta activo")
    if not disponible_en(plan, ciudad):
        raise ReglaNegocio(f"El plan {plan.nombre} no esta disponible en {ciudad}")
    if plan.especies:
        fuera = sorted(set(especies) - set(plan.especies))
        if fuera:
            raise ReglaNegocio(f"El plan {plan.nombre} no cubre: {', '.join(fuera)}")


# --- F1-PLA-04 Recomendacion ------------------------------------------------------------------


def recomendar(db: Session, ciudad: str, especies: list[str]) -> tuple[Plan, str, str]:
    """Devuelve (plan, motivo, regla). Si el plan recomendado no aplica en la ciudad o para
    las especies, se prueba la siguiente regla que se cumpla."""
    contexto = {
        "ciudad": ciudad,
        "mascotas": {
            "total": len(especies),
            **{f"{e}s": especies.count(e) for e in set(especies)},
            "especies": sorted(set(especies)),
        },
    }
    for resultado in reglas.evaluar(db, "plan.recomendacion", contexto):
        plan = db.scalar(select(Plan).where(Plan.codigo == resultado.accion["plan_codigo"]))
        if plan is None:
            continue
        try:
            validar_para_familia(plan, ciudad, especies)
        except ReglaNegocio:
            continue
        return plan, resultado.accion["motivo"], resultado.regla
    # Sin regla aplicable: el plan activo mas economico que cubra a la familia.
    activos = db.scalars(select(Plan).where(Plan.activo.is_(True)))
    con_tarifa = [p for p in activos if tarifa(p, len(especies)) is not None]
    for plan in sorted(con_tarifa, key=lambda p: (tarifa(p, len(especies)), p.codigo)):
        try:
            validar_para_familia(plan, ciudad, especies)
        except ReglaNegocio:
            continue
        return plan, "Plan de menor valor que cubre a todas las mascotas", "por_defecto"
    raise NoEncontrado("No hay un plan disponible para esa ciudad y esas mascotas")

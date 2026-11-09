"""6.3 Planes: catalogo de planes y beneficios, y recomendacion.

Lo que vive en el contrato (vigencia, cupo de mascotas, valor, cambio de plan) es de
`cartera.contratos`: planes no conoce los contratos.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errores import Conflicto, NoEncontrado, ReglaNegocio
from app.modules.planes.models import Beneficio, Plan
from app.modules.reglas import service as reglas


def obtener(db: Session, plan_id: UUID) -> Plan:
    plan = db.get(Plan, plan_id)
    if plan is None:
        raise NoEncontrado("Plan no encontrado")
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
    plan = Plan(**datos)
    plan.beneficios = [Beneficio(**b) for b in beneficios]
    db.add(plan)
    db.flush()
    return plan


def reemplazar_beneficios(db: Session, plan: Plan, beneficios: list[dict[str, Any]]) -> Plan:
    """Los beneficios vigentes pasan a inactivos y se crean los nuevos: nada se borra."""
    for anterior in plan.beneficios:
        anterior.activo = False
    # Antes de crear los nuevos: el indice unico parcial solo admite uno vigente por tipo.
    db.flush()
    db.add_all(Beneficio(plan_id=plan.id, **b) for b in beneficios)
    db.flush()
    # Recarga aqui, dentro de la sesion sincrona: el router serializa la respuesta fuera de
    # ella y una coleccion caducada no se puede cargar ahi.
    db.refresh(plan, ["beneficios"])
    return plan


def validar_para_familia(plan: Plan, ciudad: str, especies: list[str]) -> None:
    if not plan.activo:
        raise ReglaNegocio(f"El plan {plan.nombre} no esta activo")
    if plan.ciudad and plan.ciudad != ciudad:
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
    candidatos = db.scalars(
        select(Plan)
        .where(Plan.activo.is_(True), Plan.cupos_mascotas >= max(1, len(especies)))
        .order_by(Plan.valor_mensual)
    )
    for plan in candidatos:
        try:
            validar_para_familia(plan, ciudad, especies)
        except ReglaNegocio:
            continue
        return plan, "Plan de menor valor que cubre a todas las mascotas", "por_defecto"
    raise NoEncontrado("No hay un plan disponible para esa ciudad y esas mascotas")

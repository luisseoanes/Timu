"""F0-12 Evaluacion de reglas desde la base de datos."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.tiempo import hoy
from app.modules.reglas.models import Regla
from app.modules.reglas.motor import cumple, vigente


@dataclass(frozen=True)
class Resultado:
    regla: str
    nombre: str
    accion: dict[str, Any]


def evaluar(
    db: Session,
    evento: str,
    contexto: dict[str, Any],
    *,
    plan_id: UUID | None = None,
) -> list[Resultado]:
    """Acciones de las reglas activas y vigentes cuyo criterio se cumple, por prioridad.

    Las reglas atadas a un plan solo aplican cuando se evalua para ese plan; las generales
    (sin plan) aplican siempre.
    """
    stmt = select(Regla).where(Regla.evento == evento, Regla.activa.is_(True))
    stmt = stmt.where(
        or_(Regla.plan_id.is_(None), Regla.plan_id == plan_id)
        if plan_id
        else Regla.plan_id.is_(None)
    )
    dia = hoy()
    resultados = []
    for regla in db.scalars(stmt.order_by(Regla.prioridad, Regla.codigo)):
        if not vigente(regla.vigente_desde, regla.vigente_hasta, dia):
            continue
        if cumple(regla.condicion, contexto):
            resultados.append(Resultado(regla.codigo, regla.nombre, regla.accion))
            if regla.detener:
                break
    return resultados


def primera(
    db: Session, evento: str, contexto: dict[str, Any], *, plan_id: UUID | None = None
) -> Resultado | None:
    resultados = evaluar(db, evento, contexto, plan_id=plan_id)
    return resultados[0] if resultados else None


def sembrar(db: Session) -> int:
    """Crea las reglas iniciales que falten. Nunca modifica las existentes: despues de la
    primera carga, las reglas son de TIMU."""
    from app.modules.reglas.datos import REGLAS

    existentes = set(db.scalars(select(Regla.codigo)))
    nuevas = [Regla(**r) for r in REGLAS if r["codigo"] not in existentes]
    db.add_all(nuevas)
    db.flush()
    return len(nuevas)

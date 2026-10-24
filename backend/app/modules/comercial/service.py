"""F3-COM-01 Embudo comercial: todo interesado entra con su origen y un responsable."""

from datetime import date, datetime, time, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.enums import Rol
from app.core.errores import NoEncontrado, ReglaNegocio
from app.core.tiempo import ZONA_NEGOCIO, ahora
from app.core.validaciones import normalizar_telefono
from app.modules.comercial.models import Interesado

ETAPAS = ("nuevo", "contactado", "cotizado", "en_afiliacion", "afiliado")
ABIERTAS = ("nuevo", "contactado", "cotizado", "en_afiliacion")


def _telefono(valor: str | None) -> str | None:
    if not valor:
        return None
    try:
        return normalizar_telefono(valor)
    except ValueError:
        return "+" + valor.lstrip("+")


def asignar_responsable(db: Session) -> UUID | None:
    """El comercial activo con menos interesados abiertos (reparto por carga)."""
    from app.modules.auth.models import Usuario

    carga = (
        select(Interesado.responsable_id, func.count().label("n"))
        .where(Interesado.etapa.in_(ABIERTAS))
        .group_by(Interesado.responsable_id)
        .subquery()
    )
    return db.scalar(
        select(Usuario.id)
        .outerjoin(carga, carga.c.responsable_id == Usuario.id)
        .where(Usuario.rol == Rol.COMERCIAL, Usuario.activo.is_(True))
        .order_by(func.coalesce(carga.c.n, 0), Usuario.created_at)
        .limit(1)
    )


def registrar(
    db: Session,
    *,
    origen: str,
    telefono: str | None = None,
    nombre: str | None = None,
    email: str | None = None,
    ciudad: str | None = None,
    familia_id: UUID | None = None,
    etapa: str | None = None,
    datos: dict[str, Any] | None = None,
) -> Interesado:
    """Crea al interesado o actualiza el existente (mismo telefono o email). No pisa lo que
    ya se sabia ni lo hace retroceder en el embudo."""
    telefono = _telefono(telefono)
    email = email.lower() if email else None
    condiciones = []
    if telefono:
        condiciones.append(Interesado.telefono == telefono)
    if email:
        condiciones.append(Interesado.email == email)
    if familia_id:
        condiciones.append(Interesado.familia_id == familia_id)
    if not condiciones:
        raise ReglaNegocio("El interesado necesita al menos telefono o email")
    interesado = db.scalar(select(Interesado).where(or_(*condiciones)).limit(1))
    if interesado is None:
        interesado = Interesado(
            origen=origen,
            etapa="nuevo",
            telefono=telefono,
            email=email,
            datos={},
            responsable_id=asignar_responsable(db),
        )
        db.add(interesado)
    for campo, valor in (("nombre", nombre), ("ciudad", ciudad), ("familia_id", familia_id)):
        if valor and not getattr(interesado, campo):
            setattr(interesado, campo, valor)
    if telefono and not interesado.telefono:
        interesado.telefono = telefono
    if email and not interesado.email:
        interesado.email = email
    if datos:
        interesado.datos = {**(interesado.datos or {}), **datos}
    if etapa:
        avanzar(interesado, etapa)
    interesado.ultimo_contacto = ahora()
    db.flush()
    return interesado


def avanzar(interesado: Interesado, etapa: str) -> None:
    """Solo hacia adelante; 'perdido' se marca con `perder`."""
    if interesado.etapa == "perdido" or etapa not in ETAPAS:
        return
    if ETAPAS.index(etapa) > ETAPAS.index(interesado.etapa):
        interesado.etapa = etapa


def perder(db: Session, interesado: Interesado, motivo: str) -> Interesado:
    if interesado.etapa == "afiliado":
        raise ReglaNegocio("Un interesado afiliado no se marca como perdido")
    interesado.etapa = "perdido"
    interesado.motivo_perdida = motivo
    db.flush()
    return interesado


def reactivar(db: Session, interesado: Interesado) -> Interesado:
    if interesado.etapa != "perdido":
        raise ReglaNegocio("Solo se reactiva un interesado perdido")
    interesado.etapa = "contactado"
    interesado.motivo_perdida = None
    db.flush()
    return interesado


def obtener(db: Session, interesado_id: UUID) -> Interesado:
    interesado = db.get(Interesado, interesado_id)
    if interesado is None:
        raise NoEncontrado("Interesado no encontrado")
    return interesado


def embudo(db: Session, desde: date, hasta: date) -> dict[str, Any]:
    """Interesados del periodo por etapa y por origen, y su conversion a afiliado."""
    inicio = datetime.combine(desde, time.min, ZONA_NEGOCIO)
    fin = datetime.combine(hasta + timedelta(days=1), time.min, ZONA_NEGOCIO)
    periodo = (
        select(Interesado)
        .where(Interesado.created_at >= inicio, Interesado.created_at < fin)
        .subquery()
    )
    por_etapa = dict(
        db.execute(select(periodo.c.etapa, func.count()).group_by(periodo.c.etapa)).tuples().all()
    )
    por_origen: dict[str, dict[str, int]] = {}
    for origen, etapa, n in db.execute(
        select(periodo.c.origen, periodo.c.etapa, func.count()).group_by(
            periodo.c.origen, periodo.c.etapa
        )
    ):
        fila = por_origen.setdefault(origen, {"total": 0, "afiliados": 0})
        fila["total"] += n
        fila["afiliados"] += n if etapa == "afiliado" else 0
    total = sum(por_etapa.values())
    return {
        "total": total,
        "por_etapa": {e: por_etapa.get(e, 0) for e in (*ETAPAS, "perdido")},
        "por_origen": por_origen,
        "conversion": round(por_etapa.get("afiliado", 0) / total, 3) if total else None,
    }

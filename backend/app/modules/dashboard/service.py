"""F4-DAS-01 / 02 Indicadores gerenciales: definicion, formula y calculo.

Cada indicador declara su formula en texto: es la definicion acordada, la que se muestra
en el panel junto al numero y la que documenta docs/indicadores.md. Si cambia la
formula, cambia aqui y en ese documento a la vez.

Todo se calcula con agregaciones en la base (COUNT, SUM, AVG), filtrado por periodo y,
opcionalmente, ciudad. El resultado se cachea unos minutos (F4-DAS-02).
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, and_, case, func, or_, select
from sqlalchemy.orm import Session

from app.core import cache
from app.core.enums import EstadoAfiliacion, EstadoServicio
from app.core.errores import ReglaNegocio
from app.core.tiempo import ZONA_NEGOCIO
from app.modules.cartera.models import AplicacionPago, Contrato, Cuota, EstadoCuota, Pago
from app.modules.cartera.periodos import sumar_meses
from app.modules.encuestas.models import Encuesta
from app.modules.familias.models import Familia
from app.modules.rutas.models import ParadaRuta, Ruta
from app.modules.servicios.models import Servicio

CACHE_SEGUNDOS = 300
MAX_DIAS = 400
VIGENTES = (EstadoAfiliacion.ACTIVA, EstadoAfiliacion.EN_MORA, EstadoAfiliacion.CONGELADA)


@dataclass(frozen=True)
class Periodo:
    desde: date
    hasta: date
    ciudad: str | None

    @property
    def inicio(self) -> datetime:
        return datetime.combine(self.desde, time.min, ZONA_NEGOCIO)

    @property
    def fin(self) -> datetime:
        return datetime.combine(self.hasta + timedelta(days=1), time.min, ZONA_NEGOCIO)


@dataclass(frozen=True)
class Indicador:
    codigo: str
    nombre: str
    formula: str
    unidad: str
    calcular: Callable[[Session, Periodo], Any]


def _ciudad(stmt: Select[Any], p: Periodo, columna_familia: Any) -> Select[Any]:
    if p.ciudad is None:
        return stmt
    return stmt.join(Familia, Familia.id == columna_familia).where(Familia.ciudad == p.ciudad)


def _dinero(valor: Any) -> float:
    return float(valor or Decimal(0))


def afiliaciones(db: Session, p: Periodo) -> int:
    stmt = select(func.count(Contrato.id)).where(
        Contrato.fecha_inicio >= p.desde, Contrato.fecha_inicio <= p.hasta
    )
    return int(db.scalar(_ciudad(stmt, p, Contrato.familia_id)) or 0)


def retiros(db: Session, p: Periodo) -> int:
    stmt = select(func.count(Contrato.id)).where(
        Contrato.estado == EstadoAfiliacion.CANCELADA,
        Contrato.fecha_fin >= p.desde,
        Contrato.fecha_fin <= p.hasta,
    )
    return int(db.scalar(_ciudad(stmt, p, Contrato.familia_id)) or 0)


def _vigente_al_cierre(p: Periodo) -> Any:
    return and_(
        Contrato.fecha_inicio <= p.hasta,
        or_(Contrato.fecha_fin.is_(None), Contrato.fecha_fin > p.hasta),
        Contrato.estado.in_((*VIGENTES, EstadoAfiliacion.CANCELADA)),
    )


def vigentes(db: Session, p: Periodo) -> int:
    stmt = select(func.count(Contrato.id)).where(_vigente_al_cierre(p))
    return int(db.scalar(_ciudad(stmt, p, Contrato.familia_id)) or 0)


def recaudo(db: Session, p: Periodo) -> float:
    stmt = select(func.sum(Pago.valor)).where(
        Pago.estado == "aprobado", Pago.fecha_pago >= p.inicio, Pago.fecha_pago < p.fin
    )
    return _dinero(db.scalar(_ciudad(stmt, p, Pago.familia_id)))


def facturado(db: Session, p: Periodo) -> float:
    stmt = (
        select(func.sum(Cuota.valor))
        .join(Contrato, Contrato.id == Cuota.contrato_id)
        .where(
            Cuota.estado != EstadoCuota.ANULADA,
            Cuota.fecha_vencimiento >= p.desde,
            Cuota.fecha_vencimiento <= p.hasta,
        )
    )
    return _dinero(db.scalar(_ciudad(stmt, p, Contrato.familia_id)))


def recaudo_del_facturado(db: Session, p: Periodo) -> float | None:
    stmt = (
        select(func.sum(Cuota.valor), func.sum(Cuota.valor_pagado))
        .join(Contrato, Contrato.id == Cuota.contrato_id)
        .where(
            Cuota.estado != EstadoCuota.ANULADA,
            Cuota.fecha_vencimiento >= p.desde,
            Cuota.fecha_vencimiento <= p.hasta,
        )
    )
    total, pagado = db.execute(_ciudad(stmt, p, Contrato.familia_id)).one()
    return round(_dinero(pagado) / _dinero(total), 4) if total else None


def mora(db: Session, p: Periodo) -> dict[str, Any]:
    """Foto al cierre del periodo: contratos con alguna cuota vencida sin pagar.

    Lo abonado despues del cierre aun no estaba pagado ese dia: se devuelve al saldo, para
    que un cierre pasado no dependa de lo que se pago despues (la serie de la evolucion)."""
    abonado_despues = (
        select(func.coalesce(func.sum(AplicacionPago.valor), 0))
        .join(Pago, Pago.id == AplicacionPago.pago_id)
        .where(
            AplicacionPago.cuota_id == Cuota.id,
            func.coalesce(Pago.fecha_pago, Pago.created_at) >= p.fin,
        )
        .scalar_subquery()
    )
    saldo = Cuota.valor - Cuota.valor_pagado + abonado_despues
    vencidas = (
        select(Cuota.contrato_id, func.sum(saldo).label("saldo"))
        .where(
            Cuota.estado != EstadoCuota.ANULADA,
            Cuota.fecha_vencimiento < p.hasta,
            saldo > 0,
        )
        .group_by(Cuota.contrato_id)
        .subquery()
    )
    stmt = (
        select(func.count(vencidas.c.contrato_id), func.sum(vencidas.c.saldo))
        .select_from(vencidas)
        .join(Contrato, Contrato.id == vencidas.c.contrato_id)
        .where(_vigente_al_cierre(p))
    )
    en_mora, saldo_total = db.execute(_ciudad(stmt, p, Contrato.familia_id)).one()
    base = vigentes(db, p)
    return {
        "contratos_en_mora": int(en_mora or 0),
        "saldo_vencido": _dinero(saldo_total),
        "porcentaje": round((en_mora or 0) / base, 4) if base else None,
    }


def cumplimiento_rutas(db: Session, p: Periodo) -> dict[str, Any]:
    stmt = (
        select(
            func.count(ParadaRuta.id),
            func.sum(case((ParadaRuta.estado == "completada", 1), else_=0)),
            func.sum(
                case(
                    (
                        and_(
                            ParadaRuta.estado == "completada",
                            ParadaRuta.llegada_en
                            <= ParadaRuta.llegada_estimada + timedelta(minutes=30),
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
        )
        .join(Ruta, Ruta.id == ParadaRuta.ruta_id)
        .where(Ruta.fecha >= p.desde, Ruta.fecha <= p.hasta, Ruta.estado != "cancelada")
    )
    if p.ciudad:
        stmt = stmt.where(Ruta.ciudad == p.ciudad)
    planeadas, completadas, puntuales = db.execute(stmt).one()
    planeadas, completadas, puntuales = (
        int(planeadas or 0),
        int(completadas or 0),
        int(puntuales or 0),
    )
    return {
        "paradas_planeadas": planeadas,
        "paradas_completadas": completadas,
        "cumplimiento": round(completadas / planeadas, 4) if planeadas else None,
        "puntualidad": round(puntuales / completadas, 4) if completadas else None,
    }


def servicios_por_tipo(db: Session, p: Periodo) -> dict[str, int]:
    stmt = (
        select(Servicio.tipo_codigo, func.count(Servicio.id))
        .where(
            Servicio.estado == EstadoServicio.COMPLETADO,
            Servicio.programado_para >= p.inicio,
            Servicio.programado_para < p.fin,
        )
        .group_by(Servicio.tipo_codigo)
    )
    if p.ciudad:
        stmt = stmt.where(Servicio.ciudad == p.ciudad)
    return {tipo: int(n) for tipo, n in db.execute(stmt).tuples().all()}


def satisfaccion(db: Session, p: Periodo) -> dict[str, Any]:
    stmt = select(
        func.count(Encuesta.id),
        func.sum(case((Encuesta.estado == "respondida", 1), else_=0)),
        func.avg(Encuesta.puntaje),
    ).where(
        Encuesta.tipo == "satisfaccion",
        Encuesta.enviada_en >= p.inicio,
        Encuesta.enviada_en < p.fin,
    )
    enviadas, respondidas, promedio = db.execute(_ciudad(stmt, p, Encuesta.familia_id)).one()
    enviadas, respondidas = int(enviadas or 0), int(respondidas or 0)
    return {
        "enviadas": enviadas,
        "respondidas": respondidas,
        "promedio": round(float(promedio), 2) if promedio is not None else None,
        "tasa_respuesta": round(respondidas / enviadas, 4) if enviadas else None,
    }


INDICADORES: dict[str, Indicador] = {
    i.codigo: i
    for i in (
        Indicador(
            "afiliaciones",
            "Afiliaciones",
            "Contratos con fecha de inicio dentro del periodo.",
            "contratos",
            afiliaciones,
        ),
        Indicador(
            "retiros",
            "Retiros",
            "Contratos cancelados con fecha de fin dentro del periodo.",
            "contratos",
            retiros,
        ),
        Indicador(
            "vigentes",
            "Afiliados vigentes al cierre",
            "Contratos iniciados hasta el fin del periodo y sin fecha de fin anterior a el.",
            "contratos",
            vigentes,
        ),
        Indicador(
            "recaudo",
            "Recaudo",
            "Suma de pagos aprobados con fecha de pago dentro del periodo (cualquier medio).",
            "COP",
            recaudo,
        ),
        Indicador(
            "facturado",
            "Facturado",
            "Suma del valor de las cuotas (no anuladas) que vencen dentro del periodo.",
            "COP",
            facturado,
        ),
        Indicador(
            "recaudo_del_facturado",
            "Recaudo sobre lo facturado",
            "Valor pagado de las cuotas que vencen en el periodo / valor de esas cuotas.",
            "proporcion",
            recaudo_del_facturado,
        ),
        Indicador(
            "mora",
            "Mora al cierre",
            "Contratos vigentes con al menos una cuota vencida sin pagar al fin del periodo "
            "(lo pagado despues del cierre cuenta como pendiente ese dia); porcentaje sobre "
            "vigentes y saldo vencido total.",
            "contratos / COP",
            mora,
        ),
        Indicador(
            "cumplimiento_rutas",
            "Cumplimiento de rutas",
            "Paradas completadas / paradas planeadas en rutas no canceladas del periodo; "
            "puntualidad: completadas con llegada hasta 30 min despues de la estimada.",
            "proporcion",
            cumplimiento_rutas,
        ),
        Indicador(
            "servicios_por_tipo",
            "Servicios completados por tipo",
            "Servicios en estado completado, agendados dentro del periodo, por tipo.",
            "servicios",
            servicios_por_tipo,
        ),
        Indicador(
            "satisfaccion",
            "Satisfaccion",
            "Promedio de puntaje (1 a 5) de encuestas de satisfaccion respondidas que se "
            "enviaron en el periodo; tasa de respuesta = respondidas / enviadas.",
            "puntaje",
            satisfaccion,
        ),
    )
}


def periodo(desde: date, hasta: date, ciudad: str | None) -> Periodo:
    if hasta < desde:
        raise ReglaNegocio("El periodo termina antes de empezar")
    if (hasta - desde).days > MAX_DIAS:
        raise ReglaNegocio(f"El periodo maximo es de {MAX_DIAS} dias")
    return Periodo(desde, hasta, ciudad)


def calcular(
    db: Session,
    desde: date,
    hasta: date,
    ciudad: str | None = None,
    codigos: list[str] | None = None,
) -> dict[str, Any]:
    p = periodo(desde, hasta, ciudad)
    elegidos = codigos or list(INDICADORES)
    desconocidos = [c for c in elegidos if c not in INDICADORES]
    if desconocidos:
        raise ReglaNegocio(f"Indicadores desconocidos: {', '.join(desconocidos)}")

    def _todo() -> dict[str, Any]:
        return {c: INDICADORES[c].calcular(db, p) for c in elegidos}

    clave = f"dashboard:{desde}:{hasta}:{ciudad or '*'}:{','.join(sorted(elegidos))}"
    return {
        "periodo": {"desde": desde, "hasta": hasta, "ciudad": ciudad},
        "indicadores": cache.memorizar(clave, CACHE_SEGUNDOS, _todo),
    }


# --- Evolucion: el mismo calculo por tramos, para las series del panel ------------------------

MESES = 12


def _fin_de_mes(dia: date) -> date:
    return sumar_meses(dia.replace(day=1), 1) - timedelta(days=1)


def tramos(hasta: date) -> list[tuple[date, date]]:
    """Los 12 meses que terminan en el mes de `hasta`; el ultimo llega hasta `hasta`."""
    primero = hasta.replace(day=1)
    inicios = [sumar_meses(primero, -n) for n in range(MESES - 1, -1, -1)]
    return [(d, min(_fin_de_mes(d), hasta)) for d in inicios]


def periodo_comparable(desde: date, hasta: date) -> tuple[date, date]:
    """Con que se compara el periodo: el mismo tramo del mes (o del ano) anterior si el periodo
    empieza el primer dia de un mes (o de un ano) y no sale de el; si no, los mismos dias
    justo antes."""
    if desde == date(desde.year, 1, 1) and hasta.year == desde.year:
        return sumar_meses(desde, -12), sumar_meses(hasta, -12)
    if desde.day == 1 and (hasta.year, hasta.month) == (desde.year, desde.month):
        return sumar_meses(desde, -1), sumar_meses(hasta, -1)
    dias = (hasta - desde).days + 1
    return desde - timedelta(days=dias), desde - timedelta(days=1)


def evolucion(
    db: Session,
    desde: date,
    hasta: date,
    ciudad: str | None = None,
    codigos: list[str] | None = None,
) -> dict[str, Any]:
    """Los indicadores mes a mes durante 12 meses y en el periodo comparable. Cada tramo pasa
    por `calcular`, asi que comparte su formula y su cache. Un mes `parcial` aun no termina."""
    periodo(desde, hasta, ciudad)
    return {
        "anterior": calcular(db, *periodo_comparable(desde, hasta), ciudad, codigos),
        "meses": [
            {**calcular(db, d, h, ciudad, codigos), "parcial": h < _fin_de_mes(d)}
            for d, h in tramos(hasta)
        ],
    }


def definiciones() -> list[dict[str, str]]:
    return [
        {"codigo": i.codigo, "nombre": i.nombre, "formula": i.formula, "unidad": i.unidad}
        for i in INDICADORES.values()
    ]


def filas_planas(resultado: dict[str, Any]) -> list[tuple[str, str, Any]]:
    """(indicador, detalle, valor) para exportar a CSV o Excel."""
    filas: list[tuple[str, str, Any]] = []
    for codigo, valor in resultado["indicadores"].items():
        nombre = INDICADORES[codigo].nombre
        if isinstance(valor, dict):
            for detalle, v in valor.items():
                filas.append((nombre, detalle, v))
        else:
            filas.append((nombre, "", valor))
    return filas

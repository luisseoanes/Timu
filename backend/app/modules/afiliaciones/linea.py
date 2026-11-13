"""R2-PAN-02 La linea de cada familia (docs/hoja-de-ruta-rediseno.md).

Cuotas, preventivos y servicios en una sola secuencia por fecha, como las estaciones de una
linea de metro (contrato de direccion del panel, .impeccable/surfaces). Cada estacion esta
hecha, vencida, es la proxima o es futura.

La ventana va de seis meses atras a seis adelante. Lo vencido entra siempre, este donde este:
es lo primero que el equipo tiene que ver, y una ventana que lo escondiera mentiria. Lo
anulado y lo cancelado no entra: no es algo que haya pasado ni que vaya a pasar.

Cruza la ficha con el contrato, los preventivos y la agenda, asi que se orquesta aqui y no
en `familias`, que no conoce ningun dominio de negocio.
"""

from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date, datetime, time
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.enums import ColorPlan, EstadoEventoPreventivo, EstadoServicio, TipoPreventivo
from app.core.tiempo import ZONA_NEGOCIO, con_zona, hoy
from app.modules.afiliaciones.schemas import (
    EstacionRead,
    EstadoEstacion,
    LineaFamiliaRead,
    PlanDeFamiliaRead,
    TipoEstacion,
)
from app.modules.cartera.models import AfiliacionMascota, Contrato, Cuota, EstadoCuota
from app.modules.cartera.periodos import sumar_meses
from app.modules.catalogos.models import TipoServicioCatalogo
from app.modules.familias.models import Mascota
from app.modules.planes.models import Plan
from app.modules.preventivos.models import EventoPreventivo
from app.modules.servicios.models import Servicio

MESES_VENTANA = 6
MAX_FAMILIAS = 50


_MESES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)  # fmt: skip
_PREVENTIVOS = {
    TipoPreventivo.VACUNA: "Vacuna",
    TipoPreventivo.DESPARASITACION_INTERNA: "Desparasitación interna",
    TipoPreventivo.DESPARASITACION_EXTERNA: "Desparasitación externa",
}


@dataclass(frozen=True)
class Estacion:
    tipo: TipoEstacion
    referencia_id: UUID
    fecha: date
    estado: EstadoEstacion
    titulo: str
    mascota: str | None = None
    mascota_id: UUID | None = None


@dataclass(frozen=True)
class PlanDeFamilia:
    """Un plan vigente de la familia y los peludos que lo tienen. El color lo da el catalogo
    (manual de marca, regla 5): el panel no lo deduce del nombre."""

    plan_id: UUID
    nombre: str
    color: ColorPlan
    mascotas: tuple[str, ...]


def planes(db: Session, familias: list[UUID]) -> dict[UUID, list[PlanDeFamilia]]:
    """Los planes de los peludos afiliados hoy, por familia y en orden de nombre."""
    por_familia: dict[UUID, dict[UUID, tuple[Plan, list[str]]]] = {f: {} for f in familias}
    if not familias:
        return {}
    filas = db.execute(
        select(AfiliacionMascota.familia_id, Plan, Mascota.nombre)
        .join(Plan, AfiliacionMascota.plan_id == Plan.id)
        .join(Mascota, AfiliacionMascota.mascota_id == Mascota.id)
        .where(AfiliacionMascota.familia_id.in_(familias), AfiliacionMascota.activa.is_(True))
        .order_by(Mascota.nombre)
    )
    for familia_id, plan, mascota in filas:
        por_familia[familia_id].setdefault(plan.id, (plan, []))[1].append(mascota)
    return {
        f: sorted(
            (PlanDeFamilia(p.id, p.nombre, p.color, tuple(m)) for p, m in planes_.values()),
            key=lambda x: x.nombre,
        )
        for f, planes_ in por_familia.items()
    }


def _ventana(dia: date) -> tuple[date, date]:
    return sumar_meses(dia, -MESES_VENTANA), sumar_meses(dia, MESES_VENTANA)


def _estado(hecha: bool, fecha: date, dia: date) -> EstadoEstacion:
    if hecha:
        return "hecha"
    return "vencida" if fecha < dia else "futura"


def _cuotas(db: Session, familias: list[UUID], dia: date) -> list[tuple[UUID, Estacion]]:
    desde, hasta = _ventana(dia)
    abiertas = Cuota.estado.in_(list(EstadoCuota.ABIERTAS))
    filas = db.execute(
        select(Cuota, Contrato.familia_id)
        .join(Contrato, Cuota.contrato_id == Contrato.id)
        .where(
            Contrato.familia_id.in_(familias),
            Cuota.estado != EstadoCuota.ANULADA,
            or_(
                Cuota.fecha_vencimiento.between(desde, hasta),
                and_(abiertas, Cuota.fecha_vencimiento < dia),
            ),
        )
    )
    resultado = []
    for cuota, familia_id in filas:
        anio, mes = (int(p) for p in cuota.periodo.split("-"))
        titulo = (
            f"Cuota de {_MESES[mes - 1]}" + ("" if anio == dia.year else f" de {anio}")
            if cuota.tipo == "cuota"
            else "Ajuste de plan"
        )
        estacion = Estacion(
            tipo="cuota",
            referencia_id=cuota.id,
            fecha=cuota.fecha_vencimiento,
            estado=_estado(cuota.estado == EstadoCuota.PAGADA, cuota.fecha_vencimiento, dia),
            titulo=titulo,
        )
        resultado.append((familia_id, estacion))
    return resultado


def _preventivos(db: Session, familias: list[UUID], dia: date) -> list[tuple[UUID, Estacion]]:
    desde, hasta = _ventana(dia)
    aplicado = EventoPreventivo.estado == EstadoEventoPreventivo.APLICADO
    programado = EventoPreventivo.estado == EstadoEventoPreventivo.PROGRAMADO
    filas = db.execute(
        select(EventoPreventivo, Mascota.familia_id, Mascota.nombre)
        .join(Mascota, EventoPreventivo.mascota_id == Mascota.id)
        .where(
            Mascota.familia_id.in_(familias),
            or_(
                and_(aplicado, EventoPreventivo.fecha_aplicacion.between(desde, hasta)),
                and_(
                    programado,
                    or_(
                        EventoPreventivo.fecha_programada.between(desde, hasta),
                        EventoPreventivo.fecha_programada < dia,
                    ),
                ),
            ),
        )
    )
    resultado = []
    for evento, familia_id, mascota in filas:
        hecha = evento.estado == EstadoEventoPreventivo.APLICADO
        fecha = (
            evento.fecha_aplicacion
            if hecha and evento.fecha_aplicacion
            else evento.fecha_programada
        )
        estacion = Estacion(
            tipo="preventivo",
            referencia_id=evento.id,
            fecha=fecha,
            estado=_estado(hecha, fecha, dia),
            titulo=_PREVENTIVOS.get(TipoPreventivo(evento.tipo), "Preventivo"),
            mascota=mascota,
            mascota_id=evento.mascota_id,
        )
        resultado.append((familia_id, estacion))
    return resultado


def _servicios(db: Session, familias: list[UUID], dia: date) -> list[tuple[UUID, Estacion]]:
    desde, hasta = _ventana(dia)
    inicio = datetime.combine(desde, time.min, ZONA_NEGOCIO)
    fin = datetime.combine(hasta, time.max, ZONA_NEGOCIO)
    hoy_inicio = datetime.combine(dia, time.min, ZONA_NEGOCIO)
    filas = db.execute(
        select(Servicio, TipoServicioCatalogo.nombre, Mascota.nombre)
        .join(TipoServicioCatalogo, Servicio.tipo_codigo == TipoServicioCatalogo.codigo)
        .outerjoin(Mascota, Servicio.mascota_id == Mascota.id)
        .where(
            Servicio.familia_id.in_(familias),
            Servicio.estado != EstadoServicio.CANCELADO,
            or_(
                Servicio.programado_para.between(inicio, fin),
                and_(
                    Servicio.estado != EstadoServicio.COMPLETADO,
                    Servicio.programado_para < hoy_inicio,
                ),
            ),
        )
    )
    resultado = []
    for servicio, tipo, mascota in filas:
        assert servicio.programado_para is not None  # el filtro de fechas excluye los NULL
        fecha = con_zona(servicio.programado_para).astimezone(ZONA_NEGOCIO).date()
        estacion = Estacion(
            tipo="servicio",
            referencia_id=servicio.id,
            fecha=fecha,
            estado=_estado(servicio.estado == EstadoServicio.COMPLETADO, fecha, dia),
            titulo=tipo,
            mascota=mascota,
            mascota_id=servicio.mascota_id,
        )
        resultado.append((servicio.familia_id, estacion))
    return resultado


def lineas(
    db: Session, familias: list[UUID], dia: date | None = None
) -> dict[UUID, list[Estacion]]:
    """La linea de cada familia, en orden de fecha. La primera estacion pendiente desde hoy es
    la proxima. Una familia sin nada en la ventana tiene la linea vacia."""
    dia = dia or hoy()
    por_familia: dict[UUID, list[Estacion]] = {f: [] for f in familias}
    if not familias:
        return por_familia
    for familia_id, estacion in [
        *_cuotas(db, familias, dia),
        *_preventivos(db, familias, dia),
        *_servicios(db, familias, dia),
    ]:
        por_familia[familia_id].append(estacion)
    resultado: dict[UUID, list[Estacion]] = defaultdict(list)
    for familia_id, estaciones in por_familia.items():
        orden = sorted(estaciones, key=lambda e: (e.fecha, e.tipo, e.titulo))
        proxima = next((i for i, e in enumerate(orden) if e.estado == "futura"), None)
        if proxima is not None:
            e = orden[proxima]
            orden[proxima] = replace(e, estado="proxima")
        resultado[familia_id] = orden
    return dict(resultado)


def leer(db: Session, familias: list[UUID]) -> list[LineaFamiliaRead]:
    """La linea y los planes de cada familia, como los leen el panel y el portal."""
    por_familia = lineas(db, familias)
    de_cada = planes(db, familias)
    return [
        LineaFamiliaRead(
            familia_id=f,
            planes=[PlanDeFamiliaRead.model_validate(p) for p in de_cada.get(f, [])],
            estaciones=[EstacionRead.model_validate(e) for e in estaciones],
        )
        for f, estaciones in por_familia.items()
    ]

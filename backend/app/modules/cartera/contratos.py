"""6.2 / 6.3 / 6.23 Vida del contrato: vigencia, peludos con su plan, valor y cambio de plan.

Opera sobre `Contrato`, `AfiliacionMascota`, `Cuota` y `CambioPlan`. El precio sale siempre
de `planes.cotizar`: cada peludo paga la tarifa de su plan para el numero de peludos del
contrato. El catalogo (planes, tarifas, beneficios, recomendacion) sigue en `planes`, que no
conoce los contratos.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import MESES_PERIODICIDAD, EstadoAfiliacion
from app.core.errores import ReglaNegocio
from app.core.tiempo import ahora, hoy
from app.modules.cartera.models import AfiliacionMascota, Contrato, Cuota, EstadoCuota
from app.modules.cartera.periodos import dinero, periodo, sumar_meses
from app.modules.familias.models import Familia, Mascota
from app.modules.planes import service as planes
from app.modules.planes.models import CambioPlan, Plan
from app.modules.planes.service import Cotizacion
from app.modules.reglas import service as reglas

VIGENTES = (EstadoAfiliacion.ACTIVA, EstadoAfiliacion.EN_MORA, EstadoAfiliacion.CONGELADA)


def contrato_vigente(db: Session, familia_id: UUID) -> Contrato | None:
    return db.scalar(
        select(Contrato).where(Contrato.familia_id == familia_id, Contrato.estado.in_(VIGENTES))
    )


def lineas(db: Session, contrato: Contrato) -> list[AfiliacionMascota]:
    """Los peludos vigentes del contrato, en el orden en que entraron. Se consulta siempre:
    la relacion `Contrato.mascotas` puede estar cargada de antes de un cambio."""
    return list(
        db.scalars(
            select(AfiliacionMascota)
            .where(AfiliacionMascota.contrato_id == contrato.id, AfiliacionMascota.activa.is_(True))
            .order_by(AfiliacionMascota.created_at, AfiliacionMascota.id)
        )
    )


def planes_del_contrato(db: Session, contrato: Contrato) -> set[UUID]:
    """Los planes de sus peludos vigentes: las reglas de un plan aplican al contrato."""
    return {v.plan_id for v in lineas(db, contrato)}


def plan_de_mascota(db: Session, mascota_id: UUID) -> Plan | None:
    """El plan con el que esta afiliado hoy un peludo; ninguno si no esta en un contrato."""
    plan_id = db.scalar(
        select(AfiliacionMascota.plan_id).where(
            AfiliacionMascota.mascota_id == mascota_id, AfiliacionMascota.activa.is_(True)
        )
    )
    return planes.obtener(db, plan_id) if plan_id else None


def _especies(db: Session, mascota_ids: list[UUID]) -> dict[UUID, str]:
    filas = db.execute(select(Mascota.id, Mascota.especie).where(Mascota.id.in_(mascota_ids)))
    return dict(filas.tuples().all())


def _cotizar(
    db: Session,
    contrato: Contrato,
    peludos: list[tuple[UUID, UUID]],
    validar: set[int],
) -> Cotizacion:
    """Cotiza el contrato con `peludos` (mascota, plan) en su periodicidad."""
    familia = db.get(Familia, contrato.familia_id)
    assert familia is not None
    especies = _especies(db, [m for m, _ in peludos])
    return planes.cotizar(
        db,
        familia.ciudad,
        [(especies[m], p) for m, p in peludos],
        contrato.periodicidad,
        validar=validar,
    )


def _aplicar(contrato: Contrato, vigentes: list[AfiliacionMascota], cot: Cotizacion) -> None:
    for linea, cotizado in zip(vigentes, cot.peludos, strict=True):
        linea.plan_id = cotizado.plan.id
        linea.valor_mensual = dinero(cotizado.valor_mensual)
    contrato.valor_mensual = dinero(cot.valor_mensual)
    contrato.valor_periodo = dinero(cot.valor_periodo)


# --- Alta del contrato ------------------------------------------------------------------------


@dataclass
class Afiliacion:
    """Peludos de la familia con su plan, cotizados: lo que se firma al crear el contrato."""

    mascotas: list[Mascota]
    planes: list[UUID]
    cotizacion: Cotizacion


def cotizar_afiliacion(
    db: Session, familia: Familia, planes_por_mascota: dict[UUID, UUID], periodicidad: str
) -> Afiliacion:
    """Todos los peludos activos de la familia entran al contrato, cada uno con su plan: la
    tarifa depende de cuantos son, asi que ninguno puede quedar fuera."""
    activas = list(
        db.scalars(
            select(Mascota)
            .where(Mascota.familia_id == familia.id, Mascota.activa.is_(True))
            .order_by(Mascota.created_at, Mascota.id)
        )
    )
    if not activas:
        raise ReglaNegocio("La familia necesita al menos una mascota activa para afiliarse")
    faltan = [m.nombre for m in activas if m.id not in planes_por_mascota]
    if faltan:
        raise ReglaNegocio(f"Elige el plan de: {', '.join(faltan)}")
    ajenas = set(planes_por_mascota) - {m.id for m in activas}
    if ajenas:
        raise ReglaNegocio("Hay mascotas que no son peludos activos de la familia")
    elegidos = [planes_por_mascota[m.id] for m in activas]
    cot = planes.cotizar(
        db,
        familia.ciudad,
        [(m.especie, p) for m, p in zip(activas, elegidos, strict=True)],
        periodicidad,
    )
    return Afiliacion(activas, elegidos, cot)


def afiliar(db: Session, contrato: Contrato, afiliacion: Afiliacion) -> None:
    """Crea la linea de cada peludo del contrato recien creado y fija sus valores."""
    nuevas = [
        AfiliacionMascota(
            familia_id=contrato.familia_id,
            contrato_id=contrato.id,
            mascota_id=m.id,
            plan_id=plan_id,
            valor_mensual=dinero(0),
        )
        for m, plan_id in zip(afiliacion.mascotas, afiliacion.planes, strict=True)
    ]
    db.add_all(nuevas)
    _aplicar(contrato, nuevas, afiliacion.cotizacion)
    db.flush()


# --- Alta y retiro de un peludo (6.3) ---------------------------------------------------------


def _recalcular(
    db: Session,
    contrato: Contrato,
    vigentes: list[AfiliacionMascota],
    *,
    tipo: str,
    mascota_id: UUID,
    validar: set[int],
    usuario_id: UUID | None,
    plan_anterior_id: UUID | None = None,
    plan_nuevo_id: UUID | None = None,
) -> CambioPlan | None:
    """Recalcula el contrato con `vigentes`. El nuevo valor aplica desde la siguiente cuota:
    las ya emitidas no cambian. Si cambia, queda el registro en cambios_plan."""
    anterior = dinero(contrato.valor_periodo)
    cot = _cotizar(db, contrato, [(v.mascota_id, v.plan_id) for v in vigentes], validar)
    _aplicar(contrato, vigentes, cot)
    db.flush()
    if dinero(contrato.valor_periodo) == anterior:
        return None
    cambio = CambioPlan(
        contrato_id=contrato.id,
        mascota_id=mascota_id,
        tipo=tipo,
        plan_anterior_id=plan_anterior_id,
        plan_nuevo_id=plan_nuevo_id,
        valor_anterior=anterior,
        valor_nuevo=contrato.valor_periodo,
        modo="proxima_cuota",
        fecha_efectiva=hoy(),
        registrado_por_id=usuario_id,
    )
    db.add(cambio)
    db.flush()
    return cambio


def validar_alta(db: Session, contrato: Contrato, especie: str, plan_id: UUID) -> None:
    """Antes de guardar la mascota nueva: su plan se vende en la ciudad, cubre su especie y
    la familia no pasa del maximo de peludos. Un rechazo no deja nada escrito."""
    familia = db.get(Familia, contrato.familia_id)
    assert familia is not None
    actuales = lineas(db, contrato)
    especies = _especies(db, [v.mascota_id for v in actuales])
    planes.cotizar(
        db,
        familia.ciudad,
        [(especies[v.mascota_id], v.plan_id) for v in actuales] + [(especie, plan_id)],
        contrato.periodicidad,
        validar={len(actuales)},
    )


def agregar_mascota(
    db: Session, contrato: Contrato, mascota: Mascota, plan_id: UUID, usuario_id: UUID | None
) -> CambioPlan | None:
    """F1-FAM-02 / 6.3 Un peludo mas: entra con su plan y todos pasan a la tarifa del nuevo
    numero de peludos desde la siguiente cuota."""
    linea = AfiliacionMascota(
        familia_id=contrato.familia_id,
        contrato_id=contrato.id,
        mascota_id=mascota.id,
        plan_id=plan_id,
        valor_mensual=dinero(0),
    )
    db.add(linea)
    db.flush()
    vigentes = lineas(db, contrato)
    return _recalcular(
        db,
        contrato,
        vigentes,
        tipo="mascota_alta",
        mascota_id=mascota.id,
        validar={vigentes.index(linea)},
        usuario_id=usuario_id,
        plan_nuevo_id=plan_id,
    )


def retirar_mascota(
    db: Session, contrato: Contrato, mascota_id: UUID, usuario_id: UUID | None
) -> CambioPlan | None:
    """6.3 El peludo sale del contrato y los demas pasan a la tarifa del nuevo numero de
    peludos desde la siguiente cuota (si eran 4 y sale 1, pagan la de 3)."""
    vigentes = lineas(db, contrato)
    linea = next((v for v in vigentes if v.mascota_id == mascota_id), None)
    if linea is None:
        return None
    if len(vigentes) == 1:
        raise ReglaNegocio(
            "Es el unico peludo de la afiliacion: para retirarlo hay que cancelar el contrato"
        )
    linea.activa = False
    linea.dada_de_baja_en = ahora()
    vigentes.remove(linea)
    return _recalcular(
        db,
        contrato,
        vigentes,
        tipo="mascota_baja",
        mascota_id=mascota_id,
        validar=set(),
        usuario_id=usuario_id,
        plan_anterior_id=linea.plan_id,
    )


# --- F1-PLA-02 Cambio de plan de un peludo ----------------------------------------------------


def ciclo_actual(contrato: Contrato, dia: date) -> tuple[date, date]:
    """Inicio y fin del periodo de cobro que contiene `dia`: de corte a corte, con los meses
    de la periodicidad del contrato."""
    meses = MESES_PERIODICIDAD[contrato.periodicidad]
    inicio = date(contrato.fecha_inicio.year, contrato.fecha_inicio.month, contrato.dia_corte)
    while sumar_meses(inicio, meses) <= dia:
        inicio = sumar_meses(inicio, meses)
    return inicio, sumar_meses(inicio, meses)


def _cargar_ajuste(db: Session, contrato: Contrato, valor: Decimal, dia: date) -> Cuota:
    per = periodo(dia)
    existentes = list(
        db.scalars(
            select(Cuota).where(
                Cuota.contrato_id == contrato.id,
                Cuota.periodo == per,
                Cuota.tipo.like("ajuste%"),
            )
        )
    )
    abierta = next((c for c in existentes if c.estado in EstadoCuota.ABIERTAS), None)
    if abierta:
        abierta.valor = dinero(abierta.valor) + valor
        return abierta
    cuota = Cuota(
        contrato_id=contrato.id,
        periodo=per,
        tipo="ajuste" if not existentes else f"ajuste{len(existentes) + 1}",
        fecha_vencimiento=dia,
        valor=valor,
        descripcion="Ajuste por cambio de plan",
    )
    db.add(cuota)
    return cuota


def cambiar_plan(
    db: Session, contrato: Contrato, mascota_id: UUID, plan_nuevo: Plan, usuario_id: UUID | None
) -> CambioPlan:
    """El peludo pasa a otro plan. Como se cobra lo decide la regla `plan.cambio`: con
    prorrateo diario del periodo en curso, al empezar el siguiente periodo, o rechazado."""
    vigentes = lineas(db, contrato)
    linea = next((v for v in vigentes if v.mascota_id == mascota_id), None)
    if linea is None:
        raise ReglaNegocio("La mascota no esta afiliada en este contrato")
    if linea.plan_id == plan_nuevo.id:
        raise ReglaNegocio("La mascota ya tiene ese plan")
    familia = db.get(Familia, contrato.familia_id)
    assert familia is not None
    plan_anterior = planes.obtener(db, linea.plan_id)
    posicion = vigentes.index(linea)
    peludos = [(v.mascota_id, v.plan_id) for v in vigentes]
    peludos[posicion] = (mascota_id, plan_nuevo.id)
    cot = _cotizar(db, contrato, peludos, {posicion})

    anterior = dinero(contrato.valor_periodo)
    nuevo = dinero(cot.valor_periodo)
    contexto = {
        "familia": {"ciudad": familia.ciudad, "estado": familia.estado},
        "plan_anterior": {"codigo": plan_anterior.codigo, "valor": float(linea.valor_mensual)},
        "plan_nuevo": {
            "codigo": plan_nuevo.codigo,
            "valor": float(cot.peludos[posicion].valor_mensual),
        },
        "sube": nuevo > anterior,
    }
    resultado = reglas.primera(db, "plan.cambio", contexto, plan_id=plan_nuevo.id)
    if resultado is None:
        raise ReglaNegocio("No hay una regla que defina como cobrar el cambio de plan")
    if resultado.accion["tipo"] == "rechazar":
        raise ReglaNegocio(resultado.accion["motivo"])
    modo = resultado.accion["modo"]

    dia = hoy()
    inicio, fin = ciclo_actual(contrato, dia)
    ajuste = dinero(0)
    fecha_efectiva = dia
    if modo == "diario":
        ajuste = dinero((nuevo - anterior) * (fin - dia).days / (fin - inicio).days)
    elif modo == "proximo_ciclo":
        fecha_efectiva = fin

    cambio = CambioPlan(
        contrato_id=contrato.id,
        mascota_id=mascota_id,
        tipo="cambio_plan",
        plan_anterior_id=plan_anterior.id,
        plan_nuevo_id=plan_nuevo.id,
        valor_anterior=anterior,
        valor_nuevo=nuevo,
        ajuste=ajuste,
        modo=modo,
        regla_codigo=resultado.regla,
        fecha_efectiva=fecha_efectiva,
        aplicado=modo != "proximo_ciclo",
        registrado_por_id=usuario_id,
    )
    db.add(cambio)
    if cambio.aplicado:
        _aplicar(contrato, vigentes, cot)
        if ajuste > 0:
            _cargar_ajuste(db, contrato, ajuste, dia)
        elif ajuste < 0:
            contrato.saldo_a_favor = dinero(contrato.saldo_a_favor) - ajuste
    db.flush()
    return cambio


def aplicar_cambios_programados(db: Session, contrato: Contrato, hasta: date) -> None:
    """Cambios `proximo_ciclo` cuya fecha llego: se aplican antes de emitir la cuota, con la
    tarifa vigente en ese momento."""
    pendientes = db.scalars(
        select(CambioPlan)
        .where(
            CambioPlan.contrato_id == contrato.id,
            CambioPlan.aplicado.is_(False),
            CambioPlan.fecha_efectiva <= hasta,
        )
        .order_by(CambioPlan.created_at)
    )
    for cambio in pendientes:
        assert cambio.plan_nuevo_id is not None
        vigentes = lineas(db, contrato)
        linea = next((v for v in vigentes if v.mascota_id == cambio.mascota_id), None)
        if linea is not None:
            linea.plan_id = cambio.plan_nuevo_id
            cot = _cotizar(db, contrato, [(v.mascota_id, v.plan_id) for v in vigentes], set())
            _aplicar(contrato, vigentes, cot)
        cambio.aplicado = True
    db.flush()

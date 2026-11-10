"""6.1 Agregar un peludo desde el portal, con el contrato vigente.

1. `cotizar`: el contrato con el peludo nuevo a la tarifa del nuevo numero de peludos, y lo
   que cuesta lo que queda del periodo en curso con esa tarifa (prorrateo por dias, como el
   cambio de plan inmediato), mas la diferencia de las cuotas siguientes que ya se emitieron
   con el valor anterior (se emiten unos dias antes de vencer).
2. `iniciar`: guarda la ficha y el plan elegido y crea el pago por esa diferencia. La familia
   lo paga en la pasarela.
3. `completar` (pago aprobado): el peludo entra a la ficha y al contrato con su plan, el
   contrato cobra el valor nuevo desde la siguiente cuota y lo pagado cubre la cuota de
   ajuste del periodo en curso.
4. `cerrar_sin_pago` (beat): a las 48 horas sin pago, el alta se cancela.

Decision de TIMU pendiente: no hay periodo de carencia para el peludo nuevo; con el contrato
en mora o congelado no se agrega (docs/backlog.md, pendientes del 6.1).
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import nuevo_id
from app.core.enums import EstadoAfiliacion, EstadoAltaPeludo, EstadoPago
from app.core.errores import ReglaNegocio
from app.core.tiempo import ahora, hoy
from app.integrations.payments import construir_link_pago
from app.modules.afiliaciones import ciclo
from app.modules.afiliaciones.models import AltaPeludo
from app.modules.cartera import contratos, pasarela
from app.modules.cartera import service as cartera
from app.modules.cartera.models import Contrato, Pago
from app.modules.cartera.periodos import centavos, dinero
from app.modules.familias.models import Familia
from app.modules.familias.schemas import MascotaAlta
from app.modules.tareas import service as tareas

PREFIJO = "ALT-"
VIGENCIA_ENLACE = timedelta(hours=24)
CERRAR_SIN_PAGO = timedelta(hours=48)


@dataclass
class Cotizacion:
    periodicidad: str
    valor_periodo_actual: Decimal
    valor_periodo_nuevo: Decimal
    valor_ajuste: Decimal
    hasta: date  # fin del periodo en curso: desde ahi cobra el valor nuevo
    # Cuotas de periodos siguientes que ya se emitieron con el valor anterior: el ajuste
    # tambien cubre su diferencia.
    cuotas_adelantadas: int


def contrato_para_alta(db: Session, familia: Familia) -> Contrato:
    contrato = contratos.contrato_vigente(db, familia.id)
    if contrato is None:
        raise ReglaNegocio("No tienes una afiliacion vigente: afilia a tu peludo desde el inicio")
    if contrato.estado == EstadoAfiliacion.EN_MORA:
        raise ReglaNegocio(
            "Tu afiliacion tiene pagos pendientes: ponte al dia para agregar un peludo"
        )
    if contrato.estado != EstadoAfiliacion.ACTIVA:
        raise ReglaNegocio("Tu afiliacion no esta activa: escribenos para agregar un peludo")
    return contrato


def cotizar(db: Session, familia: Familia, especie: str, plan_id: UUID) -> Cotizacion:
    contrato = contrato_para_alta(db, familia)
    cot = contratos.cotizar_alta(db, contrato, especie, plan_id)
    actual = dinero(contrato.valor_periodo)
    nuevo = dinero(cot.valor_periodo)
    dia = hoy()
    hasta = contratos.ciclo_actual(contrato, dia)[1]
    adelantadas = contratos.cuotas_emitidas_desde(db, contrato, hasta)
    return Cotizacion(
        periodicidad=contrato.periodicidad,
        valor_periodo_actual=actual,
        valor_periodo_nuevo=nuevo,
        valor_ajuste=contratos.prorrateo(contrato, nuevo - actual, dia)
        + (nuevo - actual) * adelantadas,
        hasta=hasta,
        cuotas_adelantadas=adelantadas,
    )


def iniciar(
    db: Session, familia: Familia, datos: MascotaAlta, plan_id: UUID
) -> tuple[AltaPeludo, str]:
    """Devuelve el alta y el enlace de pago. Un alta anterior con el pago rechazado se cancela;
    una que aun espera la pasarela impide otra, para no cobrar dos veces."""
    nombre = datos.nombre.strip()
    db.refresh(familia, ["mascotas"])
    if any(m.activa and m.nombre.strip().casefold() == nombre.casefold() for m in familia.mascotas):
        raise ReglaNegocio(f"Ya tienes un peludo llamado {nombre}: usa otro nombre")
    for anterior in pendientes(db, familia.id):
        pago_anterior = db.get(Pago, anterior.pago_id)
        if pago_anterior is not None and pago_anterior.estado == EstadoPago.RECHAZADO:
            anterior.estado = EstadoAltaPeludo.CANCELADA
            continue
        raise ReglaNegocio(
            f"Ya hay un pago en curso para agregar a {anterior.nombre}: espera a que se confirme"
        )
    cot = cotizar(db, familia, datos.especie, plan_id)
    if cot.valor_ajuste <= 0:
        raise ReglaNegocio("No pudimos calcular el valor: escribenos para agregar tu peludo")
    contrato = contrato_para_alta(db, familia)
    pago = Pago(
        id=nuevo_id(),
        familia_id=familia.id,
        contrato_id=contrato.id,
        referencia_externa=f"{PREFIJO}{uuid4().hex[:20].upper()}",
        proveedor="wompi",
        valor=cot.valor_ajuste,
        estado=EstadoPago.PENDIENTE,
    )
    db.add(pago)
    db.flush()
    alta = AltaPeludo(
        familia_id=familia.id,
        contrato_id=contrato.id,
        plan_id=plan_id,
        nombre=nombre,
        especie=datos.especie,
        ficha=datos.model_dump(mode="json", exclude={"nombre", "especie"}),
        valor_ajuste=cot.valor_ajuste,
        valor_periodo_nuevo=cot.valor_periodo_nuevo,
        referencia_pago=pago.referencia_externa,
        pago_id=pago.id,
    )
    db.add(alta)
    db.flush()
    enlace = construir_link_pago(
        pago.referencia_externa,
        centavos(pago.valor),
        familia.email,
        redireccion=f"{settings.FRONTEND_URL}/portal/mascotas/nueva",
        vence=ahora() + VIGENCIA_ENLACE,
    )
    return alta, enlace


def pendientes(db: Session, familia_id: UUID) -> list[AltaPeludo]:
    return list(
        db.scalars(
            select(AltaPeludo).where(
                AltaPeludo.familia_id == familia_id,
                AltaPeludo.estado == EstadoAltaPeludo.PENDIENTE_PAGO,
            )
        )
    )


def listar(db: Session, familia_id: UUID) -> list[tuple[AltaPeludo, str | None]]:
    """Las altas de la familia, la mas reciente primero, con el estado de su pago."""
    filas = db.execute(
        select(AltaPeludo, Pago.estado)
        .join(Pago, Pago.id == AltaPeludo.pago_id)
        .where(AltaPeludo.familia_id == familia_id)
        .order_by(AltaPeludo.created_at.desc())
        .limit(20)
    )
    return list(filas.tuples())


@pasarela.al_aprobar(PREFIJO)
def completar(db: Session, pago: Pago) -> None:
    """Pago aprobado de un alta. Con el contexto en `sistema`, como cualquier evento de la
    pasarela."""
    alta = db.scalar(
        select(AltaPeludo).where(AltaPeludo.referencia_pago == pago.referencia_externa)
    )
    if alta is None:
        raise ReglaNegocio(f"No hay un alta de peludo para {pago.referencia_externa}")
    if alta.estado == EstadoAltaPeludo.COMPLETADA:
        return
    if alta.estado != EstadoAltaPeludo.PENDIENTE_PAGO:
        _al_equipo(db, alta, "El pago llego despues de cerrar el alta")
        return
    familia = db.get(Familia, alta.familia_id)
    assert familia is not None
    contrato = contratos.contrato_vigente(db, familia.id)
    if contrato is None or contrato.id != alta.contrato_id:
        _a_error(db, alta, "El contrato con que se cotizo ya no esta vigente")
        return
    try:
        with db.begin_nested():
            mascota = ciclo.agregar_mascota(
                db,
                familia,
                MascotaAlta(nombre=alta.nombre, especie=alta.especie, **alta.ficha),
                plan_id=alta.plan_id,
            )
    except ReglaNegocio as e:
        _a_error(db, alta, str(e))
        return
    # Lo pagado es la parte del periodo en curso con la tarifa nueva: su propia cuota, para
    # que no abone otra deuda.
    cuota = contratos.cargar_ajuste(
        db, contrato, dinero(pago.valor), hoy(), descripcion=f"Alta de {alta.nombre}"
    )
    pago.contrato_id = contrato.id
    pago.cuota_id = cuota.id
    cartera.aplicar_pago(db, pago)
    alta.mascota_id = mascota.id
    alta.estado = EstadoAltaPeludo.COMPLETADA
    db.flush()


def _a_error(db: Session, alta: AltaPeludo, motivo: str) -> None:
    alta.estado = EstadoAltaPeludo.ERROR
    alta.error = motivo
    _al_equipo(db, alta, motivo)


def _al_equipo(db: Session, alta: AltaPeludo, motivo: str) -> Any:
    db.flush()
    return tareas.crear(
        db,
        titulo="Pago de un peludo nuevo que requiere revision",
        descripcion=(
            f"Referencia {alta.referencia_pago} ({alta.nombre}): {motivo}. Afiliarlo a mano o "
            "devolver el pago."
        ),
        area="comercial",
        prioridad="alta",
        vence_en_dias=1,
        familia_id=alta.familia_id,
        origen="afiliacion",
        clave=f"alta_peludo_revision:{alta.id}",
    )


def cerrar_sin_pago(db: Session) -> int:
    """Altas sin pagar a las 48 horas: se cancelan y su pago pendiente se anula. El enlace
    vencio a las 24; un aprobado tardio deja una tarea (`completar`)."""
    limite = ahora() - CERRAR_SIN_PAGO
    vencidas = list(
        db.scalars(
            select(AltaPeludo).where(
                AltaPeludo.estado == EstadoAltaPeludo.PENDIENTE_PAGO,
                AltaPeludo.created_at <= limite,
            )
        )
    )
    canceladas = 0
    for alta in vencidas:
        with db.begin_nested():
            pago = db.get(Pago, alta.pago_id)
            assert pago is not None
            if pago.estado == EstadoPago.APROBADO:
                continue
            if pago.estado == EstadoPago.PENDIENTE:
                pago.estado = EstadoPago.ANULADO
            alta.estado = EstadoAltaPeludo.CANCELADA
            canceladas += 1
    db.flush()
    return canceladas

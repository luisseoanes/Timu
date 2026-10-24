"""6.2 / 6.4 / 6.23 Cartera: contrato, cuotas, estados, avisos, pagos y renovacion."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import partial
from typing import Any, TypeVar
from uuid import UUID, uuid4

import structlog
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import EstadoAfiliacion
from app.core.errores import Conflicto, NoEncontrado, ReglaNegocio
from app.core.tiempo import ahora, hoy
from app.modules.cartera.models import (
    AplicacionPago,
    AvisoCartera,
    Contrato,
    Cuota,
    EstadoCuota,
    MedioPagoRecurrente,
    Pago,
)
from app.modules.cartera.periodos import (
    dinero,
    formato_cop,
    periodo,
    siguiente_periodo,
    sumar_meses,
    vencimiento,
)
from app.modules.familias.models import Familia, Mascota
from app.modules.planes import service as planes
from app.modules.planes.models import Plan
from app.modules.reglas import service as reglas

logger = structlog.get_logger(__name__)

T = TypeVar("T")

GENERAN_CUOTAS = (EstadoAfiliacion.ACTIVA, EstadoAfiliacion.EN_MORA)


# --- F1-CAR-01 Contrato -----------------------------------------------------------------------


def _numero(db: Session, dia: date) -> str:
    prefijo = f"C{dia:%Y}-"
    total = db.scalar(select(func.count()).where(Contrato.numero.like(f"{prefijo}%")))
    return f"{prefijo}{(total or 0) + 1:05d}"


def crear_contrato(
    db: Session,
    familia: Familia,
    plan: Plan,
    *,
    fecha_inicio: date | None = None,
    primera_cuota: bool = True,
) -> tuple[Contrato, Cuota | None]:
    """Crea el contrato vigente de la familia, con corte, renovacion y primera cuota.

    El dia de corte es el dia de inicio (hasta el 28, para que exista en todo mes) y la
    renovacion es un ano despues del inicio.
    """
    if planes.contrato_vigente(db, familia.id):
        raise Conflicto("La familia ya tiene un contrato vigente")
    if familia.dada_de_baja_en is not None:
        raise ReglaNegocio("La familia esta dada de baja")
    inicio = fecha_inicio or hoy()
    activas = list(
        db.scalars(
            select(Mascota).where(Mascota.familia_id == familia.id, Mascota.activa.is_(True))
        )
    )
    if not activas:
        raise ReglaNegocio("La familia necesita al menos una mascota activa para afiliarse")
    planes.validar_para_familia(plan, familia.ciudad, [m.especie for m in activas])
    adicionales, valor_adicional, _ = planes.calcular_cupo(db, familia, plan, len(activas))

    contrato = Contrato(
        id=uuid4(),
        numero=_numero(db, inicio),
        familia_id=familia.id,
        plan_id=plan.id,
        fecha_inicio=inicio,
        fecha_renovacion=sumar_meses(inicio, 12),
        dia_corte=min(inicio.day, 28),
        valor_plan=dinero(plan.valor_mensual),
        mascotas_adicionales=adicionales,
        valor_adicional_mascota=valor_adicional if adicionales else dinero(0),
        estado=EstadoAfiliacion.ACTIVA,
        saldo_a_favor=dinero(0),
    )
    contrato.valor_mensual = planes.valor_mensual(contrato)
    db.add(contrato)
    db.flush()
    cuota = _emitir(db, contrato, periodo(inicio)) if primera_cuota else None
    _sincronizar_familia(db, contrato)
    return contrato, cuota


def _emitir(db: Session, contrato: Contrato, per: str) -> Cuota | None:
    existe = db.scalar(
        select(Cuota.id).where(
            Cuota.contrato_id == contrato.id, Cuota.periodo == per, Cuota.tipo == "mensual"
        )
    )
    if existe:
        return None
    valor = dinero(contrato.valor_mensual)
    cuota = Cuota(
        contrato_id=contrato.id,
        periodo=per,
        tipo="mensual",
        fecha_vencimiento=vencimiento(per, contrato.dia_corte),
        valor=valor,
        valor_pagado=dinero(0),
        estado=EstadoCuota.PENDIENTE,
        descripcion=f"Cuota {per}",
    )
    db.add(cuota)
    db.flush()
    # El saldo a favor (creditos por cambio de plan, pagos de mas) se consume primero.
    saldo = dinero(contrato.saldo_a_favor)
    if saldo > 0:
        usado = min(saldo, valor)
        contrato.saldo_a_favor = saldo - usado
        _abonar(cuota, usado)
    return cuota


def _abonar(cuota: Cuota, valor: Decimal) -> None:
    cuota.valor_pagado = dinero(cuota.valor_pagado) + valor
    cuota.estado = (
        EstadoCuota.PAGADA
        if dinero(cuota.valor_pagado) >= dinero(cuota.valor)
        else EstadoCuota.PARCIAL
    )


# --- F1-CAR-02 Generacion de cuotas -----------------------------------------------------------


def generar_cuotas(db: Session, dia: date | None = None) -> int:
    """Emite las cuotas que vencen dentro de la ventana de emision. Repetible sin duplicar:
    cada periodo se emite una sola vez por contrato (ademas de la restriccion unica)."""
    dia = dia or hoy()
    limite = dia + timedelta(days=settings.CUOTA_EMISION_DIAS_ANTES)
    emitidas = 0
    contratos = db.scalars(select(Contrato).where(Contrato.estado.in_(GENERAN_CUOTAS)))
    for contrato in list(contratos):
        emitidas += _aislado(db, contrato, partial(_emitir_pendientes, db, contrato, limite)) or 0
    db.flush()
    return emitidas


def _emitir_pendientes(db: Session, contrato: Contrato, limite: date) -> int:
    ultimo = db.scalar(
        select(func.max(Cuota.periodo)).where(
            Cuota.contrato_id == contrato.id, Cuota.tipo == "mensual"
        )
    )
    per = siguiente_periodo(ultimo) if ultimo else periodo(contrato.fecha_inicio)
    emitidas = 0
    while vencimiento(per, contrato.dia_corte) <= limite:
        planes.aplicar_cambios_programados(db, contrato, vencimiento(per, contrato.dia_corte))
        if _emitir(db, contrato, per):
            emitidas += 1
        per = siguiente_periodo(per)
    return emitidas


def _aislado(db: Session, contrato: Contrato, fn: Callable[[], T]) -> T | None:
    """Corre el trabajo de un contrato en su propio savepoint. Los procesos diarios recorren
    todos los contratos en una transaccion: sin esto, un dato raro en uno solo revertiria
    las cuotas, estados y avisos de todos los demas."""
    try:
        with db.begin_nested():
            return fn()
    except Exception:  # noqa: BLE001  se registra y el lote sigue
        logger.exception("Proceso de cartera fallido para el contrato %s", contrato.id)
        return None


# --- F1-CAR-03 / 05 Estados de cartera --------------------------------------------------------


def cuotas_abiertas(db: Session, contrato_id: UUID) -> list[Cuota]:
    return list(
        db.scalars(
            select(Cuota)
            .where(Cuota.contrato_id == contrato_id, Cuota.estado.in_(EstadoCuota.ABIERTAS))
            .order_by(Cuota.fecha_vencimiento, Cuota.tipo)
        )
    )


def _dias_mora(cuotas: list[Cuota], dia: date) -> int:
    vencidas = [c for c in cuotas if c.fecha_vencimiento < dia]
    return max((dia - vencidas[0].fecha_vencimiento).days, 0) if vencidas else 0


def _sincronizar_familia(db: Session, contrato: Contrato) -> None:
    """6.23 El estado de la familia refleja el de su contrato vigente."""
    from app.modules.familias import service as familias

    familia = db.get(Familia, contrato.familia_id)
    assert familia is not None
    if familia.dada_de_baja_en is None and familia.estado != contrato.estado:
        familias.cambiar_estado(db, familia, contrato.estado)


def reevaluar_estado(db: Session, contrato: Contrato, dia: date | None = None) -> str:
    """Deriva el estado del contrato de las reglas `cartera.estado` (dias parametrizables).

    Devuelve la transicion ocurrida: 'sin_cambio', 'en_mora', 'congelada' o 'reactivada'.
    """
    if contrato.estado == EstadoAfiliacion.CANCELADA:
        return "sin_cambio"
    dia = dia or hoy()
    abiertas = cuotas_abiertas(db, contrato.id)
    dias = _dias_mora(abiertas, dia)
    for c in abiertas:
        c.dias_mora = max((dia - c.fecha_vencimiento).days, 0)
    contexto = {
        "dias_mora": dias,
        "cuotas_vencidas": sum(1 for c in abiertas if c.fecha_vencimiento < dia),
        "saldo_pendiente": float(sum(dinero(c.valor) - dinero(c.valor_pagado) for c in abiertas)),
        "estado_actual": contrato.estado,
    }
    resultado = reglas.primera(db, "cartera.estado", contexto, plan_id=contrato.plan_id)
    if resultado is None:
        return "sin_cambio"
    nuevo = EstadoAfiliacion(resultado.accion["estado"])
    anterior = contrato.estado
    if nuevo == anterior:
        return "sin_cambio"
    contrato.estado = nuevo
    db.flush()
    _sincronizar_familia(db, contrato)
    transicion = "reactivada" if anterior == EstadoAfiliacion.CONGELADA else nuevo.value
    _notificar_transicion(db, contrato, transicion)
    return transicion


_PLANTILLAS_TRANSICION = {
    "congelada": "afiliacion_congelada",
    "reactivada": "afiliacion_reactivada",
}


def _notificar_transicion(db: Session, contrato: Contrato, transicion: str) -> None:
    plantilla = _PLANTILLAS_TRANSICION.get(transicion)
    if plantilla is None:
        return
    _notificar(db, contrato, plantilla, [])


def _notificar(db: Session, contrato: Contrato, plantilla: str, extra: list[str]) -> UUID | None:
    from app.modules.comunicaciones import service as comunicaciones

    familia = db.get(Familia, contrato.familia_id)
    assert familia is not None
    try:
        mensaje = comunicaciones.encolar_plantilla(
            db,
            telefono=familia.telefono,
            plantilla=plantilla,
            variables=[familia.titular_nombre, *extra],
            familia_id=familia.id,
        )
    except ReglaNegocio as e:
        logger.error("Aviso %s no enviado a la familia %s: %s", plantilla, familia.id, e)
        return None
    return mensaje.id


# --- F1-CAR-04 Avisos de mora -----------------------------------------------------------------


def avisar_mora(db: Session, contrato: Contrato, dia: date | None = None) -> str | None:
    """Envia el aviso mas avanzado que corresponda y no se haya enviado para la cuota mas
    antigua. Los avisos previos que el proceso no alcanzo a enviar se registran omitidos,
    para no mandar varios el mismo dia. Devuelve la clave enviada."""
    dia = dia or hoy()
    abiertas = [c for c in cuotas_abiertas(db, contrato.id) if c.fecha_vencimiento < dia]
    if not abiertas:
        return None
    cuota = abiertas[0]
    dias = (dia - cuota.fecha_vencimiento).days
    aplicables = reglas.evaluar(db, "cartera.alerta", {"dias_mora": dias})
    enviadas = set(db.scalars(select(AvisoCartera.clave).where(AvisoCartera.cuota_id == cuota.id)))
    pendientes = [r for r in aplicables if r.accion["clave"] not in enviadas]
    if not pendientes:
        return None
    elegido, *anteriores = pendientes
    saldo = sum(dinero(c.valor) - dinero(c.valor_pagado) for c in abiertas)
    mensaje_id = _notificar(
        db,
        contrato,
        elegido.accion["plantilla"],
        [formato_cop(saldo), f"{cuota.fecha_vencimiento:%d/%m/%Y}"],
    )
    if mensaje_id is None:
        return None  # sin plantilla disponible: se reintenta en la siguiente corrida
    db.add(
        AvisoCartera(
            cuota_id=cuota.id,
            clave=elegido.accion["clave"],
            regla_codigo=elegido.regla,
            mensaje_id=mensaje_id,
        )
    )
    for r in anteriores:
        db.add(
            AvisoCartera(
                cuota_id=cuota.id, clave=r.accion["clave"], regla_codigo=r.regla, omitido=True
            )
        )
    db.flush()
    return str(elegido.accion["clave"])


@dataclass
class ResumenRevision:
    revisados: int = 0
    transiciones: dict[str, int] = field(default_factory=dict)
    avisos: int = 0
    errores: int = 0


def revisar_cartera(db: Session, dia: date | None = None) -> ResumenRevision:
    """Proceso diario: estados (F1-CAR-03 / 05) y avisos (F1-CAR-04)."""
    dia = dia or hoy()
    resumen = ResumenRevision()
    contratos = db.scalars(select(Contrato).where(Contrato.estado != EstadoAfiliacion.CANCELADA))
    for contrato in list(contratos):
        resumen.revisados += 1
        resultado = _aislado(db, contrato, partial(_revisar_contrato, db, contrato, dia))
        if resultado is None:
            resumen.errores += 1
            continue
        transicion, avisado = resultado
        if transicion != "sin_cambio":
            resumen.transiciones[transicion] = resumen.transiciones.get(transicion, 0) + 1
        resumen.avisos += avisado
    return resumen


def _revisar_contrato(db: Session, contrato: Contrato, dia: date) -> tuple[str, bool]:
    transicion = reevaluar_estado(db, contrato, dia)
    avisado = contrato.estado != EstadoAfiliacion.CONGELADA and bool(avisar_mora(db, contrato, dia))
    return transicion, avisado


# --- F1-CAR-06 Pagos --------------------------------------------------------------------------


def aplicar_pago(db: Session, pago: Pago) -> list[AplicacionPago]:
    """Aplica un pago aprobado: primero a la cuota indicada, luego de la mas antigua a la
    mas reciente. Lo que sobre queda como saldo a favor del contrato."""
    if pago.aplicado:
        return []
    contrato = db.get(Contrato, pago.contrato_id) if pago.contrato_id else None
    if contrato is None:
        contrato = planes.contrato_vigente(db, pago.familia_id)
    if contrato is None:
        raise ReglaNegocio("La familia no tiene un contrato vigente al cual aplicar el pago")
    pago.contrato_id = contrato.id
    abiertas = cuotas_abiertas(db, contrato.id)
    if pago.cuota_id:
        abiertas.sort(key=lambda c: c.id != pago.cuota_id)
    restante = dinero(pago.valor)
    aplicaciones = []
    for cuota in abiertas:
        if restante <= 0:
            break
        pendiente = dinero(cuota.valor) - dinero(cuota.valor_pagado)
        abono = min(pendiente, restante)
        _abonar(cuota, abono)
        restante -= abono
        aplicacion = AplicacionPago(pago_id=pago.id, cuota_id=cuota.id, valor=abono)
        db.add(aplicacion)
        aplicaciones.append(aplicacion)
    if restante > 0:
        contrato.saldo_a_favor = dinero(contrato.saldo_a_favor) + restante
    pago.aplicado = True
    db.flush()
    reevaluar_estado(db, contrato)
    return aplicaciones


def registrar_pago_manual(
    db: Session,
    *,
    familia_id: UUID,
    valor: Decimal,
    medio: str,
    referencia: str,
    fecha_pago: datetime | None,
    cuota_id: UUID | None,
    notas: str | None,
    usuario_id: UUID | None,
) -> Pago:
    if db.scalar(select(Pago.id).where(Pago.referencia_externa == referencia)):
        raise Conflicto(f"Ya existe un pago con la referencia {referencia}")
    if cuota_id:
        cuota = db.get(Cuota, cuota_id)
        contrato = db.get(Contrato, cuota.contrato_id) if cuota else None
        if cuota is None or contrato is None or contrato.familia_id != familia_id:
            raise ReglaNegocio("La cuota no pertenece a la familia")
    pago = Pago(
        id=uuid4(),
        familia_id=familia_id,
        cuota_id=cuota_id,
        referencia_externa=referencia,
        proveedor="manual",
        medio=medio,
        valor=dinero(valor),
        estado="aprobado",
        fecha_pago=fecha_pago or ahora(),
        registrado_por_id=usuario_id,
        notas=notas,
    )
    db.add(pago)
    db.flush()
    aplicar_pago(db, pago)
    return pago


# --- F1-CAR-07 Renovacion ---------------------------------------------------------------------

VENTANA_RENOVACION_DIAS = 90


def detectar_renovaciones(db: Session, dia: date | None = None) -> int:
    dia = dia or hoy()
    creadas = 0
    contratos = db.scalars(
        select(Contrato).where(
            Contrato.estado.in_(planes.VIGENTES),
            Contrato.fecha_renovacion <= dia + timedelta(days=VENTANA_RENOVACION_DIAS),
        )
    )
    for contrato in list(contratos):
        creadas += _aislado(db, contrato, partial(_tareas_renovacion, db, contrato, dia)) or 0
    return creadas


def _tareas_renovacion(db: Session, contrato: Contrato, dia: date) -> int:
    from app.modules.tareas import service as tareas

    contexto = {
        "dias_para_renovacion": (contrato.fecha_renovacion - dia).days,
        "estado": contrato.estado,
    }
    creadas = 0
    for r in reglas.evaluar(db, "cartera.renovacion", contexto, plan_id=contrato.plan_id):
        tarea = tareas.desde_accion(
            db,
            r.accion,
            r.regla,
            familia_id=contrato.familia_id,
            contrato_id=contrato.id,
            clave=f"renovacion:{contrato.id}:{contrato.fecha_renovacion}:{r.regla}",
        )
        creadas += tarea is not None
    return creadas


def renovar(db: Session, contrato: Contrato) -> Contrato:
    if contrato.estado == EstadoAfiliacion.CANCELADA:
        raise ReglaNegocio("El contrato esta cancelado")
    if contrato.fecha_renovacion > hoy() + timedelta(days=VENTANA_RENOVACION_DIAS):
        raise ReglaNegocio("El contrato aun no esta en ventana de renovacion")
    contrato.fecha_renovacion = sumar_meses(contrato.fecha_renovacion, 12)
    db.flush()
    return contrato


def cancelar(db: Session, contrato: Contrato, motivo: str) -> Contrato:
    if contrato.estado == EstadoAfiliacion.CANCELADA:
        raise ReglaNegocio("El contrato ya esta cancelado")
    contrato.estado = EstadoAfiliacion.CANCELADA
    contrato.fecha_fin = hoy()
    for cuota in cuotas_abiertas(db, contrato.id):
        if cuota.fecha_vencimiento > hoy():
            cuota.estado = EstadoCuota.ANULADA
    # Sin contrato no hay nada que cobrar: la tarjeta autorizada deja de usarse.
    for medio in db.scalars(
        select(MedioPagoRecurrente).where(
            MedioPagoRecurrente.familia_id == contrato.familia_id,
            MedioPagoRecurrente.activo.is_(True),
        )
    ):
        medio.activo = False
    db.flush()
    from app.modules.familias import service as familias

    familia = db.get(Familia, contrato.familia_id)
    assert familia is not None
    familias.cambiar_estado(db, familia, EstadoAfiliacion.CANCELADA, motivo)
    return contrato


def url_documento(db: Session, contrato: Contrato) -> dict[str, str]:
    from app.modules.archivos import service as archivos
    from app.modules.archivos.models import Archivo

    archivo = (
        db.get(Archivo, contrato.documento_archivo_id) if contrato.documento_archivo_id else None
    )
    if archivo is None:
        raise NoEncontrado("El contrato no tiene documento generado")
    return {"url": archivos.url(archivo), "sha256": archivo.sha256}


# --- Listado de cartera ----------------------------------------------------------------------


def listar_contratos(
    db: Session,
    *,
    estado: str | None = None,
    ciudad: str | None = None,
    q: str | None = None,
    solo_mora: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """Contratos con su saldo vencido y dias de mora (de la cuota abierta mas antigua),
    los mas atrasados primero."""
    dia = hoy()
    vencidas = (
        select(
            Cuota.contrato_id,
            func.sum(Cuota.valor - Cuota.valor_pagado).label("saldo"),
            func.min(Cuota.fecha_vencimiento).label("desde"),
        )
        .where(Cuota.estado.in_(EstadoCuota.ABIERTAS), Cuota.fecha_vencimiento < dia)
        .group_by(Cuota.contrato_id)
        .subquery()
    )
    stmt = (
        select(
            Contrato,
            Familia.titular_nombre,
            Familia.ciudad,
            Plan.nombre,
            vencidas.c.saldo,
            vencidas.c.desde,
        )
        .join(Familia, Familia.id == Contrato.familia_id)
        .join(Plan, Plan.id == Contrato.plan_id)
        .outerjoin(vencidas, vencidas.c.contrato_id == Contrato.id)
    )
    if estado:
        stmt = stmt.where(Contrato.estado == estado)
    if ciudad:
        stmt = stmt.where(Familia.ciudad == ciudad)
    if q:
        patron = f"%{q}%"
        stmt = stmt.where(
            Familia.titular_nombre.ilike(patron)
            | Familia.documento.ilike(patron)
            | Contrato.numero.ilike(patron)
        )
    if solo_mora:
        stmt = stmt.where(vencidas.c.saldo > 0)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    filas = db.execute(
        stmt.order_by(vencidas.c.desde.asc().nulls_last(), Contrato.numero)
        .limit(limit)
        .offset(offset)
    ).all()
    return [
        {
            "id": c.id,
            "numero": c.numero,
            "familia_id": c.familia_id,
            "titular": titular,
            "ciudad": ciudad_familia,
            "plan": plan,
            "estado": c.estado,
            "valor_mensual": dinero(c.valor_mensual),
            "saldo_vencido": dinero(saldo),
            "dias_mora": (dia - desde).days if desde else 0,
            "fecha_renovacion": c.fecha_renovacion,
        }
        for c, titular, ciudad_familia, plan, saldo, desde in filas
    ], int(total)


# --- F1-CAR-10 Estado de cuenta ---------------------------------------------------------------


def obtener_contrato(db: Session, contrato_id: UUID) -> Contrato:
    contrato = db.get(Contrato, contrato_id)
    if contrato is None:
        raise NoEncontrado("Contrato no encontrado")
    return contrato


def estado_cuenta(db: Session, familia_id: UUID, max_cuotas: int = 24) -> dict[str, Any]:
    contrato = planes.contrato_vigente(db, familia_id)
    if contrato is None:
        contrato = db.scalar(
            select(Contrato)
            .where(Contrato.familia_id == familia_id)
            .order_by(Contrato.fecha_inicio.desc())
        )
    if contrato is None:
        raise NoEncontrado("La familia no tiene contratos")
    plan = db.get(Plan, contrato.plan_id)
    cuotas = list(
        db.scalars(
            select(Cuota)
            .where(Cuota.contrato_id == contrato.id)
            .order_by(Cuota.fecha_vencimiento.desc(), Cuota.tipo)
            .limit(max_cuotas)
        )
    )
    pagos = list(
        db.scalars(
            select(Pago)
            .where(Pago.familia_id == familia_id)
            .order_by(Pago.created_at.desc())
            .limit(max_cuotas)
        )
    )
    abiertas = cuotas_abiertas(db, contrato.id)
    dia = hoy()
    saldo = sum((dinero(c.valor) - dinero(c.valor_pagado) for c in abiertas), dinero(0))
    vencido = sum(
        (dinero(c.valor) - dinero(c.valor_pagado) for c in abiertas if c.fecha_vencimiento < dia),
        dinero(0),
    )
    proxima = next((c for c in abiertas if c.fecha_vencimiento >= dia), None)
    if proxima:
        proximo_cobro = {"fecha": proxima.fecha_vencimiento, "valor": dinero(proxima.valor)}
    else:
        ultimo = max((c.periodo for c in cuotas if c.tipo == "mensual"), default=None)
        per = siguiente_periodo(ultimo) if ultimo else periodo(dia)
        proximo_cobro = {
            "fecha": vencimiento(per, contrato.dia_corte),
            "valor": max(
                dinero(contrato.valor_mensual) - dinero(contrato.saldo_a_favor), dinero(0)
            ),
        }
    return {
        "contrato": contrato,
        "plan": plan,
        "estado": contrato.estado,
        "saldo_pendiente": saldo,
        "saldo_vencido": vencido,
        "saldo_a_favor": dinero(contrato.saldo_a_favor),
        "dias_mora": _dias_mora(abiertas, dia),
        "proximo_cobro": proximo_cobro if contrato.estado != EstadoAfiliacion.CANCELADA else None,
        "cuotas": cuotas,
        "pagos": pagos,
    }

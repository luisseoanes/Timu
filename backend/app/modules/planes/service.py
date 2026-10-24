"""6.3 Planes: administracion, cupos de mascotas, cambios de plan y recomendacion."""

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import EstadoAfiliacion
from app.core.errores import Conflicto, NoEncontrado, ReglaNegocio
from app.core.tiempo import hoy
from app.modules.cartera.models import Contrato, Cuota, EstadoCuota
from app.modules.cartera.periodos import dias_del_periodo, dinero, periodo, sumar_meses
from app.modules.familias.models import Familia, Mascota
from app.modules.planes.models import Beneficio, CambioPlan, Plan
from app.modules.reglas import service as reglas

VIGENTES = (EstadoAfiliacion.ACTIVA, EstadoAfiliacion.EN_MORA, EstadoAfiliacion.CONGELADA)


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
    plan.beneficios.clear()
    db.flush()
    plan.beneficios.extend(Beneficio(**b) for b in beneficios)
    db.flush()
    return plan


def contrato_vigente(db: Session, familia_id: UUID) -> Contrato | None:
    return db.scalar(
        select(Contrato).where(Contrato.familia_id == familia_id, Contrato.estado.in_(VIGENTES))
    )


def validar_para_familia(plan: Plan, ciudad: str, especies: list[str]) -> None:
    if not plan.activo:
        raise ReglaNegocio(f"El plan {plan.nombre} no esta activo")
    if plan.ciudad and plan.ciudad != ciudad:
        raise ReglaNegocio(f"El plan {plan.nombre} no esta disponible en {ciudad}")
    if plan.especies:
        fuera = sorted(set(especies) - set(plan.especies))
        if fuera:
            raise ReglaNegocio(f"El plan {plan.nombre} no cubre: {', '.join(fuera)}")


def _mascotas_activas(db: Session, familia_id: UUID) -> list[Mascota]:
    return list(
        db.scalars(
            select(Mascota).where(Mascota.familia_id == familia_id, Mascota.activa.is_(True))
        )
    )


def calcular_cupo(
    db: Session, familia: Familia, plan: Plan, activas: int
) -> tuple[int, Decimal, str | None]:
    """F1-PLA-03 (adicionales, valor por adicional, regla aplicada) para `activas` mascotas.

    Dentro del cupo no hay recargo. Sobre el cupo decide la regla `plan.mascota`: rechazar,
    o cobrar un valor por mascota adicional hasta un maximo (0 = sin maximo).
    """
    exceso = max(0, activas - plan.cupos_mascotas)
    if exceso == 0:
        return 0, dinero(0), None
    contexto = {
        "plan": {"codigo": plan.codigo, "cupos": plan.cupos_mascotas},
        "familia": {"ciudad": familia.ciudad, "estado": familia.estado},
        "mascotas": {"activas": activas, "exceso": exceso},
    }
    resultado = reglas.primera(db, "plan.mascota", contexto, plan_id=plan.id)
    if resultado is None or resultado.accion["tipo"] == "rechazar":
        motivo = resultado.accion["motivo"] if resultado else "El plan no tiene cupo disponible"
        raise ReglaNegocio(motivo)
    maximo = resultado.accion["maximo_adicionales"]
    if maximo and exceso > maximo:
        raise ReglaNegocio(f"El plan admite como maximo {maximo} mascotas adicionales")
    return exceso, dinero(resultado.accion["valor_por_mascota_adicional"]), resultado.regla


def valor_mensual(contrato: Contrato) -> Decimal:
    return dinero(contrato.valor_plan) + contrato.mascotas_adicionales * dinero(
        contrato.valor_adicional_mascota
    )


def ajustar_por_mascotas(
    db: Session, familia: Familia, tipo: str, usuario_id: UUID | None = None
) -> CambioPlan | None:
    """F1-PLA-03 Tras alta o baja de mascota recalcula adicionales y valor del contrato.

    Se invoca antes del flush de la mascota nueva en altas (para rechazar sin guardar) y
    despues de la baja en retiros. El nuevo valor aplica desde la siguiente cuota.
    """
    contrato = contrato_vigente(db, familia.id)
    if contrato is None:
        return None
    plan = obtener(db, contrato.plan_id)
    activas = len(_mascotas_activas(db, familia.id)) + (1 if tipo == "mascota_alta" else 0)
    adicionales, valor_adicional, regla = calcular_cupo(db, familia, plan, activas)
    anterior = valor_mensual(contrato)
    contrato.mascotas_adicionales = adicionales
    contrato.valor_adicional_mascota = valor_adicional if adicionales else dinero(0)
    contrato.valor_mensual = valor_mensual(contrato)
    if contrato.valor_mensual == anterior:
        db.flush()
        return None
    cambio = CambioPlan(
        contrato_id=contrato.id,
        tipo=tipo,
        plan_anterior_id=plan.id,
        plan_nuevo_id=plan.id,
        valor_anterior=anterior,
        valor_nuevo=contrato.valor_mensual,
        modo="proxima_cuota",
        regla_codigo=regla,
        fecha_efectiva=hoy(),
        registrado_por_id=usuario_id,
    )
    db.add(cambio)
    db.flush()
    return cambio


# --- F1-PLA-02 Cambio de plan ----------------------------------------------------------------


def _ciclo_actual(contrato: Contrato, dia: date) -> tuple[date, date]:
    """Inicio y fin del ciclo de facturacion que contiene `dia` (de corte a corte)."""
    inicio = date(dia.year, dia.month, min(contrato.dia_corte, 28))
    if inicio > dia:
        inicio = sumar_meses(inicio, -1)
    return inicio, sumar_meses(inicio, 1)


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
    db: Session, contrato: Contrato, plan_nuevo: Plan, usuario_id: UUID | None
) -> CambioPlan:
    if contrato.plan_id == plan_nuevo.id:
        raise ReglaNegocio("La familia ya tiene ese plan")
    familia = db.get(Familia, contrato.familia_id)
    assert familia is not None
    mascotas = _mascotas_activas(db, familia.id)
    validar_para_familia(plan_nuevo, familia.ciudad, [m.especie for m in mascotas])
    plan_anterior = obtener(db, contrato.plan_id)

    contexto = {
        "familia": {"ciudad": familia.ciudad, "estado": familia.estado},
        "plan_anterior": {
            "codigo": plan_anterior.codigo,
            "valor": float(plan_anterior.valor_mensual),
        },
        "plan_nuevo": {"codigo": plan_nuevo.codigo, "valor": float(plan_nuevo.valor_mensual)},
        "sube": dinero(plan_nuevo.valor_mensual) > dinero(plan_anterior.valor_mensual),
    }
    resultado = reglas.primera(db, "plan.cambio", contexto, plan_id=plan_nuevo.id)
    if resultado is None:
        raise ReglaNegocio("No hay una regla que defina como cobrar el cambio de plan")
    if resultado.accion["tipo"] == "rechazar":
        raise ReglaNegocio(resultado.accion["motivo"])
    modo = resultado.accion["modo"]

    adicionales, valor_adicional, _ = calcular_cupo(db, familia, plan_nuevo, len(mascotas))
    anterior = valor_mensual(contrato)
    nuevo = dinero(plan_nuevo.valor_mensual) + adicionales * valor_adicional
    dia = hoy()
    inicio, fin = _ciclo_actual(contrato, dia)

    ajuste = dinero(0)
    fecha_efectiva = dia
    if modo == "diario":
        restantes = (fin - dia).days
        ajuste = dinero((nuevo - anterior) * restantes / dias_del_periodo(inicio))
    elif modo == "proximo_ciclo":
        fecha_efectiva = fin

    cambio = CambioPlan(
        contrato_id=contrato.id,
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
        _aplicar(contrato, plan_nuevo, adicionales, valor_adicional)
        if ajuste > 0:
            _cargar_ajuste(db, contrato, ajuste, dia)
        elif ajuste < 0:
            contrato.saldo_a_favor = dinero(contrato.saldo_a_favor) - ajuste
    db.flush()
    return cambio


def _aplicar(contrato: Contrato, plan: Plan, adicionales: int, valor_adicional: Decimal) -> None:
    contrato.plan_id = plan.id
    contrato.valor_plan = dinero(plan.valor_mensual)
    contrato.mascotas_adicionales = adicionales
    contrato.valor_adicional_mascota = valor_adicional if adicionales else dinero(0)
    contrato.valor_mensual = valor_mensual(contrato)


def aplicar_cambios_programados(db: Session, contrato: Contrato, hasta: date) -> None:
    """Cambios `proximo_ciclo` cuya fecha llego: se aplican antes de emitir la cuota."""
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
        plan = obtener(db, cambio.plan_nuevo_id)
        familia = db.get(Familia, contrato.familia_id)
        assert familia is not None
        activas = len(_mascotas_activas(db, familia.id))
        adicionales, valor_adicional, _ = calcular_cupo(db, familia, plan, activas)
        _aplicar(contrato, plan, adicionales, valor_adicional)
        cambio.aplicado = True
    db.flush()


# --- F1-PLA-04 Recomendacion ---------------------------------------------------------------


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

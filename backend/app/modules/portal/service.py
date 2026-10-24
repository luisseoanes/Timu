"""Portal de familias (F3-POR). Cada funcion recibe la familia del usuario conectado y
verifica que lo pedido sea suyo: una mascota, un servicio o un pago ajeno da el mismo
404 que uno inexistente."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import EstadoServicio, TipoServicio
from app.core.errores import NoEncontrado, ReglaNegocio
from app.core.tiempo import ahora, con_zona
from app.modules.cartera.models import Cuota, Pago
from app.modules.cartera.periodos import centavos, dinero
from app.modules.familias.models import Familia, Mascota
from app.modules.servicios.models import Servicio

PREFIJO_PAGO = "POR-"
# Lo que la familia puede agendar sola; lo demas pasa por el equipo.
MODALIDADES_AUTOGESTION = (TipoServicio.DOMICILIARIO, TipoServicio.PREVENTIVO, TipoServicio.CLINICO)


def mascota_propia(db: Session, familia: Familia, mascota_id: UUID) -> Mascota:
    mascota = db.get(Mascota, mascota_id)
    if mascota is None or mascota.familia_id != familia.id:
        raise NoEncontrado("Mascota no encontrada")
    return mascota


def _servicio_propio(db: Session, familia: Familia, servicio_id: UUID) -> Servicio:
    servicio = db.get(Servicio, servicio_id)
    if servicio is None or servicio.familia_id != familia.id:
        raise NoEncontrado("Servicio no encontrado")
    return servicio


# --- F3-POR-01 Plan vigente -------------------------------------------------------------------


def plan(db: Session, familia: Familia) -> dict[str, Any]:
    from app.modules.planes import service as planes
    from app.modules.planes.models import Plan
    from app.modules.servicios import service as servicios

    contrato = planes.contrato_vigente(db, familia.id)
    if contrato is None:
        raise NoEncontrado("La familia no tiene un plan vigente")
    p = db.get(Plan, contrato.plan_id)
    assert p is not None
    beneficios = []
    for b in p.beneficios:
        usados = servicios._usos(db, familia.id, b)
        beneficios.append(
            {
                "tipo_servicio": b.tipo_servicio_codigo,
                "cupo": b.cupo,
                "periodo": b.periodo_cupo,
                "usados": usados,
                "disponibles": None if b.cupo is None else max(b.cupo - usados, 0),
                "cobertura_pct": b.cobertura_pct,
            }
        )
    return {
        "plan": p.nombre,
        "estado": contrato.estado,
        "valor_mensual": dinero(contrato.valor_mensual),
        "fecha_inicio": contrato.fecha_inicio,
        "fecha_renovacion": contrato.fecha_renovacion,
        "beneficios": beneficios,
    }


# --- F3-POR-02 / 03 Historia y carnet ---------------------------------------------------------


def historia(db: Session, familia: Familia, mascota_id: UUID) -> list[dict[str, Any]]:
    """Solo lo firmado y sin las notas de uso interno del equipo medico."""
    from app.modules.clinica import service as clinica

    mascota = mascota_propia(db, familia, mascota_id)
    return [
        clinica.presentar(e, "familia")
        for e in clinica.historia(db, mascota.id, solo_firmadas=True)
    ]


def url_adjunto(db: Session, familia: Familia, adjunto_id: UUID) -> dict[str, str]:
    from app.modules.clinica import service as clinica
    from app.modules.clinica.models import AdjuntoClinico, HistoriaClinica

    adjunto = db.get(AdjuntoClinico, adjunto_id)
    entrada = db.get(HistoriaClinica, adjunto.historia_id) if adjunto else None
    if entrada is None or entrada.familia_id != familia.id or entrada.estado != "firmada":
        raise NoEncontrado("Adjunto no encontrado")
    return clinica.url_adjunto(db, adjunto_id, "familia")


def adjuntos(db: Session, familia: Familia, historia_id: UUID) -> list[Any]:
    from app.modules.clinica import service as clinica
    from app.modules.clinica.models import HistoriaClinica

    entrada = db.get(HistoriaClinica, historia_id)
    if entrada is None or entrada.familia_id != familia.id or entrada.estado != "firmada":
        raise NoEncontrado("Entrada no encontrada")
    return clinica.adjuntos(db, historia_id)


# --- F3-POR-04 Autogestion de servicios -------------------------------------------------------


def _tipo_autogestionable(db: Session, codigo: str) -> Any:
    from app.modules.servicios import service as servicios

    tipo = servicios.tipo_servicio(db, codigo)
    if tipo.modalidad not in MODALIDADES_AUTOGESTION:
        raise ReglaNegocio("Ese tipo de servicio se solicita a traves del equipo de TIMU")
    return tipo


def disponibilidad(db: Session, familia: Familia, fecha: date, tipo_codigo: str) -> list[Any]:
    from app.modules.servicios import service as servicios

    tipo = _tipo_autogestionable(db, tipo_codigo)
    return servicios.disponibilidad(db, fecha, familia.ciudad, tipo)


def agendar(
    db: Session,
    familia: Familia,
    *,
    mascota_id: UUID,
    tipo_codigo: str,
    inicio: datetime,
    observaciones: str | None,
) -> Servicio:
    """Mismas reglas que el panel: elegibilidad (plan, cartera, cupo) y cupo real."""
    from app.modules.servicios import service as servicios

    mascota = mascota_propia(db, familia, mascota_id)
    tipo = _tipo_autogestionable(db, tipo_codigo)
    return servicios.agendar(
        db,
        familia=familia,
        mascota=mascota,
        tipo=tipo,
        inicio=inicio,
        observaciones=f"[portal] {observaciones}" if observaciones else "[portal]",
    )


def _con_antelacion(servicio: Servicio) -> None:
    limite = ahora() + timedelta(hours=settings.PORTAL_ANTELACION_HORAS)
    if servicio.programado_para is None or con_zona(servicio.programado_para) < limite:
        raise ReglaNegocio(
            f"Los cambios desde el portal se hacen con al menos "
            f"{settings.PORTAL_ANTELACION_HORAS} horas de anticipacion; comuniquese con TIMU"
        )


def reprogramar(
    db: Session, familia: Familia, servicio_id: UUID, inicio: datetime, motivo: str
) -> Servicio:
    from app.modules.servicios import service as servicios

    servicio = _servicio_propio(db, familia, servicio_id)
    if servicio.estado != EstadoServicio.AGENDADO or servicio.ruta_id is not None:
        raise ReglaNegocio("Ese servicio ya no se puede reprogramar desde el portal")
    _con_antelacion(servicio)
    return servicios.reprogramar(db, servicio, inicio, f"[portal] {motivo}")


def cancelar(db: Session, familia: Familia, servicio_id: UUID, motivo: str) -> Servicio:
    from app.modules.servicios import service as servicios

    servicio = _servicio_propio(db, familia, servicio_id)
    if servicio.estado not in (EstadoServicio.AGENDADO, EstadoServicio.PENDIENTE_AUTORIZACION):
        raise ReglaNegocio("Ese servicio ya no se puede cancelar desde el portal")
    _con_antelacion(servicio)
    return servicios.cambiar_estado(db, servicio, EstadoServicio.CANCELADO, f"[portal] {motivo}")


def servicios_de(db: Session, familia: Familia, incluir_pasados: bool) -> list[Servicio]:
    stmt = select(Servicio).where(Servicio.familia_id == familia.id)
    if not incluir_pasados:
        stmt = stmt.where(
            Servicio.estado.in_(
                (
                    EstadoServicio.AGENDADO,
                    EstadoServicio.PENDIENTE_AUTORIZACION,
                    EstadoServicio.EN_RUTA,
                    EstadoServicio.EN_ATENCION,
                )
            )
        )
    return list(db.scalars(stmt.order_by(Servicio.programado_para.desc()).limit(200)))


# --- F3-POR-05 Pagos en linea -----------------------------------------------------------------


def iniciar_pago(db: Session, familia: Familia, cuota_id: UUID | None) -> tuple[Pago, str]:
    """Pago de una cuota o de todo lo pendiente. Lo confirma el webhook de la pasarela,
    que aplica el pago y actualiza el estado de la familia al instante."""
    from app.integrations.payments import construir_link_pago
    from app.modules.cartera import service as cartera
    from app.modules.planes import service as planes

    contrato = planes.contrato_vigente(db, familia.id)
    if contrato is None:
        raise ReglaNegocio("La familia no tiene un contrato vigente")
    abiertas = cartera.cuotas_abiertas(db, contrato.id)
    if cuota_id is not None:
        abiertas = [c for c in abiertas if c.id == cuota_id]
        if not abiertas:
            raise NoEncontrado("Cuota no encontrada o ya pagada")
    valor = sum((dinero(c.valor) - dinero(c.valor_pagado) for c in abiertas), Decimal(0))
    if valor <= 0:
        raise ReglaNegocio("No hay saldo pendiente por pagar")
    pago = Pago(
        id=uuid4(),
        familia_id=familia.id,
        contrato_id=contrato.id,
        cuota_id=cuota_id,
        referencia_externa=f"{PREFIJO_PAGO}{uuid4().hex[:20].upper()}",
        proveedor="wompi",
        valor=dinero(valor),
        estado="pendiente",
    )
    db.add(pago)
    db.flush()
    enlace = construir_link_pago(
        pago.referencia_externa,
        centavos(pago.valor),
        familia.email,
        redireccion=f"{settings.FRONTEND_URL}/portal/pagos/{pago.id}",
    )
    return pago, enlace


def pagos(db: Session, familia: Familia) -> list[Pago]:
    return list(
        db.scalars(
            select(Pago)
            .where(Pago.familia_id == familia.id, Pago.estado != "anulado")
            .order_by(Pago.created_at.desc())
            .limit(100)
        )
    )


def comprobante(db: Session, familia: Familia, pago_id: UUID) -> bytes:
    from app.modules.cartera.models import AplicacionPago
    from app.modules.portal import documento

    pago = db.get(Pago, pago_id)
    if pago is None or pago.familia_id != familia.id:
        raise NoEncontrado("Pago no encontrado")
    if pago.estado != "aprobado":
        raise ReglaNegocio("El comprobante esta disponible cuando el pago se aprueba")
    aplicadas = db.execute(
        select(Cuota.descripcion, AplicacionPago.valor)
        .join(Cuota, Cuota.id == AplicacionPago.cuota_id)
        .where(AplicacionPago.pago_id == pago.id)
    ).all()
    return documento.generar_comprobante(
        familia={"titular": familia.titular_nombre, "documento": familia.documento},
        pago={
            "referencia": pago.referencia_externa,
            "fecha": pago.fecha_pago or pago.created_at,
            "medio": pago.medio or pago.proveedor,
            "valor": dinero(pago.valor),
        },
        aplicaciones=[(d or "Cuota", dinero(v)) for d, v in aplicadas],
    )


# --- F3-POR-06 Datos de contacto --------------------------------------------------------------


def actualizar_datos(db: Session, familia: Familia, cambios: dict[str, Any]) -> Familia:
    """Contacto y direccion, con las mismas validaciones del panel; la auditoria guarda
    quien cambio que (el usuario de portal)."""
    from app.modules.familias import service as familias
    from app.modules.familias.schemas import FamiliaUpdate

    if not cambios:
        raise ReglaNegocio("No hay cambios")
    return familias.actualizar(db, familia, FamiliaUpdate(**cambios))

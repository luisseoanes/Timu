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
from app.core.database import nuevo_id
from app.core.enums import EstadoAfiliacion, EstadoServicio, TipoServicio
from app.core.errores import NoEncontrado, ReglaNegocio
from app.core.tiempo import ahora, con_zona, hoy
from app.integrations.payments import construir_link_pago
from app.modules.afiliaciones import altas
from app.modules.cartera import contratos
from app.modules.cartera import service as cartera
from app.modules.cartera.models import AplicacionPago, Cuota, Pago
from app.modules.cartera.periodos import centavos, dinero, nombre_cuota
from app.modules.catalogos.models import TipoServicioCatalogo
from app.modules.clinica import service as clinica
from app.modules.clinica.models import AdjuntoClinico, HistoriaClinica
from app.modules.familias import service as familias
from app.modules.familias.models import Familia, Mascota
from app.modules.familias.schemas import FamiliaUpdate
from app.modules.planes import service as planes
from app.modules.portal import documento
from app.modules.servicios import service as servicios
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


# --- Seccion 14 Plan vigente -------------------------------------------------------------------


def _motivo_sin_agendar(contrato: Any) -> str | None:
    """Por que la familia no puede agendar sola ahora, en sus palabras, o None si puede. Son las
    causas del contrato de `servicios.elegibilidad`; las de cada cita (el cupo, la mascota) las
    dice el backend al agendar."""
    if contrato.fecha_renovacion < hoy():
        return "Tu plan venció y no se ha renovado: escríbenos por WhatsApp para renovarlo."
    if contrato.estado == EstadoAfiliacion.CONGELADA:
        return "Tu plan está en pausa por cuotas vencidas: al pagarlas, podrás agendar."
    if contrato.estado == EstadoAfiliacion.EN_MORA:
        return "Tienes cuotas vencidas: al pagarlas, podrás agendar."
    if contrato.estado != EstadoAfiliacion.ACTIVA:
        return "Escríbenos por WhatsApp para agendar."
    return None


def _aviso_pausa(contrato: Any) -> str | None:
    """Que sigue disponible con cuotas vencidas, dicho de frente (R4-CIE-02). Valor provisional
    del 2026-11-21, el comportamiento de hoy: no se agenda ni se agrega un peludo, y la
    orientacion virtual sigue. Lo confirma TIMU (docs/pendientes-externos.md)."""
    if contrato.estado == EstadoAfiliacion.CONGELADA:
        return (
            "Mientras el plan esté en pausa no se pueden agendar servicios ni agregar peludos. "
            "Sí puedes hablar con un veterinario."
        )
    if contrato.estado == EstadoAfiliacion.EN_MORA:
        return (
            "Mientras tengas cuotas vencidas no se pueden agendar servicios ni agregar peludos. "
            "Sí puedes hablar con un veterinario."
        )
    return None


def plan(db: Session, familia: Familia) -> dict[str, Any]:
    """La afiliacion vigente: cada peludo con su plan, lo que paga y sus beneficios con el
    cupo que le queda (cada uno tiene el suyo)."""
    contrato = contratos.contrato_vigente(db, familia.id)
    if contrato is None:
        raise NoEncontrado("La familia no tiene un plan vigente")
    peludos = []
    for linea in contratos.lineas(db, contrato):
        p = planes.obtener(db, linea.plan_id)
        mascota = db.get(Mascota, linea.mascota_id)
        assert mascota is not None
        beneficios = []
        for b in p.beneficios:
            usados = servicios._usos(db, linea.mascota_id, b)
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
        peludos.append(
            {
                "mascota_id": linea.mascota_id,
                "mascota": mascota.nombre,
                "plan": p.nombre,
                # El color del catalogo (manual de marca, regla 5): el portal no lo deduce.
                "color": p.color,
                "valor_mensual": dinero(linea.valor_mensual),
                "beneficios": beneficios,
            }
        )
    return {
        "mascotas": peludos,
        "estado": contrato.estado,
        "motivo_sin_agendar": _motivo_sin_agendar(contrato),
        "motivo_sin_alta": altas.motivo_sin_alta(contrato),
        "aviso_pausa": _aviso_pausa(contrato),
        "tipos_agendables": [
            {"codigo": t.codigo, "nombre": t.nombre, "modalidad": t.modalidad}
            for t in db.scalars(
                select(TipoServicioCatalogo)
                .where(
                    TipoServicioCatalogo.activo.is_(True),
                    TipoServicioCatalogo.modalidad.in_(MODALIDADES_AUTOGESTION),
                )
                .order_by(TipoServicioCatalogo.nombre)
            )
        ],
        "periodicidad": contrato.periodicidad,
        "valor_periodo": dinero(contrato.valor_periodo),
        "valor_mensual": dinero(contrato.valor_mensual),
        "fecha_inicio": contrato.fecha_inicio,
        "fecha_renovacion": contrato.fecha_renovacion,
    }


# --- Seccion 14 Historia y carnet ---------------------------------------------------------


def historia(db: Session, familia: Familia, mascota_id: UUID) -> list[dict[str, Any]]:
    """Solo lo firmado y sin las notas de uso interno del equipo medico."""

    mascota = mascota_propia(db, familia, mascota_id)
    return [
        clinica.presentar(e, "familia")
        for e in clinica.historia(db, mascota.id, solo_firmadas=True)
    ]


def url_adjunto(db: Session, familia: Familia, adjunto_id: UUID) -> dict[str, str]:
    adjunto = db.get(AdjuntoClinico, adjunto_id)
    entrada = db.get(HistoriaClinica, adjunto.historia_id) if adjunto else None
    if entrada is None or entrada.familia_id != familia.id or entrada.estado != "firmada":
        raise NoEncontrado("Adjunto no encontrado")
    return clinica.url_adjunto(db, adjunto_id, "familia")


def adjuntos(db: Session, familia: Familia, historia_id: UUID) -> list[Any]:
    entrada = db.get(HistoriaClinica, historia_id)
    if entrada is None or entrada.familia_id != familia.id or entrada.estado != "firmada":
        raise NoEncontrado("Entrada no encontrada")
    return clinica.adjuntos(db, historia_id)


# --- Seccion 14 Autogestion de servicios -------------------------------------------------------


def _tipo_autogestionable(db: Session, codigo: str) -> Any:
    tipo = servicios.tipo_servicio(db, codigo)
    if tipo.modalidad not in MODALIDADES_AUTOGESTION:
        raise ReglaNegocio("Ese tipo de servicio se solicita a traves del equipo de TIMU")
    return tipo


def disponibilidad(db: Session, familia: Familia, fecha: date, tipo_codigo: str) -> list[Any]:
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

    mascota = mascota_propia(db, familia, mascota_id)
    tipo = _tipo_autogestionable(db, tipo_codigo)
    if tipo.modalidad == TipoServicio.PREVENTIVO:
        # DEU-3 Una visita preventiva sin su preventivo no aplicaba nada al completarse.
        raise ReglaNegocio("Elige cuál de sus preventivos vas a agendar")
    return servicios.agendar(
        db,
        familia=familia,
        mascota=mascota,
        tipo=tipo,
        inicio=inicio,
        observaciones=f"[portal] {observaciones}" if observaciones else "[portal]",
    )


def _a_tiempo(servicio: Servicio) -> bool:
    limite = ahora() + timedelta(hours=settings.PORTAL_ANTELACION_HORAS)
    return servicio.programado_para is not None and con_zona(servicio.programado_para) >= limite


def que_puede(servicio: Servicio) -> dict[str, Any]:
    """Lo que la familia puede hacer sola con una cita, y por que no si hay algo que no. Lo
    usan el listado (el portal no copia las reglas) y `reprogramar` y `cancelar`."""
    cambiar = servicio.estado == EstadoServicio.AGENDADO and servicio.ruta_id is None
    cancelar = servicio.estado in (EstadoServicio.AGENDADO, EstadoServicio.PENDIENTE_AUTORIZACION)
    motivo = None
    if (cambiar or cancelar) and not _a_tiempo(servicio):
        cambiar = cancelar = False
        motivo = (
            f"Faltan menos de {settings.PORTAL_ANTELACION_HORAS} horas: para cambiarla o "
            "cancelarla, escríbenos por WhatsApp."
        )
    elif servicio.estado == EstadoServicio.AGENDADO and not cambiar:
        motivo = "Ya está en la ruta del día: para cambiarla, escríbenos por WhatsApp."
    return {"puede_cambiar": cambiar, "puede_cancelar": cancelar, "sin_cambios": motivo}


def reprogramar(
    db: Session, familia: Familia, servicio_id: UUID, inicio: datetime, motivo: str
) -> Servicio:
    servicio = _servicio_propio(db, familia, servicio_id)
    puede = que_puede(servicio)
    if not puede["puede_cambiar"]:
        raise ReglaNegocio(
            puede["sin_cambios"] or "Esa cita ya no se puede cambiar desde el portal"
        )
    return servicios.reprogramar(db, servicio, inicio, f"[portal] {motivo}")


def cancelar(db: Session, familia: Familia, servicio_id: UUID, motivo: str) -> Servicio:
    servicio = _servicio_propio(db, familia, servicio_id)
    puede = que_puede(servicio)
    if not puede["puede_cancelar"]:
        raise ReglaNegocio(
            puede["sin_cambios"] or "Esa cita ya no se puede cancelar desde el portal"
        )
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


# --- Seccion 14 Pagos en linea -----------------------------------------------------------------


def iniciar_pago(db: Session, familia: Familia, cuota_id: UUID | None) -> tuple[Pago, str]:
    """Pago de una cuota o de todo lo pendiente. Lo confirma el webhook de la pasarela,
    que aplica el pago y actualiza el estado de la familia al instante."""

    contrato = contratos.contrato_vigente(db, familia.id)
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
        id=nuevo_id(),
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
    pago = db.get(Pago, pago_id)
    if pago is None or pago.familia_id != familia.id:
        raise NoEncontrado("Pago no encontrado")
    if pago.estado != "aprobado":
        raise ReglaNegocio("El comprobante esta disponible cuando el pago se aprueba")
    aplicadas = db.execute(
        select(Cuota.periodo, Cuota.meses, Cuota.tipo, Cuota.descripcion, AplicacionPago.valor)
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
        aplicaciones=[(nombre_cuota(p, m, t, d), dinero(v)) for p, m, t, d, v in aplicadas],
    )


# --- 6.1 Datos de contacto --------------------------------------------------------------


def actualizar_datos(db: Session, familia: Familia, cambios: dict[str, Any]) -> Familia:
    """Contacto y direccion, con las mismas validaciones del panel; la auditoria guarda
    quien cambio que (el usuario de portal)."""

    if not cambios:
        raise ReglaNegocio("No hay cambios")
    return familias.actualizar(db, familia, FamiliaUpdate(**cambios))

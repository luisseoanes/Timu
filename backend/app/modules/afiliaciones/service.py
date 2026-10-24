"""F1-AFI-01..03 Afiliacion: formulario -> pago -> contrato -> perfil, sin redigitacion.

1. La familia llena el formulario (o comercial la afilia de forma asistida) y acepta las
   condiciones: se crea o completa su perfil y una solicitud con un pago pendiente.
2. Al aprobarse el pago (webhook de la pasarela o pago manual) se completa sola: contrato,
   primera cuota pagada, PDF del contrato, acceso al portal, calendario preventivo y
   mensaje de bienvenida.
"""

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errores import ErrorDominio, NoEncontrado, ReglaNegocio
from app.core.tiempo import ahora, hoy
from app.integrations.payments import construir_link_pago
from app.modules.afiliaciones import documento
from app.modules.afiliaciones.models import EstadoSolicitud, SolicitudAfiliacion
from app.modules.archivos import service as archivos
from app.modules.cartera import pasarela
from app.modules.cartera import service as cartera
from app.modules.cartera.models import Contrato, Pago
from app.modules.cartera.periodos import centavos, dinero
from app.modules.familias import service as familias
from app.modules.familias.models import Familia, Mascota
from app.modules.planes import service as planes
from app.modules.planes.models import Plan

logger = structlog.get_logger(__name__)

PREFIJO = "AFI-"


def _valor_inicial(db: Session, familia: Familia, plan: Plan) -> Decimal:
    activas = [m for m in familia.mascotas if m.activa]
    if not activas:
        raise ReglaNegocio("Debe registrar al menos una mascota para afiliarse")
    planes.validar_para_familia(plan, familia.ciudad, [m.especie for m in activas])
    adicionales, valor_adicional, _ = planes.calcular_cupo(db, familia, plan, len(activas))
    return dinero(plan.valor_mensual) + adicionales * valor_adicional


def iniciar(
    db: Session,
    *,
    familia: Familia,
    plan: Plan,
    origen: str,
    aceptacion: dict[str, Any],
) -> tuple[SolicitudAfiliacion, str]:
    """Crea la solicitud con su pago pendiente y devuelve el enlace de pago."""
    if planes.contrato_vigente(db, familia.id):
        raise ReglaNegocio(
            "No es posible completar la afiliacion en linea; un asesor te contactara"
        )
    abierta = db.scalar(
        select(SolicitudAfiliacion).where(
            SolicitudAfiliacion.familia_id == familia.id,
            SolicitudAfiliacion.estado == EstadoSolicitud.PENDIENTE_PAGO,
        )
    )
    if abierta:
        # Un segundo intento reemplaza al anterior (p. ej. cambio de plan antes de pagar).
        abierta.estado = EstadoSolicitud.CANCELADA
        pago_viejo = db.get(Pago, abierta.pago_id) if abierta.pago_id else None
        if pago_viejo and pago_viejo.estado == "pendiente":
            pago_viejo.estado = "anulado"
    valor = _valor_inicial(db, familia, plan)
    referencia = f"{PREFIJO}{uuid4().hex[:20].upper()}"
    pago = Pago(
        id=uuid4(),
        familia_id=familia.id,
        referencia_externa=referencia,
        proveedor="wompi",
        valor=valor,
        estado="pendiente",
    )
    solicitud = SolicitudAfiliacion(
        familia_id=familia.id,
        plan_id=plan.id,
        valor_inicial=valor,
        referencia_pago=referencia,
        pago_id=pago.id,
        origen=origen,
        aceptacion={
            **aceptacion,
            "version_terminos": documento.TERMINOS_VERSION,
            "fecha": ahora().isoformat(),
        },
    )
    db.add(pago)
    db.flush()  # la solicitud referencia al pago
    db.add(solicitud)
    db.flush()
    enlace = construir_link_pago(
        referencia,
        centavos(valor),
        familia.email,
        redireccion=f"{settings.FRONTEND_URL}/afiliacion/resultado",
    )
    return solicitud, enlace


def registrar_pago_manual(
    db: Session,
    solicitud: SolicitudAfiliacion,
    *,
    medio: str,
    comprobante: str,
    usuario_id: UUID,
) -> SolicitudAfiliacion:
    if solicitud.estado != EstadoSolicitud.PENDIENTE_PAGO:
        raise ReglaNegocio("La solicitud no esta pendiente de pago")
    pago = db.get(Pago, solicitud.pago_id)
    assert pago is not None
    pago.proveedor = "manual"
    pago.medio = medio
    pago.notas = f"Comprobante {comprobante}"
    pago.registrado_por_id = usuario_id
    pago.estado = "aprobado"
    pago.fecha_pago = ahora()
    completar(db, pago)
    return solicitud


@pasarela.al_aprobar(PREFIJO)
def completar(db: Session, pago: Pago) -> None:
    solicitud = db.scalar(
        select(SolicitudAfiliacion).where(
            SolicitudAfiliacion.referencia_pago == pago.referencia_externa
        )
    )
    if solicitud is None:
        raise ReglaNegocio(f"No hay solicitud de afiliacion para {pago.referencia_externa}")
    if solicitud.estado == EstadoSolicitud.COMPLETADA:
        return
    if solicitud.estado == EstadoSolicitud.CANCELADA:
        # Pagaron el enlace de un intento que despues se reemplazo (otro plan, otro valor):
        # afiliar con las condiciones viejas seria un error, y el dinero ya entro.
        from app.modules.tareas import service as tareas

        tareas.crear(
            db,
            titulo="Pago recibido de una solicitud de afiliacion reemplazada",
            descripcion=(
                f"Referencia {pago.referencia_externa}: decidir si se aplica a la solicitud "
                "vigente o se devuelve."
            ),
            area="comercial",
            prioridad="alta",
            vence_en_dias=1,
            familia_id=solicitud.familia_id,
            origen="afiliacion",
            clave=f"afiliacion_pago_reemplazada:{solicitud.id}",
        )
        logger.warning("Pago %s de una solicitud cancelada", pago.referencia_externa)
        return
    try:
        with db.begin_nested():
            _completar(db, solicitud, pago)
    except ErrorDominio as e:
        # El pago quedo aprobado: alguien debe resolver a mano (p. ej. el plan ya no aplica).
        from app.modules.tareas import service as tareas

        solicitud.estado = EstadoSolicitud.ERROR
        solicitud.error = e.mensaje
        tareas.crear(
            db,
            titulo="Afiliacion pagada que no se pudo completar",
            descripcion=e.mensaje,
            area="comercial",
            prioridad="alta",
            vence_en_dias=1,
            familia_id=solicitud.familia_id,
            origen="afiliacion",
            clave=f"afiliacion_error:{solicitud.id}",
        )
        logger.error("Afiliacion %s no completada: %s", solicitud.id, e.mensaje)
    db.flush()


def _completar(db: Session, solicitud: SolicitudAfiliacion, pago: Pago) -> None:
    familia = familias.obtener(db, solicitud.familia_id)
    plan = planes.obtener(db, solicitud.plan_id)
    contrato, cuota = cartera.crear_contrato(db, familia, plan, fecha_inicio=hoy())
    contrato.aceptado_en = ahora()
    contrato.medio_aceptacion = solicitud.aceptacion.get("medio")
    contrato.evidencia_aceptacion = solicitud.aceptacion

    pago.contrato_id = contrato.id
    pago.cuota_id = cuota.id if cuota else None
    cartera.aplicar_pago(db, pago)

    _documento(db, contrato, familia, plan)
    familias.habilitar_portal(db, familia)
    _calendario_preventivo(db, familia, hoy())
    _bienvenida(db, familia, plan)

    solicitud.contrato_id = contrato.id
    solicitud.estado = EstadoSolicitud.COMPLETADA
    solicitud.completada_en = ahora()
    solicitud.error = None


def _documento(db: Session, contrato: Contrato, familia: Familia, plan: Plan) -> None:
    mascotas = [m for m in familia.mascotas if m.activa]
    contenido = documento.generar_contrato(
        numero=contrato.numero,
        fecha=contrato.fecha_inicio,
        familia={
            "titular_nombre": familia.titular_nombre,
            "tipo_documento": familia.tipo_documento,
            "documento": familia.documento,
            "telefono": familia.telefono,
            "email": familia.email,
            "direccion": familia.direccion,
            "ciudad": familia.ciudad,
        },
        plan={
            "nombre": plan.nombre,
            "beneficios": [
                {
                    "tipo_servicio_codigo": b.tipo_servicio_codigo,
                    "cupo": b.cupo,
                    "periodo_cupo": b.periodo_cupo,
                    "cobertura_pct": b.cobertura_pct,
                }
                for b in plan.beneficios
            ],
        },
        mascotas=[{"nombre": m.nombre, "especie": m.especie, "raza": m.raza} for m in mascotas],
        contrato={
            "valor_plan": contrato.valor_plan,
            "mascotas_adicionales": contrato.mascotas_adicionales,
            "valor_mensual": contrato.valor_mensual,
            "dia_corte": contrato.dia_corte,
            "fecha_inicio": contrato.fecha_inicio,
            "fecha_renovacion": contrato.fecha_renovacion,
        },
    )
    archivo = archivos.guardar_bytes(
        db,
        contenido=contenido,
        nombre=f"contrato-{contrato.numero}.pdf",
        proposito="contrato",
        usuario_id=None,
    )
    contrato.documento_archivo_id = archivo.id
    contrato.evidencia_aceptacion = {
        **contrato.evidencia_aceptacion,
        "sha256_documento": archivo.sha256,
    }


def _calendario_preventivo(db: Session, familia: Familia, desde: date) -> None:
    from app.modules.preventivos import service as preventivos

    for mascota in db.scalars(
        select(Mascota).where(Mascota.familia_id == familia.id, Mascota.activa.is_(True))
    ):
        preventivos.calendario_inicial(db, mascota, desde)


def _bienvenida(db: Session, familia: Familia, plan: Plan) -> None:
    from app.modules.comunicaciones import service as comunicaciones

    try:
        comunicaciones.encolar_plantilla(
            db,
            telefono=familia.telefono,
            plantilla="bienvenida",
            variables=[familia.titular_nombre, plan.nombre],
            familia_id=familia.id,
        )
    except ReglaNegocio as e:
        logger.error("Bienvenida sin enviar a %s: %s", familia.id, e)


def obtener(db: Session, solicitud_id: UUID) -> SolicitudAfiliacion:
    solicitud = db.get(SolicitudAfiliacion, solicitud_id)
    if solicitud is None:
        raise NoEncontrado("Solicitud no encontrada")
    return solicitud

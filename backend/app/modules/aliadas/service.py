"""6.22 Clinicas aliadas: convenios, remisiones, validacion por la aliada y liquidacion."""

import secrets
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import EstadoServicio, TipoServicio
from app.core.errores import NoEncontrado, ReglaNegocio
from app.core.tiempo import ZONA_NEGOCIO, ahora, con_zona, hoy
from app.modules.aliadas.models import ClinicaAliada, ConvenioAliada, RemisionAliada
from app.modules.cartera.periodos import dinero
from app.modules.familias.models import Familia, Mascota
from app.modules.planes.models import Plan
from app.modules.servicios.models import Servicio

TIPO_SERVICIO_ALIADA = "atencion_aliada"


def obtener_clinica(db: Session, clinica_id: UUID) -> ClinicaAliada:
    clinica = db.get(ClinicaAliada, clinica_id)
    if clinica is None:
        raise NoEncontrado("Clinica aliada no encontrada")
    return clinica


# --- F2-ALI-01 Convenios ----------------------------------------------------------------------


def crear_convenio(db: Session, clinica: ClinicaAliada, datos: dict[str, Any]) -> ConvenioAliada:
    if datos.get("plan_id") and db.get(Plan, datos["plan_id"]) is None:
        raise NoEncontrado("Plan no encontrado")
    hasta = datos.get("vigente_hasta")
    if hasta and hasta < datos["vigente_desde"]:
        raise ReglaNegocio("La vigencia termina antes de empezar")
    convenio = ConvenioAliada(clinica_id=clinica.id, **datos)
    db.add(convenio)
    db.flush()
    return convenio


def convenios_vigentes(
    db: Session, clinica_id: UUID, plan_id: UUID | None, dia: date
) -> list[ConvenioAliada]:
    """Primero los del plan de la familia, despues los generales de la clinica."""
    stmt = select(ConvenioAliada).where(
        ConvenioAliada.clinica_id == clinica_id,
        ConvenioAliada.activo.is_(True),
        ConvenioAliada.vigente_desde <= dia,
        or_(ConvenioAliada.vigente_hasta.is_(None), ConvenioAliada.vigente_hasta >= dia),
        or_(ConvenioAliada.plan_id.is_(None), ConvenioAliada.plan_id == plan_id),
    )
    return sorted(db.scalars(stmt), key=lambda c: c.plan_id is None)


# --- F2-ALI-02 Remision -----------------------------------------------------------------------


def _codigo(db: Session) -> str:
    alfabeto = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    while True:
        codigo = "".join(secrets.choice(alfabeto) for _ in range(8))
        if not db.scalar(select(RemisionAliada.id).where(RemisionAliada.codigo == codigo)):
            return codigo


def emitir(
    db: Session,
    *,
    clinica_id: UUID,
    mascota_id: UUID,
    motivo: str,
    usuario_id: UUID,
    convenio_id: UUID | None = None,
) -> RemisionAliada:
    """Valida plan vigente, cartera al dia y beneficio disponible (las mismas reglas de
    elegibilidad que el agendamiento) y que la aliada tenga convenio vigente para el plan.
    La remision consume el cupo del beneficio como cualquier servicio."""
    from app.modules.planes import service as planes
    from app.modules.servicios import service as servicios

    clinica = obtener_clinica(db, clinica_id)
    if not clinica.activa:
        raise ReglaNegocio("La clinica aliada no esta activa")
    mascota = db.get(Mascota, mascota_id)
    if mascota is None:
        raise NoEncontrado("Mascota no encontrada")
    familia = db.get(Familia, mascota.familia_id)
    assert familia is not None
    tipo = servicios.tipo_servicio(db, TIPO_SERVICIO_ALIADA)
    elegibilidad = servicios.elegibilidad(db, familia, mascota, tipo)
    if not elegibilidad.elegible:
        raise ReglaNegocio("No se puede remitir: " + "; ".join(elegibilidad.motivos))
    contrato = planes.contrato_vigente(db, familia.id)
    assert contrato is not None  # la elegibilidad ya lo exige

    vigentes = convenios_vigentes(db, clinica.id, contrato.plan_id, hoy())
    if convenio_id is not None:
        vigentes = [c for c in vigentes if c.id == convenio_id]
    if not vigentes:
        raise ReglaNegocio(f"{clinica.nombre} no tiene convenio vigente para el plan de la familia")
    convenio = vigentes[0]

    servicio = Servicio(
        familia_id=familia.id,
        mascota_id=mascota.id,
        tipo_codigo=tipo.codigo,
        tipo=TipoServicio.ALIADA,
        ciudad=clinica.ciudad,
        # La fecha de emision cuenta para el cupo del beneficio del periodo.
        programado_para=ahora(),
        requiere_autorizacion=True,
        # Emitir la remision ES la autorizacion: queda registrada quien la dio.
        autorizado=True,
        autorizado_por_id=usuario_id,
        autorizado_en=ahora(),
        observaciones=f"Remision a {clinica.nombre}: {motivo}",
        estado=EstadoServicio.SOLICITADO,
    )
    db.add(servicio)
    db.flush()
    servicios.cambiar_estado(db, servicio, EstadoServicio.AGENDADO, actor_id=usuario_id)

    remision = RemisionAliada(
        codigo=_codigo(db),
        clinica_id=clinica.id,
        convenio_id=convenio.id,
        familia_id=familia.id,
        mascota_id=mascota.id,
        servicio_id=servicio.id,
        motivo=motivo,
        beneficio_aplicado=convenio.beneficio,
        cobertura_pct=convenio.cobertura_pct,
        tope_cubierto=convenio.tope_cubierto,
        vence_en=hoy() + timedelta(days=settings.REMISION_VIGENCIA_DIAS),
        emitida_por_id=usuario_id,
    )
    db.add(remision)
    db.flush()
    return remision


def obtener_remision(db: Session, remision_id: UUID) -> RemisionAliada:
    remision = db.get(RemisionAliada, remision_id)
    if remision is None:
        raise NoEncontrado("Remision no encontrada")
    return remision


def anular(db: Session, remision: RemisionAliada, motivo: str, usuario_id: UUID) -> RemisionAliada:
    """Libera el cupo: el servicio se cancela."""
    from app.modules.servicios import service as servicios

    if remision.estado != "emitida":
        raise ReglaNegocio("Solo se anula una remision emitida y no utilizada")
    remision.estado = "anulada"
    remision.motivo_anulacion = motivo
    servicio = db.get(Servicio, remision.servicio_id)
    assert servicio is not None
    servicios.cambiar_estado(
        db, servicio, EstadoServicio.CANCELADO, f"Remision anulada: {motivo}", actor_id=usuario_id
    )
    db.flush()
    return remision


# --- F2-ALI-03 Acceso de la aliada ------------------------------------------------------------


def _de_la_clinica(db: Session, codigo: str, clinica_id: UUID) -> RemisionAliada:
    """Una remision de otra clinica da el mismo 404 que una inexistente."""
    remision = db.scalar(
        select(RemisionAliada).where(RemisionAliada.codigo == codigo.strip().upper())
    )
    if remision is None or remision.clinica_id != clinica_id:
        raise NoEncontrado("Remision no encontrada")
    return remision


def vista_aliada(db: Session, codigo: str, clinica_id: UUID) -> dict[str, Any]:
    """Lo minimo para atender: a quien (nombre del titular y ultimos digitos del documento
    para verificar identidad), que mascota y que cubre. Nada de contacto, direccion,
    cartera ni historia clinica."""
    remision = _de_la_clinica(db, codigo, clinica_id)
    familia = db.get(Familia, remision.familia_id)
    mascota = db.get(Mascota, remision.mascota_id)
    assert familia is not None and mascota is not None
    vigente = remision.estado == "emitida" and remision.vence_en >= hoy()
    return {
        "codigo": remision.codigo,
        "estado": remision.estado,
        "vigente": vigente,
        "vence_en": remision.vence_en,
        "titular": familia.titular_nombre,
        "documento_ultimos": familia.documento[-4:],
        "mascota": {"nombre": mascota.nombre, "especie": mascota.especie, "raza": mascota.raza},
        "motivo": remision.motivo,
        "beneficio": remision.beneficio_aplicado,
        "cobertura_pct": remision.cobertura_pct,
        "tope_cubierto": remision.tope_cubierto,
        "valor_cubierto": remision.valor_cubierto,
    }


def reportar_atencion(
    db: Session,
    codigo: str,
    clinica_id: UUID,
    *,
    fecha: date,
    valor_atencion: Decimal,
    resumen: str,
    usuario_id: UUID,
) -> RemisionAliada:
    """La aliada reporta la atencion: se calcula lo cubierto (porcentaje y tope del
    convenio) y el servicio se completa."""
    from app.modules.servicios import service as servicios

    remision = _de_la_clinica(db, codigo, clinica_id)
    if remision.estado != "emitida":
        raise ReglaNegocio("La remision ya fue utilizada o anulada")
    if fecha > hoy():
        raise ReglaNegocio("La fecha de atencion no puede ser futura")
    emitida = con_zona(remision.created_at).astimezone(ZONA_NEGOCIO).date()
    if fecha > remision.vence_en or fecha < emitida:
        raise ReglaNegocio("La atencion esta fuera de la vigencia de la remision")
    cubierto = dinero(dinero(valor_atencion) * remision.cobertura_pct / 100)
    if remision.tope_cubierto is not None:
        cubierto = min(cubierto, dinero(remision.tope_cubierto))
    remision.estado = "utilizada"
    remision.fecha_atencion = fecha
    remision.valor_atencion = dinero(valor_atencion)
    remision.valor_cubierto = cubierto
    remision.resumen_atencion = resumen
    remision.reportada_por_id = usuario_id
    remision.reportada_en = ahora()
    servicio = db.get(Servicio, remision.servicio_id)
    assert servicio is not None
    servicios.cambiar_estado(db, servicio, EstadoServicio.EN_ATENCION, actor_id=usuario_id)
    servicios.cambiar_estado(db, servicio, EstadoServicio.COMPLETADO, actor_id=usuario_id)
    db.flush()
    return remision


# --- F2-ALI-04 Liquidacion --------------------------------------------------------------------


def liquidacion(
    db: Session, desde: date, hasta: date, clinica_id: UUID | None = None
) -> list[dict[str, Any]]:
    """Por aliada: atenciones del periodo, valor facturado, valor cubierto por TIMU (el
    saldo a pagar) y lo que asume la familia."""
    if hasta < desde:
        raise ReglaNegocio("El periodo termina antes de empezar")
    stmt = (
        select(RemisionAliada, ClinicaAliada)
        .join(ClinicaAliada, ClinicaAliada.id == RemisionAliada.clinica_id)
        .where(
            RemisionAliada.estado == "utilizada",
            RemisionAliada.fecha_atencion >= desde,
            RemisionAliada.fecha_atencion <= hasta,
        )
        .order_by(ClinicaAliada.nombre, RemisionAliada.fecha_atencion)
    )
    if clinica_id:
        stmt = stmt.where(RemisionAliada.clinica_id == clinica_id)
    resumen: dict[UUID, dict[str, Any]] = {}
    for remision, clinica in db.execute(stmt).tuples():
        fila = resumen.setdefault(
            clinica.id,
            {
                "clinica_id": clinica.id,
                "clinica": clinica.nombre,
                "nit": clinica.nit,
                "atenciones": 0,
                "valor_atenciones": dinero(0),
                "valor_cubierto": dinero(0),
                "valor_familias": dinero(0),
                "detalle": [],
            },
        )
        valor = dinero(remision.valor_atencion)
        cubierto = dinero(remision.valor_cubierto)
        fila["atenciones"] += 1
        fila["valor_atenciones"] += valor
        fila["valor_cubierto"] += cubierto
        fila["valor_familias"] += valor - cubierto
        fila["detalle"].append(
            {
                "codigo": remision.codigo,
                "fecha_atencion": remision.fecha_atencion,
                "beneficio": remision.beneficio_aplicado,
                "valor_atencion": valor,
                "valor_cubierto": cubierto,
            }
        )
    for fila in resumen.values():
        fila["saldo_a_pagar"] = fila["valor_cubierto"]
    return list(resumen.values())

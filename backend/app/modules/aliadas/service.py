"""6.22 Clinicas aliadas: convenios, remisiones, validacion por la aliada y liquidacion."""

import secrets
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import EstadoServicio, TipoServicio
from app.core.errores import NoEncontrado, ReglaNegocio
from app.core.tiempo import ZONA_NEGOCIO, ahora, con_zona, hoy
from app.modules.aliadas.models import ClinicaAliada, ConvenioAliada, RemisionAliada
from app.modules.cartera import contratos
from app.modules.cartera.periodos import dinero
from app.modules.catalogos.models import Especie
from app.modules.familias.models import Familia, Mascota
from app.modules.planes.models import Plan
from app.modules.servicios import service as servicios
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
    # La elegibilidad ya exige que la mascota este afiliada: su plan decide el convenio.
    plan = contratos.plan_de_mascota(db, mascota.id)
    assert plan is not None

    vigentes = convenios_vigentes(db, clinica.id, plan.id, hoy())
    if convenio_id is not None:
        vigentes = [c for c in vigentes if c.id == convenio_id]
    if not vigentes:
        raise ReglaNegocio(f"{clinica.nombre} no tiene convenio vigente para el plan {plan.nombre}")
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


def quienes(db: Session, remisiones: list[RemisionAliada]) -> dict[UUID, dict[str, str]]:
    """El titular, la mascota y la clinica de cada remision, en tres consultas: la bandeja dice de
    quien es cada una sin pedir una familia por fila."""

    def nombres(columna_id: Any, columna: Any, ids: set[UUID]) -> dict[UUID, str]:
        if not ids:
            return {}
        return dict(
            db.execute(select(columna_id, columna).where(columna_id.in_(ids))).tuples().all()
        )

    titulares = nombres(Familia.id, Familia.titular_nombre, {r.familia_id for r in remisiones})
    mascotas = nombres(Mascota.id, Mascota.nombre, {r.mascota_id for r in remisiones})
    clinicas = nombres(ClinicaAliada.id, ClinicaAliada.nombre, {r.clinica_id for r in remisiones})
    return {
        r.id: {
            "titular": titulares.get(r.familia_id, ""),
            "mascota": mascotas.get(r.mascota_id, ""),
            "clinica": clinicas.get(r.clinica_id, ""),
        }
        for r in remisiones
    }


def recuentos(db: Session, clinica_id: UUID | None = None) -> dict[str, int]:
    """Cuantas remisiones hay en cada estado (las vistas de la bandeja) y en total."""

    stmt = select(RemisionAliada.estado, func.count()).group_by(RemisionAliada.estado)
    if clinica_id:
        stmt = stmt.where(RemisionAliada.clinica_id == clinica_id)
    por_estado = dict(db.execute(stmt).tuples().all())
    conteo = {e: por_estado.get(e, 0) for e in ("emitida", "utilizada", "anulada")}
    return {**conteo, "todas": sum(conteo.values())}


def anular(db: Session, remision: RemisionAliada, motivo: str, usuario_id: UUID) -> RemisionAliada:
    """Libera el cupo: el servicio se cancela."""

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


def cubre(remision: RemisionAliada, valor_atencion: Decimal) -> tuple[Decimal, Decimal]:
    """Lo que cubre TIMU de una atencion (porcentaje y tope de la remision) y lo que asume la
    familia. La misma cuenta al reportar y al mostrarla antes, para que no se digan dos cifras."""
    valor = dinero(valor_atencion)
    cubierto = dinero(valor * remision.cobertura_pct / 100)
    if remision.tope_cubierto is not None:
        cubierto = min(cubierto, dinero(remision.tope_cubierto))
    return cubierto, valor - cubierto


def vista_aliada(db: Session, codigo: str, clinica_id: UUID) -> dict[str, Any]:
    """Lo minimo para atender: a quien (nombre del titular y ultimos digitos del documento
    para verificar identidad), que mascota y que cubre. Nada de contacto, direccion,
    cartera ni historia clinica. Dice si sirve y, si sirve, entre que fechas se puede
    reportar la atencion; si ya se uso, cuando y cuanto."""
    remision = _de_la_clinica(db, codigo, clinica_id)
    familia = db.get(Familia, remision.familia_id)
    mascota = db.get(Mascota, remision.mascota_id)
    assert familia is not None and mascota is not None
    especie = db.scalar(select(Especie.nombre).where(Especie.codigo == mascota.especie))
    emitida = con_zona(remision.created_at).astimezone(ZONA_NEGOCIO).date()
    vigente = remision.estado == "emitida" and remision.vence_en >= hoy()
    familia_asume = (
        remision.valor_atencion - remision.valor_cubierto
        if remision.valor_atencion is not None and remision.valor_cubierto is not None
        else None
    )
    return {
        "codigo": remision.codigo,
        "estado": remision.estado,
        "vigente": vigente,
        "vencida": remision.estado == "emitida" and not vigente,
        "vence_en": remision.vence_en,
        "emitida_en": emitida,
        "atencion_desde": emitida if vigente else None,
        "atencion_hasta": min(remision.vence_en, hoy()) if vigente else None,
        "titular": familia.titular_nombre,
        "documento_ultimos": familia.documento[-4:],
        "mascota": {
            "nombre": mascota.nombre,
            "especie": mascota.especie,
            "especie_nombre": especie or mascota.especie,
            "raza": mascota.raza,
        },
        "motivo": remision.motivo,
        "beneficio": remision.beneficio_aplicado,
        "cobertura_pct": remision.cobertura_pct,
        "tope_cubierto": remision.tope_cubierto,
        "fecha_atencion": remision.fecha_atencion,
        "valor_atencion": remision.valor_atencion,
        "valor_cubierto": remision.valor_cubierto,
        "valor_familia": familia_asume,
    }


def cobertura_de(
    db: Session, codigo: str, clinica_id: UUID, valor_atencion: Decimal
) -> dict[str, Any]:
    """Lo que cubriria TIMU de `valor_atencion` con esta remision, antes de reportarla."""
    remision = _de_la_clinica(db, codigo, clinica_id)
    cubierto, familia = cubre(remision, valor_atencion)
    return {
        "valor_atencion": dinero(valor_atencion),
        "valor_cubierto": cubierto,
        "valor_familia": familia,
        "con_tope": remision.tope_cubierto is not None
        and cubierto == dinero(remision.tope_cubierto),
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

    remision = _de_la_clinica(db, codigo, clinica_id)
    if remision.estado != "emitida":
        raise ReglaNegocio("La remision ya fue utilizada o anulada")
    if fecha > hoy():
        raise ReglaNegocio("La fecha de atencion no puede ser futura")
    emitida = con_zona(remision.created_at).astimezone(ZONA_NEGOCIO).date()
    if fecha > remision.vence_en or fecha < emitida:
        raise ReglaNegocio("La atencion esta fuera de la vigencia de la remision")
    cubierto, _ = cubre(remision, valor_atencion)
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


def mi_clinica(db: Session, clinica_id: UUID) -> ClinicaAliada:
    """La clinica de quien ingresa: el espacio de la aliada dice en cual esta."""
    return obtener_clinica(db, clinica_id)


def atendidas(db: Session, clinica_id: UUID, desde: date, hasta: date) -> dict[str, Any]:
    """Lo que la clinica reporto en el periodo, de lo mas reciente a lo mas antiguo, con lo
    que cubrio TIMU y lo que asumieron las familias: lo mismo que suma la liquidacion."""
    if hasta < desde:
        raise ReglaNegocio("El periodo termina antes de empezar")
    filas = db.execute(
        select(RemisionAliada, Familia.titular_nombre, Mascota.nombre)
        .join(Familia, Familia.id == RemisionAliada.familia_id)
        .join(Mascota, Mascota.id == RemisionAliada.mascota_id)
        .where(
            RemisionAliada.clinica_id == clinica_id,
            RemisionAliada.estado == "utilizada",
            RemisionAliada.fecha_atencion >= desde,
            RemisionAliada.fecha_atencion <= hasta,
        )
        .order_by(RemisionAliada.fecha_atencion.desc(), RemisionAliada.id.desc())
    ).tuples()
    items = []
    for remision, titular, mascota in filas:
        assert remision.valor_atencion is not None and remision.valor_cubierto is not None
        items.append(
            {
                "codigo": remision.codigo,
                "fecha_atencion": remision.fecha_atencion,
                "titular": titular,
                "mascota": mascota,
                "motivo": remision.motivo,
                "beneficio": remision.beneficio_aplicado,
                "valor_atencion": remision.valor_atencion,
                "valor_cubierto": remision.valor_cubierto,
                "valor_familia": remision.valor_atencion - remision.valor_cubierto,
            }
        )
    return {
        "desde": desde,
        "hasta": hasta,
        "atenciones": len(items),
        "valor_atenciones": dinero(sum((i["valor_atencion"] for i in items), Decimal(0))),
        "valor_cubierto": dinero(sum((i["valor_cubierto"] for i in items), Decimal(0))),
        "valor_familias": dinero(sum((i["valor_familia"] for i in items), Decimal(0))),
        "items": items,
    }


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

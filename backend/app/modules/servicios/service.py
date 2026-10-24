"""6.5 / 6.6 / 6.10 Programacion de servicios, elegibilidad, estados y pendientes."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.enums import EstadoAfiliacion, EstadoServicio
from app.core.errores import NoEncontrado, ReglaNegocio
from app.core.tiempo import ZONA_NEGOCIO, ahora, con_zona, hoy
from app.modules.catalogos.models import TipoServicioCatalogo
from app.modules.familias.models import Familia, Mascota
from app.modules.planes import service as planes
from app.modules.planes.models import Beneficio
from app.modules.reglas import service as reglas
from app.modules.servicios.models import (
    BloqueoAgenda,
    EstadoPendiente,
    Franja,
    Pendiente,
    Servicio,
    ServicioPaso,
)
from app.modules.servicios.state_machine import TransicionInvalida, aplicar, transicionar

logger = structlog.get_logger(__name__)

# Estados que ocupan cupo en la agenda.
OCUPAN_CUPO = (
    EstadoServicio.AGENDADO,
    EstadoServicio.PENDIENTE_AUTORIZACION,
    EstadoServicio.EN_RUTA,
    EstadoServicio.EN_ATENCION,
)


def tipo_servicio(db: Session, codigo: str) -> TipoServicioCatalogo:
    tipo = db.scalar(
        select(TipoServicioCatalogo).where(
            TipoServicioCatalogo.codigo == codigo, TipoServicioCatalogo.activo.is_(True)
        )
    )
    if tipo is None:
        raise NoEncontrado(f"Tipo de servicio '{codigo}' inexistente o inactivo")
    return tipo


def obtener(db: Session, servicio_id: UUID) -> Servicio:
    servicio = db.get(Servicio, servicio_id)
    if servicio is None:
        raise NoEncontrado("Servicio no encontrado")
    return servicio


# --- F1-SER-05 Elegibilidad -------------------------------------------------------------


@dataclass
class Elegibilidad:
    elegible: bool
    motivos: list[str]


def elegibilidad(
    db: Session, familia: Familia, mascota: Mascota | None, tipo: TipoServicioCatalogo
) -> Elegibilidad:
    """Plan vigente, afiliacion activa, cartera al dia, mascota valida, beneficio con cupo y
    reglas adicionales `servicio.elegibilidad`. Devuelve todos los motivos, no solo el primero,
    para que quien agenda sepa que resolver."""
    motivos: list[str] = []
    if familia.dada_de_baja_en is not None:
        return Elegibilidad(False, ["La familia esta dada de baja"])
    contrato = planes.contrato_vigente(db, familia.id)
    if contrato is None:
        return Elegibilidad(False, ["La familia no tiene un plan vigente"])
    if contrato.fecha_renovacion < hoy():
        motivos.append(f"El plan vencio el {contrato.fecha_renovacion:%d/%m/%Y} y no se renovo")
    if contrato.estado == EstadoAfiliacion.CONGELADA:
        motivos.append("La afiliacion esta congelada por mora: se reactiva al ponerse al dia")
    elif contrato.estado == EstadoAfiliacion.EN_MORA:
        motivos.append("La familia tiene cartera vencida")
    if mascota is not None:
        if mascota.familia_id != familia.id:
            motivos.append("La mascota no pertenece a la familia")
        elif not mascota.activa:
            motivos.append(f"{mascota.nombre} esta dada de baja")

    plan = planes.obtener(db, contrato.plan_id)
    beneficio = next((b for b in plan.beneficios if b.tipo_servicio_codigo == tipo.codigo), None)
    if plan.beneficios and beneficio is None:
        motivos.append(f"El plan {plan.nombre} no incluye {tipo.nombre}")
    elif beneficio is not None and beneficio.cupo is not None:
        usados = _usos(db, familia.id, beneficio)
        if usados >= beneficio.cupo:
            periodo = "mes" if beneficio.periodo_cupo == "mensual" else "ano"
            motivos.append(f"Se agoto el cupo de {tipo.nombre} ({beneficio.cupo} por {periodo})")

    contexto = {
        "familia": {"ciudad": familia.ciudad, "estado": familia.estado},
        "plan": {"codigo": plan.codigo},
        "servicio": {"tipo": tipo.codigo, "modalidad": tipo.modalidad},
        "mascota": {"especie": mascota.especie if mascota else None},
    }
    for r in reglas.evaluar(db, "servicio.elegibilidad", contexto, plan_id=plan.id):
        motivos.append(r.accion["motivo"])
    return Elegibilidad(not motivos, motivos)


def _usos(db: Session, familia_id: UUID, beneficio: Beneficio) -> int:
    dia = hoy()
    mensual = beneficio.periodo_cupo == "mensual"
    desde = dia.replace(day=1) if mensual else dia.replace(month=1, day=1)
    inicio = datetime.combine(desde, time.min, ZONA_NEGOCIO)
    return int(
        db.scalar(
            select(func.count())
            .select_from(Servicio)
            .where(
                Servicio.familia_id == familia_id,
                Servicio.tipo_codigo == beneficio.tipo_servicio_codigo,
                Servicio.estado != EstadoServicio.CANCELADO,
                Servicio.programado_para >= _utc(inicio),
            )
        )
        or 0
    )


# --- F1-SER-01 Disponibilidad y agendamiento -------------------------------------------------


def _local(dt: datetime) -> datetime:
    return con_zona(dt).astimezone(ZONA_NEGOCIO)


def _entrada(dt: datetime) -> datetime:
    """Hora recibida del usuario: sin zona se entiende como hora de Colombia."""
    return dt.replace(tzinfo=ZONA_NEGOCIO) if dt.tzinfo is None else dt


def _utc(dt: datetime) -> datetime:
    """Todo instante se guarda y se compara en UTC; la agenda se piensa en hora local."""
    return con_zona(dt)


def _bloqueado(db: Session, dia: date, ciudad: str, modalidad: str) -> BloqueoAgenda | None:
    return db.scalar(
        select(BloqueoAgenda).where(
            BloqueoAgenda.fecha == dia,
            or_(BloqueoAgenda.ciudad.is_(None), BloqueoAgenda.ciudad == ciudad),
            or_(BloqueoAgenda.modalidad.is_(None), BloqueoAgenda.modalidad == modalidad),
        )
    )


def _franjas(db: Session, dia: date, ciudad: str, modalidad: str) -> list[Franja]:
    return list(
        db.scalars(
            select(Franja)
            .where(
                Franja.ciudad == ciudad,
                Franja.modalidad == modalidad,
                Franja.dia_semana == dia.weekday(),
                Franja.activa.is_(True),
            )
            .order_by(Franja.hora_inicio)
        )
    )


def _ocupados(
    db: Session, franja_id: UUID, inicio: datetime, fin: datetime, excluir: UUID | None = None
) -> int:
    stmt = (
        select(func.count())
        .select_from(Servicio)
        .where(
            Servicio.franja_id == franja_id,
            Servicio.estado.in_(OCUPAN_CUPO),
            and_(Servicio.programado_para < _utc(fin), Servicio.termina_en > _utc(inicio)),
        )
    )
    if excluir:
        stmt = stmt.where(Servicio.id != excluir)
    return int(db.scalar(stmt) or 0)


@dataclass
class Cupo:
    inicio: datetime
    fin: datetime
    disponibles: int


def disponibilidad(db: Session, dia: date, ciudad: str, tipo: TipoServicioCatalogo) -> list[Cupo]:
    if _bloqueado(db, dia, ciudad, tipo.modalidad):
        return []
    duracion = timedelta(minutes=tipo.duracion_min)
    limite_pasado = ahora()
    cupos = []
    for franja in _franjas(db, dia, ciudad, tipo.modalidad):
        inicio = datetime.combine(dia, franja.hora_inicio, ZONA_NEGOCIO)
        cierre = datetime.combine(dia, franja.hora_fin, ZONA_NEGOCIO)
        while inicio + duracion <= cierre:
            if inicio > limite_pasado:
                libres = franja.capacidad - _ocupados(db, franja.id, inicio, inicio + duracion)
                cupos.append(Cupo(inicio, inicio + duracion, max(libres, 0)))
            inicio += duracion
    return cupos


def _reservar(
    db: Session,
    ciudad: str,
    tipo: TipoServicioCatalogo,
    inicio: datetime,
    excluir: UUID | None = None,
) -> tuple[Franja, datetime]:
    """Valida que haya cupo real en [inicio, inicio+duracion] y bloquea la franja hasta el
    commit, para que dos agendamientos simultaneos no tomen el mismo cupo."""
    local = _local(inicio)
    if local <= ahora():
        raise ReglaNegocio("No se puede agendar en el pasado")
    fin = local + timedelta(minutes=tipo.duracion_min)
    bloqueo = _bloqueado(db, local.date(), ciudad, tipo.modalidad)
    if bloqueo:
        raise ReglaNegocio(f"No hay atencion ese dia: {bloqueo.motivo}")
    for franja in _franjas(db, local.date(), ciudad, tipo.modalidad):
        dentro = franja.hora_inicio <= local.time() and fin.time() <= franja.hora_fin
        if dentro and fin.date() == local.date():
            bloqueada = db.get(Franja, franja.id, with_for_update=True, populate_existing=True)
            assert bloqueada is not None
            if _ocupados(db, bloqueada.id, local, fin, excluir) >= bloqueada.capacidad:
                raise ReglaNegocio("Ese horario ya no tiene cupo; elija otro")
            return bloqueada, fin
    raise ReglaNegocio("No hay agenda disponible para ese horario, ciudad y tipo de servicio")


def agendar(
    db: Session,
    *,
    familia: Familia,
    mascota: Mascota | None,
    tipo: TipoServicioCatalogo,
    inicio: datetime,
    observaciones: str | None = None,
    pendiente: Pendiente | None = None,
) -> Servicio:
    inicio = _entrada(inicio)
    resultado = elegibilidad(db, familia, mascota, tipo)
    if not resultado.elegible:
        raise ReglaNegocio("No se puede agendar: " + "; ".join(resultado.motivos))
    franja, fin = _reservar(db, familia.ciudad, tipo, inicio)
    servicio = Servicio(
        familia_id=familia.id,
        mascota_id=mascota.id if mascota else None,
        tipo_codigo=tipo.codigo,
        tipo=tipo.modalidad,
        ciudad=familia.ciudad,
        programado_para=_utc(inicio),
        termina_en=_utc(fin),
        franja_id=franja.id,
        requiere_autorizacion=tipo.requiere_autorizacion,
        pendiente_origen_id=pendiente.id if pendiente else None,
        observaciones=observaciones,
        estado=EstadoServicio.SOLICITADO,
    )
    db.add(servicio)
    db.flush()
    destino = (
        EstadoServicio.PENDIENTE_AUTORIZACION
        if tipo.requiere_autorizacion
        else EstadoServicio.AGENDADO
    )
    cambiar_estado(db, servicio, destino)
    return servicio


def reprogramar(db: Session, servicio: Servicio, nuevo_inicio: datetime, motivo: str) -> Servicio:
    nuevo_inicio = _entrada(nuevo_inicio)
    tipo = tipo_servicio(db, servicio.tipo_codigo)
    franja, fin = _reservar(db, servicio.ciudad, tipo, nuevo_inicio, excluir=servicio.id)
    cambiar_estado(db, servicio, EstadoServicio.REPROGRAMADO, motivo)
    servicio.programado_para = _utc(nuevo_inicio)
    servicio.termina_en = _utc(fin)
    servicio.franja_id = franja.id
    # Reprogramado solo sale a agendado; si faltaba autorizacion, se sigue exigiendo antes
    # de pasar a ruta o atencion.
    cambiar_estado(db, servicio, EstadoServicio.AGENDADO)
    return servicio


# --- F1-SER-03 Estados con disparadores -----------------------------------------------------


def cambiar_estado(
    db: Session,
    servicio: Servicio,
    destino: EstadoServicio,
    motivo: str | None = None,
    *,
    actor_id: UUID | None = None,
) -> Servicio:
    """Valida la transicion (6.10) y sus requisitos, la registra (auditoria) y ejecuta las
    reglas `servicio.transicion` (tareas y mensajes)."""
    anterior = EstadoServicio(servicio.estado)
    try:
        transicionar(anterior, destino)
    except TransicionInvalida as e:
        raise ReglaNegocio(f"No se puede pasar de {anterior} a {destino}") from e
    if destino in (EstadoServicio.EN_RUTA, EstadoServicio.EN_ATENCION):
        if servicio.requiere_autorizacion and not servicio.autorizado:
            raise ReglaNegocio("El servicio requiere autorizacion registrada antes de atenderse")
    if destino == EstadoServicio.COMPLETADO:
        faltantes = pasos_faltantes(db, servicio)
        if faltantes:
            raise ReglaNegocio("Faltan pasos obligatorios: " + ", ".join(faltantes))
    if destino in (EstadoServicio.CANCELADO, EstadoServicio.REPROGRAMADO) and not motivo:
        raise ReglaNegocio("Indique el motivo")
    # `aplicar` cambia el estado y deja el evento servicio.<estado> en el outbox (6.10).
    aplicar(db, servicio, destino, actor_id=actor_id)
    servicio.motivo_estado = motivo
    db.flush()
    _disparadores(db, servicio, anterior, destino)
    return servicio


def _disparadores(
    db: Session, servicio: Servicio, anterior: EstadoServicio, destino: EstadoServicio
) -> None:
    from app.modules.comunicaciones import service as comunicaciones
    from app.modules.tareas import service as tareas

    familia = db.get(Familia, servicio.familia_id)
    assert familia is not None
    contexto = {
        "estado_anterior": anterior.value,
        "estado_nuevo": destino.value,
        "servicio": {"tipo": servicio.tipo_codigo, "modalidad": servicio.tipo},
        "familia": {"ciudad": familia.ciudad, "estado": familia.estado},
    }
    for r in reglas.evaluar(db, "servicio.transicion", contexto):
        if r.accion["tipo"] == "tarea":
            tareas.desde_accion(
                db,
                r.accion,
                r.regla,
                familia_id=familia.id,
                servicio_id=servicio.id,
            )
        elif r.accion["tipo"] == "notificar":
            fecha = (
                f"{_local(servicio.programado_para):%d/%m/%Y %I:%M %p}"
                if servicio.programado_para
                else ""
            )
            try:
                comunicaciones.encolar_plantilla(
                    db,
                    telefono=familia.telefono,
                    plantilla=r.accion["plantilla"],
                    variables=[familia.titular_nombre, fecha],
                    familia_id=familia.id,
                )
            except ReglaNegocio as e:
                logger.error("Disparador %s sin enviar: %s", r.regla, e)


def autorizar(db: Session, servicio: Servicio, usuario_id: UUID) -> Servicio:
    if not servicio.requiere_autorizacion:
        raise ReglaNegocio("El servicio no requiere autorizacion")
    if servicio.autorizado:
        return servicio
    servicio.autorizado = True
    servicio.autorizado_por_id = usuario_id
    servicio.autorizado_en = ahora()
    if servicio.estado == EstadoServicio.PENDIENTE_AUTORIZACION:
        cambiar_estado(db, servicio, EstadoServicio.AGENDADO)
    db.flush()
    return servicio


# --- F1-SER-02 Pasos configurables --------------------------------------------------------


def pasos_faltantes(db: Session, servicio: Servicio) -> list[str]:
    tipo = tipo_servicio(db, servicio.tipo_codigo)
    hechos = set(
        db.scalars(select(ServicioPaso.paso_codigo).where(ServicioPaso.servicio_id == servicio.id))
    )
    return [p["nombre"] for p in tipo.pasos if p.get("obligatorio") and p["codigo"] not in hechos]


def completar_paso(
    db: Session,
    servicio: Servicio,
    paso_codigo: str,
    datos: dict[str, Any],
    usuario_id: UUID,
) -> ServicioPaso:
    if servicio.estado != EstadoServicio.EN_ATENCION:
        raise ReglaNegocio("Los pasos se registran durante la atencion")
    tipo = tipo_servicio(db, servicio.tipo_codigo)
    paso = next((p for p in tipo.pasos if p["codigo"] == paso_codigo), None)
    if paso is None:
        raise NoEncontrado(f"El tipo {tipo.nombre} no tiene el paso '{paso_codigo}'")
    faltantes = [c for c in paso.get("campos", []) if not datos.get(c)]
    if faltantes:
        raise ReglaNegocio(f"El paso {paso['nombre']} requiere: {', '.join(faltantes)}")
    existente = db.scalar(
        select(ServicioPaso).where(
            ServicioPaso.servicio_id == servicio.id, ServicioPaso.paso_codigo == paso_codigo
        )
    )
    if existente:
        existente.datos = datos
        existente.completado_por_id = usuario_id
        db.flush()
        return existente
    registro = ServicioPaso(
        servicio_id=servicio.id, paso_codigo=paso_codigo, datos=datos, completado_por_id=usuario_id
    )
    db.add(registro)
    db.flush()
    return registro


# --- F1-SER-04 Pendientes ------------------------------------------------------------------

_SIGUIENTE_PENDIENTE = {
    EstadoPendiente.AUTORIZADO: (EstadoPendiente.EN_GESTION, EstadoPendiente.RESUELTO),
    EstadoPendiente.EN_GESTION: (EstadoPendiente.RESUELTO,),
}


def crear_pendiente(
    db: Session, servicio: Servicio, descripcion: str, requiere_autorizacion: bool
) -> Pendiente:
    pendiente = Pendiente(
        servicio_origen_id=servicio.id,
        descripcion=descripcion,
        requiere_autorizacion=requiere_autorizacion,
        estado=(
            EstadoPendiente.PENDIENTE_AUTORIZACION
            if requiere_autorizacion
            else EstadoPendiente.AUTORIZADO
        ),
    )
    db.add(pendiente)
    db.flush()
    return pendiente


def obtener_pendiente(db: Session, pendiente_id: UUID) -> Pendiente:
    pendiente = db.get(Pendiente, pendiente_id)
    if pendiente is None:
        raise NoEncontrado("Pendiente no encontrado")
    return pendiente


def autorizar_pendiente(
    db: Session, pendiente: Pendiente, usuario_id: UUID, medio: str, aprobado: bool
) -> Pendiente:
    """Registra la autorizacion (o el rechazo) de la familia, con quien la tomo y por que medio."""
    if pendiente.estado != EstadoPendiente.PENDIENTE_AUTORIZACION:
        raise ReglaNegocio("El pendiente no esta esperando autorizacion")
    pendiente.estado = EstadoPendiente.AUTORIZADO if aprobado else EstadoPendiente.RECHAZADO
    pendiente.autorizado_por_id = usuario_id
    pendiente.autorizado_en = ahora()
    pendiente.medio_autorizacion = medio
    db.flush()
    return pendiente


def avanzar_pendiente(
    db: Session, pendiente: Pendiente, destino: str, resolucion: str | None
) -> Pendiente:
    if pendiente.estado == EstadoPendiente.PENDIENTE_AUTORIZACION:
        raise ReglaNegocio("El pendiente no puede avanzar sin autorizacion registrada")
    if destino not in _SIGUIENTE_PENDIENTE.get(pendiente.estado, ()):
        raise ReglaNegocio(f"No se puede pasar de {pendiente.estado} a {destino}")
    pendiente.estado = destino
    if destino == EstadoPendiente.RESUELTO:
        if not resolucion:
            raise ReglaNegocio("Indique la resolucion")
        pendiente.resolucion = resolucion
        pendiente.resuelto_en = ahora()
    db.flush()
    return pendiente

"""6.20 / 6.21 Encuestas de satisfaccion, seguimiento post atencion y alertas."""

import secrets
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import EstadoServicio
from app.core.errores import NoEncontrado, ReglaNegocio
from app.core.tiempo import ZONA_NEGOCIO, ahora, con_zona
from app.modules.encuestas.models import ConfiguracionEncuesta, Encuesta
from app.modules.familias.models import Familia, Mascota
from app.modules.servicios.models import Servicio

logger = structlog.get_logger(__name__)

# Respuesta por WhatsApp: se acepta un numero de 1 a 5 dentro de este plazo desde el envio.
VENTANA_RESPUESTA = timedelta(hours=72)


def configuracion(db: Session, tipo_servicio_codigo: str) -> ConfiguracionEncuesta:
    """La del tipo de atencion o, si no hay, la general (y si no, los valores por defecto)."""
    propia = db.scalar(
        select(ConfiguracionEncuesta).where(
            ConfiguracionEncuesta.tipo_servicio_codigo == tipo_servicio_codigo
        )
    )
    if propia is not None:
        return propia
    general = db.scalar(
        select(ConfiguracionEncuesta).where(ConfiguracionEncuesta.tipo_servicio_codigo.is_(None))
    )
    return general or ConfiguracionEncuesta(
        encuesta_activa=True,
        demora_horas=2,
        plantilla_encuesta="encuesta_satisfaccion",
        seguimiento_dias=None,
        plantilla_seguimiento="seguimiento_post",
        umbral_alerta=3,
    )


# --- F3-ENC-01 / 03 Programacion --------------------------------------------------------------


def programar(db: Session, servicio_id: UUID) -> list[Encuesta]:
    """Al completarse el servicio: la encuesta con la demora del tipo de atencion y, si el
    tipo lo define, el seguimiento. Repetible: no duplica por servicio y tipo."""
    servicio = db.get(Servicio, servicio_id)
    if servicio is None or servicio.estado != EstadoServicio.COMPLETADO:
        return []
    conf = configuracion(db, servicio.tipo_codigo)
    existentes = set(db.scalars(select(Encuesta.tipo).where(Encuesta.servicio_id == servicio.id)))
    creadas = []
    momento = ahora()
    pendientes: list[tuple[str, timedelta]] = []
    if conf.encuesta_activa:
        pendientes.append(("satisfaccion", timedelta(hours=conf.demora_horas)))
    if conf.seguimiento_dias:
        pendientes.append(("seguimiento", timedelta(days=conf.seguimiento_dias)))
    for tipo, demora in pendientes:
        if tipo in existentes:
            continue
        encuesta = Encuesta(
            servicio_id=servicio.id,
            familia_id=servicio.familia_id,
            responsable_id=servicio.profesional_id,
            tipo=tipo,
            token=secrets.token_urlsafe(24),
            programada_para=momento + demora,
        )
        db.add(encuesta)
        creadas.append(encuesta)
    db.flush()
    return creadas


def enviar_pendientes(db: Session, momento: datetime | None = None) -> dict[str, int]:
    """Envia las encuestas cuya hora llego. Cada envio en su savepoint: una plantilla
    faltante no frena las demas."""
    from app.modules.comunicaciones import service as comunicaciones

    momento = momento or ahora()
    resumen = {"enviadas": 0, "fallidas": 0}
    debidas = list(
        db.scalars(
            select(Encuesta)
            .where(Encuesta.estado == "pendiente", Encuesta.programada_para <= momento)
            .order_by(Encuesta.programada_para)
            .limit(500)
        )
    )
    for encuesta in debidas:
        servicio = db.get(Servicio, encuesta.servicio_id)
        familia = db.get(Familia, encuesta.familia_id)
        assert servicio is not None and familia is not None
        if familia.dada_de_baja_en is not None:
            encuesta.estado = "omitida"
            continue
        conf = configuracion(db, servicio.tipo_codigo)
        mascota = db.get(Mascota, servicio.mascota_id) if servicio.mascota_id else None
        plantilla = (
            conf.plantilla_encuesta
            if encuesta.tipo == "satisfaccion"
            else conf.plantilla_seguimiento
        )
        enlace = f"{settings.FRONTEND_URL}/encuesta/{encuesta.token}"
        try:
            with db.begin_nested():
                comunicaciones.encolar_plantilla(
                    db,
                    telefono=familia.telefono,
                    plantilla=plantilla,
                    variables=[
                        familia.titular_nombre,
                        mascota.nombre if mascota else "tu mascota",
                        enlace,
                    ],
                    familia_id=familia.id,
                )
                encuesta.estado = "enviada"
                encuesta.enviada_en = momento
            resumen["enviadas"] += 1
        except ReglaNegocio as e:
            logger.error("Encuesta %s sin enviar: %s", encuesta.id, e)
            resumen["fallidas"] += 1
    db.flush()
    return resumen


# --- F3-ENC-02 / 04 Respuestas y alertas ------------------------------------------------------


def por_token(db: Session, token: str) -> Encuesta:
    encuesta = db.scalar(select(Encuesta).where(Encuesta.token == token))
    if encuesta is None or encuesta.estado in ("pendiente", "omitida"):
        raise NoEncontrado("Encuesta no encontrada")
    return encuesta


def contexto(db: Session, token: str) -> dict[str, Any]:
    """Lo que ve quien abre el enlace: que se le pregunta y sobre que atencion. Nada mas."""
    from app.modules.catalogos.models import TipoServicioCatalogo

    encuesta = por_token(db, token)
    servicio = db.get(Servicio, encuesta.servicio_id)
    assert servicio is not None
    tipo = db.scalar(
        select(TipoServicioCatalogo.nombre).where(
            TipoServicioCatalogo.codigo == servicio.tipo_codigo
        )
    )
    mascota = db.get(Mascota, servicio.mascota_id) if servicio.mascota_id else None
    fecha = (
        con_zona(servicio.programado_para).astimezone(ZONA_NEGOCIO).date()
        if servicio.programado_para
        else None
    )
    return {
        "tipo": encuesta.tipo,
        "atencion": tipo,
        "fecha": fecha,
        "mascota": mascota.nombre if mascota else None,
        "respondida": encuesta.estado == "respondida",
    }


def responder(
    db: Session, encuesta: Encuesta, puntaje: int, comentario: str | None, canal: str
) -> Encuesta:
    if encuesta.estado == "respondida":
        raise ReglaNegocio("La encuesta ya fue respondida")
    if not 1 <= puntaje <= 5:
        raise ReglaNegocio("El puntaje va de 1 a 5")
    encuesta.puntaje = puntaje
    encuesta.comentario = comentario
    encuesta.canal_respuesta = canal
    encuesta.estado = "respondida"
    encuesta.respondida_en = ahora()
    servicio = db.get(Servicio, encuesta.servicio_id)
    assert servicio is not None
    conf = configuracion(db, servicio.tipo_codigo)
    if puntaje <= conf.umbral_alerta:
        _alertar(db, encuesta, servicio)
    db.flush()
    return encuesta


def _alertar(db: Session, encuesta: Encuesta, servicio: Servicio) -> None:
    """F3-ENC-04 Tarea inmediata de servicio al cliente con el contexto de la atencion."""
    from app.modules.auth.models import Usuario
    from app.modules.tareas import service as tareas

    responsable = db.get(Usuario, encuesta.responsable_id) if encuesta.responsable_id else None
    fecha = (
        f"{con_zona(servicio.programado_para).astimezone(ZONA_NEGOCIO):%d/%m/%Y}"
        if servicio.programado_para
        else "sin fecha"
    )
    tarea = tareas.crear(
        db,
        titulo=f"Calificacion baja ({encuesta.puntaje}/5): contactar a la familia",
        descripcion=(
            f"Atencion {servicio.tipo_codigo} del {fecha}, "
            f"atendida por {responsable.nombre if responsable else 'sin asignar'}. "
            f"Encuesta de {encuesta.tipo}. Comentario: {encuesta.comentario or '(sin comentario)'}"
        ),
        area="servicio_cliente",
        prioridad="alta",
        vence_en_dias=0,
        familia_id=encuesta.familia_id,
        servicio_id=servicio.id,
        origen="encuesta",
        clave=f"encuesta_baja:{encuesta.id}",
    )
    if tarea is not None:
        encuesta.tarea_id = tarea.id


def respuesta_whatsapp(db: Session, telefono: str, texto: str) -> Encuesta | None:
    """Si la familia contesta con un numero de 1 a 5 a una encuesta enviada hace poco, se
    toma como su respuesta. Cualquier otro texto se ignora aqui."""
    valor = texto.strip()
    if not (len(valor) == 1 and valor in "12345"):
        return None
    encuesta = db.scalar(
        select(Encuesta)
        .join(Familia, Familia.id == Encuesta.familia_id)
        .where(
            Familia.telefono == telefono,
            Encuesta.estado == "enviada",
            Encuesta.enviada_en >= ahora() - VENTANA_RESPUESTA,
        )
        .order_by(Encuesta.enviada_en.desc())
        .limit(1)
    )
    if encuesta is None:
        return None
    return responder(db, encuesta, int(valor), None, "whatsapp")


# --- Resultados -------------------------------------------------------------------------------


def resumen(db: Session, desde: date, hasta: date) -> dict[str, Any]:
    """Satisfaccion del periodo: promedio, tasa de respuesta, por responsable y por tipo."""
    from app.modules.auth.models import Usuario

    inicio = datetime.combine(desde, datetime.min.time(), ZONA_NEGOCIO)
    fin = datetime.combine(hasta + timedelta(days=1), datetime.min.time(), ZONA_NEGOCIO)
    base = select(Encuesta).where(
        Encuesta.tipo == "satisfaccion", Encuesta.enviada_en >= inicio, Encuesta.enviada_en < fin
    )
    enviadas = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    respondidas = base.where(Encuesta.estado == "respondida").subquery()
    promedio = db.scalar(select(func.avg(respondidas.c.puntaje)))
    total_resp = db.scalar(select(func.count()).select_from(respondidas)) or 0
    por_responsable = [
        {"responsable": nombre or "sin asignar", "respuestas": n, "promedio": round(float(p), 2)}
        for nombre, n, p in db.execute(
            select(Usuario.nombre, func.count(), func.avg(respondidas.c.puntaje))
            .select_from(respondidas)
            .outerjoin(Usuario, Usuario.id == respondidas.c.responsable_id)
            .group_by(Usuario.nombre)
            .order_by(func.avg(respondidas.c.puntaje))
        )
    ]
    por_tipo = [
        {"tipo_servicio": tipo, "respuestas": n, "promedio": round(float(p), 2)}
        for tipo, n, p in db.execute(
            select(Servicio.tipo_codigo, func.count(), func.avg(respondidas.c.puntaje))
            .select_from(respondidas)
            .join(Servicio, Servicio.id == respondidas.c.servicio_id)
            .group_by(Servicio.tipo_codigo)
        )
    ]
    return {
        "enviadas": enviadas,
        "respondidas": total_resp,
        "tasa_respuesta": round(total_resp / enviadas, 3) if enviadas else None,
        "promedio": round(float(promedio), 2) if promedio is not None else None,
        "por_responsable": por_responsable,
        "por_tipo_servicio": por_tipo,
    }

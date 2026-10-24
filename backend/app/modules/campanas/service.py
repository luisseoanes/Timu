"""6.16 / 6.18 Campanas masivas: creacion, previsualizacion, envio controlado,
programacion, recurrencia y resultados."""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errores import NoEncontrado, ReglaNegocio
from app.core.tiempo import ahora, con_zona
from app.modules.campanas import segmentos
from app.modules.campanas.models import (
    Campana,
    DestinatarioCampana,
    EjecucionCampana,
    Segmento,
)
from app.modules.comunicaciones.models import BajaComunicaciones, EstadoMensaje, Mensaje
from app.modules.familias.models import Familia

logger = structlog.get_logger(__name__)

FUENTES = ("titular_nombre", "mascota_nombre", "ciudad", "plan")
RECURRENCIAS = {"diaria": timedelta(days=1), "semanal": timedelta(weeks=1)}
# Se considera respuesta a la campana un mensaje entrante dentro de este plazo.
VENTANA_RESPUESTA = timedelta(hours=72)


def obtener(db: Session, campana_id: UUID) -> Campana:
    campana = db.get(Campana, campana_id)
    if campana is None:
        raise NoEncontrado("Campana no encontrada")
    return campana


def _filtros(db: Session, campana: Campana) -> segmentos.FiltrosSegmento:
    if campana.segmento_id is not None:
        segmento = db.get(Segmento, campana.segmento_id)
        if segmento is None:
            raise NoEncontrado("Segmento no encontrado")
        return segmentos.FiltrosSegmento(**segmento.filtros)
    return segmentos.FiltrosSegmento(**(campana.segmento or {}))


def _validar(db: Session, campana: Campana) -> None:
    """Plantilla aprobada y activa, y una fuente valida por cada variable."""
    from app.modules.comunicaciones import service as comunicaciones

    if campana.canal != "whatsapp":
        raise ReglaNegocio("Por ahora las campanas salen solo por WhatsApp")
    if not campana.plantilla:
        raise ReglaNegocio("La campana necesita una plantilla")
    vigente = comunicaciones.plantilla_vigente(db, campana.plantilla)
    if vigente is None:
        raise ReglaNegocio(f"La plantilla '{campana.plantilla}' no esta aprobada y activa")
    if len(campana.variables) != len(vigente.variables):
        raise ReglaNegocio(
            f"La plantilla espera {len(vigente.variables)} variables "
            f"({', '.join(vigente.variables)})"
        )
    for fuente in campana.variables:
        if fuente not in FUENTES and not fuente.startswith("texto:"):
            raise ReglaNegocio(f"Fuente de variable desconocida: {fuente}")
    _filtros(db, campana)


def guardar(
    db: Session, campana: Campana | None, datos: dict[str, Any], usuario_id: UUID | None
) -> Campana:
    if campana is None:
        # Valores explicitos: los default de columna solo se aplican al hacer flush.
        campana = Campana(
            creada_por_id=usuario_id,
            canal="whatsapp",
            variables=[],
            segmento={},
            estado="borrador",
            recurrencia="ninguna",
        )
        db.add(campana)
    elif campana.estado != "borrador":
        raise ReglaNegocio("Solo se edita una campana en borrador")
    for campo, valor in datos.items():
        setattr(campana, campo, valor)
    _validar(db, campana)
    db.flush()
    return campana


def _variables(db: Session, campana: Campana, familia: Familia) -> list[str]:
    from app.modules.planes import service as planes
    from app.modules.planes.models import Plan

    valores = []
    for fuente in campana.variables:
        if fuente.startswith("texto:"):
            valores.append(fuente.removeprefix("texto:"))
        elif fuente == "titular_nombre":
            valores.append(familia.titular_nombre)
        elif fuente == "ciudad":
            valores.append(familia.ciudad)
        elif fuente == "mascota_nombre":
            mascota = next((m for m in familia.mascotas if m.activa), None)
            valores.append(mascota.nombre if mascota else "tu mascota")
        elif fuente == "plan":
            contrato = planes.contrato_vigente(db, familia.id)
            plan = db.get(Plan, contrato.plan_id) if contrato else None
            valores.append(plan.nombre if plan else "TIMU")
    return valores


def _bajas(db: Session) -> set[str]:
    return set(db.scalars(select(BajaComunicaciones.destino)))


# --- F3-CAM-01 Previsualizacion ---------------------------------------------------------------


def previsualizar(db: Session, campana: Campana, muestra: int = 3) -> dict[str, Any]:
    """Audiencia antes de enviar: cuantas familias alcanza, cuantas se excluyen por haber
    pedido no recibir mas, y como se vera el mensaje para algunas de ellas."""
    from app.modules.comunicaciones import service as comunicaciones

    _validar(db, campana)
    filtros = _filtros(db, campana)
    familias = list(db.scalars(segmentos.consulta(filtros).order_by(Familia.titular_nombre)))
    bajas = _bajas(db)
    excluidas = [f for f in familias if f.telefono in bajas]
    vigente = comunicaciones.plantilla_vigente(db, campana.plantilla or "")
    assert vigente is not None
    ejemplos = [
        {
            "titular": f.titular_nombre,
            "mensaje": comunicaciones.render(vigente.cuerpo, _variables(db, campana, f)),
        }
        for f in familias
        if f.telefono not in bajas
    ][:muestra]
    return {
        "audiencia": len(familias),
        "excluidos_por_baja": len(excluidas),
        "se_enviaran": len(familias) - len(excluidas),
        "ejemplos": ejemplos,
    }


# --- F3-CAM-02 / 04 Lanzamiento, despacho y programacion --------------------------------------


def programar(db: Session, campana: Campana, cuando: datetime | None, recurrencia: str) -> Campana:
    """Sin fecha sale en la siguiente pasada del despachador; con fecha, en esa fecha; con
    recurrencia, se repite sin intervencion manual."""
    if campana.estado not in ("borrador", "programada"):
        raise ReglaNegocio("La campana ya salio o fue cancelada")
    if recurrencia not in ("ninguna", "mensual", *RECURRENCIAS):
        raise ReglaNegocio("Recurrencia no valida")
    _validar(db, campana)
    momento = cuando or ahora()
    campana.programada_para = momento
    campana.proxima_ejecucion = momento
    campana.recurrencia = recurrencia
    campana.estado = "programada"
    db.flush()
    return campana


def _siguiente(momento: datetime, recurrencia: str) -> datetime | None:
    if recurrencia in RECURRENCIAS:
        return momento + RECURRENCIAS[recurrencia]
    if recurrencia == "mensual":
        from app.modules.cartera.periodos import sumar_meses

        local = con_zona(momento)
        dia = sumar_meses(local.date(), 1)
        return local.replace(year=dia.year, month=dia.month, day=dia.day)
    return None


def lanzar(db: Session, campana: Campana) -> EjecucionCampana:
    """Congela la audiencia en una ejecucion. Los mensajes los encola el despachador al
    ritmo permitido; las bajas quedan excluidas con su motivo."""
    filtros = _filtros(db, campana)
    bajas = _bajas(db)
    ejecucion = EjecucionCampana(campana_id=campana.id, iniciada_en=ahora())
    db.add(ejecucion)
    db.flush()
    vistos: set[str] = set()
    for familia in db.scalars(segmentos.consulta(filtros)):
        if familia.telefono in vistos:
            continue  # dos familias con el mismo numero reciben un solo mensaje
        vistos.add(familia.telefono)
        excluida = familia.telefono in bajas
        db.add(
            DestinatarioCampana(
                ejecucion_id=ejecucion.id,
                familia_id=familia.id,
                telefono=familia.telefono,
                estado="excluido" if excluida else "pendiente",
                motivo_exclusion="baja_voluntaria" if excluida else None,
            )
        )
        ejecucion.audiencia += 1
        ejecucion.excluidos += excluida
    campana.estado = "en_envio"
    db.flush()
    return ejecucion


def lanzar_programadas(db: Session, momento: datetime | None = None) -> int:
    momento = momento or ahora()
    debidas = list(
        db.scalars(
            select(Campana).where(
                Campana.estado == "programada", Campana.proxima_ejecucion <= momento
            )
        )
    )
    for campana in debidas:
        with db.begin_nested():
            assert campana.proxima_ejecucion is not None
            siguiente = _siguiente(campana.proxima_ejecucion, campana.recurrencia)
            lanzar(db, campana)
            campana.proxima_ejecucion = siguiente
    return len(debidas)


def despachar(db: Session, limite: int | None = None) -> dict[str, int]:
    """Encola hasta `limite` mensajes por pasada (el beat la corre cada minuto): asi el
    envio respeta el ritmo del proveedor sin importar el tamano de la audiencia."""
    from app.modules.comunicaciones import service as comunicaciones

    cupo = limite if limite is not None else settings.CAMPANA_MENSAJES_POR_MINUTO
    resumen = {"encolados": 0, "excluidos": 0, "terminadas": 0}
    for ejecucion in db.scalars(
        select(EjecucionCampana)
        .where(EjecucionCampana.estado == "en_envio")
        .order_by(EjecucionCampana.iniciada_en)
    ).all():
        campana = db.get(Campana, ejecucion.campana_id)
        assert campana is not None
        pendientes = list(
            db.scalars(
                select(DestinatarioCampana)
                .where(
                    DestinatarioCampana.ejecucion_id == ejecucion.id,
                    DestinatarioCampana.estado == "pendiente",
                )
                .limit(cupo)
                .with_for_update(skip_locked=True)
            )
        )
        for destinatario in pendientes:
            familia = db.get(Familia, destinatario.familia_id)
            assert familia is not None
            try:
                with db.begin_nested():
                    mensaje = comunicaciones.encolar_plantilla(
                        db,
                        telefono=destinatario.telefono,
                        plantilla=campana.plantilla or "",
                        variables=_variables(db, campana, familia),
                        familia_id=familia.id,
                        masivo=True,
                        campana_id=campana.id,
                    )
            except ReglaNegocio as e:
                destinatario.estado = "excluido"
                destinatario.motivo_exclusion = str(e)[:120]
                resumen["excluidos"] += 1
                continue
            destinatario.mensaje_id = mensaje.id
            if mensaje.estado == EstadoMensaje.OMITIDO:
                # Pidio la baja despues de congelada la audiencia: tambien se respeta.
                destinatario.estado = "excluido"
                destinatario.motivo_exclusion = "baja_voluntaria"
                ejecucion.excluidos += 1
                resumen["excluidos"] += 1
            else:
                destinatario.estado = "encolado"
                destinatario.encolado_en = ahora()
                resumen["encolados"] += 1
        cupo -= len(pendientes)
        quedan = db.scalar(
            select(func.count())
            .select_from(DestinatarioCampana)
            .where(
                DestinatarioCampana.ejecucion_id == ejecucion.id,
                DestinatarioCampana.estado == "pendiente",
            )
        )
        if not quedan:
            ejecucion.estado = "terminada"
            ejecucion.terminada_en = ahora()
            resumen["terminadas"] += 1
            campana.estado = "programada" if campana.proxima_ejecucion else "finalizada"
        if cupo <= 0:
            break
    db.flush()
    return resumen


def cancelar(db: Session, campana: Campana) -> Campana:
    if campana.estado in ("finalizada", "cancelada"):
        raise ReglaNegocio("La campana ya termino")
    for ejecucion in db.scalars(
        select(EjecucionCampana).where(
            EjecucionCampana.campana_id == campana.id, EjecucionCampana.estado == "en_envio"
        )
    ):
        ejecucion.estado = "cancelada"
        ejecucion.terminada_en = ahora()
        for d in db.scalars(
            select(DestinatarioCampana).where(
                DestinatarioCampana.ejecucion_id == ejecucion.id,
                DestinatarioCampana.estado == "pendiente",
            )
        ):
            d.estado = "excluido"
            d.motivo_exclusion = "campana_cancelada"
    campana.estado = "cancelada"
    campana.proxima_ejecucion = None
    db.flush()
    return campana


# --- F3-CAM-03 Resultados ---------------------------------------------------------------------


def _filas(db: Session, campana: Campana, ejecucion_id: UUID | None) -> list[Any]:
    stmt = (
        select(DestinatarioCampana, Mensaje, Familia.titular_nombre)
        .join(EjecucionCampana, EjecucionCampana.id == DestinatarioCampana.ejecucion_id)
        .join(Familia, Familia.id == DestinatarioCampana.familia_id)
        .outerjoin(Mensaje, Mensaje.id == DestinatarioCampana.mensaje_id)
        .where(EjecucionCampana.campana_id == campana.id)
    )
    if ejecucion_id:
        stmt = stmt.where(EjecucionCampana.id == ejecucion_id)
    return list(db.execute(stmt).tuples())


def _respondio(db: Session, telefono: str, desde: datetime | None) -> bool:
    if desde is None:
        return False
    return bool(
        db.scalar(
            select(Mensaje.id)
            .where(
                Mensaje.direccion == "entrante",
                Mensaje.destino == telefono,
                Mensaje.created_at >= desde,
                Mensaje.created_at <= con_zona(desde) + VENTANA_RESPUESTA,
            )
            .limit(1)
        )
    )


def resultados(db: Session, campana: Campana, ejecucion_id: UUID | None = None) -> dict[str, Any]:
    """Enviados, entregados, leidos, respondidos, fallidos y excluidos."""
    conteo = {
        "audiencia": 0,
        "excluidos": 0,
        "encolados": 0,
        "enviados": 0,
        "entregados": 0,
        "leidos": 0,
        "respondidos": 0,
        "fallidos": 0,
    }
    orden = EstadoMensaje.ORDEN
    for destinatario, mensaje, _ in _filas(db, campana, ejecucion_id):
        conteo["audiencia"] += 1
        if destinatario.estado == "excluido":
            conteo["excluidos"] += 1
            continue
        if mensaje is None:
            continue
        conteo["encolados"] += 1
        if mensaje.estado == EstadoMensaje.FALLIDO:
            conteo["fallidos"] += 1
            continue
        nivel = orden.get(mensaje.estado, -1)
        conteo["enviados"] += nivel >= orden[EstadoMensaje.ENVIADO]
        conteo["entregados"] += nivel >= orden[EstadoMensaje.ENTREGADO]
        conteo["leidos"] += nivel >= orden[EstadoMensaje.LEIDO]
        conteo["respondidos"] += _respondio(db, destinatario.telefono, destinatario.encolado_en)
    return conteo


def detalle(
    db: Session, campana: Campana, ejecucion_id: UUID | None = None
) -> list[dict[str, Any]]:
    """Una fila por destinatario, para exportar."""
    return [
        {
            "titular": titular,
            "telefono": d.telefono,
            "estado_destinatario": d.estado,
            "motivo_exclusion": d.motivo_exclusion,
            "estado_mensaje": m.estado if m else None,
            "encolado_en": d.encolado_en,
            "entregado_en": m.entregado_en if m else None,
            "leido_en": m.leido_en if m else None,
            "respondio": _respondio(db, d.telefono, d.encolado_en),
        }
        for d, m, titular in _filas(db, campana, ejecucion_id)
    ]

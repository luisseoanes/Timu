"""6.8 / 6.9 / 6.13 / 6.15 Calendario preventivo, autorizacion, agenda y carnet."""

import hashlib
import secrets
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errores import NoEncontrado, ReglaNegocio
from app.core.tiempo import ahora, hoy
from app.modules.catalogos.models import Especie, EsquemaPreventivo
from app.modules.familias.models import Familia, Mascota
from app.modules.preventivos.models import CarnetEmitido, EventoPreventivo

logger = structlog.get_logger(__name__)

# Hasta esta edad se asume que la mascota no ha completado la serie inicial.
EDAD_SERIE_INICIAL_SEMANAS = 52

# Tipo de servicio con el que se agenda cada clase de preventivo.
TIPO_SERVICIO = {
    "vacuna": "vacunacion",
    "desparasitacion_interna": "desparasitacion",
    "desparasitacion_externa": "desparasitacion",
}

PLANTILLA_RECORDATORIO = "recordatorio_preventivo"


def fechas_esquema(
    esquema: EsquemaPreventivo, nacimiento: date | None, desde: date
) -> tuple[list[date], bool]:
    """Fechas de las dosis a programar para una mascota que entra al plan en `desde`, y si
    son de refuerzo.

    - Cachorro que aun no llega a la edad minima: la serie arranca en esa edad.
    - Cachorro que ya la paso: la serie completa arranca en `desde` (no se conoce su historia;
      el profesional ajusta si trae carnet).
    - Adulto o edad desconocida: una dosis de refuerzo en `desde`.
    """
    if nacimiento is not None:
        edad_semanas = (desde - nacimiento).days // 7
        if edad_semanas < EDAD_SERIE_INICIAL_SEMANAS:
            inicio = max(desde, nacimiento + timedelta(weeks=esquema.edad_minima_semanas))
            return [
                inicio + timedelta(days=esquema.intervalo_inicial_dias * i)
                for i in range(esquema.dosis_iniciales)
            ], False
    return ([desde] if esquema.intervalo_refuerzo_dias else []), True


def calendario_inicial(db: Session, mascota: Mascota, desde: date) -> list[EventoPreventivo]:
    """F1-AFI-03 Programa los preventivos de la mascota segun los esquemas de su especie.
    Repetible: no duplica esquemas que la mascota ya tenga programados."""
    esquemas = db.scalars(
        select(EsquemaPreventivo).where(
            EsquemaPreventivo.especie_codigo == mascota.especie,
            EsquemaPreventivo.activo.is_(True),
        )
    )
    ya_programados = set(
        db.scalars(
            select(EventoPreventivo.esquema_codigo).where(EventoPreventivo.mascota_id == mascota.id)
        )
    )
    eventos = []
    for esquema in esquemas:
        if esquema.codigo in ya_programados:
            continue
        fechas, refuerzo = fechas_esquema(esquema, mascota.fecha_nacimiento, desde)
        for numero, fecha in enumerate(fechas, start=1):
            evento = EventoPreventivo(
                mascota_id=mascota.id,
                esquema_codigo=esquema.codigo,
                tipo=esquema.tipo,
                dosis_numero=numero,
                es_refuerzo=refuerzo,
                fecha_programada=fecha,
                requiere_autorizacion=esquema.requiere_autorizacion,
            )
            db.add(evento)
            eventos.append(evento)
    db.flush()
    return eventos


# --- Consultas -------------------------------------------------------------------------------


def consulta(
    *,
    mascota_id: UUID | None = None,
    estado: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    pendientes_autorizacion: bool = False,
) -> Select[tuple[EventoPreventivo]]:
    stmt = select(EventoPreventivo)
    if mascota_id:
        stmt = stmt.where(EventoPreventivo.mascota_id == mascota_id)
    if estado:
        stmt = stmt.where(EventoPreventivo.estado == estado)
    if desde:
        stmt = stmt.where(EventoPreventivo.fecha_programada >= desde)
    if hasta:
        stmt = stmt.where(EventoPreventivo.fecha_programada <= hasta)
    if pendientes_autorizacion:
        stmt = stmt.where(
            EventoPreventivo.estado == "programado",
            EventoPreventivo.requiere_autorizacion.is_(True),
            EventoPreventivo.autorizado.is_(False),
        )
    return stmt


def obtener(db: Session, evento_id: UUID) -> EventoPreventivo:
    evento = db.get(EventoPreventivo, evento_id)
    if evento is None:
        raise NoEncontrado("Evento preventivo no encontrado")
    return evento


def _mascota(db: Session, mascota_id: UUID) -> Mascota:
    mascota = db.get(Mascota, mascota_id)
    if mascota is None:
        raise NoEncontrado("Mascota no encontrada")
    return mascota


def _esquema(db: Session, codigo: str | None) -> EsquemaPreventivo | None:
    if codigo is None:
        return None
    return db.scalar(select(EsquemaPreventivo).where(EsquemaPreventivo.codigo == codigo))


# --- F2-PRE-03 Autorizacion ------------------------------------------------------------------


def autorizar(
    db: Session, evento: EventoPreventivo, usuario_id: UUID, medio: str, aprobado: bool
) -> EventoPreventivo:
    """Registra la autorizacion (o el rechazo) de la familia. Sin autorizacion registrada,
    un preventivo que la requiere no se puede aplicar."""
    if evento.estado != "programado":
        raise ReglaNegocio("Solo se autoriza un preventivo programado")
    if not evento.requiere_autorizacion:
        raise ReglaNegocio("Este preventivo no requiere autorizacion")
    evento.autorizado = aprobado
    evento.autorizado_por_id = usuario_id
    evento.autorizado_en = ahora()
    evento.medio_autorizacion = medio
    if not aprobado:
        evento.estado = "cancelado"
        evento.motivo_cancelacion = "La familia no autorizo el preventivo"
    db.flush()
    return evento


# --- F2-PRE-02 Aplicacion y proxima fecha ----------------------------------------------------


def _siguiente(db: Session, evento: EventoPreventivo, numero: int) -> EventoPreventivo | None:
    return db.scalar(
        select(EventoPreventivo).where(
            EventoPreventivo.mascota_id == evento.mascota_id,
            EventoPreventivo.esquema_codigo == evento.esquema_codigo,
            EventoPreventivo.dosis_numero == numero,
            EventoPreventivo.estado == "programado",
        )
    )


def aplicar(
    db: Session,
    evento: EventoPreventivo,
    *,
    fecha: date,
    producto: str,
    lote: str | None,
    usuario_id: UUID,
    servicio_id: UUID | None = None,
) -> EventoPreventivo:
    """Registra la aplicacion y recalcula la siguiente fecha a partir de la fecha REAL,
    no de la programada: si la segunda dosis se puso una semana tarde, la tercera corre."""
    if evento.estado != "programado":
        raise ReglaNegocio("El preventivo ya fue aplicado o cancelado")
    if evento.requiere_autorizacion and not evento.autorizado:
        raise ReglaNegocio("Falta la autorizacion de la familia para aplicar este preventivo")
    if fecha > hoy():
        raise ReglaNegocio("La fecha de aplicacion no puede ser futura")
    evento.estado = "aplicado"
    evento.fecha_aplicacion = fecha
    evento.producto = producto
    evento.lote = lote
    evento.aplicado_por_id = usuario_id
    if servicio_id:
        evento.servicio_id = servicio_id

    esquema = _esquema(db, evento.esquema_codigo)
    if esquema is not None:
        serie_pendiente = not evento.es_refuerzo and evento.dosis_numero < esquema.dosis_iniciales
        if serie_pendiente:
            proxima = fecha + timedelta(days=esquema.intervalo_inicial_dias)
            refuerzo = False
        elif esquema.intervalo_refuerzo_dias:
            proxima = fecha + timedelta(days=esquema.intervalo_refuerzo_dias)
            refuerzo = True
        else:
            proxima = None
        if proxima is not None:
            siguiente = _siguiente(db, evento, evento.dosis_numero + 1)
            if siguiente is None:
                siguiente = EventoPreventivo(
                    mascota_id=evento.mascota_id,
                    esquema_codigo=evento.esquema_codigo,
                    tipo=evento.tipo,
                    dosis_numero=evento.dosis_numero + 1,
                    requiere_autorizacion=esquema.requiere_autorizacion,
                    fecha_programada=proxima,
                )
                db.add(siguiente)
            siguiente.fecha_programada = proxima
            siguiente.es_refuerzo = refuerzo
        evento.proxima_fecha = proxima
    db.flush()
    return evento


def cancelar(db: Session, evento: EventoPreventivo, motivo: str) -> EventoPreventivo:
    if evento.estado != "programado":
        raise ReglaNegocio("Solo se cancela un preventivo programado")
    evento.estado = "cancelado"
    evento.motivo_cancelacion = motivo
    db.flush()
    return evento


# --- F2-PRE-04 Agenda preventiva -------------------------------------------------------------


def _vigente(db: Session, familia_id: UUID) -> bool:
    from app.modules.planes import service as planes

    return planes.contrato_vigente(db, familia_id) is not None


def agenda_diaria(db: Session, dia: date | None = None) -> dict[str, int]:
    """Avisa a la familia de los preventivos que se acercan (una sola vez por evento) para
    que los agende. Solo mascotas activas de familias con plan vigente."""
    from app.modules.comunicaciones import service as comunicaciones

    dia = dia or hoy()
    limite = dia + timedelta(days=settings.PREVENTIVO_ANTICIPACION_DIAS)
    resumen = {"avisados": 0, "sin_aviso": 0}
    filas = db.execute(
        select(EventoPreventivo, Mascota, Familia)
        .join(Mascota, Mascota.id == EventoPreventivo.mascota_id)
        .join(Familia, Familia.id == Mascota.familia_id)
        .where(
            EventoPreventivo.estado == "programado",
            EventoPreventivo.notificado_en.is_(None),
            EventoPreventivo.servicio_id.is_(None),
            EventoPreventivo.fecha_programada <= limite,
            Mascota.activa.is_(True),
            Familia.dada_de_baja_en.is_(None),
        )
        .order_by(EventoPreventivo.fecha_programada)
    ).all()
    for evento, mascota, familia in filas:
        if not _vigente(db, familia.id):
            continue
        esquema = _esquema(db, evento.esquema_codigo)
        nombre = esquema.nombre if esquema else evento.tipo
        try:
            with db.begin_nested():
                comunicaciones.encolar_plantilla(
                    db,
                    telefono=familia.telefono,
                    plantilla=PLANTILLA_RECORDATORIO,
                    variables=[
                        familia.titular_nombre,
                        mascota.nombre,
                        nombre,
                        f"{evento.fecha_programada:%d/%m/%Y}",
                    ],
                    familia_id=familia.id,
                )
                evento.notificado_en = ahora()
            resumen["avisados"] += 1
        except ReglaNegocio as e:
            logger.error("Recordatorio preventivo sin enviar: %s", e)
            resumen["sin_aviso"] += 1
    db.flush()
    return resumen


def agendar(
    db: Session, evento: EventoPreventivo, inicio: datetime, observaciones: str | None = None
) -> EventoPreventivo:
    """Convierte el evento en un servicio agendado contra la disponibilidad real."""
    from app.modules.servicios import service as servicios

    if evento.estado != "programado":
        raise ReglaNegocio("Solo se agenda un preventivo programado")
    if evento.servicio_id is not None:
        raise ReglaNegocio("El preventivo ya tiene un servicio agendado")
    mascota = _mascota(db, evento.mascota_id)
    familia = db.get(Familia, mascota.familia_id)
    assert familia is not None
    tipo = servicios.tipo_servicio(db, TIPO_SERVICIO.get(evento.tipo, "vacunacion"))
    servicio = servicios.agendar(
        db,
        familia=familia,
        mascota=mascota,
        tipo=tipo,
        inicio=inicio,
        observaciones=observaciones or f"Preventivo: {evento.tipo} dosis {evento.dosis_numero}",
    )
    evento.servicio_id = servicio.id
    db.flush()
    return evento


# --- F2-PRE-05 / 06 Carnet ---------------------------------------------------------------------


def _fila_carnet(evento: EventoPreventivo, esquemas: dict[str, str]) -> dict[str, Any]:
    return {
        "id": str(evento.id),
        "tipo": evento.tipo,
        "nombre": esquemas.get(evento.esquema_codigo or "", evento.tipo),
        "dosis": evento.dosis_numero,
        "refuerzo": evento.es_refuerzo,
        "fecha_programada": evento.fecha_programada.isoformat(),
        "fecha_aplicacion": (
            evento.fecha_aplicacion.isoformat() if evento.fecha_aplicacion else None
        ),
        "producto": evento.producto,
        "lote": evento.lote,
        "proxima_fecha": evento.proxima_fecha.isoformat() if evento.proxima_fecha else None,
    }


def carnet(db: Session, mascota_id: UUID, dia: date | None = None) -> dict[str, Any]:
    """Lo efectivamente aplicado, lo vencido (programado con fecha pasada) y lo proximo.
    Nada de lo programado figura como aplicado."""
    dia = dia or hoy()
    mascota = _mascota(db, mascota_id)
    especie = db.scalar(select(Especie.nombre).where(Especie.codigo == mascota.especie))
    esquemas = dict(
        db.execute(select(EsquemaPreventivo.codigo, EsquemaPreventivo.nombre)).tuples().all()
    )
    eventos = list(
        db.scalars(
            select(EventoPreventivo)
            .where(EventoPreventivo.mascota_id == mascota.id)
            .order_by(EventoPreventivo.fecha_programada, EventoPreventivo.dosis_numero)
        )
    )
    aplicados = [e for e in eventos if e.estado == "aplicado"]
    aplicados.sort(key=lambda e: e.fecha_aplicacion or e.fecha_programada)
    programados = [e for e in eventos if e.estado == "programado"]
    return {
        "mascota": {
            "id": str(mascota.id),
            "nombre": mascota.nombre,
            "especie": especie or mascota.especie,
            "raza": mascota.raza,
            "fecha_nacimiento": (
                mascota.fecha_nacimiento.isoformat() if mascota.fecha_nacimiento else None
            ),
        },
        "aplicados": [_fila_carnet(e, esquemas) for e in aplicados],
        "vencidos": [_fila_carnet(e, esquemas) for e in programados if e.fecha_programada < dia],
        "proximos": [_fila_carnet(e, esquemas) for e in programados if e.fecha_programada >= dia],
    }


def _codigo_unico(db: Session) -> str:
    # Sin caracteres ambiguos (0/O, 1/I): el codigo se dicta por telefono o se transcribe.
    alfabeto = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    while True:
        codigo = "".join(secrets.choice(alfabeto) for _ in range(10))
        if not db.scalar(select(CarnetEmitido.id).where(CarnetEmitido.codigo == codigo)):
            return codigo


def emitir_carnet(db: Session, mascota_id: UUID, usuario_id: UUID | None) -> CarnetEmitido:
    """F2-PRE-06 Genera el PDF con un codigo de verificacion y guarda lo que decia."""
    from app.modules.archivos import service as archivos
    from app.modules.preventivos import documento

    datos = carnet(db, mascota_id)
    codigo = _codigo_unico(db)
    url_verificacion = f"{settings.FRONTEND_URL}/verificar/{codigo}"
    contenido = documento.generar_carnet(datos, codigo=codigo, url_verificacion=url_verificacion)
    archivo = archivos.guardar_bytes(
        db,
        contenido=contenido,
        nombre=f"carnet-{datos['mascota']['nombre']}-{codigo}.pdf",
        proposito="carnet",
        usuario_id=usuario_id,
    )
    registro = CarnetEmitido(
        codigo=codigo,
        mascota_id=mascota_id,
        archivo_id=archivo.id,
        sha256=hashlib.sha256(contenido).hexdigest(),
        contenido={"mascota": datos["mascota"], "aplicados": datos["aplicados"]},
        emitido_por_id=usuario_id,
    )
    db.add(registro)
    db.flush()
    return registro


def verificar_carnet(db: Session, codigo: str) -> dict[str, Any]:
    """Lo que ve un tercero con el codigo: la mascota y lo aplicado al emitir, sin datos
    de la familia. Mismo 404 para codigo inexistente que para mal escrito."""
    registro = db.scalar(
        select(CarnetEmitido).where(CarnetEmitido.codigo == codigo.strip().upper())
    )
    if registro is None:
        raise NoEncontrado("Carnet no encontrado")
    mascota = registro.contenido["mascota"]
    return {
        "codigo": registro.codigo,
        "emitido_en": registro.created_at,
        "sha256": registro.sha256,
        "mascota": {k: mascota.get(k) for k in ("nombre", "especie", "raza")},
        "aplicados": [
            {k: a.get(k) for k in ("nombre", "dosis", "fecha_aplicacion", "producto", "lote")}
            for a in registro.contenido["aplicados"]
        ],
    }

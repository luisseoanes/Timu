"""6.19 Mensajeria: bandeja de salida con reintentos, estados de entrega y reglas de Meta.

Ningun modulo llama a la API de WhatsApp directamente: todos encolan aqui. Asi cada envio
queda trazado por destinatario (F1-WHA-01), respeta la ventana de 24 horas y las bajas
(F1-WHA-04) y solo usa plantillas aprobadas (F1-WHA-03).
"""

import re
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errores import NoEncontrado, ReglaNegocio
from app.core.eventos import EventoDominio
from app.core.outbox import publicar
from app.core.tiempo import ahora, con_zona
from app.core.validaciones import normalizar_telefono, telefono_whatsapp
from app.integrations import correo
from app.integrations.whatsapp import ErrorWhatsApp, WhatsAppClient
from app.modules.comunicaciones.models import (
    BajaComunicaciones,
    ConversacionWhatsApp,
    EstadoMensaje,
    Mensaje,
    PlantillaWhatsApp,
)

logger = structlog.get_logger(__name__)

TAREA_ENVIO = "comunicaciones.enviar_mensaje"
EVENTO_ENCOLADO = "mensaje.encolado"
MAX_INTENTOS = 5
VENTANA = timedelta(hours=24)
# Respuestas que se interpretan como pedido de baja de los envios masivos.
PALABRAS_BAJA = {"BAJA", "STOP", "NO MAS", "NO MÁS", "DETENER"}


# --- Plantillas (F1-WHA-03) -------------------------------------------------------------


def render(cuerpo: str, variables: list[str]) -> str:
    return re.sub(
        r"\{\{(\d+)\}\}",
        lambda m: variables[int(m.group(1)) - 1] if int(m.group(1)) <= len(variables) else "",
        cuerpo,
    )


def plantilla_vigente(db: Session, nombre: str, idioma: str = "es") -> PlantillaWhatsApp | None:
    return db.scalar(
        select(PlantillaWhatsApp)
        .where(
            PlantillaWhatsApp.nombre == nombre,
            PlantillaWhatsApp.idioma == idioma,
            PlantillaWhatsApp.estado_aprobacion == "aprobada",
            PlantillaWhatsApp.activa.is_(True),
        )
        .order_by(PlantillaWhatsApp.version.desc())
        .limit(1)
    )


def crear_version_plantilla(db: Session, datos: dict[str, Any]) -> PlantillaWhatsApp:
    ultima = db.scalar(
        select(func.max(PlantillaWhatsApp.version)).where(
            PlantillaWhatsApp.nombre == datos["nombre"],
            PlantillaWhatsApp.idioma == datos.get("idioma", "es"),
        )
    )
    plantilla = PlantillaWhatsApp(**datos, version=(ultima or 0) + 1, estado_aprobacion="borrador")
    db.add(plantilla)
    db.flush()
    return plantilla


def cambiar_estado_plantilla(
    db: Session, plantilla_id: UUID, estado: str, activa: bool | None
) -> PlantillaWhatsApp:
    plantilla = db.get(PlantillaWhatsApp, plantilla_id)
    if plantilla is None:
        raise NoEncontrado("Plantilla no encontrada")
    plantilla.estado_aprobacion = estado
    if activa:
        if estado != "aprobada":
            raise ReglaNegocio("Solo una plantilla aprobada por Meta puede activarse")
        # Una sola version activa por nombre e idioma.
        otras = db.scalars(
            select(PlantillaWhatsApp).where(
                PlantillaWhatsApp.nombre == plantilla.nombre,
                PlantillaWhatsApp.idioma == plantilla.idioma,
                PlantillaWhatsApp.id != plantilla.id,
            )
        )
        for otra in otras:
            otra.activa = False
        plantilla.activa = True
    elif activa is False or estado != "aprobada":
        plantilla.activa = False
    db.flush()
    return plantilla


# --- Bajas y ventana (F1-WHA-04) ---------------------------------------------------------


def esta_de_baja(db: Session, destino: str) -> bool:
    return bool(
        db.scalar(select(BajaComunicaciones.id).where(BajaComunicaciones.destino == destino))
    )


def registrar_baja(
    db: Session, destino: str, *, canal: str = "whatsapp", motivo: str | None = None
) -> BajaComunicaciones:
    existente = db.scalar(select(BajaComunicaciones).where(BajaComunicaciones.destino == destino))
    if existente:
        return existente
    baja = BajaComunicaciones(destino=destino, canal=canal, motivo=motivo)
    db.add(baja)
    db.flush()
    return baja


def quitar_baja(db: Session, destino: str) -> None:
    baja = db.scalar(select(BajaComunicaciones).where(BajaComunicaciones.destino == destino))
    if baja is None:
        raise NoEncontrado("El destino no esta dado de baja")
    db.delete(baja)


def ventana_abierta(db: Session, telefono: str) -> bool:
    ultimo = db.scalar(
        select(ConversacionWhatsApp.ultimo_entrante_en).where(
            ConversacionWhatsApp.telefono == telefono
        )
    )
    return ultimo is not None and ahora() - con_zona(ultimo) < VENTANA


# --- Encolado (F1-WHA-01) ------------------------------------------------------------------


def _encolar(db: Session, mensaje: Mensaje) -> Mensaje:
    mensaje.id = mensaje.id or uuid4()  # el default de la columna solo se aplica en el flush
    db.add(mensaje)
    if mensaje.estado == EstadoMensaje.ENCOLADO:
        # El envio sale cuando la transaccion se confirma (outbox), nunca antes.
        publicar(db, EventoDominio(EVENTO_ENCOLADO, {"mensaje_id": str(mensaje.id)}))
    return mensaje


def encolar_plantilla(
    db: Session,
    *,
    telefono: str,
    plantilla: str,
    variables: list[str] | None = None,
    familia_id: UUID | None = None,
    masivo: bool = False,
    campana_id: UUID | None = None,
    idioma: str = "es",
) -> Mensaje:
    variables = variables or []
    vigente = plantilla_vigente(db, plantilla, idioma)
    if vigente is None:
        raise ReglaNegocio(f"La plantilla '{plantilla}' no esta aprobada y activa")
    if len(variables) != len(vigente.variables):
        raise ReglaNegocio(
            f"La plantilla '{plantilla}' espera {len(vigente.variables)} variables "
            f"({', '.join(vigente.variables)}) y recibio {len(variables)}"
        )
    telefono = normalizar_telefono(telefono)
    omitido = masivo and esta_de_baja(db, telefono)
    mensaje = Mensaje(
        familia_id=familia_id,
        canal="whatsapp",
        destino=telefono,
        plantilla=plantilla,
        variables=variables,
        contenido=render(vigente.cuerpo, variables),
        masivo=masivo,
        campana_id=campana_id,
        estado=EstadoMensaje.OMITIDO if omitido else EstadoMensaje.ENCOLADO,
        error="Destinatario dado de baja de envios masivos" if omitido else None,
    )
    _encolar(db, mensaje)
    db.flush()
    return mensaje


def encolar_texto(
    db: Session, *, telefono: str, texto: str, familia_id: UUID | None = None
) -> Mensaje:
    telefono = normalizar_telefono(telefono)
    if not ventana_abierta(db, telefono):
        raise ReglaNegocio(
            "Fuera de la ventana de 24 horas desde el ultimo mensaje de la persona "
            "solo se pueden enviar plantillas aprobadas"
        )
    mensaje = Mensaje(familia_id=familia_id, canal="whatsapp", destino=telefono, contenido=texto)
    _encolar(db, mensaje)
    db.flush()
    return mensaje


def encolar_correo(
    db: Session,
    *,
    email: str,
    asunto: str,
    cuerpo: str,
    familia_id: UUID | None = None,
    masivo: bool = False,
) -> Mensaje:
    omitido = masivo and esta_de_baja(db, email)
    mensaje = Mensaje(
        familia_id=familia_id,
        canal="email",
        destino=email,
        asunto=asunto,
        contenido=cuerpo,
        masivo=masivo,
        estado=EstadoMensaje.OMITIDO if omitido else EstadoMensaje.ENCOLADO,
    )
    _encolar(db, mensaje)
    db.flush()
    return mensaje


# --- Envio (ejecutado por el worker) -----------------------------------------------------


def procesar_envio(db: Session, mensaje_id: UUID, cliente: WhatsAppClient | None = None) -> str:
    """Intenta enviar. Devuelve el estado resultante, o 'reintentar' si el fallo es temporal
    y quedan intentos: el worker reprograma la tarea con espera creciente."""
    mensaje = db.get(Mensaje, mensaje_id, with_for_update=True)
    if mensaje is None or mensaje.estado != EstadoMensaje.ENCOLADO:
        return mensaje.estado if mensaje else "inexistente"
    mensaje.intentos += 1
    try:
        if mensaje.canal == "email":
            assert mensaje.destino and mensaje.contenido is not None
            resultado = correo.enviar(mensaje.destino, mensaje.asunto or "", mensaje.contenido)
            mensaje.id_externo = None if resultado == "enviado" else resultado
        else:
            cliente = cliente or WhatsAppClient()
            assert mensaje.destino
            destino = telefono_whatsapp(mensaje.destino)
            if mensaje.plantilla:
                mensaje.id_externo = cliente.enviar_plantilla(
                    destino, mensaje.plantilla, mensaje.variables
                )
            else:
                mensaje.id_externo = cliente.enviar_texto(destino, mensaje.contenido or "")
    except (ErrorWhatsApp, correo.ErrorCorreo) as e:
        mensaje.error = str(e)
        if e.temporal and mensaje.intentos < MAX_INTENTOS:
            logger.warning("Envio %s fallo (intento %s): %s", mensaje.id, mensaje.intentos, e)
            return "reintentar"
        mensaje.estado = EstadoMensaje.FALLIDO
        logger.error("Envio %s fallido definitivamente: %s", mensaje.id, e)
        return mensaje.estado
    mensaje.estado = EstadoMensaje.ENVIADO
    mensaje.enviado_en = ahora()
    mensaje.error = None
    return mensaje.estado


def pendientes_por_reencolar(db: Session, antiguedad: timedelta) -> list[UUID]:
    """Mensajes que siguen encolados mucho despues de creados (broker caido al encolar)."""
    limite = ahora() - antiguedad
    ids = db.scalars(
        select(Mensaje.id).where(
            Mensaje.estado == EstadoMensaje.ENCOLADO, Mensaje.created_at < limite
        )
    )
    return list(ids)


# --- Webhook de Meta (F1-WHA-02) -----------------------------------------------------------

_ESTADOS_META = {
    "sent": EstadoMensaje.ENVIADO,
    "delivered": EstadoMensaje.ENTREGADO,
    "read": EstadoMensaje.LEIDO,
    "failed": EstadoMensaje.FALLIDO,
}


def _ts(valor: str | None) -> datetime:
    return datetime.fromtimestamp(int(valor), UTC) if valor else ahora()


def _familia_por_telefono(db: Session, telefono: str) -> UUID | None:
    from app.modules.familias.models import Familia

    return db.scalar(select(Familia.id).where(Familia.telefono == telefono).limit(1))


def _aplicar_estado(db: Session, st: dict[str, Any]) -> None:
    mensaje = db.scalar(select(Mensaje).where(Mensaje.id_externo == st.get("id")))
    nuevo = _ESTADOS_META.get(st.get("status", ""))
    if mensaje is None or nuevo is None:
        return
    momento = _ts(st.get("timestamp"))
    if nuevo == EstadoMensaje.FALLIDO:
        mensaje.estado = nuevo
        errores = st.get("errors") or [{}]
        mensaje.error = errores[0].get("title") or errores[0].get("message") or "Fallo en Meta"
        return
    if nuevo == EstadoMensaje.ENTREGADO:
        mensaje.entregado_en = mensaje.entregado_en or momento
    if nuevo == EstadoMensaje.LEIDO:
        mensaje.leido_en = mensaje.leido_en or momento
        mensaje.entregado_en = mensaje.entregado_en or momento
    # Los eventos pueden llegar desordenados: el estado solo avanza.
    actual = EstadoMensaje.ORDEN.get(mensaje.estado, -1)
    if EstadoMensaje.ORDEN[nuevo] > actual:
        mensaje.estado = nuevo


def _remitente(numero: str) -> str:
    """Los numeros colombianos se normalizan para encontrar a la familia; uno extranjero
    se guarda tal cual en E.164 en lugar de tumbar el resto del webhook."""
    try:
        return normalizar_telefono(numero)
    except ValueError:
        return "+" + numero.lstrip("+")


def _registrar_entrante(db: Session, msg: dict[str, Any]) -> None:
    telefono = _remitente(msg["from"])
    if db.scalar(select(Mensaje.id).where(Mensaje.id_externo == msg.get("id"))):
        return  # Meta reintenta webhooks: el mismo mensaje no se registra dos veces
    familia_id = _familia_por_telefono(db, telefono)
    texto = (msg.get("text") or {}).get("body") or (msg.get("button") or {}).get("text")
    db.add(
        Mensaje(
            familia_id=familia_id,
            canal="whatsapp",
            direccion="entrante",
            destino=telefono,
            contenido=texto or f"[{msg.get('type', 'desconocido')}]",
            estado=EstadoMensaje.RECIBIDO,
            id_externo=msg.get("id"),
        )
    )
    momento = _ts(msg.get("timestamp"))
    conversacion = db.scalar(
        select(ConversacionWhatsApp).where(ConversacionWhatsApp.telefono == telefono)
    )
    if conversacion is None:
        db.add(
            ConversacionWhatsApp(
                telefono=telefono, familia_id=familia_id, ultimo_entrante_en=momento
            )
        )
    else:
        conversacion.ultimo_entrante_en = max(con_zona(conversacion.ultimo_entrante_en), momento)
        conversacion.familia_id = conversacion.familia_id or familia_id
    if texto and texto.strip().upper() in PALABRAS_BAJA:
        registrar_baja(db, telefono, motivo="Solicitada por WhatsApp")


def procesar_evento_whatsapp(db: Session, payload: dict[str, Any]) -> dict[str, int]:
    conteo = {"estados": 0, "entrantes": 0}
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            valor = change.get("value", {})
            for st in valor.get("statuses", []):
                _aplicar_estado(db, st)
                conteo["estados"] += 1
            for msg in valor.get("messages", []):
                _registrar_entrante(db, msg)
                conteo["entrantes"] += 1
            db.flush()
    return conteo

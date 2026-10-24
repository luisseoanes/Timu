"""F3-COM-02..04 Conversacion comercial automatizada por WhatsApp.

Un arbol de nodos (editable como dato, ver ArbolConversacion) resuelve las preguntas
frecuentes, captura ciudad y mascotas, recomienda el plan con las reglas ya definidas y
lleva a la afiliacion. Pasa a un asesor humano si la persona lo pide o si el bot no la
entiende varias veces seguidas.

Nodo:
    {"mensaje": "...", "opciones": {"1": "otro_nodo"}}          menu
    {"mensaje": "...", "captura": "ciudad", "siguiente": "..."}   pregunta abierta
    {"accion": "recomendar", "siguiente": "..."}                  paso automatico
Acciones: recomendar, enlace_afiliacion, cobertura, asesor.
"""

import re
import unicodedata
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errores import NoEncontrado, ReglaNegocio
from app.modules.comercial import service as embudo
from app.modules.comercial.models import ArbolConversacion, ConversacionComercial, Interesado

logger = structlog.get_logger(__name__)

MAX_FALLOS = 3
PALABRAS_MENU = {"menu", "inicio", "hola", "buenas", "buenos dias", "buenas tardes"}
PALABRAS_ASESOR = ("asesor", "humano", "persona", "agente")

ARBOL_POR_DEFECTO: dict[str, Any] = {
    "inicio": {
        "mensaje": (
            "Hola, soy el asistente de TIMU. Cuidamos a tus mascotas en casa con planes "
            "mensuales.\n1. Conocer el plan ideal para mi familia\n2. Ciudades donde "
            "atendemos\n3. Hablar con un asesor"
        ),
        "opciones": {"1": "pedir_ciudad", "2": "cobertura", "3": "asesor"},
    },
    "pedir_ciudad": {
        "mensaje": "En que ciudad vives?",
        "captura": "ciudad",
        "siguiente": "pedir_mascotas",
    },
    "pedir_mascotas": {
        "mensaje": "Cuantas mascotas tienes y de que especie? Por ejemplo: 2 perros y 1 gato",
        "captura": "mascotas",
        "siguiente": "recomendacion",
    },
    "recomendacion": {"accion": "recomendar", "siguiente": "tras_recomendacion"},
    "tras_recomendacion": {
        "mensaje": "1. Quiero afiliarme\n2. Hablar con un asesor\n3. Volver al inicio",
        "opciones": {"1": "afiliar", "2": "asesor", "3": "inicio"},
    },
    "afiliar": {"accion": "enlace_afiliacion", "siguiente": "fin"},
    "cobertura": {"accion": "cobertura", "siguiente": "inicio_corto"},
    "inicio_corto": {
        "mensaje": "1. Conocer el plan ideal\n2. Hablar con un asesor",
        "opciones": {"1": "pedir_ciudad", "2": "asesor"},
    },
    "asesor": {"accion": "asesor"},
    "fin": {"mensaje": "Gracias por escribirnos. Escribe *menu* cuando quieras volver."},
}


def validar_arbol(nodos: dict[str, Any]) -> None:
    """Un arbol roto dejaria a la gente sin respuesta: se valida antes de activarlo."""
    if "inicio" not in nodos:
        raise ReglaNegocio("El arbol necesita un nodo 'inicio'")
    acciones = {"recomendar", "enlace_afiliacion", "cobertura", "asesor"}
    for nombre, nodo in nodos.items():
        destinos = list((nodo.get("opciones") or {}).values())
        if "siguiente" in nodo:
            destinos.append(nodo["siguiente"])
        for destino in destinos:
            if destino not in nodos:
                raise ReglaNegocio(f"El nodo '{nombre}' apunta a '{destino}', que no existe")
        if "accion" in nodo and nodo["accion"] not in acciones:
            raise ReglaNegocio(f"Accion desconocida en '{nombre}': {nodo['accion']}")
        if "captura" in nodo and nodo["captura"] not in ("ciudad", "mascotas", "nombre"):
            raise ReglaNegocio(f"Captura desconocida en '{nombre}': {nodo['captura']}")
        if not any(k in nodo for k in ("mensaje", "accion")):
            raise ReglaNegocio(f"El nodo '{nombre}' no dice ni hace nada")


def arbol(db: Session) -> dict[str, Any]:
    activo = db.scalar(select(ArbolConversacion).where(ArbolConversacion.activo.is_(True)))
    return activo.nodos if activo else ARBOL_POR_DEFECTO


# --- Capturas ---------------------------------------------------------------------------------


def _sin_tildes(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


_NUMEROS = {"un": 1, "una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5}
_ESPECIES = {
    "canino": ("perro", "perra", "perrito", "perrita", "canino", "cachorro"),
    "felino": ("gato", "gata", "gatito", "gatita", "felino"),
}


def leer_mascotas(texto: str) -> list[str]:
    """'2 perros y un gato' -> ['canino', 'canino', 'felino']. Sin cantidad, cuenta 1."""
    palabras = re.findall(r"[a-z0-9]+", _sin_tildes(texto.lower()))
    especies: list[str] = []
    for i, palabra in enumerate(palabras):
        for codigo, nombres in _ESPECIES.items():
            if any(palabra.startswith(n) for n in nombres):
                anterior = palabras[i - 1] if i else ""
                cantidad = int(anterior) if anterior.isdigit() else _NUMEROS.get(anterior, 1)
                especies.extend([codigo] * min(cantidad, 10))
    return especies


def _capturar(db: Session, tipo: str, texto: str) -> tuple[Any, str | None]:
    """(valor, error). Un error de cobertura no es un "no te entendi": va a un asesor."""
    from app.modules.catalogos import service as catalogos

    if tipo == "ciudad":
        try:
            return catalogos.ciudad_valida(db, _sin_tildes(texto)), None
        except ReglaNegocio:
            return texto.strip(), "sin_cobertura"
    if tipo == "mascotas":
        especies = leer_mascotas(texto)
        return (especies, None) if especies else (None, "no_entendido")
    if tipo == "nombre":
        return (texto.strip()[:160], None) if texto.strip() else (None, "no_entendido")
    return None, "no_entendido"


# --- Motor ------------------------------------------------------------------------------------


class _Turno:
    """Respuestas acumuladas en un turno: se envian juntas al final."""

    def __init__(self) -> None:
        self.mensajes: list[str] = []

    def decir(self, texto: str) -> None:
        self.mensajes.append(texto)


def procesar_entrante(db: Session, telefono: str, texto: str, familia_id: Any = None) -> list[str]:
    """Responde un mensaje entrante. Devuelve lo que se respondio (para trazas y pruebas)."""
    from app.modules.comunicaciones import service as comunicaciones

    conversacion = db.scalar(
        select(ConversacionComercial).where(ConversacionComercial.telefono == telefono)
    )
    turno = _Turno()
    nodos = arbol(db)
    if conversacion is None:
        interesado = (
            None
            if familia_id
            else embudo.registrar(db, origen="whatsapp", telefono=telefono, etapa="contactado")
        )
        conversacion = ConversacionComercial(
            telefono=telefono,
            interesado_id=interesado.id if interesado else None,
            nodo="inicio",
            datos={},
            estado="automatica",
            fallos=0,
        )
        db.add(conversacion)
        db.flush()
        _ir(db, conversacion, "inicio", nodos, turno)
    elif conversacion.estado == "con_asesor":
        return []  # lo atiende una persona; el bot no interrumpe
    else:
        _responder(db, conversacion, texto, nodos, turno)

    for mensaje in turno.mensajes:
        try:
            comunicaciones.encolar_texto(
                db, telefono=telefono, texto=mensaje, familia_id=familia_id
            )
        except (ReglaNegocio, ValueError) as e:
            logger.error("Respuesta comercial sin enviar: %s", e)
    db.flush()
    return turno.mensajes


def _responder(
    db: Session,
    conversacion: ConversacionComercial,
    texto: str,
    nodos: dict[str, Any],
    turno: _Turno,
) -> None:
    limpio = _sin_tildes(texto.strip().lower())
    if limpio in PALABRAS_MENU:
        conversacion.fallos = 0
        _ir(db, conversacion, "inicio", nodos, turno)
        return
    if any(p in limpio for p in PALABRAS_ASESOR):
        _asesor(db, conversacion, "La persona pidio hablar con un asesor", turno)
        return
    nodo = nodos.get(conversacion.nodo) or nodos["inicio"]
    if "captura" in nodo:
        valor, error = _capturar(db, nodo["captura"], texto)
        if error == "sin_cobertura":
            conversacion.datos = {**conversacion.datos, "ciudad_sin_cobertura": valor}
            turno.decir(f"Por ahora no atendemos en {valor}, pero un asesor revisara tu caso.")
            _asesor(db, conversacion, f"Ciudad sin cobertura: {valor}", turno)
            return
        if error is None:
            conversacion.datos = {**conversacion.datos, nodo["captura"]: valor}
            conversacion.fallos = 0
            _ir(db, conversacion, nodo["siguiente"], nodos, turno)
            return
    elif "opciones" in nodo:
        destino = nodo["opciones"].get(limpio)
        if destino:
            conversacion.fallos = 0
            _ir(db, conversacion, destino, nodos, turno)
            return
        if _pregunta_abierta(db, conversacion, texto, turno):
            return
    _fallo(db, conversacion, nodos, turno)


def _pregunta_abierta(
    db: Session, conversacion: ConversacionComercial, texto: str, turno: _Turno
) -> bool:
    """F4-IAA-02 Una pregunta que no es una opcion del menu: la IA responde dentro del
    guion aprobado o, si sale de el, pasa a un asesor. Sin IA disponible, no hace nada y la
    conversacion sigue su camino (cuenta como no entendida)."""
    from app.modules.ia import service as ia

    if len(texto.strip()) < 8:
        return False  # "ok", "si", "???": no es una pregunta
    try:
        respuesta = ia.responder_comercial(db, texto, conversacion.telefono)
    except ia.IANoDisponible:
        return False
    if respuesta is None:
        _asesor(db, conversacion, f"Pregunta fuera del guion: {texto[:200]}", turno)
        return True
    conversacion.fallos = 0
    turno.decir(respuesta)
    turno.decir("Escribe *menu* para ver las opciones.")
    return True


def _fallo(
    db: Session, conversacion: ConversacionComercial, nodos: dict[str, Any], turno: _Turno
) -> None:
    """F3-COM-04 Tras varios intentos sin entender, pasa a una persona."""
    conversacion.fallos += 1
    if conversacion.fallos >= MAX_FALLOS:
        _asesor(db, conversacion, "El asistente no logro entender a la persona", turno)
        return
    turno.decir("No te entendi. Responde con el numero de una opcion o escribe *asesor*.")
    nodo = nodos.get(conversacion.nodo) or nodos["inicio"]
    if "mensaje" in nodo:
        turno.decir(nodo["mensaje"])


def _ir(
    db: Session,
    conversacion: ConversacionComercial,
    destino: str,
    nodos: dict[str, Any],
    turno: _Turno,
) -> None:
    """Entra al nodo: ejecuta su accion, dice su mensaje y, si es un paso automatico,
    sigue al siguiente."""
    for _ in range(10):  # un arbol mal armado no puede dejar el bot en un ciclo
        conversacion.nodo = destino
        nodo = nodos[destino]
        accion = nodo.get("accion")
        if accion == "asesor":
            _asesor(db, conversacion, "La persona eligio hablar con un asesor", turno)
            return
        if accion and not _accion(db, conversacion, accion, turno):
            return
        if "mensaje" in nodo:
            turno.decir(nodo["mensaje"])
        if accion and "siguiente" in nodo:
            destino = nodo["siguiente"]
            continue
        return


def _interesado(db: Session, conversacion: ConversacionComercial) -> Interesado | None:
    return db.get(Interesado, conversacion.interesado_id) if conversacion.interesado_id else None


def _accion(db: Session, conversacion: ConversacionComercial, accion: str, turno: _Turno) -> bool:
    """Ejecuta la accion. Devuelve False si la conversacion no debe seguir sola."""
    from app.modules.cartera.periodos import formato_cop
    from app.modules.catalogos.models import Ciudad
    from app.modules.planes import service as planes

    interesado = _interesado(db, conversacion)
    if accion == "cobertura":
        ciudades = db.scalars(
            select(Ciudad.nombre).where(Ciudad.activa.is_(True)).order_by(Ciudad.nombre)
        )
        turno.decir("Atendemos en: " + ", ".join(ciudades) + ".")
        return True
    if accion == "recomendar":
        ciudad = conversacion.datos.get("ciudad")
        especies = conversacion.datos.get("mascotas") or []
        if not ciudad:
            turno.decir("Antes necesito saber tu ciudad.")
            conversacion.nodo = "pedir_ciudad"
            return False
        try:
            plan, motivo, _ = planes.recomendar(db, ciudad, especies)
        except NoEncontrado:
            turno.decir("No encontramos un plan para esa combinacion; un asesor te ayudara.")
            _asesor(db, conversacion, "Sin plan para la ciudad y las mascotas", turno)
            return False
        conversacion.datos = {**conversacion.datos, "plan": plan.codigo}
        if interesado is not None:
            interesado.ciudad = interesado.ciudad or ciudad
            interesado.plan_sugerido = plan.codigo
            interesado.datos = {**(interesado.datos or {}), "mascotas": especies}
            embudo.avanzar(interesado, "cotizado")
        turno.decir(
            f"Te recomendamos el {plan.nombre}: {formato_cop(plan.valor_mensual)} al mes. {motivo}."
        )
        return True
    if accion == "enlace_afiliacion":
        plan = conversacion.datos.get("plan", "")
        turno.decir(
            f"Afiliate en linea aqui: {settings.FRONTEND_URL}/afiliacion?plan={plan}. "
            "Si prefieres, escribe *asesor* y te acompanamos."
        )
        return True
    return True


def _asesor(db: Session, conversacion: ConversacionComercial, motivo: str, turno: _Turno) -> None:
    """F3-COM-04 Pasa la conversacion a una persona con todo el contexto: lo capturado,
    el motivo y los ultimos mensajes, en una tarea del responsable comercial."""
    from app.modules.comunicaciones.models import Mensaje
    from app.modules.tareas import service as tareas

    if conversacion.estado == "con_asesor":
        return
    interesado = _interesado(db, conversacion)
    asesor_id = (interesado.responsable_id if interesado else None) or embudo.asignar_responsable(
        db
    )
    ultimos = list(
        db.scalars(
            select(Mensaje.contenido)
            .where(Mensaje.destino == conversacion.telefono, Mensaje.direccion == "entrante")
            .order_by(Mensaje.created_at.desc())
            .limit(5)
        )
    )
    contexto = "; ".join(f"{k}: {v}" for k, v in conversacion.datos.items()) or "sin datos"
    tarea = tareas.crear(
        db,
        titulo=f"WhatsApp {conversacion.telefono}: pasar a asesor",
        descripcion=(
            f"Motivo: {motivo}. Datos capturados: {contexto}. "
            f"Ultimos mensajes: {' | '.join(m or '' for m in reversed(ultimos)) or '-'}"
        ),
        area="comercial",
        prioridad="alta",
        vence_en_dias=0,
        familia_id=interesado.familia_id if interesado else None,
        origen="conversacion",
    )
    if tarea is not None and asesor_id:
        tarea.asignada_a_id = asesor_id
    conversacion.estado = "con_asesor"
    conversacion.asesor_id = asesor_id
    conversacion.tarea_id = tarea.id if tarea else None
    turno.decir("Te comunico con un asesor de TIMU; te escribira en breve.")


def liberar(db: Session, conversacion: ConversacionComercial) -> ConversacionComercial:
    """El asesor termina: la proxima vez que la persona escriba, vuelve el asistente."""
    conversacion.estado = "automatica"
    conversacion.nodo = "inicio"
    conversacion.fallos = 0
    db.flush()
    return conversacion

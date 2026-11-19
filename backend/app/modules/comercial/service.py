"""6.11 Embudo comercial: todo interesado entra con su origen y un responsable."""

from datetime import date, datetime, time, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Session

from app.core.database import acotar_publico
from app.core.errores import NoEncontrado, ReglaNegocio
from app.core.eventos import EventoDominio, declarar_evento
from app.core.outbox import publicar
from app.core.tiempo import ZONA_NEGOCIO, ahora
from app.core.validaciones import normalizar_telefono
from app.modules.comercial.models import ConversacionComercial, Interesado
from app.modules.comunicaciones.models import Mensaje
from app.modules.tareas import service as tareas

ETAPAS = ("nuevo", "contactado", "cotizado", "en_afiliacion", "afiliado")
ABIERTAS = ("nuevo", "contactado", "cotizado", "en_afiliacion")
# La etapa a la que el equipo pasa a un interesado abierto. «afiliado» no: la pone la afiliacion.
SIGUIENTE = dict(zip(ABIERTAS[:-1], ABIERTAS[1:], strict=True))


def _telefono(valor: str | None) -> str | None:
    if not valor:
        return None
    try:
        return normalizar_telefono(valor)
    except ValueError:
        return "+" + valor.lstrip("+")


def asignar_responsable(db: Session) -> UUID | None:
    """El comercial activo con menos interesados abiertos (reparto por carga). Lo calcula la
    funcion comercial_con_menos_carga() de la base, que ve a todos los interesados: un
    formulario publico, que solo ve los suyos, tambien reparte bien."""
    return db.scalar(select(func.comercial_con_menos_carga(cast(list(ABIERTAS), ARRAY(String)))))


def registrar(
    db: Session,
    *,
    origen: str,
    telefono: str | None = None,
    nombre: str | None = None,
    email: str | None = None,
    ciudad: str | None = None,
    familia_id: UUID | None = None,
    etapa: str | None = None,
    datos: dict[str, Any] | None = None,
) -> Interesado:
    """Crea al interesado o actualiza el existente (mismo telefono o email). No pisa lo que
    ya se sabia ni lo hace retroceder en el embudo."""
    telefono = _telefono(telefono)
    email = email.lower() if email else None
    acotar_publico(db, contacto_telefono=telefono, contacto_email=email)
    condiciones = []
    if telefono:
        condiciones.append(Interesado.telefono == telefono)
    if email:
        condiciones.append(Interesado.email == email)
    if familia_id:
        condiciones.append(Interesado.familia_id == familia_id)
    if not condiciones:
        raise ReglaNegocio("El interesado necesita al menos telefono o email")
    interesado = db.scalar(select(Interesado).where(or_(*condiciones)).limit(1))
    if interesado is None:
        interesado = Interesado(
            origen=origen,
            etapa="nuevo",
            telefono=telefono,
            email=email,
            datos={},
            responsable_id=asignar_responsable(db),
        )
        db.add(interesado)
    for campo, valor in (("nombre", nombre), ("ciudad", ciudad), ("familia_id", familia_id)):
        if valor and not getattr(interesado, campo):
            setattr(interesado, campo, valor)
    if telefono and not interesado.telefono:
        interesado.telefono = telefono
    if email and not interesado.email:
        interesado.email = email
    if datos:
        interesado.datos = {**(interesado.datos or {}), **datos}
    if etapa:
        avanzar(interesado, etapa)
    interesado.ultimo_contacto = ahora()
    db.flush()
    return interesado


def avanzar(interesado: Interesado, etapa: str) -> None:
    """Solo hacia adelante; 'perdido' se marca con `perder`."""
    if interesado.etapa == "perdido" or etapa not in ETAPAS:
        return
    if ETAPAS.index(etapa) > ETAPAS.index(interesado.etapa):
        interesado.etapa = etapa


def perder(db: Session, interesado: Interesado, motivo: str) -> Interesado:
    if interesado.etapa == "afiliado":
        raise ReglaNegocio("Un interesado afiliado no se marca como perdido")
    interesado.etapa = "perdido"
    interesado.motivo_perdida = motivo
    db.flush()
    return interesado


def reactivar(db: Session, interesado: Interesado) -> Interesado:
    if interesado.etapa != "perdido":
        raise ReglaNegocio("Solo se reactiva un interesado perdido")
    interesado.etapa = "contactado"
    interesado.motivo_perdida = None
    db.flush()
    return interesado


def obtener(db: Session, interesado_id: UUID) -> Interesado:
    interesado = db.get(Interesado, interesado_id)
    if interesado is None:
        raise NoEncontrado("Interesado no encontrado")
    return interesado


def embudo(db: Session, desde: date, hasta: date) -> dict[str, Any]:
    """Interesados del periodo por etapa y por origen, y su conversion a afiliado."""
    inicio = datetime.combine(desde, time.min, ZONA_NEGOCIO)
    fin = datetime.combine(hasta + timedelta(days=1), time.min, ZONA_NEGOCIO)
    periodo = (
        select(Interesado)
        .where(Interesado.created_at >= inicio, Interesado.created_at < fin)
        .subquery()
    )
    por_etapa = dict(
        db.execute(select(periodo.c.etapa, func.count()).group_by(periodo.c.etapa)).tuples().all()
    )
    por_origen: dict[str, dict[str, int]] = {}
    for origen, etapa, n in db.execute(
        select(periodo.c.origen, periodo.c.etapa, func.count()).group_by(
            periodo.c.origen, periodo.c.etapa
        )
    ):
        fila = por_origen.setdefault(origen, {"total": 0, "afiliados": 0})
        fila["total"] += n
        fila["afiliados"] += n if etapa == "afiliado" else 0
    total = sum(por_etapa.values())
    return {
        "total": total,
        "por_etapa": {e: por_etapa.get(e, 0) for e in (*ETAPAS, "perdido")},
        "por_origen": por_origen,
        "conversion": round(por_etapa.get("afiliado", 0) / total, 3) if total else None,
    }


# --- R2-PAN-08/09 Listado con ficha: recuentos por etapa y la conversacion de cada interesado ---


def recuentos(db: Session, q: str | None = None) -> dict[str, int]:
    """Cuantos interesados hay en cada etapa, y abiertos en total, con la misma busqueda."""
    stmt = select(Interesado.etapa, func.count()).group_by(Interesado.etapa)
    if q:
        patron = f"%{q}%"
        stmt = stmt.where(or_(Interesado.nombre.ilike(patron), Interesado.telefono.ilike(patron)))
    por_etapa = {str(e): n for e, n in db.execute(stmt).tuples()}
    salida = {e: por_etapa.get(e, 0) for e in (*ETAPAS, "perdido")}
    salida["abiertos"] = sum(salida[e] for e in ABIERTAS)
    return salida


MENSAJES_DE_LA_CONVERSACION = 100


def conversacion_de(
    db: Session, interesado: Interesado
) -> tuple[ConversacionComercial | None, list[Mensaje]]:
    """La conversacion de WhatsApp de un interesado y sus ultimos mensajes, en orden."""
    if not interesado.telefono:
        return None, []
    conversacion = db.scalar(
        select(ConversacionComercial).where(ConversacionComercial.telefono == interesado.telefono)
    )
    recientes = list(
        db.scalars(
            select(Mensaje)
            .where(Mensaje.destino == interesado.telefono, Mensaje.canal == "whatsapp")
            .order_by(Mensaje.created_at.desc(), Mensaje.id.desc())
            .limit(MENSAJES_DE_LA_CONVERSACION)
        )
    )
    return conversacion, recientes[::-1]


# --- R3-PUB-04 El formulario de contacto de la portada -----------------------------------------

# El worker deja la tarea de responder: `publico`, que envia el formulario, no crea tareas.
EVENTO_CONTACTO_WEB = declarar_evento("comercial.contacto_web")

# Lo que la persona autoriza al enviar el formulario (Ley 1581): se guarda tal cual con su fecha.
AUTORIZACION_CONTACTO = (
    "Autorizo a TIMU a usar estos datos para responder mi mensaje y contarme de sus planes."
)


def contacto_web(
    db: Session,
    *,
    nombre: str,
    telefono: str | None,
    email: str | None,
    ciudad: str | None,
    mascota: str | None,
    especie: str | None,
    mensaje: str,
) -> Interesado:
    """Quien escribe desde la portada entra al embudo como interesado (6.11) con su
    mensaje, y el equipo comercial recibe una tarea para responderle."""
    interesado = registrar(
        db, origen="web", telefono=telefono, nombre=nombre, email=email, ciudad=ciudad
    )
    cuando = ahora().isoformat()
    mensajes = list((interesado.datos or {}).get("mensajes_web", []))
    mensajes.append({"fecha": cuando, "mascota": mascota, "especie": especie, "mensaje": mensaje})
    interesado.datos = {
        **(interesado.datos or {}),
        # Los ultimos veinte: un formulario abierto no puede crecer sin fin una fila.
        "mensajes_web": mensajes[-20:],
        "autorizacion_datos": {"texto": AUTORIZACION_CONTACTO, "aceptada_en": cuando},
    }
    db.flush()
    publicar(
        db,
        EventoDominio(EVENTO_CONTACTO_WEB, {"interesado_id": str(interesado.id), "fecha": cuando}),
    )
    return interesado


def tarea_contacto_web(db: Session, interesado_id: UUID, fecha: str) -> None:
    """La tarea de responder un mensaje de la portada, una por mensaje."""
    interesado = db.get(Interesado, interesado_id)
    if interesado is None:
        return
    mensaje = next(
        (m for m in interesado.datos.get("mensajes_web", []) if m["fecha"] == fecha), None
    )
    if mensaje is None:
        return
    quien = interesado.nombre or interesado.telefono or interesado.email
    tareas.crear(
        db,
        titulo=f"Responder el mensaje de la web de {quien}",
        area="comercial",
        vence_en_dias=1,
        descripcion=mensaje["mensaje"],
        familia_id=interesado.familia_id,
        origen="web",
        clave=f"contacto_web:{interesado.id}:{fecha}",
    )

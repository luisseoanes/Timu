"""6.1 Registro en linea: la familia elige ciudad, peludos y plan de cada uno, paga y despues
completa sus datos en un formulario.

1. `iniciar`: con la ciudad, los peludos (nombre, especie, plan), la forma de pago y el
   contacto del titular, cotiza en el backend y crea la solicitud, sus peludos y el pago. El
   navegador recibe un token para continuar sin esperar el mensaje.
2. El pago aprobado (service.completar) la deja `pagada` y envia el enlace del formulario.
3. `completar`: con el formulario crea o completa la familia (un documento existente completa
   su ficha), sus peludos y contactos, el acceso al portal con la contrasena elegida y la
   afiliacion. Si la familia ya tiene un contrato vigente no se afilia dos veces: el equipo
   decide.
4. `recordar` (beat): a las 24 horas reenvia el enlace; a las 48, tarea comercial.

Lo que no se paga: el enlace de pago vence a las 24 horas; tras un rechazo, `reintentar`
da otro pago a la misma solicitud. `cerrar_sin_pago` (beat) cancela a las 48 horas del
ultimo enlace y deja una tarea comercial, y `anonimizar_abandonados` (beat) borra a los seis
meses el contacto de lo que nunca se pago (Ley 1581).
"""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import acotar_publico, nuevo_id
from app.core.enums import EstadoPago
from app.core.errores import NoEncontrado, ReglaNegocio
from app.core.security import generar_token_opaco, hash_token
from app.core.tiempo import ZONA_NEGOCIO, ahora, hoy
from app.integrations.payments import construir_link_pago
from app.modules.afiliaciones import ciclo, documento, enlaces, service
from app.modules.afiliaciones.models import EstadoSolicitud, PeludoSolicitud, SolicitudAfiliacion
from app.modules.cartera import contratos
from app.modules.cartera.models import Pago
from app.modules.cartera.periodos import centavos, dinero, sumar_meses
from app.modules.comunicaciones import service as comunicaciones
from app.modules.familias import service as familias
from app.modules.familias.models import Familia, Mascota
from app.modules.familias.schemas import ContactoIn, FormularioFamilia, MascotaAlta
from app.modules.planes import service as planes
from app.modules.planes.models import CiudadPlan, Plan
from app.modules.tareas import service as tareas

RECORDAR_DESPUES = timedelta(hours=24)
TAREA_DESPUES = timedelta(hours=48)
VIGENCIA_ENLACE = timedelta(hours=24)
# Margen sobre la vigencia del enlace para los eventos que la pasarela entrega tarde.
CERRAR_SIN_PAGO = timedelta(hours=48)
RETENCION_SIN_PAGO_MESES = 6


def ciudades_con_cobertura(db: Session) -> list[str]:
    """Las ciudades donde se vende algun plan activo: el resto ve el aviso de cobertura."""
    return sorted(
        set(
            db.scalars(
                select(CiudadPlan.ciudad)
                .join(Plan, Plan.id == CiudadPlan.plan_id)
                .where(CiudadPlan.activa.is_(True), Plan.activo.is_(True))
            )
        )
    )


def planes_en(db: Session, ciudad: str) -> list[Plan]:
    planes_activos = db.scalars(select(Plan).where(Plan.activo.is_(True)).order_by(Plan.codigo))
    disponibles = [p for p in planes_activos if planes.disponible_en(p, ciudad)]
    return sorted(disponibles, key=lambda p: (planes.tarifa(p) or Decimal(0), p.codigo))


@dataclass
class Peludo:
    nombre: str
    especie: str
    plan_id: UUID


@dataclass
class Contacto:
    nombre: str
    telefono: str
    email: str


def iniciar(
    db: Session,
    *,
    ciudad: str,
    peludos: list[Peludo],
    periodicidad: str,
    contacto: Contacto,
    aceptacion: dict[str, Any],
) -> tuple[SolicitudAfiliacion, str, str]:
    """Devuelve la solicitud, el enlace de pago y el token del navegador. El valor sale del
    backend (planes.cotizar), nunca del navegador."""
    if ciudad not in ciudades_con_cobertura(db):
        raise ReglaNegocio(f"Por ahora no tenemos cobertura en {ciudad}")
    nombres = [p.nombre.strip().casefold() for p in peludos]
    if len(set(nombres)) != len(nombres):
        raise ReglaNegocio("Cada peludo necesita un nombre distinto")
    cot = planes.cotizar(db, ciudad, [(p.especie, p.plan_id) for p in peludos], periodicidad)
    valor = dinero(cot.valor_periodo)
    referencia = _referencia()
    solicitud_id = nuevo_id()
    acotar_publico(db, registro=solicitud_id, referencia_pago=referencia)
    token = generar_token_opaco()
    pago = _pago(db, referencia, valor)
    solicitud = SolicitudAfiliacion(
        id=solicitud_id,
        familia_id=None,
        ciudad=ciudad,
        contacto_nombre=contacto.nombre,
        contacto_telefono=contacto.telefono,
        contacto_email=contacto.email,
        token_hash=hash_token(token),
        periodicidad=periodicidad,
        valor_inicial=valor,
        referencia_pago=referencia,
        pago_id=pago.id,
        origen="formulario",
        aceptacion={
            **aceptacion,
            "version_terminos": documento.TERMINOS_VERSION,
            "fecha": ahora().isoformat(),
        },
    )
    db.add(solicitud)
    db.flush()
    db.add_all(
        PeludoSolicitud(
            solicitud_id=solicitud.id,
            posicion=posicion,
            nombre=peludo.nombre.strip(),
            especie=peludo.especie,
            plan_id=cotizado.plan.id,
            valor_mensual=dinero(cotizado.valor_mensual),
        )
        for posicion, (peludo, cotizado) in enumerate(
            zip(peludos, cot.peludos, strict=True), start=1
        )
    )
    db.flush()
    db.refresh(solicitud, ["peludos"])
    # Quien llega a pagar ya es un interesado: si no termina, comercial lo ve en el embudo.
    service.al_embudo(
        db,
        etapa="en_afiliacion",
        origen=solicitud.origen,
        plan=cot.peludos[0].plan.codigo,
        telefono=contacto.telefono,
        email=contacto.email,
        nombre=contacto.nombre,
        ciudad=ciudad,
    )
    return solicitud, _enlace(solicitud), token


def _referencia() -> str:
    return f"{service.PREFIJO}{uuid4().hex[:20].upper()}"


def _pago(db: Session, referencia: str, valor: Decimal) -> Pago:
    pago = Pago(
        id=nuevo_id(),
        familia_id=None,
        referencia_externa=referencia,
        proveedor="wompi",
        valor=valor,
        estado="pendiente",
    )
    db.add(pago)
    db.flush()
    return pago


def _enlace(solicitud: SolicitudAfiliacion) -> str:
    """Vence a las 24 horas: `cerrar_sin_pago` cancela despues sin dejar un enlace vivo."""
    return construir_link_pago(
        solicitud.referencia_pago,
        centavos(solicitud.valor_inicial),
        solicitud.contacto_email,
        redireccion=f"{settings.FRONTEND_URL}/afiliacion/resultado",
        vence=ahora() + VIGENCIA_ENLACE,
    )


def reintentar(db: Session, solicitud: SolicitudAfiliacion) -> str:
    """Tras un pago rechazado, otro pago para la misma solicitud, con referencia nueva: la
    pasarela no documenta que una referencia rechazada se pueda volver a usar. La anterior se
    guarda para reconocer un aprobado tardio con ella (`service.completar`). Con el contexto
    ya en `sistema`, como `completar`."""
    if solicitud.estado != EstadoSolicitud.PENDIENTE_PAGO or solicitud.familia_id is not None:
        raise ReglaNegocio("Este registro ya no espera un pago")
    anterior = db.get(Pago, solicitud.pago_id) if solicitud.pago_id else None
    if anterior is None or anterior.estado != EstadoPago.RECHAZADO:
        raise ReglaNegocio("Solo se puede reintentar un pago rechazado")
    referencia = _referencia()
    pago = _pago(db, referencia, solicitud.valor_inicial)
    solicitud.referencias_anteriores = [
        *solicitud.referencias_anteriores,
        solicitud.referencia_pago,
    ]
    solicitud.referencia_pago = referencia
    solicitud.pago_id = pago.id
    db.flush()
    return _enlace(solicitud)


def por_token(db: Session, token: str) -> SolicitudAfiliacion:
    """La solicitud del token del navegador o del enlace enviado. Un token que no casa no
    dice si existe otra solicitud."""
    huella = hash_token(token)
    acotar_publico(db, token_registro=huella)
    solicitud = db.scalar(
        select(SolicitudAfiliacion).where(
            or_(
                SolicitudAfiliacion.token_hash == huella,
                SolicitudAfiliacion.token_enlace_hash == huella,
            )
        )
    )
    if solicitud is None:
        raise NoEncontrado("El enlace no es valido")
    acotar_publico(db, registro=solicitud.id)
    db.refresh(solicitud, ["peludos"])
    return solicitud


def estado_pago(db: Session, solicitud: SolicitudAfiliacion) -> EstadoPago | None:
    """Quien vuelve de la pasarela con el pago rechazado ve que la solicitud sigue pendiente:
    con esto sabe que debe intentarlo de nuevo en vez de esperar una confirmacion."""
    acotar_publico(db, referencia_pago=solicitud.referencia_pago)
    pago = db.get(Pago, solicitud.pago_id) if solicitud.pago_id else None
    return EstadoPago(pago.estado) if pago else None


@dataclass
class DatosPeludo:
    posicion: int
    nombre: str
    raza: str | None
    sexo: str | None
    fecha_nacimiento: Any
    peso_kg: float
    esterilizada: bool | None = None


@dataclass
class Resultado:
    """`completada`: la afiliacion quedo activa. `revision`: el pago esta recibido y el
    equipo resuelve (ya habia un contrato vigente, el precio cambio...)."""

    estado: str
    mensaje: str
    familia: Familia | None = None
    clave_nueva: bool = False


def completar(
    db: Session,
    solicitud: SolicitudAfiliacion,
    *,
    titular: dict[str, Any],
    contactos: list[ContactoIn],
    clave: str,
    peludos: list[DatosPeludo],
) -> Resultado:
    """Con el contexto ya en `sistema`: el token del formulario es la credencial, como la
    firma de un webhook, y la afiliacion toca tablas que `publico` no escribe."""
    if solicitud.estado == EstadoSolicitud.COMPLETADA:
        return Resultado("completada", "Tu afiliacion ya esta activa: ingresa al portal")
    if solicitud.estado != EstadoSolicitud.PAGADA:
        raise ReglaNegocio("Aun no recibimos la confirmacion de tu pago")
    por_posicion = {p.posicion: p for p in peludos}
    if set(por_posicion) != {p.posicion for p in solicitud.peludos}:
        raise ReglaNegocio("Completa los datos de cada peludo")
    pago = db.get(Pago, solicitud.pago_id)
    assert pago is not None

    existente = db.scalar(
        select(Familia).where(
            and_(
                Familia.tipo_documento == titular["tipo_documento"],
                Familia.documento == titular["documento"],
            )
        )
    )
    if existente is not None and contratos.contrato_vigente(db, existente.id) is not None:
        return _a_revision(
            db,
            solicitud,
            existente.id,
            "Ya hay una afiliacion vigente con ese documento: decidir si se suman los peludos "
            "al contrato existente o se devuelve el pago.",
        )

    formulario = FormularioFamilia(
        **titular,
        ciudad=solicitud.ciudad,
        mascotas=[
            MascotaAlta(
                nombre=por_posicion[p.posicion].nombre,
                especie=p.especie,
                raza=por_posicion[p.posicion].raza,
                sexo=por_posicion[p.posicion].sexo,  # type: ignore[arg-type]
                fecha_nacimiento=por_posicion[p.posicion].fecha_nacimiento,
                peso_kg=por_posicion[p.posicion].peso_kg,
                esterilizada=por_posicion[p.posicion].esterilizada,
            )
            for p in solicitud.peludos
        ],
        origen="registro_en_linea",
    )
    resultado = familias.desde_formulario(db, formulario, agregar_mascota=ciclo.agregar_mascota)
    familia = familias.obtener(db, resultado.familia_id)
    db.refresh(familia, ["mascotas"])
    activas = {m.nombre.strip().casefold(): m for m in familia.mascotas if m.activa}
    for peludo in solicitud.peludos:
        mascota: Mascota | None = activas.get(por_posicion[peludo.posicion].nombre.casefold())
        if mascota is None or mascota.especie != peludo.especie:
            return _a_revision(
                db,
                solicitud,
                familia.id,
                f"No se pudo emparejar el peludo {peludo.nombre} con una mascota de la ficha.",
            )
        peludo.mascota_id = mascota.id
        peludo.nombre = mascota.nombre
        peludo.familia_id = familia.id
    for contacto in contactos:
        familias.agregar_contacto(db, familia, contacto)

    clave_nueva = familia.usuario_portal_id is None
    familias.habilitar_portal(db, familia, clave)
    solicitud.familia_id = familia.id
    pago.familia_id = familia.id
    comunicaciones.asignar_familia(
        db,
        familia.id,
        [d for d in (solicitud.contacto_email, solicitud.contacto_telefono) if d],
        solicitud.created_at,
    )
    db.flush()
    if not service.completar_o_dejar_tarea(db, solicitud, pago):
        return Resultado(
            "revision",
            "Recibimos tu pago y tus datos; un asesor te contactara para terminar la afiliacion",
            familia,
        )
    return Resultado("completada", "Tu afiliacion quedo activa", familia, clave_nueva)


def _a_revision(
    db: Session, solicitud: SolicitudAfiliacion, familia_id: UUID, motivo: str
) -> Resultado:
    solicitud.estado = EstadoSolicitud.ERROR
    solicitud.error = motivo
    tareas.crear(
        db,
        titulo="Registro en linea pagado que requiere revision",
        descripcion=f"Referencia {solicitud.referencia_pago}: {motivo}",
        area="comercial",
        prioridad="alta",
        vence_en_dias=1,
        familia_id=familia_id,
        origen="afiliacion",
        clave=f"registro_revision:{solicitud.id}",
    )
    db.flush()
    return Resultado(
        "revision",
        "Recibimos tu pago; un asesor te contactara para terminar la afiliacion",
    )


def recordar(db: Session) -> tuple[int, int]:
    """Registros pagados sin formulario: a las 24 horas se reenvia el enlace (una vez) y a
    las 48 el equipo recibe una tarea para llamar. Repetible: la tarea es una por registro."""
    momento = ahora()
    pagadas = list(
        db.scalars(
            select(SolicitudAfiliacion).where(
                SolicitudAfiliacion.estado == EstadoSolicitud.PAGADA,
                SolicitudAfiliacion.pagada_en <= momento - RECORDAR_DESPUES,
            )
        )
    )
    recordadas = llamadas = 0
    for solicitud in pagadas:
        if solicitud.recordada_en is None:
            enlaces.enviar(db, solicitud)
            solicitud.recordada_en = momento
            recordadas += 1
        assert solicitud.pagada_en is not None
        if solicitud.pagada_en <= momento - TAREA_DESPUES:
            tarea = tareas.crear(
                db,
                titulo="Registro pagado sin formulario",
                descripcion=(
                    f"{solicitud.contacto_nombre} ({solicitud.contacto_telefono}) pago la "
                    f"afiliacion {solicitud.referencia_pago} hace mas de 48 horas y no ha "
                    "completado sus datos: llamar para terminarla."
                ),
                area="comercial",
                prioridad="alta",
                vence_en_dias=1,
                origen="afiliacion",
                clave=f"registro_sin_formulario:{solicitud.id}",
            )
            llamadas += tarea is not None
    db.flush()
    return recordadas, llamadas


def cerrar_sin_pago(db: Session) -> tuple[int, int]:
    """Registros sin pagar a las 48 horas del ultimo enlace: se cancelan, su pago pendiente se
    anula y comercial recibe una tarea para contactar, salvo que esa persona ya se haya
    afiliado por otra via. Un pago ya aprobado no se toca: lo resuelve `service.completar`."""
    limite = ahora() - CERRAR_SIN_PAGO
    vencidas = list(
        db.scalars(
            select(SolicitudAfiliacion)
            .join(Pago, Pago.id == SolicitudAfiliacion.pago_id)
            .where(
                SolicitudAfiliacion.estado == EstadoSolicitud.PENDIENTE_PAGO,
                SolicitudAfiliacion.familia_id.is_(None),
                Pago.created_at <= limite,
            )
        )
    )
    canceladas = avisos = 0
    for solicitud in vencidas:
        # Un dato raro en un registro no revierte el lote.
        with db.begin_nested():
            pago = db.get(Pago, solicitud.pago_id)
            assert pago is not None
            if pago.estado == EstadoPago.APROBADO:
                continue
            if pago.estado == EstadoPago.PENDIENTE:
                pago.estado = EstadoPago.ANULADO
            solicitud.estado = EstadoSolicitud.CANCELADA
            canceladas += 1
            if not _ya_afiliado(db, solicitud):
                avisos += _tarea_sin_pago(db, solicitud, pago) is not None
    db.flush()
    return canceladas, avisos


def _ya_afiliado(db: Session, solicitud: SolicitudAfiliacion) -> bool:
    """La misma persona (telefono o correo) ya es familia o pago otro registro."""
    familia = db.scalar(
        select(Familia.id)
        .where(
            or_(
                Familia.telefono == solicitud.contacto_telefono,
                Familia.email == solicitud.contacto_email,
            )
        )
        .limit(1)
    )
    if familia is not None:
        return True
    otra = db.scalar(
        select(SolicitudAfiliacion.id)
        .where(
            SolicitudAfiliacion.id != solicitud.id,
            SolicitudAfiliacion.estado.in_(
                [EstadoSolicitud.PAGADA, EstadoSolicitud.COMPLETADA, EstadoSolicitud.ERROR]
            ),
            or_(
                SolicitudAfiliacion.contacto_telefono == solicitud.contacto_telefono,
                SolicitudAfiliacion.contacto_email == solicitud.contacto_email,
            ),
        )
        .limit(1)
    )
    return otra is not None


def _tarea_sin_pago(db: Session, solicitud: SolicitudAfiliacion, pago: Pago) -> object:
    peludos = ", ".join(f"{p.nombre} ({p.especie})" for p in solicitud.peludos)
    motivo = "la pasarela rechazo el pago" if pago.estado == EstadoPago.RECHAZADO else "no pago"
    return tareas.crear(
        db,
        titulo="Registro en linea sin pagar",
        descripcion=(
            f"{solicitud.contacto_nombre} ({solicitud.contacto_telefono}, "
            f"{solicitud.contacto_email}) eligio planes en {solicitud.ciudad} para {peludos} "
            f"por {centavos(solicitud.valor_inicial) // 100} pesos y {motivo}: contactar."
        ),
        area="comercial",
        prioridad="media",
        vence_en_dias=2,
        origen="afiliacion",
        clave=f"registro_sin_pago:{solicitud.id}",
    )


def anonimizar_abandonados(db: Session) -> int:
    """Ley 1581: el contacto de los registros que nunca se pagaron se conserva seis meses
    para el seguimiento comercial; despues lo borra anonimizar_registros_abandonados() de la
    base, tambien su rastro en la bitacora, el interesado que creo y la tarea del cierre."""
    limite = datetime.combine(sumar_meses(hoy(), -RETENCION_SIN_PAGO_MESES), time.min)
    return int(
        db.scalar(
            text("SELECT anonimizar_registros_abandonados(:limite)"),
            {"limite": limite.replace(tzinfo=ZONA_NEGOCIO)},
        )
        or 0
    )

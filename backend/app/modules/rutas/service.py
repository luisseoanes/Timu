"""6.7 Rutas domiciliarias: planeacion, optimizacion, ejecucion y cambios en caliente."""

from datetime import date, datetime, time, timedelta
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import EstadoServicio, TipoServicio
from app.core.errores import NoEncontrado, ReglaNegocio
from app.core.eventos import EventoDominio
from app.core.outbox import publicar
from app.core.tiempo import ZONA_NEGOCIO, ahora, con_zona
from app.integrations.routing import Coordenada, Visita, insertar_mas_barato, optimizar
from app.modules.catalogos.models import Ciudad, TipoServicioCatalogo
from app.modules.familias.models import Familia, Mascota
from app.modules.rutas import distancias
from app.modules.rutas.models import ParadaRuta, PlanificacionRuta, Ruta
from app.modules.servicios.models import Servicio

logger = structlog.get_logger(__name__)

EVENTO_PLANIFICACION = "rutas.planificacion_solicitada"
# Modalidades que se atienden en casa de la familia.
MODALIDADES_EN_CASA = (TipoServicio.DOMICILIARIO, TipoServicio.PREVENTIVO)

PLANTILLA_VENTANA = "ventana_llegada"
PLANTILLA_EN_CAMINO = "tecnico_en_camino"


def _segundos(dt: datetime) -> int:
    local = con_zona(dt).astimezone(ZONA_NEGOCIO)
    return local.hour * 3600 + local.minute * 60 + local.second


def _instante(fecha: date, segundos: int) -> datetime:
    return datetime.combine(fecha, time.min, ZONA_NEGOCIO) + timedelta(seconds=segundos)


def _hora(texto: str) -> int:
    h, m = (int(x) for x in texto.split(":"))
    return h * 3600 + m * 60


# --- F2-RUT-01 Planeacion -----------------------------------------------------------------------


def solicitar(
    db: Session, fecha: date, ciudad: str, responsables: list[UUID], usuario_id: UUID | None
) -> PlanificacionRuta:
    """Registra la solicitud; el worker la resuelve (la optimizacion es CPU-bound)."""
    from app.modules.auth.models import Usuario

    if not responsables:
        raise ReglaNegocio("Indique al menos un responsable para las rutas")
    activos = set(
        db.scalars(select(Usuario.id).where(Usuario.id.in_(responsables), Usuario.activo.is_(True)))
    )
    if len(activos) != len(set(responsables)):
        raise ReglaNegocio("Hay responsables inexistentes o inactivos")
    planificacion = PlanificacionRuta(
        fecha=fecha,
        ciudad=ciudad,
        responsables=[str(r) for r in dict.fromkeys(responsables)],
        solicitada_por_id=usuario_id,
    )
    db.add(planificacion)
    db.flush()
    publicar(db, EventoDominio(EVENTO_PLANIFICACION, {"planificacion_id": str(planificacion.id)}))
    return planificacion


def por_rutear(db: Session, fecha: date, ciudad: str) -> list[Servicio]:
    """Servicios en casa de la familia, agendados para ese dia y ciudad, sin ruta aun."""
    inicio = datetime.combine(fecha, time.min, ZONA_NEGOCIO)
    return list(
        db.scalars(
            select(Servicio)
            .where(
                Servicio.ciudad == ciudad,
                Servicio.tipo.in_(MODALIDADES_EN_CASA),
                Servicio.estado == EstadoServicio.AGENDADO,
                Servicio.ruta_id.is_(None),
                Servicio.programado_para >= inicio,
                Servicio.programado_para < inicio + timedelta(days=1),
            )
            .order_by(Servicio.programado_para)
        )
    )


def _base(db: Session, ciudad: str) -> Coordenada:
    c = db.scalar(select(Ciudad).where(Ciudad.nombre == ciudad))
    if c is None or c.latitud is None or c.longitud is None:
        raise ReglaNegocio(f"La ciudad {ciudad} no tiene coordenadas de base en el catalogo")
    return c.latitud, c.longitud


def _duracion(db: Session, servicio: Servicio) -> int:
    minutos = db.scalar(
        select(TipoServicioCatalogo.duracion_min).where(
            TipoServicioCatalogo.codigo == servicio.tipo_codigo
        )
    )
    return (minutos or 30) * 60


def _visita(db: Session, servicio: Servicio) -> Visita:
    """F2-RUT-03 La atencion empieza dentro de la ventana acordada con la familia: desde
    la hora agendada hasta RUTA_VENTANA_LLEGADA_MIN despues."""
    assert servicio.programado_para is not None
    inicio = _segundos(servicio.programado_para)
    return Visita(
        inicio_min=inicio,
        inicio_max=inicio + settings.RUTA_VENTANA_LLEGADA_MIN * 60,
        duracion=_duracion(db, servicio),
    )


def planificar(db: Session, planificacion_id: UUID) -> PlanificacionRuta:
    """Agrupa los servicios del dia en rutas, una por responsable, y las ordena con
    tiempos reales. Lo que no cabe (sin ubicacion, fuera de la jornada, sobre la
    capacidad) queda sin asignar con su motivo."""
    planificacion = db.get(PlanificacionRuta, planificacion_id, with_for_update=True)
    if planificacion is None:
        raise NoEncontrado("Planificacion no encontrada")
    if planificacion.estado != "pendiente":
        return planificacion

    servicios = por_rutear(db, planificacion.fecha, planificacion.ciudad)
    sin_asignar: list[dict[str, str]] = []
    ubicables: list[tuple[Servicio, Familia]] = []
    for servicio in servicios:
        familia = db.get(Familia, servicio.familia_id)
        assert familia is not None
        if familia.latitud is None or familia.longitud is None:
            sin_asignar.append({"servicio_id": str(servicio.id), "motivo": "sin_ubicacion"})
        else:
            ubicables.append((servicio, familia))

    base = _base(db, planificacion.ciudad)
    puntos: list[Coordenada] = [base] + [(f.latitud, f.longitud) for _, f in ubicables]  # type: ignore[misc]
    metros, segundos = distancias.matriz(db, puntos)
    plan = optimizar(
        segundos,
        [_visita(db, s) for s, _ in ubicables],
        vehiculos=len(planificacion.responsables),
        capacidad=settings.RUTA_MAX_ATENCIONES,
        jornada=(_hora(settings.RUTA_JORNADA_INICIO), _hora(settings.RUTA_JORNADA_FIN)),
        segundos_busqueda=settings.RUTA_SEGUNDOS_OPTIMIZACION,
    )

    rutas_creadas = 0
    for responsable, recorrido in zip(planificacion.responsables, plan.rutas, strict=True):
        if not recorrido:
            continue
        ruta = Ruta(
            fecha=planificacion.fecha,
            ciudad=planificacion.ciudad,
            responsable_id=UUID(responsable),
            planificacion_id=planificacion.id,
        )
        db.add(ruta)
        db.flush()
        anterior = 0
        total_m = 0
        for orden, (nodo, llegada) in enumerate(recorrido, start=1):
            servicio, familia = ubicables[nodo - 1]
            total_m += metros[anterior][nodo]
            anterior = nodo
            ruta.paradas.append(
                ParadaRuta(
                    servicio_id=servicio.id,
                    orden=orden,
                    latitud=familia.latitud,
                    longitud=familia.longitud,
                    llegada_estimada=_instante(planificacion.fecha, llegada),
                )
            )
            servicio.ruta_id = ruta.id
            servicio.profesional_id = UUID(responsable)
        total_m += metros[anterior][0]
        ruta.distancia_km = round(total_m / 1000, 1)
        primera = recorrido[0][1] - segundos[0][recorrido[0][0]]
        ultima_nodo, ultima_llegada = recorrido[-1]
        fin = (
            ultima_llegada + _duracion(db, ubicables[ultima_nodo - 1][0]) + segundos[ultima_nodo][0]
        )
        ruta.duracion_min = max(0, (fin - primera) // 60)
        rutas_creadas += 1
    for nodo in plan.descartados:
        sin_asignar.append(
            {"servicio_id": str(ubicables[nodo - 1][0].id), "motivo": "no_cabe_en_la_jornada"}
        )

    planificacion.estado = "lista"
    planificacion.resultado = {
        "rutas": rutas_creadas,
        "asignados": len(ubicables) - len(plan.descartados),
        "sin_asignar": sin_asignar,
    }
    db.flush()
    for ruta in db.scalars(select(Ruta).where(Ruta.planificacion_id == planificacion.id)):
        avisar_ventanas(db, ruta)
    return planificacion


def fallo_planificacion(db: Session, planificacion_id: UUID, error: str) -> None:
    planificacion = db.get(PlanificacionRuta, planificacion_id)
    if planificacion is not None and planificacion.estado == "pendiente":
        planificacion.estado = "fallida"
        planificacion.error = error[:2000]
        db.flush()


# --- Consultas ----------------------------------------------------------------------------------


def obtener(db: Session, ruta_id: UUID) -> Ruta:
    ruta = db.get(Ruta, ruta_id)
    if ruta is None:
        raise NoEncontrado("Ruta no encontrada")
    return ruta


def obtener_parada(db: Session, parada_id: UUID) -> ParadaRuta:
    parada = db.get(ParadaRuta, parada_id)
    if parada is None:
        raise NoEncontrado("Parada no encontrada")
    return parada


def cancelar(db: Session, ruta: Ruta) -> Ruta:
    """Deshace una ruta que aun no arranca: sus servicios vuelven a quedar por rutear."""
    if ruta.estado != "planificada":
        raise ReglaNegocio("Solo se cancela una ruta que no ha arrancado")
    for parada in ruta.paradas:
        servicio = db.get(Servicio, parada.servicio_id)
        if servicio is not None and servicio.ruta_id == ruta.id:
            servicio.ruta_id = None
    ruta.estado = "cancelada"
    db.flush()
    return ruta


# --- F2-RUT-04 Ejecucion ------------------------------------------------------------------------


def _servicio(db: Session, parada: ParadaRuta) -> Servicio:
    servicio = db.get(Servicio, parada.servicio_id)
    assert servicio is not None
    return servicio


def iniciar(db: Session, ruta: Ruta, usuario_id: UUID) -> Ruta:
    if ruta.estado != "planificada":
        raise ReglaNegocio("La ruta ya arranco o fue cancelada")
    if ruta.responsable_id not in (None, usuario_id):
        raise ReglaNegocio("Solo el responsable arranca la ruta")
    ruta.estado = "en_curso"
    ruta.inicio_real = ahora()
    db.flush()
    return ruta


def _en_curso(parada: ParadaRuta) -> None:
    if parada.ruta.estado != "en_curso":
        raise ReglaNegocio("La ruta no esta en curso")


def en_camino(db: Session, parada: ParadaRuta, usuario_id: UUID) -> ParadaRuta:
    """El tecnico sale hacia la familia: el servicio pasa a en ruta y se le avisa."""
    from app.modules.servicios import service as servicios

    _en_curso(parada)
    if parada.estado != "pendiente":
        raise ReglaNegocio("La parada ya fue atendida o esta en curso")
    otra = next(
        (
            p
            for p in parada.ruta.paradas
            if p.estado in ("en_camino", "en_sitio") and p is not parada
        ),
        None,
    )
    if otra is not None:
        raise ReglaNegocio("Cierre la parada en curso antes de salir hacia otra")
    servicios.cambiar_estado(db, _servicio(db, parada), EstadoServicio.EN_RUTA, actor_id=usuario_id)
    parada.estado = "en_camino"
    _aviso(db, parada, PLANTILLA_EN_CAMINO, "aviso_en_camino_en")
    db.flush()
    return parada


def llegada(db: Session, parada: ParadaRuta, usuario_id: UUID) -> ParadaRuta:
    from app.modules.servicios import service as servicios

    _en_curso(parada)
    if parada.estado not in ("pendiente", "en_camino"):
        raise ReglaNegocio("La llegada ya se registro")
    servicios.cambiar_estado(
        db, _servicio(db, parada), EstadoServicio.EN_ATENCION, actor_id=usuario_id
    )
    parada.estado = "en_sitio"
    parada.llegada_en = ahora()
    db.flush()
    return parada


def salida(
    db: Session,
    parada: ParadaRuta,
    usuario_id: UUID,
    *,
    nota: str | None,
    evidencia: bytes | None = None,
    nombre_evidencia: str | None = None,
) -> ParadaRuta:
    """Cierra la visita: el servicio se completa (si tiene sus pasos obligatorios) y la
    evidencia queda guardada. Con la ultima parada, la ruta termina."""
    from app.modules.archivos import service as archivos
    from app.modules.servicios import service as servicios

    _en_curso(parada)
    if parada.estado != "en_sitio":
        raise ReglaNegocio("Registre la llegada antes de la salida")
    servicios.cambiar_estado(
        db, _servicio(db, parada), EstadoServicio.COMPLETADO, actor_id=usuario_id
    )
    if evidencia:
        archivo = archivos.subir(
            db,
            evidencia,
            nombre=nombre_evidencia,
            proposito="adjunto_clinico",
            usuario_id=usuario_id,
        )
        parada.evidencia_archivo_id = archivo.id
    parada.nota = nota
    parada.estado = "completada"
    parada.salida_en = ahora()
    _quizas_finalizar(parada.ruta)
    db.flush()
    return parada


def _quizas_finalizar(ruta: Ruta) -> None:
    if all(p.estado in ("completada", "omitida") for p in ruta.paradas):
        ruta.estado = "finalizada"
        ruta.fin_real = ahora()


# --- F2-RUT-05 Cambios en caliente --------------------------------------------------------------


def _coordenada(parada: ParadaRuta) -> Coordenada:
    assert parada.latitud is not None and parada.longitud is not None
    return parada.latitud, parada.longitud


def _pendientes(ruta: Ruta) -> list[ParadaRuta]:
    return [p for p in ruta.paradas if p.estado == "pendiente"]


def _renumerar(ruta: Ruta, pendientes: list[ParadaRuta] | None = None) -> None:
    """Lo recorrido conserva su orden, lo pendiente sigue y lo omitido va al final."""
    por_orden = sorted(ruta.paradas, key=lambda p: p.orden)
    hechas = [p for p in por_orden if p.estado not in ("pendiente", "omitida")]
    omitidas = [p for p in por_orden if p.estado == "omitida"]
    if pendientes is None:
        pendientes = [p for p in por_orden if p.estado == "pendiente"]
    for orden, p in enumerate([*hechas, *pendientes, *omitidas], start=1):
        p.orden = orden


def recalcular_llegadas(db: Session, ruta: Ruta) -> None:
    """Reestima la llegada de lo que falta: desde la ultima parada cerrada (o la base) se
    suman viaje y atencion, esperando cuando se llega antes de la ventana."""
    pendientes = sorted(_pendientes(ruta), key=lambda p: p.orden)
    if not pendientes:
        return
    cerradas = [p for p in ruta.paradas if p.estado != "pendiente" and p.latitud is not None]
    cerradas.sort(key=lambda p: p.orden)
    if cerradas:
        ultima = cerradas[-1]
        origen: Coordenada = (ultima.latitud, ultima.longitud)  # type: ignore[assignment]
        reloj = _segundos(ultima.salida_en or ultima.llegada_en or ahora())
    else:
        origen = _base(db, ruta.ciudad)
        reloj = (
            _segundos(ruta.inicio_real) if ruta.inicio_real else _hora(settings.RUTA_JORNADA_INICIO)
        )
    puntos = [origen] + [_coordenada(p) for p in pendientes]
    _, segundos = distancias.matriz(db, puntos)
    anterior = 0
    for i, parada in enumerate(pendientes, start=1):
        servicio = _servicio(db, parada)
        visita = _visita(db, servicio)
        llegada_s = max(reloj + segundos[anterior][i], visita.inicio_min)
        parada.llegada_estimada = _instante(ruta.fecha, llegada_s)
        reloj = llegada_s + visita.duracion
        anterior = i


def omitir(
    db: Session, parada: ParadaRuta, motivo: str, *, cancelar_servicio: bool, usuario_id: UUID
) -> ParadaRuta:
    """Saca la parada de la ruta; las demas se renumeran y se reestima su llegada. El
    servicio se cancela o vuelve a quedar por rutear."""
    from app.modules.servicios import service as servicios

    if parada.estado in ("completada", "omitida"):
        raise ReglaNegocio("La parada ya esta cerrada")
    servicio = _servicio(db, parada)
    if cancelar_servicio:
        servicios.cambiar_estado(
            db, servicio, EstadoServicio.CANCELADO, motivo, actor_id=usuario_id
        )
    else:
        servicio.ruta_id = None
        servicio.profesional_id = None
        if servicio.estado != EstadoServicio.AGENDADO:
            raise ReglaNegocio("Solo un servicio aun no atendido vuelve a quedar por rutear")
    parada.estado = "omitida"
    parada.motivo_omision = motivo
    ruta = parada.ruta
    _renumerar(ruta)
    if ruta.estado == "en_curso":
        _quizas_finalizar(ruta)
    recalcular_llegadas(db, ruta)
    db.flush()
    return parada


def agregar(db: Session, ruta: Ruta, servicio_id: UUID) -> ParadaRuta:
    """Inserta un servicio en la posicion que menos tiempo agrega, sin tocar lo ya
    recorrido ni reordenar a mano el resto."""
    if ruta.estado not in ("planificada", "en_curso"):
        raise ReglaNegocio("La ruta esta cerrada")
    servicio = db.get(Servicio, servicio_id)
    if servicio is None:
        raise NoEncontrado("Servicio no encontrado")
    if servicio.ruta_id is not None:
        raise ReglaNegocio("El servicio ya esta en una ruta")
    if servicio.estado != EstadoServicio.AGENDADO or servicio.ciudad != ruta.ciudad:
        raise ReglaNegocio("Solo se agrega un servicio agendado de la misma ciudad")
    if (
        servicio.programado_para is None
        or con_zona(servicio.programado_para).astimezone(ZONA_NEGOCIO).date() != ruta.fecha
    ):
        raise ReglaNegocio("El servicio no es de la fecha de la ruta")
    activas = [p for p in ruta.paradas if p.estado != "omitida"]
    if len(activas) >= settings.RUTA_MAX_ATENCIONES:
        raise ReglaNegocio("La ruta ya tiene el maximo de atenciones del tecnico")
    familia = db.get(Familia, servicio.familia_id)
    assert familia is not None
    if familia.latitud is None or familia.longitud is None:
        raise ReglaNegocio("La familia no tiene ubicacion; no se puede rutear")

    pendientes = sorted(_pendientes(ruta), key=lambda p: p.orden)
    base = _base(db, ruta.ciudad)
    nuevo: Coordenada = (familia.latitud, familia.longitud)
    puntos = [base] + [_coordenada(p) for p in pendientes] + [nuevo]
    _, segundos = distancias.matriz(db, puntos)
    secuencia = list(range(1, len(pendientes) + 1))
    posicion = insertar_mas_barato(segundos, secuencia, len(puntos) - 1)

    parada = ParadaRuta(
        servicio_id=servicio.id, orden=0, latitud=familia.latitud, longitud=familia.longitud
    )
    ruta.paradas.append(parada)
    nuevas_pendientes = [*pendientes[:posicion], parada, *pendientes[posicion:]]
    _renumerar(ruta, nuevas_pendientes)
    servicio.ruta_id = ruta.id
    servicio.profesional_id = ruta.responsable_id
    db.flush()
    recalcular_llegadas(db, ruta)
    _aviso(db, parada, PLANTILLA_VENTANA, "aviso_ventana_en")
    db.flush()
    return parada


# --- F2-RUT-06 Avisos ---------------------------------------------------------------------------


def _aviso(db: Session, parada: ParadaRuta, plantilla: str, marca: str) -> None:
    """Una sola vez por parada y tipo de aviso. Sin plantilla aprobada se registra y la
    operacion sigue: un aviso que no sale no frena la ruta."""
    from app.modules.comunicaciones import service as comunicaciones

    if getattr(parada, marca) is not None:
        return
    servicio = _servicio(db, parada)
    familia = db.get(Familia, servicio.familia_id)
    mascota = db.get(Mascota, servicio.mascota_id) if servicio.mascota_id else None
    assert familia is not None
    if plantilla == PLANTILLA_VENTANA:
        if parada.llegada_estimada is None:
            return
        margen = timedelta(minutes=settings.RUTA_AVISO_MARGEN_MIN)
        eta = con_zona(parada.llegada_estimada).astimezone(ZONA_NEGOCIO)
        variables = [
            familia.titular_nombre,
            f"{eta - margen:%I:%M %p}",
            f"{eta + margen:%I:%M %p}",
        ]
    else:
        variables = [familia.titular_nombre, mascota.nombre if mascota else "tu mascota"]
    try:
        with db.begin_nested():
            comunicaciones.encolar_plantilla(
                db,
                telefono=familia.telefono,
                plantilla=plantilla,
                variables=variables,
                familia_id=familia.id,
            )
            setattr(parada, marca, ahora())
    except Exception as e:  # noqa: BLE001
        logger.error("Aviso %s sin enviar para la parada %s: %s", plantilla, parada.id, e)


def avisar_ventanas(db: Session, ruta: Ruta) -> int:
    enviados = 0
    for parada in _pendientes(ruta):
        antes = parada.aviso_ventana_en
        _aviso(db, parada, PLANTILLA_VENTANA, "aviso_ventana_en")
        enviados += antes is None and parada.aviso_ventana_en is not None
    db.flush()
    return enviados


def presentar(ruta: Ruta) -> dict[str, Any]:
    return {
        "id": ruta.id,
        "fecha": ruta.fecha,
        "ciudad": ruta.ciudad,
        "responsable_id": ruta.responsable_id,
        "estado": ruta.estado,
        "distancia_km": ruta.distancia_km,
        "duracion_min": ruta.duracion_min,
        "inicio_real": ruta.inicio_real,
        "fin_real": ruta.fin_real,
        "paradas": [
            {
                "id": p.id,
                "servicio_id": p.servicio_id,
                "orden": p.orden,
                "estado": p.estado,
                "latitud": p.latitud,
                "longitud": p.longitud,
                "llegada_estimada": p.llegada_estimada,
                "llegada_en": p.llegada_en,
                "salida_en": p.salida_en,
                "nota": p.nota,
                "motivo_omision": p.motivo_omision,
            }
            for p in sorted(ruta.paradas, key=lambda p: p.orden)
        ],
    }

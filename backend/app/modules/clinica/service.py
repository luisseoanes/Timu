"""6.14 / 6.17 Historia clinica, adjuntos, formulas y atencion veterinaria virtual."""

import re
import unicodedata
from typing import Any, Literal
from uuid import UUID

import structlog
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.core.enums import EstadoServicio, Rol
from app.core.errores import Conflicto, NoEncontrado, Prohibido, ReglaNegocio
from app.core.eventos import declarar_evento
from app.core.plantillas import declarar_plantilla
from app.core.scope import Alcance, restringir
from app.core.tiempo import ahora, hoy
from app.modules.archivos import service as archivos
from app.modules.archivos.models import Archivo
from app.modules.auth.models import Usuario
from app.modules.cartera import contratos
from app.modules.catalogos import service as catalogos
from app.modules.clinica import documento
from app.modules.clinica.models import (
    AdjuntoClinico,
    Formula,
    HistoriaClinica,
    PlantillaConsulta,
    RespuestaVirtual,
    SolicitudVirtual,
)
from app.modules.comunicaciones import service as comunicaciones
from app.modules.familias.models import Familia, Mascota
from app.modules.servicios import service as servicios
from app.modules.servicios.models import Servicio, ServicioPaso

logger = structlog.get_logger(__name__)

# 6.17 El medico pide a la IA un borrador de respuesta para la solicitud virtual.
EVENTO_BORRADOR = declarar_evento("ia.borrador_solicitado")

CAMPOS_CLINICOS = ("motivo", "anamnesis", "examen_fisico", "diagnostico", "tratamiento")

# 6.14 Lo que ve cada perfil. El medico y el admin ven la historia completa; el resto
# del equipo, lo necesario para operar (cuando, por que y quien); la familia, todo lo
# clinico menos lo de uso interno.
Vista = Literal["completa", "resumen", "familia"]
_CAMPOS_RESUMEN = {"id", "mascota_id", "fecha", "tipo", "motivo", "estado", "profesional_id"}
_OCULTOS_FAMILIA = {"notas_internas"}


# R2-PAN-07 La consulta es el registro de la visita: al firmarla, cada paso del servicio que
# pide uno de estos campos se registra con lo que dice la consulta, y el medico no escribe dos
# veces lo mismo. Un paso con un campo que no esta aqui (el lote de una vacuna) sigue pidiendose
# en el servicio.
_PASOS_DESDE_LA_CONSULTA = {
    "hallazgos": lambda e: "\n".join(
        x for x in (e.examen_fisico, e.diagnostico and f"Diagnostico: {e.diagnostico}") if x
    ),
    "recomendaciones": lambda e: e.tratamiento,
}


catalogos.conectar_campos_de_la_consulta(frozenset(_PASOS_DESDE_LA_CONSULTA))

# Fuera de la ventana de 24 h, el aviso de que la respuesta esta en el portal (6.17).
PLANTILLA_RESPUESTA = declarar_plantilla(
    "respuesta_virtual", "Respuesta de la atención virtual", "el aviso de la respuesta virtual"
)


def vista_para(rol: Rol) -> Vista:
    if rol in (Rol.MEDICO, Rol.ADMIN):
        return "completa"
    if rol == Rol.FAMILIA:
        return "familia"
    return "resumen"


def presentar(entrada: HistoriaClinica, vista: Vista) -> dict[str, Any]:
    datos = {
        c.key: getattr(entrada, c.key)
        for c in HistoriaClinica.__table__.columns  # type: ignore[attr-defined]
    }
    if vista == "resumen":
        return {k: v for k, v in datos.items() if k in _CAMPOS_RESUMEN}
    if vista == "familia":
        return {k: v for k, v in datos.items() if k not in _OCULTOS_FAMILIA}
    return datos


# --- 6.14 Historia -----------------------------------------------------------------------


def _mascota(db: Session, mascota_id: UUID) -> Mascota:
    mascota = db.get(Mascota, mascota_id)
    if mascota is None:
        raise NoEncontrado("Mascota no encontrada")
    return mascota


def consulta_mascotas(alcance: Alcance, q: str | None) -> Select[tuple[Mascota, Familia]]:
    """6.14 La historia clinica es del medico, que no tiene Familias (Seccion 12): busca la
    mascota por su nombre, el del titular o su documento, y recibe solo lo que necesita para
    abrir la historia (R4-CIE-02: antes el buscador pedia /familias y le daba 403)."""
    stmt = select(Mascota, Familia).join(Familia, Familia.id == Mascota.familia_id)
    if q and q.strip():
        patron = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Mascota.nombre.ilike(patron),
                Familia.titular_nombre.ilike(patron),
                Familia.documento.ilike(patron),
            )
        )
    return restringir(stmt, Familia, alcance)


def buscar_mascotas(
    db: Session, alcance: Alcance, q: str | None, limit: int, offset: int
) -> tuple[list[tuple[Mascota, Familia]], int]:
    stmt = consulta_mascotas(alcance, q)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    filas = db.execute(
        stmt.order_by(Familia.titular_nombre, Mascota.nombre, Mascota.id)
        .limit(limit)
        .offset(offset)
    ).tuples()
    return list(filas), total


def mascota_con_titular(db: Session, alcance: Alcance, mascota_id: UUID) -> tuple[Mascota, Familia]:
    """De quien es la mascota de una historia, sin abrir su familia."""
    fila = db.execute(
        restringir(
            select(Mascota, Familia)
            .join(Familia, Familia.id == Mascota.familia_id)
            .where(Mascota.id == mascota_id),
            Familia,
            alcance,
        )
    ).first()
    if fila is None:
        raise NoEncontrado("Mascota no encontrada")
    return fila.tuple()


def obtener(db: Session, historia_id: UUID) -> HistoriaClinica:
    entrada = db.get(HistoriaClinica, historia_id)
    if entrada is None:
        raise NoEncontrado("Entrada de historia clinica no encontrada")
    return entrada


def plantilla(db: Session, codigo: str) -> PlantillaConsulta:
    p = db.scalar(
        select(PlantillaConsulta).where(
            PlantillaConsulta.codigo == codigo, PlantillaConsulta.activa.is_(True)
        )
    )
    if p is None:
        raise NoEncontrado(f"Plantilla de consulta '{codigo}' inexistente o inactiva")
    return p


def listar_plantillas(
    db: Session, *, tipo_servicio: str | None = None, incluir_inactivas: bool = False
) -> list[PlantillaConsulta]:
    """Las activas, que son las que ofrece la consulta; con `incluir_inactivas`, tambien las
    retiradas, al final (las mantiene el equipo medico en Clinica)."""
    stmt = select(PlantillaConsulta)
    if not incluir_inactivas:
        stmt = stmt.where(PlantillaConsulta.activa.is_(True))
    if tipo_servicio:
        stmt = stmt.where(PlantillaConsulta.tipo_servicio_codigo == tipo_servicio)
    orden = (PlantillaConsulta.activa.desc(), PlantillaConsulta.nombre)
    return list(db.scalars(stmt.order_by(*orden)))


def _campos_plantilla(campos: dict[str, str]) -> dict[str, str]:
    """Solo los apartados con texto: uno vacio no prellena nada."""
    return {k: v.strip() for k, v in campos.items() if k in CAMPOS_CLINICOS and v.strip()}


def _nombre_libre(db: Session, nombre: str, *, salvo: UUID | None = None) -> str:
    """Dos plantillas con el mismo nombre no se distinguen en la consulta."""
    nombre = nombre.strip()
    stmt = select(PlantillaConsulta.id).where(
        func.lower(PlantillaConsulta.nombre) == nombre.lower()
    )
    if salvo is not None:
        stmt = stmt.where(PlantillaConsulta.id != salvo)
    if db.scalar(stmt) is not None:
        raise Conflicto(f"Ya hay una plantilla que se llama «{nombre}»")
    return nombre


def _codigo_plantilla(db: Session, nombre: str) -> str:
    """El codigo interno, sacado del nombre: sin tildes, en minusculas y unico («Otitis
    externa» → «otitis_externa»). No cambia al editar: es su identificador en la API y en la
    URL del panel."""
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-z0-9]+", "_", sin_tildes.lower()).strip("_")[:36]
    base = base if len(base) >= 3 else f"plantilla_{base}".rstrip("_")
    existentes = set(
        db.scalars(
            select(PlantillaConsulta.codigo).where(PlantillaConsulta.codigo.like(f"{base}%"))
        )
    )
    codigo, n = base, 2
    while codigo in existentes:
        codigo, n = f"{base}_{n}", n + 1
    return codigo


def crear_plantilla(
    db: Session, nombre: str, campos: dict[str, str], tipo_servicio_codigo: str | None = None
) -> PlantillaConsulta:
    nombre = _nombre_libre(db, nombre)
    if tipo_servicio_codigo is not None:
        servicios.tipo_servicio(db, tipo_servicio_codigo)
    p = PlantillaConsulta(
        codigo=_codigo_plantilla(db, nombre),
        nombre=nombre,
        tipo_servicio_codigo=tipo_servicio_codigo,
        campos=_campos_plantilla(campos),
    )
    db.add(p)
    db.flush()
    return p


def editar_plantilla(db: Session, codigo: str, cambios: dict[str, Any]) -> PlantillaConsulta:
    """6.14 El equipo medico corrige el texto de una plantilla o la retira (`activa`); no
    se borra (nada de negocio se borra) y la bitacora guarda cada version. La consulta copia
    los textos al crearse: lo ya registrado no cambia."""
    p = db.scalar(select(PlantillaConsulta).where(PlantillaConsulta.codigo == codigo))
    if p is None:
        raise NoEncontrado(f"Plantilla de consulta '{codigo}' inexistente")
    # Un nulo no borra: solo el tipo de atencion admite quedar vacio (vale para cualquiera).
    if cambios.get("nombre") is not None:
        p.nombre = _nombre_libre(db, cambios["nombre"], salvo=p.id)
    if cambios.get("campos") is not None:
        p.campos = _campos_plantilla(cambios["campos"])
    if "tipo_servicio_codigo" in cambios:
        tipo = cambios["tipo_servicio_codigo"]
        # Solo se valida el que cambia: uno que el catalogo retiro despues se puede conservar.
        if tipo is not None and tipo != p.tipo_servicio_codigo:
            servicios.tipo_servicio(db, tipo)
        p.tipo_servicio_codigo = tipo
    if cambios.get("activa") is not None:
        p.activa = cambios["activa"]
    db.flush()
    return p


def uso_de_plantillas(db: Session) -> dict[str, int]:
    """Cuantas consultas firmadas y vigentes partieron de cada plantilla: ni los borradores ni
    las versiones ya corregidas. Las que no se han usado no aparecen."""
    filas = db.execute(
        select(HistoriaClinica.plantilla_codigo, func.count())
        .where(HistoriaClinica.plantilla_codigo.is_not(None), HistoriaClinica.estado == "firmada")
        .group_by(HistoriaClinica.plantilla_codigo)
    )
    return {str(codigo): int(total) for codigo, total in filas}


def crear_entrada(
    db: Session,
    mascota_id: UUID,
    datos: dict[str, Any],
    profesional_id: UUID,
    *,
    servicio_id: UUID | None = None,
    plantilla_codigo: str | None = None,
    tipo: str = "presencial",
) -> HistoriaClinica:
    """Abre una entrada en borrador. Con plantilla, sus textos son el punto de partida y lo
    que mande el profesional los reemplaza."""
    mascota = _mascota(db, mascota_id)
    base: dict[str, Any] = {}
    if plantilla_codigo:
        base = {
            k: v for k, v in plantilla(db, plantilla_codigo).campos.items() if k in CAMPOS_CLINICOS
        }
    valores = {**base, **{k: v for k, v in datos.items() if v is not None}}
    if not valores.get("motivo"):
        raise ReglaNegocio("La entrada necesita el motivo de consulta")
    if servicio_id is not None:
        _del_servicio(servicios.obtener(db, servicio_id), mascota)
    entrada = HistoriaClinica(
        mascota_id=mascota.id,
        familia_id=mascota.familia_id,
        servicio_id=servicio_id,
        profesional_id=profesional_id,
        plantilla_codigo=plantilla_codigo,
        tipo=tipo,
        fecha=valores.pop("fecha", None) or hoy(),
        **{k: valores.get(k) for k in (*CAMPOS_CLINICOS, "notas_internas")},
    )
    db.add(entrada)
    db.flush()
    return entrada


def _editable(entrada: HistoriaClinica, usuario_id: UUID) -> None:
    if entrada.estado != "borrador":
        raise ReglaNegocio("Una entrada firmada no se edita: se corrige con una nueva version")
    if entrada.profesional_id != usuario_id:
        raise Prohibido("Solo quien abrio la entrada puede editarla antes de firmar")


def editar(
    db: Session, entrada: HistoriaClinica, datos: dict[str, Any], usuario_id: UUID
) -> HistoriaClinica:
    _editable(entrada, usuario_id)
    for campo in (*CAMPOS_CLINICOS, "notas_internas", "fecha"):
        if campo in datos:
            setattr(entrada, campo, datos[campo])
    if not entrada.motivo:
        raise ReglaNegocio("La entrada necesita el motivo de consulta")
    db.flush()
    return entrada


def _del_servicio(servicio: Servicio, mascota: Mascota) -> None:
    """La consulta de una visita es de la mascota que la visita atiende."""
    if servicio.familia_id != mascota.familia_id or servicio.mascota_id not in (None, mascota.id):
        raise ReglaNegocio("El servicio no es de esta mascota")


def _registrar_pasos_del_servicio(db: Session, entrada: HistoriaClinica, usuario_id: UUID) -> None:
    """Registra los pasos del servicio que la consulta ya dice, si el servicio se esta
    atendiendo. Los que ya estan registrados no se tocan: los escribio alguien en el servicio."""
    if entrada.servicio_id is None:
        return
    servicio = servicios.obtener(db, entrada.servicio_id)
    if servicio.estado != EstadoServicio.EN_ATENCION:
        return
    hechos = set(
        db.scalars(select(ServicioPaso.paso_codigo).where(ServicioPaso.servicio_id == servicio.id))
    )
    for paso in servicios.tipo_servicio(db, servicio.tipo_codigo).pasos:
        campos = paso.get("campos", [])
        if paso["codigo"] in hechos or not campos:
            continue
        if not all(c in _PASOS_DESDE_LA_CONSULTA for c in campos):
            continue
        datos = {c: _PASOS_DESDE_LA_CONSULTA[c](entrada) for c in campos}
        if all(datos.values()):
            servicios.completar_paso(db, servicio, paso["codigo"], datos, usuario_id)


def firmar(db: Session, entrada: HistoriaClinica, usuario_id: UUID) -> HistoriaClinica:
    """Cierra la entrada. Si era la correccion de otra, esa queda como `corregida`. Si es la
    consulta de una visita en curso, registra los pasos del servicio que ya dice."""
    _editable(entrada, usuario_id)
    if not entrada.diagnostico:
        raise ReglaNegocio("Para firmar se requiere el diagnostico")
    entrada.estado = "firmada"
    entrada.firmada_en = ahora()
    entrada.firmada_por_id = usuario_id
    if entrada.reemplaza_id:
        anterior = obtener(db, entrada.reemplaza_id)
        anterior.estado = "corregida"
    db.flush()
    _registrar_pasos_del_servicio(db, entrada, usuario_id)
    return entrada


def borradores(db: Session, profesional_id: UUID) -> list[HistoriaClinica]:
    """R2-PAN-07 Las consultas que el profesional abrio y aun no firma: su trabajo pendiente."""
    return list(
        db.scalars(
            select(HistoriaClinica)
            .where(
                HistoriaClinica.profesional_id == profesional_id,
                HistoriaClinica.estado == "borrador",
            )
            .order_by(HistoriaClinica.fecha.desc(), HistoriaClinica.created_at.desc())
        )
    )


def corregir(
    db: Session, entrada: HistoriaClinica, datos: dict[str, Any], usuario_id: UUID
) -> HistoriaClinica:
    """Nueva version en borrador de una entrada firmada vigente. La original no cambia
    hasta que la correccion se firma."""
    if entrada.estado != "firmada":
        raise ReglaNegocio("Solo se corrige una entrada firmada y vigente")
    abierta = db.scalar(
        select(HistoriaClinica.id).where(
            HistoriaClinica.reemplaza_id == entrada.id, HistoriaClinica.estado == "borrador"
        )
    )
    if abierta:
        raise ReglaNegocio("Ya hay una correccion en curso de esta entrada")
    nueva = HistoriaClinica(
        mascota_id=entrada.mascota_id,
        familia_id=entrada.familia_id,
        servicio_id=entrada.servicio_id,
        profesional_id=usuario_id,
        plantilla_codigo=entrada.plantilla_codigo,
        tipo=entrada.tipo,
        fecha=entrada.fecha,
        version=entrada.version + 1,
        reemplaza_id=entrada.id,
        **{k: datos.get(k, getattr(entrada, k)) for k in (*CAMPOS_CLINICOS, "notas_internas")},
    )
    db.add(nueva)
    db.flush()
    return nueva


def historia(
    db: Session, mascota_id: UUID, *, incluir_corregidas: bool = False, solo_firmadas: bool = False
) -> list[HistoriaClinica]:
    _mascota(db, mascota_id)
    stmt = select(HistoriaClinica).where(HistoriaClinica.mascota_id == mascota_id)
    if not incluir_corregidas:
        stmt = stmt.where(HistoriaClinica.estado != "corregida")
    if solo_firmadas:
        stmt = stmt.where(HistoriaClinica.estado == "firmada")
    return list(
        db.scalars(stmt.order_by(HistoriaClinica.fecha.desc(), HistoriaClinica.created_at.desc()))
    )


# --- 6.14 Adjuntos -----------------------------------------------------------------------


def adjuntar(
    db: Session,
    entrada: HistoriaClinica,
    contenido: bytes,
    *,
    nombre: str | None,
    descripcion: str | None,
    usuario_id: UUID,
) -> AdjuntoClinico:
    """Un examen puede llegar despues de firmar: adjuntar no altera lo firmado."""

    if entrada.estado == "corregida":
        raise ReglaNegocio("Adjunte a la version vigente de la entrada")
    archivo = archivos.subir(
        db, contenido, nombre=nombre, proposito="adjunto_clinico", usuario_id=usuario_id
    )
    adjunto = AdjuntoClinico(
        historia_id=entrada.id,
        archivo_id=archivo.id,
        nombre_archivo=archivo.nombre_original,
        content_type=archivo.content_type,
        descripcion=descripcion,
        subido_por_id=usuario_id,
    )
    db.add(adjunto)
    db.flush()
    return adjunto


def adjuntos(db: Session, historia_id: UUID) -> list[AdjuntoClinico]:
    return list(
        db.scalars(
            select(AdjuntoClinico)
            .where(AdjuntoClinico.historia_id == historia_id)
            .order_by(AdjuntoClinico.created_at)
        )
    )


def url_adjunto(db: Session, adjunto_id: UUID, vista: Vista) -> dict[str, str]:
    """6.14 Solo quien ve la historia clinica completa (o la familia, sobre lo suyo,
    resuelto por el alcance antes de llegar aqui) abre un adjunto."""

    if vista == "resumen":
        raise Prohibido("Su perfil no puede abrir adjuntos clinicos")
    adjunto = db.get(AdjuntoClinico, adjunto_id)
    if adjunto is None:
        raise NoEncontrado("Adjunto no encontrado")
    archivo = db.get(Archivo, adjunto.archivo_id)
    assert archivo is not None
    return {"url": archivos.url(archivo), "nombre": adjunto.nombre_archivo}


# --- 6.14 Formula ------------------------------------------------------------------------


def emitir_formula(
    db: Session,
    entrada: HistoriaClinica,
    items: list[dict[str, Any]],
    indicaciones: str | None,
    usuario_id: UUID,
) -> Formula:
    if entrada.estado == "corregida":
        raise ReglaNegocio("Emita la formula desde la version vigente de la entrada")
    if not items:
        raise ReglaNegocio("La formula necesita al menos un medicamento")
    mascota = _mascota(db, entrada.mascota_id)
    familia = db.get(Familia, mascota.familia_id)
    profesional = db.get(Usuario, usuario_id)
    assert familia is not None and profesional is not None
    contenido = documento.generar_formula(
        fecha=hoy(),
        mascota={"nombre": mascota.nombre, "especie": mascota.especie, "peso_kg": mascota.peso_kg},
        titular=familia.titular_nombre,
        profesional=profesional.nombre,
        diagnostico=entrada.diagnostico,
        items=items,
        indicaciones=indicaciones,
    )
    archivo = archivos.guardar_bytes(
        db,
        contenido=contenido,
        nombre=f"formula-{mascota.nombre}-{hoy():%Y%m%d}.pdf",
        proposito="formula",
        usuario_id=usuario_id,
    )
    formula = Formula(
        historia_id=entrada.id,
        items=items,
        indicaciones=indicaciones,
        archivo_id=archivo.id,
        emitida_por_id=usuario_id,
    )
    db.add(formula)
    db.flush()
    return formula


# --- 6.17 Atencion virtual ---------------------------------------------------------------


def render(cuerpo: str, variables: list[str]) -> str:
    return re.sub(
        r"\{\{(\d+)\}\}",
        lambda m: variables[int(m.group(1)) - 1] if int(m.group(1)) <= len(variables) else "",
        cuerpo,
    )


def solicitar_virtual(
    db: Session, mascota_id: UUID, motivo: str, *, canal: str, prioridad: str = "media"
) -> SolicitudVirtual:
    mascota = _mascota(db, mascota_id)
    if not mascota.activa:
        raise ReglaNegocio("La mascota esta dada de baja")

    if contratos.contrato_vigente(db, mascota.familia_id) is None:
        raise ReglaNegocio("La orientacion virtual requiere un plan vigente")
    solicitud = SolicitudVirtual(
        familia_id=mascota.familia_id,
        mascota_id=mascota.id,
        canal=canal,
        motivo=motivo,
        prioridad=prioridad,
    )
    db.add(solicitud)
    db.flush()
    return solicitud


def obtener_solicitud(db: Session, solicitud_id: UUID) -> SolicitudVirtual:
    solicitud = db.get(SolicitudVirtual, solicitud_id)
    if solicitud is None:
        raise NoEncontrado("Solicitud no encontrada")
    return solicitud


def tomar(db: Session, solicitud: SolicitudVirtual, medico_id: UUID) -> SolicitudVirtual:
    if solicitud.estado != "en_cola":
        raise ReglaNegocio("La solicitud ya fue tomada")
    solicitud.estado = "en_atencion"
    solicitud.asignada_a_id = medico_id
    solicitud.tomada_en = ahora()
    db.flush()
    return solicitud


def respuesta_aprobada(db: Session, codigo: str) -> RespuestaVirtual:
    r = db.scalar(
        select(RespuestaVirtual).where(
            RespuestaVirtual.codigo == codigo, RespuestaVirtual.estado == "aprobada"
        )
    )
    if r is None:
        raise ReglaNegocio(f"La respuesta '{codigo}' no existe o no esta aprobada")
    return r


def responder(
    db: Session,
    solicitud: SolicitudVirtual,
    *,
    respuesta_codigo: str,
    variables: list[str],
    medico_id: UUID,
    diagnostico: str | None = None,
    notas_internas: str | None = None,
) -> SolicitudVirtual:
    """Arma la respuesta desde una plantilla aprobada, la registra como entrada firmada de
    la historia y la envia a la familia (texto libre si hay ventana de WhatsApp abierta,
    plantilla si no)."""

    if solicitud.estado != "en_atencion" or solicitud.asignada_a_id != medico_id:
        raise ReglaNegocio("Solo quien tomo la solicitud puede responderla")
    plantilla_resp = respuesta_aprobada(db, respuesta_codigo)
    if len(variables) != len(plantilla_resp.variables):
        raise ReglaNegocio(
            f"La respuesta espera {len(plantilla_resp.variables)} variables "
            f"({', '.join(plantilla_resp.variables)})"
        )
    texto = render(plantilla_resp.cuerpo, variables)
    entrada = crear_entrada(
        db,
        solicitud.mascota_id,
        {
            "motivo": solicitud.motivo,
            "diagnostico": diagnostico or "Orientacion virtual",
            "tratamiento": texto,
            "notas_internas": notas_internas,
        },
        medico_id,
        tipo="virtual",
    )
    firmar(db, entrada, medico_id)
    solicitud.estado = "respondida"
    solicitud.respuesta_codigo = plantilla_resp.codigo
    solicitud.respuesta = texto
    solicitud.respondida_en = ahora()
    solicitud.historia_id = entrada.id

    familia = db.get(Familia, solicitud.familia_id)
    assert familia is not None
    try:
        with db.begin_nested():
            if comunicaciones.ventana_abierta(db, familia.telefono):
                comunicaciones.encolar_texto(
                    db, telefono=familia.telefono, texto=texto, familia_id=familia.id
                )
            else:
                comunicaciones.encolar_plantilla(
                    db,
                    telefono=familia.telefono,
                    plantilla=PLANTILLA_RESPUESTA,
                    variables=[familia.titular_nombre],
                    familia_id=familia.id,
                )
    except ReglaNegocio as e:
        # La respuesta queda en el portal y en la historia aunque el aviso no salga.
        logger.error("Aviso de respuesta virtual sin enviar: %s", e)
    db.flush()
    return solicitud


def cerrar_solicitud(db: Session, solicitud: SolicitudVirtual) -> SolicitudVirtual:
    if solicitud.estado != "respondida":
        raise ReglaNegocio("Solo se cierra una solicitud respondida")
    solicitud.estado = "cerrada"
    db.flush()
    return solicitud


def crear_respuesta(db: Session, datos: dict[str, Any]) -> RespuestaVirtual:
    if db.scalar(select(RespuestaVirtual.id).where(RespuestaVirtual.codigo == datos["codigo"])):
        raise ReglaNegocio(f"Ya existe la respuesta {datos['codigo']}")
    usadas = {int(n) for n in re.findall(r"\{\{(\d+)\}\}", datos["cuerpo"])}
    if usadas != set(range(1, len(datos.get("variables", [])) + 1)):
        raise ReglaNegocio("Las variables {{n}} del cuerpo no coinciden con las declaradas")
    respuesta = RespuestaVirtual(**datos, estado="borrador")
    db.add(respuesta)
    db.flush()
    return respuesta


def aprobar_respuesta(db: Session, codigo: str, usuario_id: UUID) -> RespuestaVirtual:
    r = db.scalar(select(RespuestaVirtual).where(RespuestaVirtual.codigo == codigo))
    if r is None:
        raise NoEncontrado("Respuesta no encontrada")
    r.estado = "aprobada"
    r.aprobada_por_id = usuario_id
    r.aprobada_en = ahora()
    db.flush()
    return r


def cola(db: Session) -> list[SolicitudVirtual]:
    """Primero lo urgente, despues lo mas antiguo."""
    orden = {"alta": 0, "media": 1, "baja": 2}
    pendientes = list(
        db.scalars(
            select(SolicitudVirtual)
            .where(SolicitudVirtual.estado.in_(("en_cola", "en_atencion")))
            .order_by(SolicitudVirtual.created_at)
        )
    )
    return sorted(pendientes, key=lambda s: orden.get(s.prioridad, 1))

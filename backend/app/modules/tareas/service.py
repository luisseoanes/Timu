"""6.4 Bandeja de tareas internas generadas por reglas o creadas a mano."""

from collections.abc import Callable
from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.core.enums import AreaTarea, Rol
from app.core.errores import NoEncontrado, ReglaNegocio
from app.core.tiempo import ahora, hoy
from app.modules.auth.models import Usuario
from app.modules.familias.models import Familia
from app.modules.tareas.models import Tarea

# El enum `prioridad` se declara alta, media, baja: ordenar por la columna es ordenar por
# urgencia, y lo sirve el indice ix_tareas_bandeja (un CASE no lo podria usar).
ORDEN_PRIORIDAD = Tarea.prioridad


def crear(
    db: Session,
    *,
    titulo: str,
    area: str,
    prioridad: str = "media",
    vence_en_dias: int | None = None,
    descripcion: str | None = None,
    familia_id: UUID | None = None,
    servicio_id: UUID | None = None,
    contrato_id: UUID | None = None,
    origen: str | None = None,
    clave: str | None = None,
) -> Tarea | None:
    """Crea la tarea. Con `clave`, si ya existe no crea otra y devuelve None."""
    if clave and db.scalar(select(Tarea.id).where(Tarea.clave == clave)):
        return None
    tarea = Tarea(
        titulo=titulo,
        area=area,
        prioridad=prioridad,
        descripcion=descripcion,
        vence_el=hoy() + timedelta(days=vence_en_dias) if vence_en_dias is not None else None,
        familia_id=familia_id,
        servicio_id=servicio_id,
        contrato_id=contrato_id,
        origen=origen,
        clave=clave,
    )
    db.add(tarea)
    db.flush()
    return tarea


def desde_accion(db: Session, accion: dict[str, Any], regla: str, **vinculos: Any) -> Tarea | None:
    """Crea la tarea descrita por una accion de tipo 'tarea' del motor de reglas."""
    return crear(
        db,
        titulo=accion["titulo"],
        area=accion["area"],
        prioridad=accion.get("prioridad", "media"),
        vence_en_dias=accion.get("vence_en_dias"),
        origen=regla,
        **vinculos,
    )


# Seccion 12 Cada perfil ve y trabaja las tareas de su area (docs/perfiles-y-permisos.md).
AREAS_POR_ROL: dict[str, tuple[str, ...]] = {
    Rol.COMERCIAL: (AreaTarea.COMERCIAL,),
    Rol.ATENCION_CLIENTE: (AreaTarea.CARTERA, AreaTarea.SERVICIO_CLIENTE),
    Rol.OPERACIONES: (AreaTarea.OPERACIONES,),
    Rol.MEDICO: (AreaTarea.MEDICO,),
}


def consulta(
    *,
    areas: tuple[str, ...] | None = None,
    area: str | None = None,
    estado: str | None = None,
    asignada_a_id: UUID | None = None,
    sin_asignar: bool = False,
    vencidas: bool = False,
    familia_id: UUID | None = None,
    excluir_origen: str | None = None,
) -> Select[tuple[Tarea]]:
    stmt = select(Tarea)
    if areas is not None:
        stmt = stmt.where(Tarea.area.in_(areas))
    if area:
        stmt = stmt.where(Tarea.area == area)
    if estado == "pendiente":
        # Lo que falta por hacer: abiertas y en progreso (iniciar una no la saca de la vista).
        stmt = stmt.where(Tarea.estado != "cerrada")
    elif estado:
        stmt = stmt.where(Tarea.estado == estado)
    if asignada_a_id:
        stmt = stmt.where(Tarea.asignada_a_id == asignada_a_id)
    if sin_asignar:
        stmt = stmt.where(Tarea.asignada_a_id.is_(None))
    if vencidas:
        stmt = stmt.where(Tarea.vence_el < hoy(), Tarea.estado != "cerrada")
    if familia_id:
        stmt = stmt.where(Tarea.familia_id == familia_id)
    if excluir_origen:
        stmt = stmt.where(or_(Tarea.origen.is_(None), Tarea.origen != excluir_origen))
    return stmt


def obtener(db: Session, tarea_id: UUID, areas: tuple[str, ...] | None = None) -> Tarea:
    """Con `areas`, una tarea de otra area no existe para quien pregunta."""
    tarea = db.get(Tarea, tarea_id)
    if tarea is None or (areas is not None and tarea.area not in areas):
        raise NoEncontrado("Tarea no encontrada")
    return tarea


# Como se dicen las areas y los perfiles en un mensaje de error.
_NOMBRE_AREA = {
    AreaTarea.COMERCIAL: "Comercial",
    AreaTarea.CARTERA: "Cartera",
    AreaTarea.SERVICIO_CLIENTE: "Servicio al cliente",
    AreaTarea.OPERACIONES: "Operaciones",
    AreaTarea.MEDICO: "Médica",
}
_NOMBRE_ROL = {
    Rol.ADMIN: "Administración",
    Rol.GERENCIA: "Gerencia",
    Rol.COMERCIAL: "Comercial",
    Rol.ATENCION_CLIENTE: "Atención al cliente",
    Rol.OPERACIONES: "Operaciones",
    Rol.MEDICO: "Médico veterinario",
}


def asignar(db: Session, tarea: Tarea, usuario_id: UUID | None) -> Tarea:
    if tarea.estado == "cerrada":
        raise ReglaNegocio("La tarea ya esta cerrada")
    if usuario_id is not None:
        # Seccion 12: cada perfil ve las tareas de su area. Asignarla a quien no la ve la
        # perderia: no la encontraria ni en «Mis tareas».
        usuario = db.get(Usuario, usuario_id)
        if usuario is None or not usuario.activo:
            raise NoEncontrado("Usuario no encontrado")
        if tarea.area not in AREAS_POR_ROL.get(usuario.rol, ()):
            perfil = _NOMBRE_ROL.get(usuario.rol, usuario.rol)
            area = _NOMBRE_AREA.get(AreaTarea(tarea.area), tarea.area)
            raise ReglaNegocio(f"{usuario.nombre} ({perfil}) no ve las tareas de {area}")
    tarea.asignada_a_id = usuario_id
    db.flush()
    return tarea


def iniciar(db: Session, tarea: Tarea) -> Tarea:
    if tarea.estado != "abierta":
        raise ReglaNegocio("Solo una tarea abierta puede pasar a en progreso")
    tarea.estado = "en_progreso"
    db.flush()
    return tarea


def cerrar(db: Session, tarea: Tarea, resolucion: str) -> Tarea:
    if tarea.estado == "cerrada":
        raise ReglaNegocio("La tarea ya esta cerrada")
    tarea.estado = "cerrada"
    tarea.cerrada_en = ahora()
    tarea.resolucion = resolucion
    db.flush()
    return tarea


# --- A quien afecta: el titular de la familia y, si es de un servicio, su tipo y su mascota --
# servicios importa tareas (crea tareas al cambiar de estado), asi que tareas no puede importar
# servicios: servicios le conecta como describir sus servicios (`conectar_servicios`, al
# importar servicios/service.py, que la API y el worker cargan siempre).
DescribirServicios = Callable[[Session, set[UUID]], dict[UUID, dict[str, Any]]]

_describir_servicios: DescribirServicios | None = None


def conectar_servicios(describir: DescribirServicios) -> None:
    global _describir_servicios
    _describir_servicios = describir


def a_quien_afecta(
    db: Session, familia_ids: set[UUID], servicio_ids: set[UUID]
) -> tuple[dict[UUID, dict[str, Any]], dict[UUID, dict[str, Any]]]:
    """Lo que nombra cada fila de la bandeja, en lote: dos consultas por pagina, no por fila."""
    familias = (
        {
            f.id: {"id": f.id, "titular_nombre": f.titular_nombre}
            for f in db.execute(
                select(Familia.id, Familia.titular_nombre).where(Familia.id.in_(familia_ids))
            )
        }
        if familia_ids
        else {}
    )
    if not servicio_ids:
        return familias, {}
    if _describir_servicios is None:
        # Sin conectar, la bandeja callaria de que servicio es cada tarea sin avisar.
        raise RuntimeError("tareas sin conectar: falta conectar_servicios()")
    return familias, _describir_servicios(db, servicio_ids)

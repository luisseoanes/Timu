"""F1-SER-06 Bandeja de tareas internas generadas por reglas o creadas a mano."""

from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import Select, case, select
from sqlalchemy.orm import Session

from app.core.errores import NoEncontrado, ReglaNegocio
from app.core.tiempo import ahora, hoy
from app.modules.tareas.models import Tarea

ORDEN_PRIORIDAD = case({"alta": 0, "media": 1, "baja": 2}, value=Tarea.prioridad, else_=3)


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


def consulta(
    *,
    area: str | None = None,
    estado: str | None = None,
    asignada_a_id: UUID | None = None,
    sin_asignar: bool = False,
    vencidas: bool = False,
    familia_id: UUID | None = None,
) -> Select[tuple[Tarea]]:
    stmt = select(Tarea)
    if area:
        stmt = stmt.where(Tarea.area == area)
    if estado:
        stmt = stmt.where(Tarea.estado == estado)
    if asignada_a_id:
        stmt = stmt.where(Tarea.asignada_a_id == asignada_a_id)
    if sin_asignar:
        stmt = stmt.where(Tarea.asignada_a_id.is_(None))
    if vencidas:
        stmt = stmt.where(Tarea.vence_el < hoy(), Tarea.estado != "cerrada")
    if familia_id:
        stmt = stmt.where(Tarea.familia_id == familia_id)
    return stmt


def obtener(db: Session, tarea_id: UUID) -> Tarea:
    tarea = db.get(Tarea, tarea_id)
    if tarea is None:
        raise NoEncontrado("Tarea no encontrada")
    return tarea


def asignar(db: Session, tarea: Tarea, usuario_id: UUID | None) -> Tarea:
    if tarea.estado == "cerrada":
        raise ReglaNegocio("La tarea ya esta cerrada")
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

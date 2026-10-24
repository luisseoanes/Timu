"""F0-09 Carga repetible de catalogos: inserta lo nuevo y actualiza lo existente por codigo."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errores import ReglaNegocio
from app.modules.catalogos import datos
from app.modules.catalogos.models import (
    Ciudad,
    Especie,
    EsquemaPreventivo,
    TipoServicioCatalogo,
)

# Orden de carga: los esquemas referencian especies.
CATALOGOS: list[tuple[type[Any], list[dict[str, Any]]]] = [
    (Ciudad, datos.CIUDADES),
    (Especie, datos.ESPECIES),
    (TipoServicioCatalogo, datos.TIPOS_SERVICIO),
    (EsquemaPreventivo, datos.ESQUEMAS_PREVENTIVOS),
]


def _upsert(db: Session, modelo: type[Any], filas: list[dict[str, Any]]) -> dict[str, int]:
    existentes = {o.codigo: o for o in db.scalars(select(modelo))}
    creados = actualizados = 0
    for fila in filas:
        obj = existentes.get(fila["codigo"])
        if obj is None:
            db.add(modelo(**fila))
            creados += 1
            continue
        cambio = False
        for campo, valor in fila.items():
            if getattr(obj, campo) != valor:
                setattr(obj, campo, valor)
                cambio = True
        actualizados += cambio
    db.flush()
    return {"creados": creados, "actualizados": actualizados}


def cargar(db: Session) -> dict[str, dict[str, int]]:
    return {m.__tablename__: _upsert(db, m, filas) for m, filas in CATALOGOS}


def ciudad_valida(db: Session, nombre: str) -> str:
    """F1-FAM-04 Devuelve el nombre canonico de la ciudad activa (sin distinguir mayusculas)."""
    ciudad = db.scalar(
        select(Ciudad.nombre).where(
            func.lower(Ciudad.nombre) == nombre.strip().lower(), Ciudad.activa.is_(True)
        )
    )
    if ciudad is None:
        raise ReglaNegocio(f"La ciudad '{nombre}' no esta en el catalogo de ciudades activas")
    return ciudad


def especie_valida(db: Session, codigo: str) -> str:
    codigo = codigo.strip().lower()
    if not db.scalar(select(Especie.id).where(Especie.codigo == codigo, Especie.activa.is_(True))):
        raise ReglaNegocio(f"La especie '{codigo}' no esta en el catalogo")
    return codigo

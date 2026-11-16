"""F0-09 Carga repetible de catalogos: inserta lo nuevo y actualiza lo existente por codigo."""

import unicodedata
from typing import Any

from sqlalchemy import select
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


def _sin_tildes(texto: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFD", texto.strip().lower())
        if not unicodedata.combining(c)
    )


def ciudad_valida(db: Session, nombre: str) -> str:
    """F1-FAM-04 Devuelve el nombre canonico de la ciudad activa, sin distinguir mayusculas ni
    tildes: quien escribe «bogota» (en un formulario o por WhatsApp) llega a «Bogotá». Las
    ciudades activas son unas decenas: se comparan en Python."""
    buscada = _sin_tildes(nombre)
    ciudad = next(
        (
            n
            for n in db.scalars(select(Ciudad.nombre).where(Ciudad.activa.is_(True)))
            if _sin_tildes(n) == buscada
        ),
        None,
    )
    if ciudad is None:
        raise ReglaNegocio(f"La ciudad '{nombre}' no esta en el catalogo de ciudades activas")
    return ciudad


def especie_valida(db: Session, codigo: str) -> str:
    codigo = codigo.strip().lower()
    if not db.scalar(select(Especie.id).where(Especie.codigo == codigo, Especie.activa.is_(True))):
        raise ReglaNegocio(f"La especie '{codigo}' no esta en el catalogo")
    return codigo


# --- Que pasos registra la consulta clinica ---------------------------------------------------
# clinica importa catalogos, asi que catalogos no puede importar clinica: clinica le conecta, al
# importar clinica/service.py (que la API carga siempre), los campos de un paso que la consulta
# firmada sabe llenar. Asi el catalogo dice a quien lo lee (el panel, para decidir adonde lleva
# «Registrar la atencion») que pasos registra la consulta, sin que nadie copie la tabla.
_campos_de_la_consulta: frozenset[str] | None = None


def conectar_campos_de_la_consulta(campos: frozenset[str]) -> None:
    global _campos_de_la_consulta
    _campos_de_la_consulta = campos


def lo_registra_la_consulta(campos: list[str]) -> bool:
    """Un paso lo registra la consulta si tiene campos y la consulta los llena todos."""
    if _campos_de_la_consulta is None:
        # Sin conectar, el panel mandaria a registrar en el servicio lo que llena la consulta.
        raise RuntimeError("catalogos sin conectar: falta conectar_campos_de_la_consulta()")
    return bool(campos) and set(campos) <= _campos_de_la_consulta

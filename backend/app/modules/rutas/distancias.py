"""F2-RUT-02 Matriz de tiempos de viaje con cache y tope de consultas.

1. Lo que ya esta en cache no se vuelve a pedir (Distance Matrix se factura por par).
2. Lo que falta se pide a Google mientras quede cupo en el tope diario.
3. Lo que no se pudo pedir (sin API key, tope agotado, proveedor caido) se estima por
   distancia geodesica: la ruta se planea igual, un poco menos precisa.
"""

from collections.abc import Sequence

import structlog
from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.tiempo import hoy
from app.integrations import mapas
from app.integrations.routing import Coordenada, estimar
from app.modules.rutas.models import ConsumoMapas, DistanciaCache

logger = structlog.get_logger(__name__)

Matriz = list[list[int]]


def clave(p: Coordenada) -> str:
    # 4 decimales ~ 11 m: dos visitas al mismo edificio comparten la entrada de cache.
    return f"{p[0]:.4f},{p[1]:.4f}"


def _cupo(db: Session) -> ConsumoMapas:
    consumo = db.scalar(select(ConsumoMapas).where(ConsumoMapas.fecha == hoy()).with_for_update())
    if consumo is None:
        consumo = ConsumoMapas(fecha=hoy(), elementos=0)
        db.add(consumo)
        db.flush()
    return consumo


def _consultar_faltantes(
    db: Session, puntos: Sequence[Coordenada], faltan: dict[int, list[int]]
) -> dict[tuple[str, str], tuple[int, int]]:
    """Pide a Google lo que falta, por origen y en bloques, sin pasar del tope diario."""
    nuevos: dict[tuple[str, str], tuple[int, int]] = {}
    consumo = _cupo(db)
    for i, destinos in faltan.items():
        for k in range(0, len(destinos), mapas.MAX_ORIGENES):
            bloque = destinos[k : k + mapas.MAX_ORIGENES]
            if consumo.elementos + len(bloque) > settings.MAPS_TOPE_DIARIO:
                logger.warning("Tope diario de Distance Matrix alcanzado; se estima el resto")
                return nuevos
            try:
                (fila,) = mapas.consultar([puntos[i]], [puntos[j] for j in bloque])
            except mapas.ErrorMapas:
                logger.warning("Distance Matrix fallo; se estima el resto", exc_info=True)
                return nuevos
            consumo.elementos += len(bloque)
            for j, celda in zip(bloque, fila, strict=True):
                if celda is not None:
                    par = (clave(puntos[i]), clave(puntos[j]))
                    nuevos[par] = celda
                    db.add(
                        DistanciaCache(
                            origen=par[0], destino=par[1], metros=celda[0], segundos=celda[1]
                        )
                    )
    db.flush()
    return nuevos


def matriz(db: Session, puntos: Sequence[Coordenada]) -> tuple[Matriz, Matriz]:
    """(metros, segundos) entre todos los puntos."""
    claves = [clave(p) for p in puntos]
    pares = {(claves[i], claves[j]) for i in range(len(puntos)) for j in range(len(puntos))}
    pares = {(a, b) for a, b in pares if a != b}
    conocidos: dict[tuple[str, str], tuple[int, int]] = {}
    if pares:
        filas = db.execute(
            select(
                DistanciaCache.origen,
                DistanciaCache.destino,
                DistanciaCache.metros,
                DistanciaCache.segundos,
            ).where(tuple_(DistanciaCache.origen, DistanciaCache.destino).in_(list(pares)))
        )
        conocidos = {(o, d): (m, s) for o, d, m, s in filas}

    faltan: dict[int, list[int]] = {}
    vistos: set[tuple[str, str]] = set()
    for i in range(len(puntos)):
        for j in range(len(puntos)):
            par = (claves[i], claves[j])
            if par[0] != par[1] and par not in conocidos and par not in vistos:
                faltan.setdefault(i, []).append(j)
                vistos.add(par)
    if faltan and mapas.configurado():
        conocidos.update(_consultar_faltantes(db, puntos, faltan))

    metros: Matriz = [[0] * len(puntos) for _ in puntos]
    segundos: Matriz = [[0] * len(puntos) for _ in puntos]
    for i, a in enumerate(puntos):
        for j, b in enumerate(puntos):
            if claves[i] == claves[j]:
                continue
            m, s = conocidos.get((claves[i], claves[j])) or estimar(
                a, b, settings.RUTA_VELOCIDAD_KMH
            )
            metros[i][j], segundos[i][j] = m, s
    return metros, segundos

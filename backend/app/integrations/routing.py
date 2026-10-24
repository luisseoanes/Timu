"""6.7 Optimizacion de rutas con Google OR-Tools (VRP con ventanas horarias).

Es CPU-bound: se invoca SIEMPRE desde una tarea de Celery, nunca desde un endpoint
async (bloquearia el event loop). Por eso OR-Tools vive en requirements-worker.txt.

Todo el tiempo se expresa en segundos desde la medianoche del dia de la ruta. El nodo
0 es la base de salida; los demas, una visita cada uno.
"""

from dataclasses import dataclass, field
from math import asin, cos, radians, sin, sqrt

Coordenada = tuple[float, float]  # (latitud, longitud)

RADIO_TIERRA_M = 6_371_000
# Las calles no son lineas rectas: factor tipico de desvio urbano sobre la geodesica.
FACTOR_DESVIO = 1.35


def haversine_m(a: Coordenada, b: Coordenada) -> int:
    lat1, lon1, lat2, lon2 = map(radians, (*a, *b))
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return int(2 * RADIO_TIERRA_M * asin(sqrt(h)))


def estimar(a: Coordenada, b: Coordenada, velocidad_kmh: float) -> tuple[int, int]:
    """(metros, segundos) aproximados cuando no hay proveedor de mapas o se agoto el tope."""
    metros = int(haversine_m(a, b) * FACTOR_DESVIO)
    return metros, int(metros / (velocidad_kmh * 1000 / 3600))


@dataclass(frozen=True)
class Visita:
    """Ventana en la que puede EMPEZAR la atencion y cuanto dura."""

    inicio_min: int
    inicio_max: int
    duracion: int


@dataclass
class Plan:
    # Por vehiculo: [(nodo, segundo de llegada)], sin incluir la base.
    rutas: list[list[tuple[int, int]]] = field(default_factory=list)
    descartados: list[int] = field(default_factory=list)


def optimizar(
    tiempos: list[list[int]],
    visitas: list[Visita],
    *,
    vehiculos: int,
    capacidad: int,
    jornada: tuple[int, int],
    segundos_busqueda: int = 1,
) -> Plan:
    """Reparte las visitas entre los vehiculos y las ordena respetando ventanas, duracion
    de cada atencion, jornada y maximo de atenciones por tecnico.

    `tiempos[i][j]` es el viaje de i a j (0 = base). `visitas[k]` corresponde al nodo k+1.
    Lo que no cabe se devuelve en `descartados` (nodos) en lugar de romper la jornada.
    """
    n = len(visitas) + 1
    if n == 1 or vehiculos == 0:
        return Plan(rutas=[[] for _ in range(vehiculos)], descartados=list(range(1, n)))

    from ortools.constraint_solver import pywrapcp, routing_enums_pb2

    manager = pywrapcp.RoutingIndexManager(n, vehiculos, 0)
    routing = pywrapcp.RoutingModel(manager)
    duracion = [0] + [v.duracion for v in visitas]

    def transito(desde: int, hasta: int) -> int:
        i, j = manager.IndexToNode(desde), manager.IndexToNode(hasta)
        return tiempos[i][j] + duracion[i]

    indice_tiempo = routing.RegisterTransitCallback(transito)
    routing.SetArcCostEvaluatorOfAllVehicles(indice_tiempo)
    # Holgura: el tecnico puede esperar a que abra la ventana de la siguiente familia.
    routing.AddDimension(indice_tiempo, 4 * 3600, 24 * 3600, False, "Tiempo")
    dim_tiempo = routing.GetDimensionOrDie("Tiempo")
    for nodo, visita in enumerate(visitas, start=1):
        dim_tiempo.CumulVar(manager.NodeToIndex(nodo)).SetRange(
            visita.inicio_min, visita.inicio_max
        )
    for v in range(vehiculos):
        dim_tiempo.CumulVar(routing.Start(v)).SetRange(*jornada)
        dim_tiempo.CumulVar(routing.End(v)).SetRange(*jornada)
        routing.AddVariableMinimizedByFinalizer(dim_tiempo.CumulVar(routing.Start(v)))
        routing.AddVariableMinimizedByFinalizer(dim_tiempo.CumulVar(routing.End(v)))

    def demanda(indice: int) -> int:
        return 0 if manager.IndexToNode(indice) == 0 else 1

    indice_demanda = routing.RegisterUnaryTransitCallback(demanda)
    routing.AddDimensionWithVehicleCapacity(
        indice_demanda, 0, [capacidad] * vehiculos, True, "Capacidad"
    )
    # Una visita que no cabe se descarta con penalidad alta: el solver solo lo hace si no
    # hay forma de atenderla dentro de las restricciones.
    for nodo in range(1, n):
        routing.AddDisjunction([manager.NodeToIndex(nodo)], 10_000_000)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    params.time_limit.seconds = segundos_busqueda

    solucion = routing.SolveWithParameters(params)
    if solucion is None:
        return Plan(rutas=[[] for _ in range(vehiculos)], descartados=list(range(1, n)))

    plan = Plan()
    visitados: set[int] = set()
    for v in range(vehiculos):
        ruta: list[tuple[int, int]] = []
        indice = solucion.Value(routing.NextVar(routing.Start(v)))
        while not routing.IsEnd(indice):
            nodo = manager.IndexToNode(indice)
            ruta.append((nodo, solucion.Min(dim_tiempo.CumulVar(indice))))
            visitados.add(nodo)
            indice = solucion.Value(routing.NextVar(indice))
        plan.rutas.append(ruta)
    plan.descartados = [nodo for nodo in range(1, n) if nodo not in visitados]
    return plan


def insertar_mas_barato(
    tiempos: list[list[int]], secuencia: list[int], nuevo: int, desde: int = 0
) -> int:
    """Posicion de `secuencia` donde insertar `nuevo` con el menor tiempo extra, sin tocar
    lo ya recorrido (posiciones antes de `desde`). La secuencia arranca en la base (0)."""
    mejor, mejor_pos = None, len(secuencia)
    camino = [0, *secuencia]
    for pos in range(desde, len(secuencia) + 1):
        a = camino[pos]
        b = camino[pos + 1] if pos + 1 < len(camino) else None
        extra = tiempos[a][nuevo] + (tiempos[nuevo][b] - tiempos[a][b] if b is not None else 0)
        if mejor is None or extra < mejor:
            mejor, mejor_pos = extra, pos
    return mejor_pos

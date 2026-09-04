"""6.7 Optimizacion de rutas con Google OR-Tools.

Se resuelve un TSP sobre la matriz de distancias; la matriz real se obtiene de
Google Maps Distance Matrix, con fallback a distancia euclidiana para desarrollo.
"""

from math import dist

Coordenada = tuple[float, float]


def matriz_distancias(puntos: list[Coordenada]) -> list[list[int]]:
    """Matriz aproximada en metros. Sustituible por Distance Matrix API."""
    return [[int(dist(a, b) * 111_000) for b in puntos] for a in puntos]


def optimizar_secuencia(puntos: list[Coordenada]) -> list[int]:
    """Devuelve los indices de los puntos en orden optimo, empezando en el indice 0."""
    if len(puntos) < 3:
        return list(range(len(puntos)))

    from ortools.constraint_solver import pywrapcp, routing_enums_pb2

    matriz = matriz_distancias(puntos)
    manager = pywrapcp.RoutingIndexManager(len(puntos), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def callback(from_index: int, to_index: int) -> int:
        return matriz[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit = routing.RegisterTransitCallback(callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(params)
    if solution is None:
        return list(range(len(puntos)))

    orden: list[int] = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        orden.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    return orden

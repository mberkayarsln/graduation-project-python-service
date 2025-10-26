from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import math


def haversine(lat1, lon1, lat2, lon2):
    r = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_distance_matrix(points):
    n = len(points)
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = int(haversine(
                    points[i][0], points[i][1],
                    points[j][0], points[j][1]
                ))
    return matrix


def optimize_tsp(points, office=None):
    all_points = points + [office] if office else points

    n = len(all_points)
    
    dist_matrix = compute_distance_matrix(all_points)

    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return dist_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_params.log_search = False

    solution = routing.SolveWithParameters(search_params)
    if not solution:
        return points

    index = routing.Start(0)
    ordered_points = []
    while not routing.IsEnd(index):
        ordered_points.append(all_points[manager.IndexToNode(index)])
        index = solution.Value(routing.NextVar(index))

    if office and office not in ordered_points:
        ordered_points.append(office)

    return ordered_points
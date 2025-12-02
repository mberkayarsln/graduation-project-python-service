import math
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def haversine(lat1, lon1, lat2, lon2):
    r = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_distance_matrix(points, use_traffic=False, api_key=None, departure_time=None, k_nearest=5):
    n = len(points)
    matrix = [[0] * n for _ in range(n)]
    
    haversine_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            dist = haversine(*points[i], *points[j])
            haversine_matrix[i][j] = dist
            haversine_matrix[j][i] = dist
    
    if use_traffic and api_key:
        from traffic_router import get_route_with_traffic
        
        print(f"    optimized traffic-aware matrix (k={k_nearest} nearest neighbors per node)...")
        
        api_calls = 0
        total_possible = n * (n - 1) // 2
        
        for i in range(n):
            distances = [(j, haversine_matrix[i][j]) for j in range(n) if j > i]
            distances.sort(key=lambda x: x[1])
            
            nearest_count = min(k_nearest, len(distances))
            nearest_neighbors = [j for j, _ in distances[:nearest_count]]
            
            for j in range(i + 1, n):
                if j in nearest_neighbors:
                    try:
                        result = get_route_with_traffic(
                            [points[i], points[j]], 
                            api_key, 
                            departure_time
                        )
                        duration = int(result['duration_with_traffic_min'] * 60)
                        matrix[i][j] = duration
                        matrix[j][i] = duration
                        api_calls += 1
                    except Exception as e:
                        dist = int(haversine_matrix[i][j])
                        matrix[i][j] = dist
                        matrix[j][i] = dist
                else:
                    dist = int(haversine_matrix[i][j])
                    matrix[i][j] = dist
                    matrix[j][i] = dist
        
        print(f"    API calls: {api_calls}/{total_possible} (%{(api_calls/total_possible)*100:.1f} of possible)")
    else:
        for i in range(n):
            for j in range(n):
                matrix[i][j] = int(haversine_matrix[i][j])
    
    return matrix


def optimize_tsp(points, office=None, use_traffic=False, api_key=None, departure_time=None, k_nearest=5):
    all_points = points + [office] if office else points
    n = len(all_points)
    
    dist_matrix = compute_distance_matrix(
        all_points, 
        use_traffic=use_traffic, 
        api_key=api_key, 
        departure_time=departure_time,
        k_nearest=k_nearest
    )
    
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
    
    solution = routing.SolveWithParameters(search_params)
    
    if solution:
        index = routing.Start(0)
        route = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route.append(all_points[node])
            index = solution.Value(routing.NextVar(index))
        
        if office and route[-1] != office:
            route.append(office)
        
        return route
    
    return all_points
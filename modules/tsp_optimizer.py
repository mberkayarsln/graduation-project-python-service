import math
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


class TSPOptimizer:
    def __init__(self, office_location=None):
        self.office_location = office_location
        self.distance_matrix = None
        self.solution_route = None
    
    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        r = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        
        a = (math.sin(dphi / 2) ** 2 + 
             math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
        
        return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    def compute_distance_matrix(self, points, use_traffic=False, 
                                api_key=None, departure_time=None, k_nearest=5):
        n = len(points)
        matrix = [[0] * n for _ in range(n)]
        haversine_matrix = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                dist = self.haversine(*points[i], *points[j])
                haversine_matrix[i][j] = dist
                haversine_matrix[j][i] = dist
        if use_traffic and api_key:
            from modules.traffic_router import TrafficRouter
            router = TrafficRouter(api_key=api_key, cache_enabled=True)

            print(f"    building traffic-aware matrix (API calls for all pairs)...")

            api_calls = 0
            total_possible = n * (n - 1) // 2

            for i in range(n):
                for j in range(i + 1, n):
                    try:
                        result = router.get_route_with_traffic([points[i], points[j]], departure_time)
                        duration_seconds = int(result['duration_with_traffic_min'] * 60)
                        matrix[i][j] = duration_seconds
                        matrix[j][i] = duration_seconds
                        api_calls += 1
                    except Exception as e:
                        print(f"    Warning: traffic API call failed for pair ({i},{j}): {e}")
                        CITY_SPEED_KMH = 30
                        distance_km = haversine_matrix[i][j] / 1000
                        duration_seconds = int((distance_km / CITY_SPEED_KMH) * 3600)
                        matrix[i][j] = duration_seconds
                        matrix[j][i] = duration_seconds

            if total_possible > 0:
                print(f"    API calls: {api_calls}/{total_possible} (%{(api_calls/total_possible)*100:.1f} of possible)")
            else:
                print(f"    API calls: {api_calls} (single point, no pairs)")
        else:
            from modules.osrm_router import OSRMRouter
            osrm = OSRMRouter()
            
            print(f"    building distance matrix with OSRM (road distances for all pairs)...")
            
            api_calls = 0
            total_possible = n * (n - 1) // 2
            
            for i in range(n):
                for j in range(i + 1, n):
                    try:
                        result = osrm.get_route([points[i], points[j]])
                        distance_meters = int(result['distance_km'] * 1000)
                        matrix[i][j] = distance_meters
                        matrix[j][i] = distance_meters
                        api_calls += 1
                    except Exception as e:
                        print(f"    Warning: OSRM failed ({i},{j}): {e}")
                        matrix[i][j] = int(haversine_matrix[i][j])
                        matrix[j][i] = int(haversine_matrix[i][j])
            
            if total_possible > 0:
                print(f"    OSRM calls: {api_calls}/{total_possible} (%{(api_calls/total_possible)*100:.1f} of possible)")
            else:
                print(f"    OSRM calls: {api_calls} (single point, no pairs)")
        
        self.distance_matrix = matrix
        return matrix
    
    def optimize(self, points, use_traffic=False, api_key=None, 
                departure_time=None, k_nearest=5):
        if not points:
            return [self.office_location] if self.office_location else []
        
        n = len(points)
        if n == 1:
            route = [points[0]]
            if self.office_location:
                route.append(self.office_location)
            return route
        dist_matrix = self.compute_distance_matrix(
            points, use_traffic, api_key, departure_time, k_nearest
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
                route.append(points[node])
                index = solution.Value(routing.NextVar(index))
            if self.office_location:
                route.append(self.office_location)
            
            self.solution_route = route
            return route
        result = points.copy()
        if self.office_location:
            result.append(self.office_location)
        return result

"""Routing Service"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from modules.tsp_optimizer import TSPOptimizer
from modules.osrm_router import OSRMRouter
from models.route import Route


class RoutingService:
    """Rota optimizasyon"""
    
    def __init__(self, config):
        self.config = config
        self.strategy = 'tsp'
        self.office_location = config.OFFICE_LOCATION
        self.optimizer = TSPOptimizer(office_location=self.office_location)
        self.osrm_router = OSRMRouter()
    
    def optimize_cluster_route(self, cluster, use_traffic=False, 
                              api_key=None, departure_time=None, use_stops=True):
        """Cluster rotası optimize et"""
        if use_stops and cluster.has_stops():
            points_to_optimize = cluster.stops
            print(f"   Optimizing {len(points_to_optimize)} stops for cluster {cluster.id}")
        else:
            points_to_optimize = cluster.get_employee_locations(include_excluded=False)
            print(f"   Optimizing {len(points_to_optimize)} employee locations for cluster {cluster.id}")
        
        if len(points_to_optimize) == 0:
            return None
        optimized_stops = self.optimizer.optimize(
            points=points_to_optimize,
            use_traffic=use_traffic,
            api_key=api_key,
            departure_time=departure_time,
            k_nearest=5
        )
        route = Route(cluster=cluster)
        route.set_stops(optimized_stops)
        route.mark_optimized()
        if not use_traffic:
            try:
                osrm_data = self.osrm_router.get_route(optimized_stops)
                route.coordinates = osrm_data['coordinates']
                route.distance_km = osrm_data['distance_km']
                route.duration_min = osrm_data['duration_min']
                print(f"✓ OSRM route: {route.distance_km:.1f}km, {route.duration_min:.1f}min")
            except Exception as e:
                print(f"✗ OSRM failed: {e}")
                route.calculate_stats_from_stops()
        else:
            route.calculate_stats_from_stops()
        cluster.assign_route(route)
        
        return route
    
    def optimize_all_clusters(self, clusters, use_traffic=False):
        """Tüm cluster rotaları optimize et"""
        routes = []
        api_key = self.config.TOMTOM_API_KEY if use_traffic else None
        departure_time = self.config.get_departure_time() if use_traffic else None
        
        for cluster in clusters:
            route = self.optimize_cluster_route(
                cluster=cluster,
                use_traffic=use_traffic,
                api_key=api_key,
                departure_time=departure_time
            )
            if route:
                routes.append(route)
        
        return routes

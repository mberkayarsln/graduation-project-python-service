"""Routing Service - handles route optimization for clusters."""
from routing_engines.osrm import OSRMRouter
from core.route import Route


class RoutingService:
    """Service for optimizing vehicle routes."""
    
    def __init__(self, config):
        self.config = config
        self.office_location = config.OFFICE_LOCATION
        self.osrm_router = OSRMRouter()
    
    def optimize_cluster_route(self, cluster, use_traffic=False, 
                              api_key=None, departure_time=None, use_stops=True):
        """
        Optimize route for a single cluster.
        
        Args:
            cluster: Cluster object to route
            use_traffic: Whether to use traffic-aware routing
            api_key: TomTom API key (if use_traffic=True)
            departure_time: Departure time for traffic estimation
            use_stops: Whether to use predetermined stops
        
        Returns:
            Route object or None if no route possible
        """
        if use_stops and cluster.has_stops():
            route_stops = cluster.stops
            print(f"   Using {len(route_stops)} predetermined stops for cluster {cluster.id}")
        else:
            route_stops = cluster.get_employee_locations(include_excluded=False)
            print(f"   Using {len(route_stops)} employee locations for cluster {cluster.id}")
        
        if len(route_stops) == 0:
            return None
        
        route = Route(cluster=cluster)
        route.set_stops(route_stops)
        
        if not use_traffic:
            try:
                osrm_data = self.osrm_router.get_route(route_stops)
                route.coordinates = osrm_data['coordinates']
                route.distance_km = osrm_data['distance_km']
                route.duration_min = osrm_data['duration_min']
                print(f"   OK: OSRM route: {route.distance_km:.1f}km, {route.duration_min:.1f}min")
            except Exception as e:
                print(f"   ERROR: OSRM failed: {e}")
                route.calculate_stats_from_stops()
        else:
            route.calculate_stats_from_stops()
        
        cluster.assign_route(route)
        
        return route
    
    def optimize_all_clusters(self, clusters, use_traffic=False):
        """Optimize routes for all clusters."""
        routes = []
        api_key = self.config.TOMTOM_API_KEY if use_traffic else None
        
        from services.traffic import TrafficService
        departure_time = TrafficService.get_departure_time() if use_traffic else None
        
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

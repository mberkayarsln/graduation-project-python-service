"""Routing Service - handles route optimization for clusters."""
from routing_engines.osrm import OSRMRouter
from routing_engines.google import GoogleRouter
from core.route import Route


class RoutingService:
    """Service for optimizing vehicle routes with multiple engine support."""
    
    def __init__(self, config):
        self.config = config
        self.office_location = config.OFFICE_LOCATION
        self.routing_engine = getattr(config, 'ROUTING_ENGINE', 'osrm')
        
        # Initialize routers
        self.osrm_router = OSRMRouter()
        self.google_router = None
        
        # Initialize Google router if configured
        if self.routing_engine == 'google' and config.GOOGLE_MAPS_API_KEY:
            self.google_router = GoogleRouter(api_key=config.GOOGLE_MAPS_API_KEY)
    
    def _get_router(self):
        """Get the configured routing engine."""
        if self.routing_engine == 'google' and self.google_router:
            return self.google_router, 'Google'
        else:
            return self.osrm_router, 'OSRM'
    
    def optimize_cluster_route(self, cluster, use_traffic=False, 
                              api_key=None, departure_time=None, use_stops=True):
        """
        Optimize route for a single cluster.
        
        Args:
            cluster: Cluster object to route
            use_traffic: Whether to use traffic-aware routing
            api_key: API key for traffic routing
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
        
        router, engine_name = self._get_router()
        
        try:
            if self.routing_engine == 'google':
                # Use Google Directions API
                route_data = router.get_route(
                    route_stops, 
                    departure_time=int(departure_time.timestamp()) if departure_time else None
                )
                route.coordinates = route_data['coordinates']
                route.distance_km = route_data['distance_km']
                route.duration_min = route_data['duration_min']
                
                # Add traffic data if available
                if 'duration_in_traffic_min' in route_data:
                    route.duration_no_traffic_min = route_data['duration_min']
                    route.duration_min = route_data['duration_in_traffic_min']
                    route.traffic_delay_min = route_data.get('traffic_delay_min', 0)
                    route.has_traffic_data = True
                    
                print(f"   OK: {engine_name} route: {route.distance_km:.1f}km, {route.duration_min:.1f}min")
            else:
                # Use OSRM
                route_data = router.get_route(route_stops)
                route.coordinates = route_data['coordinates']
                route.distance_km = route_data['distance_km']
                route.duration_min = route_data['duration_min']
                print(f"   OK: {engine_name} route: {route.distance_km:.1f}km, {route.duration_min:.1f}min")
                
        except Exception as e:
            print(f"   ERROR: {engine_name} failed: {e}")
            route.calculate_stats_from_stops()
        
        cluster.assign_route(route)
        return route
    
    def optimize_all_clusters(self, clusters, use_traffic=False):
        """Optimize routes for all clusters."""
        routes = []
        
        from services.traffic import TrafficService
        departure_time = TrafficService.get_departure_time() if use_traffic else None
        
        for cluster in clusters:
            route = self.optimize_cluster_route(
                cluster=cluster,
                use_traffic=use_traffic,
                departure_time=departure_time
            )
            if route:
                routes.append(route)
        
        return routes

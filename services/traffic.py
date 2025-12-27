"""Traffic Service - handles traffic-aware routing."""
from routing_engines.tomtom import TrafficRouter


class TrafficService:
    """Service for adding traffic data to routes."""
    
    def __init__(self, config):
        self.config = config
        self.api_key = config.TOMTOM_API_KEY
        self.enabled = config.USE_TRAFFIC and bool(self.api_key)
        if self.enabled:
            self.router = TrafficRouter(api_key=self.api_key, cache_enabled=True)
        else:
            self.router = None
    
    @staticmethod
    def get_departure_time():
        """Get next 8 AM departure time."""
        from datetime import datetime, timedelta
        tomorrow_8am = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        if datetime.now().hour >= 8:
            tomorrow_8am += timedelta(days=1)
        return tomorrow_8am
    
    def add_traffic_data_to_route(self, route, departure_time=None):
        """
        Add traffic data to a route.
        
        Args:
            route: Route object to enhance
            departure_time: Departure time for traffic estimation
        
        Returns:
            True if traffic data was added, False otherwise
        """
        if not self.enabled or not self.router:
            return False
        
        if not route or not route.stops:
            return False
        
        try:
            departure_time = departure_time or self.get_departure_time()
            traffic_info = self.router.get_route_with_traffic(
                points=route.stops,
                departure_time=departure_time
            )
            
            route.set_traffic_data(traffic_info)
            
            return True
            
        except Exception as e:
            print(f"   WARNING: Could not get traffic data: {e}")
            return False
    
    def add_traffic_data_to_routes(self, routes):
        """Add traffic data to multiple routes."""
        if not self.enabled:
            return 0
        
        departure_time = self.get_departure_time()
        success_count = 0
        
        for route in routes:
            if self.add_traffic_data_to_route(route, departure_time):
                success_count += 1
        
        return success_count
    
    def is_enabled(self):
        """Check if traffic service is enabled."""
        return self.enabled

"""Traffic Service"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from modules.traffic_router import TrafficRouter


class TrafficService:
    """Trafik analizi"""
    
    def __init__(self, config):
        self.config = config
        self.api_key = config.TOMTOM_API_KEY
        self.enabled = config.USE_TRAFFIC and bool(self.api_key)
        if self.enabled:
            self.router = TrafficRouter(api_key=self.api_key, cache_enabled=True)
        else:
            self.router = None
    
    def add_traffic_data_to_route(self, route, departure_time=None):
        """Trafik verisi ekle"""
        if not self.enabled or not self.router:
            return False
        
        if not route or not route.stops:
            return False
        
        try:
            departure_time = departure_time or self.config.get_departure_time()
            traffic_info = self.router.get_route_with_traffic(
                points=route.stops,
                departure_time=departure_time
            )
            
            # Route objesine ekle
            route.set_traffic_data(traffic_info)
            
            return True
            
        except Exception as e:
            print(f"   WARNING: Trafik verisi alınamadı: {e}")
            return False
    
    def add_traffic_data_to_routes(self, routes):
        """
        Birden fazla rotaya trafik verisi ekle
        
        Args:
            routes: Route listesi
        
        Returns:
            int: Başarılı olan rota sayısı
        """
        if not self.enabled:
            return 0
        
        departure_time = self.config.get_departure_time()
        success_count = 0
        
        for route in routes:
            if self.add_traffic_data_to_route(route, departure_time):
                success_count += 1
        
        return success_count
    
    def is_enabled(self):
        """Trafik analizi aktif mi?"""
        return self.enabled

"""
RoutingService - Rota optimizasyonu
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from modules.tsp_optimizer import TSPOptimizer
from modules.osrm_router import OSRMRouter
from models.route import Route


class RoutingService:
    """Rota optimizasyonu ve yönetimi"""
    
    def __init__(self, config):
        """
        Args:
            config: Config objesi
        """
        self.config = config
        self.strategy = 'tsp'  # TSP (Traveling Salesman Problem)
        self.office_location = config.OFFICE_LOCATION
        self.optimizer = TSPOptimizer(office_location=self.office_location)
        self.osrm_router = OSRMRouter()  # OSRM ile rota çizimi
    
    def optimize_cluster_route(self, cluster, use_traffic=False, 
                              api_key=None, departure_time=None):
        """
        Tek bir cluster'ın rotasını optimize et
        
        Args:
            cluster: Cluster objesi
            use_traffic: Trafik verisi kullan
            api_key: TomTom API key
            departure_time: Kalkış zamanı
        
        Returns:
            Route: Optimize edilmiş Route objesi
        """
        # Aktif çalışan konumlarını al
        employee_locations = cluster.get_employee_locations(include_excluded=False)
        
        if len(employee_locations) == 0:
            return None
        
        # TSPOptimizer kullan (OOP)
        optimized_stops = self.optimizer.optimize(
            points=employee_locations,
            use_traffic=use_traffic,
            api_key=api_key,
            departure_time=departure_time,
            k_nearest=5
        )
        
        # Route objesi oluştur
        route = Route(cluster=cluster)
        route.set_stops(optimized_stops)  # optimized_stops = [(lat, lon), ...]
        route.mark_optimized()
        
        # Trafik YOKSA: OSRM ile rota çizgisi al
        if not use_traffic:
            try:
                # optimized_stops zaten [(lat, lon), ...] formatında
                osrm_data = self.osrm_router.get_route(optimized_stops)
                
                # OSRM koordinatlarını ve istatistiklerini kaydet
                route.coordinates = osrm_data['coordinates']
                route.distance_km = osrm_data['distance_km']
                route.duration_min = osrm_data['duration_min']
                print(f"✓ OSRM route: {route.distance_km:.1f}km, {route.duration_min:.1f}min")
            except Exception as e:
                print(f"✗ OSRM failed, using Haversine: {e}")
                # Hata durumunda Haversine kullan
                route.calculate_stats_from_stops()
        else:
            # Trafik VARSA: Basit istatistikler (TrafficService günceller)
            route.calculate_stats_from_stops()
        
        # Cluster'a rotayı ata
        cluster.assign_route(route)
        
        return route
    
    def optimize_all_clusters(self, clusters, use_traffic=False):
        """
        Tüm cluster'ların rotalarını optimize et
        
        Args:
            clusters: Cluster listesi
            use_traffic: Trafik verisi kullan
        
        Returns:
            list: Route objeleri listesi
        """
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

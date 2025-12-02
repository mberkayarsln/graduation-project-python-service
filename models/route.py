"""
Route - Rota sınıfı
"""


class Route:
    """Bir rotayı temsil eder"""
    
    def __init__(self, cluster=None):
        """
        Args:
            cluster: Cluster objesi (opsiyonel)
        """
        self.cluster = cluster
        self.stops = []               # [(lat, lon), ...] - Durak noktaları
        self.coordinates = []         # [(lat, lon), ...] - Detaylı yol çizgisi
        self.distance_km = 0.0
        self.duration_min = 0.0
        self.duration_no_traffic_min = 0.0
        self.traffic_delay_min = 0.0
        self.optimized = False
        self.has_traffic_data = False
    
    def set_stops(self, stops):
        """
        Durak noktalarını ayarla
        
        Args:
            stops: [(lat, lon), ...] listesi
        """
        self.stops = stops
    
    def set_coordinates(self, coordinates):
        """
        Yol koordinatlarını ayarla (OSRM/TomTom'dan gelen)
        
        Args:
            coordinates: [(lat, lon), ...] listesi
        """
        self.coordinates = coordinates
    
    def add_stop(self, lat, lon):
        """Rotaya durak ekle"""
        self.stops.append((lat, lon))
    
    def set_distance(self, distance_km):
        """Mesafe bilgisi"""
        self.distance_km = distance_km
    
    def set_duration(self, duration_min, no_traffic_min=None):
        """
        Süre bilgisi
        
        Args:
            duration_min: Toplam süre (trafikli)
            no_traffic_min: Trafiksiz süre (opsiyonel)
        """
        self.duration_min = duration_min
        if no_traffic_min:
            self.duration_no_traffic_min = no_traffic_min
            self.traffic_delay_min = duration_min - no_traffic_min
            self.has_traffic_data = True
    
    def set_traffic_data(self, traffic_info):
        """
        Trafik verilerini ekle
        
        Args:
            traffic_info: Dict {
                'coordinates': [...],
                'distance_km': float,
                'duration_with_traffic_min': float,
                'duration_no_traffic_min': float,
                'traffic_delay_min': float
            }
        """
        self.coordinates = traffic_info.get('coordinates', [])
        self.distance_km = traffic_info.get('distance_km', 0)
        self.duration_min = traffic_info.get('duration_with_traffic_min', 0)
        self.duration_no_traffic_min = traffic_info.get('duration_no_traffic_min', 0)
        self.traffic_delay_min = traffic_info.get('traffic_delay_min', 0)
        self.has_traffic_data = True
    
    def mark_optimized(self):
        """Rotanın optimize edildiğini işaretle"""
        self.optimized = True
    
    def get_stop_count(self):
        """Durak sayısı"""
        return len(self.stops)
    
    def get_avg_speed_kmh(self):
        """Ortalama hız hesapla"""
        if self.duration_min > 0:
            return (self.distance_km / self.duration_min) * 60
        return 0
    
    def calculate_stats_from_stops(self):
        """
        Durak noktalarından istatistikleri hesapla
        (Trafik verisi yoksa kullanılır)
        """
        if not self.stops or len(self.stops) < 2:
            self.distance_km = 0
            self.duration_min = 0
            return
        
        # TSPOptimizer'ın haversine metodunu kullan
        from modules.tsp_optimizer import TSPOptimizer
        
        # Toplam mesafe
        total_distance = 0
        for i in range(len(self.stops) - 1):
            lat1, lon1 = self.stops[i]
            lat2, lon2 = self.stops[i + 1]
            total_distance += TSPOptimizer.haversine(lat1, lon1, lat2, lon2)
        
        self.distance_km = total_distance / 1000
        
        # Ortalama hız varsayımı (şehir içi, trafiksiz)
        avg_speed_kmh = 40
        self.duration_min = (self.distance_km / avg_speed_kmh) * 60
    
    def get_stats(self):
        """Rota istatistikleri"""
        stats = {
            'stops': len(self.stops),
            'distance_km': round(self.distance_km, 2),
            'duration_min': round(self.duration_min, 1),
            'avg_speed_kmh': round(self.get_avg_speed_kmh(), 1),
            'optimized': self.optimized,
            'has_traffic_data': self.has_traffic_data
        }
        
        if self.has_traffic_data:
            stats['duration_no_traffic_min'] = round(self.duration_no_traffic_min, 1)
            stats['traffic_delay_min'] = round(self.traffic_delay_min, 1)
        
        return stats
    
    def to_dict(self):
        """Dictionary'ye dönüştür (visualizer için)"""
        return {
            'coordinates': self.coordinates if self.coordinates else self.stops,
            'stops': self.stops,
            'distance_km': self.distance_km,
            'duration_min': self.duration_min
        }
    
    def __repr__(self):
        return f"Route(stops={len(self.stops)}, distance={self.distance_km:.1f}km)"
    
    def __str__(self):
        traffic_info = f", +{self.traffic_delay_min:.0f}dk trafik" if self.has_traffic_data else ""
        return f"Rota: {len(self.stops)} durak, {self.distance_km:.1f}km, {self.duration_min:.0f}dk{traffic_info}"

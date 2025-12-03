"""Stop Clusterer"""
from sklearn.cluster import KMeans
import numpy as np
from pyrosm import OSM
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points


class StopClusterer:
    """Durak noktaları oluştur (sub-clustering)"""
    
    def __init__(self, osm_file="data/istanbul-center.osm.pbf", snap_to_roads=True):
        self.osm_file = osm_file
        self.snap_to_roads = snap_to_roads
        self._roads = None
    
    def _load_major_roads(self):
        """Ana yolları yükle"""
        if self._roads is not None:
            return self._roads
        
        try:
            osm = OSM(self.osm_file)
            roads = osm.get_network(network_type="driving")
            major_roads = roads[roads['highway'].isin([
                'motorway', 'trunk', 'primary', 'secondary'
            ])]
            
            self._roads = major_roads
            return self._roads
        except Exception as e:
            print(f"⚠️  Ana yollar yüklenemedi: {e}")
            self._roads = None
            return None
    
    def _snap_to_nearest_road(self, lat, lon, max_distance=200):
        """En yakın yola snap"""
        if not self.snap_to_roads or self._roads is None:
            return (lat, lon)
        
        try:
            point = Point(lon, lat)
            min_distance = float('inf')
            nearest_point = None
            
            for _, road in self._roads.iterrows():
                if road.geometry is None:
                    continue
                road_nearest = nearest_points(point, road.geometry)[1]
                distance = point.distance(road_nearest)
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_point = road_nearest
            
            # Eğer çok uzaktaysa snap yapma
            if nearest_point and min_distance < max_distance / 111320:  # metre → derece yaklaşık
                return (nearest_point.y, nearest_point.x)  # lat, lon
            
        except Exception as e:
            print(f"⚠️  Road snapping hatası: {e}")
        
        return (lat, lon)  # Başarısız, orijinali dön
    
    @staticmethod
    def calculate_optimal_stops(n_employees, employees_per_stop, min_stops, max_stops):
        """
        Cluster boyutuna göre optimal durak sayısını hesapla
        
        Args:
            n_employees: Çalışan sayısı
            employees_per_stop: Durak başına ideal çalışan sayısı
            min_stops: Minimum durak sayısı
            max_stops: Maximum durak sayısı
        
        Returns:
            int: Durak sayısı
        """
        if n_employees == 0:
            return 0
        
        # Her X çalışana 1 durak
        calculated = n_employees // employees_per_stop
        
        # Min-max aralığında tut
        return max(min_stops, min(calculated, max_stops))
    
    def generate_stops(self, employees, n_stops=None, employees_per_stop=None, 
                      min_stops=2, max_stops=15):
        """Durakları oluştur (sub-clustering)"""
        if not employees or len(employees) == 0:
            return {
                'stops': [],
                'assignments': [],
                'stop_loads': []
            }
        
        if n_stops is None:
            if employees_per_stop is None:
                employees_per_stop = 4
            
            n_stops = self.calculate_optimal_stops(
                len(employees), 
                employees_per_stop=employees_per_stop,
                min_stops=min_stops,
                max_stops=max_stops
            )
        if len(employees) == 1:
            return {
                'stops': [(employees[0].lat, employees[0].lon)],
                'assignments': [0],
                'stop_loads': [1]
            }
        
        # Çalışan sayısı durak sayısından azsa
        if len(employees) <= n_stops:
            stops = [(emp.lat, emp.lon) for emp in employees]
            assignments = list(range(len(employees)))
            stop_loads = [1] * len(employees)
            return {
                'stops': stops,
                'assignments': assignments,
                'stop_loads': stop_loads
            }
        
        # K-means ile sub-clustering
        coordinates = np.array([[emp.lat, emp.lon] for emp in employees])
        
        kmeans = KMeans(
            n_clusters=n_stops,
            random_state=42,
            n_init=10
        )
        
        labels = kmeans.fit_predict(coordinates)
        centers = kmeans.cluster_centers_
        
        # Ana yolları yükle (snap aktifse)
        if self.snap_to_roads:
            self._load_major_roads()
        
        # Durak koordinatları (ana yollara snap et)
        stops = []
        snapped_count = 0
        
        for lat, lon in centers:
            if self.snap_to_roads:
                snapped_lat, snapped_lon = self._snap_to_nearest_road(lat, lon, max_distance=200)
                if (snapped_lat, snapped_lon) != (lat, lon):
                    snapped_count += 1
                stops.append((snapped_lat, snapped_lon))
            else:
                stops.append((float(lat), float(lon)))
        
        if self.snap_to_roads and snapped_count > 0:
            print(f"      → {snapped_count}/{n_stops} durak ana yola yerleştirildi")
        
        # Her çalışanın durak ataması
        assignments = labels.tolist()
        
        # Her duraktaki yük (çalışan sayısı)
        stop_loads = [0] * n_stops
        for label in labels:
            stop_loads[label] += 1
        
        return {
            'stops': stops,
            'assignments': assignments,
            'stop_loads': stop_loads
        }
    
    def get_stats(self, result):
        """
        Durak istatistikleri
        
        Args:
            result: generate_stops() çıktısı
        
        Returns:
            dict: İstatistikler
        """
        if not result['stops']:
            return {
                'n_stops': 0,
                'total_employees': 0,
                'avg_load': 0,
                'min_load': 0,
                'max_load': 0
            }
        
        loads = result['stop_loads']
        
        return {
            'n_stops': len(result['stops']),
            'total_employees': sum(loads),
            'avg_load': sum(loads) / len(loads),
            'min_load': min(loads),
            'max_load': max(loads),
            'balance_ratio': min(loads) / max(loads) if max(loads) > 0 else 0
        }

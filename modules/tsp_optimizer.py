"""
TSPOptimizer - TSP optimization (OOP)
"""
import math
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


class TSPOptimizer:
    """
    Traveling Salesman Problem (TSP) çözücü
    Google OR-Tools kullanır
    """
    
    def __init__(self, office_location=None):
        """
        Args:
            office_location: Başlangıç/bitiş noktası (lat, lon)
        """
        self.office_location = office_location
        self.distance_matrix = None
        self.solution_route = None
    
    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        """
        İki nokta arası kuş uçuşu mesafe (Haversine formülü)
        
        Args:
            lat1, lon1: İlk nokta
            lat2, lon2: İkinci nokta
        
        Returns:
            float: Mesafe (metre)
        """
        r = 6371000  # Dünya yarıçapı (metre)
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        
        a = (math.sin(dphi / 2) ** 2 + 
             math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
        
        return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    def compute_distance_matrix(self, points, use_traffic=False, 
                                api_key=None, departure_time=None, k_nearest=5):
        """
        Nokta-nokta mesafe matrisi oluştur
        
        Args:
            points: [(lat, lon), ...] listesi
            use_traffic: Trafik verisi kullan
            api_key: TomTom API key
            departure_time: Kalkış zamanı
            k_nearest: Trafik için en yakın k komşu
        
        Returns:
            list: 2D mesafe matrisi
        """
        n = len(points)
        matrix = [[0] * n for _ in range(n)]
        
        # Önce Haversine matrisi oluştur
        haversine_matrix = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                dist = self.haversine(*points[i], *points[j])
                haversine_matrix[i][j] = dist
                haversine_matrix[j][i] = dist
        
        # Trafik verisi varsa
        if use_traffic and api_key:
            from modules.traffic_router import TrafficRouter

            # TrafficRouter instance oluştur (cache ile)
            router = TrafficRouter(api_key=api_key, cache_enabled=True)

            print(f"    building traffic-aware matrix (API calls for all pairs)...")

            api_calls = 0
            total_possible = n * (n - 1) // 2

            # Tüm i<j çiftleri için API çağrısı yap (matris tamamen API sürelerinden oluşacak)
            for i in range(n):
                for j in range(i + 1, n):
                    try:
                        result = router.get_route_with_traffic([points[i], points[j]], departure_time)
                        # TomTom döndürdüğü değer dakika cinsinden, burayı saniyeye çevir
                        duration_seconds = int(result['duration_with_traffic_min'] * 60)
                        matrix[i][j] = duration_seconds
                        matrix[j][i] = duration_seconds
                        api_calls += 1
                    except Exception as e:
                        # Beklenmeyen hata: uyarı ver, fallback olarak Haversine-based süre kullan
                        # (Not: API hatası tüm çalışmayı bozmasın diye yedek bırakıldı)
                        print(f"    Warning: traffic API call failed for pair ({i},{j}): {e}")
                        # Haversine -> süre yaklaşık tahmin (şehir hızı 30km/h)
                        CITY_SPEED_KMH = 30
                        distance_km = haversine_matrix[i][j] / 1000
                        duration_seconds = int((distance_km / CITY_SPEED_KMH) * 3600)
                        matrix[i][j] = duration_seconds
                        matrix[j][i] = duration_seconds

            print(f"    API calls: {api_calls}/{total_possible} (%{(api_calls/total_possible)*100:.1f} of possible)")
        else:
            # Trafiksiz mod: OSRM mesafelerini kullan
            from modules.osrm_router import OSRMRouter
            osrm = OSRMRouter()
            
            print(f"    building distance matrix with OSRM (road distances for all pairs)...")
            
            api_calls = 0
            total_possible = n * (n - 1) // 2
            
            # Tüm i<j çiftleri için OSRM çağrısı yap
            for i in range(n):
                for j in range(i + 1, n):
                    try:
                        result = osrm.get_route([points[i], points[j]])
                        # OSRM mesafe km cinsinden döndürür, metre'ye çevir
                        distance_meters = int(result['distance_km'] * 1000)
                        matrix[i][j] = distance_meters
                        matrix[j][i] = distance_meters
                        api_calls += 1
                    except Exception as e:
                        # OSRM başarısız olursa Haversine kullan
                        print(f"    Warning: OSRM call failed for pair ({i},{j}): {e}")
                        matrix[i][j] = int(haversine_matrix[i][j])
                        matrix[j][i] = int(haversine_matrix[i][j])
            
            print(f"    OSRM calls: {api_calls}/{total_possible} (%{(api_calls/total_possible)*100:.1f} of possible)")
        
        self.distance_matrix = matrix
        return matrix
    
    def optimize(self, points, use_traffic=False, api_key=None, 
                departure_time=None, k_nearest=5):
        """
        TSP optimizasyonu yap
        
        Args:
            points: Ziyaret edilecek noktalar [(lat, lon), ...]
            use_traffic: Trafik verisi kullan
            api_key: TomTom API key
            departure_time: Kalkış zamanı
            k_nearest: Trafik için en yakın k komşu
        
        Returns:
            list: Optimize edilmiş rota [(lat, lon), ...]
        """
        # Ofis konumu varsa ekle
        all_points = points + ([self.office_location] if self.office_location else [])
        n = len(all_points)
        
        # Mesafe matrisi oluştur
        dist_matrix = self.compute_distance_matrix(
            all_points, use_traffic, api_key, departure_time, k_nearest
        )
        
        # OR-Tools ile TSP çöz
        manager = pywrapcp.RoutingIndexManager(n, 1, 0)  # 0 = başlangıç noktası
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
            
            # Ofise dönüş ekle
            if self.office_location and route[-1] != self.office_location:
                route.append(self.office_location)
            
            self.solution_route = route
            return route
        
        # Çözüm bulunamazsa orijinal sırayı dön
        return all_points

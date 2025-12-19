import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.location_service import LocationService
from services.clustering_service import ClusteringService
from services.routing_service import RoutingService
from services.traffic_service import TrafficService
from services.visualization_service import VisualizationService
from models.vehicle import Vehicle


class ServicePlanner:    
    def __init__(self, config):
        self.config = config
        
        self.employees = []
        self.clusters = []
        self.vehicles = []
        
        self.location_service = LocationService(config)
        self.clustering_service = ClusteringService(config)
        self.routing_service = RoutingService(config)
        self.traffic_service = TrafficService(config)
        self.visualization_service = VisualizationService(config)
        
        self.stats = {}
    
    def generate_employees(self, count=None, seed=None):
        count = count or self.config.NUM_EMPLOYEES
        seed = seed if seed is not None else 42
        
        print(f"[1] {count} çalışan konumu oluşturuluyor...")
        self.employees = self.location_service.generate_employees(count, seed)
        print(f"    OK: {len(self.employees)} çalışan oluşturuldu")
        
        return self.employees
    
    def create_clusters(self, num_clusters=None):
        num_clusters = num_clusters or self.config.NUM_CLUSTERS
        
        print(f"[2] {num_clusters} cluster oluşturuluyor...")
        self.clusters = self.clustering_service.cluster_employees(
            self.employees,
            num_clusters,
            random_state=42
        )
        print(f"    OK: {len(self.clusters)} cluster oluşturuldu")
        
        return self.clusters
    
    def filter_employees_by_distance(self):
        max_distance = self.config.MAX_DISTANCE_FROM_CENTER
        total_excluded = 0
        
        print(f"[3] Uzak çalışanlar filtreleniyor (max: {max_distance/1000}km)...")
        for cluster in self.clusters:
            excluded = cluster.filter_by_distance(max_distance)
            total_excluded += excluded
        
        print(f"    OK: {total_excluded} çalışan hariç tutuldu")
        
        return total_excluded
    
    def generate_stops(self):
        print(f"[4] Finding farthest employees from office in each cluster...")
        
        office_lat, office_lon = self.config.OFFICE_LOCATION
        total_routes = 0
        
        for cluster in self.clusters:
            active_employees = cluster.get_active_employees()
            
            if len(active_employees) == 0:
                continue
            
            max_distance = 0
            farthest_employee = None
            
            for employee in active_employees:
                distance = employee.distance_to(office_lat, office_lon)
                if distance > max_distance:
                    max_distance = distance
                    farthest_employee = employee
            
            if farthest_employee:
                cluster_center = cluster.center
                route_points = [
                    farthest_employee.get_location(),
                    cluster_center,
                    self.config.OFFICE_LOCATION
                ]
                
                cluster.set_stops(
                    stops=route_points,
                    assignments=[0] * len(active_employees) + [1, 2],
                    stop_loads=[len(active_employees), 0, 0]
                )
                
                total_routes += 1
                print(f"   Cluster {cluster.id}: Farthest employee {farthest_employee.id} "
                      f"at {max_distance/1000:.2f}km → cluster center → office")
        
        print(f"    OK: {total_routes} direct routes created")
        
        return {
            'total_routes': total_routes
        }
    
    def optimize_routes(self, use_traffic=None, use_stops=True):
        use_traffic = use_traffic if use_traffic is not None else self.config.USE_TRAFFIC
        
        mode = "duraklar" if use_stops else "çalışan konumları"
        print(f"[5] Rotalar oluşturuluyor ({mode}, trafik: {'ON' if use_traffic else 'OFF'})...")
        
        routes = []
        api_key = self.config.TOMTOM_API_KEY if use_traffic else None
        departure_time = self.traffic_service.get_departure_time() if use_traffic else None
        
        for cluster in self.clusters:
            route = self.routing_service.optimize_cluster_route(
                cluster=cluster,
                use_traffic=use_traffic,
                api_key=api_key,
                departure_time=departure_time,
                use_stops=use_stops
            )
            if route:
                routes.append(route)
        
        for i, cluster in enumerate(self.clusters):
            if cluster.route:
                active = cluster.get_employee_count(include_excluded=False)
                if use_stops and cluster.has_stops():
                    n_stops = len(cluster.stops)
                else:
                    n_stops = len(cluster.route.stops) - 1 if len(cluster.route.stops) > 0 else 0
                
                print(f"   Cluster {cluster.id}: {active} çalışan → {n_stops} durak")
        
        print(f"    OK: {len(routes)} rota oluşturuldu")
        
        if use_traffic and self.traffic_service.is_enabled():
            print(f"Trafik verileri ekleniyor...")
            success = self.traffic_service.add_traffic_data_to_routes(routes)
            print(f"    OK: {success}/{len(routes)} rotaya trafik verisi eklendi")
        
        return routes
    
    def assign_vehicles(self):
        print(f"Araçlar atanıyor...")
        
        self.vehicles = []
        for i, cluster in enumerate(self.clusters):
            vehicle = Vehicle(
                id=i + 1,
                capacity=50,
                vehicle_type="Minibüs"
            )
            vehicle.assign_cluster(cluster)
            vehicle.set_departure_time(self.traffic_service.get_departure_time())
            cluster.assign_vehicle(vehicle)
            self.vehicles.append(vehicle)
        
        print(f"    OK: {len(self.vehicles)} araç atandı")
        
        return self.vehicles
    
    def generate_maps(self):
        print(f"[6] Haritalar oluşturuluyor...")
        
        files = self.visualization_service.create_all_maps(self.clusters)
        
        
        print(f"    OK: {files[0]} (çalışanlar)")
        print(f"    OK: {files[1]} (cluster'lar)")
        print(f"    OK: {files[2]} (rotalar)")
        
        
        if len(files) > 3:
            print(f"    OK: {len(files) - 3} detaylı cluster haritası oluşturuldu")
        
        return files
    
    def calculate_statistics(self):
        total_employees = len(self.employees)
        excluded_employees = sum(1 for emp in self.employees if emp.excluded)
        active_employees = total_employees - excluded_employees
        
        total_distance = 0
        total_duration = 0
        total_traffic_delay = 0
        
        for cluster in self.clusters:
            if cluster.route:
                total_distance += cluster.route.distance_km
                total_duration += cluster.route.duration_min
                if cluster.route.has_traffic_data:
                    total_traffic_delay += cluster.route.traffic_delay_min
        
        self.stats = {
            'total_employees': total_employees,
            'active_employees': active_employees,
            'excluded_employees': excluded_employees,
            'num_clusters': len(self.clusters),
            'num_vehicles': len(self.vehicles),
            'total_distance_km': round(total_distance, 2),
            'total_duration_min': round(total_duration, 1),
            'total_traffic_delay_min': round(total_traffic_delay, 1),
            'use_traffic': self.traffic_service.is_enabled()
        }
        
        return self.stats
    
    def print_summary(self):
        stats = self.calculate_statistics()
        
        print("\n" + "=" * 50)
        print("                    ÖZET")
        print("=" * 50)
        print(f"✓ Toplam Çalışan: {stats['total_employees']}")
        print(f"✓ Aktif Çalışan: {stats['active_employees']}")
        print(f"✓ Hariç Tutulan: {stats['excluded_employees']}")
        print(f"✓ Cluster Sayısı: {stats['num_clusters']}")
        print(f"✓ Araç Sayısı: {stats['num_vehicles']}")
        print(f"✓ Toplam Mesafe: {stats['total_distance_km']} km")
        print(f"✓ Toplam Süre: {stats['total_duration_min']:.0f} dakika")
        
        if stats['use_traffic'] and stats['total_traffic_delay_min'] > 0:
            print(f"⚠ Trafik Gecikmesi: +{stats['total_traffic_delay_min']:.0f} dakika")
        
        print(f"✓ Trafik Analizi: {'Aktif' if stats['use_traffic'] else 'Pasif'}")
        print("=" * 50 + "\n")
    
    def run(self):
        print("\n" + "=" * 50)
        print("        SERVİS ROTA OPTİMİZASYONU (OOP)")
        print("=" * 50)
        print(f"Çalışan Sayısı: {self.config.NUM_EMPLOYEES}")
        print(f"Cluster Sayısı: {self.config.NUM_CLUSTERS}")
        print(f"Trafik Analizi: {'✓ Aktif' if self.config.USE_TRAFFIC else '✗ Pasif'}")
        print("=" * 50 + "\n")
        
        self.generate_employees()
        
        self.create_clusters()
        
        self.filter_employees_by_distance()
        
        self.generate_stops()
        
        self.optimize_routes(use_stops=True)
        
        self.assign_vehicles()
        
        self.generate_maps()
        
        self.print_summary()

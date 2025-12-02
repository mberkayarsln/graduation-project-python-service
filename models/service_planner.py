"""
ServicePlanner - Ana koordinatör sınıfı
"""
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
    """
    Ana servis planlama koordinatörü
    
    Tüm işlemleri yönetir:
    - Çalışan konumları oluşturma
    - Clustering
    - Rota optimizasyonu
    - Trafik analizi
    - Harita oluşturma
    """
    
    def __init__(self, config):
        """
        Args:
            config: Config objesi
        """
        self.config = config
        
        # Data
        self.employees = []
        self.clusters = []
        self.vehicles = []
        
        # Services
        self.location_service = LocationService(config)
        self.clustering_service = ClusteringService(config)
        self.routing_service = RoutingService(config)
        self.traffic_service = TrafficService(config)
        self.visualization_service = VisualizationService(config)
        
        # Statistics
        self.stats = {}
    
    def generate_employees(self, count=None, seed=None):
        """
        Çalışan konumları oluştur
        
        Args:
            count: Çalışan sayısı (None ise config'den al)
            seed: Random seed
        
        Returns:
            list: Employee listesi
        """
        count = count or self.config.NUM_EMPLOYEES
        seed = seed if seed is not None else 42
        
        print(f"📍 {count} çalışan konumu oluşturuluyor...")
        self.employees = self.location_service.generate_employees(count, seed)
        print(f"   ✓ {len(self.employees)} çalışan oluşturuldu")
        
        return self.employees
    
    def create_clusters(self, num_clusters=None):
        """
        Çalışanları kümele
        
        Args:
            num_clusters: Küme sayısı (None ise config'den al)
        
        Returns:
            list: Cluster listesi
        """
        num_clusters = num_clusters or self.config.NUM_CLUSTERS
        
        print(f"🔵 {num_clusters} cluster oluşturuluyor...")
        self.clusters = self.clustering_service.cluster_employees(
            self.employees,
            num_clusters,
            random_state=42
        )
        print(f"   ✓ {len(self.clusters)} cluster oluşturuldu")
        
        return self.clusters
    
    def filter_employees_by_distance(self):
        """
        Merkeze uzak çalışanları filtrele
        
        Returns:
            int: Hariç tutulan toplam çalışan sayısı
        """
        max_distance = self.config.MAX_DISTANCE_FROM_CENTER
        total_excluded = 0
        
        print(f"🔍 Uzak çalışanlar filtreleniyor (max: {max_distance/1000}km)...")
        for cluster in self.clusters:
            excluded = cluster.filter_by_distance(max_distance)
            total_excluded += excluded
        
        print(f"   ✓ {total_excluded} çalışan hariç tutuldu")
        
        return total_excluded
    
    def optimize_routes(self, use_traffic=None):
        """
        Tüm rotaları optimize et
        
        Args:
            use_traffic: Trafik verisi kullan (None ise config'den al)
        
        Returns:
            list: Route listesi
        """
        use_traffic = use_traffic if use_traffic is not None else self.config.USE_TRAFFIC
        
        print(f"🚗 Rotalar optimize ediliyor (trafik: {'✓' if use_traffic else '✗'})...")
        
        # Rota optimizasyonu
        routes = self.routing_service.optimize_all_clusters(
            self.clusters,
            use_traffic=use_traffic
        )
        
        for i, cluster in enumerate(self.clusters):
            if cluster.route:
                active = cluster.get_employee_count(include_excluded=False)
                print(f"   Cluster {cluster.id}: {active} çalışan → {len(cluster.route.stops)} durak")
        
        print(f"   ✓ {len(routes)} rota oluşturuldu")
        
        # Trafik verisi ekle (eğer aktifse)
        if use_traffic and self.traffic_service.is_enabled():
            print(f"🚦 Trafik verileri ekleniyor...")
            success = self.traffic_service.add_traffic_data_to_routes(routes)
            print(f"   ✓ {success}/{len(routes)} rotaya trafik verisi eklendi")
        
        return routes
    
    def assign_vehicles(self):
        """
        Cluster'lara araç ata
        
        Returns:
            list: Vehicle listesi
        """
        print(f"🚌 Araçlar atanıyor...")
        
        self.vehicles = []
        for i, cluster in enumerate(self.clusters):
            vehicle = Vehicle(
                id=i + 1,
                capacity=50,
                vehicle_type="Minibüs"
            )
            vehicle.assign_cluster(cluster)
            vehicle.set_departure_time(self.config.get_departure_time())
            cluster.assign_vehicle(vehicle)
            self.vehicles.append(vehicle)
        
        print(f"   ✓ {len(self.vehicles)} araç atandı")
        
        return self.vehicles
    
    def generate_maps(self):
        """
        Haritaları oluştur
        
        Returns:
            list: Dosya adları
        """
        print(f"🗺️  Haritalar oluşturuluyor...")
        
        files = self.visualization_service.create_all_maps(self.clusters)
        
        for file in files:
            print(f"   ✓ {file}")
        
        return files
    
    def calculate_statistics(self):
        """İstatistikleri hesapla"""
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
        """Özet istatistikleri yazdır"""
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
        """
        Tüm süreci çalıştır
        
        1. Çalışan konumları oluştur
        2. Clustering yap
        3. Uzak çalışanları filtrele
        4. Rotaları optimize et
        5. Araçları ata
        6. Haritaları oluştur
        7. İstatistikleri göster
        """
        print("\n" + "=" * 50)
        print("        SERVİS ROTA OPTİMİZASYONU (OOP)")
        print("=" * 50)
        print(f"Çalışan Sayısı: {self.config.NUM_EMPLOYEES}")
        print(f"Cluster Sayısı: {self.config.NUM_CLUSTERS}")
        print(f"Trafik Analizi: {'✓ Aktif' if self.config.USE_TRAFFIC else '✗ Pasif'}")
        print("=" * 50 + "\n")
        
        # 1. Çalışan oluştur
        self.generate_employees()
        
        # 2. Clustering
        self.create_clusters()
        
        # 3. Filtrele
        self.filter_employees_by_distance()
        
        # 4. Rota optimizasyonu
        self.optimize_routes()
        
        # 5. Araç ataması
        self.assign_vehicles()
        
        # 6. Haritalar
        self.generate_maps()
        
        # 7. Özet
        self.print_summary()

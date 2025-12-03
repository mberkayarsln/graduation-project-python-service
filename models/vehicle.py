"""Vehicle model"""
from datetime import datetime


class Vehicle:
    """Servis aracı"""
    
    def __init__(self, id, capacity=50, vehicle_type="Minibüs"):
        self.id = id
        self.capacity = capacity
        self.vehicle_type = vehicle_type
        self.cluster = None
        self.route = None
        self.departure_time = None
        self.driver_name = None
    
    def assign_cluster(self, cluster):
        """Cluster ata"""
        self.cluster = cluster
        self.route = cluster.route if cluster else None
    
    def set_departure_time(self, departure_time):
        """Kalkış saati"""
        self.departure_time = departure_time
    
    def set_driver(self, driver_name):
        """Sürücü ata"""
        self.driver_name = driver_name
    
    def can_accommodate(self, employee_count):
        """Kapasite kontrolü"""
        return employee_count <= self.capacity
    
    def get_occupancy_rate(self):
        """Doluluk oranı (%)
        """
        if self.cluster:
            employee_count = self.cluster.get_employee_count()
            return (employee_count / self.capacity) * 100
        return 0
    
    def is_full(self):
        """Araç dolu mu?"""
        return self.get_occupancy_rate() >= 100
    
    def get_stats(self):
        """Araç istatistikleri"""
        stats = {
            'id': self.id,
            'type': self.vehicle_type,
            'capacity': self.capacity,
            'occupancy_rate': round(self.get_occupancy_rate(), 1),
            'has_cluster': self.cluster is not None,
            'has_route': self.route is not None,
            'driver': self.driver_name
        }
        
        if self.cluster:
            stats['cluster_id'] = self.cluster.id
            stats['employee_count'] = self.cluster.get_employee_count()
        
        if self.route:
            stats['route_distance_km'] = self.route.distance_km
            stats['route_duration_min'] = self.route.duration_min
        
        if self.departure_time:
            stats['departure_time'] = self.departure_time.strftime('%H:%M')
        
        return stats
    
    def __repr__(self):
        return f"Vehicle(id={self.id}, capacity={self.capacity})"
    
    def __str__(self):
        occupancy = f"{self.get_occupancy_rate():.0f}%" if self.cluster else "boş"
        return f"Araç {self.id} ({self.vehicle_type}): {occupancy}"

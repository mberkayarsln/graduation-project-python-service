"""
Cluster - Cluster sınıfı
"""


class Cluster:
    """Bir çalışan kümesini temsil eder"""
    
    def __init__(self, id, center):
        """
        Args:
            id: Cluster ID
            center: Merkez koordinatı (lat, lon)
        """
        self.id = id
        self.center = center  # (lat, lon) tuple
        self.employees = []   # Employee listesi
        self.route = None     # Route objesi
        self.vehicle = None   # Vehicle objesi
    
    def add_employee(self, employee):
        """
        Cluster'a çalışan ekle
        
        Args:
            employee: Employee objesi
        """
        self.employees.append(employee)
        employee.cluster_id = self.id
    
    def remove_employee(self, employee):
        """Çalışanı cluster'dan çıkar"""
        if employee in self.employees:
            self.employees.remove(employee)
            employee.cluster_id = None
    
    def filter_by_distance(self, max_distance):
        """
        Merkeze uzak çalışanları filtrele
        
        Args:
            max_distance: Maksimum mesafe (metre)
        
        Returns:
            int: Hariç tutulan çalışan sayısı
        """
        excluded_count = 0
        center_lat, center_lon = self.center
        
        for employee in self.employees:
            distance = employee.distance_to(center_lat, center_lon)
            if distance > max_distance:
                employee.exclude(f"Merkeze uzak ({distance:.0f}m)")
                excluded_count += 1
        
        return excluded_count
    
    def get_active_employees(self):
        """Hariç tutulmayan çalışanları döndür"""
        return [emp for emp in self.employees if not emp.excluded]
    
    def get_employee_count(self, include_excluded=False):
        """
        Çalışan sayısı
        
        Args:
            include_excluded: Hariç tutulanları da say
        
        Returns:
            int: Çalışan sayısı
        """
        if include_excluded:
            return len(self.employees)
        return len(self.get_active_employees())
    
    def get_employee_locations(self, include_excluded=False):
        """
        Çalışan konumlarını liste olarak döndür
        
        Returns:
            list: [(lat, lon), ...]
        """
        employees = self.employees if include_excluded else self.get_active_employees()
        return [emp.get_location() for emp in employees]
    
    def assign_route(self, route):
        """Cluster'a rota ata"""
        self.route = route
        route.cluster = self
    
    def assign_vehicle(self, vehicle):
        """Cluster'a araç ata"""
        self.vehicle = vehicle
        vehicle.cluster = self
    
    def get_stats(self):
        """Cluster istatistikleri"""
        active = self.get_employee_count(include_excluded=False)
        total = self.get_employee_count(include_excluded=True)
        excluded = total - active
        
        stats = {
            'id': self.id,
            'center': self.center,
            'total_employees': total,
            'active_employees': active,
            'excluded_employees': excluded,
            'has_route': self.route is not None,
            'has_vehicle': self.vehicle is not None
        }
        
        if self.route:
            stats['route_distance_km'] = self.route.distance_km
            stats['route_duration_min'] = self.route.duration_min
        
        return stats
    
    def __repr__(self):
        return f"Cluster(id={self.id}, employees={len(self.employees)})"
    
    def __str__(self):
        active = self.get_employee_count(include_excluded=False)
        total = self.get_employee_count(include_excluded=True)
        return f"Cluster {self.id}: {active}/{total} çalışan"

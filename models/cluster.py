"""Cluster model"""

class Cluster:
    """Çalışan kümesi"""
    
    def __init__(self, id, center):
        self.id = id
        self.center = center
        self.employees = []
        self.route = None
        self.vehicle = None
        self.stops = []
        self.stop_assignments = {}
        self.stop_loads = []
    
    def add_employee(self, employee):
        """Çalışan ekle"""
        self.employees.append(employee)
        employee.cluster_id = self.id
    
    def remove_employee(self, employee):
        """Çalışan çıkar"""
        if employee in self.employees:
            self.employees.remove(employee)
            employee.cluster_id = None
    
    def filter_by_distance(self, max_distance):
        """Uzak çalışanları filtrele (metre)"""
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
        """Çalışan sayısı"""
        if include_excluded:
            return len(self.employees)
        return len(self.get_active_employees())
    
    def get_employee_locations(self, include_excluded=False):
        """Çalışan lokasyonları: [(lat, lon), ...]"""
        employees = self.employees if include_excluded else self.get_active_employees()
        return [emp.get_location() for emp in employees]
    
    def assign_route(self, route):
        """Rota ata"""
        self.route = route
        route.cluster = self
    
    def assign_vehicle(self, vehicle):
        """Araç ata"""
        self.vehicle = vehicle
        vehicle.cluster = self
    
    def set_stops(self, stops, assignments, stop_loads):
        """Durak kaydet"""
        self.stops = stops
        self.stop_loads = stop_loads
        

        self.stop_assignments = {}
        active_employees = self.get_active_employees()
        
        for i, employee in enumerate(active_employees):
            if i < len(assignments):
                self.stop_assignments[employee.id] = assignments[i]
    
    def get_employee_stop(self, employee):
        """Çalışanın durağı: (index, location)"""
        if employee.id in self.stop_assignments:
            stop_index = self.stop_assignments[employee.id]
            if stop_index < len(self.stops):
                return stop_index, self.stops[stop_index]
        
        return None, None
    
    def has_stops(self):
        """Durak var mı?"""
        return len(self.stops) > 0
    
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
            'has_vehicle': self.vehicle is not None,
            'has_stops': self.has_stops(),
            'n_stops': len(self.stops)
        }
        
        if self.has_stops():
            stats['stop_loads'] = self.stop_loads
            stats['avg_load_per_stop'] = sum(self.stop_loads) / len(self.stop_loads) if self.stop_loads else 0
        
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

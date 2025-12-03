"""Employee model"""
import math


class Employee:
    """Çalışan"""
    
    def __init__(self, id, lat, lon, name=None):
        self.id = id
        self.lat = lat
        self.lon = lon
        self.name = name or f"Çalışan {id}"
        self.cluster_id = None
        self.excluded = False
        self.exclusion_reason = None
    
    def distance_to(self, other_lat, other_lon):
        """Haversine mesafe (metre)"""
        R = 6371000  # Dünya yarıçapı (metre)
        
        phi1 = math.radians(self.lat)
        phi2 = math.radians(other_lat)
        dphi = math.radians(other_lat - self.lat)
        dlambda = math.radians(other_lon - self.lon)
        
        a = (math.sin(dphi / 2) ** 2 + 
             math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def exclude(self, reason):
        """Hariç tut"""
        self.excluded = True
        self.exclusion_reason = reason
    
    def get_location(self):
        """(lat, lon)"""
        return (self.lat, self.lon)
    
    def to_dict(self):
        """Dict dönüştür"""
        return {
            'id': self.id,
            'lat': self.lat,
            'lon': self.lon,
            'name': self.name,
            'cluster': self.cluster_id,  # visualizer için 'cluster' key'i lazım
            'cluster_id': self.cluster_id,
            'excluded': self.excluded,
            'exclusion_reason': self.exclusion_reason
        }
    
    def __repr__(self):
        status = "excluded" if self.excluded else f"cluster {self.cluster_id}"
        return f"Employee(id={self.id}, {status})"
    
    def __str__(self):
        return f"{self.name} ({self.lat:.4f}, {self.lon:.4f})"

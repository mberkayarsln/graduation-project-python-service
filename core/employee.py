"""Employee model - represents a single employee with location data."""
import math


class Employee:
    """Represents an employee with geographic location and pickup assignment."""
    
    def __init__(self, id, lat, lon, name=None):
        self.id = id
        self.lat = lat
        self.lon = lon
        self.name = name or f"Employee {id}"
        self.cluster_id = None
        self.excluded = False
        self.exclusion_reason = ""
        self.pickup_point = None
        self.pickup_type = "route"  # 'route' (fallback) or 'stop' (safe osm stop)
    
    def set_pickup_point(self, lat, lon, type="route"):
        """Set the pickup point for this employee."""
        self.pickup_point = (lat, lon)
        self.pickup_type = type
    
    def distance_to(self, other_lat, other_lon):
        """Calculate distance in meters to another point using Haversine formula."""
        from utils.geo import haversine
        return haversine(self.lat, self.lon, other_lat, other_lon)
    
    def exclude(self, reason):
        """Mark employee as excluded from routing."""
        self.excluded = True
        self.exclusion_reason = reason
    
    def get_location(self):
        """Return (lat, lon) tuple."""
        return (self.lat, self.lon)
    
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'lat': self.lat,
            'lon': self.lon,
            'name': self.name,
            'cluster': self.cluster_id,
            'cluster_id': self.cluster_id,
            'excluded': self.excluded,
            'exclusion_reason': self.exclusion_reason
        }
    
    def __repr__(self):
        status = "excluded" if self.excluded else f"cluster {self.cluster_id}"
        return f"Employee(id={self.id}, {status})"
    
    def __str__(self):
        return f"{self.name} ({self.lat:.4f}, {self.lon:.4f})"

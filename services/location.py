"""Location Service - handles employee location generation and transit stops."""
from utils.data_generator import DataGenerator
from core.employee import Employee


class LocationService:
    """Service for generating and managing employee locations."""
    
    def __init__(self, config):
        self.config = config
        self.office_location = config.OFFICE_LOCATION
        self.data_generator = DataGenerator()
    
    def generate_employees(self, count, seed=None):
        """
        Generate random employee locations.
        
        Args:
            count: Number of employees to generate
            seed: Random seed for reproducibility
        
        Returns:
            List of Employee objects
        """
        df = self.data_generator.generate(n=count, seed=seed)
        employees = []
        for _, row in df.iterrows():
            employee = Employee(
                id=int(row['id']),
                lat=row['lat'],
                lon=row['lon'],
                name=f"Employee {int(row['id'])}"
            )
            employees.append(employee)
        
        return employees
    
    def get_transit_stops(self):
        """Get list of transit stops from OSM data."""
        return self.data_generator.get_transit_stops()
    
    def get_office_location(self):
        """Return the office location tuple."""
        return self.office_location
    
    def is_within_bounds(self, employee, max_distance_from_center):
        """Check if employee is within acceptable distance from office."""
        office_lat, office_lon = self.office_location
        distance = employee.distance_to(office_lat, office_lon)
        return distance <= max_distance_from_center

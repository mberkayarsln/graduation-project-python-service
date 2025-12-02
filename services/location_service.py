"""
LocationService - Konum işlemleri
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from modules.data_generator import DataGenerator
from models.employee import Employee


class LocationService:
    """Konum oluşturma ve yönetimi"""
    
    def __init__(self, config):
        """
        Args:
            config: Config objesi
        """
        self.config = config
        self.office_location = config.OFFICE_LOCATION
        self.data_generator = DataGenerator()
    
    def generate_employees(self, count, seed=None):
        """
        Rastgele çalışan konumları oluştur
        
        Args:
            count: Çalışan sayısı
            seed: Random seed (tekrarlanabilirlik için)
        
        Returns:
            list: Employee objeleri listesi
        """
        # DataGenerator kullan (OOP)
        df = self.data_generator.generate(n=count, seed=seed)
        
        # Employee objelerine dönüştür
        employees = []
        for _, row in df.iterrows():
            employee = Employee(
                id=int(row['id']),
                lat=row['lat'],
                lon=row['lon'],
                name=f"Çalışan {int(row['id'])}"
            )
            employees.append(employee)
        
        return employees
    
    def get_office_location(self):
        """Ofis konumunu döndür"""
        return self.office_location
    
    def is_within_bounds(self, employee, max_distance_from_center):
        """
        Çalışan belirli bir sınır içinde mi?
        
        Args:
            employee: Employee objesi
            max_distance_from_center: Maksimum mesafe (metre)
        
        Returns:
            bool: Sınır içinde mi?
        """
        office_lat, office_lon = self.office_location
        distance = employee.distance_to(office_lat, office_lon)
        return distance <= max_distance_from_center

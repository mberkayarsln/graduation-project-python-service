"""
OSRMRouter - OSRM API ile rota çizgisi alma
"""
import requests


class OSRMRouter:
    """
    OSRM (Open Source Routing Machine) ile yol çizgisi al
    Ücretsiz, trafik bilgisi yok
    """
    
    def __init__(self, base_url="https://router.project-osrm.org"):
        """
        Args:
            base_url: OSRM sunucu URL'i
        """
        self.base_url = base_url
    
    def get_route(self, points, profile='driving'):
        """
        OSRM'den rota al
        
        Args:
            points: [(lat, lon), ...] listesi
            profile: 'driving', 'car', 'bike', 'foot'
        
        Returns:
            dict: {
                'coordinates': [[lat, lon], ...],
                'distance_km': float,
                'duration_min': float
            }
        """
        # OSRM lon,lat formatı kullanır (ters!)
        coords = ';'.join([f"{lon},{lat}" for lat, lon in points])
        url = f"{self.base_url}/route/v1/{profile}/{coords}"
        
        params = {
            'overview': 'full',      # Tam detay
            'geometries': 'geojson'  # GeoJSON formatı
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'routes' not in data or len(data['routes']) == 0:
                raise Exception("No route found")
            
            route_data = data['routes'][0]
            
            # GeoJSON coordinates [lon, lat] → [lat, lon]
            coordinates = [[coord[1], coord[0]] for coord in route_data['geometry']['coordinates']]
            
            # Mesafe ve süre
            distance_km = route_data['distance'] / 1000
            duration_min = route_data['duration'] / 60
            
            return {
                'coordinates': coordinates,
                'distance_km': distance_km,
                'duration_min': duration_min
            }
            
        except requests.exceptions.RequestException as e:
            print(f"OSRM API error: {e}")
            raise
        except KeyError as e:
            print(f"Unexpected OSRM response format: {e}")
            raise

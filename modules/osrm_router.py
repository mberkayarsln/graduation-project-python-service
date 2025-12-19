import requests
from modules.api_cache import APICache


class OSRMRouter:    
    def __init__(self, base_url="https://router.project-osrm.org", cache_enabled=True):
        self.base_url = base_url
        self.cache = APICache(cache_file='data/osrm_cache.json') if cache_enabled else None
    
    def get_route(self, points, profile='driving'):
        if self.cache:
            cached_result = self.cache.get(points, departure_time=None)
            if cached_result is not None:
                return cached_result
        
        coords = ';'.join([f"{lon},{lat}" for lat, lon in points])
        url = f"{self.base_url}/route/v1/{profile}/{coords}"
        
        params = {
            'overview': 'full',      
            'geometries': 'geojson' 
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'routes' not in data or len(data['routes']) == 0:
                raise Exception("No route found")
            
            route_data = data['routes'][0]
            
            coordinates = [[coord[1], coord[0]] for coord in route_data['geometry']['coordinates']]
            
            distance_km = route_data['distance'] / 1000
            duration_min = route_data['duration'] / 60
            
            result = {
                'coordinates': coordinates,
                'distance_km': distance_km,
                'duration_min': duration_min
            }
            
            if self.cache:
                self.cache.set(points, departure_time=None, data=result)
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"OSRM API error: {e}")
            raise
        except KeyError as e:
            print(f"Unexpected OSRM response format: {e}")
            raise

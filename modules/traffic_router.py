"""Traffic Router"""
import requests
from datetime import datetime
from modules.api_cache import APICache


class TrafficRouter:
    """TomTom trafik verisi"""
    
    def __init__(self, api_key, cache_enabled=True):
        self.api_key = api_key
        self.cache = APICache(cache_file='data/tomtom_cache.json') if cache_enabled else None
        self.base_url = "https://api.tomtom.com/routing/1/calculateRoute"
    
    def get_route_with_traffic(self, points, departure_time=None):
        """Trafikli rota al"""
        if departure_time is None:
            departure_time = datetime.now()
        if self.cache:
            cached_result = self.cache.get(points, departure_time)
            if cached_result is not None:
                return cached_result
        locations = ':'.join([f"{lat},{lon}" for lat, lon in points])
        url = f"{self.base_url}/{locations}/json"
        
        params = {
            'key': self.api_key,
            'traffic': 'true',
            'departAt': departure_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'travelMode': 'car',
            'routeType': 'fastest',
            'computeTravelTimeFor': 'all'
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'routes' not in data or len(data['routes']) == 0:
                raise Exception("No route found")
            
            route_data = data['routes'][0]
            summary = route_data['summary']
            
            # Koordinatları topla
            route_coords = []
            for leg in route_data['legs']:
                for point in leg['points']:
                    route_coords.append([point['latitude'], point['longitude']])
            
            # Süre bilgileri
            dist_km = summary['lengthInMeters'] / 1000
            duration_no_traffic = summary.get('noTrafficTravelTimeInSeconds', 
                                             summary['travelTimeInSeconds']) / 60
            duration_with_traffic = summary.get('historicTrafficTravelTimeInSeconds', 
                                                summary['travelTimeInSeconds']) / 60
            traffic_delay = duration_with_traffic - duration_no_traffic
            
            result = {
                'coordinates': route_coords,
                'distance_km': dist_km,
                'duration_no_traffic_min': duration_no_traffic,
                'duration_with_traffic_min': duration_with_traffic,
                'traffic_delay_min': traffic_delay,
                'departure_time': departure_time
            }
            
            # Cache'e kaydet
            if self.cache:
                self.cache.set(points, departure_time, result)
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"TomTom API error: {e}")
            raise
        except KeyError as e:
            print(f"Unexpected API response format: {e}")
            raise
    
    def clear_cache(self):
        """Cache'i temizle"""
        if self.cache:
            self.cache.clear()

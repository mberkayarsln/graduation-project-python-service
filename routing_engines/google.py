"""Google Routes API - Google Maps Platform routing integration (New Routes API)."""
import requests
from routing_engines.cache import APICache


class GoogleRouter:
    """Client for Google Routes API (v2) with traffic-aware routing."""
    
    def __init__(self, api_key, cache_enabled=True):
        self.api_key = api_key
        self.cache = APICache(cache_file='data/google_cache.json') if cache_enabled else None
        self.routes_url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        self.distance_matrix_url = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
    
    def get_route(self, points, departure_time=None, traffic_model="TRAFFIC_AWARE"):
        """
        Get route between points using Google Routes API (v2).
        
        Args:
            points: List of (lat, lon) tuples
            departure_time: Departure time as Unix timestamp (None = now)
            traffic_model: 'TRAFFIC_UNAWARE', 'TRAFFIC_AWARE', or 'TRAFFIC_AWARE_OPTIMAL'
        
        Returns:
            Dict with 'coordinates', 'distance_km', 'duration_min', 
            'duration_in_traffic_min' (if traffic data available)
        """
        if len(points) < 2:
            raise ValueError("Need at least 2 points for routing")
        
        # Check cache
        if self.cache:
            cached_result = self.cache.get(points, departure_time=None)
            if cached_result is not None:
                return cached_result
        
        # Build request body for Routes API v2
        origin = {"location": {"latLng": {"latitude": points[0][0], "longitude": points[0][1]}}}
        destination = {"location": {"latLng": {"latitude": points[-1][0], "longitude": points[-1][1]}}}
        
        # Intermediate waypoints
        intermediates = []
        if len(points) > 2:
            for lat, lon in points[1:-1]:
                intermediates.append({
                    "location": {"latLng": {"latitude": lat, "longitude": lon}}
                })
        
        request_body = {
            "origin": origin,
            "destination": destination,
            "travelMode": "DRIVE",
            "routingPreference": traffic_model,
            "computeAlternativeRoutes": False,
            "polylineEncoding": "ENCODED_POLYLINE",
        }
        
        if intermediates:
            request_body["intermediates"] = intermediates
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs.duration,routes.legs.distanceMeters"
        }
        
        try:
            response = requests.post(self.routes_url, json=request_body, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                raise Exception(f"Google Routes API error: {data['error'].get('message', str(data['error']))}")
            
            if 'routes' not in data or len(data['routes']) == 0:
                raise Exception("No route found")
            
            route = data['routes'][0]
            
            # Decode polyline
            encoded_polyline = route.get('polyline', {}).get('encodedPolyline', '')
            coordinates = self._decode_polyline(encoded_polyline) if encoded_polyline else []
            
            # Parse duration (format: "1234s")
            duration_str = route.get('duration', '0s')
            duration_seconds = int(duration_str.replace('s', ''))
            
            # Distance in meters
            distance_meters = route.get('distanceMeters', 0)
            
            result = {
                'coordinates': coordinates,
                'distance_km': distance_meters / 1000,
                'duration_min': duration_seconds / 60,
            }
            
            if self.cache:
                self.cache.set(points, departure_time=None, data=result)
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"Google Routes API error: {e}")
            raise
    
    def get_distance_matrix(self, origins, destinations, departure_time=None):
        """
        Get distance matrix between origins and destinations using Route Matrix API.
        
        Args:
            origins: List of (lat, lon) tuples
            destinations: List of (lat, lon) tuples
            departure_time: Unix timestamp for traffic-aware times
        
        Returns:
            2D list of distances in meters
        """
        if self.cache:
            cached_result = self.cache.get_matrix(origins, destinations, 'google')
            if cached_result is not None:
                return cached_result
        
        # Build origins/destinations for Route Matrix API
        origin_waypoints = []
        for lat, lon in origins:
            origin_waypoints.append({
                "waypoint": {"location": {"latLng": {"latitude": lat, "longitude": lon}}}
            })
        
        dest_waypoints = []
        for lat, lon in destinations:
            dest_waypoints.append({
                "waypoint": {"location": {"latLng": {"latitude": lat, "longitude": lon}}}
            })
        
        request_body = {
            "origins": origin_waypoints,
            "destinations": dest_waypoints,
            "travelMode": "DRIVE",
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "originIndex,destinationIndex,distanceMeters,duration"
        }
        
        try:
            response = requests.post(self.distance_matrix_url, json=request_body, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                raise Exception(f"Google Route Matrix API error: {data['error'].get('message', '')}")
            
            # Initialize result matrix
            result = [[None] * len(destinations) for _ in range(len(origins))]
            
            # The API returns a flat list of elements
            for element in data:
                origin_idx = element.get('originIndex', 0)
                dest_idx = element.get('destinationIndex', 0)
                distance = element.get('distanceMeters', 0)
                result[origin_idx][dest_idx] = distance
            
            if self.cache:
                self.cache.set_matrix(origins, destinations, 'google', result)
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"Google Route Matrix API error: {e}")
            return None
    
    def _decode_polyline(self, encoded):
        """Decode Google's encoded polyline format to list of [lat, lon]."""
        if not encoded:
            return []
            
        decoded = []
        index = 0
        lat = 0
        lng = 0
        
        while index < len(encoded):
            # Decode latitude
            shift = 0
            result = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            lat += (~(result >> 1) if result & 1 else result >> 1)
            
            # Decode longitude
            shift = 0
            result = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            lng += (~(result >> 1) if result & 1 else result >> 1)
            
            decoded.append([lat / 1e5, lng / 1e5])
        
        return decoded
    
    def clear_cache(self):
        """Clear the route cache."""
        if self.cache:
            self.cache.clear()

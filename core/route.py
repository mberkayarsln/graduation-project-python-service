"""Route model - represents an optimized vehicle route."""


class Route:
    """An optimized route for a cluster with stops and distance/duration info."""
    
    def __init__(self, cluster=None):
        self.cluster = cluster
        self.stops = []
        self.coordinates = []
        self.distance_km = 0.0
        self.duration_min = 0.0
        self.duration_no_traffic_min = 0.0
        self.traffic_delay_min = 0.0
        self.optimized = False
        self.has_traffic_data = False
    
    def set_stops(self, stops):
        """Set the list of stops for this route."""
        self.stops = stops
    
    def set_coordinates(self, coordinates):
        """Set the route polyline coordinates."""
        self.coordinates = coordinates
    
    def add_stop(self, lat, lon):
        """Add a stop to the route."""
        self.stops.append((lat, lon))
    
    def set_distance(self, distance_km):
        """Set the total distance in kilometers."""
        self.distance_km = distance_km
    
    def set_duration(self, duration_min, no_traffic_min=None):
        """Set the duration with optional no-traffic baseline."""
        self.duration_min = duration_min
        if no_traffic_min:
            self.duration_no_traffic_min = no_traffic_min
            self.traffic_delay_min = duration_min - no_traffic_min
            self.has_traffic_data = True
    
    def set_traffic_data(self, traffic_info):
        """Set route data from traffic API response."""
        self.coordinates = traffic_info.get('coordinates', [])
        self.distance_km = traffic_info.get('distance_km', 0)
        self.duration_min = traffic_info.get('duration_with_traffic_min', 0)
        self.duration_no_traffic_min = traffic_info.get('duration_no_traffic_min', 0)
        self.traffic_delay_min = traffic_info.get('traffic_delay_min', 0)
        self.has_traffic_data = True
    
    def mark_optimized(self):
        """Mark this route as optimized."""
        self.optimized = True
    
    def get_stop_count(self):
        """Return number of stops."""
        return len(self.stops)
    
    def get_avg_speed_kmh(self):
        """Calculate average speed in km/h."""
        if self.duration_min > 0:
            return (self.distance_km / self.duration_min) * 60
        return 0
    
    def calculate_stats_from_stops(self):
        """Calculate distance and duration from stops using haversine."""
        if not self.stops or len(self.stops) < 2:
            self.distance_km = 0
            self.duration_min = 0
            return
        
        from utils.geo import haversine
        total_distance = 0
        for i in range(len(self.stops) - 1):
            lat1, lon1 = self.stops[i]
            lat2, lon2 = self.stops[i + 1]
            total_distance += haversine(lat1, lon1, lat2, lon2)
        
        self.distance_km = total_distance / 1000
        avg_speed_kmh = 40
        self.duration_min = (self.distance_km / avg_speed_kmh) * 60
    
    def get_stats(self):
        """Return route statistics."""
        stats = {
            'stops': len(self.stops),
            'distance_km': round(self.distance_km, 2),
            'duration_min': round(self.duration_min, 1),
            'avg_speed_kmh': round(self.get_avg_speed_kmh(), 1),
            'optimized': self.optimized,
            'has_traffic_data': self.has_traffic_data
        }
        
        if self.has_traffic_data:
            stats['duration_no_traffic_min'] = round(self.duration_no_traffic_min, 1)
            stats['traffic_delay_min'] = round(self.traffic_delay_min, 1)
        
        return stats
    
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            'coordinates': self.coordinates if self.coordinates else self.stops,
            'stops': self.stops,
            'distance_km': self.distance_km,
            'duration_min': self.duration_min
        }
    
    def match_employees_to_route(self, employees, safe_stops=None):
        """Match employees to pickup points along the route."""
        if not self.coordinates or len(self.coordinates) < 2:
            return 0
        
        try:
            from shapely.geometry import Point, LineString, MultiPoint
            from shapely.ops import nearest_points
            
            line = LineString(self.coordinates)
            matched_count = 0
            
            valid_route_stops = [s for s in self.stops] if self.stops else []
            
            # Add safe stops near the route
            if safe_stops and len(safe_stops) > 0:
                for s in safe_stops:
                    s_point = Point(s[0], s[1])
                    if line.distance(s_point) < 0.00015:
                        valid_route_stops.append(s)
            
            # Filter stops to only those on the right side of the route
            if valid_route_stops:
                filtered_stops = []
                for s in valid_route_stops:
                    s_point = Point(s[0], s[1])
                    dist = line.project(s_point)
                    
                    delta = 1e-5
                    p1 = line.interpolate(max(0, dist - delta))
                    p2 = line.interpolate(min(line.length, dist + delta))
                    
                    vx = p2.x - p1.x
                    vy = p2.y - p1.y
                    wx = s_point.x - p1.x
                    wy = s_point.y - p1.y
                    
                    cross_product = vx * wy - vy * wx
                    
                    if cross_product >= -1e-10:
                        filtered_stops.append(s)
                
                valid_route_stops = filtered_stops
            
            # Match employees to stops using OSRM distance matrix
            if valid_route_stops:
                active_employees = [e for e in employees if not e.excluded]
                
                if not active_employees:
                    return 0
                    
                from routing_engines.osrm import OSRMRouter
                router = OSRMRouter()
                
                emp_locs = [(e.lat, e.lon) for e in active_employees]
                distances_matrix = router.get_distance_matrix(emp_locs, valid_route_stops, profile='foot')
                
                if distances_matrix:
                    for i, employee in enumerate(active_employees):
                        dists = distances_matrix[i]
                        
                        min_dist_meters = float('inf')
                        best_stop_idx = -1
                        
                        for stop_idx, dist in enumerate(dists):
                            if dist is not None and dist < min_dist_meters:
                                min_dist_meters = dist
                                best_stop_idx = stop_idx
                        
                        if best_stop_idx != -1:
                            best_stop = valid_route_stops[best_stop_idx]
                            employee.set_pickup_point(best_stop[0], best_stop[1], type="stop")
                            matched_count += 1
                    
                    return matched_count
            
            # Geometric fallback
            print("Using geometric fallback for route matching...")
            
            valid_stops_multipoint = None
            if valid_route_stops:
                try:
                    valid_stops_multipoint = MultiPoint([(s[0], s[1]) for s in valid_route_stops])
                except Exception as e:
                    print(f"Error creating MultiPoint from stops: {e}")
            
            for employee in employees:
                if employee.excluded:
                    continue
                
                emp_point = Point(employee.lat, employee.lon)
                
                distance_on_line = line.project(emp_point)
                ideal_point = line.interpolate(distance_on_line)
                final_pickup = (ideal_point.x, ideal_point.y)
                pickup_type = "route"
                
                if valid_stops_multipoint:
                    nearest_stop = nearest_points(emp_point, valid_stops_multipoint)[1]
                    final_pickup = (nearest_stop.x, nearest_stop.y)
                    pickup_type = "stop"
                        
                employee.set_pickup_point(final_pickup[0], final_pickup[1], type=pickup_type)
                matched_count += 1
                
            return matched_count
            
        except ImportError:
            print("Shapely module not found. Skipping route matching.")
            return 0
        except Exception as e:
            print(f"Error matching employees to route: {e}")
            return 0

    def __repr__(self):
        return f"Route(stops={len(self.stops)}, distance={self.distance_km:.1f}km)"
    
    def __str__(self):
        traffic_info = f", +{self.traffic_delay_min:.0f}min traffic" if self.has_traffic_data else ""
        return f"Route: {len(self.stops)} stops, {self.distance_km:.1f}km, {self.duration_min:.0f}min{traffic_info}"

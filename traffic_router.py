import requests
from datetime import datetime


def get_route_with_traffic(points, api_key, departure_time=None):
    if departure_time is None:
        departure_time = datetime.now()
    
    locations = ':'.join([f"{lat},{lon}" for lat, lon in points])
    
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{locations}/json"
    
    params = {
        'key': api_key,
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
            raise Exception("no route found")
        
        route_data = data['routes'][0]

        summary = route_data['summary']
        # print("summary: ", summary)
        
        route_coords = []
        for leg in route_data['legs']:
            for point in leg['points']:
                route_coords.append([point['latitude'], point['longitude']])
        
        dist_km = route_data['summary']['lengthInMeters'] / 1000
        
        duration_no_traffic = summary.get('noTrafficTravelTimeInSeconds', summary['travelTimeInSeconds']) / 60
        duration_with_traffic = summary.get('historicTrafficTravelTimeInSeconds', summary['travelTimeInSeconds']) / 60
        
        traffic_delay = duration_with_traffic - duration_no_traffic
        
        return {
            'coordinates': route_coords,
            'distance_km': dist_km,
            'duration_no_traffic_min': duration_no_traffic,
            'duration_with_traffic_min': duration_with_traffic,
            'traffic_delay_min': traffic_delay,
            'departure_time': departure_time
        }
    
    except requests.exceptions.RequestException as e:
        print(f"TomTom API error: {e}")
        raise
    except KeyError as e:
        print(f"unexpected API response format: {e}")
        raise
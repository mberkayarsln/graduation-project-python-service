import requests
import folium


def get_route(points, profile='driving'):
    coords = ';'.join([f"{lon},{lat}" for lat, lon in points])
    url = f"https://router.project-osrm.org/route/v1/{profile}/{coords}"
    params = {
        'overview': 'full',
        'geometries': 'geojson'
    }
    
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    
    route = data['routes'][0]['geometry']['coordinates']
    latlon = [[c[1], c[0]] for c in route]
    dist_km = data['routes'][0]['distance'] / 1000
    dur_min = data['routes'][0]['duration'] / 60
    
    return latlon, dist_km, dur_min


def draw_route(points, file_path='maps/route_map.html'):
    route, km, mins = get_route(points)
    
    mid_lat = sum(lat for lat, lon in points) / len(points)
    mid_lon = sum(lon for lat, lon in points) / len(points)

    m = folium.Map(location=[mid_lat, mid_lon], zoom_start=12)

    folium.PolyLine(
        route,
        color='#2563eb',
        weight=6,
        opacity=0.85
    ).add_to(m)

    for i, (lat, lon) in enumerate(points):
        folium.Marker(
            location=[lat, lon],
            popup=f"<b>stop {i}</b><br>Lat: {lat:.5f}<br>Lon: {lon:.5f}",
            icon=folium.DivIcon(
                html=f"""
                <div style='
                    font-size: 14px; 
                    color: white; 
                    background: #2563eb; 
                    border-radius: 50%; 
                    width: 24px; 
                    height: 24px; 
                    text-align: center; 
                    line-height: 24px;
                    font-weight: bold;
                '>{i}</div>
                """
            ),
        ).add_to(m)

    folium.Marker(
        location=points[0],
        popup=f"<b>route summary</b><br>Distance: {km:.2f} km<br>Duration: {mins:.1f} min",
        icon=folium.Icon(color='green', icon='info-sign')
    ).add_to(m)

    m.save(file_path)

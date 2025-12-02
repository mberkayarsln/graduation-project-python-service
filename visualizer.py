"""
Harita görselleştirme fonksiyonları
"""
import folium
from config import Config


def create_employees_map(employees, office):
    """
    Tüm çalışanların konumlarını gösteren harita oluşturur
    
    Args:
        employees: [{'lat': float, 'lon': float, 'id': int}, ...]
        office: (lat, lon) tuple
    
    Returns:
        str: Oluşturulan dosya yolu
    """
    if not employees:
        return None
    
    avg_lat = sum(e['lat'] for e in employees) / len(employees)
    avg_lon = sum(e['lon'] for e in employees) / len(employees)
    
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=11)
    
    # Ofis işareti
    folium.Marker(
        office,
        popup="<b>🏢 Ofis - Maslak</b>",
        icon=folium.Icon(color='red', icon='building', prefix='fa')
    ).add_to(m)
    
    # Çalışanları ekle
    for emp in employees:
        emp_id = emp.get('id', 'N/A')
        popup_html = f"""
        <div style='min-width: 150px; font-family: Arial;'>
            <h4 style='color: #2E86AB; margin: 0 0 8px 0;'>👤 Çalışan {emp_id}</h4>
            <table style='width: 100%; font-size: 11px;'>
                <tr><td><b>📍 Konum:</b></td><td>{emp['lat']:.4f}, {emp['lon']:.4f}</td></tr>
            </table>
        </div>
        """
        
        folium.CircleMarker(
            location=[emp['lat'], emp['lon']],
            radius=6,
            color='#2E86AB',
            fill=True,
            fillColor='#A23B72',
            fillOpacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=250)
        ).add_to(m)
    
    filename = Config.MAP_EMPLOYEES
    m.save(filename)
    return filename


def create_cluster_map(employees, centers, office):
    """
    Cluster'lanmış çalışanları gösteren harita oluşturur
    
    Args:
        employees: [{'lat': float, 'lon': float, 'cluster': int, 'id': int}, ...]
        centers: [(lat, lon), ...] cluster merkez noktaları
        office: (lat, lon) tuple
    
    Returns:
        str: Oluşturulan dosya yolu
    """
    if not employees:
        return None
    
    avg_lat = sum(e['lat'] for e in employees) / len(employees)
    avg_lon = sum(e['lon'] for e in employees) / len(employees)
    
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=11)
    
    # Ofis işareti
    folium.Marker(
        office,
        popup="<b>🏢 Ofis - Maslak</b>",
        icon=folium.Icon(color='red', icon='building', prefix='fa')
    ).add_to(m)
    
    colors = Config.CLUSTER_COLORS
    
    # Cluster merkezlerini ekle
    for i, center in enumerate(centers):
        color_hex = colors[i % len(colors)]
        # Folium'un desteklediği renk isimlerine çevir
        color_name = ['red', 'blue', 'green', 'orange', 'purple', 
                      'pink', 'cadetblue', 'lightblue', 'lightgreen', 'darkred'][i % 10]
        
        folium.Marker(
            [center[0], center[1]],
            popup=f"<b>Cluster {i} Merkezi</b>",
            icon=folium.Icon(color=color_name, icon='star', prefix='fa')
        ).add_to(m)
    
    # Çalışanları ekle
    for emp in employees:
        cluster_id = int(emp['cluster'])
        color = colors[cluster_id % len(colors)]
        
        folium.CircleMarker(
            location=[emp['lat'], emp['lon']],
            radius=5,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            popup=f"<b>Çalışan {emp.get('id', 'N/A')}</b><br>Cluster {cluster_id}"
        ).add_to(m)
    
    filename = Config.MAP_CLUSTERS
    m.save(filename)
    return filename


def create_routes_map(routes, office, centers, employees):
    """
    Optimize edilmiş rotaları gösteren harita oluşturur
    
    Args:
        routes: {cluster_id: {
            'coordinates': [...],  # OSRM rota çizgisi
            'stops': [...],        # Gerçek durak noktaları
            'distance_km': float, 
            'duration_min': float
        }, ...}
        office: (lat, lon) tuple
        centers: [(lat, lon), ...] cluster merkez noktaları
        employees: [{'lat': float, 'lon': float, 'cluster': int}, ...]
    
    Returns:
        str: Oluşturulan dosya yolu
    """
    if not employees:
        return None
    
    avg_lat = sum(e['lat'] for e in employees) / len(employees)
    avg_lon = sum(e['lon'] for e in employees) / len(employees)
    
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=11)
    
    # Ofis işareti
    folium.Marker(
        office,
        popup="<b>🏢 Ofis - Maslak</b>",
        icon=folium.Icon(color='red', icon='building', prefix='fa')
    ).add_to(m)
    
    colors = Config.CLUSTER_COLORS
    
    total_distance = 0
    total_duration = 0
    
    for cluster_id, route_data in routes.items():
        coordinates = route_data['coordinates']
        distance = route_data.get('distance_km', 0)
        duration = route_data.get('duration_min', 0)
        color = colors[cluster_id % len(colors)]
        
        total_distance += distance
        total_duration += duration
        
        # Popup içeriği
        stops = route_data.get('stops', [])
        num_stops = len(stops) - 1 if len(stops) > 0 else 0  # Ofisi sayma
        
        popup_html = f"""
        <div style='min-width: 200px; font-family: Arial;'>
            <h4 style='color: {color}; margin: 0 0 10px 0;'>🚌 Cluster {cluster_id}</h4>
            <table style='width: 100%; font-size: 12px;'>
                <tr><td><b>📍 Durak:</b></td><td>{num_stops} çalışan</td></tr>
                <tr><td><b>📏 Mesafe:</b></td><td>{distance:.1f} km</td></tr>
                <tr><td><b>⏱️ Süre:</b></td><td>{duration:.0f} dk</td></tr>
                <tr><td><b>⚡ Ort. Hız:</b></td><td>{(distance / (duration / 60) if duration > 0 else 0):.0f} km/h</td></tr>
            </table>
        </div>
        """
        
        # Rota çizgisi
        folium.PolyLine(
            coordinates,
            color=color,
            weight=4,
            opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)
        
        # Gerçek durak noktalarını işaretle (varsa)
        stops = route_data.get('stops', [])
        if stops:
            # İlk durak (başlangıç - ofis)
            folium.CircleMarker(
                location=stops[0],
                radius=8,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                popup=f"<b>Cluster {cluster_id}</b><br>🏁 Başlangıç (Ofis)"
            ).add_to(m)
            
            # Çalışan durakları
            for i in range(1, len(stops)):
                folium.CircleMarker(
                    location=stops[i],
                    radius=6,
                    color=color,
                    fill=True,
                    fillColor='white',
                    fillOpacity=0.9,
                    weight=2,
                    popup=f"<b>Cluster {cluster_id}</b><br>🚏 Durak {i}"
                ).add_to(m)
    
    # Özet paneli
    legend_html = f'''
    <div style="position: fixed; bottom: 50px; right: 50px; background-color: white; 
                padding: 15px; border: 2px solid grey; border-radius: 5px; z-index: 9999; font-family: Arial;">
        <h4 style="margin-top: 0;">📊 Özet</h4>
        <p style="margin: 5px 0;"><b>Aktif Rotalar:</b> {len(routes)}</p>
    '''
    
    if total_distance > 0:
        legend_html += f'''
        <hr>
        <p style="margin: 5px 0;"><b>📏 Toplam Mesafe:</b> {total_distance:.1f} km</p>
        <p style="margin: 5px 0;"><b>⏱️ Toplam Süre:</b> {total_duration:.0f} dk</p>
        <p style="margin: 5px 0;"><b>⚡ Ort. Hız:</b> {(total_distance / (total_duration / 60) if total_duration > 0 else 0):.0f} km/s</p>
        '''
    
    legend_html += '</div>'
    m.get_root().html.add_child(folium.Element(legend_html))
    
    filename = Config.MAP_ROUTES
    m.save(filename)
    return filename

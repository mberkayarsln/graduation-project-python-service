"""Visualization Service"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import folium


class VisualizationService:
    """Harita görselleştirme"""
    
    def __init__(self, config):
        self.config = config
        self.office_location = config.OFFICE_LOCATION
    
    def create_employees_map(self, employees):
        """Çalışan haritası"""
        filename = "maps/employees.html"
        
        if not employees:
            return filename
        
        # Ortalama konum
        avg_lat = sum(emp.lat for emp in employees) / len(employees)
        avg_lon = sum(emp.lon for emp in employees) / len(employees)
        
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)
        
        # Ofis
        folium.Marker(
            location=self.office_location,
            popup="<b>Ofis</b>",
            icon=folium.Icon(color='red', icon='home', prefix='fa')
        ).add_to(m)
        
        # Çalışanlar
        for emp in employees:
            folium.CircleMarker(
                location=[emp.lat, emp.lon],
                radius=4,
                color='#2563eb',
                fill=True,
                fill_opacity=0.7,
                popup=f"<b>ID:</b> {emp.id}"
            ).add_to(m)
        
        m.save(filename)
        return filename
    
    def create_clusters_map(self, clusters):
        """Cluster haritası"""
        filename = "maps/clusters.html"
        
        # Tüm çalışanları topla
        all_employees = []
        for cluster in clusters:
            all_employees.extend(cluster.employees)
        
        if not all_employees:
            return filename
        
        # Ortalama konum
        avg_lat = sum(emp.lat for emp in all_employees) / len(all_employees)
        avg_lon = sum(emp.lon for emp in all_employees) / len(all_employees)
        
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)
        
        # Renkler
        colors = self.config.CLUSTER_COLORS
        
        # Ofis
        folium.Marker(
            location=self.office_location,
            popup="<b>Ofis</b>",
            icon=folium.Icon(color='red', icon='home', prefix='fa')
        ).add_to(m)
        
        # Cluster merkezleri ve kapsama daireleri
        radius_km = self.config.MAX_DISTANCE_FROM_CENTER / 1000  # metre → km
        
        for cluster in clusters:
            color = colors[cluster.id % len(colors)]
            
            # Kapsama dairesi (yarıçap)
            folium.Circle(
                location=cluster.center,
                radius=self.config.MAX_DISTANCE_FROM_CENTER,  # metre
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.1,
                weight=2,
                opacity=0.5,
                popup=f"<b>Cluster {cluster.id}</b><br>"
                      f"Yarıçap: {radius_km:.1f} km"
            ).add_to(m)
            
            # Merkez noktası
            folium.Marker(
                location=cluster.center,
                popup=f"<b>Cluster {cluster.id}</b><br>"
                      f"Merkez<br>"
                      f"Kapsama: {radius_km:.1f} km",
                icon=folium.Icon(color='black', icon='star', prefix='fa')
            ).add_to(m)
        
        # Çalışanlar
        for emp in all_employees:
            cluster_id = emp.cluster_id
            color = colors[cluster_id % len(colors)]
            
            folium.CircleMarker(
                location=[emp.lat, emp.lon],
                radius=5,
                color=color,
                fill=True,
                fill_opacity=0.7,
                popup=f"<b>ID:</b> {emp.id}<br><b>Cluster:</b> {cluster_id}"
            ).add_to(m)
        
        m.save(filename)
        return filename
    
    def create_routes_map(self, clusters):
        """Rota haritası"""
        filename = "maps/optimized_routes.html"
        
        # Routes dict oluştur
        routes_dict = {}
        for cluster in clusters:
            if cluster.route:
                routes_dict[cluster.id] = cluster.route
        
        if not routes_dict:
            return filename
        
        m = folium.Map(location=self.office_location, zoom_start=11)
        
        # Renkler
        colors = self.config.CLUSTER_COLORS
        
        # Ofis
        folium.Marker(
            location=self.office_location,
            popup="<b>Ofis</b>",
            icon=folium.Icon(color='red', icon='home', prefix='fa')
        ).add_to(m)
        
        # Her cluster için rota çiz
        for cluster_id, route in routes_dict.items():
            cluster = clusters[int(cluster_id)]
            color = colors[int(cluster_id) % len(colors)]
            
            # Rota çizgisi (araç rotası)
            if route.coordinates:
                folium.PolyLine(
                    route.coordinates,
                    color=color,
                    weight=4,
                    opacity=0.7,
                    popup=f"<b>Araç Rotası - Cluster {cluster_id}</b>"
                ).add_to(m)
            
            # DURAK SİSTEMİ: Duraklar ve yürüme çizgileri
            if cluster.has_stops():
                # Rota sırasına göre durak mapping oluştur
                stop_order_map = {}
                if route and route.stops:
                    # Ofis hariç durakları al (son nokta ofis)
                    route_stops = route.stops[:-1] if len(route.stops) > 1 else route.stops
                    for order, stop in enumerate(route_stops):
                        stop_order_map[stop] = order + 1
                
                # Durak noktaları
                for i, (stop_lat, stop_lon) in enumerate(cluster.stops):
                    load = cluster.stop_loads[i] if i < len(cluster.stop_loads) else 0
                    stop_tuple = (stop_lat, stop_lon)
                    display_number = stop_order_map.get(stop_tuple, i+1)
                    
                    folium.Marker(
                        location=[stop_lat, stop_lon],
                        popup=f"<b>Durak {display_number}</b><br>"
                              f"Cluster {cluster_id}<br>"
                              f"{load} çalışan",
                        icon=folium.DivIcon(html=f"""
                            <div style="background: {color}; color: white; 
                                 padding: 3px 8px; border-radius: 5px; 
                                 font-weight: bold; font-size: 14px;
                                 border: 2px solid white;
                                 box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                                {display_number}
                            </div>
                        """)
                    ).add_to(m)
                
                # Çalışan → Durak yürüme çizgileri
                for employee in cluster.get_active_employees():
                    stop_index, stop_location = cluster.get_employee_stop(employee)
                    
                    if stop_location:
                        folium.PolyLine(
                            [employee.get_location(), stop_location],
                            color=color,
                            weight=1,
                            opacity=0.3,
                            dash_array='5, 5',
                            popup=f"Yürüme: {employee.id} → Durak {stop_index+1}"
                        ).add_to(m)
                        
                        # Çalışan noktası (küçük)
                        folium.CircleMarker(
                            location=employee.get_location(),
                            radius=3,
                            color=color,
                            fill=True,
                            fill_opacity=0.5,
                            popup=f"<b>ID:</b> {employee.id}<br>"
                                  f"<b>Durak:</b> {stop_index+1}"
                        ).add_to(m)
            else:
                # ESKİ SİSTEM: Direkt çalışan konumları
                for i, stop in enumerate(route.stops):
                    folium.CircleMarker(
                        location=stop,
                        radius=6,
                        color=color,
                        fill=True,
                        fill_opacity=0.9,
                        popup=f"<b>Cluster {cluster_id}</b><br>Nokta {i}"
                    ).add_to(m)
            
            # Cluster bilgisi
            center = cluster.center
            n_stops = len(cluster.stops) if cluster.has_stops() else len(route.stops)
            
            folium.Marker(
                location=center,
                popup=f"<b>Cluster {cluster_id}</b><br>"
                      f"{n_stops} durak<br>"
                      f"{route.distance_km:.1f} km<br>"
                      f"{route.duration_min:.0f} dk",
                icon=folium.DivIcon(html=f"""
                    <div style="background: {color}; color: white; 
                         padding: 5px; border-radius: 50%; 
                         width: 30px; height: 30px; text-align: center;
                         line-height: 30px; font-weight: bold;
                         border: 3px solid white;
                         box-shadow: 0 3px 6px rgba(0,0,0,0.4);">
                        {cluster_id}
                    </div>
                """)
            ).add_to(m)
        
        m.save(filename)
        return filename
    
    def create_cluster_detail_map(self, cluster):
        """Detaylı cluster haritası"""
        import os
        
        # Klasör oluştur
        os.makedirs("maps/detailed", exist_ok=True)
        
        filename = f"maps/detailed/cluster_{cluster.id}_detail.html"
        
        # Cluster merkezi odaklı harita
        m = folium.Map(location=cluster.center, zoom_start=14)
        
        color = self.config.CLUSTER_COLORS[cluster.id % len(self.config.CLUSTER_COLORS)]
        
        # Ofis
        folium.Marker(
            location=self.office_location,
            popup="<b>Ofis</b>",
            icon=folium.Icon(color='red', icon='home', prefix='fa')
        ).add_to(m)
        
        # Kapsama dairesi
        radius_km = self.config.MAX_DISTANCE_FROM_CENTER / 1000
        folium.Circle(
            location=cluster.center,
            radius=self.config.MAX_DISTANCE_FROM_CENTER,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.15,
            weight=2,
            opacity=0.6,
            popup=f"Kapsama Alanı<br>{radius_km:.1f} km"
        ).add_to(m)
        
        # Cluster merkezi
        folium.Marker(
            location=cluster.center,
            popup=f"<b>Cluster {cluster.id} Merkezi</b>",
            icon=folium.Icon(color='black', icon='star', prefix='fa')
        ).add_to(m)
        
        # Duraklar
        if cluster.has_stops():
            # Rota sırasına göre durak mapping
            stop_order_map = {}
            if cluster.route and cluster.route.stops:
                route_stops = cluster.route.stops[:-1] if len(cluster.route.stops) > 1 else cluster.route.stops
                for order, stop in enumerate(route_stops):
                    stop_order_map[stop] = order + 1
            
            for i, (stop_lat, stop_lon) in enumerate(cluster.stops):
                load = cluster.stop_loads[i] if i < len(cluster.stop_loads) else 0
                stop_tuple = (stop_lat, stop_lon)
                display_number = stop_order_map.get(stop_tuple, i+1)
                
                folium.Marker(
                    location=[stop_lat, stop_lon],
                    popup=f"<b>Durak {display_number}</b><br>"
                          f"{load} çalışan<br>"
                          f"Cluster {cluster.id}",
                    icon=folium.DivIcon(html=f"""
                        <div style="background: {color}; color: white; 
                             padding: 5px 10px; border-radius: 8px; 
                             font-weight: bold; font-size: 16px;
                             border: 3px solid white;
                             box-shadow: 0 2px 8px rgba(0,0,0,0.4);">
                            {display_number}
                        </div>
                    """)
                ).add_to(m)
        
        # Çalışanlar (aktif + hariç tutulan)
        for employee in cluster.employees:
            if employee.excluded:
                # Hariç tutulan çalışanlar (gri)
                folium.CircleMarker(
                    location=employee.get_location(),
                    radius=4,
                    color='gray',
                    fill=True,
                    fillColor='lightgray',
                    fillOpacity=0.5,
                    popup=f"<b>ID:</b> {employee.id}<br>"
                          f"<b>Durum:</b> Hariç tutuldu<br>"
                          f"<b>Sebep:</b> {employee.exclusion_reason}",
                    weight=1
                ).add_to(m)
            else:
                # Aktif çalışanlar
                stop_index, stop_location = cluster.get_employee_stop(employee)
                
                # Yürüme çizgisi (çalışan → durak)
                if stop_location and cluster.has_stops():
                    folium.PolyLine(
                        [employee.get_location(), stop_location],
                        color=color,
                        weight=1.5,
                        opacity=0.4,
                        dash_array='5, 5',
                        popup=f"Yürüme: {employee.id} → Durak {stop_index+1}"
                    ).add_to(m)
                
                folium.CircleMarker(
                    location=employee.get_location(),
                    radius=5,
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.7,
                    popup=f"<b>ID:</b> {employee.id}<br>"
                          f"<b>Durak:</b> {stop_index+1 if stop_index is not None else 'N/A'}",
                    weight=2
                ).add_to(m)
        
        # Rota çizgisi (varsa)
        if cluster.route and cluster.route.coordinates:
                folium.PolyLine(
                    cluster.route.coordinates,
                    color=color,
                    weight=5,
                    opacity=0.8,
                    popup=f"<b>Araç Rotası</b><br>"
                          f"{cluster.route.distance_km:.1f} km<br>"
                          f"{cluster.route.duration_min:.0f} dk"
            ).add_to(m)        # Bilgi kutusu
        info_html = f"""
        <div style="position: fixed; 
                    top: 10px; right: 10px; 
                    width: 250px; 
                    background: white; 
                    border: 2px solid {color};
                    border-radius: 10px;
                    padding: 15px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    z-index: 9999;">
            <h3 style="margin: 0 0 10px 0; color: {color};">
                Cluster {cluster.id}
            </h3>
            <p style="margin: 5px 0;">
                <b>Toplam Çalışan:</b> {len(cluster.employees)}<br>
                <b>Aktif:</b> {cluster.get_employee_count(include_excluded=False)}<br>
                <b>Hariç:</b> {cluster.get_employee_count(include_excluded=True) - cluster.get_employee_count(include_excluded=False)}<br>
                <b>Durak Sayısı:</b> {len(cluster.stops) if cluster.has_stops() else 0}<br>
        """
        
        if cluster.route:
            info_html += f"""
                <b>Rota Mesafesi:</b> {cluster.route.distance_km:.1f} km<br>
                <b>Süre:</b> {cluster.route.duration_min:.0f} dk<br>
            """
        
        info_html += """
            </p>
        </div>
        """
        
        m.get_root().html.add_child(folium.Element(info_html))
        
        m.save(filename)
        return filename
    
    def create_all_maps(self, clusters):
        """Tüm haritalar"""
        files = []
        
        # 1. Çalışan haritası
        all_employees = []
        for cluster in clusters:
            all_employees.extend(cluster.employees)
        
        files.append(self.create_employees_map(all_employees))
        
        # 2. Cluster haritası
        files.append(self.create_clusters_map(clusters))
        
        # 3. Rotalar haritası
        files.append(self.create_routes_map(clusters))
        
        # 4. Her cluster için detaylı harita
        for cluster in clusters:
            detail_file = self.create_cluster_detail_map(cluster)
            files.append(detail_file)
        
        return files

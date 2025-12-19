import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import folium


class VisualizationService:    
    def __init__(self, config):
        self.config = config
        self.office_location = config.OFFICE_LOCATION
        self.cluster_colors = {}
    
    def _get_cluster_color(self, cluster_id):
        if cluster_id not in self.cluster_colors:
            import random
            import hashlib
            
            seed_str = f"cluster_{cluster_id}_color_seed"
            hash_value = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
            random.seed(hash_value)
            
            golden_ratio = 0.618033988749895
            hue = int((cluster_id * golden_ratio * 360) % 360)
            
            hue = (hue + random.randint(-30, 30)) % 360
            
            saturation = random.randint(65, 95)
            lightness = random.randint(40, 70)
            
            self.cluster_colors[cluster_id] = f'hsl({hue}, {saturation}%, {lightness}%)'
        return self.cluster_colors[cluster_id]
    
    def create_employees_map(self, employees):
        filename = "maps/employees.html"
        
        if not employees:
            return filename
        
        avg_lat = sum(emp.lat for emp in employees) / len(employees)
        avg_lon = sum(emp.lon for emp in employees) / len(employees)
        
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)
        
        folium.Marker(
            location=self.office_location,
            popup="<b>Ofis</b>",
            icon=folium.Icon(color='red', icon='home', prefix='fa')
        ).add_to(m)
        
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
        filename = "maps/clusters.html"
        
        all_employees = []
        for cluster in clusters:
            all_employees.extend(cluster.employees)
        
        if not all_employees:
            return filename
        
        avg_lat = sum(emp.lat for emp in all_employees) / len(all_employees)
        avg_lon = sum(emp.lon for emp in all_employees) / len(all_employees)
        
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)
        
        folium.Marker(
            location=self.office_location,
            popup="<b>Ofis</b>",
            icon=folium.Icon(color='red', icon='home', prefix='fa')
        ).add_to(m)
        
        """ radius_km = self.config.MAX_DISTANCE_FROM_CENTER / 1000 
        
        for cluster in clusters:
            color = self._get_cluster_color(cluster.id)
            folium.Circle(
                location=cluster.center,
                radius=self.config.MAX_DISTANCE_FROM_CENTER, 
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.1,
                weight=2,
                opacity=0.5,
                popup=f"<b>Cluster {cluster.id}</b><br>"
            ).add_to(m) 
        """
            
        folium.Marker(
                location=cluster.center,
                popup=f"<b>Cluster {cluster.id}</b><br>"
                      f"Merkez<br>",
                icon=folium.Icon(color='black', icon='star', prefix='fa')
            ).add_to(m)
        
        for emp in all_employees:
            cluster_id = emp.cluster_id
            color = self._get_cluster_color(cluster_id)
            
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
        filename = "maps/optimized_routes.html"
        
        routes_dict = {}
        for cluster in clusters:
            if cluster.route:
                routes_dict[cluster.id] = cluster.route
        
        if not routes_dict:
            return filename
        
        m = folium.Map(location=self.office_location, zoom_start=11)
        
        folium.Marker(
            location=self.office_location,
            popup="<b>Ofis</b>",
            icon=folium.Icon(color='red', icon='home', prefix='fa')
        ).add_to(m)
        
        for cluster_id, route in routes_dict.items():
            cluster = clusters[int(cluster_id)]
            color = self._get_cluster_color(int(cluster_id))
            
            if route.coordinates:
                folium.PolyLine(
                    route.coordinates,
                    color=color,
                    weight=4,
                    opacity=0.7,
                    popup=f"<b>Araç Rotası - Cluster {cluster_id}</b>"
                ).add_to(m)
            
            if cluster.has_stops():
                stop_order_map = {}
                if route and route.stops:
                    route_stops = route.stops[:-1] if len(route.stops) > 1 else route.stops
                    for order, stop in enumerate(route_stops):
                        stop_order_map[stop] = order + 1
                
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
                
                for employee in cluster.get_active_employees():
                    stop_index, stop_location = cluster.get_employee_stop(employee)
                    
                    target_location = employee.pickup_point if hasattr(employee, 'pickup_point') and employee.pickup_point else stop_location
                    
                    if target_location:
                        walk_distance = employee.distance_to(target_location[0], target_location[1])
                        
                        folium.PolyLine(
                            [employee.get_location(), target_location],
                            color=color,
                            weight=1.5,
                            opacity=0.6,
                            dash_array='5, 5',
                            popup=f"Yürüme: {employee.id} → Rota"
                        ).add_to(m)
                        
                        folium.CircleMarker(
                            location=employee.get_location(),
                            radius=3,
                            color=color,
                            fill=True,
                            fill_opacity=0.5,
                            popup=f"<b>ID:</b> {employee.id}<br>"
                        ).add_to(m)
                        
                        # Only indicate if it is a safe stop found in OSM
                        is_safe_stop = hasattr(employee, 'pickup_type') and employee.pickup_type == 'stop'
                        
                        if target_location and is_safe_stop:
                            folium.Marker(
                                location=target_location,
                                icon=folium.Icon(color='green', icon='bus', prefix='fa', icon_size=(24,24)),
                                popup="Taşıt Durağı (Güvenli Nokta)"
                            ).add_to(m)
            else:
                for i, stop in enumerate(route.stops):
                    folium.CircleMarker(
                        location=stop,
                        radius=6,
                        color=color,
                        fill=True,
                        fill_opacity=0.9,
                        popup=f"<b>Cluster {cluster_id}</b><br>Nokta {i}"
                    ).add_to(m)
            
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
        import os
        
        os.makedirs("maps/detailed", exist_ok=True)
        
        filename = f"maps/detailed/cluster_{cluster.id}_detail.html"
        m = folium.Map(location=cluster.center, zoom_start=14)
        
        color = self._get_cluster_color(cluster.id)
        
        folium.Marker(
            location=self.office_location,
            popup="<b>Ofis</b>",
            icon=folium.Icon(color='red', icon='home', prefix='fa')
        ).add_to(m)
        
        """ radius_km = self.config.MAX_DISTANCE_FROM_CENTER / 1000
        folium.Circle(
            location=cluster.center,
            radius=self.config.MAX_DISTANCE_FROM_CENTER,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.15,
            weight=2,
            opacity=0.6,
        ).add_to(m) """
        
        folium.Marker(
            location=cluster.center,
            popup=f"<b>Cluster {cluster.id} Merkezi</b>",
            icon=folium.Icon(color='black', icon='star', prefix='fa')
        ).add_to(m)
        
        if cluster.has_stops():
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
        
        for employee in cluster.employees:
            if employee.excluded:
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
                stop_index, stop_location = cluster.get_employee_stop(employee)
                
                target_location = employee.pickup_point if hasattr(employee, 'pickup_point') and employee.pickup_point else stop_location
                
                if target_location:
                    walk_distance = employee.distance_to(target_location[0], target_location[1])
                    
                    folium.PolyLine(
                        [employee.get_location(), target_location],
                        color=color,
                        weight=1.5,
                        opacity=0.6,
                        dash_array='5, 5',
                        popup=f"Pick-up: {employee.id}"
                    ).add_to(m)
                    
                    midpoint = [
                        (employee.lat + target_location[0]) / 2,
                        (employee.lon + target_location[1]) / 2
                    ]
                    
                    folium.Marker(
                        location=midpoint,
                        icon=folium.DivIcon(icon_size=(100, 20), icon_anchor=(50, 10), html=f"""
                            <div style="font-size: 10px; color: {color}; font-weight: bold; 
                                 background: rgba(255, 255, 255, 0.7); padding: 0 2px; border-radius: 3px;
                                 text-align: center; width: auto; display: inline-block;">
                                {walk_distance:.0f}m
                            </div>
                        """)
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
                
                # Add a distinct marker for the safe pickup point itself (if it's different from a regular stop)
                # Only indicate if it is a safe stop found in OSM
                is_safe_stop = hasattr(employee, 'pickup_type') and employee.pickup_type == 'stop'
                
                if is_safe_stop:
                    folium.Marker(
                        location=target_location,
                        icon=folium.Icon(color='green', icon='bus', prefix='fa', icon_size=(24,24)),
                        popup="Taşıt Durağı (Güvenli Nokta)"
                    ).add_to(m)
        
        if cluster.route and cluster.route.coordinates:
                folium.PolyLine(
                    cluster.route.coordinates,
                    color=color,
                    weight=5,
                    opacity=0.8,
                    popup=f"<b>Araç Rotası</b><br>"
                          f"{cluster.route.distance_km:.1f} km<br>"
                          f"{cluster.route.duration_min:.0f} dk"
            ).add_to(m)
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
        
        # m.get_root().html.add_child(folium.Element(info_html))
        
        m.save(filename)
        return filename
    
    def create_all_maps(self, clusters):
        files = []
        all_employees = []
        for cluster in clusters:
            all_employees.extend(cluster.employees)
        
        files.append(self.create_employees_map(all_employees))
        files.append(self.create_clusters_map(clusters))
        files.append(self.create_routes_map(clusters))
        
        for cluster in clusters:
            detail_file = self.create_cluster_detail_map(cluster)
            files.append(detail_file)
        
        return files

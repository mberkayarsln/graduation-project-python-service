"""
VisualizationService - Harita oluşturma
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import folium


class VisualizationService:
    """Harita ve görselleştirme yönetimi"""
    
    def __init__(self, config):
        """
        Args:
            config: Config objesi
        """
        self.config = config
        self.office_location = config.OFFICE_LOCATION
    
    def create_employees_map(self, employees):
        """
        Çalışan konumları haritası
        
        Args:
            employees: Employee listesi
        
        Returns:
            str: Dosya adı
        """
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
        """
        Cluster haritası
        
        Args:
            clusters: Cluster listesi
        
        Returns:
            str: Dosya adı
        """
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
        
        # Cluster merkezleri
        for cluster in clusters:
            folium.Marker(
                location=cluster.center,
                popup=f"<b>Cluster {cluster.id}</b>",
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
        """
        Rotalar haritası
        
        Args:
            clusters: Cluster listesi (route bilgisi ile)
        
        Returns:
            str: Dosya adı
        """
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
            color = colors[int(cluster_id) % len(colors)]
            
            # Rota çizgisi
            if route.coordinates:
                folium.PolyLine(
                    route.coordinates,
                    color=color,
                    weight=4,
                    opacity=0.7
                ).add_to(m)
            
            # Duraklar
            for i, stop in enumerate(route.stops):
                folium.CircleMarker(
                    location=stop,
                    radius=6,
                    color=color,
                    fill=True,
                    fill_opacity=0.9,
                    popup=f"<b>Cluster {cluster_id}</b><br>Durak {i}"
                ).add_to(m)
            
            # Rota bilgisi
            center = clusters[int(cluster_id)].center
            folium.Marker(
                location=center,
                popup=f"<b>Cluster {cluster_id}</b><br>"
                      f"Mesafe: {route.distance_km:.1f} km<br>"
                      f"Süre: {route.duration_min:.0f} dk",
                icon=folium.DivIcon(html=f"""
                    <div style="background: {color}; color: white; 
                         padding: 5px; border-radius: 50%; 
                         width: 30px; height: 30px; text-align: center;
                         line-height: 30px; font-weight: bold;">
                        {cluster_id}
                    </div>
                """)
            ).add_to(m)
        
        m.save(filename)
        return filename
    
    def create_all_maps(self, clusters):
        """
        Tüm haritaları oluştur
        
        Args:
            clusters: Cluster listesi
        
        Returns:
            list: Dosya adları
        """
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
        
        return files

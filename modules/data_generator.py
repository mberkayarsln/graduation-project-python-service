"""
DataGenerator - Çalışan konumu oluşturucu (OOP)
"""
import numpy as np
import pandas as pd
from shapely.geometry import Point
import folium
from pyrosm import OSM


class DataGenerator:
    """İstanbul'da OSM verisi kullanarak rastgele konum oluşturur"""
    
    def __init__(self, osm_file="data/istanbul-center.osm.pbf"):
        """
        Args:
            osm_file: OSM PBF dosya yolu
        """
        self.osm_file = osm_file
        self._osm = None
        self._urban_area = None
        self._bounds = None
    
    def _load_osm_data(self):
        """OSM verisini yükle (lazy loading)"""
        if self._osm is None:
            self._osm = OSM(self.osm_file)
            
            landuse = self._osm.get_data_by_custom_criteria(
                custom_filter={"landuse": ["residential"]},
                filter_type="keep",
                keep_nodes=False,
                keep_ways=True,
                keep_relations=True
            )
            
            self._urban_area = landuse.unary_union
            self._bounds = landuse.total_bounds
    
    def generate(self, n=100, seed=42):
        """
        Rastgele konum oluştur
        
        Args:
            n: Oluşturulacak nokta sayısı
            seed: Random seed
        
        Returns:
            pandas.DataFrame: id, lat, lon kolonları
        """
        self._load_osm_data()
        
        rng = np.random.default_rng(seed)
        points = []
        attempts = 0
        max_attempts = n * 30
        
        while len(points) < n and attempts < max_attempts:
            lon = rng.uniform(self._bounds[0], self._bounds[2])
            lat = rng.uniform(self._bounds[1], self._bounds[3])
            p = Point(lon, lat)
            
            if self._urban_area.contains(p):
                points.append((lat, lon))
            
            attempts += 1
        
        df = pd.DataFrame({
            "id": np.arange(1, len(points) + 1),
            "lat": [p[0] for p in points],
            "lon": [p[1] for p in points],
        })
        
        return df
    
    def generate_and_save_map(self, n=100, seed=42, output_file="maps/generated_points.html"):
        """
        Konum oluştur ve haritaya kaydet
        
        Args:
            n: Nokta sayısı
            seed: Random seed
            output_file: Çıktı dosyası
        
        Returns:
            tuple: (DataFrame, dosya_adı)
        """
        df = self.generate(n, seed)
        
        # Harita oluştur
        m = folium.Map(
            location=[df['lat'].mean(), df['lon'].mean()], 
            zoom_start=12
        )
        
        for _, row in df.iterrows():
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=3,
                color="#2563eb",
                fill=True,
                fill_opacity=0.9,
                popup=f"Employee {row['id']}"
            ).add_to(m)
        
        m.save(output_file)
        
        return df, output_file

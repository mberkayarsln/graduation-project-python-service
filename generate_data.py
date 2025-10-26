import numpy as np
import pandas as pd
from shapely.geometry import Point
import folium
from pyrosm import OSM


def generate_points(n=100, seed=42, show_map=True):
    rng = np.random.default_rng(seed)

    osm = OSM("data/istanbul-center.osm.pbf")

    landuse = osm.get_data_by_custom_criteria(
        custom_filter={
            "landuse": ["residential", "commercial"]
        },
        filter_type="keep",
        keep_nodes=False,
        keep_ways=True,
        keep_relations=True
    )

    urban_area = landuse.unary_union

    bounds = landuse.total_bounds
    points = []
    attempts = 0
    max_attempts = n * 30
    
    while len(points) < n and attempts < max_attempts:
        lon = rng.uniform(bounds[0], bounds[2])
        lat = rng.uniform(bounds[1], bounds[3])
        p = Point(lon, lat)
        if urban_area.contains(p):
            points.append((lat, lon))
        attempts += 1

    df = pd.DataFrame({
        "id": np.arange(1, len(points) + 1),
        "lat": [p[0] for p in points],
        "lon": [p[1] for p in points],
    })

    if show_map:
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
        m.save("maps/generated_points.html")

    return df
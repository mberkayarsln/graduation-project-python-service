from generate_data import generate_points
from kmeans_cluster import cluster_points
from optimize_route import optimize_tsp
from draw_route import draw_route, get_route
from traffic_router import get_route_with_traffic
import folium
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()


def main():
    
    OFFICE_LOCATION = (41.1097, 29.0204)
    NUM_EMPLOYEES = 100
    NUM_CLUSTERS = 10
    
    USE_TRAFFIC = True
    TOMTOM_API_KEY = os.getenv('TOMTOM_API_KEY')
    tomorrow_7am = datetime.now().replace(hour=7, minute=0, second=0, microsecond=0)
    if datetime.now().hour >= 7:
        tomorrow_7am += timedelta(days=1)
    DEPARTURE_TIME = tomorrow_7am
    
    if USE_TRAFFIC and not TOMTOM_API_KEY:
        print("warning: TOMTOM_API_KEY not found in .env file")
        print("traffic analysis will be disabled")
        USE_TRAFFIC = False
    
    print("starting route optimization system...")
    print(f"traffic analysis: {'enabled ✓' if USE_TRAFFIC else 'disabled ✗'}")
    if USE_TRAFFIC:
        print(f"departure time: {DEPARTURE_TIME.strftime('%Y-%m-%d %H:%M')}")
    
    print(f"\ngenerating {NUM_EMPLOYEES} random employee locations...")
    df = generate_points(n=NUM_EMPLOYEES, seed=42, show_map=True)
    print(f"generated {len(df)} points")
    print(f"map saved to: maps/generated_points.html")
    
    print(f"\nclustering employees into {NUM_CLUSTERS} groups...")
    df, centers = cluster_points(df, k=NUM_CLUSTERS, random_state=42)
    print(f"created {NUM_CLUSTERS} clusters")
    
    print(f"\noptimizing routes for each cluster...")
    all_routes = []
    
    for cluster_id in range(NUM_CLUSTERS):
        cluster_df = df[df['cluster'] == cluster_id]
        points = list(zip(cluster_df['lat'], cluster_df['lon']))
        
        if len(points) > 0:
            print(f"  cluster {cluster_id}: {len(points)} employees", end=" → ")
            
            optimized_route = optimize_tsp(
                points, 
                office=OFFICE_LOCATION,
                use_traffic=USE_TRAFFIC,
                api_key=TOMTOM_API_KEY if USE_TRAFFIC else None,
                departure_time=DEPARTURE_TIME if USE_TRAFFIC else None,
                k_nearest=5
            )
            
            all_routes.append((cluster_id, optimized_route))
            print(f"{len(optimized_route)} stops")
    
    print(f"\ncreating visualization...")
    
    m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=11)
    
    colors = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', 
              '#ec4899', '#14b8a6', '#06b6d4', '#84cc16', '#f97316']
    
    total_distance = 0
    total_duration_no_traffic = 0
    total_duration_with_traffic = 0
    total_traffic_delay = 0
    
    for cluster_id, route in all_routes:
        color = colors[cluster_id % len(colors)]
        
        try:
            if USE_TRAFFIC:
                result = get_route_with_traffic(route, TOMTOM_API_KEY, DEPARTURE_TIME)
                route_coords = result['coordinates']
                km = result['distance_km']
                mins_no_traffic = result['duration_no_traffic_min']
                mins_with_traffic = result['duration_with_traffic_min']
                traffic_delay = result['traffic_delay_min']
                
                total_distance += km
                total_duration_no_traffic += mins_no_traffic
                total_duration_with_traffic += mins_with_traffic
                total_traffic_delay += traffic_delay
                
                popup_text = f"""
                <b>cluster {cluster_id}</b><br>
                distance: {km:.1f} km<br>
                <hr>
                <span style='color: green'>no traffic: {mins_no_traffic:.0f} min</span><br>
                <span style='color: orange'>with traffic: {mins_with_traffic:.0f} min</span><br>
                <span style='color: red'>delay: +{traffic_delay:.0f} min</span>
                """
            else:
                route_coords, km, mins = get_route(route)
                total_distance += km
                total_duration_no_traffic += mins
                
                popup_text = f"<b>cluster {cluster_id}</b><br>{km:.1f} km<br>{mins:.0f} min"
            
            folium.PolyLine(
                route_coords,
                color=color,
                weight=4,
                opacity=0.7,
                popup=folium.Popup(popup_text, max_width=250)
            ).add_to(m)
            
        except Exception as e:
            print(f"  could not get detailed route for cluster {cluster_id}: {e}")
            folium.PolyLine(
                route,
                color=color,
                weight=3,
                opacity=0.5,
                popup=f"cluster {cluster_id} (simple)"
            ).add_to(m)
        
        for i, (lat, lon) in enumerate(route[:-1]):
            folium.CircleMarker(
                location=[lat, lon],
                radius=4,
                color=color,
                fill=True,
                fill_opacity=0.8,
                popup=f"<b>cluster {cluster_id}</b><br>stop {i+1}"
            ).add_to(m)
    
    folium.Marker(
        location=OFFICE_LOCATION,
        popup="<b>office (destination)</b>",
        icon=folium.Icon(color='red', icon='building', prefix='fa')
    ).add_to(m)
    
    m.save("maps/all_clusters_to_office.html")
    print(f"master map saved to: maps/all_clusters_to_office.html")
    
    if all_routes:
        print(f"\ndrawing detailed route for cluster 0...")
        draw_route(all_routes[0][1], file_path='maps/cluster_0_route.html')
        print(f"detailed route saved to: maps/cluster_0_route.html")
    
    print("\n" + "="*70)
    print("route optimization complete!")
    print("="*70)
    print(f"\nsummary:")
    print(f"  • total employees: {len(df)}")
    print(f"  • number of clusters: {NUM_CLUSTERS}")
    print(f"  • total routes: {len(all_routes)}")
    
    if total_distance > 0:
        print(f"  • total distance: {total_distance:.1f} km")
        
        if USE_TRAFFIC:
            print(f"\ntraffic analysis:")
            print(f"  • duration (no traffic): {total_duration_no_traffic:.0f} min ({total_duration_no_traffic/60:.1f} hours)")
            print(f"  • duration (with traffic): {total_duration_with_traffic:.0f} min ({total_duration_with_traffic/60:.1f} hours)")
            print(f"  • total traffic delay: +{total_traffic_delay:.0f} min ({total_traffic_delay/60:.1f} hours)")
            
            if total_duration_no_traffic > 0:
                impact = (total_traffic_delay/total_duration_no_traffic)*100
                print(f"  • traffic impact: +{impact:.1f}%")
                
                if impact < 20:
                    print(f"  • traffic status: 🟢 light traffic")
                elif impact < 40:
                    print(f"  • traffic status: 🟡 moderate traffic")
                else:
                    print(f"  • traffic status: 🔴 heavy traffic")
        else:
            print(f"  • total duration: {total_duration_no_traffic:.0f} min ({total_duration_no_traffic/60:.1f} hours)")
    
    print(f"\noutput files:")
    print(f"  • maps/generated_points.html - employee locations")
    print(f"  • maps/all_clusters_to_office.html - all optimized routes")
    print(f"  • maps/cluster_0_route.html - detailed view of first cluster")
    print("="*70)


if __name__ == "__main__":
    main()
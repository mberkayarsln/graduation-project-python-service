"""
Ana uygulama dosyası - Servis rota optimizasyonu
"""
from config import Config
from utils import print_section_header, print_summary
from modules.generate_data import generate_points
from modules.kmeans_cluster import cluster_points
from modules.optimize_route import optimize_tsp
from modules.draw_route import draw_route
from modules.traffic_router import get_route_with_traffic
import visualizer
import pandas as pd


def filter_employees_by_distance(df, centers, max_distance):
    """
    Merkeze uzak çalışanları filtreler
    
    Args:
        df: Çalışan dataframe
        centers: Cluster merkez noktaları
        max_distance: Maksimum mesafe (metre)
    
    Returns:
        df: Güncellenmiş dataframe (excluded kolonuyla)
    """
    from utils import haversine
    
    df['excluded'] = False
    
    for cluster_id in range(len(centers)):
        cluster_mask = df['cluster'] == cluster_id
        center = centers[cluster_id]
        
        for idx in df[cluster_mask].index:
            distance = haversine(
                df.loc[idx, 'lat'], 
                df.loc[idx, 'lon'], 
                center[0], 
                center[1]
            )
            if distance > max_distance:
                df.loc[idx, 'excluded'] = True
    
    return df


def optimize_cluster_routes(df, centers, config):
    """
    Her cluster için rota optimizasyonu yapar
    
    Args:
        df: Çalışan dataframe
        centers: Cluster merkez noktaları
        config: Konfigurasyon objesi
    
    Returns:
        list: [(cluster_id, optimized_route), ...]
    """
    print_section_header("ROTA OPTİMİZASYONU")
    
    all_routes = []
    
    for cluster_id in range(config.NUM_CLUSTERS):
        # Hariç tutulmayanları al
        cluster_df = df[(df['cluster'] == cluster_id) & (df['excluded'] == False)]
        all_in_cluster = len(df[df['cluster'] == cluster_id])
        points = list(zip(cluster_df['lat'], cluster_df['lon']))
        
        if len(points) > 0:
            excluded_count = all_in_cluster - len(points)
            print(f"Cluster {cluster_id}: {len(points)} çalışan (hariç: {excluded_count})", end=" → ")
            
            optimized_route = optimize_tsp(
                points, 
                office=config.OFFICE_LOCATION,
                use_traffic=config.USE_TRAFFIC,
                api_key=config.TOMTOM_API_KEY if config.USE_TRAFFIC else None,
                departure_time=config.get_departure_time() if config.USE_TRAFFIC else None,
                k_nearest=5
            )
            
            all_routes.append((cluster_id, optimized_route))
            print(f"{len(optimized_route)} durak")
        else:
            print(f"Cluster {cluster_id}: Boş (tüm çalışanlar hariç tutuldu)")
    
    return all_routes


def create_all_maps(df, centers, all_routes, config):
    """
    Tüm haritaları oluşturur
    
    Args:
        df: Çalışan dataframe
        centers: Cluster merkez noktaları
        all_routes: Optimize edilmiş rotalar
        config: Konfigurasyon objesi
    
    Returns:
        list: Oluşturulan dosya isimleri
    """
    print_section_header("HARİTALAR OLUŞTURULUYOR")
    
    output_files = []
    
    # 1. Çalışan konumları haritası
    print("1. Çalışan konumları haritası oluşturuluyor...")
    employees = [{'lat': row['lat'], 'lon': row['lon'], 'id': row['id']} 
                 for _, row in df.iterrows()]
    emp_file = visualizer.create_employees_map(employees, config.OFFICE_LOCATION)
    output_files.append(emp_file)
    print(f"   ✓ {emp_file}")
    
    # 2. Cluster haritası
    print("2. Cluster haritası oluşturuluyor...")
    employees_with_clusters = [
        {'lat': row['lat'], 'lon': row['lon'], 'cluster': int(row['cluster']), 'id': row['id']} 
        for _, row in df.iterrows()
    ]
    cluster_file = visualizer.create_cluster_map(
        employees_with_clusters, 
        centers, 
        config.OFFICE_LOCATION
    )
    output_files.append(cluster_file)
    print(f"   ✓ {cluster_file}")
    
    # 3. Optimized routes haritası
    if all_routes:
        print("3. Optimize edilmiş rotalar haritası oluşturuluyor...")
        
        routes_dict = {}
        for cluster_id, route in all_routes:
            if config.USE_TRAFFIC and config.TOMTOM_API_KEY:
                try:
                    result = get_route_with_traffic(
                        route, 
                        config.TOMTOM_API_KEY, 
                        config.get_departure_time()
                    )
                    routes_dict[cluster_id] = {
                        'coordinates': result['coordinates'],  # OSRM rota çizgisi
                        'stops': route,  # Gerçek durak noktaları
                        'distance_km': result['distance_km'],
                        'duration_min': result['duration_with_traffic_min']
                    }
                except Exception as e:
                    print(f"   ⚠ Cluster {cluster_id} için trafik bilgisi alınamadı: {e}")
                    from utils import calculate_route_stats
                    stats = calculate_route_stats(route)
                    routes_dict[cluster_id] = {
                        'coordinates': route,  # Basit çizgi için aynı noktalar
                        'stops': route,  # Gerçek durak noktaları
                        'distance_km': stats['distance_km'],
                        'duration_min': stats['duration_min']
                    }
            else:
                from utils import calculate_route_stats
                stats = calculate_route_stats(route)
                routes_dict[cluster_id] = {
                    'coordinates': route,  # Basit çizgi için aynı noktalar
                    'stops': route,  # Gerçek durak noktaları
                    'distance_km': stats['distance_km'],
                    'duration_min': stats['duration_min']
                }
        
        routes_file = visualizer.create_routes_map(
            routes_dict,
            config.OFFICE_LOCATION,
            centers,
            employees_with_clusters
        )
        output_files.append(routes_file)
        print(f"   ✓ {routes_file}")
        
        # 4. İlk cluster detay haritası
        if all_routes:
            print("4. Cluster 0 detay haritası oluşturuluyor...")
            draw_route(all_routes[0][1], file_path=config.MAP_CLUSTER_DETAIL)
            output_files.append(config.MAP_CLUSTER_DETAIL)
            print(f"   ✓ {config.MAP_CLUSTER_DETAIL}")
    
    return output_files


def main():
    """Ana program akışı"""
    
    # Konfigürasyonu yükle
    config = Config()
    
    # Başlık
    print_section_header("SERVİS ROTA OPTİMİZASYONU")
    print(f"Çalışan Sayısı: {config.NUM_EMPLOYEES}")
    print(f"Cluster Sayısı: {config.NUM_CLUSTERS}")
    print(f"Trafik Analizi: {'✓ Aktif' if config.USE_TRAFFIC else '✗ Pasif'}")
    
    if config.USE_TRAFFIC:
        if config.TOMTOM_API_KEY:
            departure = config.get_departure_time()
            print(f"Kalkış Saati: {departure.strftime('%Y-%m-%d %H:%M')}")
        else:
            print("⚠ TOMTOM_API_KEY bulunamadı - Trafik analizi devre dışı")
            config.USE_TRAFFIC = False
    
    # 1. Çalışan konumları oluştur
    print_section_header("ÇALIŞAN KONUMLARI OLUŞTURULUYOR")
    df = generate_points(n=config.NUM_EMPLOYEES, seed=42, show_map=False)
    print(f"✓ {len(df)} çalışan konumu oluşturuldu")
    
    # 2. Clustering yap
    print_section_header("CLUSTERING")
    df, centers = cluster_points(df, k=config.NUM_CLUSTERS, random_state=42)
    print(f"✓ {config.NUM_CLUSTERS} cluster oluşturuldu")
    
    # 3. Merkeze uzak çalışanları filtrele
    df = filter_employees_by_distance(df, centers, config.MAX_DISTANCE_FROM_CENTER)
    excluded_count = df['excluded'].sum()
    print(f"✓ {excluded_count} çalışan hariç tutuldu (>{config.MAX_DISTANCE_FROM_CENTER/1000}km)")
    
    # 4. Her cluster için rota optimizasyonu
    all_routes = optimize_cluster_routes(df, centers, config)
    
    # 5. Haritaları oluştur
    output_files = create_all_maps(df, centers, all_routes, config)
    
    # 6. İstatistikleri hesapla ve göster
    total_distance = 0
    total_duration = 0
    
    for cluster_id, route in all_routes:
        from utils import calculate_route_stats
        stats = calculate_route_stats(route)
        total_distance += stats['distance_km']
        total_duration += stats['duration_min']
    
    summary_stats = {
        'total_employees': len(df),
        'num_clusters': config.NUM_CLUSTERS,
        'active_routes': len(all_routes),
        'excluded': int(excluded_count),
        'total_distance': total_distance,
        'total_duration': total_duration,
        'use_traffic': config.USE_TRAFFIC,
        'output_files': output_files
    }
    
    print_summary(summary_stats)


if __name__ == "__main__":
    main()

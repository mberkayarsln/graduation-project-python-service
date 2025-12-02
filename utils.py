"""
Yardımcı fonksiyonlar
"""
import math
import folium
from config import Config


def haversine(lat1, lon1, lat2, lon2):
    """
    İki nokta arasındaki mesafeyi metre cinsinden hesaplar (Haversine formülü)
    
    Args:
        lat1, lon1: İlk noktanın koordinatları
        lat2, lon2: İkinci noktanın koordinatları
    
    Returns:
        float: Metre cinsinden mesafe
    """
    r = 6371000  # Dünya yarıçapı (metre)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def calculate_route_stats(route_points):
    """
    Rota için toplam mesafe ve tahmini süre hesaplar
    
    Args:
        route_points: [(lat, lon), ...] şeklinde koordinat listesi
    
    Returns:
        dict: {
            'distance_km': float,
            'duration_min': float,
            'avg_speed_kmh': float
        }
    """
    if len(route_points) < 2:
        return {'distance_km': 0, 'duration_min': 0, 'avg_speed_kmh': 0}
    
    total_distance = 0
    for i in range(len(route_points) - 1):
        total_distance += haversine(
            route_points[i][0], route_points[i][1],
            route_points[i+1][0], route_points[i+1][1]
        )
    
    distance_km = total_distance / 1000
    avg_speed_kmh = 30  # Ortalama şehir içi hız
    duration_min = (distance_km / avg_speed_kmh) * 60
    
    return {
        'distance_km': distance_km,
        'duration_min': duration_min,
        'avg_speed_kmh': avg_speed_kmh
    }


def create_base_map(center_lat, center_lon, zoom=11):
    """
    Temel harita objesi oluşturur
    
    Args:
        center_lat, center_lon: Harita merkez koordinatları
        zoom: Zoom seviyesi
    
    Returns:
        folium.Map
    """
    return folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles='OpenStreetMap'
    )


def add_office_marker(map_obj, office_location):
    """
    Haritaya ofis işareti ekler
    
    Args:
        map_obj: folium.Map objesi
        office_location: (lat, lon) tuple
    """
    folium.Marker(
        location=office_location,
        popup="<b>🏢 Ofis - Maslak</b>",
        icon=folium.Icon(color='red', icon='building', prefix='fa')
    ).add_to(map_obj)


def print_section_header(title):
    """Konsol çıktısı için bölüm başlığı yazdırır"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def print_summary(stats):
    """
    Özet istatistikleri yazdırır
    
    Args:
        stats: dict içinde istatistik bilgileri
    """
    print_section_header("ÖZET")
    
    print(f"Toplam Çalışan: {stats.get('total_employees', 0)}")
    print(f"Cluster Sayısı: {stats.get('num_clusters', 0)}")
    print(f"Aktif Rotalar: {stats.get('active_routes', 0)}")
    print(f"Hariç Tutulanlar: {stats.get('excluded', 0)}")
    
    if stats.get('total_distance', 0) > 0:
        print(f"\nToplam Mesafe: {stats['total_distance']:.1f} km")
        print(f"Toplam Süre: {stats.get('total_duration', 0):.0f} dk ({stats.get('total_duration', 0)/60:.1f} saat)")
    
    if stats.get('use_traffic', False) and stats.get('traffic_delay', 0) > 0:
        print(f"\n🚦 Trafik Analizi:")
        print(f"  Trafiksiz: {stats.get('duration_no_traffic', 0):.0f} dk")
        print(f"  Trafik ile: {stats.get('duration_with_traffic', 0):.0f} dk")
        print(f"  Gecikme: +{stats.get('traffic_delay', 0):.0f} dk")
        
        if stats.get('duration_no_traffic', 0) > 0:
            impact = (stats['traffic_delay'] / stats['duration_no_traffic']) * 100
            print(f"  Etki: +{impact:.1f}%")
    
    print(f"\n📁 Çıktı Dosyaları:")
    for filename in stats.get('output_files', []):
        print(f"  • {filename}")
    
    print('='*70)

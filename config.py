"""
Uygulama yapılandırma ayarları
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Uygulama konfigürasyonu"""
    
    # Ofis konumu (Maslak, İstanbul)
    OFFICE_LOCATION = (41.1097, 29.0204)
    
    # Çalışan ve cluster ayarları
    NUM_EMPLOYEES = 200
    NUM_CLUSTERS = 10
    MAX_DISTANCE_FROM_CENTER = 2000  # metre cinsinden (2km)
    
    # Trafik API ayarları
    USE_TRAFFIC = True
    TOMTOM_API_KEY = os.getenv('TOMTOM_API_KEY')
    
    # Kalkış saati (yarın sabah 8)
    @staticmethod
    def get_departure_time():
        """Yarın sabah 8:00 için datetime döndürür"""
        tomorrow_8am = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        if datetime.now().hour >= 8:
            tomorrow_8am += timedelta(days=1)
        return tomorrow_8am
    
    # Görselleştirme renkleri
    CLUSTER_COLORS = [
        '#ef4444',  # Kırmızı
        '#3b82f6',  # Mavi
        '#10b981',  # Yeşil
        '#f59e0b',  # Turuncu
        '#8b5cf6',  # Mor
        '#ec4899',  # Pembe
        '#14b8a6',  # Turkuaz
        '#06b6d4',  # Açık Mavi
        '#84cc16',  # Limon Yeşili
        '#f97316'   # Koyu Turuncu
    ]
    
    # Çıktı dosyaları
    OUTPUT_DIR = "maps"
    MAP_EMPLOYEES = f"{OUTPUT_DIR}/employees.html"
    MAP_CLUSTERS = f"{OUTPUT_DIR}/clusters.html"
    MAP_ROUTES = f"{OUTPUT_DIR}/optimized_routes.html"
    MAP_CLUSTER_DETAIL = f"{OUTPUT_DIR}/cluster_0_detail.html"

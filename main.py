"""
Ana uygulama dosyası - Object Oriented Versiyon

Kullanım:
    python main_oop.py
"""
from config import Config
from models.service_planner import ServicePlanner


def main():
    """Ana program akışı"""
    
    # Konfigürasyonu yükle
    config = Config()
    
    # Ana planlayıcı oluştur
    planner = ServicePlanner(config)
    
    # Tüm süreci çalıştır
    planner.run()


if __name__ == "__main__":
    main()

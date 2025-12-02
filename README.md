# Servis Rota Optimizasyon Sistemi

Bu proje, çalışanların konumlarına göre optimal servis rotalarını hesaplayan bir Python uygulamasıdır.

## 📁 Dosya Yapısı

```
.
├── config.py              # Uygulama konfigürasyonu
├── utils.py               # Yardımcı fonksiyonlar
├── visualizer.py          # Harita görselleştirme
├── main.py                # Ana uygulama (YENİ - DÜZENLENMİŞ)
│
├── old_version/           # Eski dosyalar (yedek)
│   └── main.py            # Eski ana program
│
├── generate_data.py       # Rastgele çalışan konumları oluşturma
├── kmeans_cluster.py      # K-means clustering
├── optimize_route.py      # TSP rota optimizasyonu
├── draw_route.py          # Detaylı rota çizimi
├── traffic_router.py      # Trafik analizi (TomTom API)
├── api_cache.py           # API cache yönetimi
│
├── requirements.txt       # Python bağımlılıkları
├── .env                   # API anahtarları (GİZLİ)
└── maps/                  # Oluşturulan haritalar
    ├── employees.html
    ├── clusters.html
    ├── optimized_routes.html
    └── cluster_0_detail.html
```

## 🚀 Kullanım

```bash
python main.py
```

> **Not:** Eski versiyon `old_version/` klasöründe yedek olarak saklanmaktadır.

## ⚙️ Konfigürasyon

`config.py` dosyasından ayarları değiştirebilirsiniz:

```python
NUM_EMPLOYEES = 200              # Çalışan sayısı
NUM_CLUSTERS = 10                # Cluster sayısı
MAX_DISTANCE_FROM_CENTER = 2000  # Max mesafe (metre)
USE_TRAFFIC = True               # Trafik analizi aktif/pasif
```

## 📊 Çıktılar

Program çalıştığında `maps/` klasöründe şu dosyalar oluşur:

1. **employees.html** - Tüm çalışan konumları
2. **clusters.html** - Cluster'lanmış çalışanlar
3. **optimized_routes.html** - Optimize edilmiş rotalar
4. **cluster_0_detail.html** - İlk cluster'ın detaylı rotası

## 🔧 Gereksinimler

```bash
pip install -r requirements.txt
```

## 🔑 API Anahtarı

TomTom API kullanmak için `.env` dosyasına API anahtarınızı ekleyin:

```
TOMTOM_API_KEY=your_api_key_here
```

## 📝 Notlar

- **main.py**: Yeniden düzenlenmiş, temiz kod yapısı
- **old_version/main.py**: Orijinal versiyon, yedek olarak saklanıyor

## 🎯 Özellikler

✅ Rastgele çalışan konumu oluşturma  
✅ K-means clustering  
✅ TSP (Gezgin Satıcı Problemi) optimizasyonu  
✅ Trafik analizi (TomTom API)  
✅ İnteraktif harita görselleştirme  
✅ Mesafe/süre hesaplama  
✅ Merkeze uzak çalışanları filtreleme  

## 📈 Geliştiriciler İçin

### Modül Yapısı

- **config.py**: Tüm ayarlar tek bir yerde
- **utils.py**: Tekrar kullanılabilir yardımcı fonksiyonlar
- **visualizer.py**: Harita oluşturma fonksiyonları
- **main.py**: Ana iş akışı, daha modüler

### Kod Organizasyonu

1. **Konfigürasyon** → config.py
2. **Veri Üretimi** → generate_data.py
3. **Clustering** → kmeans_cluster.py
4. **Optimizasyon** → optimize_route.py
5. **Görselleştirme** → visualizer.py
6. **Ana Akış** → main_new.py

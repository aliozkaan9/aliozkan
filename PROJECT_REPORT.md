# 🏭 Kablo Fabrikası MES Projesi Raporu

Bu rapor, kablo fabrikası için geliştirilen Üretim Yürütme Sistemi'nin (MES) teknik detaylarını, mimarisini ve kullanım senaryolarını içerir.

## 1. Proje Özeti
Bu proje, kablo üretim sürecini dijitalleştirmek, anlık izlenebilirlik sağlamak ve üretim verimliliğini (OEE) artırmak amacıyla tasarlanmıştır. Sistem, iş emirlerini yönetir, makinelerden gerçek zamanlı veri toplar ve kalite standartlarını otomatik olarak denetler.

## 2. Sistem Mimarisi

Sistem, modern Python teknolojileri kullanılarak modüler bir yapıda geliştirilmiştir.

### Teknoloji Yığını
*   **Programlama Dili:** Python 3.12
*   **Web Framework:** Flask (Backend API ve Dashboard)
*   **Veritabanı:** SQLite (SQLAlchemy ORM ile)
*   **Frontend:** HTML5, Bootstrap 5 (Responsive Dashboard)

### Klasör Yapısı
```
/
├── cable_mes/              # Ana Uygulama Paketi
│   ├── database.py         # Veritabanı bağlantısı
│   ├── models.py           # Veri Modelleri (Tablolar)
│   └── services.py         # İş Mantığı (Servis Katmanı)
├── templates/              # HTML Dosyaları
│   └── index.html          # Operatör Paneli
├── app.py                  # Web Sunucusu (Flask)
├── simulator.py            # Makine Simülatörü
└── init_db_script.py       # Kurulum Scripti
```

## 3. Veri Modelleri

Sistem aşağıdaki temel varlıklar üzerine kuruludur:

1.  **Machine (Makine):** Fabrikadaki üretim hatlarını temsil eder (Örn: Extruder, Büküm).
2.  **Product (Ürün):** Üretilecek kablo tiplerini ve teknik spekülasyonlarını (Hedef Çap, Tolerans) tutar.
3.  **WorkOrder (İş Emri):** Belirli bir ürünün, belirli bir miktarda üretilmesi emridir.
4.  **Telemetry (Telemetri):** Makineden saniyelik olarak gelen verilerdir:
    *   Hız (m/dak)
    *   Sıcaklık (°C)
    *   Çap (mm)
5.  **QualityAlert (Kalite Alarmı):** Üretim toleranslarının dışına çıkıldığında oluşan kayıtlar.

## 4. Temel Fonksiyonlar

### A. İş Emri Yönetimi
Planlama departmanı (veya ERP) tarafından oluşturulan iş emirleri sisteme girilir. Operatör iş emrini başlattığında, makine durumu "RUNNING" olarak güncellenir ve üretim sayacı başlar.

### B. Gerçek Zamanlı İzleme ve Kalite Kontrol
Sistem, sahadan gelen verileri (`Telemetry`) anlık olarak işler.
*   **Çap Kontrolü:** Ölçülen kablo çapı, ürün reçetesindeki `hedef_çap ± tolerans` aralığı ile karşılaştırılır.
*   **Otomatik Alarm:** Eğer çap tolerans dışındaysa, sistem otomatik olarak bir `QualityAlert` kaydı oluşturur ve dashboard üzerinde operatörü uyarır.

### C. OEE (Genel Ekipman Etkinliği) Hesabı
Sistem basitleştirilmiş bir OEE hesabı yapar:
*   **Performans:** (Gerçekleşen Hız / Hedef Hız) * 100

## 5. Simülasyon Senaryosu
`simulator.py` dosyası, gerçek bir Ekstruder makinesini taklit eder.
*   Otomatik iş emri oluşturur.
*   Hızı kademeli olarak artırır.
*   Rastgele zamanlarda çap sapmaları (Anomali) üreterek sistemin alarm mekanizmasını tetikler.

## 6. Kurulum ve Çalıştırma

1.  **Kurulum:**
    ```bash
    pip install -r requirements.txt
    python init_db_script.py
    ```

2.  **Web Arayüzünü Başlatma:**
    ```bash
    python app.py
    ```
    Tarayıcıda `http://localhost:5000` adresine gidin.

3.  **Simülasyonu Başlatma (Yeni Terminalde):**
    ```bash
    python simulator.py
    ```
    Dashboard üzerinde canlı verilerin aktığını göreceksiniz.

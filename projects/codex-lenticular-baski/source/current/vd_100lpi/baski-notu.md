# VD — 100 LPI Üç Derinlik Denemesi Baskı Notu ve Kalibrasyon Taslağı

> [!IMPORTANT]
> Bu çalışma bir **baskı denemesi / kalibrasyon taslağıdır**. Çıktılar 100 LPI lens ve 1200 DPI yazıcı adayı için dijital olarak doğrulanmıştır; henüz fiziksel RIP/baskı doğrulaması yapılmamıştır.

## 1. Üretim Özeti ve Parametreler
- **Kaynak Görsel:** `vd-gigapixel-recover v2-2x-faceai v2.jpg` (1872 × 3098 px, Tam kadraj)
- **Sabit Burun Referansı:** Piksel (958, 432) | Normalize (x=0.512026, y=0.139490)
- **Ortak Derinlik Haritası:** DA3MONO-LARGE (process_res=1008, preserve normalizasyon) + Ayrıntılı yerel AI derinlik (güç 0.8)
- **Baskı Çözünürlüğü:** 1200 PPI / 1200 DPI
- **Lens:** Nominal ve Etkin 100 LPI dikey, Tilt=0, Bleed=0, Fit=Contain
- **Kanal Sayısı:** Ne=6 kanal, Nr=6 kamera görünüşü
- **Kanal Başına Raster Piksel:** Kanal başına 2.0000 raster piksel hesaplanmıştır; fiziksel kanal ayrımı henüz doğrulanmamıştır.

## 2. Varyant Karşılaştırma Tablosu

| Parametre | A - Normal | B - Artırılmış | C - Güçlü |
| :--- | :--- | :--- | :--- |
| **Kamera Açısı (İstenen / Uygulanan)** | 0.84° / 0.84° | 1.26° / 1.26° | 1.67° / 1.67° |
| **Hedef Bütçe (Ön / Arka Paralaks)** | %0.28 / %0.42 | %0.42 / %0.61 | %0.56 / %0.84 |
| **Gerçekleşen Max Paralaks** | %0.42 | %0.61 | %0.84 |
| **Disparite Aralığı** | [-5.2, 7.8] px | [-7.8, 11.5] px | [-10.4, 15.7] px |
| **Sayfa Birleştirme Fazı** | 0.0000 | 0.7500 | 0.5000 |
| **Bağımsız Panel Fazı** | 0.0000 | 0.0000 | 0.0000 |
| **Görünüş Boşluk Oranı** | %0.0000 | %0.0000 | %0.0000 |
| **Burun Sabitliği (Uç Görüşler)** | Sabit (<=1 px) | Sabit (<=1 px) | Sabit (<=1 px) |

## 3. Sayfa ve Dosya Yapısı
1. **Tek Parça 100 LPI Lens Altında Birleşik Karşılaştırma Sayfası:**
   - `karsilastirma_sayfasi_etiketli_100lpi_1200ppi.tif`: 18423 × 10446 px (~389.95 × 221.12 mm). Altta 6 mm açıklama şeridi mevcuttur.
   - `karsilastirma_sayfasi_resim_alani_100lpi_1200ppi.tif`: 18423 × 10163 px (~389.95 × 215.12 mm). Saf görüntü alanıdır.
2. **Ayrı Lens Parçaları İçin Bağımsız Paneller (Faz=0.0):**
   - `panel_A_bagimsiz_phase0.tif`, `panel_B_bagimsiz_phase0.tif`, `panel_C_bagimsiz_phase0.tif` (6141 × 10163 px).

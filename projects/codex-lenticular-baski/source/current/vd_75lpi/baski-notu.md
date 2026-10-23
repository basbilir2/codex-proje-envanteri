# VD — 75 LPI Üç Derinlik Denemesi Baskı Notu ve Kalibrasyon Taslağı

> [!IMPORTANT]
> Bu çalışma bir **baskı denemesi / kalibrasyon taslağıdır**. Çıktılar 75 LPI lens ve 1200 DPI yazıcı adayı için dijital olarak doğrulanmıştır; henüz fiziksel RIP/baskı doğrulaması yapılmamıştır.

## 1. Üretim Özeti ve Parametreler
- **Kaynak Görsel:** `vd-gigapixel-recover v2-2x-faceai v2.jpg` (1872 × 3098 px, Tam kadraj)
- **Sabit Burun Referansı:** Piksel (958, 432) | Normalize (x=0.512026, y=0.139490)
- **Ortak Derinlik Haritası:** DA3MONO-LARGE (process_res=1008, preserve normalizasyon) + Ayrıntılı yerel AI derinlik (güç 0.8)
- **Baskı Çözünürlüğü:** 1200 PPI / 1200 DPI
- **Lens:** Nominal ve Etkin 75 LPI dikey, Tilt=0, Bleed=0, Fit=Contain
- **Kanal Sayısı:** Ne=8 kanal, Nr=8 kamera görünüşü
- **Kanal Başına Raster Piksel:** Kanal başına 2.0000 raster piksel hesaplanmıştır; fiziksel kanal ayrımı henüz doğrulanmamıştır.

## 2. Varyant Karşılaştırma Tablosu

| Parametre | A - Normal | B - Artırılmış | C - Güçlü |
| :--- | :--- | :--- | :--- |
| **Kamera Açısı (İstenen / Uygulanan)** | 1.56° / 1.56° | 2.34° / 2.34° | 3.13° / 3.13° |
| **Hedef Bütçe (Ön / Arka Paralaks)** | %0.52 / %0.78 | %0.78 / %1.15 | %1.04 / %1.56 |
| **Gerçekleşen Max Paralaks** | %0.78 | %1.15 | %1.56 |
| **Disparite Aralığı** | [-9.7, 14.6] px | [-14.6, 21.4] px | [-19.5, 29.2] px |
| **Sayfa Birleştirme Fazı** | 0.0000 | 0.8125 | 0.6250 |
| **Bağımsız Panel Fazı** | 0.0000 | 0.0000 | 0.0000 |
| **Görünüş Boşluk Oranı** | %0.0000 | %0.0000 | %0.0000 |
| **Burun Sabitliği (Uç Görüşler)** | Sabit (<=1 px) | Sabit (<=1 px) | Sabit (<=1 px) |

## 3. Sayfa ve Dosya Yapısı
1. **Tek Parça 75 LPI Lens Altında Birleşik Karşılaştırma Sayfası:**
   - `karsilastirma_sayfasi_etiketli_75lpi_1200ppi.tif`: 18423 × 10446 px (~389.95 × 221.12 mm). Altta 6 mm açıklama şeridi mevcuttur.
   - `karsilastirma_sayfasi_resim_alani_75lpi_1200ppi.tif`: 18423 × 10163 px (~389.95 × 215.12 mm). Saf görüntü alanıdır.
2. **Ayrı Lens Parçaları İçin Bağımsız Paneller (Faz=0.0):**
   - `panel_A_bagimsiz_phase0.tif`, `panel_B_bagimsiz_phase0.tif`, `panel_C_bagimsiz_phase0.tif` (6141 × 10163 px).

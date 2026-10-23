# VD — Üç Derinlik Denemesi Baskı Notu ve Kalibrasyon Taslağı

> [!IMPORTANT]
> Bu çalışma bir **baskı denemesi / kalibrasyon taslağıdır**. Çıktılar 50.20 LPI lens ve 1200 DPI yazıcı adayı için dijital olarak doğrulanmıştır; henüz fiziksel RIP/baskı doğrulaması yapılmamıştır.

## 1. Üretim Özeti ve Parametreler
- **Kaynak Görsel:** `vd-gigapixel-recover v2-2x-faceai v2.jpg` (1872 × 3098 px, Tam kadraj)
- **Sabit Burun Referansı:** Piksel (958, 432) | Normalize (x=0.512026, y=0.139490)
- **Derinlik Modeli:** DA3MONO-LARGE (process_res=1008, preserve normalizasyon) + Ayrıntılı yerel AI derinlik (güç 0.8)
- **Baskı Çözünürlüğü:** 1200 PPI / 1200 DPI
- **Lens:** Nominal ve Etkin 50.20 LPI dikey, Tilt=0, Bleed=0, Fit=Contain
- **Kanal Sayısı:** Ne=10 kanal, Nr=10 kamera görünüşü
- **Kanal Başına Raster Piksel:** Kanal başına 2,3904 raster piksel hesaplanmıştır; fiziksel kanal ayrımı henüz doğrulanmamıştır.

## 2. Varyant Karşılaştırma Tablosu

| Parametre | A - Normal | B - Artırılmış | C - Güçlü |
| :--- | :--- | :--- | :--- |
| **Kamera Açısı (İstenen / Uygulanan)** | 3.0° / 3.00° | 4.5° / 4.50° | 6.0° / 6.00° |
| **Hedef Bütçe (Ön / Arka Paralaks)** | %1.0 / %1.5 | %1.5 / %2.2 | %2.0 / %3.0 |
| **Gerçekleşen Max Paralaks** | %1.50 | %2.20 | %3.00 |
| **Disparite Aralığı** | [-18.7, 28.1] px | [-28.1, 41.2] px | [-37.4, 56.2] px |
| **Burun Çevresi İç Hacim (Relief)** | 2.5 px | 3.7 px | 5.1 px |
| **Sayfa Birleştirme Fazı** | 0.0000 | 0.8985 | 0.7970 |
| **Bağımsız Panel Fazı** | 0.0000 | 0.0000 | 0.0000 |
| **Görünüş Boşluk Oranı** | %0.0000 | %0.0000 | %0.0000 |
| **Burun Sabitliği (Uç Görüşler)** | Sabit (<=1 px) | Sabit (<=1 px) | Sabit (<=1 px) |

## 3. Sayfa ve Dosya Yapısı

1. **Tek Parça Lens Altında Birleşik Karşılaştırma Sayfası:**
   - `karsilastirma_sayfasi_etiketli_1200ppi.tif`: 18423 × 10446 px (~389.95 × 221.12 mm). Altta 6 mm açıklama şeridi mevcuttur.
   - `karsilastirma_sayfasi_resim_alani_1200ppi.tif`: 18423 × 10163 px (~389.95 × 215.12 mm). Saf görüntü alanıdır.
   - **Sürekli Lens Fazı Uyarısı:** Tek lens yaprağı altında şerit başlangıcının kaymaması için B paneli faz=0.8985, C paneli faz=0.7970 ile kodlanarak birleştirilmiştir. `(global_phase + x_offset_px * 50.20 / 1200) % 1` kuralı korunmuştur.

2. **Ayrı Lens Parçaları İçin Bağımsız Panel Dosyaları (Faz = 0.0):**
   - `panel_A_bagimsiz_phase0.tif`: 6141 × 10163 px (129.98 × 215.12 mm)
   - `panel_B_bagimsiz_phase0.tif`: 6141 × 10163 px (129.98 × 215.12 mm)
   - `panel_C_bagimsiz_phase0.tif`: 6141 × 10163 px (129.98 × 215.12 mm)
   *Paneller ayrı ayrı kesilmiş 13 cm lenslerin altına yerleştirilecekse bu bağımsız faz=0 dosyaları basılmalıdır.*

3. **Önizleme ve Kalite Belgeleri:**
   - `karsilastirma_onizleme_kucuk.jpg`: Hızlı ekrandan inceleme için 3000 px genişliğinde önizleme görseli.
   - `analysis_A/`, `analysis_B/`, `analysis_C/`: Sahne analizi raporları ve optik risk haritaları.
   - `render_A/`, `render_B/`, `render_C/`: Her varyantın 10 adet 3D kamera karesi, derinlik ve onarım katmanları.

## 4. Kritik Baskı ve RIP Talimatları
- **Baskı Ölçeği:** Yazdırma yazılımında kesinlikle **%100 (Gerçek Boyut / Do Not Scale)** seçilmeli; 'Sayfaya Sığdır' veya yeniden örnekleme kapatılmalıdır.
- **13 cm Kuralı:** Her görsel paneli tam olarak 129.98 mm (6141 piksel) olarak sınırlandırılmıştır. Birleşik sayfa eni ~39 cm'dir. Tüm sayfayı 13 cm'e küçültmeyiniz.
- **Renk Profili:** Çıktılar profilli RGB modundadır. Verilmiş bir ICC dosyası olmadığı için yapay CMYK dönüşümü yapılmamıştır.
- **Ön/Arka Baskı:** Dosyalar önden yönlendirilmiş (mirror=false, white_underbase=false) deneme formatındadır. Arka yüz UV baskı yapılacaksa RIP veya laminasyon aşamasında ters baskı gereksinimi doğrulanmalıdır.
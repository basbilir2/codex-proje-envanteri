# Lentiküler Baskı Projesi — Kalıcı Öğrenme ve Deneyim Kaydı

> **Kapsam Notu:** Bu belge yalnız `C:\Users\USER\Documents\lenticular baskı` projesi ve alt klasörleri için geçerlidir. Genel kullanıcı/sistem kurallarını etkilemez.

---

## 1. Güncel Durum Özeti ve Konu Dizini

### 1.1 Güncel Durum Özeti (12 Ekim 2026)

> **Son üretim — aynı geometriyle 75 ve 50,20 LPI:** Codex'in 4° / 6 görüş / 6 kanal 100 LPI düzeltmesindeki altı kare aynen kullanıldı. Yeni dosyalar `vd_75_50_20_codex_20261012/75lpi/interlaced.tif` ve `50_2lpi/interlaced.tif`. Açı, 3D geometri ve derinlik haritası değişmedi; AI/Blender veya yeni önizleme üretimi yok. Dijital kontroller geçti, fiziksel kalite onayı bekleniyor. Önceki doğal hacim reçetesi kullanıcı tarafından başarısız bulundu; güncel geometri referansı `vd_100lpi_codex_20261012/`.

- **Doğrulanan Dijital Çıktılar:**
  - **50.20 LPI:** 3 varyant (A: 3°, B: 4.5°, C: 6°), Nr=10, Ne=10. Bağımsız paneller, tek lens fazlı paneller, birleşik etiketli/etiketsiz 1200 PPI TIFF'ler (ICC gömülü), temiz orta görüş ve hareketli önizlemeler üretildi ve doğrulandı.
  - **75.0 LPI:** 3 varyant (A: 1.562°, B: 2.344°, C: 3.126°), Nr=8, Ne=8. `vd_75lpi/` altında tüm paneller, birleşik TIFF sayfaları ve önizlemeler üretildi ve doğrulandı.
  - **100.0 LPI:** 3 varyant (A: 0.837°, B: 1.256°, C: 1.675°), Nr=6, Ne=6. `vd_100lpi/` altında tüm paneller, birleşik TIFF sayfaları ve önizlemeler üretildi ve doğrulandı.
  - **Yeni Belirgin Derinlik Denemesi (10° Açı, %4 Ön / %6 Arka Paralaks, Nr=12, Ne=12):** Ortak 12-görüşlü Blender render seti (`shared_render_12/`, 1872x3098 tam kadraj) paylaşılarak 50.20 LPI, 75 LPI ve 100 LPI için 3 yeni bağımsız profilli 1200 PPI TIFF panel (`panel_*lpi_belirgin_phase0.tif`), 2-panelli ve 4-panelli hareketli karşılaştırmalar (APNG/GIF), statik orta görüş ve detay kırpılmış kusur panoları üretildi ve doğrulandı (`vd_belirgin_derinlik_20261012/`).
  - **Doğal Hacim ve Bölgesel Düzenleme Denemesi (10° Açı, %2.8 Ön / %6 Arka Paralaks, Nr=12, Ne=12):** Kullanıcının gerçek fiziksel baskı geri bildirimi üzerine (elin aşırı fırlaması fakat yüzey iç hacimlerinin düz kalması), el hareketi %30 azaltılmış (-52.42 px disparite), el tavan kırpılması giderilmiş, burun sabit (0.00 px) tutularak yüz hatları 1.70x kabartılmış, gövde kavisi ve kıyafet kumaş katmanları eklenmiş yeni derinlik haritası (`depth_dogal_hacim.npy`) ile 50.20, 75 ve 100 LPI için yeni üretimler ve 4-bölgeli detaylı karşılaştırma animasyonları hazırlandı (`vd_dogal_hacim_20261012/`).
- **Kullanıcı Gerçek Baskı Geri Bildirimi ve Alınan Ders:** Kullanıcı gerçek baskıda elin gereğinden fazla dışarı çıktığını, yüz, parmak ve kıyafet detaylarının ise hacimsiz kaldığını; yalnızca öne fırlayan bir nesne değil doğal hacimli 3D istendiğini belirtti. Hangi LPI baskısının incelendiği belirtilmedi (tüm lenslerin genel kuralı sayılmadı). Tek nesnenin öne çıkması ile yüzeylerin iç hacmi ayrıldı; elin baskı düzlemine göre aşırı paralaksı azaltılırken anatomik iç hacimler bağımsız olarak heykeltıraş hassasiyetiyle güçlendirildi.
- **Çözülen Kritik Sorunlar:** Ham TIFF birleştirmede ICC profili kaybı, küçültülmüş interlace kaynaklı sahte önizleme çizgilenmesi, salt dosya varlığına dayalı önbellek hatası, çoklu varyantların ortak `render_manifest.json` üzerine yazması, eksik `quality.json` yolu ve normalizer eğrisi kaynaklı el paralaksının geri çekilememesi sorunu (balanced normalizer trap) çözüldü.
- **Bekleyen Doğrulama:** Fiziksel baskı kalibrasyonu (`pitch_verified=false`, `lens_angle_verified=false`, `raster_ppi_verified=false`, `physical_3d_verified=false`). Doğal hacim denemesi kullanıcının fiziksel incelemesine sunulmuştur.

### 1.2 Konu Dizini
1. [Sistem Mimarisi, Motorlar ve Araçlar](#2-sistem-mimarisi-motorlar-ve-araçlar)
2. [Ortak Derinlik Haritası ve Yeniden Kullanım Protokolü](#3-ortak-derinlik-haritası-ve-yeniden-kullanım-protokolü)
3. [Üretim Varyantları ve Doğrulama Durumları](#4-üretim-varyantları-ve-doğrulama-durumları)
4. [Hata Çözümleri ve Doğrulanmış Dersler](#5-hata-çözümleri-ve-doğrulanmış-dersler)
5. [Önbellek Geçersiz Kılma Matrisi](#6-önbellek-geçersiz-kılma-matrisi)
6. [Doğrulanmamış Fiziksel Parametreler ve Baskı Geri Bildirimi](#7-doğrulanmamış-fiziksel-parametreler-ve-baskı-geri-bildirimi)
7. [Deneyim ve Değişiklik Günlüğü](#8-deneyim-ve-değişiklik-günlüğü)

---

## 2. Sistem Mimarisi, Motorlar ve Araçlar

### 2.1 Asıl Yazılım ve Çalışma Ortamı
- **Yazılım Kökü:** `C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1` (Lenticular Studio)
- **Python Yolu:** `C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1\.venv\Scripts\python.exe`
- **Kaynak Veriler:** `sources/` salt okunurdur. Mevcut projede çalışma alanı `C:\Users\USER\Documents\lenticular baskı` klasörüdür.

### 2.2 Çekirdek Python Modülleri
| Modül | Görev ve İşlev | Çağrı Biçimi |
| :--- | :--- | :--- |
| `lenticular.analyzer` | Sahne geometrisi, disparite aralığı, derinlik örnekleme riski hesaplama | `analyze_scene(photo, depth, render=None, printing=None)` / `save_analysis(...)` |
| `lenticular.repair` | Derinlik düzenleme, sıfır düzlemi belirleme, paralaks bütçesi planlama | `editable_depth(...)`, `plan_parallax(...)`, `save_parallax_map(...)` |
| `lenticular.geometry` | Kamera dizilimi, açı ve render parametre doğrulama | `validate(dict(nr=..., ne=..., ...))` |
| `lenticular.runner` | Blender üzerinden çoklu görüş renderı alma, SHA256 özet çıkarma | `render(photo, depth, out_dir, config, blender=...)`, `digest(path)` |
| `lenticular.printing` | Görüşleri şeritler halinde lentiküler rastera interlace etme | `encode(render_dir, print_dir, print_config)` |
| `lenticular.optics` | Optik pitch, izleme mesafesi, açı ve kanal kapasitesi modelleme | Heuristik başlangıç hesaplamaları |
| `lenticular.detail_depth`| AI derinliğine yüksek frekanslı yüzey kabartısı ekleme | `detail_strength=0.8` (yalnız ilk harita üretiminde) |

### 2.3 Projeye Özel Araçlar (`tools/`)
- [`tools/lens_plan.py`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/tools/lens_plan.py):
  - **Kullanım:** `python tools/lens_plan.py --lpi 75 100`
  - **İşlev:** 50.20 LPI temelini referans alarak seçilen kamera hareketini piksel ölçeğinde koruyan deterministik JSON üretim planı oluşturur. Girdiler değişmedikçe aynı plan hash'ini döndürür.
- [`tools/execute_lens_plan.py`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/tools/execute_lens_plan.py):
  - **Kullanım:** `python tools/execute_lens_plan.py --plan <plan_path> [--check-cache-only]`
  - **İşlev:** Çoklu lens planı yürütme motorudur. Giriş bütünlüğünü doğrular, C önizleme boşluk kontrolü yapar, Blender renderlarını alır, burun stabilitesini teyit eder, interlace yapar, ICC profilini koruyarak etiketli/etiketsiz karşılaştırma sayfalarını birleştirir, temiz önizlemeler üretir.
  - **Önbellek Denetimi:** `--check-cache-only` bayrağı ile üretim başlatmadan tüm varyantların önbellek geçerliliğini test eder.
- [`apply_vd_fixes.py`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/apply_vd_fixes.py):
  - 50.20 LPI sonuçlarındaki ICC profili aktarımı ve temiz görüş önizlemesi montajı için kullanılan düzeltme betiğidir.
- [`execute_vd_plan.py`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/execute_vd_plan.py):
  - 50.20 LPI ilk üretimi için yazılmış tek seferlik yürütücüdür (yeni çoklu lens işleri için doğrudan çalıştırılmaz).

---

## 3. Ortak Derinlik Haritası ve Yeniden Kullanım Protokolü

### 3.1 Kaynak ve Derinlik Kimliği
- **Kaynak Görsel:** `C:\Users\USER\Downloads\vd-gigapixel-recover v2-2x-faceai v2.jpg`
  - Boyut: 1872 × 3098 piksel, tam kadraj.
  - SHA256: `d7d3c1c669483c99540c1f82ad71e34d3aa9b027facf6ce1c5785e400f694ec5`
- **Doğrulanmış Derinlik Haritası:** `prepared_depth/depth.npy`
  - SHA256: `931371a06d7434291818da22b7598206f5460a1810f7c777b3d350deb3cb879b`
  - Reçete: `process_res=1008`, `depth_normalization="preserve"`, `detail_enabled=true`, `detail_strength=0.8`, `surface_strength=0`.
  - Kayıt Dosyası: [`knowledge/depth-cache.json`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/knowledge/depth-cache.json)

### 3.2 Yeniden Kullanım Kuralları
1. **AI Derinliğini Tekrar Çalıştırmama:** `prepared_depth/depth.npy` dosyası `detail_strength=0.8` kabartısını zaten içermektedir. Yeniden detaylandırma çalıştırılırsa yüzey kabartısı çiftlenir ve yapay kırılmalar oluşur.
2. **Sabit Burun Referansı:**
   - Normalize koordinat: `x = PRIVATE_PHONE_0001`, `y = 0.1394898289` (yaklaşık piksel: 958, 432).
   - Bu nokta sıfır paralaks (fiziksel lens yüzeyi) referansıdır. Tüm lens ve varyantlarda aynı referans noktası korunmalıdır; burun derinliği elle boyanmamalıdır.
3. **Katman ve Onarım Bütçesi:** 4 katman (`layers=4`), inpaint yarıçapı 5 (`inpaint_radius=5`), gelişmiş onarım (`repair_quality="advanced"`).

---

## 4. Üretim Varyantları ve Doğrulama Durumları

Bütün paneller 6141 × 10163 piksel, 1200 PPI, 129.9845 × 215.1168 mm boyutlarındadır (13 cm kullanıcı sınırına uygun).

### 4.1 50.20 LPI Karşılaştırma Seti
- **Lens / Raster:** `nominal_lpi = effective_lpi = 50.20`, $N_r = 10$, $N_e = 10$, piksel/kanal: 2.3904.
- **Varyant Ayarları:**
  - **A (Normal):** İstenen/Uygulanan Açı: 3.00°, Ön Paralaks: %1.0, Arka: %1.5, Gerçekleşen Max Paralaks: %1.50.
  - **B (Artırılmış):** İstenen/Uygulanan Açı: 4.50°, Ön Paralaks: %1.5, Arka: %2.2, Gerçekleşen Max Paralaks: %2.20.
  - **C (Güçlü):** İstenen/Uygulanan Açı: 6.00°, Ön Paralaks: %2.0, Arka: %3.0, Gerçekleşen Max Paralaks: %3.00.
- **Çıktı Yolları:**
  - Birleşik Sayfalar: [`karsilastirma_sayfasi_etiketli_1200ppi.tif`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/karsilastirma_sayfasi_etiketli_1200ppi.tif) (18423 × 10446 px, ICC gömülü), `karsilastirma_sayfasi_resim_alani_1200ppi.tif`.
  - Bağımsız Paneller: `panel_A_bagimsiz_phase0.tif`, `panel_B_bagimsiz_phase0.tif`, `panel_C_bagimsiz_phase0.tif`.
  - Tek Lens Sayfa Fazı Panelleri: `panel_A_sheet_phase.tif`, `panel_B_sheet_phase.tif`, `panel_C_sheet_phase.tif`.
  - Önizlemeler: `karsilastirma_temiz_gorunusler_merkez.jpg`, `karsilastirma_hareketli_look_around.png`.
- **Durum:** `rendered_and_verified_digital: true`, `physical_3d_verified: false`.

### 4.2 75.0 LPI Karşılaştırma Seti
- **Lens / Raster:** `nominal_lpi = effective_lpi = 75.0`, $N_r = 8$, $N_e = 8$, piksel/kanal: 2.0000. Çıkış Klasörü: `vd_75lpi/`.
- **Varyant Ayarları:**
  - **A (Normal):** Açı: 1.562038°, Gerçekleşen Max Paralaks: %0.780889, Disparite: `[-9.7, 14.6]` px, Burun kayması: 0 px (Sabit).
  - **B (Artırılmış):** Açı: 2.343545°, Gerçekleşen Max Paralaks: %1.145304, Disparite: `[-14.6, 21.4]` px, Burun kayması: 0 px (Sabit).
  - **C (Güçlü):** Açı: 3.125638°, Gerçekleşen Max Paralaks: %1.561778, Disparite: `[-19.5, 29.2]` px, Burun kayması: 0 px (Sabit).
- **Çıktı Yolları:**
  - Birleşik Sayfalar: [`vd_75lpi/karsilastirma_sayfasi_etiketli_75lpi_1200ppi.tif`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/vd_75lpi/karsilastirma_sayfasi_etiketli_75lpi_1200ppi.tif), `vd_75lpi/karsilastirma_sayfasi_resim_alani_75lpi_1200ppi.tif`.
  - Bağımsız Paneller: `vd_75lpi/panel_{A,B,C}_bagimsiz_phase0.tif`.
  - Sayfa Fazlı Paneller: `vd_75lpi/panel_{A,B,C}_sheet_phase.tif` (Fazlar: A=0, B=0.8125, C=0.625).
  - Önizlemeler: `vd_75lpi/karsilastirma_temiz_gorunusler_orta_75lpi.jpg`, `vd_75lpi/karsilastirma_hareketli_look_around_75lpi.png`.
- **Durum:** `rendered_and_verified_digital: true`, `physical_3d_verified: false`.

### 4.3 100.0 LPI Karşılaştırma Seti
- **Lens / Raster:** `nominal_lpi = effective_lpi = 100.0`, $N_r = 6$, $N_e = 6$, piksel/kanal: 2.0000. Çıkış Klasörü: `vd_100lpi/`.
- **Varyant Ayarları:**
  - **A (Normal):** Açı: 0.836843°, Gerçekleşen Max Paralaks: %0.418333, Disparite: `[-5.2, 7.8]` px, Burun kayması: 0 px (Sabit).
  - **B (Artırılmış):** Açı: 1.255595°, Gerçekleşen Max Paralaks: %0.613556, Disparite: `[-7.8, 11.5]` px, Burun kayması: 0 px (Sabit).
  - **C (Güçlü):** Açı: 1.674745°, Gerçekleşen Max Paralaks: %0.836667, Disparite: `[-10.4, 15.6]` px, Burun kayması: 0 px (Sabit).
- **Çıktı Yolları:**
  - Birleşik Sayfalar: [`vd_100lpi/karsilastirma_sayfasi_etiketli_100lpi_1200ppi.tif`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/vd_100lpi/karsilastirma_sayfasi_etiketli_100lpi_1200ppi.tif), `vd_100lpi/karsilastirma_sayfasi_resim_alani_100lpi_1200ppi.tif`.
  - Bağımsız Paneller: `vd_100lpi/panel_{A,B,C}_bagimsiz_phase0.tif`.
  - Sayfa Fazlı Paneller: `vd_100lpi/panel_{A,B,C}_sheet_phase.tif` (Fazlar: A=0, B=0.75, C=0.5).
  - Önizlemeler: `vd_100lpi/karsilastirma_temiz_gorunusler_orta_100lpi.jpg`, `vd_100lpi/karsilastirma_hareketli_look_around_100lpi.png`.
- **Durum:** `rendered_and_verified_digital: true`, `physical_3d_verified: false`.

### 4.4 Yeni Belirgin Derinlik Denemesi (10° Açı, %4 Ön / %6 Arka Paralaks, Nr=12, Ne=12)
Kullanıcının önceki 3D etkisini zayıf bulması üzerine hazırlanan tek görsellik yeni denemedir. Üç lenste de render parametreleri aynı olduğu için 12 görüşlük tek bir Blender render seti paylaşılmış; interlace aşaması 50.20, 75 ve 100 LPI için ayrı yapılmıştır.

- **Ortak Render Parametreleri:**
  - $N_r = 12$, $N_e = 12$, Açı = 10.0°, Ön Paralaks = %4.0, Arka Paralaks = %6.0, Azami Paralaks Sınırı = %6.0.
  - `edge_guard = false` (kenar kusurları görüntü üzerinden incelenmek üzere serbest bırakıldı).
  - Burun referans noktası (`x=PRIVATE_PHONE_0001, y=0.1394898289`), kaynak kadraj ve ortak detaylı harita (`prepared_depth/depth.npy`) korundu.
  - Render Çıktısı: [`vd_belirgin_derinlik_20261012/shared_render_12/`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/vd_belirgin_derinlik_20261012/shared_render_12)
  - Gerçekleşen Değerler: Efektif Açı = 10.0°, Gerçekleşen Max Paralaks = %6.00, Disparite Aralığı = `[-74.88, +112.32]` px. Sahne uç disparite farkı 187.2 px'dir; bu değer tek bir elin hareketi olmayıp arka plan (+112.32 px) ile ön plan (-74.88 px) arasındaki toplam sahne aralığıdır. Yüz/burun referans bölgesi derinlik rölyefi = 10.14 px (bu değer geometrik paralaks bütçesini gösterir; anatomik doğruluğun veya fiziksel kabartının kanıtı sayılamaz).
  - Boşluk Oranı: %0.00 (`max_nonopaque_fraction = 0.0`).
  - Burun Referansı Stabilitesi ve Ölçüm Ayrımı:
    - Geometrik Sıfır Düzlemi Disparitesi: `0.0 px`.
    - Seçilen Burun Kerteriz Noktası [958, 432] Takibi (Lucas-Kanade): Uç görüşler (v0 -> v11) arasında `dx = 0.0818 px, dy = 0.0184 px` (İleri-geri hata < 0.006 px; kerteriz noktası pratikte sabittir: `stable = true`).
    - Geniş Yüz Yaması Şablon Eşleşmesi (~150x186 px): 8 px kayma. Bu ham ölçüm kerteriz noktasının hareketi olmayıp, yanak ve yüz konturlarındaki 3D derinlik rölyefinin 10° perspektif altında şablon korelasyon kaymasıdır. Bu ölçüme dayanarak kareler kaydırılmamalı veya açı daraltılmamalıdır.
- **Üretilen Yeni Baskı Panelleri (1200 PPI, Faz=0.0, sRGB ICC Gömülü, Genişlik <= 13 cm / 6141 px):**
  - **50.20 LPI:** [`vd_belirgin_derinlik_20261012/50_20lpi/panel_50_20lpi_belirgin_phase0.tif`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/vd_belirgin_derinlik_20261012/50_20lpi/panel_50_20lpi_belirgin_phase0.tif) (6141 × 10163 px, 1.992 piksel/kanal).
  - **75.0 LPI:** [`vd_belirgin_derinlik_20261012/75lpi/panel_75lpi_belirgin_phase0.tif`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/vd_belirgin_derinlik_20261012/75lpi/panel_75lpi_belirgin_phase0.tif) (6141 × 10163 px, 1.333 piksel/kanal).
  - **100.0 LPI:** [`vd_belirgin_derinlik_20261012/100lpi/panel_100lpi_belirgin_phase0.tif`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/vd_belirgin_derinlik_20261012/100lpi/panel_100lpi_belirgin_phase0.tif) (6141 × 10163 px, 1.000 piksel/kanal).
- **Üretilen Karşılaştırma ve İnceleme Çıktıları:**
  - 2-Panelli Animasyon (Eski 50.20 C 6° vs Yeni 10°): [`karsilastirma_hareketli_eski50c_vs_yeni10deg.png`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/vd_belirgin_derinlik_20261012/karsilastirma_hareketli_eski50c_vs_yeni10deg.png) & `.gif`.
  - 4-Panelli Senkronize Animasyon (Eski 50C vs 75C vs 100C vs Yeni 10°): [`karsilastirma_hareketli_eski_vs_yeni_4panel.png`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/vd_belirgin_derinlik_20261012/karsilastirma_hareketli_eski_vs_yeni_4panel.png) & `.gif`.
  - Statik Orta Görüş: [`karsilastirma_statik_orta_gorunus.jpg`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/vd_belirgin_derinlik_20261012/karsilastirma_statik_orta_gorunus.jpg).
  - Detay Kırpılmış Kusur Panosu: [`karsilastirma_detay_kirpilmis_kusurlar.jpg`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/vd_belirgin_derinlik_20261012/karsilastirma_detay_kirpilmis_kusurlar.jpg).
- **Durum:** `rendered_and_verified_digital: true`, `physical_3d_verified: false`.

### 4.5 Doğal Hacim ve Bölgesel Düzenleme Denemesi (10° Açı, %2.8 Ön / %6 Arka Paralaks, Nr=12, Ne=12)
Kullanıcının gerçek fiziksel baskı incelemesinde *"El biraz daha geride olabilir. Sadece el dışarı çıkmış, o da gereğinden fazla. Yüz hatları, parmaklar ve kıyafet detayları derinlikli değil. İstenen sonuç, yalnız öne çıkan bir nesne değil; doğal hacimli, gerçekçi bir 3D görüntü."* geri bildirimi üzerine üretilen bölgesel hacim odaklı denemedir.

- **Bölgesel Düzenleme Mühendisliği (`prepared_depth/depth_dogal_hacim.npy`):**
  - **Öne Uzanan El:** Baskı düzlemine göre hareketi tam %30 azaltıldı (ön uç disparite -74.88 px'den -52.42 px'e çekildi). Avuç ve parmaklar düzleştirilmedi; 1.0 tavan kırpılması (plateau clipping) önlenerek başparmak, avuç içi ve parmak eklemlerine yuvarlak silindirik kesit formu verildi.
  - **Yüz ve Kafa Hacmi:** Burun kerteriz noktası `[958, 432]` sıfır düzleminde (0.00 px) sabit kilitli tutuldu (Lucas-Kanade drift 0.0000 px). Burun köprüsü, göz çukurları, yanaklar, alın, dudaklar ve çene anatomik konturları %70 kabartıldı (rölyef 0.0427'den 0.0726'ya yükseltildi; 1.70x kazanç).
  - **Gövde ve Kıyafet Hacmi:** Göğüs ve karına fıçı kavisi eklendi. Kumaş rengi/deseni çukurlaştırmadan (bilateral + bant geçiren filtre ile) gerçek kumaş döküm ve kıvrımları derinliğe aktarıldı (yüzey gradyanı 3.58x güçlendirildi).
- **Ortak Render Parametreleri:**
  - $N_r = 12$, $N_e = 12$, Açı = 10.0°, Ön Paralaks = %2.8, Arka Paralaks = %6.0, Azami Paralaks = %6.0, `edge_guard = false`.
  - Normalizer Trap Çözümü: `depth_curve = "balanced"` algoritması tepe noktayı normalize ettiği için ön paralaks %2.8'e kalibre edilerek matematiksel %30 azaltma garantilendi.
  - Render Klasörü: [`vd_dogal_hacim_20261012/shared_render_12/`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/vd_dogal_hacim_20261012/shared_render_12)
  - Boşluk Oranı: %0.00 (`max_nonopaque_fraction = 0.0`).
- **Üretilen Yeni Baskı Panelleri (1200 PPI, Faz=0.0, sRGB ICC Gömülü, Genişlik <= 13 cm / 6141 px):**
  - **50.20 LPI:** [`vd_dogal_hacim_20261012/50_20lpi/panel_50_20lpi_dogal_hacim_phase0.tif`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/vd_dogal_hacim_20261012/50_20lpi/panel_50_20lpi_dogal_hacim_phase0.tif)
  - **75.0 LPI:** [`vd_dogal_hacim_20261012/75lpi/panel_75lpi_dogal_hacim_phase0.tif`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/vd_dogal_hacim_20261012/75lpi/panel_75lpi_dogal_hacim_phase0.tif)
  - **100.0 LPI:** [`vd_dogal_hacim_20261012/100lpi/panel_100lpi_dogal_hacim_phase0.tif`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/vd_dogal_hacim_20261012/100lpi/panel_100lpi_dogal_hacim_phase0.tif)
- **Üretilen Karşılaştırma ve İnceleme Çıktıları:**
  - 4-Bölgeli Detaylı Senkronize Animasyon (Tam Kadraj, Yüz Yakın Çekim, El Yakın Çekim, Kıyafet Yakın Çekim): [`vd_dogal_hacim_20261012/karsilastirma_hareketli_4bolgeli_preview.gif`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/vd_dogal_hacim_20261012/karsilastirma_hareketli_4bolgeli_preview.gif) & `.png`.
- **Durum:** `rendered_and_verified_digital: true`, `physical_3d_verified: false`.

---

## 5. Hata Çözümleri ve Doğrulanmış Dersler

Proje sürecinde tespit edilen ve doğrulanmış çözümleri geliştirilen dersler ([`knowledge/lessons.jsonl`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/knowledge/lessons.jsonl)):

### 5.1 Ham TIFF Birleştirmede ICC Kaybı (`icc-assembly`)
- **Neden:** `numpy.concatenate` ile piksel dizileri birleştirilip standart TIFF kaydedicide yazıldığında panel dosyalarında bulunan gömülü ICC profili kayboluyordu.
- **Çözüm:** Interlace panel TIFF'inden ICC etiket baytları (Tag 34675) doğrudan okundu. Birleştirilen büyük TIFF yazılırken `extratags=[(34675, 'B', len(icc), icc, True)]` ile profil korundu.
- **Ders:** ICC profillerini karşılaştırırken dosya oluşturma zaman damgası (byte 12-23) dışarıda bırakılarak profil kimliği teyit edilmelidir.

### 5.2 Küçültülmüş Interlace'ten Hatalı Önizleme Üretimi (`preview-source`)
- **Neden:** Interlace edilmiş TIFF dosyasını küçülterek önizleme JPG veya animasyon yapmak optik lens etkisi vermez; aksine şerit örtüşmesi (moiré) ve piksel kırılması üretir.
- **Çözüm:** Statik ve hareketli önizlemeler doğrudan Blender renderı alınan temiz kamera görüş karelerinden (`views/view_*.png`) üretildi.
- **Ders:** Görsel değerlendirme yalnız temiz kamera kareleriyle yapılır; interlace TIFF asla stereo önizleme kaynağı değildir.

### 5.3 Salt Dosya Varlığına Dayalı Önbellek Yanılgısı (`cache-identity`)
- **Neden:** `execute_vd_plan.py` içinde `path.exists()` ile yapılan önbellek kontrolleri, kaynak dosya veya parametreler değiştiğinde eski dosyaları sessizce devralıyordu.
- **Çözüm:** Önbellek geçerliliği kaynak SHA256, model sürümü, render parametreleri ve motor hash'lerini içeren deterministik manifest karşılaştırmasına bağlandı.

### 5.4 Çoklu Varyant Manifest Çakışması ve Hatalı Quality Yolu (`render-manifest-collision-and-quality-path`)
- **Neden:** `execute_lens_plan.py` içinde A, B ve C varyantları aynı `render_output.parent / "render_manifest.json"` dosyasına yazıyor ve birbirinin üzerine yazıyordu. Ayrıca `check_render_cached` fonksiyonu olmayan `quality.json` yolunu arıyordu (gerçek dosyalar `quality_A.json`, `quality_B.json`, `quality_C.json`).
- **Çözüm:** Manifest yolu varyantın kendi klasörüne alındı (`render_output / "render_manifest.json"`). `check_render_cached` fonksiyonuna `var_code` parametresi eklenerek `quality_{var_code}.json` denetimi sağlandı. 6 varyantın manifestleri migrate edildi.

### 5.5 Çift Detaylandırma Riski (`prepared-depth-already-detailed`)
- **Neden:** `prepared_depth/depth.npy` oluşturulurken `detail_strength=0.8` zaten uygulanmıştır. Render sırasında `detail_depth` modülünü tekrar çalıştırmak yüzeyi yapaylaştırır.
- **Çözüm:** Hazırlanmış derinlik haritası doğrudan kullanıldı, yeni LPI denemelerinde yeniden AI detaylandırma işletilmedi.

### 5.6 Muhafazakâr Paralaks Bütçesi ve İstenen Görsel Etki Dersi (`stronger-parallax-review`)
- **Geri Bildirim:** Kullanıcı önceki 3D etkisini zayıf buldu; aşırı muhafazakâr reçeteden şikâyet etti. Bu geri bildirimin ekranda mı fiziksel baskıda mı gözlendiği belirtilmedi; varsayım yapılmadı.
- **Mühendislik Tespiti:** Önceki lens planlayıcı, lentikül başına düşen kanal hareketini korumak amacıyla 75 LPI'de açı bütçesini 3.13°'ye, 100 LPI'de ise 1.67°'ye kadar düşürmüştü. Bu matematiksel güvenlik kısıtı ölçülmüş fiziksel lens kapasitesine dayanmıyordu ve kullanıcı algısında derinliğin düzleşmesine yol açtı.
- **Kalıcı Ders:**
  > “Önceki denemede dosya doğruluğu, boşluksuz render ve muhafazakâr örnekleme sınırları kontrol edildi; hedeflenen görsel derinlik yeterince değerlendirilmedi. 75/100 LPI’de hareket bütçesi, ölçülmüş lens kapasitesine dayanmadan fazla azaltıldı. Kullanıcı etkiyi zayıf buldu. Sonraki üretimlerde iç hacim ve istenen görsel etki ayrıca değerlendirilmelidir.”
- **Kısıt ve Uyarılar:** Daha yüksek açı (10°) ve paralaks (%6) girilmiş olması tek başına başarı sayılmaz. İki-piksel kuralı ve bir-lens-adımı uyarıları (p95 adım 50.20'de 1.05, 75'te 1.56, 100'de 2.08 lentikül) kaydedildi; bu güçlü reçete sanatsal bir denemedir ve fiziksel olarak doğrulanmış genel varsayılan kabul edilmemiştir.

### 5.7 Ölçüm Yöntemini Doğrulamadan Neden Üretmeme ve Dosya Doğruluğunu Görsel Kaliteyle Eşitlememe (`measurement-verification-and-quality`)
- **Neden:** 10° denemesinde geniş yüz bölgesi (~150x186 px) şablon eşleşmesinde tespit edilen 8 px kayma, seçilmiş burun kerteriz noktasının hareketi sanılarak "burun 8 px kaydı" şeklinde sunulmuştu. Bağımsız Lucas-Kanade nokta takibi yapıldığında seçilen burun kerterizinin [958, 432] yalnız 0.082 px kaydığı (ileri-geri hata < 0.006 px, geometrik sıfır düzlem disparitesi 0.0 px) kanıtlandı. 8 piksellik kayma, yanak ve yüz konturlarındaki 3D derinlik rölyefinin 10° perspektif açısı altındaki şablon korelasyon kaymasıdır.
- **Benzer Hata:** 187.2 piksel değeri sahnedeki disparite uç değerlerinin farkıdır (`112.32 - (-74.88)`); tek bir elin ölçülmüş hareketi değildir (ön plan mutlak hareketi 74.88 px, arka plan mutlak hareketi 112.32 px).
- **Kalıcı Ders:**
  > “Ölçüm yöntemini doğrulamadan neden açıklaması üretme; dosya doğruluğunu görsel kaliteyle eşitleme.”
  - Geniş yüz yaması şablon kaymasına dayanarak kareler kaydırılmamalı veya açı daraltılmamalıdır. Kerteriz takibi nokta bazlı (Lucas-Kanade) doğrulanmalıdır.
  - Bir dosyanın 1200 PPI, ICC gömülü ve sıfır boşluklu olması tek başına estetik veya algısal 3D kalitesini kanıtlamaz.
  - Ölçümün desteklemediği yüz/gövde hacim iddiaları kesin doğrular gibi sunulmamalıdır; derinlik rölyef aralığı geometrik paralaks bütçesini gösterir, anatomik hacim veya fiziksel kabartı kanıtı değildir.

### 5.8 Bölgesel Hacim Şekillendirmesi ve Tek Nesne Çıkıntısı Yanılgısı (`regional-volume-vs-protrusion`)
- **Fiziksel Gözlem / Sorun:** Kullanıcı gerçek baskıda elin gereğinden fazla dışarı fırladığını, yüz, parmak ve kıyafet detaylarının ise hacimsiz/düz kaldığını bildirdi. Genel paralaksı veya kamera açısını artırmak tek başına tüm sahneyi dengeli 3D yapmaz; yalnızca en öndeki nesneyi gözü yoracak derecede dışarı fırlatır (pop-out tuzağı).
- **Mühendislik Çözümü:**
  - Nesnenin sahne içindeki konumu (z düzlemi / paralaks bütçesi) ile nesnenin kendi iç şekli ve anatomik eğriliği (iç rölyef) birbirinden ayrıldı.
  - Elin mutlak hareketi %30 azaltılırken (`front_parallax_percent = 2.8%`, disparite -52.42 px), 1.0 tepe kırpılması önlenerek parmak ve avuç içine silindirik yuvarlaklık verildi.
  - Burun kerterizi sıfır düzleminde (0.00 px) sabit kilitlenerek yüz anatomik hatları 1.70x kabartıldı.
  - Gövdeye fıçı kavisi ve kumaş rengi/deseni yerine fiziksel kıvrımları derinliğe işleyen bilateral bant geçiren filtreleme uygulandı (3.58x eğim artışı).
  - Normalizer Trap: `depth_curve = "balanced"` algoritmasının ön plan tepe noktasına bölerek normalize ettiği keşfedildi; derinlikte el geriye çekildiğinde eğrinin bunu tekrar esnetmemesi için `front_parallax_percent` doğrudan %2.8 olarak hedeflendi.
- **Kalıcı Ders:**
  > “Tek nesnenin öne çıkması, bütün görüntünün doğal 3D hacim kazanması değildir. Nesnenin baskı düzlemine göre konumu ile yüzeyin iç şekli ayrı kontrol edilmelidir. Elin aşırı paralaksını azaltmak; yüz, parmak ve kıyafet hacmini düzleştirmeyi gerektirmez.”

---

## 6. Önbellek Geçersiz Kılma Matrisi

| Değişen Parametre | AI Derinlik Önbelleği | Render Önbelleği (`render_manifest.json`) | Baskı Önbelleği (`interlaced.tif`) | Açıklama |
| :--- | :---: | :---: | :---: | :--- |
| **Kaynak Fotoğraf Hash'i** | **GEÇERSİZ** | **GEÇERSİZ** | **GEÇERSİZ** | Kaynak değiştiğinde tüm zincir baştan üretilmelidir. |
| **AI Model / Derinlik Reçetesi** | **GEÇERSİZ** | **GEÇERSİZ** | **GEÇERSİZ** | Detay gücü veya derinlik motoru değişirse harita yenilenir. |
| **Kamera Açısı (`angle_deg`)** | *Geçerli* | **GEÇERSİZ** | **GEÇERSİZ** | Harita korunur; Blender renderı ve interlace yenilenir. |
| **Görüş Sayısı ($N_r$)** | *Geçerli* | **GEÇERSİZ** | **GEÇERSİZ** | Kamera sayısı değiştiğinde yeni render gerekir. |
| **Grid Boyutu / Katman / Onarım** | *Geçerli* | **GEÇERSİZ** | **GEÇERSİZ** | 3D mesh ve inpaint parametreleri renderi bozar. |
| **Lens LPI (nominal/effective)** | *Geçerli* | *Geçerli* | **GEÇERSİZ** | Açı ve $N_r$ aynıysa render korunur; yalnız interlace yenilenir. |
| **Baskı Fazı (`phase`)** | *Geçerli* | *Geçerli* | **GEÇERSİZ** | Render etkilenmez; panel veya sayfa fazı yeniden kodlanır. |
| **Baskı PPI / Ölçü / ICC** | *Geçerli* | *Geçerli* | **GEÇERSİZ** | Yalnız interlace ve TIFF çıktıları yeniden üretilir. |

---

## 7. Doğrulanmamış Fiziksel Parametreler ve Baskı Geri Bildirimi

Aşağıdaki değerler optik ve matematiksel planlama hedefleridir; **fiziksel baskı kalibrasyonu henüz tamamlanmamıştır**:

1. **Efektif Lens Pitch:**
   - 50.20 LPI, 75.0 LPI ve 100.0 LPI değerleri kullanıcının sağladığı nominal lens değerleridir (`pitch_verified = false`). Gerçek RIP baskısında termal genleşme veya RIP çözünürlüğü nedeniyle pitch test şeridiyle doğrulanmalıdır.
2. **Kanal Başına Raster Piksel Kapasitesi:**
   - 50.20 LPI'de 2.3904 piksel/kanal; 75 ve 100 LPI'de 2.0 piksel/kanal hesaplanmıştır (`raster_ppi_verified = false`). Bu bir başlangıç kuralıdır; lensin fiziksel optik ayırma gücünü kanıtlamaz.
3. **Lens Görüş Açısı ve İzleme Mesafesi:**
   - 30° lens açısı ve 500 mm izleme mesafesi yazılımın geçici geometrik varsayımlarıdır (`lens_angle_verified = false`).
4. **Arka Yüz UV Baskı / Beyaz Katman:**
   - Tüm çıktılarda `mirror = false` ve `white_underbase = false` ayarlanmıştır. Arka yüz baskı ve beyaz katman reçetesi fiziksel RIP profilinde ayrıca test edilmelidir.

> **Geri Bildirim Kaydı:** Gerçek baskı sonuçları kullanıcı tarafından gözlemlendiğinde [`knowledge/feedback-template.json`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/knowledge/feedback-template.json) şablonu kullanılarak kaydedilmelidir. Tek bir lens gözlemi tüm lenslerin varsayılanını değiştirmek için kullanılmamalıdır.

---

## 8. Deneyim ve Değişiklik Günlüğü

### [2026-10-11] 50.20 LPI Üçlü Varyant Üretimi ve Düzeltmeler
- **Amaç:** VD görseli için A (Normal, 3°), B (Artırılmış, 4.5°), C (Güçlü, 6°) varyantlarının üretimi.
- **Değişiklik:** `execute_vd_plan.py` ve `apply_vd_fixes.py` çalıştırıldı. ICC profili birleşik TIFF'e aktarıldı, temiz orta görüş JPG ve hareketli önizleme oluşturuldu.
- **Doğrulama Sonucu:** Dijital doğrulamalar başarılı (`verified_digital`).
- **Kanıt Dosyaları:** `karsilastirma_sayfasi_etiketli_1200ppi.tif`, `baski-notu.md`.

### [2026-10-11] 75 ve 100 LPI Çoklu Lens Planlaması ve Üretimi
- **Amaç:** Aynı kaynak ve burun referansıyla 75 LPI ($N_r=8$) ve 100 LPI ($N_r=6$) üçer varyantının üretimi.
- **Değişiklik:** `tools/lens_plan.py` ile parametrik plan oluşturuldu ([`plan.json`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/plans/vd-75-100-1200ppi-8af22b6a/plan.json)). `tools/execute_lens_plan.py` geliştirilerek tam kadraj renderlar, bağımsız/sayfa fazlı paneller ve birleşik sayfalar üretildi.
- **Doğrulama Sonucu:** C önizleme boşluk oranı %0.00, burun uç görüş kayması 0 px, 6 varyantın tamamı dijital olarak doğrulandı.
- **Kanıt Dosyaları:** [`knowledge/runs/vd-75-100-execution-20261011.json`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/knowledge/runs/vd-75-100-execution-20261011.json), `vd_75lpi/`, `vd_100lpi/`.

### [2026-10-12] Render Önbellek İzolasyonu ve Manifest Migrasyonu
- **Sorun:** A/B/C varyantları aynı `render_manifest.json` üzerine yazıyordu ve `check_render_cached` olmayan `quality.json` dosyasını arıyordu.
- **Değişiklik:** Manifestler varyant klasörlerine (`render_output / "render_manifest.json"`) taşındı. `quality_{var_code}.json` yolu bağlandı. `--check-cache-only` CLI seçeneği eklendi. Mevcut 6 varyantın parametreleri doğrulanarak manifestleri oluşturuldu.
- **Doğrulama Sonucu:** 6 varyantın tamamı geçerli önbellek olarak tanındı (True); açı, derinlik hash'i, görüş sayısı ve radius değişiklikleri önbellek tarafından başarıyla reddedildi (False).
- **Kanıt Dosyaları:** [`tools/execute_lens_plan.py`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/tools/execute_lens_plan.py), `vd_75lpi/render_A/render_manifest.json`, `vd_100lpi/render_A/render_manifest.json`.

### [2026-10-12] Yeni Belirgin Derinlik Denemesi (10° Açı, %4 Ön / %6 Arka Paralaks, Nr=12)
- **Sorun / Geri Bildirim:** Kullanıcı önceki denemedeki 3D etkisini zayıf buldu. Geri bildirimin ekranda mı fiziksel baskıda mı gözlendiği belirtilmedi.
- **Değişiklik:** `plans/vd-strong-50.20-75-100-20261012/strong-plan.json` planı uygulandı. `tools/execute_strong_trial.py` ile ortak 1024 px önizleme ve 12 görüşlük Blender renderı (`shared_render_12`, 1872x3098 tam kadraj) üretildi. Üç hedef lens (50.20, 75, 100 LPI) için bağımsız interlace panelleri kodlandı. 2-panelli ve 4-panelli hareketli karşılaştırmalar, statik orta görüş ve detay kırpılmış kusur panoları üretildi.
- **Kullanılan Ayarlar:** $N_r=12$, $N_e=12$, Açı = 10.0°, Ön Paralaks = %4.0, Arka = %6.0, `edge_guard=false`, Grid=1024, 4 Katman, Yarıçap=5, `advanced` onarım, 1200 PPI, Faz=0.0.
- **Doğrulama Sonucu:**
  - Render boşluk oranı: %0.00 (`max_nonopaque_fraction = 0.0`).
  - Burun stabilitesi: Kerteriz noktası [958, 432] Lucas-Kanade nokta takibiyle uç görüşler arasında dx=0.0818, dy=0.0184 px ile sabit doğrulanmıştır (`stable = true`, geometrik sıfır disparitesi 0.0 px). Geniş yüz yaması (~150x186 px) şablon eşleşmesindeki 8 px kayma ise kerterizin hareketi olmayıp çevre yüz konturlarındaki 3D rölyefin 10° perspektif altındaki korelasyon kaymasıdır.
  - Gerçekleşen Max Paralaks: %6.00, Disparite: `[-74.88, +112.32]` px (toplam sahne aralığı 187.2 px; tek el hareketi değildir).
  - Paneller: 50.20, 75 ve 100 LPI panellerinin üçünde de 6141x10163 px, 1200 PPI ve sRGB ICC profili (588 bayt) doğrulandı (`verified_digital`).
  - Fiziksel durum: Henüz fiziksel baskıda test edilmedi (`physical_3d_verified = false`).
- **Kanıt Dosyaları:**
  - Paneller: `vd_belirgin_derinlik_20261012/50_20lpi/panel_50_20lpi_belirgin_phase0.tif`, `75lpi/panel_75lpi_belirgin_phase0.tif`, `100lpi/panel_100lpi_belirgin_phase0.tif`.
  - Animasyonlar: `vd_belirgin_derinlik_20261012/karsilastirma_hareketli_eski50c_vs_yeni10deg.png` (.gif), `karsilastirma_hareketli_eski_vs_yeni_4panel.png` (.gif).
  - Görsel İnceleme: `vd_belirgin_derinlik_20261012/karsilastirma_statik_orta_gorunus.jpg`, `karsilastirma_detay_kirpilmis_kusurlar.jpg`.
  - Koşu Kaydı: [`knowledge/runs/vd-strong-execution-20261012.json`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/knowledge/runs/vd-strong-execution-20261012.json).
  - Bağımsız İnceleme: [`knowledge/reviews/strong-review-20261012.json`](file:///c:/Users/USER/Documents/lenticular%20bask%C4%B1/knowledge/reviews/strong-review-20261012.json).
- **Sonraki İşte Uygulanacak Ders:** 75/100 LPI'de lentikül hareketi bütçesini teorik olarak kısmak yerine görsel iç hacim ve kullanıcı beklentisi kontrol edilmelidir. Ölçüm yöntemi doğrulanmadan neden açıklaması üretilmemeli, dosya doğruluğu görsel kaliteyle eşitlenmemeli ve desteklenmeyen hacim iddialarında bulunulmamalıdır. Bu belirgin reçete fiziksel olarak doğrulanana kadar varsayılan kabul edilmemelidir.

### [2026-10-12] Kullanıcı Fiziksel Baskı Geri Bildirimi ve Doğal Hacim Üretimi

> **Sonraki inceleme bu reçeteyi geçersiz kıldı:** Kullanıcı parmak bozulması ve yüz/kıyafet/arka plan hacminin yine yetersiz kaldığını bildirdi. Aşağıdaki ifadeler önceki üretimin tarihsel kaydıdır; görsel veya fiziksel kalite onayı olarak kullanılmamalıdır. Güncel düzeltme ve kanıtlar en sondaki 100 LPI kaydındadır.
- **Fiziksel Gözlem / Geri Bildirim:** Kullanıcı fiziksel baskıda *"El biraz daha geride olabilir. Sadece el dışarı çıkmış, o da gereğinden fazla. Yüz hatları, parmaklar ve kıyafet detayları derinlikli değil. İstenen sonuç, yalnız öne çıkan bir nesne değil; doğal hacimli, gerçekçi bir 3D görüntü."* bildiriminde bulundu. Hangi LPI baskısının incelendiği belirtilmedi.
- **Değişiklik:** Genel açıyı artırmak yerine `tools/refine_regional_depth.py` ile bölgesel heykel düzenlemesi yapıldı:
  - `prepared_depth/depth_dogal_hacim.npy` üretildi.
  - Elin mutlak hareketi %30 azaltılarak ön uç disparite -52.42 px'e çekildi (`front_parallax_percent = 2.8%`).
  - El tavan kırpılması (1.0 düzlüğü) engellenerek parmak eklemleri ve avuç içine silindirik yuvarlaklık verildi.
  - Burun kerterizi [958, 432] sıfır düzleminde (0.00 px) sabit kilitli tutuldu (Lucas-Kanade drift 0.0000 px).
  - Yüz içi rölyefi 1.70x kabartıldı (alın, burun köprüsü, göz çukurları, yanaklar, dudaklar, çene).
  - Gövde fıçı kavisi ve kumaş drapeleri (bilateral bant geçiren filtreleme ile koyu kumaş dokusu çukurlaştırılmadan) eklendi (eğim artışı: 3.58x).
- **Üretim:** `plans/vd-dogal-hacim-20261012/plan.json` planlandı ve `tools/execute_dogal_hacim.py` ile yürütüldü.
  - Ortak 12-görüşlü Blender renderı (`shared_render_12/`, 1872x3098 tam kadraj) sıfır boşlukla üretildi.
  - 50.20, 75 ve 100 LPI için 3 bağımsız 1200 PPI TIFF panel (`panel_*lpi_dogal_hacim_phase0.tif`, ICC gömülü, genişlik <= 13 cm) kodlandı.
  - 4-bölgeli detaylı senkronize animasyonlar (`karsilastirma_hareketli_4bolgeli_preview.gif` ve tam çözünürlüklü versiyon) hazırlandı.
- **Kanıt Dosyaları:**
  - Paneller: `vd_dogal_hacim_20261012/50_20lpi/panel_50_20lpi_dogal_hacim_phase0.tif`, `75lpi/panel_75lpi_dogal_hacim_phase0.tif`, `100lpi/panel_100lpi_dogal_hacim_phase0.tif`.
  - Animasyonlar: `vd_dogal_hacim_20261012/karsilastirma_hareketli_4bolgeli_preview.gif`, `karsilastirma_hareketli_4bolgeli_dogal_hacim.gif`.
  - Plan ve Geri Bildirim: `plans/vd-dogal-hacim-20261012/plan.json`, `knowledge/feedback/physical-feedback-20261012.json`.
  - Koşu Kaydı: `knowledge/runs/vd-dogal-hacim-execution-20261012.json`.
- **Sonraki Adım:** Kullanıcının doğal hacimli yeni baskıları (50.20, 75, 100 LPI) fiziken inceleyip yüzey iç hacimleri ve el mesafesi dengesini değerlendirmesi.




### [2026-10-12] Codex — yalnız 100 LPI, tutarlı yüzeylerle yeniden üretim

- **Yeni kullanıcı kararı:** Önceki parmak bozuk ve fazla öndeydi; diğer bölgeler hacimsizdi. Yalnız 100 LPI istendi. Referans düzlemi burundan geriye alınabilir; burun az öne gelebilir. Bu izin bu işe aittir; eski burun sabit varsayımı bu işte uygulanmaz. Pitch ölçümü yoktur.
- **Kodda doğrulanan sorunlar:** Önceki `refine_regional_depth.py` arka planı değiştirmiyordu; parmak dikdörtgenlerinin bir kısmı gerçek parmak koordinatlarıyla uyuşmuyordu. Parlaklık gradyanından kumaş şekli çıkarımı güvenilir hacim ölçüsü değildir. Derinlik dilimleri parmak içinden geçebilir. Yeni önizlemede ayrıca gizli kıyafet yüzeyinin elin önüne çıktığı görüldü; alfa boşluğu sıfır olsa bile bu anatomik hatayı kaçırır.
- **Düzeltme:** `tools/codex_portrait_100.py` ve `vd_100lpi_codex_20261012/`. Orijinal fotoğraf ve AI derinlik önbelleği korundu. Gerçek siluetler, sürekli arka plan/zemin, tutarlı gövde ve bütün ön kol/el yüzeyi kullanıldı. Gizli gövde elden, gizli duvar kişiden geride tutuldu. Parlaklık kabartması yerine anatomik kavis ve sınırlandırılmış derinlik haritası artığı kullanıldı. El aşırı çıkışı azaltıldı; yüz, gövde ve arka plana ayrı derinlik verildi.
- **Ayarlar:** nominal 100 LPI; Nr=Ne=6; 1200 PPI; 129,9845×215,1168 mm; 4° sanal kamera; faz=0; dikey lens; aynalama/beyaz katman kapalı. Lens başına 12, kanal başına 2 raster piksel. LPI, fiziksel lens açısını belirlemez.
- **Dijital kanıt:** 6 farklı kare, bozuk parmak renklerinin giderilmesi, sıfır son saydamlık, tam sahne ve dört bölgenin uç görüş incelemesi, düşük ileri/geri hatalı nokta takibi. Burun −3,90 px, sol yanak +5,64 px, başparmak −8,88 px, gövde merkezi −3,94 px, sol duvar +34,76 px uç kare hareketi. Bir kıyafet takip penceresi parmak örtüşmesine girdiğinden kanıt olarak reddedildi. Zemin üzerindeki 7–11 tekil kısmi alfa pikseli RGB değiştirilmeden düzeltildi ve işlem ayrıca kaydedildi. TIFF 6141×10163 px, 1200 PPI, 588 bayt sRGB ICC; 30.705 örnek raster pikseli doğrulandı.
- **Kanıt dosyaları:** `knowledge/runs/vd-100lpi-codex-20261012.json`, `vd_100lpi_codex_20261012/quality-checks.json`, `analysis/scene-analysis.json`, `print/print-report.json`, `render-d5732201/alpha-finalization.json`.
- **Sonraki işlerde ders:** Sıfır boşluk, dosya varlığı ve doğru TIFF ölçüsü algılanan 3D kalite demek değildir. Tüm görüntü, siluet, katman örtüşmesi ve yerel iç hacim birlikte incelenmeli. Kaynak ve önbellek hash'leri doğrulanmalı; yalnız değişen geometri gerektiğinde üretilmeli. Tek fotoğraftan çıkarılan anatomik şekil tahmindir. Bu reçete yeni fiziksel baskı görülmeden başarılı optik varsayılan sayılmamalı. Lens/RIP/pitch doğrulanmadı; arka planın kanal adımı için geçiş/netlik riski sürer; `physical_3d_verified=false`.


### [2026-10-12] Aynı altı görüntüyle 75 ve 50,20 LPI şeritleme

- **Kullanıcı şartı:** Kamera açısını, 3D etki geometrisini ve derinlik haritasını değiştirme; aynı görüntüleri kullan; gereksiz işlem, tekrar veya deneme yapma.
- **Uygulama:** `tools/reinterlace_existing.py` mevcut `lenticular.printing.encode` motorunu kullandı. Önce doğrulanmış render iş/derinlik/kare hash'leri eşleştirildi. Yalnız `nominal_lpi` ve `effective_lpi` değiştirildi; Nr=Ne=6 ve kaynak sırası [5,4,3,2,1,0] korundu. AI/Blender başlatılmadı; geometri, kamera, sıfır düzlemi, maskeler ve hareketli önizleme değişmedi. Ek pitch sayfası üretilmedi. Her yeni TIFF bir kez kodlandı.
- **Çıktı:** `vd_75_50_20_codex_20261012/75lpi/interlaced.tif`, `50_2lpi/interlaced.tif`. Her ikisi 6141×10163 px, 1200 PPI, 588 bayt sRGB ICC ve aynı yaklaşık 13×21,51 cm ölçüde. Büyük TIFF'lerin hash'i üretim raporundan alındı; tekrar okunmadı.
- **Kontrol:** Aynı altı ayrı kaynak karesi ve aynı kanal sırası; yalnız LPI alanları farklı. Dosya boyut/çözünürlük/ICC ve 30.705 örnek raster pikseli kontrolü her iki dosyada geçti. Kanal başına 75 LPI'de 2,6667; 50,20 LPI'de 3,9841 raster piksel. 75 LPI'de kesirli şeritler farklı kanal raster paylarına neden olabilir; kullanıcının değişiklik yasağı doğrultusunda Ne/faz/örnekleme değiştirilmedi. Fiziksel lensin algılanan derinliğe etkisi dosya geometrisiyle aynı şey değildir; fiziksel onay yok.
- **Kanıt:** `knowledge/runs/vd-75-50-20-reinterlace-20261012.json`, `vd_75_50_20_codex_20261012/execution.json`, iki hedefin `print-report.json` ve `reuse-manifest.json` dosyaları.
- **Tekrar kullanım:** Aynı LPI ve aynı kimlikte mevcut baskıyı kullan. LPI değişimi tek başına yeniden açı, derinlik veya render hesabı gerektirmez. Kullanıcı aynı görüntüleri istiyorsa görüş/kanal sayısını lens başına otomatik değiştirme.


### [2026-10-12] Bilgisayar genelinde yalnız eski, kullanılmayan Lenticular içeriği temizliği

- **Yetki ve sınır:** Kullanıcı yalnız Lenticular dosyalarının temizliğini istedi; son 24 saatte oluşturulan/değiştirilen dosyalar ve ilgisiz içerikler korunacak. C: erişilebilir dosya adları tarandı; bağlantılar takip edilmedi. 137 erişim izni olmayan konuma dokunulmadı.
- **Sonuç:** 39.003 dosya, 44,097 GB (41,069 GiB) silindi. Önceden çöp kutusuna taşınmış Lenticular yedeği, yarım GGUF indirmesi, superseded eski VD deney varlıkları ve eski program deneme/ara çıktıları temizlendi. Küçük tarihi planlar/raporlar, belirsiz eski nihai baskılar ve uzmanlık bilgi veritabanı korundu.
- **Kritik koruma:** Son 24 saat verileri; kullanılan yazılım/.venv/.models/.deps; mevcut ortak derinlik; kaynak fotoğraf; `fullscene-20261009-135756/person-mask.png` (mevcut yardımcı tarafından okunuyor); güncel 100/75/50,20 LPI dosyaları ve aynı altı kamera karesi korunmuştur. Yaş tek başına kullanımdan düşme kanıtı değildir. Eski raporların işaret ettiği bazı deney görsel/render dosyaları artık yoktur; bu raporları geçerli render önbelleği sanma.
- **Doğrulama:** Tam yol silme listesi, yeniden zaman/boyut/reparse kontrolü ve dosya başına silme kaydı kullanıldı. Silinen bütün hedeflerin yokluğu, yakın tarihli dosyaların korunması ve yedi güncel render görüntüsünün hash'leri doğrulandı. Gereksiz TIFF hash'i, AI, Blender veya üretim testi çalıştırılmadı.
- **Kanıt:** `knowledge/runs/lenticular-cleanup-20261012.json`, `knowledge/cleanup-20261012/temizlik-raporu.md`, `deletion-log.jsonl`, `verification.json`.


### [2026-10-13] GIF ve gerçek TIFF kimliği kontrolü

Kullanıcı `vd_100lpi_codex_20261012/hareketli-onizleme.gif` ile baskıların aynı görünmediğini/aralığın yok gibi olduğunu bildirdi. GIF'in on karesi aynı altı kaynak görüşe ileri/geri sırayla eşleşti. 4° kamera aralığı korunmuş; üç gerçek TIFF'ten bağımsız sütun/kanal ve doğrudan OpenCV source sampling ile toplam 8.472 pikselde fark sıfır. Yeni üretim veya ayar değişikliği yok. Dosya adları artık `interlaced 100.tif`, `interlaced 75 .tif`, `interlaced 50.tif` (gerçek LPI 50,20).

GIF ölçüsünde burun yaklaşık 1 px, el 3 px, duvar 11 px hareket ediyor. Küçük GIF'teki kıyafet takibi yüksek ileri/geri hata nedeniyle kanıt olarak reddedildi. Dosya doğruluğu yeterli yüz/kıyafet hacmi veya fiziksel kalite kabulü değildir; kullanıcı beklentisini bu doğrulamayla geçersiz sayma. Gözlemin fiziksel baskı mı ekrandaki TIFF mi olduğu belirtilmediği için fiziksel neden uydurulmadı. Kanıt: `knowledge/reviews/gif-tiff-identity-20261013.json` ve `gif-tiff-kontrol-20261013.md`.


### [2026-10-13] 75 LPI görsel hacim reddi — kullanıcı sorusunu dosya kimliğine indirgeme

Kullanıcı Downloads/interlaced 75 .tif görüntüsünde istediği etkinin görünmediğini belirtti ve dosya eşleşmesinin sorusu olmadığını açıkça düzeltti. Doğrudan TIFF genel görünümü ve TIFF sütunlarından ayrılan uç kanallar görsel olarak incelendi: arka plan/kişi ayrımı var, ancak yüz ve gövde çoğunlukla düz önden fotoğraf görünümünde; istenen anatomik/kıyafet iç hacmi yeterince belirgin değil. Bu sonuç kullanıcı hedefi için başarılı kabul edilmemeli. El bozulmasını sınırlamak ile yüz/gövde iç hacmini güçlendirmek ayrı amaçlardır; yalnız LPI şeritlemesi kalite eksiğini çözmez. Dosya hash/piksel uyumunu yeniden anlatmak kullanıcının görsel eleştirisine cevap değildir. Hiçbir açı, derinlik veya baskı dosyası değiştirilmedi. Kanıt: knowledge/reviews/75lpi-download-20261013/review.json; geri bildirim: knowledge/feedback/75lpi-insufficient-visible-volume-20261013.json.

# VD / 75 ve 100 LPI üretim devri

Önce proje kökündeki AGENTS.md, knowledge/snapshot.md, verified-facts.json ve current-task.json oku. Güncel görev planı current-task.json içindedir. Plan ve altı analyzer raporu zaten hesaplandı; tarama veya aynı analizi tekrarlama. Eksik bilgi çıkarsa yalnız ilgili dosyayı oku.

## Amaç ve hazır veriler

Aynı VD fotoğrafından her lens için A Normal, B Artırılmış, C Güçlü karşılaştırması üret: toplam altı varyant, iki ayrı karşılaştırma sayfası. Her panel en fazla 13 cm; tam kadraj, burun referansı ve mevcut ayrıntılı derinlik aynı. 75 LPI ve 100 LPI sayfaları farklı lenslerle kullanılır. İki LPI'yi tek lens altında birleştirme.

Girdi `prepared_depth/depth.npy`, temel AI derinliği ile 0.8 ayrıntı gücünün ZATEN birleştirildiği haritadır. Yeniden ayrıntı ekleme ve AI tahmini çalıştırma. knowledge/depth-cache.json kimliğini doğrula. Kaynak/model/derinlik hash'i uyuşmazsa dur; sessizce yeni harita üretme. Bu harita her yeni render için yalnız editable_depth ile yeni ön/arka bütçeye düzenlenir.

Plan `variants[].render` ve `variants[].print` sözlükleri uygulamanın gerçek ayarlarıdır. Planın üst düzey alanları uygulama ayarı değildir. Çıkış klasörleri planda verilmiştir: vd_75lpi ve vd_100lpi. Mevcut 50,20 LPI çıktılarını değiştirme.

## Yeniden kullanılabilir yürütme

Asıl lenticular paketini kullan. Eski execute_vd_plan.py'yi `main()` olarak çalıştırma. Yordamlarını referans al; yalnız dar, plan dosyası kabul eden bir `tools/execute_lens_plan.py` adaptörü gerektiğinde yaz. Kullanımı `--plan <tam plan.json yolu>` olsun. Lens başına betik kopyalama. Adaptörün konumunu ve kullanımını verified-facts.json'a kanıtla ekle.

Eski yürütücüde giderilmesi gereken sabit varsayımlar:
- `view_0009.png` / `[0,4,9]` / sabit 10 kare yerine `Nr`, son indeks `Nr-1` ve orta indeks `(Nr-1)//2`. Nr çift olduğundan tam sıfır açılı kamera olmayabilir; orta kareyi mutlak sıfır diye etiketleme.
- Faz, LPI, açı, ön/arka bütçe, etiket ve ölçüler plan sözlüğünden alınmalı. Birleştirme sonrası ICC düşürülmemeli.
- Önbellek için dosya varlığı yeterli değildir. Planın render_cache_identity değerini manifest olarak sakla; bütün beklenen kareler ve quality/coverage raporu da bulunmalı. Başarısız/yarım iş yeniden kullanılmamalı.
- Baskı için tamamlanmış render kimliği ile bütün print ayarlarını eşleştir. LPI/Ne/faz/ICC değişmesi önceki TIFF'i geçersiz kılar; depth'i değil.

Her lensin C varyantında 1024 uzun kenar / 512 mesh önizleme ile yeni açı/onarım kontrolü yap; mevcut geçerli aynı önizleme varsa yeniden üretme. Uygunsa ortak hazır depth'ten yeni Nr ve açılarla üç nihai renderi üret. Nihai uzun kenar 0, mesh 1024. RENDER_ENGINE_VERSION ve ilgili motor hash'leri manifestte yer alsın.

## Baskı ve kontrol

Lens başına 6141 × 10163 piksel paneller ve 18423 × 10163 piksel birleşik resim alanı, 1200 PPI. Etiket için altta 6 mm eklenebilir. Görüş sayısı 75 LPI için 8, 100 LPI için 6. Planın source_indices seçimi kadar ayrı gerçek kare bulunmalı; tekrarlanan veya interpolasyonla doldurulmuş kamera kareleri kullanma.

Tek lens altında boşluksuz üç panelde planın sheet_phase değerleri: 75 LPI A/B/C = 0 / 0.8125 / 0.625; 100 LPI = 0 / 0.75 / 0.5. Bunlar dikey lens, tilt=0, mirror=false, bleed=0 ve 6141 piksel panel eni içindir. Bağımsız paneller ayrıca phase=0 olarak kodlanır. ICC korunur; profiller yalnız tarih alanında farklıysa renk tanımı aynı kabul edilebilir. %100 ölçekte baskı, otomatik sığdırma kapalı.

Her lens için temiz yan yana orta görüş JPG'si ve aynı NORMALİZE kamera adımında A/B/C'yi ilerleten hareketli önizleme hazırla. 75 ve 100 farklı görüş sayılarıdır; aynı fiziksel kamera açısına sahipmiş gibi karıştırma. İnterlaced TIFF'i küçülterek görsel kalite önizlemesi yapma.

Burun sabitliği, el/saç/bitki/bacak arası kenarlar, boşluklar, gerçekleşen açı, ön/arka hareket, kanal seçimi, TIFF ölçü/PPI/ICC ve sayfa fazı kontrol edilsin. Raporu var olan yanlış sabit tablolarla oluşturma. Tam test paketi veya ilgisiz kaynak taraması yapma.

## İş sonunda öğrenme kaydı

knowledge/runs/ altında her lens için giriş kimliği, ayarlar, durum, çıktı yolları ve dar doğrulama sonuçlarını kaydet; current-task ve kısa snapshot'ı güncelle. Yeni bir hata çözüldüyse lessons.jsonl'a kanıtlı tek kayıt ekle. Aynı ders veya başarılı üretim tekrar araştırılmasın.

Nominal 75/100 LPI kalibre edilmiş effective pitch değildir. Yeni sayfalarda pitch/raster/lens açısı doğrulama işaretleri false kalır. Gerçek baskı sonuçları kullanıcıdan geldiğinde feedback-template.json şemasıyla kaydet; deneysel ayarları bütün projeye doğrulanmış varsayılan yapma.

Teslim: lens başına üç bağımsız panel, tek lens fazlarıyla etiketli karşılaştırma TIFF'i, temiz sabit/hareketli önizleme, quality/print raporları, plan kopyası ve kısa baskı notu. Üretim veya kontrol başarısızsa tamamlandı deme; kısa kanıtla dur.

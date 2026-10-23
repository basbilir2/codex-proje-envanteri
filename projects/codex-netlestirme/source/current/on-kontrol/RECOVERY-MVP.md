# Design Recovery — 22 Ekim uygulama ve doğrulama

## Yapılan

- Mevcut Node/Python uygulaması incelendi. app.py / pipeline.py bu checkout'ta bulunmuyor.
- Model zinciri yerine görev odaklı `pipeline.mjs`, geometri ve değiştirilebilir Qwen adaptörü uygulandı.
- Homografi ile isteğe bağlı dört köşe düzeltmesi, kaynak yönü/sRGB, crop ve bozulmadan oran/padding eklendi.
- Yüzeyden kurtarma, düz tasarım onarımı ve fotoğraf restorasyonu ayrıldı. Kaynak fotoğrafına renk kilidi/fidelity puanı kullanılmıyor. quick API kaldırıldı.
- Teknik boyut/boş çıktı kontrolleri ve kalıcı recovery/export raporları eklendi; kalite kabulü otomatik verilmez.
- Motor başarısızsa filtreye düşmez. İptalde worker ve alt süreç kapanana kadar iş kilidi tutulur.
- Mevcut isteğe bağlı 2×/BiRefNet/fırça korunur. sRGB PNG/DPI/alpha dışa aktarma ayrı modüldür; 4K/8K yeniden örneklemeyi gerçek detay üretimi diye sunmaz.
- README, MIMARI, KAPSAM, DEVAM, kurulum yolu ve testler güncellendi.

## Gerçek kontroller

`npm test`: **14/14 GEÇTİ**. Kontroller homografi koordinatları, EXIF/kaynak, oran/padding, görev ve dosya bağlantıları, hata/boş/boyut reddi, fallback olmaması, iptal/süreç ağacı, PNG alpha/DPI ve gerçek HTTP kaydet/dışa aktarma/erişim sınırlarını kapsar. Son log `recovery-tests.txt`.

Test adaptörü kopyalama yapar ve `TEST-TRANSPORT-DOUBLE` diye kaydedilir. **Bu model çıkarımı veya kumaştan tasarım kurtarma başarısı değildir.** Test çıktıları geçici test alanında oluşturulup kaldırılır; kullanıcı kaynakları silinmez.

Tarayıcı kontrolü gerçek `app/inputs/mavi.jpeg` ile yapıldı: 738×1600 kaynak yüklendi; dört köşe seçildi; sağda 409×266 kaynak önizlemesi görüldü. `recovery-ui.png` kaynak önizlemesi kanıtıdır; üretilmiş veya düzleştirilmiş tasarım değildir. AI düğmesine basılmadı. Tarayıcıda yüksek çözünürlüklü export düğmesiyle gerçek model çıktısı kabul testi yapılmadı; export HTTP ve piksel testleriyle doğrulandı.

Python işçisinin komut arayüzü ve kurulum betiğinin sözdizimi kontrol edildi. Kurulu 4 Qwen ağırlığı + Lightning için mevcut SHA256 makbuzunun boyut, mtime ve manifest eşleşmesi geçti; büyük dosyalar tekrar hash edilmedi. Yeni PC kurulumu veya model indirme yapılmadı.

## Çalışma adresi

Yeni sürüm: http://127.0.0.1:17863/ . Önceki 17861 servisi durdurulup yeniden başlatılmak istendi; otomatik onay denetimi işlemi engelledi, ayrıntılı gerekçe sağlamadı. Daha güvenli işlem olarak eski süreç korundu, yeni servis ayrı portta açıldı. Servis terminal oturum kimliği: 29846; portun canlı olması ayrıca doğrulanır. Başlat kısayolu yeni portu kullanır.

## Açık kabul engelleri

Yeni design recovery görevi için **ÇALIŞTIRILMADI**. Önceki yerel Qwen 4-adım denemesi 304,25 saniyede çıktı vermedi; bu mimari değişikliği hız sorununu gidermedi. Önceki GPU sonuçları restorasyon görevidir ve yeni kurtarma başarısı sayılmaz.

Otomatik güvenilir tasarım yerelleştirme, OCR/logo/kimlik/gerçek renk değerlendirmesi, kumaş deformasyon haritası ve yüksek ayrıntılı gerçek 4K/8K üretim yoktur. Semantik koruma/yüzey temizliği şimdilik model talimatıdır, doğrulanmış sonuç değildir. Gerektiğinde alpha ince çizgi veya beyaz dolgu kaybı ayrıca kontrol edilmeli. CMYK/ICC, fiziksel baskı ve dağıtım paketi kabulü açık.

Ücretli kaynak veya API açılmadı; model indirme/eğitim yok. Ürün kabulü false ve enhancementReady false korunur. Tam çalışan ve hedef kaliteyi karşılayan MVP teslimi henüz sağlanmadı; bu turun teslimi test edilmiş yazılım altyapısı ve açık eksik listesidir.

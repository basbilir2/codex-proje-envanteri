# Kullanıcı isteğiyle aşamalı düzenleyici — 22 Ekim 2026

- Kullanıcının başarısız işi `bed2de0b-18e1-4aef-b4cc-63fb5d6d46a2`: Vulkan `ErrorOutOfDeviceMemory`, 832×1248 / 4-adım; 180,28 saniyede çıktı yok. Sorun yalnız önizleme değildi; büyük model görüntü üretememişti.
- Yeni varsayılan ilk aşama aynı boyutta hızlı Sharp netleştirmedir. Üretken AI olduğu iddia edilmez; indirme/büyük model/otomatik 2× yok. Önceki Qwen ana düğmeden çıkarılıp açıkça işaretli ileri denemeye alındı.
- Tasarım alanı doğal görsel koordinatlarında isteğe bağlı dikdörtgen olarak seçilir; seçim yoksa tamamı işlenir. EXIF yönü düzeltilir, seçilen alanın gerçek piksel boyutu korunur. Geçersiz/sınır dışı seçim reddedilir.
- İsteğe bağlı 2×: mevcut kaynakta zaten kurulu UpscalerJS 1.0.0 / ESRGAN Slim 2× ve TFJS 4.11.0 yerel paketlendi. Önceki `enhance-fidelity` koruması ve alpha işleme kullanıldı; webden çalışma zamanı/model isteği yok. Bu motor ChatGPT eşitliği kanıtı değildir.
- İşlem aşaması, varsa gerçek tamamlanan adım/parça yüzdesi ve geçen süre gösterilir. Bilinmeyen sürede sahte yüzde yok. Başarısız yeni işlem önceki sonucu silmez.
- Silgi, geri getirme, bellek sınırlı geri alma, kenar temizleme/isteğe bağlı 1px daraltma, şeffaf boşluk kırpma, yakınlaştırma ve parlaklık/kontrast eklendi. PNG son canvas piksellerinden indirilir; düzenlenmiş dosya iş klasörüne kaydedilir.
- Büyük Qwen için CPU'da ağırlık, grafik işlemede 1,2 GiB bütçe, CPU metin/VAE ve 512 uzun kenar önizlemesi ayarlandı. Ayrıntılı aşama akışı işçiden aktarılır; bellek/süre hatası ayrıştırılır. Bu yeni bellek ayarıyla tam Qwen çıkarımı tekrar yapılmadı; hız/kalite sorunu çözülmüş sayılmaz.

## Yalnız gerekli doğrulama

1. Gerçek HTTP bölge/çıktı/kayıt kontrolü: 160×180 bölge aynı boyutta PNG, yaklaşık 0,186 saniye; sınır dışı seçim reddedildi, kilit açık kaldı, kaynak SHA değişmedi (`workflow-check.json`).
2. Tarayıcıda gerçek sürükleme: 192×192 kaynaktan 97×97 bölge seçildi; hızlı sonuç gösterildi. Ayrı 2× işlem 194×194 gerçek çıktı üretti; ekranda tamamlanma yaklaşık 2 saniye.
3. Fırça kontrolünde geri getirme antialias sorunu bulundu ve `copy` birleştirmesiyle düzeltildi. Yeniden yapılan yalnız fırça kontrolü: merkez alpha silgide 0, geri getirmede 255, geri almada yeniden 0 (`editor-check.json`, `v2-*`). 2× modeli yeniden çalıştırılmadı.
4. Aynı küçük görselde arka plan/kenar/ton adımları ve PNG indirme tamamlandı. Son 97×97 PNG'de 2344 tam şeffaf piksel, merkez alpha 255. Gerçek indirilen dosya `editor-download.png`; ekran `editor-v2.png`.

RunPod açılmadı. Büyük model yeniden denenmedi. Eski DTF kaynakları değiştirilmedi; yalnız ilgili modüller buraya alındı. ChatGPT kalite/hız kabulü hâlâ verilmiş değildir.

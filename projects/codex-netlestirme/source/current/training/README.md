# Qwen 2511 — sınırlı tasarım kurtarma uyarlama pilotu

Hedef: bulut çıkarımındaki koyu dolgu kaybı ve küçük yazı atlamasını azaltıp azaltamayacağımızı tek küçük LoRA pilotuyla sınamak. Bu bir genel eğitim korpusu veya bitmiş ürün değildir.

## Güncel kapanış

Son gerçek sonuç `pilot-20261022/validation-20261022/SONUC.md`. Eğitim 48 adım tamamlandı; son 236 MB adaptör yerelde hash doğrulandı. Önbellek/checkpoint ve 2511 görsel-listesi conditioning düzeltmeleri gerçek GPU'da çalıştı. Mavi ana tasarımı temiz ayrılıyor, koyu dolgu korunuyor; EST.1991 atlandığı için kalite **GEÇMEDİ**. Karşılaştırmada üç ham çıktı var; son SOLAR-LoRA dosyası alınamadı ve açıkça doğrulanmadı etiketli. Giriş düzeltmesinin etkisi temel modelde de görüldü; tamamı LoRA kazancı değildir. Eski tek-Image 48-adım çalışma ayrı `single-input-v1/` arşivindedir. Paket mevcut liste sözleşmesiyle yeniden oluşturuldu.

Son kontrol GPU'yu kapalı, bütün oranları PRIVATE_AMOUNT/saat gösterdi; bakiye PRIVATE_AMOUNT, oturum farkı PRIVATE_AMOUNT. Kapanış kontrolü gecikti, 60 dakika hedefi doğrulanmadı. Sonraki ücretli kaynak öncesi sağlayıcı düzeyinde GPU zamanlı kapanışı güvenceye alınmalı; işlem `timeout` komutu GPU faturasını durdurmaz. Aşağıdaki önceki durumlar tarihseldir; yeni deneme için bunları tekrar etme.

## Son gerçek durum — 22 Ekim

Son devam girişiminde mevcut A40 başlatma/taşıma ve aynı A40 için yeni sunucu isteği kapasite yok yanıtı aldı. Yeni pod veya eğitim başlamadı; yeni harcama yok. Görünen bakiye PRIVATE_AMOUNT. `corrected-validation-attempt.json` ve `capacity-blocked.png` kayıtları bu sonraki girişime aittir. `cloud-pilot.zip` artık düzeltilmiş mevcut kaynaklardan yeniden paketlenmiştir; önceki arşiv uyarısı bu güncel paket için geçersizdir.

Veri ve safetensors ağırlıkları A40 buluta aktarıldı; altı örneğin ön işlemesi tamamlandı. İlk yüklemedeki Transformers 5 uyumsuzluğu `transformers==4.57.1`, `peft==0.17.1` ile giderildi. Eğitim ilk forward sırasında CUDA bellek hatası verdi; **0/48 optimizer adımı, checkpoint yok**, dolayısıyla adaptörlü kalite karşılaştırması yapılmadı. RAM'e checkpoint offload eklenmesi de aynı hatayla durdu. Rastgele parametre/model taraması yapılmadı.

GPU kapandıktan sonra stack trace ve sabit upstream kodundan neden bulundu: ön işleme `inputs_shared` içine checkpoint bayraklarını `False` kaydetmişti; `sft:train`, önbellekteki bu değerleri komut satırındaki eğitim ayarlarıyla değiştirmiyor. Çağrı doğrudan checkpoint fonksiyonunun kapalı dalına giriyordu. Bu nedenle sonuç A40'ın düzeltilmiş eğitim için yetersiz olduğunu kanıtlamaz. Başlatıcıda bayraklar hem ön işlem hem eğitim ortak ayarına taşındı; eski bayraklarla önbelleği yeniden kullanma reddedilir. **Bu son düzeltme bulutta doğrulanmadı.** Sonraki çalışmada önbellek yeniden üretilmeli; yeni GPU açılmadan kayıtlı kanıt kullanılmalı.

Görünen bakiye 10,24 → PRIVATE_AMOUNT (PRIVATE_AMOUNT fark); aktif oran PRIVATE_AMOUNT/saat. `pilot-20261022/SONUC.md`, `evidence/` ve `gpu-stopped.png` gerçek kanıtlardır. Güncel kaynaklar düzeltmeyi içerir; arşiv `cloud-pilot.zip` çalıştırılan ilk sürümdür, güncel başlatıcı yerine kullanılmamalıdır.

## Veri

`pilot-20261022/` içinde 8 farklı tasarımın temiz hedef/yüzeyli kaynak çifti var. İlk 6 tasarım eğitim, son 2 tasarım değerlendirme içindir. Mavi kaynak ve onaylı ChatGPT referansı eğitime dahil edilmez. Mavi dosyası yalnız `holdout-mavi.jpeg` değerlendirme girdisidir; eğitim metadata'sında geçmez.

Bütün temiz tasarımlar ve bozulmuş eşler yerleşik `image_gen` aracıyla üretildi. Kaynak eşlerinde kumaş, kıvrım, ışık, yüzey veya perspektif değiştirildi; yazı, temel şekil ve dolgu kimliği görsel olarak kontrol edildi. Sentetik eşler piksel hizalı fiziksel gerçeklik değildir; üretken modelin küçük şekil/renk sapmaları bulunabilir. Bu sınırlama değerlendirmede ayrıca dikkate alınır.

`pilot-assets.json` her tasarımın kaynak üretim dosyasını, metnini, özelliğini ve ayrımını kaydeder. `manifest.json` SHA256 ve boyutları içerir. `train.json` ve `validation.json`, resmi DiffSynth sözleşmesiyle `image` (temiz hedef), `edit_image` (yüzeyli kaynak), `prompt` alanlarıdır. Bütün örneklerde aynı genel kurtarma talimatı kullanılır; beklenen kelimeler modele ayrı ipucu olarak verilmez.

`package-pilot.mjs` yalnız dosya kopyalar, hash/boyut kontrolü yapar, metadata yazar ve değişmeyen görüntüleri etiketli bir inceleme sayfasında gösterir. Eğitim görüntülerine kodla doku, kıvrım, gölge, dolgu veya rötuş uygulanmaz. `review.png` yalnız sunum içindir, eğitim dosyası değildir.

## Üretim talimatları

Temiz hedefler için kullanılan talimat setinin ortak yapısı: özgün, düz baskı tasarımı; açık nötr gri gösterim zemini; belirtilen tam metinler ve dolu renkler; açık iç boşluklar; keskin ince konturlar; kumaş/gölge/ek yazı bulunmaması. Tasarıma özel metin, renk ve bileşenler `pilot-assets.json` içindedir.

Yüzeyli eşler için ortak talimat: temiz görsel referans alınır; aynı harf biçimleri, küçük numaralar, dolgu ve kompozisyon korunarak doğrudan belirtilen yüzeye uygulanır. Gri arka levha kaldırılır; hafif kıvrım/perspektif/ışık ve fotoğraf bozulması eklenir. Yeni yazı veya simge eklenmez, iç dolgular delik yapılmaz. Son (08) eşin talimatı:

> Create the exact photographed surface partner of this River design for held-out evaluation. Preserve identical connected script letter shapes, deep blue opaque fills, thin white outlines, underline and exact small white text SINCE 1976. Apply as ink directly on a deep blue cotton shirt surface, replacing the gray backing entirely. Gentle folds, side lighting and slight perspective, mildly soft photo detail. Complete artwork and text visible with cloth margin, landscape 3:2 close-up, no person or extra marks. Do not make blue ink interiors transparent, redesign the script, change date numerals or add a backing rectangle.

## Eğitim yolu

GitHub kaynağı: [DiffSynth-Studio](https://github.com/modelscope/DiffSynth-Studio), sabit revision `d188f01d09013688dea27cc28f2e8dc0953c2543`. Resmi 2511 LoRA tarifi ve ön işleme önbelleği/FP8 örnekleri temel alındı. Upstream eğitim kodu değiştirilmez. `upstream/` ilgili kısa kaynakların kanıt kopyalarını tutar; bunlar yerel model çalıştırmaz.

`weights.json` safetensors eğitim ağırlıklarını sabit Hugging Face revision'larında belirtir. Transformer + metin kodlayıcı yaklaşık 53,5 GiB; VAE/tokenizer/processor ayrıca gerekir. Mevcut GGUF dosyası eğitim ağırlığı olarak kullanılmaz. Eğitim için en az 65 GiB boş disk, en az 40 GiB GPU belleği önkoşulu kondu; 100 GB geçici diskli A40 seçildi. Gerçek yeterlilik ancak pilot çalışınca doğrulanır.

Pilot: 6 örnek × 8 tekrar × 1 epoch = 48 optimizer adımı, LoRA rank 16, öğrenme oranı 1e-4, sabit seed 42, 768×512 hedef. Deterministik ön işleme 6 örnek için bir kez önbelleğe alınır. 24 ve 48. adım ağırlıkları kaydedilir. Eğitimin kendisi `sft:train` aşamasında gradient/optimizer güncellemeleridir; veri üretimi veya önbellekleme eğitim diye sunulmaz.

Eğitimden sonra aynı safetensors/FP8 temel model üzerinde aynı seed ve 40 adımla önce adaptörsüz, sonra LoRA ile iki karşılaştırma alınır: gerçek Mavi ve eğitimde kullanılmayan 07 numaralı tasarım. Böylece eski GGUF ile farklı runtime sonucu doğrudan eğitim başarısı diye sunulmaz. 08 numaralı ikinci değerlendirme tasarımı ayrıca saklıdır. Tek pilot; seed/öğrenme oranı/model taraması yok.

Bu pilotun oturum sınırı PRIVATE_AMOUNT ve 60 dakika; önceki toplam PRIVATE_AMOUNT sınırı ayrıca geçerli. Aktif ücret kaynak açarken doğrulanır. Kurulum/indirme, önbellek, eğitim ve değerlendirme zaman sınırları `pilot.json` içindedir; dış çalıştırıcı bütün oturumu sınırlar. Operatör GPU'yu bitince/başarısızlıkta kapatır ve son fiyat/bakiyeyi kaydeder. Scriptin bitmesi kendi başına RunPod faturasını durdurmaz.

## Dosyalar

- `cloud-setup.sh`: sabit GitHub kodu ve bağımlılık kurulumu; mevcut PyTorch ortamı kullanılır.
- `cloud-download.py`: yalnız gerekli, revision'ı sabit eğitim ağırlıkları.
- `cloud-pilot.py`: önbellek → 48 adım → kontrollü karşılaştırma; otomatik yeniden deneme yok.
- `seeded-train.py`: sabit seed ile upstream eğitim giriş noktası.
- `cloud-evaluate.py`: adaptörsüz/adaptörlü aynı koşullar; çıktıları ve süreleri kaydeder.
- `package-cloud.py`: yalnız bu pilotu buluta paketler; Mavi eğitim metadata'sına katılmaz.

Kaydedilmiş checkpoint, eğitim kaybının azalması veya sentetik görselde ilerleme genel kalite kabulü değildir. Dolgu, küçük yazı, tasarım biçimi ve gerçek kaynakta yüzeyden ayrılma ayrıca incelenir. Son üründeki PC hızı/ücretsiz çalışma şartları bu pilotla kendiliğinden sağlanmaz.

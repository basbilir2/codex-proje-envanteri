# Gerçek uygulama kontrolü — 22 Ekim 2026

**Ürün kabul edilmedi ve bitmiş proje değildir.** Yerel hız şartı sağlanmadı. Bulut sonuçları PC'de aynı hızın kanıtı değildir. Yeni ücretli kaynak veya otomatik tekrar başlatılmayacak.

## Hazırlanan yazılım

`app/` içinde Qwen Python işçisi, sabit checkpoint/revision/hash kaydı, doğrulamalı model indirme, yerel Node servisi ve iki düğmeli arayüz var. BiRefNet Lite 512, Transformers.js/ONNX WASM ve alpha/kenar kodu tamamen yerel dosyalardan çalışıyor. Eski DTF/Wix uygulaması değiştirilmedi. Model kurulumu kullanıcıya bırakılmadı.

Ana işlem PC'de gerekli hızı sağlayamadığı için `app/runtime-config.json` içindeki `enhancementReady=false`; servis gerçek kullanıma hazır olmayan ana işlemi başlatmaz. Kurulum/kısayol üretimi ve bitmiş ürün teslimi yapılmadı. Geliştirme sunucusu ve yerel model süreçleri kapatıldı.

## Gerekli kontroller ve kanıtlar

| Kontrol | Gerçek sonuç | Kanıt |
|---|---|---|
| PC / CPU, 512×1104, 40 adım | 537,35 saniyede çıktı yokken yavaş yol durduruldu. Tamamlanmış kalite testi değildir. | `app/jobs/local-first/result.json`, `.log` |
| PC / AMD Vulkan, aynı girdi ve boyut | 1201,38 saniyede zaman aşımı; 2/40 adım. Adımlar 474,71 ve 458,31 saniye. Çıktı yok. | `app/jobs/local-vulkan/result.json`, `.log` |
| PC / AMD Vulkan + Lightning, portre 512×512 / 4 adım | GPU'da 13,40 saniyede üretilen aynı işin son yerel kontrolü. 300 saniye sınırında zaman aşımı; kapanış dahil 304,25 saniye, çıktı yok. Tek deneme, tekrar yok. | `app/jobs/local-fast/result.json`, `.log` |
| A40 / Qwen temel, Mavi 512×1104 | Gerçek PNG, toplam 197,01 saniye. Netlik arttı; küçük tarih yazısı bozuldu. Bu düşük çıktı boyutu kabul edilmedi. | `on-kontrol/gpu-mavi.png`, `.json`, `.log` |
| A40 / Qwen temel, portre 192→512 | Gerçek PNG, toplam 91,62 saniye. Netlik arttı; yüz ve rozet ayrıntıları aslıyla birebir korunmadı. | `on-kontrol/gpu-portrait.png`, `.json`, `.log` |
| A40 / aynı portre + Lightning 4-adım | Gerçek PNG, toplam 13,40 saniye. Hızlandı; orijinale ayrıntı sadakati sorunu sürdü. | `on-kontrol/gpu-portrait-fast.png`, `.json`, `.log` |
| A40 / Mavi + Lightning, 768×1664 | Önceki küçük-yazı hatasına yönelik tek çözünürlük düzeltmesi. Gerçek PNG, toplam 39,11 saniye. Görsel kontrolde `EST.1991` düzeldi; bu tek sonuç genel kalite garantisi değildir. | `on-kontrol/gpu-mavi-fast-native.png`, `.json`, `.log` |
| PC / çevrimdışı BiRefNet 512×512 | Gerçek alpha PNG; 27,25 saniye. 120652 tam şeffaf, 139257 opak, 2235 ara alpha pikseli. Konu/saç/kenar görsel kontrolü yapıldı. Ölçüm sırasında Vulkan işi de açıktı; izole hız kıyası değildir. | `on-kontrol/portrait-alpha.png` |

Portre kontrolünde orijinali bilinen bağımsız bir girdi kullanıldı: scikit-image v0.25.2 `skimage/data/astronaut.png`; kaynak 512×512, bozulmuş girdi 192×192 ve JPEG kalite 45 + blur 0,7. Tam sahne karşılaştırması `on-kontrol/portre-karsilastirma.png` içinde. Kullanıcıya örnek hazırlama veya işaretleme işi verilmedi. Elle yazı/yüz düzeltme yapılmadı.

## Dar mimari düzeltmesi

Yerel standart 40-adım yolu çok yavaş kaldığından, aynı Qwen 2511 tabanına resmi LightX2V 4-adım LoRA eklendi. Model değişimi, Print Extraction veya eğitim yok. Kesin dosya/revision/SHA256 `app/models.json` içindedir; temel ağırlıkla hızlandırıcı iki kere birleştirilmedi. Son GPU çıktıları kaydedilip pod kapatıldıktan sonra hızlandırıcı da PC'ye hash doğrulamasıyla indirildi. Aynı 512×512 portre işi yalnız bir kez, beş dakika sınırıyla yerelde kontrol edildi; çıktı vermeden zaman aşımına uğradı. GPU başarısı yerel hız engelini çözmedi. Bu son kontrol ek bulut kaynağı veya harcama açmadı.

## Harcama ve kapanış

- Kullanıcının son toplam sınırı PRIVATE_AMOUNT; ek ödeme ve otomatik yükleme yok.
- Son görünen bakiye **PRIVATE_AMOUNT**; ilk PRIVATE_AMOUNT bakiyeye göre görünen fark **PRIVATE_AMOUNT**. Nihai fatura yerine panelin kapanış gözlemidir.
- Pod `farhpxgvyg704w` durduruldu. Panelde compute/container storage **Not running**, toplam **PRIVATE_AMOUNT/saat**, idle disk **PRIVATE_AMOUNT/saat** görüldü.
- Tüm gerçek çıktılar, işlem raporları/logları ve derlenen CUDA çalıştırıcısı kapatmadan önce yerel diske alındı. CUDA arşivi `on-kontrol/cuda-runtime.tar.gz`, bağımlılık listesi yanındadır; yeniden derlemek gerekmez.
- Kapanış ekranı: `on-kontrol/runpod-kapali.png`. Geliştirme Jupyter sekmesi ve yerel kontrol sekmesi kapatıldı. Kullanıcının diğer sekmelerine dokunulmadı.

## Devam özeti

**Amaç:** ChatGPT düzeyinde kalite/hızla, rutin RunPod/API gerektirmeden PC'de iki işlem.
**Tamamlanan:** kaynak bağlantıları, yerel model kurulumu, gerçek GPU çıktıları ve çevrimdışı alpha kanıtı.
**Engel:** seçilen Qwen motoru mevcut PC'de gereken hızı sağlamıyor; portrede kaynak ayrıntılarını tam koruma da doğrulanmadı.
**Değişen alan:** yalnız bu çalışma klasörü; eski DTF kaynakları salt okunur kullanıldı.
**Sonraki karar:** yerel hesaplama ve kaynak sadakati sorunu çözülmeden paketleme, yeni ücretli deneme veya tamamlandı iddiası yok. Aynı testleri tekrar çalıştırma; bu kanıtları kullan.

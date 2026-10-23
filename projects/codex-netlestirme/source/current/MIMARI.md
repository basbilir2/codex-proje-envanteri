# Design Recovery / Artwork Reconstruction mimarisi

22 Ekim 2026. Bu belge önceki model zinciri merkezli planın yerine geçer. Ürün hedefi fotoğrafı güzelleştirmek değil, fotoğrafın içindeki gerçek tasarımı kurtarmaktır. Mimari kodlandı; üretken tasarım kurtarma kalitesi henüz kabul edilmedi.

## Sözleşme ve aşamalar

| Aşama | Uygulama | Sınır |
|---|---|---|
| Kaynak alımı | `inspectSource`, EXIF yönü, sRGB kopyası, değişmeyen orijinal ve SHA256 | Girdi 16 MP / 25 MB; otomatik nesne/tasarım tespiti yok |
| Tasarım alanı | Tam görsel varsayılan; isteğe bağlı dikdörtgen veya dört köşe | Kullanıcıya zorunlu örnek/metin hazırlığı verilmez |
| Geometri | `geometry.mjs`, konveks dörtgen doğrulama, homografi | Düzlemsel perspektif; kıvrım haritası veya bilinmeyen gerçek oran çıkarımı yok |
| Üretken kurtarma | `pipeline.mjs` → değiştirilebilir `engine.run` adaptörü | Yüzey, ışık, kıvrım, JPEG ve bozulan ayrıntıyı anlama eğitilmiş modele bağlı |
| Görev ayrımı | `extract-design`, `repair-artwork`, `restore-image` | Düz tasarıma kumaş çıkarma, fotoğrafa yanlışlıkla tasarım ayırma uygulanmaz |
| Teknik kontrol | PNG çözme, boyut, tek renk/boş çıktı, süre/hata ve model sürüm kaydı | Metin, logo, yüz, gerçek renk veya yüzey temizliğini otomatik kabul etmez |
| Yardımcı işlemler | Ayrı 2×, BiRefNet, alpha/kenar ve geri alınabilir düzenleme | Reconstruction yerine geçmez; ana çıktı korunur |
| Dışa aktarma | sRGB PNG, alpha, DPI, 24 MP sınırı, gerçek üretim/büyütme ayrımı | `printReady=false`; CMYK/ICC ve fiziksel baskı kabulü yok |

Eski kaynak fotoğrafına COLOR_LOCK/histogram geri eşleme veya fotoğraf benzerliği puanı yoktur. Gölgeyi ve kumaşı geri basan karşılaştırma yapılmaz. Yeniden çalıştırma daima özgün kaynağı kullanır; üretilen hatalar tekrar girdiye katlanmaz. ESRGAN/BiRefNet otomatik zorunlu zincir değildir. `mode=quick` kurtarma API'sinde reddedilir.

## Üretken adaptör kararı

Mevcut Qwen-Image-Edit-2511 GGUF + sabit stable-diffusion.cpp, yeniden indirmeden kullanılan ilk adaptördür. Bu, yeni recovery kalitesinin kabul edildiği anlamına gelmez. Resmi Qwen model kartındaki düzenleme/tutarlılık/geometri yetenekleri görev için değerlendirme gerekçesidir; kumaştan hatasız tasarım çıkarma kanıtı değildir. Adaptör başarısızsa iş başarısız biter; gizli filtre, başka model, rastgele seed taraması veya bulut çağrısı yoktur.

`engine.run({dir, task, width, height, signal, progress})` gerçek `reconstructed.png` ve tamamlanmış motor kaydı üretmelidir. Çekirdek model ismine bağlı değildir. Adaptör çıktısı teknik olarak doğrulanır; anlamsal başarı ayrı kabul şartıdır. Model/runtime revision, ağırlık hashleri, prompt, accelerator, seed, adım, boyut ve süre motor kaydındadır. Ağırlıkların doğrulama makbuzları boyut/mtime/sabit hash ile kontrol edilir; değişmiş dosya sessiz kabul edilmez.

Yerel en fazla 512 uzun kenarlı üretim, 16 katına uydurulan boyutlarda oran korunarak padding alır; üretim sonrası padding kaldırılır. Orijinal görüntü en-boy oranı bu aşamada esnetilmez. Çok uzun/ince girdide gerçek içerik boyutu küçülür; raporda görünür. 4K/8K dışa aktarma eksik ayrıntıyı öğrenmez. Kaynak veya önceki üretilmiş ayrıntıyı kurtaran ayrı yüksek çözünürlük modeli bu tur eklenmedi.

## İş yönetimi ve dosyalar

Mevcut yerel Node servis/tarayıcı/Python omurgası korunur; ayrı Gradio/FastAPI uygulaması oluşturulmaz. Ağır işler tekildir. İptalde worker ve alt süreç ağacı kapanana kadar kilit tutulur. Kaynak, hazırlama, ham üretim, nihai PNG, log ve rapor ayrı saklanır. Rapor/çıktı yazımı geçici dosya + rename ile yapılır. Tamamlanmamış işin çıktı URL'si sunulmaz. Kesilmiş oturum işi yeniden açıldığında başarısız olarak işaretlenir; önceki tamamlanmış iş/çıktılar okunabilir.

Kurtarma raporu (`recovery.json`) ve dışa aktarma raporu (`export.json`) ayrıdır. Fırça/yardımcı değişiklikler düzenlenmiş kopyaya yazılır; ilk kurtarma raporu ham üretimi anlatır. Dışa aktarma düzenlenmiş girdinin SHA256'sını kaydeder. `completed` yalnız dosya/iş tamamlanmasıdır; `quality.status=unverified`, `printReady=false` kalır.

Servis yalnız localhost; POST işlemleri oturum token'ı ve aynı Origin gerektirir. Bulut/ücretli API çağrısı yoktur. Dosya sunumu izinli iş çıktılarıyla sınırlıdır. Kullanıcının diğer projeleri ve önceki canlı verileri değiştirilmez.

## Doğrulama ve ürün kabul kapısı

Yazılım testleri gerçek homografi/piksel, yön/oran, kaynak koruma, hatalı motor çıktısı, iptal/süreç ağacı, PNG/alpha ve HTTP sınırlarını kontrol eder. Adaptör veri akışı testleri `TEST-TRANSPORT-DOUBLE` kullanır; bunlar çıkarım veya model kalitesi sonucu değildir.

Ürün kabulü için yeni görevle gerçek üretim, geliştirmede kullanılmamış çeşitli girdilerde ChatGPT referansına göre yazı/rakam/logo/geometri/kimlik/renk ve yüzeyden ayrılma kontrolü gerekir. Tam sahne/genel yazılım hedefi birkaç örneğe indirgenmez. Sonrasında PC'de gerçek süre ve kaynak kullanımı, açık/koyu zeminde alpha ve fiziksel baskı/ICC gereksinimleri değerlendirilir. Elle düzeltme otomatik model başarısı sayılmaz. Önceki yerel hız başarısızlığı prompt veya mimari değişince kendiliğinden çözülmüş değildir.

Yeni görevle gerçek çıkarım yapılmadığından çalışan ve kalite hedefini karşılayan reconstruction MVP'si teslim edilmiş sayılmaz. Bu tur tamamlanan kapsam, çalıştırılabilir ve test edilmiş kurtarma yazılım iskeleti/bağlantılarıdır. Kritik eksikler `app/README.md` ve `on-kontrol/RECOVERY-MVP.md` içinde açıkça kayıtlıdır.

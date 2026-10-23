# Design Recovery / Artwork Reconstruction Engine

Bu sürümün ana işi, fotoğraf/mockup/yüzey içinde görünen tasarımı kurtarmaktır. Eski Qwen → renk kilidi → otomatik ESRGAN → fotoğraf benzerliği puanı → BiRefNet zinciri kullanılmaz. Bu çalışma klasöründe `app.py` veya `pipeline.py` bulunmadığı için mevcut Node servisi ve Python model adaptörü geliştirildi; ikinci bir uygulama kurulmadı.

## Durum

Güncel yeterlilik hedefi: kullanıcı `../outputs/mavi-karsilastirma-20261022/chatgpt-tasarim.png` dosyasının netliğini ve üretken yeniden oluşturmasını yeterli buldu. Bu artık somut onaylı görsel referansıdır; `../on-kontrol/approved-recovery-reference.json` kabul kapsamını ve hashleri tutar. Yazılımın aynı kaliteyi ürettiği henüz doğrulanmadı. Referans görüntü, yeni gelen kaynakların yerine çıktı olarak kullanılmaz ve yalnız Mavi'ye özel kod yazılmaz.

**Çalışan yazılım altyapısı; kalite kabulü yapılmış tasarım kurtarma ürünü değil.** Geometri, kaynak koruma, adaptör bağlantısı, iptal, teknik çıktı doğrulama, düzenleyici ve PNG dışa aktarma uygulanmıştır. Yeni kurtarma göreviyle gerçek Qwen çıktısı bu turda alınmadı. Önceki yerel 512×512 / 4-adım denemesi 304,25 saniyede çıktısız zaman aşımına uğradı. Önceki bulut sonuçları yeni tasarım kurtarma yeteneğinin kanıtı değildir.

## Akış

1. PNG/JPEG/WebP yüklenir; orijinal byte'lar ve SHA256 iş klasöründe saklanır. EXIF yönü düzeltilir, sRGB çalışma kopyası hazırlanır.
2. Alan seçmek isteğe bağlıdır. Dikdörtgen alan kırpılabilir veya sol üst → sağ üst → sağ alt → sol alt sırasıyla dört köşe seçilerek düz yüzey perspektifi giderilebilir. Kaynak önizlemesi hemen görünür; üretimmiş gibi sunulmaz. Köşe seçimi otomatik yapılmaz; seçenek kullanmak zorunlu değildir.
3. Görev seçilir: **yüzeyden tasarım kurtar**, **zaten düz tasarımı onar**, **fotoğrafı koruyarak onar**. Tasarım kurtarma varsayılandır. Kumaş/destek yüzeyi kaldırma talimatı fotoğrafı koruma görevine uygulanmaz.
4. `pipeline.mjs`, üretken adaptörü çağırır. Kumaş, gölge, kıvrım, parlama ve bozulmuş çizgileri ele alma işi modelin eğitilmiş yeteneğine bağlıdır. Kaynak fotoğrafına renk kilidi, histogram eşleştirme, yüz değiştirme veya otomatik yazı yeniden dizgisi yoktur.
5. PNG çözülür; gerçek boyut ve boş/tek renk çıktı kontrol edilir. Bu kontroller yazı/logo/kimlik veya yüzeyden ayrılmanın doğru olduğunu kanıtlamaz. Rapor bu maddeleri **doğrulanmadı**, `printReady=false` olarak tutar. Model hatasında filtreye geçilmez.
6. İstenirse mevcut yerel 2×, BiRefNet arka plan ayırma ve fırça uygulanır. Bunlar ana kurtarma aşamasının dışındadır. Opak ana çıktı saklanır; beyaz tasarım dolguları otomatik beyaz silmeyle kaldırılmaz.
7. PNG mevcut boyutta veya 2048/4096/8192 uzun kenarda dışa aktarılır (en fazla 24 MP). Alpha korunur; DPI ve gerçek üretim/büyütme ayrı kaydedilir. Büyük dışa aktarma Lanczos3 yeniden örneklemedir; yüksek ayrıntı üretildiği anlamına gelmez.

## Dosyalar ve API

- `pipeline.mjs`: görev sözleşmesi, hazırlama, üretken adaptör bağlantısı, teknik kontrol, rapor ve PNG dışa aktarma.
- `geometry.mjs`: sınır/konvekslik kontrolü, homografi ve çift doğrusal örnekleme. Kumaşın yerel deformasyonunu çözmez; bilinmeyen gerçek en-boy oranını çıkarmaz.
- `qwen-adapter.mjs` / `qwen_worker.py`: sabit sürümlü yerel Qwen adaptörü, gerçek alt süreç yönetimi ve süre sınırı. Tek deneme; sessiz model değiştirme yok.
- `server.mjs`: yerel servis, tek ağır iş, kalıcı iş kaydı, güvenli dosya sunumu ve iptal. İptalde işçi ve alt süreçleri kapanana kadar yeni ağır iş kabul edilmez.
- `web/`: mevcut kaynak/sonuç düzenleyicisi; alan ve dört köşe seçimi; yardımcı araçlar ve rapor bağlantıları.
- `models.json`: mevcut model/runtime sürümleri ve ağırlık hashleri. Yeni eğitilmiş bir recovery modeli üretilmedi.

`POST /api/recover?task=extract-design|repair-artwork|restore-image`: dosya gövdesi, isteğe bağlı `X-Region` veya `X-Quad` JSON başlığı. İkisi birlikte verilmez. Yanıt 202 ve iş kimliğidir. `GET /api/jobs/:id` ile izlenir. `POST /api/cancel` iptal eder. Eski `/api/enhance?mode=ai` bağlantısı aynı kurtarma akışına yönlenir; `mode=quick` reddedilir.

`POST /api/edited/:id`, `POST /api/transparent/:id`: tamamlanmış işin PNG kopyası. `POST /api/export/:id`: `{input: 'edited', longEdge: 4096, dpi: 300}`. `GET /report/:id/recovery.json` ve `export.json` denetlenebilir kayıtları verir. Her POST aynı yerel Origin ve ana sayfanın oturum token'ını gerektirir. Servis yalnız 127.0.0.1'e bağlanır; internet yayını yapılmaz.

Her iş `jobs/<id>/` içinde orijinal, `prepared.png`, dolgulu `input.png`, ham `reconstructed.png`, motor log/JSON'u, `enhanced.png`, `recovery.json`, varsa düzenlenmiş/şeffaf PNG ve `export.png` / `export.json` içerir. Başarısızlık kaydı da tutulur. Kaynaklar veya önceki sonuçlar otomatik silinmez. Ham üretim ve padding sonrası çıktı ayrı tutulur; üretken motorun tasarımı kaydırıp kaydırmadığı görsel kontrolde incelenmelidir.

## Model kararı

Qwen-Image-Edit-2511, mevcut indirilmiş ve sürümü sabitlenmiş **değiştirilebilir üretken adaptör** olarak korundu; ürün bu modelin ismine göre tanımlanmıyor. Resmi model kartı görüntü düzenleme, tutarlılık ve geometri yeteneklerini açıklıyor; kumaştan hatasız tasarım kurtarma garantisi vermiyor. Yeni bir modelin daha iyi olduğu kanıtlanmadan büyük indirme/harcama yapılmadı. BiRefNet yalnız yardımcı segmentasyon; ESRGAN yalnız isteğe bağlı 2× işlemidir. Yardımcı 2× içindeki renk/alpha koruması kurtarılmış çalışma görüntüsünü esas alır; gölgeli özgün fotoğrafı kurtarma çıktısına geri basmaz. Baskı çıkarma LoRA'sı eklenmedi.

Resmi kaynaklar: [Qwen model kartı](https://huggingface.co/Qwen/Qwen-Image-Edit-2511), [BiRefNet](https://github.com/ZhengPeng7/BiRefNet). Kesin kurulu türev/sürüm bilgileri `models.json` ve `licenses/` içindedir.

## Kurulum ve çalıştırma

Mevcut PC'de Node, Python, Sharp, Qwen ağırlıkları ve BiRefNet dosyaları hazırdır. Kullanıcıdan terminal/kurulum beklenmez. Yeni sürüm bu oturumda **http://127.0.0.1:17863/** üzerinde açıldı; önceki 17861 servisi korunuyor.

Yeni Windows geliştirici kurulumu için Node 22+ ve Python 3.10+ gerekir. `pwsh -File setup.ps1` mevcut model dosyalarını kullanarak bağımlılıkları kurar, Python yolunu kaydeder ve testleri çalıştırır. İlk indirme gereken geliştirici kurulumu için `-DownloadModels` verilir; yaklaşık 19 GB+ model, ayrıca runtime ve yardımcı dosyalar indirilir. Bu seçenek ücretsiz indirmedir, GPU kiralamaz. Windows CPU runtime resmi sabit sürümden alınır; Vulkan runtime bu PC'deki mevcut doğrulanmış pakettir. CPU'ya düşülmesi hız kabulü anlamına gelmez. Model hazırlama betikleri kesilmiş indirmeyi sürdürür ve ağırlık hashlerini doğrular.

`Baslat.cmd` yerel sayfayı açar ve servisi çalıştırır (varsayılan 17863). Aynı portta zaten servis varsa açık sayfa kullanılmalıdır. Geliştirici komutları: `npm start`, `npm test`. Varsayılan `npm start` portu 17861; `RECOVERY_PORT` ile değişebilir. Testler geçici 17862 portunu kullanır. Node/Python olmayan yeni bir PC için tek dosyalı kurulum paketi bu sürümde tamamlanmış değildir. Dağıtım paketi model kalite/hız kabulünden sonra hazırlanmalıdır.

## Test kapsamı ve kritik eksikler

`npm test` 14 test içerir: tarayıcı modülleri sözdizimi, EXIF/kaynak koruma, homografi, geçersiz köşe reddi, aşırı en-boy oranı, görev/adaptör bağlantısı, crop, başarısız/boş/boyutu yanlış çıktı reddi, filtreye düşmeme, iptal ve gerçek alt süreç kapatma, 2048 PNG/DPI/alpha, HTTP güvenliği. **Adaptör bağlantı testleri açıkça `TEST-TRANSPORT-DOUBLE` kullanır; gerçek model çıktısı veya kalite testi değildir.** Kaynaklar geçici test dizinlerindedir; ağır model/GPU başlatılmaz.

Açık kalan kabul şartları:

- Yeni görevle gerçek yüzeyden tasarım kurtarma; bağımsız fotoğraf/mockup, logo/yazı/desen ve yüz içeren girdilerde ChatGPT referansıyla değerlendirme yapılmadı.
- Yazı/logo/kimliği otomatik güvenilir biçimde onaylayan OCR/geometri/kimlik denetimi yoktur. Kaynak fotoğrafına piksel benzerliği başarı ölçütü olarak kullanılmaz.
- Tek fotoğrafta gizlenen çizgi, aşırı yansıma, okunamayan metin ve gerçek boya rengi kesin olarak çıkarılamayabilir. Kaynak kodu yazmak yeni tanıma yeteneği eğitmez.
- Otomatik tasarım alanı/çoklu tasarım seçimi ve kumaşın yerel deformasyon haritası yoktur; bunlar modelin çıkarımına bırakılmıştır. Dört köşe yalnız düzlemsel perspektifi düzeltir.
- Yerel model girdisi en fazla 512 uzun kenar; ince/uzun oranlarda padding kullanılır. Bu donanımda hız kabulü geçmedi. 4K/8K dışa aktarma yüksek ayrıntılı reconstruction kanıtı değildir.
- Alpha motoru saç/ince çizgi veya beyaz iç dolgu kaybedebilir; şeffaf PNG açık/koyu zeminde ayrıca kontrol edilmelidir. Görsel silgi/geri al araçları bu kabulü otomatikleştirmez.
- CMYK/ICC baskı profili, fiziksel baskı testi ve üretime uygun paketleme tamamlanmadı. PNG sRGB'dir.

Bu eksikler giderilmeden hedefe ulaşılmış veya baskıya hazır çalışan ürün teslim edilmiş sayılmaz. Önceki ağır deneyler `../SONUC.md`; bu tur kanıtı `../on-kontrol/RECOVERY-MVP.md` içindedir.

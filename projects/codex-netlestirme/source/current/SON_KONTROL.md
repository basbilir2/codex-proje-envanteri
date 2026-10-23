# Başlamadan önce son kontrol — 21 Ekim 2026

**Son kapsam güncellemesi:** Kullanıcı ilk ürünü iki genel işleve indirgedi: görüntünün netlik/çözünürlüğünü geliştirmek, ardından istenirse arka planını kaldırmak. Kalite ve hız hedefi en az ChatGPT düzeyi. Güncel kayıt `KAPSAM.md` içindedir. Aşağıdaki bulgular eski Print Extraction adayının kontrolüdür; adapter erişim eksikliği genel restorasyonun bütün yollarını engelleyen zorunlu eksik sayılmaz. Yeniden model seçimi henüz yapılmadı; ana mimari değişmedi.

## Sonuç

Mevcut mimarinin ana yapısı korunuyor: görseli/alanı al → hazır eğitilmiş motorla mevcut tasarımı yeniden oluştur → gerçek alpha/kenar işlemi → PC uygulaması. Sonra web entegrasyonu. Yeni tasarım/süs/metin ekleme yok; ürün birkaç kullanıcı örneğine özel olmayacak.

Geliştirme yolu mevcut; **bütün bileşenler bağımsız çalışmaya hazır ve doğrulanmış durumda değil.** Gerçek olarak tespit edilen eksikler aşağıdadır. Şu anki iş ücretli kaynak veya model çıkarımı başlatmadan yapılmış dosya/kod/erişim kontrolüdür.

## Doğrulanan mevcut parçalar

- `Qwen/Qwen-Image-Edit-2511` resmi temel modeli ve kullanım örneği erişilebilir. [Model kartı](https://huggingface.co/Qwen/Qwen-Image-Edit-2511).
- stable-diffusion.cpp, Windows/CPU/GGUF ve tam 2511 yolu belgeliyor; 2511'e özel `qwen_image_zero_cond_t=true` ayarı unutulmayacak. Bu belge tam adapterle çıkarımın başarılı olduğu kanıtı değil. [2511 belgesi](https://github.com/leejet/stable-diffusion.cpp/blob/master/docs/qwen_image_edit.md).
- Eski uygulamada alan seçme, PNG kaydetme, alpha/kenar işleme ve BiRefNet Lite 512 arka plan modeli bağlantısı zaten var. `src/background.mjs` modeli revision `962e67969ec6acec9c19fab76acee4f5e22e990c` ile çağırıyor. [Model kartında MIT etiketi](https://huggingface.co/studioludens/birefnet-lite-512). Bu modüller gereksiz yere yeniden yazılmayacak.
- Yayıncının gerçek workflow JSON'u tarayıcıdaki Download ile indirildi. Arşiv: `on-kontrol/yayinci-qwen2511-v2-is-akisi.json`. Dosya kaynak kopyayla SHA-256 eşleşti; özeti `on-kontrol/sonuc.json`. [Yayıncı workflow'u](https://www.runninghub.ai/post/2041179666408546306).

## Gerçek eksikler ve gereken dar değişiklikler

### 1. Print Extraction ağırlığının bağımsız erişimi ve izni

[Yayıncı model sayfası](https://www.runninghub.ai/model/public/2041179522065764354) tam dosya adını ve MD5'i doğruluyor:

`印花提取-Qwen-Edit-2511-LoRA-V2.safetensors`
`7b4f31dcebf47228d7962c3f809c1028`

Canlı model sayfasında bağımsız ağırlık indirme bağlantısı görülmedi. Workflow JSON'u indirilebildi; bu JSON model ağırlığını içermiyor. İlgili Qwen deney klasöründe bu safetensors dosyası bulunmadı. Hedefli isim/hash aramasında bağımsız bir dağıtım doğrulanmadı. Bu, dosyanın hiçbir koşulda indirilemeyeceği anlamına gelmez; **bağımsız erişim şu anda doğrulanmamıştır.** Yayıncı sayfasında açık kullanım/yeniden dağıtım lisansı da doğrulanamadı.

Karar: bu parça çözülmeden ücretli GPU açma. Başka LoRA'yı sessizce yerine koyma; dosya varsa hash kontrolünden sonra kullan. Temel modelin Apache-2.0 etiketi bu adapterin izni yerine geçmez. Son ürünü ücretli RunningHub API'sine bağlamak bağımsız çalışma şartını sağlamaz.

### 2. Workflow'daki hızlandırıcı bağımlılığı ve ayarlar

İndirilen grafikte etkin ikinci `LoraLoader` var: `Qwen-Image-Edit-2511-Lightning-8steps_V1.safetensors`, güç 1. Print Extraction gücü 1.5; sampler 8 adım, CFG 1, Euler/simple; ModelSamplingAuraFlow shift 1.8; CFGNorm 1; örnek çıktı 1536×2048. Bunlar incelenmiş yayıncı ayarlarıdır; her görsele zorunlu boyut/seed/prompt olarak sabitlenmez.

[LightX2V'nin resmi deposunda](https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning/tree/main) 8-step BF16/FP32 dosyaları var; yayıncı grafiğindeki ad ile güncel ad aynı değil. Tam artefakt/sürüm eşleşmesi kontrol edilecek. 4-step birleşik modelle veya ikinci hızlandırıcı ekleyerek sessizce farklı bir yol kurulmayacak. Merged Lightning temelinde aynı LoRA tekrar uygulanmayacak.

Karar: ek bağımlılık sürüm listesine alınır. Yalnız Print Extraction LoRA ile 8 adımı aynı kaliteyi verecek diye varsayma. Bu mevcut motor yolunun eksik bağımlılık kontrolüdür; yeni temel model seçimi değildir.

### 3. Yeni Qwen adaptörü henüz yazılmamış

Yerel `service/local-redraw.mjs` açıkça FLUX.2-klein motoru, 4 adım ve FLUX2 VAE ayarlarına bağlı. Qwen'i bu ayarlara yalnız dosya adı değiştirerek bağlamak doğru değil.

Karar: mevcut giriş/çıkış ve iş yönetimi korunur; gereken Qwen 2511 adaptörü eklenir. Qwen metin/vision kodlayıcısı, VAE, 2511 model ayarı ve adapter yükleme doğrulaması ayrı tanımlanır. Mimari baştan kurulmaz.

### 4. Şeffaflık ayrı aşamadır; sabit renk silme genel çözüm değil

Yayıncı workflow'u VAEDecode → SaveImage ile bitiyor; özel alpha/matting düğümü içermiyor. Workflow indirilmiş olması gerçek şeffaf PNG üretildiği anlamına gelmez.

Mevcut `src/redraw-matte.mjs` kasıtlı magenta fonu renk farkıyla siliyor. Tasarımın kendisindeki magenta/pembe ayrıntılar da aynı renk ölçütüne girebilir; bu nedenle bütün görsellere zorunlu uygulanacak yöntem olamaz. Bu risk mevcut kod formülünden tespit edildi; yeni bir model çıkarımı veya başarısız test iddiası değildir.

Karar: mevcut BiRefNet/alpha/kenar altyapısını koru, yeniden oluşturma sonrasına doğru bağla. Genel tasarım renkleri sabit chroma temizliğiyle otomatik silinmez. İnce çizgi, iç dolgu ve gerçek boşlukların korunması gerekli kabul kontrolünde doğrulanır; modelin mevcut olması kusursuz ayırma garantisi sayılmaz.

## Hız ve PC koşulu

Kullanıcı en az beklemeyi istiyor; süreyi ayrıca sormak yerine kaliteyi koruyan en hızlı uygulanabilir yol geliştirilecek. Aynı ağır modelin bulutta hızlı çalışması bu PC'deki hızı kanıtlamaz. Mevcut donanım incelemesinde 37,8 GiB RAM, Ryzen 7 7730U ve bütünleşik AMD grafik birimi var. Model indirmesi/kurulum ve warm çalışma süreleri ayrı ölçülecek; kanıt olmadan saniye veya gerçek zamanlı çalışma sözü verilmeyecek.

## Şu anki durum

- Model çıkarımı: yapılmadı.
- Ücretli GPU/ödeme: başlatılmadı.
- Yayıncı workflow'u: indirildi, gerçek grafiği incelendi, arşivlendi.
- Print Extraction ağırlığı ve kullanım izni: doğrulanmadı; harcama öncesi açık eksik.
- Mimari değişikliği: ana yapı korunuyor; yalnız yukarıdaki kanıtlanmış eksikler tamamlanacak.
- Kullanıcıdan görsel çifti, doğru metin listesi veya kurulum işi beklenmiyor. Kullanım hedefinde sorulacak başka bir belirsizlik kalmadı; teknik eksikler geliştiricinin sorumluluğunda.

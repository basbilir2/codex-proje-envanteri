# Geliştirmeden önce gerçekçilik kararı

**Son kapsam güncellemesi:** İlk ürün genel görsel netlik/çözünürlük geliştirme + isteğe bağlı arka plan kaldırmadır. Kalite ve hız hedefi en az ChatGPT düzeyi. Güncel bağlayıcı kısa kayıt `KAPSAM.md` içindedir. Aşağıdaki Qwen + Print Extraction incelemesi önceki baskı çıkarma adayına aittir; bu adapter genel restorasyonun zorunlu ön koşulu değildir. Yeni bir motor henüz seçilmedi. Önceki bütçe/süre tahmini doğrulanmış genel ürün teslim fiyatı değildir.

21 Ekim 2026. Bu değerlendirme gerçek model çıkarımı veya başarı sonucu değildir. Ücretli kaynak başlatılmadı; model indirilmedi veya PC'ye yeni uygulama kurulmadı.

## Karar

Kullanıcı düzeltmesi: ChatGPT'nin gösterilen örneklerde ulaştığı hedef kalite bellidir; referanslar bu sonucun elde edilebildiğini gösterir. Doğrulanması gereken, seçilen ücretsiz model/adapter ve yerel çalışma yolunun aynı kaliteyi sağlamasıdır. “Kalite belirsiz” ifadesi hedefin tanımsız veya sonucun elde edilemez olduğu anlamında kullanılmayacak. Bu referanslar her kaynağın kusursuz çözüleceği veya başka bir modelin otomatik olarak eşit olduğu kanıtı sayılmaz.

Hazır açık kodu kullanarak seçili tasarımı işleyen ve Windows'a kurulabilen bir uygulama geliştirmek teknik olarak gerçekçi. Mevcut seçilmiş Qwen-Image-Edit-2511 + Print Extraction LoRA bunun için gerçek bir aday. Ancak **PRIVATE_AMOUNT geliştirme kredisiyle her görselde kusursuz ChatGPT kalitesini ve bu PC'de kabul edilebilir süreyi garanti etmek için kanıt yok.** Bu koşullar kesinleşmiş sonuç gibi sunulamaz.

İzlenecek yol, sıfırdan temel model eğitmek veya belirsiz bir hafif model vaat etmek değil: hazır tam model/adaptere erişimi ve yerel çalışma yolunu doğrula; sınırlı gerçek kalite değerlendirmesi yap; yalnız yeterliyse PC uygulamasına geçir. Hedefe ulaşılmadığı anlaşılırsa bitmiş proje iddiası ve aynı kör denemelerle devam yok.

## Bu turda doğrulananlar

| Konu | Kanıt ve sınır |
|---|---|
| Hazır temel model | [Qwen 2511 resmi model kartı](https://huggingface.co/Qwen/Qwen-Image-Edit-2511) ve [resmi GitHub](https://github.com/QwenLM/Qwen-Image) mevcut. Kart BF16/CUDA örneği ve Apache-2.0 etiketi içeriyor. Kart, bizim referanslarımızda ChatGPT eşitliği kanıtı değil. |
| Tam adapter | [Yayıncının Print Extraction V2 sayfası](https://www.runninghub.ai/model/public/2041179522065764354), 2511 tabanı, tam dosya adı ve beklenen MD5'i doğruluyor. [Yayıncının workflow'u](https://www.runninghub.ai/post/2041179666408546306) mevcut. Dosyanın bağımsız indirilmesi ve ticari yeniden dağıtım/kullanım şartları henüz doğrulanmadı; sayfanın varlığından serbest lisans çıkarılmaz. |
| Yerel çalışma adayı | [stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp) Windows, CPU, Vulkan, GGUF ve LoRA desteği belgeliyor. [2511 kullanım belgesi](https://github.com/leejet/stable-diffusion.cpp/blob/master/docs/qwen_image_edit.md) tam sürüm için örnek veriyor. Bu, tam Print Extraction adapterinin yüklenip doğru sonuç verdiğini henüz kanıtlamaz. |
| Sıkıştırılmış ağırlık | Çalıştırıcının yönlendirdiği [Unsloth 2511 GGUF deposunda](https://huggingface.co/unsloth/Qwen-Image-Edit-2511-GGUF/tree/main) Q4_K_M dosyası 13,2 GB görünüyor. Bu yalnız diffusion dosyası; metin/vision kodlayıcı, VAE, adapter ve çalışma belleği ayrıca gerekir. Dosya boyutu toplam RAM veya hız garantisi değildir. |
| Gerçek PC | Bu turda salt okunur donanım sorgusu: Ryzen 7 7730U, 8 çekirdek, 37,8 GiB fiziksel RAM; AMD Radeon için Windows AdapterRAM değeri 2 GiB, C: boş alan 163,1 GiB. Bütünleşik grafiklerde raporlanan değer toplam paylaşılabilir bellekle aynı değildir. Yerel süre ve en yüksek bellek kullanımı ölçülmedi. |

Çıkarım: CPU/quantized yolu tamamen yok saymak doğru değil. “Bu donanımda hızlı ve ChatGPT kalitesinde kesin çalışır” demek de doğru değil. BF16/CUDA örneğinin tek başına bu PC'de çalışmaması, bütün optimize yolların imkânsızlığını kanıtlamaz.

## Teknik olarak korunacak ayrıntılar

- Tam temel sürüm `Qwen-Image-Edit-2511`; tam adapter `印花提取-Qwen-Edit-2511-LoRA-V2.safetensors`; MD5 `7b4f31dcebf47228d7962c3f809c1028`. Bir başka model veya adapter sessizce yerine konulmaz.
- Yerel çalıştırıcının güncel 2511 belgesi `--model-args qwen_image_zero_cond_t=true` gerektiriyor; atlanırsa kalite bozulabileceği belgelenmiş. Seçilen sürüm sabitlenip kendi komut belgesiyle eşleştirilecek.
- [LoRA belgesi](https://github.com/leejet/stable-diffusion.cpp/blob/master/docs/lora.md), quantized modelde varsayılan `at_runtime` yolunu ve bellek/hız farkını açıklıyor. “Dosya bulundu” ile “adapter gerçekten uygulandı” ayrı kontrol edilecek.
- Windows paketinde yalnız arayüz veya geçmiş örnek sonucu bulunması yeterli değil. Yeni bir görsel, yerel motor tarafından gerçekten işlenmeli. RunPod kapalıyken sonuç üretmek PC kabul şartıdır.
- Aynı ayar/kaynak/model sürümü kaydedilerek bulut ve PC karşılaştırması gereksiz belirsizlikten korunacak. Quantization etkisi kontrol edilmeden BF16 bulut sonucunu PC çıktısı sayma.

## Başlama ve bütçe

### Sınırları belli uygulama planı

Bu plan yalnız mevcut Qwen-Image-Edit-2511 + tam Print Extraction LoRA yolunu kapsar. Yeni temel model eğitimi, rastgele alternatif model araştırması ve donanım satın alımı kapsamında değildir. Az önce doğrulanan A6000 tarifesi PRIVATE_AMOUNT/saat ve yaklaşık PRIVATE_AMOUNT/USD hesap varsayımıyla GPU yaklaşık PRIVATE_AMOUNT/saat eder. Banka farkı ve depolama ayrıca hesaba katılır. Fiyat kaynağı: https://www.runpod.io/pricing .

- GPU açmadan önce tam dosyaya erişimi ve runtime uyumluluğunu incele. Kodlama ve Windows paketleme sırasında gerekmedikçe kiralık GPU açık kalmaz.
- İlk gerçek çıktıya ilişkin kurulum/kalite kararına en fazla 2 faturalandırılmış GPU saati ayır (GPU yaklaşık PRIVATE_AMOUNT). Süre dolup çıkarım yapılamadıysa bunu kalite başarısızlığı diye değil kurulum engeli diye kaydet; ücretli kaynağı durdur. Çıktı hedefe yetmiyorsa belirli bir teknik hata bulunmadan yeni seed/prompt denemeleriyle devam etme.
- İlk sonuç yeterliyse diğer mevcut örnekler, gereken optimizasyon ve PC'ye aktarım için ilerle. Toplam planlama tahmini 3–8 GPU saati; kısa süreli depolama ve ödeme farkı dahil dış hizmet gideri tahmini 150–PRIVATE_AMOUNT. Bu bir planlama aralığıdır; gerçek model testi veya kesin tamamlanma fiyatı değildir.
- Mevcut PRIVATE_AMOUNT sınırı harcama tavanıdır, tüketilecek hedef değildir. Aşılması gerekirse otomatik devam/ek yükleme yok. Kullanıcının fiyat sorusu bütçe artışı değildir.
- Teslim yolu: seçili alan → aynı Qwen + adapter ile tasarımı yeniden oluştur → gerçek alpha/kenar işlemi → aynı modelin uygun sıkıştırılmış sürümüyle yerel Windows motoru → PC'ye kurulum ve RunPod kapalıyken yeni görselde doğrulama.
- Her kalite kontrolü farklı bir kabul şartını sınar. Yeni gerekçe olmadan aynı görsel/ayar tekrar çalıştırılmaz; eski sohbetler tekrar taranmaz. İlk sonuç yeterli olmazsa tamamlanmış ürün veya garanti iddiası yoktur.

Kullanıcı PRIVATE_AMOUNT kredi alacağını, tamamlayınca “aldım, başla” yazacağını söyledi. Bu sinyal gelmeden ücretli GPU başlatılmaz. Sinyal geldikten sonra açık oturumdaki bakiye/ayarlar kontrol edilip rutin teknik adımlarda tekrar onay istenmez.

Yeni geliştirme harcaması yüklenen bu kredi ve PRIVATE_AMOUNT sınırıyla sınırlıdır; başka mevcut kredi, otomatik yükleme veya ek ödeme yetkisi yoktur. Hesaptaki fiili para birimi/tutarı o anda kaydedilir. GPU, container ve depolama toplamı bütçeye dahildir; kredi bittiğinde yeni satın alma yapılmaz. Aktif GPU iş dışı bırakılmaz. Kalıcı ücretli depolama tutulması sessizce süresiz varsayılmaz; gerekli çıktılar alınır ve mevcut ilgisiz kaynaklara dokunulmaz.

PRIVATE_AMOUNT'ye “kusursuz model eğitimi” veya kesin bitiş süresi taahhüdü yok. Hazır modelin yeterli çıkması halinde mevcut kodu birleştirmek hedefleniyor. Yetersizliği rastgele model/prompt taramasıyla örtme.

## En az gerekli doğrulama ile yol

Son kapsam düzeltmesi: aşağıdaki Mavi/üç örnek sırası ilk öneriydi; kullanıcı genel yazılım hedefini birkaç kaynağa bağlamayı reddetti. Bağlayıcı güncel yaklaşım, genel kaynak kodu ve eğitilmiş modelle yeni girdileri tanıyıp işlemektir. Mevcut örnekler isteğe bağlı geçmiş hata kontrolü olabilir; kabul bunların başarısına indirgenmez. Çeşitli ve geliştirmede kullanılmamış girdilerle gerekli doğrulamayı geliştirici üstlenecek; kullanıcıdan örnek eşleştirmesi veya doğru metin listesi istenmeyecek. Kaynak kodu geliştirme ile model ağırlığı eğitimi aynı işlem değildir; hazır kodun varlığı model yeteneği garantisi olarak anlatılmaz.

1. **GPU kiralamadan önce:** tam adapter indirilebilir mi, kullanım koşulları belli mi ve seçilen runtime/sürüm adapteri destekliyor mu kontrol et. Küçük metadata/kod incelemesiyle çözülen konu için inference çalıştırma. Eksik temel girdi varken saatlik GPU açma.
2. **Genel yöntem ve ilk kalite kontrolü:** kod/parametreleri belirli tasarım veya metne sabitlemeden, seçilmiş model ve adapterle genel tanıma/çıkarma akışını uygula. Metin, geometri, dolgu, yüzey temizliği ve alpha sonucunu incele. Eski FLUX çıktısını referans alma. Sorun varsa yalnız belirlenmiş teknik nedene bağlı düzeltme yap; rastgele seed/prompt taraması yok.
3. **Genellenebilirlik:** geliştiricinin sağlayacağı çeşitli ve geliştirmede kullanılmamış girdilerde yöntemi doğrula. Kullanıcıdan kaynak/sonuç çiftleri hazırlamasını isteme. Birkaç logonun başarısını bütün tasarımları çözen sistem diye sunma. Aynı çalıştırmayı yeni neden olmadan tekrarlama.
4. **İlk ürün:** kabul edilen motoru sade Windows uygulamasına bağla: görsel seç → alan seç → işle → şeffaf PNG kaydet. Mevcut kullanılabilir kod parçalarını yeniden yazma; gereken adaptörü ekle. Wix, üyelik, ödeme ve dizgi bu adımın ön koşulu değil.
5. **Yerel kabul ve kurulum:** uygulamayı PC'ye kur, kısayolunu hazırla; RunPod'a bağlanmadan yeni bir görselde gerçek üretim ve PNG kaydını bir kez doğrula. Gerçek süre/bellek ve önemli sınırlamaları kaydet. Yalnız derlenmesi, açılması veya eski görseli göstermesi bitmiş iş kanıtı değil.
6. **Teslim veya dürüst engel:** kalite ve yerel kullanım koşulları geçtiğinde çalışır uygulamayı, çıktıları ve kısa kullanım bilgisini ver. Geçmediyse eksik sistemi bitmiş diye sunma; bütçe/süre/hardware engelini somut kanıtla bildir. Kullanıcının ek mesaj yazmak istememesi belirsiz sonucu başarılı ilan etme izni değildir.

Bu kontroller kullanıcının gereksiz test yasağıyla uyumludur: her biri ayrı bir kabul şartını kanıtlar. Gereksiz tekrar yapılmayacak; çalıştığını sınamadan teslim edilmeyecek.

## Sonraki aşama

İlk hedef PC'de kullanımdır. Webde aynı motoru sunmak sonradan ele alınacak; web arayüzünün varlığı sunucu hesaplamasını ortadan kaldırmaz. Kendi PC'sinde çalıştırma seçeneği ile her ziyaretçinin tarayıcısında ücretsiz çalışması aynı iddia değildir; web ölçeği henüz doğrulanmadı.

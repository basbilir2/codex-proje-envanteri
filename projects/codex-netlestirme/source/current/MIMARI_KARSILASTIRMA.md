# Mevcut mimari ve önerilen yöntemler — 21 Ekim 2026

**Güncel değerlendirme önceliği:** Kullanıcı asıl hedefi üretken görsel düzenleme olarak tekrar açıkladı. Qwen-Image-Edit-2511 bu ana iş için öncelikli aday; SeedVR2/Real-ESRGAN yardımcı restorasyon/büyütme adayları. Aşağıdaki önceki SeedVR2 önceliği, tek başına ana ürün seçimi olarak kullanılmayacak. Yeni motor kurulmadı; bu bir görev uygunluğu düzeltmesidir.

Bu bir belge/kod/lisans karşılaştırmasıdır. Yeni model kurulmadı, kalite/hız karşılaştırmalı inference yapılmadı, ücretli GPU açılmadı. Kullanıcı öneriyi karşılaştırmamızı istedi; önerinin bütünü uygulandı veya ChatGPT eşitliği kanıtlandı sayılmaz.

## Mevcut durum

Güncel ürün kapsamı `KAPSAM.md` içindedir: genel görsel netlik/çözünürlük geliştirme ve ardından isteğe bağlı arka plan kaldırma. Eski Qwen 2511 + Print Extraction LoRA, baskı çıkarma aday incelemesidir; genel restorasyon için zorunlu motor değildir. Eski kaynak uygulama HTML/JavaScript ve yerel Node servisleri içerir; bağımlılık listesinde ESRGAN Slim ve Transformers.js vardır. Arka plan kodu BiRefNet Lite 512'yi sabit model revision'ıyla kullanır. Qwen bağlanmış değildir.

## Karşılaştırma

| Katman | Mevcut yapı | Önerinin değerlendirmesi |
|---|---|---|
| Hızlı netleştirme/büyütme | ESRGAN Slim 2× ve sınırlı ek işlemler | Real-ESRGAN, genel fotoğraf restorasyonuna yönelik daha doğrudan bir aday. NCNN/Vulkan Windows sürümü AMD/Intel/NVIDIA için belgelenmiş; Python/CUDA kurulumu istemeyen dağıtım yolu var. Mevcut PC'de hız ve kalite ölçülmeden üstün sonuç kanıtı sayılmaz. |
| Üretici restorasyon | Eski Qwen düzenleme/baskı çıkarma adayı | SUPIR doğrudan fotogerçekçi restorasyon için geliştirilmiş. Görünüm ile kaynağa bağlılık arasında ayar dengesi var; varsayılan fotogerçekçi prompt'ları her logo/yazı/illüstrasyona aynen uygulamak uygun olmaz. “ChatGPT'ye en yakın” iddiasını bu incelemede doğrulayan doğrudan karşılaştırma yok. |
| Yüz | Ayrı kabul edilmiş yüz motoru yok | GFPGAN/CodeFormer yalnız yüz bulunan girdilerde isteğe bağlı/koşullu uzman bileşen olabilir. Yüzü yeniden yorumlama/kimlik değişimi gerekli kontroldür. Yazı ve logo iyileştirme motoru yerine geçmez. GFPGAN'ın resmi lisansı Apache-2.0; CodeFormer ticari kullanım için ek izin ister. |
| Arka plan | BiRefNet Lite 512 ve alpha/kenar işleme mevcut | Aynı model ailesi zaten var. Korunacak; daha büyük BiRefNet varyantına ancak gerçek kenar/saç kaybı ve ölçülen fayda gerektirirse geçilir. BiRefNet adının aynı olması varyantların aynı kalite/hız olduğu anlamına gelmez. |
| Arayüz | Mevcut HTML/JS ve yerel servis altyapısı | Gradio prototip için veya FastAPI ayrı servis için kullanılabilir; ikisi de görüntü kalitesini artıran motor değildir. Çalışan sade arayüzü sırf framework tercihi için yeniden yazmak gerekli görünmüyor. |

## Lisans ve donanım bulguları

- [Real-ESRGAN resmi proje](https://github.com/xinntao/Real-ESRGAN), [BSD-3-Clause lisansı](https://github.com/xinntao/Real-ESRGAN/blob/master/LICENSE). Resmi README, NCNN taşınabilir Windows sürümünü ve AMD/Intel/NVIDIA yolunu belgeliyor. Model ve bağımlılıkların dağıtım bildirimleri korunur.
- [SUPIR resmi proje](https://github.com/Fanghua-Yu/SUPIR), [ticari kullanım koşulları](https://github.com/Fanghua-Yu/SUPIR/blob/master/LICENSE): ticari kod/ağırlık kullanımı için ayrı yazılı izin/lisans gerekiyor. Bu nedenle son ürünün ücretsiz ticari kullanım şartına mevcut haliyle kabul edilemez. README düşük bellek yolu için 12G diffusion/16G LLaVA ve daha yavaş çalışma notu veriyor; bunlar farklı bileşenler/yerleşim içerdiğinden tek toplam VRAM gereksinimi gibi okunmamalı. “24 GB her koşulda yeterli” veya bu PC'de hızlı çalışma varsayılmaz.
- [CodeFormer lisansı](https://github.com/sczhou/CodeFormer/blob/master/LICENSE), ticari kullanım için geliştiriciyle iletişim gerektiriyor.
- [GFPGAN resmi proje](https://github.com/TencentARC/GFPGAN), Apache-2.0 lisansını belirtiyor. Seçilecek checkpoint/dependency dağıtımı ayrıca sabitlenir.
- [BiRefNet resmi proje](https://github.com/ZhengPeng7/BiRefNet), MIT lisanslı. Mevcut varyant ayrıca [Studio Ludens Lite 512](https://huggingface.co/studioludens/birefnet-lite-512).
- [rembg](https://github.com/danielgatis/rembg) bir model değil, farklı modelleri çalıştıran araçtır; BiRefNet'i de destekler. Bu nedenle “BiRefNet her zaman rembg'den iyi” doğru karşılaştırma değildir; model/varyant ve aynı girişler karşılaştırılır.
- [FastAPI resmi belge](https://fastapi.tiangolo.com/), servis katmanıdır. Framework performansı modelin görüntü kalitesi veya PC'deki inference hızıyla aynı ölçüm değildir.

## Mimaride önerilen dar düzeltme

Ana akış korunur: yükle → iyileştir → istenirse arka planı kaldır → kaydet. Genel restorasyonun hızlı yolu için Real-ESRGAN değerlendirilir; mevcut BiRefNet/kenar motoru ve uygun arayüz parçaları korunur. GFPGAN ancak yüz ihtiyacı varsa eklenir. Her görsele bütün motorlar sırayla uygulanmaz.

SUPIR ve CodeFormer, ticari izin/uygunluk çözülmeden ana motora alınmaz. SUPIR'i çıkarmakla güçlü üretici restorasyon/ChatGPT kalite hedefinin çözüldüğü iddia edilmez: Real-ESRGAN + BiRefNet tek başına bütün kötü kaynaklarda ChatGPT düzeyini kanıtlamaz. Daha güçlü ücretsiz ticari restorasyon yolu son kapsamın açık motor seçimi konusudur; bu karşılaştırmada alternatif model araştırması yapılmadı.

Öneri, yeni iki işlevli ürün hedefiyle eski Print Extraction odağından daha iyi eşleşiyor; bu görev uygunluğu değerlendirmesidir, ölçülmüş kalite sıralaması değildir. Kullanıcı sonucu değerlendirmeden bu belgeyi yeni uygulamanın kurulmuş olması gibi sunma.

## Üretici restorasyon adaylarının doğrulaması — aynı gün

Kullanıcı Qwen-Image-Edit, SeedVR2 ve DiffBIR'i araştırılacak adaylar olarak sundu. Bu kapsamda yalnız ilgili resmi kaynaklar ve doğrudan kod incelendi; yeni model kurulmadı/çalıştırılmadı, ücretli kaynak açılmadı.

| Aday | Doğrulama | Ürün açısından değerlendirme |
|---|---|---|
| SeedVR2-3B | [Resmi kod](https://github.com/ByteDance-Seed/SeedVR) ve [3B model kartı](https://huggingface.co/ByteDance-Seed/SeedVR2-3B), Apache-2.0 belirtiyor. Resmi `projects/inference_seedvr2_3b.py` kodunda `is_image_file`, JPG/PNG/WebP gibi uzantılar ve tek görsel için `sp_size=1` yolu gerçekten var. Kod CUDA kullanıyor. | Genel restorasyona doğrudan odaklı ve tek diffusion adımlı olması nedeniyle güçlü katmanın ilk değerlendirme adayı; üstün kalite/hız sonucu henüz ölçülmedi. Tek adım, bütün işlemin tek hızlı hesap olduğu veya mevcut AMD PC'de hızlı olduğu anlamına gelmez. |
| Qwen-Image-Edit-2511 | [Tam sürümün resmi kartı](https://huggingface.co/Qwen/Qwen-Image-Edit-2511) Apache-2.0; hazır düzenleme pipeline'ı mevcut. Bu bilgi başka Qwen sürümlerine veya üçüncü taraf Print Extraction LoRA'ya aktarılmaz. | Anlamsal yeniden oluşturma/düzenleme için aday kalabilir. Genel restorasyonda her görsele zorunlu uygulanmayacak; yazı, geometri ve yüz sadakati doğrulanmalı. |
| DiffBIR | [Resmi repo](https://github.com/XPixelGroup/DiffBIR) Apache-2.0 kod, v2.1 checkpoint'leri ve tiled sampling belgeliyor. Stable Diffusion 2.1 ve görev özelinde başka stage-1 modelleri kullanıyor. Bu turda resmi SD 2.1 model sayfası 401 döndü; bütün temel model/yardımcı ağırlık lisans ve erişim zinciri tamamlandı diye işaretlenmedi. | Restorasyona uygun ikinci aday. Kod lisansından bütün ağırlıkların dağıtım izni çıkarılmaz. Ölçülmüş kıyas olmadan SeedVR2/Qwen'den iyi veya kötü denmez. |

### Hazır optimizasyon yolu

[numz SeedVR2 entegrasyonu](https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler), tek görsel/standalone CLI, GGUF, CPU'ya offload, BlockSwap ve VAE tiling seçeneklerini ve Apache-2.0 kod lisansını belgeliyor. 8 GB veya daha düşük VRAM için örnekler var; bunlar bu PC'nin bütünleşik AMD grafik biriminde destek/hız garantisi değildir. Ana resmi README'deki H100 video ölçüleri, tek fotoğrafın asgari gereksinimi gibi sunulmaz. CPU'ya offload ile tamamen CPU inference aynı şey değildir. İntegrasyon ve quantized ağırlıklar kullanılacaksa tam sürüm/hash/lisanslar ayrıca sabitlenir.

### Kullanıcının metnindeki kesinleştirilmemiş iddialar

- Real-ESRGAN yalnız keskinleştirme filtresi değildir; GAN tabanlı öğrenilmiş süper çözünürlükle ayrıntı tahmin eder. Genel anlamsal yeniden oluşturma yeteneği ayrıca değerlendirilir. Kaynak: [resmi proje](https://github.com/xinntao/Real-ESRGAN).
- Tiling büyük çıktıların bellek ihtiyacını azaltır; 4K piksel boyutu ayrıntı doğruluğu veya dikişsiz/tutarlı sonuç garantisi değildir. SeedVR2 entegrasyonu overlap ve olası tile izlerini ayrıca belgeliyor.
- Alpha matting saç/yarı şeffaf kenarlara yardımcı olabilir; cam ve her tasarım için kusursuzluk garantisi değildir. Mevcut alpha/kenar kodu korunur, yalnız gerekli eksikler düzeltilir.
- Yerel kuyruk/toplu iş, kapasiteyi donanım ve işlem süresinden bağımsız veya sınırsız yapmaz. ChatGPT'yi kalite/hız/sadakat açısından geçtiğimiz iddiası için gerçek kıyas gerekir.

### Dar kapsamlı öneri

Ana iki işlev ve arayüz korunur. Hızlı iyileştirme için Real-ESRGAN; güçlü restorasyon için ilk değerlendirme adayı SeedVR2-3B; sonuçtan arka plan ayırma için mevcut BiRefNet/alpha altyapısı. İki iyileştirme motoru her görselde art arda zorunlu çalıştırılmaz. Qwen 2511 ve DiffBIR alternatif adaylar olarak tutulur; rastgele çok-model taraması yapılmaz. Bu belge bir kurulmuş model değişikliği değildir. SeedVR2'nin yerel kalite/hızı doğrulanmadan nihai motor veya bağımsız PC ürünü tamamlandı denmez.

## Kullanıcının karşılaştırma kaynaklarını kontrol — son düzeltme

- [VideoProc incelemesi](https://www.videoproc.com/resource/open-source-image-upscaler.htm), kendi sınırlı örneklerinde SeedVR2'yi doğal görünüm/tutarlılık açısından öne çıkarıyor; SUPIR'in bazı ağır bozulma/üretici ayrıntı durumlarında değerini de belirtiyor. Yerel test donanımı RTX 3060 12GB; SeedVR2 gibi yerelde güvenilir çalışmayan araçlarda bulut ComfyUI kullanılmış. Bu nedenle sayfa, eşit donanımda kesin hız kazananı veya tüm kaynaklarda kalite kazananı kanıtı değildir. Yazar bir ticari görüntü yazılımı üreticisinde çalışıyor; sayfa kendi ürününü de tanıtıyor. SUPIR'e yazdığı ekip bilgisi resmi proje yazar listesiyle uyuşmuyor. Genel teknik/lisans kararları bu incelemeye dayandırılmaz.
- [aiofm rehberi](https://aiofm.info/en/guides/ai-image-upscaling), SUPIR'i portre/fotogerçekçilik açısından öneriyor; görünür karşılaştırma listesinde SeedVR2 yok. Aynı girdi/sürüm/ayarlarla SeedVR2 karşısında kazandığı kontrollü test sayılmaz. SUPIR için kullandığı “free” ifadesi ücretsiz ticari kullanım izni yerine geçmez.
- [SeedVR2.net sayfası](https://seedvr2.net/supir-vs-seedvr2), SeedVR2 erişimi sattığını ve kontrollü benchmark/kalite kazananı iddiasında bulunmadığını açıkça yazıyor. Tarafsız kalite testi veya ByteDance'in resmi benchmarkı olarak kullanılmaz. Teknik sonuçlar bu ticari sayfaya dayandırılmaz.
- SUPIR ticari kullanım kısıtı [kendi LICENSE dosyasının 3. bölümünden](https://github.com/Fanghua-Yu/SUPIR/blob/master/LICENSE) yeniden doğrulandı: kod/ağırlıkların ticari kullanımı için ayrı yazılı izin/lisans gerekiyor. Önceki bulgu üçüncü taraf siteye bağlı değildir.
- [Qwen-Image-Edit-2511 resmi kartı](https://huggingface.co/Qwen/Qwen-Image-Edit-2511), görüntü girdisi ve talimatla düzenleme, kimlik/tutarlılık ve geometrik akıl yürütme geliştirmelerini belgeliyor. Bu yetenek sınıfı, kullanıcının mevcut görüntüyü anlayıp yeniden oluşturma talebiyle doğrudan örtüşüyor. “Qwen kesin ChatGPT'yi geçer” sonucu çıkarılmaz.
- SeedVR2 ve SUPIR de üretici diffusion tabanlı restorasyon yapar. Üretici model kullanmaları, genel talimat takip eden görsel düzenlemeyle aynı görev sınıfı oldukları anlamına gelmez. Kullanıcının istediği davranıştan hareketle genel düzenleme katmanı ana aday konumuna alınır; üçüncü taraf karşılaştırmalarından birinci model seçilmez.

**Güncel ana akış:** görüntü girdisi → içeriği koruyarak üretken düzenleme (öncelikli aday Qwen 2511) → yalnız gerekirse restorasyon/büyütme yardımı → kullanıcı isterse mevcut BiRefNet + alpha/kenar işlemi → kaydet. Kullanıcıya iki işlevli ekran korunur. Ücretli kaynak ve gerçek inference başlatılmadı.

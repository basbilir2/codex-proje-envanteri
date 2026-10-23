# Uygulama öncesi mimari — 21 Ekim 2026

Durum: kullanıcı kredi yüklediğini bildirdi ve geliştirmeyi başlattı. Uygulama ilerlemesi `on-kontrol/gelistirme-durumu.json` içindedir. Yerel RAM'e uygun Q4_K_M ağırlıkları, sabit sürümlü stable-diffusion.cpp ile Python işçisinden çalıştırılacak; bulutta CUDA, PC'de desteklenen yerel backend kullanılacak. Bu runtime tercihi modeli değiştirmez; nicemlemenin kalite etkisi gerçek çıktıda kontrol edilecek. Bu belge uygulama planıdır; eski karşılaştırma ve baskı çıkarma deneyleri tarihsel kanıttır.

## Ürün ve akış

Windows'ta tek kısayolla açılan küçük uygulama. Kullanıcı görseli yükler, **Mükemmelleştir** düğmesine basar; sonucu kaydedebilir veya **Arka planı kaldır** düğmesiyle şeffaf PNG alabilir. Önce/sonra görüntüsü, işlem durumu ve kaydetme aynı ekranda bulunur. Model, prompt ve GPU ayarları kullanıcı işi değildir.

Akış: orijinal → üretken düzenleme → gerekliyse büyütme → iyileştirilmiş PNG → kullanıcı isterse arka plan ayırma/kenar düzeltme → RGBA PNG.

Orijinal dosya değişmez. Tam görsel işlenir; zorunlu bölge seçimi yoktur. Arka plan kaldırıldığında ayrıca iyileştirilmiş opak çıktı korunur. Üretken düzenleme, şeffaflaştırmadan sonra tekrar uygulanmaz.

## Bileşen kararları

| Bileşen | Karar | Uygulama sınırı |
|---|---|---|
| Ana düzenleme | **Qwen-Image-Edit-2511** | İlk uygulanacak ve kabulü ölçülecek ana motor. İçeriği anlayarak yeniden oluşturma; yazı, kimlik, şekil, renk ve kompozisyonu koruma talimatı. Başarısı henüz ölçülmedi. |
| Yardımcı büyütme | **Real-ESRGAN**, gerekirse | Yalnız ana çıktı istenen piksel boyutunu karşılamadığında ve detay faydası doğrulandığında. Ana motor hatasını gizleyen veya ona sessizce alternatif olan yol değildir. |
| Ek restorasyon | **SeedVR2**, yedek aday | İlk kurulumun zorunlu parçası değil. Qwen çıktısında somut restorasyon eksikliği görülürse, sınırlı ve gerekçeli değerlendirme. |
| Arka plan | **Mevcut BiRefNet Lite 512 + alpha/kenar işleme** | Mevcut kod yeniden kullanılır. Varyant yalnız gerçek detay kaybı ve ölçülen fayda gerektirirse değişir. Sabit renkle silme genel yöntem değildir. |
| Arayüz ve iş yönetimi | **Mevcut HTML/JavaScript + Node altyapısı** | Uygun parçalar alınır; ayrı framework veya ikinci prototip arayüz kurulmaz. Ürün ekranı yalnız iki işleve odaklanır. |
| Model çalıştırıcı | **Ayrı Python işçisi ve Qwen adaptörü** | Yerel servis süreci yönetir. Mevcut FLUX çalıştırıcısı yalnız dosya adı değiştirilerek Qwen'e dönüştürülmez. |

Print Extraction ve Lightning LoRA ilk sürümün zorunlu bağımlılıkları değildir. Yeni LoRA, yüz motoru veya ayrı görsel tanıma modeli ancak ölçülmüş ihtiyaçla eklenir. SUPIR/CodeFormer mevcut ticari izin şartları nedeniyle bu plana dahil değildir.

## Kod sınırları ve veri sözleşmesi

- **Arayüz:** yükleme, iki işlem düğmesi, önizleme, durum ve kaydetme. Görsel işleme kararları servis/işçi tarafında kalır.
- **Yerel servis:** dosya doğrulama, iş kuyruğu, işçiyi başlatma/durdurma, çıktıların kaydı. İlk sürümde aynı anda tek ağır iş; gereksiz tekrar tıklama ikinci iş oluşturmaz. Servis yalnız yerel bilgisayara bağlanır.
- **Düzenleme adaptörü:** `enhance` işi kaynak görseli, açık hedef boyutunu ve sabit koruma talimatını alır; çıktı dosyası, gerçek boyut, kullanılan model/sürüm ve süreyi döndürür. Boyut üst sınırı seçilen çalıştırıcının doğrulanmış kapasitesine göre belirlenir; sessiz kırpma olmaz.
- **Arka plan adaptörü:** `remove_background` işi seçilen iyileştirilmiş çıktıyı alır; aynı boyutta alpha içeren PNG döndürür. Saç/ince çizgi, iç dolgular ve açık/koyu zeminde kenarlar değerlendirilir.
- **İş kaydı:** iş kimliği, kaynak/çıktı kimliği, işlem, model revision/hash, parametreler, süre ve hata tutulur. Durumlar: sırada, çalışıyor, tamamlandı, iptal edildi, başarısız. Gerçek çıktı oluşmadan tamamlandı gösterilmez; uygulama açısından tamamlanma kalite kabulü anlamına gelmez.
- **Dosyalar:** her iş ayrı klasörde orijinal, iyileştirilmiş çıktı, varsa şeffaf çıktı ve kısa işlem kaydı tutar. Geçici dosya nihai çıktı adıyla sunulmaz. Kaynak ve onaylanmış çıktılar otomatik silinmez.

Model kaydı; kesin checkpoint/revision, bağımlılıklar, ağırlık formatı, lisans bildirimleri ve doğrulanmış çalışma ortamını içerir. Bunlar indirme aşamasında bir kez sabitlenir; henüz seçilmemiş runtime sürümü veya hash uydurulmaz. Bellek hatasında açık hata verilir; sessiz model değişikliği veya sınırsız yeniden deneme yapılmaz.

## Mevcut koddan yararlanma

Kaynak uygulama:
`C:\Users\USER\Documents\Codex\2026-10-17\referenced-chatgpt-conversation-this-is-an\outputs\dtf-studio`

Başlangıçta yalnız ilgili arayüz bağlantıları, `src/background.mjs`, alpha/kenar yardımcıları ve `service/local-redraw.mjs` / `service/redraw-worker.mjs` sözleşmeleri incelenir. Gerekli parçalar bu çalışma klasöründeki uygulamaya alınır; eski ürünün dizgi/Wix özellikleri taşınmaz. Eski uygulama değiştirilmez. Yeni Qwen işçisi eksik parçadır; mevcut BiRefNet ve uygun iş kuyruğu/arayüz kodu korunur.

## Çalıştırma ve teslim kapısı

RunPod yalnız geliştirme ve gerekli ölçüm ortamıdır. Nihai uygulama yerel model dosyalarıyla çalışacak şekilde paketlenir. İlk teslimden sonraki rutin işlemler ücretli görsel API'sine veya RunPod'a bağlanmaz. Daha sonraki web arayüzü aynı iş sözleşmesini kullanır; webde modelin hangi kullanıcıya ait donanımda çalışacağı ayrıca çözülmeden sıfır barındırma maliyeti veya tarayıcıda çalışma sözü verilmez.

Kayıtlı PC: Ryzen 7 7730U, yaklaşık 38 GiB RAM, AMD bütünleşik grafik. Bu donanımda Qwen'in kabul edilebilir kalite/hızla çalışması açık doğrulama maddesidir. RunPod'da hızlı sonuç, PC teslim kanıtı değildir. Donanıma uygun çalıştırıcı/ağırlık formatı doğrulanamazsa arayüz paketlemeye zaman harcanmadan engel raporlanır. CPU'ya geçiş hızlı çalışma vaadi sayılmaz.

## Başlama sırası ve kaynak kontrolü

1. Kullanıcı başlama sinyali verdiğinde mevcut koddan yalnız gerekli parçaları incele; Qwen için yerel çalıştırma yolunu ve kesin bağımlılık/ağırlık erişimini kontrol et. Yeni geniş model araştırması yapma.
2. Kullanıcının 22 Ekim güncellemesiyle toplam sınır **PRIVATE_AMOUNT**; otomatik yükleme ve ek harcama yok. İlk kurulum/kalite kararı en fazla iki ücretli GPU saati ve kalan bütçeyle sınırlı. Güncel ücret depolama dahil kontrol edilir.
3. Ana adaptörü bağla; küçük, çeşitli ve sabit bir doğrulama grubu üzerinde çalıştır. Yeni görsellere genellenebilirlik için ayar geliştirmede kullanılmamış girdileri de kapsa. Kullanıcıya veri hazırlama işi verme. Rastgele prompt/seed taraması veya bütün adayları indirme yok.
4. Ana motorun içerik koruması, kalite ve süre sonucuna göre yalnız somut eksik için yardımcı işlem ekle. Gerekçe olmadan tekrar çalıştırma; her başarısızlık için hedefli düzeltme kararı ver.
5. Yerel bilgisayarda gerçek çıkarım ve gerekli kalite/hız kabulü sağlandıktan sonra BiRefNet akışını, kurulum paketini ve kısayolu tamamla. Paketlenmiş uygulamayı gerçek görselle bir kez uçtan uca doğrula.

Kodlama ve paketleme sırasında kullanılmayan GPU kapatılır; ücretli depolama dahil açık kaynaklar izlenir. Bütçe/kurulum sınırına gelindiğinde yeni harcama başlatılmaz. Gerekçe ve sonuç kısa kaydedilir.

## Teslim ölçütleri

- Gerçek yeni girdide içerik korunarak üretken iyileştirme; logo/yazı, fotoğraf/yüz ve ince detay içeren farklı örneklerde kontrol. Sadece piksel sayısının artması başarı değildir.
- Hedef: ChatGPT düzeyinde kalite ve hız. Karşılaştırılabilir kaynak/referans varsa yan yana kıyas; yoksa eşitlik iddiası kurulmaz. Elle düzeltilmiş örnek genel otomatik başarı sayılmaz.
- İsteğe bağlı arka plan işlemi gerçek alpha üretir; kenarlar ve iç dolgular korunur.
- Kullanıcının PC'sinde kurulu sürüm kendi modelleriyle gerçek çıktı üretir; süre ve donanım kaydedilir. RunPod sonucu yerel sonuç yerine sunulmaz.
- Kaynak kodu, sürümü sabitlenmiş bağımlılıklar, gerekli lisans bildirimleri, kurulum/kısayol ve kısa kullanım bilgisi teslim edilir. Kanıtlanmamış koşul varsa proje bitmiş olarak sunulmaz.

## Devam özeti

**Tamamlanan:** iki işlevli ürünün bileşenleri, veri akışı, sınırları ve uygulama sırası belirlendi.
**Kritik karar:** ana motor Qwen-Image-Edit-2511; BiRefNet mevcut; yardımcılar yalnız ihtiyaçla.
**Açık konu:** seçilen motorun gerçek genel kalite/hızı ve bu PC'deki bağımsız çalışması.
**Sıradaki iş:** başlama sinyalinden sonra yukarıdaki 1. adım. Şu an model indirme, inference, kurulum veya harcama yok.

Önceki doğrulanmış kaynaklar ve lisans incelemesi: `MIMARI_KARSILASTIRMA.md`. Eski baskı/LoRA kontrolü genel ürünün zorunlu başlangıç koşulu değildir.

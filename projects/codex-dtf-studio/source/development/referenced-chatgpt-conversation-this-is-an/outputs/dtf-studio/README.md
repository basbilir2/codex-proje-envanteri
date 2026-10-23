# DTF Studio — çalışan ilk sürüm

Bu sürüm dosya yükleme ve DTF baskı hazırlığına odaklanır. Üyelik, ödeme ve kullanım hakkı zorunluluğu yoktur.

`dist/DTF-Studio.html` dosyasını Chrome veya Edge ile açın. Kurulum ve sunucu gerekmez. Arka plan kaldırma için ilk kullanımda internet gerekir; model indirmesi yaklaşık 183 MB'dır. Görselleriniz bilgisayarınızda işlenir.

## Kullanım

1. PNG, JPEG veya WebP tasarım ekleyin. Bir dosya en fazla 25 MB / 50 megapiksel olabilir.
2. Gerekirse arka planı kaldırın ve şeffaf boşlukları kırpın.
3. Her tasarımın cm ölçüsünü ve adedini belirleyin. En/boy değişikliklerinde oran korunur. Şeffaf alanı kırpmak, basılacak içeriğin mevcut fiziksel ölçüsünü koruyarak dış ölçüyü küçültür.
4. Film eni, kenar payı, parça aralığı ve DPI seçin. Adet modunda film uzunluğu hesaplanır. Metre modunda tek tasarımın seçilen film uzunluğuna sığan adedi hesaplanır.
5. Arka plan, kenar ve AI düzenlemelerini tamamlayıp Dizgiye geç düğmesine basın. Bundan sonra ölçü/adet/film ayarları değişince dizgi otomatik yenilenir. Önizlemeyi kontrol edin, PNG veya PDF indirin.

PNG şeffaftır ve gerçek DPI metadatası taşır. PDF'nin sayfa ölçüsü gerçek film ölçüsüdür. RIP/yazdırma sırasında %100 / gerçek boyut kullanın. Aynalama seçeneğini RIP'in ayrıca uyguladığı aynalamayla birlikte değerlendirin. Çıktı RGB'dir; beyaz mürekkep, ICC profili, toz ve kür ayarları baskı sisteminde yapılır.

## Açık sınırlar

- AI 2× iyileştirme ücretsiz ESRGAN Slim modeliyle cihazda çalışır; ilk kullanımda internet gerekir. Olası ayrıntılar tahmin edilir, kaynakta bulunmayan gerçek ayrıntıyı geri getirme garantisi yoktur. Özgün kaynak DPI ve AI çıktı DPI ayrı gösterilir. Çıktı sınırı 24 megapikseldir.
- AI maske 512×512 modelden üretilir ve kaynak renkleriyle kenarları iyileştirilir. Fotoğraf ayırmada silgi, detayı geri getirme fırçası ve son fırçayı geri alma vardır. Kenarları temizle düşük opaklıklı artıkları azaltır; ince çizgileri ve beyaz baskıyı önizlemede kontrol edin.
- Dizgi dikdörtgen esaslıdır. Şeffaf konturları iç içe geçirmez ve matematiksel optimum garantisi vermez.
- Bir işte en fazla 30 tasarım / 500 parça; dizgi uzunluğunda 20 m sınırı vardır.
- PNG için güvenli sayfa sınırı 80 megapiksel / 16384 px. Büyük işler tasarımlar kesilmeden, ölçü ve DPI korunarak numaralı PNG dosyalarına ayrılır ve ZIP verilir. Kesilmeden bölünemeyen yerleşimde gerçek ölçülü PDF hazırlanır. PDF tasarımları doğrudan yerleştirir; tüm filmi tek tuvale çizmez. ZIP boyut sınırı 512 MB. Çok uzun PDF fiziksel ölçüsü UserUnit ile korunur; RIP uyumluluğunu kontrol edin.
- Dosyalar veya projeler kalıcı kaydedilmez. Sayfayı yenilemek çalışma alanını sıfırlar.
- Fiziksel DTF baskı testi yapılmadı; gerçek ölçü, piksel ve şeffaflık dijital olarak kontrol edildi.

## Wix

Yeni site kimliği: `b9ff64fa-0b6c-49da-b3b3-32efbf93b84e`.

DTF uygulaması ana sayfaya HTML gömme olarak eklendi. Böylece Custom Element'in Premium/domain gereksinimine bağlı kalmadan uygulama önizlemesi çalışır. Üyelik uygulaması ilk kurulum sırasında eklenmişti; kullanıcının sonraki talebi üzerine ücretli paketlerin ve backend kurulumunun devamı durduruldu. Paket satışı açılmadı, ödeme bağlanmadı.

Gömülecek son tek dosya: `dist/DTF-Studio.html`. Velo sayfa kodu gerekmez. Wix'e yeni HTML sürümü uygulanırsa `filesusr.com` üzerindeki dosya bağlantısı değişir.

`wix/` ve `service/` altında önceki üyelik mimarisinin taslak kaynakları korunur. Canlı abonelik sistemi olarak kurulmuş veya doğrulanmış sayılmaz. Bu sürümün çalışması bu dosyalara bağlı değildir.

## Kaynak ve doğrulama

Geliştirici için: `npm ci`, `npm run build`, `npm test`. Testler: dizgi sınırları ve boşluklar; dönüş; metre hesabı; geçersiz girdi; DPI metadatası; PNG şeffaflığı; PDF fiziksel ölçüsü. Taslak quota modülünün yarış koşulu testleri de kaynak pakette korunur.

Kaynak lisansları: `THIRD_PARTY_NOTICES.txt`. AI model sürümü `962e67969ec6acec9c19fab76acee4f5e22e990c` olarak sabitlenmiştir.

## Fotoğraftan baskıyı ayırma

Yükleme alanında varsayılan “Ürün fotoğrafı — baskıyı ayır” seçeneği, opak fotoğrafta otomatik baskı alanı önerisini açar. Şeffaf tasarımlar doğrudan eklenir. Kullanıcı fotoğraf üzerinde sürükleyerek bölgeyi düzeltebilir; zemin temizleme seviyesi ve açık/koyu kontrol zemini vardır. Sonuç ayrı bir PNG olarak indirilebilir veya ölçülendirme ve dizgiye aktarılabilir.

Bu özellik tarayıcıda yerel renk/kontrast analizi ve kumaş zemini kestirimi kullanır; ücretli API veya model indirmesi yoktur. Genel amaçlı semantik AI tanıma değildir. Düz veya az dokulu kumaşta uygundur; karmaşık desen, gölge, baskıyla aynı renk kumaş ve perspektif bozulması için kusursuz sonuç garantisi yoktur. Fotoğrafta bulunmayan ayrıntıları yeniden üretmez. Bölge önerisini ve maskeyi kullanıcı doğrulamalıdır.

Verilen 738 × 1600 px MAVİ tişört fotoğrafında baskı otomatik bulundu: x=286, y=548, 278 × 184 px çalışma bölgesi; baskı içeriği yaklaşık 220 × 127 px. Motorun gerçek fotoğraf testi geçti. İşletim sistemi dosya seçicisiyle tarayıcı otomasyon testi tamamlanmadı.


## Wix üzerinden açılış

Canlı giriş: https://izmirdedtf.wixsite.com/dtf-studio

HOME sayfa kodu `wix/pages/Home-free.js`, stüdyoyu aynı sekmede tam sayfa açar. Uygulama aynı Wix sitesinin dosya alanında barınır. Bu sürümde üyelik ve ödeme zorunluluğu yoktur. Editördeki HTML bileşeni güncel uygulama kaynağını korur; canlı giriş iframe indirme/yükleme kısıtlarına bağlı değildir. Yeni HTML sürümü yüklenince Home-free.js içindeki studioUrl de yeni Wix kaynak adresine güncellenmelidir.

Ana araçlar: Baskıyı ayır, Arka planı kaldır, AI 2× iyileştir. Şeffaf alanı kırp/Kenarları temizle/Orijinale dön, Diğer araçlar altında; film aralığı, kenar payı, dönüş ve aynalama İnce ayarlar altında. Silgi ve detay geri getirme fırçaları Baskıyı ayır ekranındadır.

## 1 piksel maske daraltma

Arka plan kaldırma ve fotoğraftaki baskıyı ayırma, son maskeyi kaynak görsel çözünürlüğünde 1 piksel içeri daraltır. Görselin en/boyu korunur. Dış sınır ve iç boşluklarda 3×3 minimum alfa uygulanır; yumuşak alfa değerleri korunur. İşlem modelin 512 piksel maskesinde değil, kaynak boyutuna iyileştirilmiş maskede bir kez uygulanır.


## Hazırlık önce, dizgi sonra

Yeni görseller önce hazırlık aşamasına girer. Baskıyı ayırma, arka plan silme, kenar temizliği, fırça ve AI büyütme bu aşamada yapılır. Dizgiye geç basılana kadar otomatik yerleşim ve dosya indirme kapalıdır. Dizgi aşamasında görsel araçları gizlenir; Görselleri düzenle ile hazırlığa dönülür. Yeniden görsel düzenlemesi veya yeni dosya ekleme mevcut dizgiyi ve indirme bağlantısını iptal eder; hazırlıktan sonra tekrar Dizgiye geç gerekir. Ölçü/adet değişiklikleri dizgi aşamasında otomatik güncellenmeye devam eder.

## Büyük görsel kontrolü

Hazırlık aşamasında seçili tasarım dama veya koyu zeminde büyük gösterilir. Küçük görselin üzerine basılarak düzenlenecek tasarım seçilebilir. Bu önizleme çıktı piksellerini değiştirmez. Dizgiye geç sonrasında aynı alan film yerleşimine dönüşür.


## Tam ekran görsel düzenleyici — 19 Ekim 2026

Görsel hazırlığı tek pencerede yapılır: fotoğraftan baskıyı ayırma, AI arka plan kaldırma, kenar temizleme, AI 2× büyütme, şeffaf boşluk kırpma, silgi/geri getirme ve son işlemi geri alma. Pencere ekran yüksekliğini kullanır; masaüstünde kaynak, sonuç ve araçlar yan yanadır. Küçük ekranlarda gerekli alanlar kayar; onay düğmesi sabittir. Vazgeç mevcut kaydedilmiş görseli değiştirmez.

Onayla ve dizgiye geç görseli kaydeder ve dizgiyi açar. Birden fazla yeni görsel varsa önce sıradaki görsel açılır; hepsi onaylandıktan sonra dizgiye geçilir. Önceki ayrı araç düğmeleri Görseli düzenle altında birleşmiştir. AI çıktı boyutu ile kaynak boyutu ayrı korunur; tekrar düzenleme AI sonucunu veya maskeyi kendiliğinden sıfırlamaz.

1 px içeri daraltma varsayılan olarak açıktır; çok küçük/ince çizgilerde pencereden kapatılabilir. AI maskesinin 0/255 sınırları da kaynak renkleriyle iyileştirilir; düşük çözünürlüklü maske sert basamaklarla büyütülmez. WebGL kullanılamıyorsa AI büyütme CPU ile çalışır; bu daha yavaştır. Model veya küçücük kaynak tüm ayrıntıyı doğru yeniden oluşturma garantisi sağlamaz.

Ardışık kumaş ve AI temizliğinde 1 px daraltma yalnız bir kez uygulanır; geri alma ve düzenlemeye dönüş bu bilgiyi korur. Boş/şeffaf sonuç onaylanamaz. Model giriş/çıkış işlemleri resmi model kartıyla karşılaştırıldı: https://huggingface.co/studioludens/birefnet-lite-512 (logits üzerine sigmoid, 512 px maske, kaynak boyutuna kenar duyarlı aktarım).


## 19 Ekim — önce büyütme, sonra temizleme

Güncel akış (20 Ekim): Fotoğraf yüklendiğinde yalnız baskı alanı önerilir ve kumaşıyla kırpılır. AI ve maske otomatik çalışmaz. Kullanıcı önce AI 2× veya ikinci kademeyi seçerek netliği kontrol eder; sonra Arka planı temizle düğmesi mevcut düzenlenmiş piksellerden kumaşı ayırır. Temizlik düğmesi de gizlice AI büyütme başlatmaz. Temizleme ayarları maskelemeden sonra açılır. Bölge yeniden seçilirse yeniden kumaşlı hazırlığa dönülür; maskeden önce dizgi onayı kapalıdır. Hazır/şeffaf tasarımların mevcut düzenleme akışı korunur.

Açık tek renk baskıda I=alpha*ink+(1-alpha)*fabric ayrıştırması kullanılır. Harf içlerinde gerçek mürekkebe uzak kumaş pusu çıkarılır, yumuşak kenarlar ve ayrı küçük harf/noktalar korunur. Otomatik mod renkli baskıyı bu işleme zorlamaz; tür elle de seçilebilir. 1 px daraltma açık renkli tek piksel çizgi ve noktalara karşı korumalıdır. WASM hızlandırması WebGL olmayan cihazlarda CPU öncesinde denenir; kaynak çözünürlüğü ve AI çıktı çözünürlüğü ayrı kalır.

Verilen WhatsApp Image 2026-10-19 at 13.34.07.jpeg ile gerçek tarayıcı akışı tamamlandı: seçili baskı ve EST.1991 birlikte bulundu; çıktı672×386px, kaynak336×193px, AI2×. PNG alpha0..255 olarak doğrulandı. Küçük kaynak fotoğrafın eksik ayrıntısını kusursuz geri getirme garantisi yoktur. Pencerenin araç alanı502/502px; taşma yok.


## 20 Ekim — ikinci kademe çizgi netliği

AI ile geliştir2× yanında 2.kademe netleştir2× seçeneği vardır. Örneğin kullanıcı AI2× uyguladıktan sonra ikinci kademe toplam4× boyuta çıkarır. Yeni kademe aynı ESRGAN büyütmenin ardından mevcut alfayı, ince çizgiyi ve sınırlı parlaklık ayrıntısını işler; yeni öğe/yazı üretmek için generatif çizim yapmaz. Şeffaf delikler ve kaynakta sıfır alfa olan alanlar netlik filtresinde korunur. RGB düzeltmesi kanal başına en fazla12/255, alfa düzeltmesi80/255 ile sınırlıdır. Kaynak ve çıktı DPI ayrı kalır.

Üst üste netlik birikimini önlemek için kademe bir kez uygulanır; Son işlemi geri al önceki boyut/maske/işlem durumunu geri getirir. Onaydan sonra tekrar açmak aynı işlemi tekrar uygulamaz. İkinci kademe12MP çıktı sınırındadır. Renk, çizgi ve küçük yazı mutlaka önizlemede kontrol edilmelidir; düşük çözünürlüklü kaynaktan eksik ayrıntı garantili geri kazanılmaz.

SAT doğrulaması kullanıcı tarafından paylaşılan uygulama ekranındaki grafik bölgesinden334×247 çalışma örneği çıkarılarak yapılmıştır; özgün SAT PNG'si verilmediği için bu doğrudan kaynak dosya testi olarak sunulmaz. Gerçek ESRGAN+WASM ve netlik filtresi668×494 çıktı üretti. SAT-Netlik-Karsilastirma.png karşılaştırması ve SAT-Ikinci-Kademe-Deneme.png şeffaf çıktıdır.


## 2026-10-20: quality engines, unchanged interface
Robust cloth estimation chooses a planar or quadratic illumination model using held-out border samples; measured texture sets a conservative noise floor. Automatic neutral dark ink on light cloth is supported alongside light and coloured prints. Native alpha finishing preserves holes and thin ink. The general BiRefNet path refines uncertain colours/alpha against local confident foreground/background and removes colour spill; 512px tiles include a 12px halo to bound memory. AI upscaling retains the original alpha, extends edge colours underneath transparency, overlaps patches by 16px, and bounds neural luminance/chroma changes against the source. Second-stage detail remains optional. Model initialization is shared and recoverable; inference input/output tensors are disposed. No UI controls, membership or output dimensions changed.
Validation: 15 focused tests passed. Real browser ESRGAN/WASM preprocessing of the supplied Mavi photograph produced a 672x386 transparent PNG; local fixture, not a Chrome file-picker test. See work/engine-upgrade/metrics.json and outputs/Mavi-Motor-Gercek-Cikti.png. Perfect recovery of absent photo detail or production RIP/physical print fidelity is not claimed.


## Local fine-text finishing
The optional fine-text button in the preparation dialog lets the user drag a rectangle on the processed image. It applies seven bounded non-generative Richardson-Lucy iterations to the existing alpha only, with feathered selection borders. It neither reads/retypes text nor changes the font. Pure-engine RGB and pixels outside the rectangle are unchanged; zero-alpha holes remain zero, image size and source DPI remain unchanged. The operation is undoable and runs locally without model downloads. Very small lettering cannot be perfectly recovered. Source: src/fine-text.mjs; tests: tests/fine-text.test.mjs.


## 20 October: explicit preparation stages
Upload and region selection only crop original opaque pixels. AI enhancement is optional and explicit; background removal operates on the current enhanced crop. Undo includes pre-mask stage and raw mask cache metadata. Confirm and alpha editing tools are blocked during opaque photo preparation. Source DPI stays distinct from upscaled output. No automatic AI or masking on upload, area selection, or reset.


### İki kalite modu — 20 Ekim 2026

- **Orijinali koru:** mevcut ücretsiz tarayıcı motoru, fotoğraftan alan seçimi, isteğe bağlı ESRGAN, açıkça istenen arka plan temizliği, onay ve dizgi. Kaynağın vermediği ayrıntıyı garanti etmez.
- **AI ile yeniden oluştur:** Apache-2.0 FLUX.2-klein-4B Q4_0, Qwen3-4B Q4_K_M ve FLUX2 VAE; stable-diffusion.cpp CPU çalıştırıcısı. Ücretli API yok. Bu bilgisayarda 512×336 örnek 247,6 saniyede gerçekten üretildi. 5,3 GB model dosyası proje paketine dahil değildir. Harfler/dokular yeniden yorumlanabilir; genel bir kusursuzluk garantisi yoktur.
- İki mod düzenleme penceresinde yer alır. Modlar arası geçişte sonuçlar ayrı tutulur. Üretim arka planı kendiliğinden silmez; kullanıcı ayrıca temizleyip onaylar. Yapay fon için renk ayırma ve kenar bulaşmasını giderme ayrı motordur.
- **Canlı bağlantı henüz kurulmadı.** Yerel arayüz testi, daha önce gerçekten üretilen PNG'yi açıkça etiketlenmiş örnek olarak kullanır; Wix uçtan uca testi veya yeni çıkarım değildir. Bağlanmamış mod çalışıyormuş gibi gösterilmez.

#### Wix bağlantısının hazırlanmış dosyaları

1. `wix/backend/redraw-queue.js` → Velo backend modülü.
2. `wix/backend/redraw-http.js` içeriği → var olan `backend/http-functions.js` ile birleştirilmeli (var olan HTTP işlevlerini silme). `GET/POST/OPTIONS dtfAi`.
3. `wix/backend/redraw-setup.web.js` → yöneticiye özel bir defalık `initializeRedraw`; `DtfAiQueue` koleksiyonunun tüm CRUD izinleri yalnız ADMIN olmalı.
4. Site sahibinin oluşturacağı `DTF_REDRAW_WORKER_KEY` sırrı Wix Secrets Manager'a kaydedilmeli. Aynı anahtar yalnız yerel model klasörü `private/wix-worker.json` içinde `{"workerKey":"..."}` şeklinde bulunmalı. Anahtar tarayıcı paketine, loga, ZIP'e, URL'ye veya sohbete girmemeli.
5. `service/redraw-worker.mjs` yalnız dışarıya HTTPS ile bu Wix sitesinden iş alır. Bilgisayarda dışarıdan erişilecek port/tünel açılmaz. Bir işçi aynı anda bir iş çalıştırır; bilgisayar açık olmalıdır. İşçi kapanırsa mod erişilebilir görünmez.
6. Önce yalnız sahibiyle özel bağlantı testi; sonra aynı Wix sitede uygulama güncellemesi ve yayın doğrulaması. `src/reconstruction.mjs` sabit adresi bu sitenin `_functions/dtfAi` uç noktasıdır.

İş kuyruğu: tahmin edilemez işe özel görüntüleme bileti; ayrı işçi anahtarı; kamuya açık CMS okuma yok; en fazla iki bekleyen/çalışan iş (eşzamanlı başvuru yarışında saatlik dört sınırı üst sınırdır); saatlik toplam dört başvuru; bir saatlik iş süresi; sonraki işçi kontrolünde süreli kayıt temizliği; başarı/iptalde kaynak görsel silinir. Sonuç aktarımı CMS öğe sınırı altında tutulur. İptal çalışmakta olan çıkarımı bir sonraki işçi kontrolünde durdurur. Yeni site ziyaretçisi bu bilgisayarın toplam ücretsiz saatlik kapasitesini tüketebilir; halka açık yoğun kullanım için üyelik/izinli kullanıcı kapısı ayrıca gereklidir ve bu aşamada etkin değildir.

Bu bağlantı yeni ve kalıcı bir işçi erişimi oluşturduğu için canlı sır ve bağlantı adımı kullanıcı onayından önce uygulanmadı. Yerel örnek, test ve kod hazır; canlı Wix kurulumu tamamlandı olarak sunulmamalı.

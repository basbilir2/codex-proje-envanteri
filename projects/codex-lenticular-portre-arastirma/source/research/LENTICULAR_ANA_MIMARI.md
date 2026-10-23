# Lenticular Studio — mevcut uygulamaya motor ve animasyon ekleme mimarisi

Tarih: 8 Ekim 2026. Durum: tasarım ve araştırma; uygulama yapılmadı.

## 1. Bağlayıcı kapsam

Bu tasarım çalışan Lenticular Studio'yu genişletir. DPI, PPI, LPI, ölçü, yön, faz, ICC, beyaz kanal, kalibrasyon ve baskı motoru zaten vardır. Kullanıcının Grondo UV yazıcıda sık kullandığı 1200 DPI bir sabit veya yeni varsayılan değildir. Bütün mevcut değişken değerler ve kayıtlı seçimler korunur.

Ana yeni gereksinim: **yalnız iki fotoğraf verilse bile gerçek ara kareler üreterek akıcı animasyon hazırlamak ve mevcut lenticular baskı hattına bağlamak.** Kareyi tekrar etmek, hareket ara karesi üretmek ve morph üç ayrı işlemdir.

İncelenen uygulama kökü:

    C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1

Bu belgelerin bulunduğu g-p-6ac173361d8c8191a1449be5154f589f klasörü ayrı proje aynasıdır; burada uygulama kaynakları bulunamadı. Uygulayıcı yanlış klasörde yeni bir program oluşturmamalıdır. Kaynak konumu uygulama başlangıcında tekrar doğrulanmalıdır.

Kusursuzluk iddiasının yerine ölçülebilir sözleşmeler ve kabul koşulları konulmuştur. Fiziksel lens/yazıcı sonucu, iki fotoğraf arasındaki bilinmeyen hareket ve görünmeyen yüzeyler yalnız yazılım incelemesiyle garanti edilemez.

## 2. Kodda doğrulanan mevcut temel

| Mevcut parça | Korunacak görev | Eklenecek bağlantı |
|---|---|---|
| depth.py / detail_depth.py | DA3 derinliği, ayrıntı ve yüzey düzeltmeleri | İsteğe bağlı alternatif model adaptörü |
| repair.py / layers.py | Fırça, sabit derinlik, katmanlar, GrabCut sınırı, Telea | Seçim/matting ve ortak sahne tamamlama |
| geometry.py / runner.py / blender_scene.py | Kamera geometrisi ve Blender görünüşleri | Blender sonucunu ortak FrameSet'e çevirme |
| printing.py | Nr→Ne, interlacing, ICC, TIFF, beyaz maske, pitch, simülasyon | Kamera gerektirmeyen kare kaynağı ve açık kanal planı |
| pipeline.py | JSON durum, tek işçi, iptal, önbellek, profil | Sekans varlığı, efekt işi, aşama bazında yeniden kullanım |
| studio.py / web/ | Yerel HTTP ve Türkçe arayüz | Mevcut ekrana efekt modu ve kare şeridi |

Önemli kod bulguları:

- printing.frame_mapping(), kamera positions/zero alanlarından açı çıkarıyor; zaman sıralı fotoğraflar bunun yerine doğrudan bağlanamaz.
- printing.encode(), kamera ekseni ve Blender job.json yapısı bekliyor. Animasyon için sahte kamera dosyası üretmek doğru çözüm değildir.
- pipeline.Studio.start(), render/print/full/pitch/depth aşamalarını kabul ediyor; sekans işi henüz ayrı bir tür değil.
- runner.preview() mevcut görünüşlerden ileri/geri önizleme yapıyor. Bu, iki fotoğraftan hareket ara karesi üreten motor değildir.
- web/app.js suggestedViews(), min(PPI,DPI)/LPI tabanlı öneri yapıyor. Bu değer fiziksel olarak ölçülmüş kullanılabilir kanal sayısı olarak sunulmamalıdır; yeni kapasite raporu raster hesabı ile optik ölçümü ayrı gösterecek.
- Beyaz alt baskı şu anda tam alan maskesi. Nesneye özel beyaz desteği ayrı geliştirmedir.
- Baskı PPI'si şu anda tek sayıdır; bağımsız X/Y PPI desteği genişletmedir.
- Güncel kodda RENDER_ENGINE_VERSION=15; baskı sınırı 500 MP, tek kenar 100000 piksel, Ne=2–64. Mevcut mimari belgesindeki sürüm 8 / 400 MP notları güncel kodu tam yansıtmıyor. Başlangıçta kod esas alınır; bu çalışma bu sınırları değiştirmez.

Bunlar kaynak incelemesi bulgularıdır. Bu turda uygulama, render, test veya fiziksel baskı çalıştırılmadı.

## 3. Profesyonel yazılımlardan alınan ürün gereksinimleri

Üretici belgeleri yetenek beyanıdır; karşılaştırmalı performans testi yapılmadı. Ticari yazılımların iç algoritmalarının aynısına sahip olduğumuz iddia edilmez.

| Referans | Belgelenen özellik | Bizdeki karşılığı |
|---|---|---|
| [Triaxes 3DMasterKit](https://triaxes.com/3dmasterkit/) | Flip, animasyon, morph, zoom; PSD/derinlik katmanı ve çoklu görünüş | Ayrı efekt sağlayıcıları, ortak kare sözleşmesi |
| [Triaxes Legend](https://triaxes.com/legend/) | UV doğrudan baskı, aynalama, alfa, hizalama, farklı X/Y çözünürlüğü, panel bölme | Mevcut UV hattını koruma; ileri aşamada anizotropik raster ve panel |
| [Imagiam Lenticular Suite](https://www.imagiam.com/lenticular-software/features) | ICC, kalibrasyon, katman içinde animasyon, 16-bit, büyük dosya ve farklı X/Y çözünürlüğü | Katman zaman çizelgesi, renk sözleşmesi, diskten işleme |
| [3DZ Lenticular Suite](https://www.lenticularsoftware.de/onlinetools/index.htm) | Yerel işleme, otomatik hizalama, katmanlı animasyon, optik/mekanik pitch ayrımı | Yerel motorlar, referansla hizalama, açık kalibrasyon türü |

Öncelik: iki fotoğraftan animasyon → flip/sekans → video/zoom/morph → nesne seçimi ve kenarlar → üretim ölçeği. Yeni RIP yazılması veya mevcut programın başka bir teknolojiyle yeniden kurulması bu tasarımın hedefi değildir.

## 4. Ana mimari kararı

**Kare üretimini, karelerin optik kanallara atanmasını ve baskı kodlamasını ayır.** Tek uygulama içinde modüller yeterlidir; mikroservis, bulut veya yeni arayüz çatısı gerekmez.

~~~mermaid
flowchart TD
  A[Mevcut fotoğraf ve derinlik akışı] --> B[Mevcut Blender görünüşleri]
  C[İki fotoğraf] --> D[Hareket ara karesi veya morph]
  E[Kare dizisi veya video] --> F[Seçim, hizalama ve efektler]
  B --> G[Ortak FrameSet]
  D --> G
  F --> G
  G --> H[ChannelPlan: Ne kanala açık eşleme]
  H --> I[Mevcut telafi ve interlacing motoru]
  I --> J[ICC TIFF, beyaz, kalibrasyon ve rapor]
  H --> K[Kanal ve açı önizlemesi]
  G --> L[Zaman önizlemesi]
~~~

Bir akış için depth veya Blender gerekmiyorsa çalıştırılmaz. Fotoğraf dizisinin ve iki fotoğraflı düz animasyonun baskısı Blender kurulumu veya AI depth çalışması beklememelidir.

### 4.1 Sayıların anlamı

| Alan | Anlam |
|---|---|
| Ns | Yüklenen kaynak görsel sayısı; iki fotoğraf için 2 |
| Nt | Üretilmiş zaman kareleri; ara kareler dahil |
| Nr | Üretilmiş kamera görünüşleri; yalnız 3D türünde anlamlı |
| Ne | Baskıda kodlanan kanal sayısı |
| preview_fps | Ekrandaki oynatma hızı; fiziksel baskı hızı değildir |

Örnek: Ns=2 → Nt=24 ara kareli dizi → seçilen Ne=8 baskı kanalı. Bu yalnız örnektir; 8, 24 veya 1200 hiçbir ayara sabitlenmez. Nt=48 olması lensin 48 bağımsız hareket anını ayırabildiği anlamına gelmez.

### 4.2 Veri sözleşmeleri

Yeni sözleşmeler küçük Python veri tipleri ve sürümlü JSON olarak tanımlanır. Aynı alanın doğrulaması farklı yerlerde tekrar yazılmaz. İlk aşamada yeni doğrulama çatısı bağımlılığı gerekmez.

| Sözleşme | Zorunlu içerik |
|---|---|
| AssetRef | Kimlik, kaynak hash'i, dosya türü, yön, boyut, ICC; kaynak salt okunur |
| FrameSet v1 | kind, sıralı kare referansları, ortak tuval, renk/alfa semantiği, motor kimliği/revizyonu, kaynak hash'leri |
| FrameRecord | Kare kimliği, dosya/hash; türüne göre time_s veya view_coordinate; gerçek/üretilmiş etiketi |
| EffectSpec v1 | Efekt türü, kaynaklar, kırpma/hizalama dönüşümleri, zaman eğrisi, anahtar kareler, motor ve parametreleri |
| ChannelPlan v1 | Ne uzunlukta açık örnek listesi; kanal→kare veya üretim örneği; yön/sıra; tekrarlar ve atlanan kareler |
| EngineManifest v1 | Girdi/çıktı yetenekleri, sürüm, model hash'i, lisans kaydı, donanım koşulu, deterministik çalışma bilgisi |
| CalibrationProfile v1 | Lens partisi, makine/RIP modu, DPI X/Y, raster PPI X/Y, yön, malzeme/ICC, bakış mesafesi ve test kanıtı |
| ExportReport v2 | Yukarıdaki kimlik/hash'ler, Ns/Nt/Nr/Ne, ölçü, kaynak çözünürlüğü, kanal kapsaması, kalite durumu |

FrameSet.kind: multiview_3d, time_sequence veya hybrid_path. Flip ve zoom üreticileri time_sequence verir. Nr, zaman dizisinde null olur; Nt alanına Nr yazılmaz.

Her FrameSet'te ortak boyut ve açık renk uzayı zorunlu. Alfayı taşıyan karelerde straight/premultiplied tanımı kayıtlıdır; bileştirme lineer ışıkta premultiplied alfa ile yapılır. Eski 8-bit sRGB çıktıları adaptörle aynı görünümde kabul edilir. Yeni float/16-bit işleme, eski render sonucunu sessizce değiştirmez.

Önerilen dar arabirimler:

~~~text
LegacyRenderAdapter.open(render_folder) -> FrameSet
EffectEngine.plan(assets, effect_spec) -> EffectPlan
EffectEngine.render(effect_plan, job_context) -> FrameSet
FrameProvider.read_region(frame_id, rect, scale) -> ImageTile
ChannelPlanner.plan(frameset, effect_spec, print_spec) -> ChannelPlan
PrintEngine.encode_frames(frameset, channel_plan, output, print_spec, job_context)
~~~

Eski encode(render_folder, ...) dış çağrısı korunur; legacy adaptör üzerinden yeni dar çekirdeğe geçer. Adaptör kendiliğinden eski çıktı klasörüne manifest yazmaz. Yeni raporlar yeni iş klasörüne yazılır.

## 5. İki fotoğraftan akıcı animasyon motoru — zorunlu özellik

### 5.1 Üç farklı davranış

1. **Hareket:** aynı sahnenin iki anı. İki yönlü hareket kestirimi ve ara kare sentezi kullanılır. İlk aday yerel RIFE adaptörüdür; OpenCV optik akış daha hafif alternatif olur.
2. **Morph:** farklı şekil veya kompozisyonlar. Eşleşen kontrol noktaları/nesne maskeleri üzerinden şekil dönüşümü ve doku geçişi yapılır. Fotoğraflar ilişkisizse kullanıcı referans noktalarıyla yönlendirebilir.
3. **Yumuşak geçiş:** renklerin lineer ışıkta dissolve edilmesi. Kullanıcı bu efekti seçerse uygulanır; hareket üretildi diye etiketlenmez.

Otomatik mod, eşleşme kalitesine göre öneri yapar. Güven düşükse sorunlu bölgeleri gösterir. Sessizce A/B tekrarına veya dissolve'a düşüp 'akıcı hareket tamamlandı' demez. İki ilişkisiz fotoğraftan fiziksel olarak doğru ara hareket garanti edilmez.

### 5.2 İşlem sırası

1. İki kaynağı hash ile kaydet; EXIF ve ICC'yi çöz; kullanıcının görebildiği ortak kırpma/tuval oluştur.
2. İstenirse sabit arka plan veya seçilen referans üzerinden kamera titremesini hizala. Asıl nesne hareketini ortadan kaldırma. Kaynaklara dönüştürme yazma.
3. A→B ve B→A eşleşmeleri; örtülen/açılan bölgeler ve tutarsızlık haritası çıkar. AI motorunun vermediği güven puanı varmış gibi davranma; hesaplanan kalite göstergesinin yöntemi raporda yazsın.
4. Seçilen Nt için t değerleri üret; uçlar 0 ve 1. Motor ara konumları üretir. t=0 ve t=1 normalize edilmiş A/B'nin aynısıdır; uç fotoğrafları model yeniden üretmez.
5. Akış tabanlı sağlayıcıda ileri/geri warp, örtüşme görünürlüğü ve alfa birleştirmesi kullan. RIFE sağlayıcısında desteklenen t aralığı ve padding/ölçek davranışı doğrulansın. Gerçek desteklenmeyen özellik işaretlenmesin.
6. Kareler arasında yüz, yazı, logo, ince kenar ve arka plan titreşimini denetle; sorun haritası/uyarı üret. Kullanıcının koruduğu yazı/logo katmanı ayrı sabit katman kalabilir.
7. Tek yön, ters veya ileri/geri dizi kur. Ping-pong dizisi 0…Nt−1,Nt−2…1 olur; uç kareler gereksiz iki kez eklenmez.
8. FrameSet ve zaman önizlemesi oluştur; ChannelPlan mevcut Ne'ye göre seçimi açıkça raporlasın.

Hız eğrisi yalnız t örneklerini değiştirir. Aynı açı altında daha uzun görünmesi istenen bir duruma daha fazla komşu kanal ayrılabilir; bu işlem yeni hareket ayrıntısı üretmez.

### 5.3 RIFE kararının dayanağı ve sınırı

[Resmî RIFE deposu](https://github.com/hzwer/ECCV2022-RIFE) iki görüntü arasında ara zamanlarda kare üretimini ve iki girdiden çok sayıda ara kare örneğini belgeliyor. Bu nedenle çift fotoğraf motoru için uygun ilk adaydır. Bu bilgisayarda hız, Windows/CPU/GPU uyumu ve baskı kalitesi henüz ölçülmedi. Uygulama sırasında kod revizyonu, uygun checkpoint, ağırlık hash'i ve dağıtım koşulları sabitlenir. Resmî depoda kod MIT olarak listeleniyor; seçilen ağırlığın koşulları ayrıca kaydedilir.

[OpenCV optik akış](https://docs.opencv.org/4.x/d4/dee/tutorial_optical_flow.html) iki kare arasındaki hareket alanını hesaplamak için temel sağlar. Tek başına akış hesaplamak tam ara kare motoru sayılmaz; görünürlük ve yeniden örnekleme adımları ayrıca uygulanır.

## 6. Diğer efekt motorları

| Motor | Girdi → çıktı | Kapsam |
|---|---|---|
| Flip | İki veya daha çok görsel → açısal bekleme grupları | Sert değişim; geçiş bulanıklığı varsayılan değil |
| Sekans | Sıralı fotoğraflar → zaman dizisi | Doğal dosya sırası, elle sıralama, eksik/çift kare kontrolü |
| Video | Yerel video → seçilmiş zaman kareleri | Klip başlangıç/bitiş, gerçek zaman damgası, sahne kesimi, ortak tuval |
| Zoom/pan | Bir görsel → anahtar kareli dönüşüm | Merkez/başlangıç/bitiş/eğri; örtülmeyen kenarları görünür kontrol |
| Morph | A/B + eşleşmeler → şekil dönüşüm dizisi | Üçgen/mesh warp; katlanan üçgen ve sınır denetimi |
| Katman | Alfa katmanları + zaman eğrileri → birleştirilmiş kareler | Nesneye özel hareket; kaynak görünür renklerin korunması |
| Hybrid | Derinlik sahnesi + katman animasyonu → tek optik yol | Ayrı ileri aşama; aşağıdaki fiziksel sınıra bağlı |

Video için [FFmpeg](https://ffmpeg.org/ffmpeg.html) yerel alt süreç adaptörü kullanılır. Değişken FPS, zaman damgası, dönüş metadatası ve HDR/SDR farkı çözümlenir; yalnız kare numarasını FPS'ye bölmek yeterli değildir. Sahne kesimleri arasında otomatik ara kare yapılmaz. İlk sürüm desteklenen SDR dosyalarını açıkça sınırlar; HDR sessizce SDR diye okunmaz. Dağıtılan FFmpeg derlemesinin [lisans koşulları](https://ffmpeg.org/legal.html) ayrıca kaydedilir.

## 7. 3D ve animasyonun birlikte çalışması

Silindirik lenticular yüzey bir ana açısal değişken taşır. Genel bir baskıda zaman ve stereo bakış açısı bağımsız iki kontrol ekseni gibi vaat edilmez.

- Saf 3D: t sabit, kamera açısı değişir.
- Saf animasyon: kamera sabit, t değişir.
- Hybrid: kanal j için hem camera(j) hem time(j) açık olarak belirlenir; tek yol örneklenir. Her Nt×Nr birleşimini gereksiz üretme.

Dikey lentiküller normal kullanımda yatay stereo farkı sağlayabilir. Yatay lentiküller yukarı/aşağı animasyon için uygundur; mevcut Y kamera hareketinin çalışması tek başına normal yatay göz ayrımıyla stereoskopik derinlik garantisi değildir. Dikey animasyonda iki göz farklı zaman karelerini görebilir; hybrid tasarım buna göre fiziksel değerlendirilir. Yön örnekleri [3DZ üretici kılavuzunda](https://www.lenticularsoftware.de/onlinetools/Interlacer/anleitung.htm) da ayrılır.

Mevcut Y kamera özelliği kaldırılmaz. Yeni arayüz bu modun neyi temsil ettiğini doğru adlandırır. Stereo güvenilirliği kanıtlanmayan hybrid işleri deneysel durum taşır.

## 8. Lens ve baskı mühendisliği kuralları

### 8.1 Değişken ölçü ve çözünürlük

Lens nominal LPI'si, etkin kodlama LPI'si, dosya PPI'si ve yazıcı DPI'si ayrı alanlar olarak kalır. Lens partisi ve üretim koşuluyla kalibrasyon ilişkilendirilir. [Triaxes pitch açıklaması](https://triaxes.com/docs/Pitch-test-en/Description.html), yeni lens/yazıcı/malzeme birleşiminde test ve hedef bakış mesafesinde değerlendirme gereğini açıklar. [DP Lenticular baskı hazırlığı](https://dplenticular.com/technology/prepress-process/) optik ve mekanik pitch ayrımını ele alır.

Basit, eksenle hizalı raster hesabı:

~~~text
lens_adımı_mm = 25.4 / etkin_LPI
lens_başına_raster_örneği = PPI_dik / etkin_LPI
kanal_başına_raster_örneği = PPI_dik / (etkin_LPI × Ne)
Wpx = round((genişlik_mm + 2 × taşma_mm) × PPI_x / 25.4)
Hpx = round((yükseklik_mm + 2 × taşma_mm) × PPI_y / 25.4)
~~~

PPI_dik lenslere dik yöndeki raster örneklemesidir; dönüşlü/anizotropik durumda gerçek örnekleme haritası değerlendirilir. Bu oranlar üretim kapasitesinin ön kontrolüdür. Damla yayılması, RIP örneklemesi, kanal sızıntısı, lens açısı ve bakış mesafesi nedeniyle 'PPI/LPI kadar kusursuz kare' sonucu çıkarılmaz.

Yazıcıdaki 1200 DPI etiketi 1200 PPI giriş kabul edildiğini veya 20 net kare basılacağını kanıtlamaz. Kullanıcının mevcut DPI değeri hiçbir nedenle sessizce değiştirilmez.

### 8.2 İnterlacing sözleşmesi

Mevcut periyodik desen korunur. X/Y PPI genişletmesinde hesabın ortak temeli fiziksel koordinat olur:

~~~text
p = final sayfa piksel merkezinin kanonik lens düzlemindeki konumu (inç)
n = lens çizgilerine dik birim vektör
q = frac(etkin_LPI × dot(n, p - origin) + phase)
channel = min(floor(q × Ne), Ne - 1)
~~~

Kanonik görünüm, lensin önünden bakılan sayfadır; X sağa, Y aşağıdır. Lens dikey ise n=(1,0), yatay ise n=(0,1). Eğimin işareti eski desenle regresyon testiyle eşleştirilir. Bleed, fiziksel sayfa konumu, panel başlangıcı ve aynalama aynı dönüşüm zincirine dahildir. Görsel, alfa, beyaz maskesi ve hizalama aynı zinciri kullanır. Aynalama ile kare sırasını ters çevirmek iki farklı seçimdir.

Kesirli lens adımı her lens için tamsayıya yuvarlanmaz; faz birikimi korunur. Tile koordinatı global koordinata eklenir. Tile/panel sınırında desen yeniden sıfırlanmaz. RGB baskı pikselleri, ekranın RGB altpikselleri gibi bölünmez.

Kaynak görseller interlacing öncesinde hedef tuvale örneklenir. Kodlanmış TIFF daha sonra döndürülüp ölçeklenerek lens aralığı bozulmaz; gerekli baskı dönüşümü kodlama planında hesaplanır. RIP'e %100 fiziksel ölçü ve yeniden örneklememe notu aktarılır. Genişlik/yükseklik yuvarlama farkı raporda gerçek mm olarak yazılır.

### 8.3 UV, renk ve beyaz

Mevcut ICC hattı ilk sürümde korunur. Yeni efektlerde lineer ışıkta bileştirme ile çıktı profiline dönüşümün sırası açık olur. Uygulama/RIP arasında renk dönüşümünü kimin yaptığı profile yazılır; çift dönüşümden kaçınılır.

Grondo'nun tam modeli, RIP'i, pass modu, UV kürleme ayarı ve CMYK/White basım sırası henüz bilinmiyor. Bunlar makine profiline girilebilir alanlar olur; üreticiye özgü sıra uydurulmaz. Lensin arkasına doğrudan baskı ve lamine baskı ayrı proses profilleridir.

Şimdiki tam alan beyaz maskesi korunur. İleri aşamadaki nesne maskesinde beyaz, son kompozisyonun görünür kapsamasından türetilir; renk gibi aynı kanal geometrisinden geçirilir. Choke/spread mm ile tanımlanır. Aynalama ve ölçü maskeyle birebir eşleşir. Ayrı gri TIFF dosyasının otomatik olarak spot White olduğu söylenmez; RIP'te kanal ataması gerekir.

### 8.4 Kalibrasyon ve ghosting

Kalibrasyonun üç kaydı ayrılır: geometrik pitch/faz/eğim, Ne'ye bağlı kanal yanıtı, renk/beyaz/proses koşulları. Tek checkbox bütününün doğrulanması anlamına gelmez.

Makine/RIP modu, yön, PPI/DPI, lens partisi, malzeme, boyut kapsamı veya ilgili proses değişirse etkilenen kayıt stale olur. Ne değişimi kanal yanıtını geçersiz kılar; aynı geometri pitch ölçümünü otomatik silmek zorunda değildir. Faz değişimi hizalama kanıtını etkiler. Sunucu bu bağımlılıkları kontrol eder; yalnız arayüz uyarısına dayanılmaz.

Var olan lineer matris telafisi korunur. Yeni ölçüm içe aktarımı karanlık/beyaz referansını, pozlamayı, açı sırasını ve Ne boyutunu kaydeder. Uzamsal olarak değişen veya renk kanallarına göre farklı sızıntı, tek ortak matrisin sınırıdır. Koşul sayısı kötü, ölçüm eksik veya telafi renkleri taşırıyorsa üretim profili doğrulanmış sayılmaz. Kalibrasyonsuz simülasyonun iyileşmesi gerçek ghosting'in azaldığını kanıtlamaz.

## 9. Takılabilir görüntü motorları

| Motor | Eklenme nedeni | Uygulama kararı |
|---|---|---|
| Mevcut DA3 + detail_depth | Derinlik ve mevcut ayrıntı akışı | Korunur; alternatif motor bunu silmez |
| [RIFE](https://github.com/hzwer/ECCV2022-RIFE) | İki fotoğraftan hareket ara kareleri | Çekirdek yeni gereksinimin ilk AI adayı; önce küçük uygunluk/kalite çalışması |
| OpenCV flow / kontrol noktalı morph | Daha hafif hareket ve yönlendirilebilir dönüşüm | Ortak Interpolator arayüzünün ayrı sağlayıcıları |
| [SAM 2](https://github.com/facebookresearch/sam2) | Noktayla nesne seçimi ve videoda maske takibi | İsteğe bağlı; segmentasyon saç/duvak matting'i diye sunulmaz |
| [ViTMatte](https://github.com/hustvl/ViTMatte) | Trimap ile ince alfa sınırları | SAM maskesi veya elle trimap sonrası ayrı sağlayıcı |
| [LaMa](https://github.com/advimman/lama) | Açılan arka plan bölgeleri için daha gelişmiş tamamlama | Telea alternatifi; ortak sahnede bir kere üret, her görünüşte farklı içerik üretme |
| [MoGe](https://github.com/microsoft/MoGe) | Alternatif geometri/derinlik karşılaştırması | Deneysel adaptör; mevcut normalize yakınlık sözleşmesine açık dönüşüm |

SAM 2 üreticisi checkpoint ve temel kod için Apache-2.0 koşullarını açıkça belirtiyor. Diğer adaylarda kullanılacak kesin ağırlık/sürümün koşulları adaptör işinde kaydedilir; depo lisansı ile bütün ağırlıkların lisansı özdeş varsayılmaz. Bu belgede hiçbir yeni model indirilmiş, kurulmuş veya test edilmiş değildir.

Motorlar ihtiyaç anında yüklenir. CUDA/Torch/sürüm çatışması halinde ayrı yerel ortam ve alt süreç kullanılır; mevcut DA3 ortamı bozulmaz. Dosya tabanlı istek/sonuç sözleşmesi, kaynak hash'i ve hata kodu bulunur. Donanım ölçümü yapılmadan çalışma süresi sözü verilmez.

## 10. Önizleme, arayüz ve kalite durumu

Mevcut sayfaya '3D / İki fotoğraftan hareket / Flip / Sekans / Video / Zoom / Morph' modu eklenir. İlk teslimde yalnız tamamlanan modlar gösterilir. Çalışmayan butonlar tamamlanmış özellik gibi konulmaz.

İki fotoğraflı akış: A/B yükle → ortak kadraj → hareket/morph seç → ara kare sayısı ve ileri/geri → önizleme → mevcut lens/baskı ayarları → fiziksel prova.

Ekranda üç görünüm ayrı adlandırılır:

- Zaman önizlemesi: üretilen Nt kare ve oynatma hızı.
- Kanal önizlemesi: gerçekte Ne'ye seçilen kareler ve tekrarlar; bakış kaydırıcısı.
- Lens simülasyonu: belirtilen veya ölçülen kanal yanıtı; model adı ve ölçülmüş/tahmini etiketi.

İlk sürümde açı→kanal geçişi normalize bakış konumuyla gösterilir. Derece cinsinden optik açı doğrulanmadıysa kesin dereceye göre gerçek lens davranışı iddia edilmez. İş ayarı değiştiğinde eski önizleme stale olur.

Kalite durumları: draft, digitally_verified, pitch_confirmed, physical_sample_approved. Sonuncusu dosya hash'i + profil sürümü + numune/operatör kaydıyla ilişkilidir. Hatalı yapısal veri export'u durdurur. Düşük kaynak ayrıntısı, zayıf eşleşme ve optik belirsizlik uyarıları gizlenmez. Kalibrasyon taslağı üretmek mümkündür; üretim onayı gibi etiketlenmez.

## 11. İş yönetimi, performans ve saklama

Tek işçi kuyruğu korunur. Her aşama prepare/run/validate/commit mantığındadır. Geçici dosyalar yalnız iş klasörüne yazılır; manifest en son atomik tamamlanır. İptalde alt süreç ve bekleyen görev durur; kısmi çıktı tamamlandı sayılmaz.

FrameProvider kareleri/bölgeleri gerektiğinde diskten alır. Yeni sekanslarda tüm Nt×baskı çözünürlüğü RAM'e yüklenmez. LRU önbellek ve RAM bütçesine göre tile yüksekliği kullanılır. Mevcut legacy yolun performansı gereksiz refactor edilmez. Tam görüntü ve tile işleme aynı örnekleme koordinatlarını paylaşır; filtre halo'su tile sınırında kırpılmaz.

Önbellek anahtarı: kaynak hash'leri + ortak kadraj + sıralama + efekt parametreleri + motor/model revizyonu + renk sözleşmesi. Derinlik, ara kare, ChannelPlan ve baskı anahtarları ayrıdır. Yalnız DPI/LPI/faz değişmesi fotoğraftan ara kareleri yeniden üretmez; hedef çözünürlük değişip mevcut detay yetersizse yeniden üretim gerekebilir. Önizleme FPS değişimi baskı rasterini yeniden üretmez. Yazıcı DPI'si piksel hesabına doğrudan girmese bile kalibrasyon/proses kaydını etkiler.

Çıktı boyutu, bellek ve boş disk ön kontrolde hesaplanır. TIFF/BigTIFF seçimi RIP uyumluluğuna bağlıdır; dosyanın yazılabilmesi RIP'in okuyabildiği anlamına gelmez. Anizotropik PPI, 16-bit ve çok panel ayrı yetenek bayraklarıdır. Mevcut 500 MP sınırı ölçüm yapılmadan yükseltilmez.

Yeni sekans ve video alımında streaming/ölçülü dosya aktarımı kullanılır. Mevcut 512 MB bütün gövde okuma yoluna büyük video zorla sokulmaz. Yerel dosya izin sınırları, oturum/Origin/Host kontrolleri ve localhost sınırı korunur. ZIP desteği eklenirse yol taşması, dosya sayısı ve açılmış boyut sınırları uygulanır; v1 için ZIP zorunlu değildir.

## 12. Üretim kabulü

Sayısal kontroller ve gerçek örnekler görev planında ayrıntılıdır. Kabulün özü:

1. Eski fotoğraf→3D→baskı hattında davranış değişmemesi.
2. İki fotoğraftan gerçek ara hareket; uç fotoğrafların korunması; tekrar/dissolve'ın hareket diye geçmemesi.
3. Kaynak ve kodlanmış kanal sırasının doğru olması; ayna/yön/fazın aynı referansta işlemesi.
4. Kullanıcının değişken DPI/PPI/LPI/ölçü seçimlerinin korunması.
5. Kaynak, eski işler, profil ve model ortamının korunması.
6. Hedef Grondo/RIP/lens birleşiminde pitch, yön, kanal ayırımı, beyaz ve gerçek animasyon numunesi.

Makine modeli/RIP ve lens ürünleri bilinmediği için fiziksel kabul halen açıktır. Bu eksikler dijital mimariyi hazırlamayı engellemez; kalibrasyon profiline gerçek değerler girilmeden baskı uygunluğu tamamlandı denemez.

Bu mimarinin uygulama sırası ve dosya sınırları LENTICULAR_GOREV_PLANI.md içinde; uygulayıcı modele verilecek başlangıç metni UYGULAYICI_MODELE_DEVIR.md içindedir.

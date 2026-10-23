# Lenticular Studio — uygulama görevleri ve kabul koşulları

8 Ekim 2026. Yalnız plan. Hiçbir aşağıdaki görev bu belgelerin hazırlanması sırasında uygulanmadı.

Ana kararlar LENTICULAR_ANA_MIMARI.md içindedir. Mevcut uygulama kökü:

    C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1

## 1. Başlangıç kanıtı ve kapsam sınırı

Kaynaklar bu turda okundu; çalışan sunucu, kullanıcı projeleri, model ortamı ve uygulama kodu değiştirilmedi. Şu SHA-256 değerleri yalnız incelenen sürümü tanımlar:

| Dosya | SHA-256 |
|---|---|
| lenticular/pipeline.py | 8BA2030C7F8017558211FA77CDE45676A7FF213F316941700333A514FD18762E |
| lenticular/printing.py | 7A3D5AE8D7AAEAECB242FA007A822B15D8A2A868D516FE414B9371252BD60D37 |
| lenticular/studio.py | E90DEC75DA04EA20D4917DD004966238F03EFAA40A56E78087F2F20E7AAADF8D |
| lenticular/runner.py | 6A3D81BD7880B3E1545D31A31F32425E878E02F3089249CAAC1521E46F3D8D0B |
| lenticular/web/app.js | 589C9EB2488BBA5658A0BC0A16F76E8D78EA9C80479B826C93828E198835C24E |
| lenticular/detail_depth.py | FBFB11C299DE1EA3955482BDCB750C3DB28169B583FDB369FEB22B76EBF6C2E8 |

Başlangıçta fark bulunursa eski sürümü geri yükleme. Yalnız değişen ilgili bölümü oku ve görev sınırını güncel koda uyarla. docs/ARCHITECTURE.md bazı eski sürüm/sınır bilgileri taşıyor; gerçek doğrulayıcı kod önceliklidir.

sources/, mevcut outputs/, .models/ ve kullanıcı kaynakları korunur. Canlı .studio/state.json migrasyonuna geçmeden mevcut durumun hash kontrollü kopyası alınır; önce kopya üzerinde denenir. Geri dönüş güncel kullanıcı verilerini kaybettirmemelidir.

## 2. Aşama bağımlılıkları

~~~text
M0 mevcut durum ve küçük referans örneği
 └─ M1 FrameSet + eski render adaptörü
     └─ M2 sekans/flip + mevcut baskıya bağlantı
         └─ M3 iki fotoğraftan gerçek ara kare ve morph
             └─ M4 kanal önizlemesi + kalite/kalibrasyon bağı
                 └─ M5 odaklı regresyon + fiziksel numune paketi

M6 video ve anahtar kareli zoom/pan       : M3 sonrası
M7 nesne seçimi, matting, inpainting     : M3 sonrası, bağımsız motorlar
M8 X/Y PPI, seçici beyaz, büyük baskı    : M4 sonrası
M9 hybrid 3D + hareket                  : M7 ve fiziksel değerlendirme sonrası
~~~

M0–M5 ana ürün teslimidir. Bunun sonunda iki fotoğraf → yeni ara kareler → Ne kanal → lenticular baskı dosyası eksiksiz çalışmalıdır. M6–M9 tam ürün yol haritasıdır; çekirdek kabulü bekleten gereksiz bağımlılık yapılmaz. M3 içindeki basit yönlendirilmiş morph, farklı iki görüntü için temel yol olarak ana teslim kapsamındadır.

## M0 — doğru uygulama ve referans

Oku: AGENTS.md, pyproject.toml; yalnız pipeline.start/work/finish_print, printing.frame_mapping/encode, runner.preview ve ilgili arayüz bölümleri.

Yapılacak: çalışma ağacını/kaynak durumunu saptamak, mevcut DPI/PPI/LPI/ölçü davranışını kaydetmek, mevcut yerel ortamın ve Blender'ın durumunu öğrenmek. Git yoksa Git varmış gibi işlem yapma. Uygulama sürümünü veya bağımlılıkları sırf hazırlık için yükseltme.

Referans: küçük sentetik çoklu görünüş seti ile eski encode sonucu; bir mevcut render'ın salt okunur tekrar baskısı yalnız yeni çıktı dizinine. Büyük düğün işi veya AI depth bu aşamada yeniden üretilmez.

Kabul: ilgili dosya listesi, kullanılacak test girdisi, mevcut çıktı piksel/ICC/PPI referansı ve çalışma verisini koruma yöntemi kaydedilir. İşlev incelemesi ile gerçek test sonucu ayrı yazılır.

## M1 — FrameSet ve legacy adaptör

Önerilen yeni dosyalar: lenticular/contracts.py ve lenticular/frames.py. Sadece ihtiyaç duyulan veri tiplerini oluştur; boş motor sınıfları fabrikası kurma.

Değişiklik: printing.py içine encode_frames girişini ekle; eski encode imzasını koru. frame_mapping kamera yolunu legacy planner'a bağla. proof ve rapor üretimi de kamera bilgisi gerektirmeyen FrameSet'i kabul etsin. Yalnız encode'u ayırıp proof'ta Blender bağımlılığı bırakma.

Kabul:

- Eski renderer job.json dosyaları yeniden yazılmadan okunur.
- Legacy adaptör ile eski yolun küçük testte TIFF piksel sonuçları aynıdır; metadata'nın sıralaması/dosya hash'i yerine anlamlı alanlar karşılaştırılır.
- Nr/Ne açı seçimi, reverse_views, mevcut alfa/boş alan kontrolü korunur.
- Eksik kare, farklı boyut, NaN zaman/açı, geçersiz tür ve izinli kök dışına çıkan yol reddedilir.
- Bu aşamada depth/geometry/Blender davranışına müdahale edilmez.

## M2 — sekans ve flip

M2a: lenticular/media.py ile kaynak kare koleksiyonu ve ortak tuval; animation.py ile flip/time_sequence → ChannelPlan. pipeline.py'ye sequence asset ve sekans işi ekle.

M2b: studio.py ve web/ içindeki mevcut ekranı genişlet; yükleme, kare şeridi, doğal sıralama ve elle yeniden sıralama. Ayrı uygulama/servis veya yeni frontend çatısı kurma.

Yeni asset, mevcut tek fotoğraf asset'ini değiştirmeden kind alanıyla ayrılır. Eski kayıtların eksik kind alanı photo kabul edilir. state schema yükselirse migrasyon idempotent ve atomik olur; unknown gelecekteki sürüm sessizce düşürülmez.

Kabul:

- İki kaynakla Ne=8 eşit flip için plan [A,A,A,A,B,B,B,B]. Bu plan kare tekrarı olduğunu doğru raporlar.
- Üç eşit süreli kare/Ne=6 örneğinde plan [A,A,B,B,C,C]; gerçek görünür kanal görüntüleri test edilir.
- İstenen her zorunlu durum için en az bir kanal gerekliyse, durum sayısı Ne'den büyük olduğunda sessiz düşürme yoktur; preflight uyarısı veya açık azaltma seçimi vardır.
- Düz animasyon yolu depth veya Blender çağırmaz. Kamera ekseni kontrolü yalnız multiview_3d yolunda uygulanır.
- Düzenleme kaynak görüntülerin hash'lerini değiştirmez. Kareler ortak kadrajı paylaşır; otomatik ayrı kırpmayla titreme yaratılmaz.

## M3 — iki fotoğraftan gerçek ara kareler

Bu aşama zorunludur. Flip'in çalışması M3'ün bittiği anlamına gelmez.

M3a / sağlayıcı sözleşmesi: lenticular/interpolation.py. Girdi: A, B, t listesi, ortak tuval, kalite/maske parametreleri. Çıktı: FrameSet + üretim metadatası + yöntem açıklamalı kalite göstergeleri.

M3b / hareket: önce RIFE'nin sabit revizyon/checkpoint ile küçük yerel uygunluk çalışması. İzole ortam gereksinimi, CPU/GPU, gerçek ara zaman desteği, padding, kaynak hash'i ve çıktı tutarlılığı kaydedilir. Aynı sözleşmede iki yönlü OpenCV akış/warp sağlayıcısı hafif alternatif olur. İki sağlayıcıya da kullanıcıya belirtilmeden geçiş yapılmaz. RIFE kurulum sorunu varsa görevi tekrar/dissolve ile başarılı sayma.

M3c / morph: eşleşen kontrol noktaları, sınır köşeleri, ara mesh ve parça bazlı warp. Üçgen ters dönmesi/katlanması denetlenir; gerekiyorsa kullanıcı eşleşmeyi düzeltir. Hareket motoru ayrı, morph ayrı seçilebilir. Dissolve ayrı efekt olarak tanımlanır.

M3d / arayüz: A/B, ara kare sayısı, hareket/morph seçimi, ortak kadraj, sabit bölge, tek yön/ileri-geri, zaman ve kanal önizleme. İleri ayarlar başlangıç akışını kaplamaz.

M3 kabul örnekleri:

| Örnek | Zorunlu sonuç |
|---|---|
| Aynı A ve B | Bütün kareler aynı; sonradan titreşim/hareket eklenmez |
| 256×256 sentetik nesne A'dan B'ye 24 px gider | Yarı zamandaki ağırlık merkezi beklenen konumdan en fazla 1 px sapar; iki hayalet nesneyle dissolve bu testi geçemez |
| t=0 ve t=1 | Ortak normalizasyon sonrası A/B pikselleri aynıdır |
| Nt=3, 8, 17 gibi farklı sayılar | Gerçek ara kareler ve doğru sıra; yalnız 2'nin kuvvetleriyle sınırlı kalma |
| İleri/geri | Tam 2×Nt−2 örnek; uçlarda gereksiz çift bekleme yok |
| Saç/duvak veya örtüşen el | Belirsiz bölge görünür; kaynak görünmeyen ayrıntısı doğrulanmış diye sunulmaz |
| Logo/yazı sabit katmanı | Korunan bölge istemsiz morph edilmez |
| İlişkisiz iki fotoğraf | Düşük eşleşme açıklanır; morph/kontrol noktası yolu kullanılabilir |

Sentetik 1 px eşiği tasarım kabul hedefidir; doğal görüntüler için evrensel kalite garantisi değildir. Doğal fotoğraf çiftleri ayrıca tam boy görünümde değerlendirilir. Test verisinde kullanıcı fotoğrafları izinsiz dış servise gönderilmez.

## M4 — kanal planı, optik önizleme ve preflight

Önerilen yeni parça: lenticular/preflight.py. printing.py, pipeline.py ve ilgili arayüzde dar bağlantılar.

Zaman dizisi seçiminde gerçek time_s kullan; kamerada açı kullan. Eşit uzaklıkta seçim için deterministik tie-break tanımla. Flip ağırlıkları pozitif ve normalize olsun; kanal dağıtımı toplam Ne'yi korusun. Temsil edilemeyen kısa beklemeler raporlansın.

Zaman önizlemesi ile Ne'ye indirgenmiş önizleme ayrılır. Yalnız preview_fps değişince ChannelPlan/çıktı rasteri değişmez. Lens yönü değişikliği kamera gerekmeyen animasyonda gereksiz render başlatmaz.

Kapasite raporu raster örnek sayısını, temsil edilmeyen kanalı, kaynak ayrıntısını, tekrarları ve ölçülmüş kanal ayrımını ayrı gösterir. UI'deki eski suggestedViews formülü bu yeni raporla uyumlu açıklanır; DPI ve PPI otomatik eşitlenmez.

Kalibrasyon geçerliliği sunucuda kontrol edilir. Eski pitch_verified kayıtları geçmiş operatör beyanı olarak taşınır; yeni kapsamlı fiziksel onaya otomatik yükseltilmez. Ne değişince eski Ne×Ne yanıt matrisi reddedilir.

Kabul: eski kalibrasyonla farklı LPI/Ne/yön/proses üretim onaylı görünmez; draft dışa aktarım mümkündür. Report ve dosya hash'i aynı işe bağlanır. İptal veya hatadan kalan TIFF baskıya hazır listesine girmez.

## M5 — çekirdek teslim ve gerçek baskı paketi

Yalnız değişen davranışları kapsayan testleri çalıştır. Bir kez geçen testleri kod değişmedikçe tekrar tekrar çalıştırma. Aşağıdaki raster matrisi küçük sentetik dosyalardan oluşur; hepsi için Blender/AI yeniden çalıştırılmaz.

| Kontrol | Kabul |
|---|---|
| 2/3/8 etiketli renkli kanal | Kanal sırası doğrudan TIFF piksellerinden doğru |
| Dikey/yatay, ayna, reverse, faz | Her seçim ayrı etkili; çift aynalama yok |
| Kesirli LPI (örnek 60.13) | Büyük global koordinatta lens fazı birikimli ve tutarlı |
| Tile vs tek parça | Aynı çekirdek için bit düzeyinde aynı pikseller; tile dikişi yok |
| Değişken DPI/PPI/LPI/ölçü | Kullanıcının seçimi korunur; lens hesabı yanlışlıkla DPI üzerinden yapılmaz |
| Baskı mm / TIFF PPI | Yuvarlama hatası eksen başına en fazla yarım raster pikselin fiziksel karşılığı |
| ICC ve White | Doğru profil/ölçü; beyaz ile renk ayna ve konumu aynı |
| Eski fotoğraf/3D işi | Açılır, önizlenir ve mevcut ayarlarla yeniden baskı hazırlanır |
| İptal ve uygulama tekrar açma | Kısmi iş başarılı olmaz; önceki kaynak/çıktı korunur |
| Önbellek | FPS değişimi baskı üretmez; LPI değişimi ara kare modelini çalıştırmaz |
| Kaynak bütünlüğü | İşlem öncesi/sonrası kaynak hash'i aynı |

Teslim paketi: interlaced.tif, seçildiyse white-underbase.tif, mevcut pitch/registration dosyaları, channel-plan.json, frameset.json, zaman/kanal önizleme, print-report.json ve operatör notları. Önizleme dosyası baskı master'ı diye teslim edilmez.

Fiziksel kabul sırası: gerçek makine/RIP modunu kaydet → X/Y ölçek cetveli → hedef mesafede pitch → faz/eğim/sıra çizelgesi → 2 kanallı flip → birkaç farklı Ne ile aynı kısa animasyon → beyaz/renk kontrolü → gerçek iki fotoğraflı numune.

Her numunede dosya hash'i, lens partisi, ölçü, yön, DPI/PPI, RIP ölçeği ve gözlem kaydedilir. Evrensel ghosting eşiği uydurulmaz; kullanım mesafesi ve görünür geçiş kalitesi için numune kabulü yapılır. Fiziksel test yoksa 'dijital doğrulama tamamlandı, fiziksel numune bekliyor' denir.

## M6 — video ve hareket tasarımı

FFmpeg adaptörü, seçilen klip aralığı, doğal zaman damgaları, sahne kesimi, ortak kadraj. Yüklemeyi bellek sınırlı yap; medya paketindeki yürütülebilir komutları çalıştırma. Alt süreç shell komut birleştirmesiyle değil argüman listesiyle başlatılır.

Zoom/pan için aynı ortak koordinat sistemi ve anahtar kareler. Kaynak boyutunu aşan yakınlaşmada ayrıntı kaybı görünür. Kabul: VFR kısa klipte seçilen gerçek anların tutması, farklı yön metadatası, sahne kesiminden ara kare üretilmemesi, eksik FFmpeg'in anlaşılır hata vermesi.

## M7 — seçme, matting ve ortak arka plan

Her sağlayıcı ayrı eklenir: SAM 2 seçimi → ViTMatte/trimap alfa → isteğe bağlı LaMa; MoGe bağımsız alternatif geometri deneyi. Hepsini tek teslimde kurmak zorunlu değildir.

SAM maskesi otomatik saç matting'i sayılmaz. Katman alfa düzenlemeleri orijinalden ayrı tutulur. Inpainting ortak sahne dokusuna uygulanır; kamera başına yeniden tahmin edilmez. Videoda aynı nesne kimliği ve sınır sürekliliği korunur; bağımsız per-frame depth normalizasyonu yüzey zıplaması oluşturmamalıdır.

Kabul: kullanıcı görünür kaynak bölgesi korunur; gizli/tahmin edilen maske raporlanır; model sürümü/cache değişimi izlenir; başarısız yeni motor mevcut DA3/Telea yolunu bozmaz.

## M8 — ileri UV üretim

M8a: ppi_x/ppi_y; eski ppi her iki eksene eşlenir. Eski eşit eksen yolu aynı pikselleri üretmeli. Fiziksel koordinat formülü ana mimarideki gibidir; kalibrasyon ve registration dahil tüm tüketiciler aynı dönüşümü alır.

M8b: seçici White, mm cinsinden choke/spread ve sabit arka katman. Mevcut tam alan White davranışı korunur.

M8c: 16-bit ve çok panel; RIP desteği kanıtına göre açılır. Panel üretimi global faz/orijini korur, bindirme ve kesim payı ayrı tutulur. Ayrı lens parçalarında montaj kayıtları da gerekir; hesap tek başına fiziksel panel hizasını sağlamaz.

Kabul: anizotropik rasterde fiziksel oran bozulmaz; tile/panel birleşimleri tam görüntüyle eşleşir; TIFF/BigTIFF RIP denemesi yapılmadan uyum iddia edilmez. Kaynak 512 px iken yüksek PPI dosya üretmek yeni ayrıntı diye sunulmaz.

## M9 — kontrollü hybrid

Katman animasyonu ile camera(j), time(j) birlikte örneklenir. Ne kanallık açık tek yol saklanır. Nt×Nr bütün kombinasyonları varsayılan üretilmez. Normal silindirik lensle bağımsız zaman/stereo kontrolü vaat edilmez.

Kabul: zaman sabitlenince saf 3D, kamera sabitlenince saf animasyon; katman kimlikleri ve sabit referans korunur. İki gözde farklı zaman içeriğinin etkisi fiziksel numunede değerlendirilmeden üretim onayı verilmez.

## 3. Uygulayıcı modelin çalışma kuralı

- Her seferinde tek aşamanın ilgili dosyalarını oku; bütün repository ve büyük çıktıları tarama.
- Bir aşamayı tasarım değişikliği gerektirmeden bitirebiliyorsan rutin kararları kendin ver.
- Sözleşme, kaynak korunması, renk/optik anlam veya kabul hedefi değişmek zorundaysa nedeni ve somut seçenekleri mimari denetime taşı.
- Yeni kütüphaneleri yalnız ilgili motor aşamasında ekle; mevcut ortamı topluca yükseltme.
- Rutin küçük kontrolleri birleştir. Her testin doğruladığı kullanıcı davranışı belli olsun.
- Aşama sonunda kısa kayıt: amaç / tamamlanan / kritik karar / değişen dosya / geçen test / sınır / sonraki adım.
- Sonuçta yapılmayan fiziksel testleri, test edilmiş gibi anlatma. Başarısız ara kare motorunu tekrar karelerle gizleme.

Bu planın yazılması uygulama yetkisi veya başlatma değildir. Uygulamaya, kullanıcı bu devir görevini bir modele başlatmasını söylediğinde geçilir.

# VD — üç derinlik denemesi için uygulama talimatı

Bu dosyayı ve yanındaki `vd-three-variant-settings.json` dosyasını kullan. Amaç aynı fotoğrafı A normal, B artırılmış, C güçlü derinlik olarak, aynı 50,20 LPI lens altında karşılaştırmaktır. Yazılımı geliştirme veya başka projeleri değiştirme; mevcut motorları kullan. Bu bir uygulama reçetesidir; sonuç henüz üretilmedi.

## Kaynak ve kapsam
- Fotoğraf: C:\Users\USER\Downloads\vd-gigapixel-recover v2-2x-faceai v2.jpg
- Aktif uygulama: C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1
- Kaynak: 1872 × 3098 piksel. Tam kadraj korunacak. Yeniden AI görsel üretimi, yeni yüz, keskinleştirme, renk değişimi veya kırpma yapılmayacak.
- Kullanıcının 13 cm sınırı HER GÖRSEL için kabul edildi. Üçü yan yana yaklaşık 39 cm eder. Tüm sayfanın 13 cm olması istenirse bu plan uygulanmadan ölçü yeniden hesaplanmalı.
- JSON bir aktarım planıdır; uygulamanın doğrudan içe aktarma dosyası değildir. `variants[i].render` ve `variants[i].print` uygulamanın gerçek ayar sözlükleridir. Üst düzey açıklama alanlarını uygulamaya gönderme.

## Görsel değerlendirmesi ve beklenen hacim
- Görüntünün solundaki öne uzatılan el ve başparmak ana ön plan etkisidir. Parmak, avuç ve önkol hacimleri korunmalı; el tek renkli düz bir plaka yapılmamalı.
- Burun ucunun merkezi sabit referanstır: yaklaşık kaynak piksel (958,432), normalize x=PRIVATE_PHONE_0001, y=0.1394898289. Bu noktayı fotoğrafta kontrol et; bütün varyantlarda aynı noktayı kullan. `zero_reference=0.5` yalnız yedek başlangıçtır; program `reference_point` üzerinden gerçek sıfır derinliğini örnekler. Burun derinliğini elle 0.5'e boyama.
- Burun, göz çukurları, yanaklar, alın, saç ve sakal arasında kesintisiz yüz hacmi olmalı. Sakaldaki koyuluğu çukur, beyaz saçları yüksek kabartı sayma.
- Göğüs, karın ve kollar birbiriyle hacimsel bağını korumalı. Koyu tişörtteki gölgeler otomatik geometrik çukur yapılmamalı.
- Görüntünün sağındaki diz üstü el, diz/şort yüzeyinin önünde yer almalı. Bacaklar, ayakkabılar ve aşağıya yaklaşan zemin perspektif sürekliliğini korumalı; tüm alt yarıyı tek uzak düzlem yapma.
- Taş duvar geride kalmalı; taşlar arasında sınırlı gerçekçi yüzey farklılığı korunmalı. Sağdaki dal/yapraklar duvardan ayrışabilir fakat elin önüne taşınmamalı.
- Başparmak çevresi, el-gövde örtüşmesi, saç/omuz kenarları, yaprak araları ve bacakların arasındaki görünen arka plan kontrol edilecek. Otomatik analyzer bu bölgelerin anatomik doğruluğunu garanti etmez.

## Ortak ayarlar ve varyantlar
Bütün gerçek alanlar JSON'da eksiksiz verilmiştir. Önemli ortak değerler: Nr=10, Ne=10; kamera x; dikey lens; ayrıntılı AI derinlik açık, güç 0.8; parlaklıktan yüzey kabartısı 0; normalizasyon preserve; derinlik siyah/beyaz/gamma 0/1/1; yumuşatma 0.15; kenar düzeltme 0.5; depth çözünürlüğü 1008; dengeli ön/arka bütçe; paralaks ve kenar korumaları açık; gelişmiş arka plan onarımı; 4 katman; doldurma yarıçapı 5. Nesne bölgeleri/fırça başlangıçta boş. Haritayı görmeden keyfi ofset/poligon veya düz yüzey ekleme.

- A Normal: toplam kamera açısı 3°, ön paralaks %1, arka %1.5.
- B Artırılmış: toplam kamera açısı 4.5°, ön paralaks %1.5, arka %2.2.
- C Güçlü: toplam kamera açısı 6°, ön paralaks %2, arka %3.
- Üçünde azami paralaks sınırı %3. `balanced` eğrisinde hedefi ön/arka paralaks alanları belirler; etki ve ön/arka güç alanları 1'de kalır. Sırf gücü artırarak ikinci bir kontrol uygulama.
- Bu yüzdeler sağ ve sol uç görüş arasındaki yatay hareketin görsel enine oranıdır; fiziksel çıkıntının cm değeri değildir. Açılar lens görüş açısı değildir. Verilenler hedef bütçeleridir; derinlik aralığı ve korumalar gerçekleşen değeri azaltabilir.

## Baskı ayarları
- Her panel 6141 × 10163 piksel, 1200 PPI; 129.9845 × 215.116833 mm. 13 cm üst sınırını yuvarlama ile aşmamak için en 6141 pikseldir.
- Yazıcı DPI=1200, dosya PPI=1200 deneme adayı; bu ikisini eşit girmek fiziksel RIP doğrulaması değildir. Kaynağın bu ölçekte ayrıntı çözünürlüğü yaklaşık 366 PPI'dir; 1200 PPI interlace rasteri yeni fotoğraf ayrıntısı üretmez.
- nominal_lpi=effective_lpi=50.20, lens dikey, tilt=0, taşma=0, fit=contain, stripe_sampling=center, Ne=10. Hesaplanan kanal başına raster piksel 2.3904; optik kanal kapasitesi ölçülmüş değildir.
- Tekil bağımsız panelde phase=0. Görüş sırası ters çevirme kapalı. Program kendi kamera/kanal eşlemesini yapar; elle bir kez daha ters çevirme.
- RGB, uygulamanın profilli RGB çıktısı; ICC dosyası verilmediği için CMYK dönüşümü uydurma. Crosstalk=0, compensation=0, matris yok, regularization=0.02, gamut_guard açık.
- mirror=false ve white_underbase=false önden yönlendirilmiş deneme içindir. Bunları arka yüz UV baskı reçetesi diye sunma. Gerçek üretim ters baskı/beyaz katman gerektiriyorsa uygulama biçimi doğrulanmadan baskıya hazır onayı verme.
- pitch_verified=false, raster_ppi_verified=false, lens_angle_verified=false. Kullanıcının 50.20 değeri kullanılacak; ölçüm yapıldı bilgisi verilmedi. 30° lens açısı ve 500 mm izleme mesafesi yalnız yazılımın geçici varsayımlarıdır; ölçülmüş sayma, derinliği cm olarak raporlama.
- Pitch ince taraması: 50.195–50.205, 0.001 adım, 11 aday. Bu dar test aralığı ölçülmemiş geniş pitch hatasını taramaz; uygun çizgi aralık dışındaysa merkez/aralık fiziksel sonuçla değişmelidir. Var olan aynı RIP/lens kalibrasyonu geçerliyse gereksiz pitch testi basma.
- allow_unfilled=false. Doldurulmamış hatalı çıktıyı başarılı diye vermek için açma.

## Tek seferlik ve ekonomik uygulama sırası
1. JSON ayarlarıyla mevcut kaynak/derinlik önbelleğini eşleştir. Kaynak, model, çözünürlük ve normalizasyon aynıysa önbelleği kullan; eski elle düzleştirilmiş/başka reçeteden derinliği sessizce devralma. Bir temel ve bir ayrıntı haritasını üç varyantta paylaş. AI tahminini üç kez çalıştırma.
2. Önce A/B/C analyzer raporlarını üret; Blender renderi başlatmadan aynı haritada karşılaştır. Üretim geometrisi için render_long_edge=0 kalsın. Sonra tek bir C önizlemesini render_long_edge=1024 ve grid_size=512 ile al; bunun amacı en zor varyantta kenar ve boşluk sorununu erken görmek. Tam renderde grid_size=1024 ve render_long_edge=0 kullan. Fotoğrafı 4096 gibi daha büyük boyuta yükseltme.
3. Burun sabitliği, anatomik derinlik sıralaması, kenar onarımı ve boşluklar uygunsa üç nihai renderi üret. Aynı iş parametreleriyle tekrar render başlatma. Bir sorun varsa aynı ayarlarla tekrar deneme; durup sorunlu bölge görüntüsü, ilgili ayarlar ve kısa hata/analiz raporu sun. Ucuz model rastgele parametre araması yapmasın.
4. Her varyant için requested/effective_angle, gerçekleşen ön/arka endpoint hareketi, iç hacim ve selected-channel sampling sonuçlarını kaydet. Koruma nedeniyle üç çıktı aynıya yakınsa bunları üç farklı güç sonucu diye etiketleme. Analyzer önerilerini körlemesine uygulayıp karşılaştırmayı bozma; özellikle Nr/Ne değiştirmek ortak baskı koşullarını değiştirir.
5. Tam görüntünün ilk/orta/son görüşlerini kontrol et. Burun hareketi yaklaşık bir render pikselini aşıyorsa, el duvarın arkasına geçiyorsa, saç/ellerde yinelenen kontur veya açık boşluk varsa final başarılı değildir. Arka plan/yüz düzlüğünü yalnız genel açıyı yükselterek düzeltme. Analyzer'daki bir-lens-adımı uyarısı fiziksel başarısızlığın kesin kanıtı değildir ama görmezden gelinerek baskı doğrulandı denemez.
6. A/B/C'yi soldan sağa aynı ölçekte tek baskı sayfasına yerleştir. Üç bağımsız interlaced paneli faz=0 ile yan yana yapıştırma: tek lens altında global şerit başlangıcı tutarlı olmalıdır.
   En dar mevcut-motor yolu: aynı renderleri kullanarak panel TIFF'lerini sırayla phase=0, 0.8985, 0.7970 ile encode et; bu değerler x başlangıcı 0, 6141, 12282 piksel ve lens 50.20/1200 için hesaplandı. Sonra piksel değiştirmeden, boşluksuz yatay birleştir. Bu fazlar yalnız mevcut dikey lens, tilt=0, mirror=false, bleed=0 düzeni için geçerlidir. Genel formül `(global_phase + x_offset_px * effective_lpi / ppi) % 1`.
   Birleşik resim alanı 18423 × 10163 piksel, yaklaşık 389.9535 × 215.1168 mm. Etiketleri resmin üstüne basma; altta sabit 6 mm şerit ekleyebilirsin. Etiketler A Normal / B Artırılmış / C Güçlü olsun. Renk profili ve 1200 PPI korunmalı. Baskıda %100, otomatik sığdırma/yeniden örnekleme kapalı. Tüm sayfayı 13 cm'e küçültme.
   Paneller ayrı lens parçalarıyla kullanılacaksa bağımsız phase=0 dosyaları ayrıca gereklidir. Tek lens sayfası için ayarlanmış B/C fazlarını bağımsız panel dosyası diye sunma.
7. Teslim: ortak karşılaştırma TIFF'i, düşük boyutlu karşılaştırma önizlemesi, A/B/C analyzer ve quality raporları, kullanılan JSON ve kısa baskı notu. Fiziksel baskı yapılmadıysa sonucu “baskı denemesi / kalibrasyon taslağı” olarak belirt.

## İşlem sınırı
Gereksiz tam test paketi, kod refactoru, yeni model indirme, internet/API kullanımı veya eski projeleri tarama yapma. Gerçek ayar girişleri ve çıktı kontrolleri yeterli. JSON değerleri mevcut render/print doğrulayıcılarıyla kabul edildi; bu yalnız şema/aralık doğrulamasıdır, üç görüntünün üretildiği veya baskıda iyi olduğu anlamına gelmez.

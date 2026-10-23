# Görüntü bozulmalarının ortak değerlendirmesi — 10 Ekim 2026

Önceki `native-portrait-final` görüntüsündeki parmak çıkıntıları dijital üretim hatasıydı. Fiziksel baskı beklenerek açıklanabilecek bir sorun değildi. Önceki TIFF onaylı sonuç sayılmamalıdır.

**Son kabul durumu: dijital görsel kabul geçmedi.** Parmak kenarı ve merkez fotoğrafın korunması belirgin iyileşti. Şortun dar kıvrımında iki uç bakışta kalan şekil bozulması nedeniyle bu adaydan yeni baskı TIFF'i üretilmedi. Bu sonuç kusursuz veya baskıya hazır olarak teslim edilmez. Bölge, fotoğraf koordinatlarında yaklaşık x=240–490, y=1550–1810'dur.

## Bulgular ve birlikte uygulanan düzeltmeler

| Bulgu | Düzeltme | Kabul kontrolü |
|---|---|---|
| Alan yüzdelikleri, eli gömlekle ve başka keskin sınırları aynı yüzeyde bırakıyordu | Alan yüzdeliklerinin kaçırdığı keskin derinlik geçişleri de ayrılır; toplam en fazla sekiz yüzey kullanılır | Aynı kamera açıklığında iki uç bakış, parmak ve kumaş sınırları |
| Doldurma alanı ve ön nesnenin alfa sınırı uyuşmuyordu | Arka plan temizliği ile ön planın kapladığı alan aynı destek bölgesini kullanır. Ön renk ve alfa, gerçekten gösterilen alt yüzeye göre doğrusal ışıkta birlikte hesaplanır | Kaynak kamerada fotoğrafın yeniden birleşmesi; görünür detayın silinmesi ve ikinci çizgi için regresyon testleri |
| Komşu katmanların kapalı derinlik aralıkları aynı düzlemde buluşuyordu | Çok küçük aralıkla kesin derinlik sırası uygulanır; çakışan yüzeylerin kararsız görünmesi önlenir | Kaydedilen mesh aralıklarının birbirine değmemesi ve aynı kumaş bölgesinin merkez/yan bakışları |
| Dış görüntü kenarı tekrar edilerek uzatılıyordu | Bir kez tamamlanan ortak kenar dokusu ve doğru UV koordinatları | Tam sahnenin iki dış kenarı; kaynak kamera hizalama testi |
| Güvenilir iç bölge çıkarılırken ince bağımsız parçalar silinebiliyordu | Her bağlı parça kendi derinlik örneğini korur | İnce ve kalın iki bağımsız nesne testi |

Kaynak fotoğraf, kamera aralığı, sıfır düzlemi ve görüntü çözünürlüğü değiştirilmedi. Ayrım ve renk birleştirme birlikte değerlendirilir: fazla yüzey eklemek tek başına yeterli değildir; yalnız ön bandı ayırmak da kumaştaki diğer derinlik kopukluklarını bırakır. Klasik yöntem korunur. Gelişmiş yöntemin önbellek sürümü yükseltildi; eski görünüşler yeni hesap yerine kullanılmaz.

## Denetim ve kanıt

- Son kodla genel test takımındaki 50 test geçti. Buna rağmen görsel kabul ayrıca incelendi ve kalan kumaş kusuru kaydedildi.
- Gerçek kontrol görüntüsü 1872 × 3098 pikseldir. İki uç ve merkez bakışta el, kumaş, saç, bitki ve görüntü sınırları incelenir; yalnız küçük el kırpması kabul ölçütü değildir.
- Aynı girdiye ait önceki LaMa tahminleri, maske ve boyut eşitlikleri doğrulanarak yeniden kullanıldı. Her açı için yeni doku üretilmez.
- `outputs/contour-correction-20261010/final-checks.json` kaynak kameradaki renk farklarını ve değişen dosya özetlerini kaydeder. Bu ölçüm tek başına yan bakış geometrisinin doğru olduğunu kanıtlamaz.
- `strict-order-verification.json` yüzey sırasını sayısal olarak doğrular. Önceki adayda bir katmanda 71.813 tepe noktası üst sınıra, komşusunda 1.734 tepe noktası aynı alt sınıra oturuyordu. Renk/maske hesabının doğruluğu, bu geometrik çakışmayı tek başına gideremezdi.
- Son `coupled` klasöründe iki uç görünüş ve merkez vardır. `visual-acceptance.json` baskı kabulünün verilmediğini kaydeder. Önceki `validation.json` ve `scene/print` ara adaya aittir; sonucun baskı onayı değildir.
- `son-karsilastirma.png`, `thumb-before-after.png`, `regional-review.png` ve `scene-before-after.jpg` görsel inceleme belgeleridir.

Önceki adaylar kanıt olarak korunur. `rejected-global-slices`, `rejected-minimum-coverage`, `scene` ve `ownership` teslim sonucu değildir. Kaynaklar ve kayıtlı işler silinmez.

Son kontrolde Studio servisi kapalıydı; otomatik yeniden açılmadı. Kod değişiklikleri sonraki açılışta yüklenir. Kayıtlı veri bütünlüğü `state-verification.json` içinde ayrıca kontrol edilir.

Kaynak kamerada, herhangi bir renk kanalında 32/255 değerinden fazla fark bulunan piksel oranı bütün fotoğrafta %0,352'den %0,030'a; incelenen kumaş bölgesinde %1,215'ten %0,042'ye indi. Bu ölçüm merkezdeki renk kaybını gösterir; yan bakış şekil bozukluğunun giderildiği anlamına gelmez.

## Kalan engelin değerlendirmesi

Dar kumaş kıvrımında fotoğrafın gerçek nesne sınırı ile derinlikten türetilen katman sınırı uyuşmuyor. Bu bir baskı sorunu değildir. Yeni yumuşatma, yeni doldurma modeli veya daha fazla katman tek başına doğru nesne geometrisini sağlamaz. Sonraki gerekli düzeltme, bu bölgede doğrulanmış nesne maskesi ile ona bağlı tutarlı derinliğin birlikte hazırlanmasıdır. Mevcut bölgesel konum/hacim aracı, güvenilir nesne segmentasyonu yerine geçmez. Bu eksik kapanmadan otomatik üretimin bütün fotoğraflarda kusursuz olduğu söylenemez.

## Açık sınırlar

Bu yöntem tam anlamsal nesne ayrımı veya ölçülmüş üç boyutlu geometri değildir. Ek ayrım bütün sahnedeki her yanlış derinlik sınırını otomatik düzelttiği anlamına gelmez. Yanlış kaynak derinliği, belirsiz maske ve görünmeyen yüzeyler hâlâ görsel değerlendirme gerektirir. Arka plan ve dış çerçeve tahmindir. Kumaş gibi aynı nesnenin sürekli yüzeylerinde ayrı renk/derinlik kestirimleri biçim hatası üretebilir. Kaynak renk tutarlılığı kontrolü tamamen opak kaynak piksellerine uygulanır; yarı saydam kaynaklarda aynı garanti verilmez.

Lens, gerçek pitch, RIP ölçeklemesi, hayalet görüntü ve fiziksel netlik bu dijital denetimle onaylanmış olmaz. Yazılım testleri veya bir TIFF'in başarıyla yazılması “her görüntüde kusursuz” sonucu kanıtlamaz.

## Teknik dayanak

Gerçek derinlik kopukluklarını ayrı temsil etme ilkesi için [Shih ve arkadaşları, CVPR 2020](https://openaccess.thecvf.com/content_CVPR_2020/html/Shih_3D_Photography_Using_Context-Aware_Layered_Depth_Inpainting_CVPR_2020_paper.html); trimap ve ön renk kestirimi için [PyMatting](https://pymatting.github.io/foreground.html). Buradaki yakın bant ayrımı yerel bir sezgiseldir; makaledeki bütün öğrenilmiş sistemin uygulandığı iddia edilmez. Renk tutarlılığı `I = αF + (1−α)B` birleşiminden hesaplanır.

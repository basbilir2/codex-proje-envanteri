# Lenticular Studio — Kolay Kullanım Kılavuzu

**Referans seçimini, 3D ayarlarını ve fırçayı uygulayarak öğrenmek için:** [3D etkisini ayarlamayı öğren](3D_ETKI_OGRENME_KILAVUZU.md).

**Kısa yol:** Fotoğraf seç → Hızlı önizleme → 3D etkisini kontrol et → Lens/baskı ayarlarını gir → Baskı dosyasını al.

## 1. Programı aç ve fotoğrafı seç

1. Proje klasöründeki **Lenticular Studio.cmd** dosyasına çift tıkla.
2. Açılan sayfada **＋ Fotoğraf seç** düğmesine bas.
3. Fotoğrafını seç. Ortada görüntülendiğinde yükleme tamamdır.

Blender’ı elle kullanman gerekmez; program onu arka planda çalıştırır. Hazır depth haritan yoksa **Hazır derinlik haritası kullan** bölümünü atla.

## 2. İlk 3D önizlemeyi oluştur

**Hızlı önizleme** düğmesine bas. Program derinliği hesaplar ve Blender ile **2 uç görünüşü, 512 piksel çalışma boyutunda** hazırlar.

**Tamamlandı** yazısını bekle. **3D önizleme → ▶ Oynat** ile hareketi izle. Kaydırma çubuğuyla özellikle en sağ ve en sol görüntüyü kontrol et.

Derinlik modeli zaten bilgisayarda kurulu. Her fotoğrafta yeniden indirilmez; yeni fotoğrafın derinliği hesaplanır.

İstediğin sayıda kare için **Görünüşleri oluştur** kullan. Nr alanına 2–256 arasında tam sayı yazabilirsin; 12'nin katı olması gerekmez.

## 3. Etkiyi ayarla

İlk kullanımda yalnız şu üç ayarla çalışman yeterli:

| Ayar | Ne işe yarar? |
|---|---|
| **3D etki gücü** | Öndeki ve arkadaki bölgelerin derinlik farkını artırır veya azaltır. |
| **Toplam kamera açısı** | Sağ ve sol görünüşlerin birbirinden ne kadar farklı olacağını belirler. |
| **Sabit kalacak derinlik** | Hareket sırasında hangi derinliğin yerinde kalacağını belirler. |

Ana kişiyi sabitlemek için derinlik hesaplandıktan sonra **Fotoğraf** sekmesine geç. **Araç → Sabit nokta seç** seçeneğini açıp kişinin üzerinde bir noktaya tıkla.

Etkiyi küçük adımlarla değiştir. Her değişiklikten sonra **Hızlı önizleme** düğmesine yeniden bas; eski görüntü kendiliğinden yenilenmez.

**Kenar bozulmasında açıyı otomatik daralt**, **Aşırı paralaksta açıyı otomatik sınırla** ve **Kenar boşluklarını katmanlı arka planla doldur** seçeneklerini başlangıçta açık tut. Koruma devreye girerse program seçtiğinden daha küçük açı uygulayabilir; uygulanan açı sonuçta yazılır.

## 4. Baskı ayarlarını gir

Sağdaki **Lens ve çıktı** bölümünü kullan:

| Alan | Ne gireceksin? |
|---|---|
| **Baskı eni / boyu** | İstediğin baskı ölçüsü, milimetre olarak. Örneğin 10 × 15 cm için 100 × 150. |
| **Dosya çözünürlüğü (PPI)** | Baskı dosyasının çözünürlüğü; baskıcının istediği değer. |
| **Yazıcı noktası (DPI)** | Yazıcı/RIP için kullanılan değer. PPI ile aynı şey değildir. |
| **Lens etiketi (LPI)** | Kullanacağın lenticular lensin etiketindeki değer. |
| **Etkin / ölçülmüş LPI** | Aynı lens ve yazıcıyla yapılan pitch testinde belirlenen değer. |
| **Baskı kanalı (Ne)** | Lens altına dilimlenecek kanal sayısı. Başlangıçta **PPI / LPI için kanal sayısı öner** düğmesini kullan. |

**Nr**, Blender’ın ürettiği fotoğraf sayısıdır. **Ne**, baskıya kodlanan kanal sayısıdır. Aynı olmak zorunda değiller. Şimdilik **Nr = 12** ile çalış; görünüş sayısını artırmak tek başına etkiyi güçlendirmez.

Sağ/sol 3D için lens yönü **Dikey · sağ/sol 3D** olmalı. **Alanı doldur** fotoğrafı kırpabilir; tüm fotoğrafı korumak istiyorsan **Tamamını koru** seç.

## 5. Lens ölçüsünü doğrula ve dosyayı al

1. **Pitch testi ve hizalama üret** düğmesine bas.
2. **Çalışmalar ve dosyalar** bölümündeki **Pitch testi** dosyasını, üretimde kullanacağın lens ve yazıcı koşullarında **%100 ölçekte** bastır. “Sayfaya sığdır” kullanma.
3. Testi lensle kontrol ederek uygun değeri belirle; **Etkin / ölçülmüş LPI** alanına gir. Emin değilsen baskıcınla birlikte belirle.
4. Yalnız fiziksel testi yaptıysan **Etkin LPI’yi aynı lens ve yazıcıyla test ederek doğruladım** kutusunu işaretle.
5. **Çalışmalar ve dosyalar** listesinden tamamlanan 3D çalışmanı seç. **Seçili render’dan baskı hazırla** düğmesine bas.
6. Tamamlanınca **Lenticular TIFF** dosyasını al. **Baskı teslim notları** ve **Baskı raporu** dosyalarını da baskıcıya ver.

Yalnız baskı ayarlarını değiştirdiysen Blender görünüşlerini yeniden üretmen gerekmez. Açı veya derinlik etkisini değiştirdiysen önce **Görünüşleri oluştur** düğmesini kullan.

**Fotoğraftan baskıya hazırla**, derinlikten baskı dosyasına kadar bütün akışı çalıştırır. İlk denemede önce önizlemeyi kontrol etmek daha kolaydır.

## 6. Şimdilik hangi ayarları bırakabilirsin?

- **Ghosting azaltma:** İlk denemede karışım ve telafi gücünü 0 bırak. Fiziksel baskıda çift görüntü varsa önce lens hizasını ve pitch değerini kontrol et; sonra telafiyi küçük adımlarla dene.
- **CMYK / ICC, aynalama ve UV beyaz maske:** Baskıcının üretim yöntemine göre ayarla. CMYK için yazıcı ICC profili gerekir. Beyaz maske ayrı dosyadır.
- **Lens fazı, eğimi, mesh ve doldurma ayrıntıları:** Başlangıçta mevcut değerleri koru.

İyi bir ayar bulduğunda **Lens / çalışma profili** alanına bir ad yazıp **Kaydet** düğmesine bas.

## Bir sorun görürsen

| Sorun | Yapılacak işlem |
|---|---|
| Fotoğraf yüklenmiyor / bağlantı hatası | **Lenticular Studio.cmd** dosyasından yeniden aç ve açılan güncel sayfayı kullan. |
| Kol, saç veya nesne kenarı uzuyor | Önce kamera açısını, gerekirse 3D etki gücünü azalt; önizlemeyi yeniden oluştur. |
| Ayarı değiştirdim ama görüntü aynı | **Hızlı önizleme** veya **Görünüşleri oluştur** düğmesine bas. |
| Eski çalışmaya dönmek istiyorum | Listeden çalışmayı seç; **Seçili çalışmanın ayarlarını kullan** düğmesine bas. |
| “Kalibrasyon taslağı” yazıyor | Lens/yazıcı pitch doğrulaması henüz onaylanmamış. Dosya üretilebilir; fiziksel baskı kontrolü gereklidir. |

**Son kontrol:** Ekrandaki 3D önizleme hareketi gösterir. Gerçek lenticular sonuç için küçük bir fiziksel baskıyı lensle kontrol et. Tek fotoğrafta görünmeyen bölgeler tahmin edilir; saç ve tül gibi ayrıntılarda iz kalabilir.

AI ince kıvrımları çıkaramıyorsa **Yüzey kabartısı · tahmini** ile düşük güçte ek kabartı verebilirsin. 0 kapalıdır; pozitif değer aydınlığı öne, gölgeyi arkaya taşır. Bu sanatsal bir tahmindir; desen ve gölgeyi yanlış kabartabileceği için haritada kontrol et.

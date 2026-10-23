# Lenticular uygulama kapsamı

## Hedef

Tek fotoğraftan yerel depth, Blender 2.5D sahne ve çoklu görünüş;
ardından kullanılan lens ve yazıcıya göre kalibre edilmiş lenticular baskı dosyası.
`sources/` salt okunur kalır. Güncel motorlar ve sınırlar `ARCHITECTURE.md` içinde açıklanır.

## Hazır olan altyapı

- Hazır depth veya yerel DA3MONO-LARGE ile Blender sahnesi.
- Nr render sayısı, yatay kamera açıklığı/konumları, near/far ve zero-parallax ayarı.
- 48 render görünüşü desteklenir; kontroller Studio ayar ekranından kullanılabilir.
- Nr ve Ne bağımsızdır; interlacing, ICC TIFF ve kalibrasyon dosyaları çalışır.
- Hareketli önizleme ve kaydırıcı; kaynak fotoğraf korunur.

## Uygulanan kullanıcı kontrolleri

- Görünüş sayısı: 12, 24, 36, 48 ve özel değer.
- Bakış açığı: yatay kamera aralığı; derinlik etkisiyle birlikte önizlenir.
- 3D etki gücü: derinlik aralığı/sıkıştırması; fotoğraftaki nesne sırası korunur.
- Zero-parallax: sabit kalacak derinliği veya fotoğraf üzerinde referans noktayı seçme.
- Önizleme oynatma hızı, karşılaştırma, ayarları kaydetme ve yükleme.
- Mevcut depth tekrar kullanılabilir; yalnız kamera/render ayarını değiştirmek AI modelini tekrar indirmez.

## Görüntü kalitesi

- Varsayılan çalışma 12 görünüş / 512 px; 48 görünüş desteği korunur.
- Yumuşak derinlik eğrisi, ayrı ön/arka etki ve renk/depth ortak kenar filtresi.
- Global paralaks bütçesi ve yerel kenar korumasıyla uygulanan kamera açısı raporu.
- Keskin derinlik sınırlarında bağımsız yüzey parçaları; Blender'da 8 örnek kenar yumuşatma.
- İşaretli paralaks haritası ve gerçek render boşluk/kırpılma bilgileri.
- Kişi, saç, duvak ve ince nesne sınırlarının önizlemesi ve manuel derinlik fırçası.
- Açılan arka plan bölgeleri için ortak sahnede renk/depth katmanları ve OpenCV Telea inpainting.
- Güçlü efekti artırırken açılan boşlukları ve aşırı yatay farkları göstermek.
- Göreli AI depth'i fiziksel ölçüm gibi sunmamak; gerekirse bölge derinliği düzeltmesi.

## Uygulanan Blender sonrası baskı aşaması

- Baskı boyutu, raster PPI, yazıcı/RIP çözünürlüğü ve ölçekleme kontrolü.
- Nominal lens LPI ve pitch testiyle bulunan etkin LPI; lens yönü ve bakış mesafesi.
- Ne baskı kanalı seçimi; Nr görünüşlerini seçilen Ne kanalına ayrı örnekleme.
- İnterlacing/dilimleme, görünüş sırası, yatay faz/kaydırma ve hizalama ayarları.
- Kalibrasyon/test baskıları, kenar payları, ayna/yön ayarı ve UV baskı iş akışına uygun çıktı.
- Renk profili ve RIP sürecine göre çıktı seçenekleri.

## Ghosting azaltma

Renk taşmasında piksel başına telafi azaltma, telafisiz/telafili model karşılaştırması,
lineer ışıkta alan örnekleme ve kanal payı dengesizliği uyarısı uygulanır. Lens veya
raster ayarı değişince arayüz eski pitch onayını kaldırır. Baskı teslim notları üretilir.

Lens/yazıcı kalibrasyonu, doğru kanal seçimi, uygun derinlik ve açı,
hizalama ve ölçülmüş lens karışımına dayalı telafi kontrolleri bulunur.
Telafi uygulanmadan önce gerçek test baskısı gerekir; yazılım bütün lenslerde sıfır ghosting garanti etmez.
48 render görünüşü, baskıda mutlaka 48 bağımsız kanal kullanılacağı anlamına gelmez.

## Kalite kabulü

Son kabul yalnız ekrandaki animasyona göre yapılmaz. Kullanılacak lens, yazıcı ve
malzemeyle pitch testi ve gerçek baskı kontrolü yapılır. Kaynak fotoğrafın çözünürlüğü
hedef baskı boyutuna uygun olmalıdır; 540×540 deneme görüntüsü büyük baskı ayrıntısını temsil etmez.

Kalibrasyon referansı: https://dplenticular.com/technology/prepress-process/

## Daha ileri motorlar

Otomatik SAM/matting, ikinci geometri modeli, üretken inpainting ve otomatik fiziksel
ölçüm analizi ileride eklenebilir. Mevcut doldurma tahmini, görünmeyen gerçek içerik değildir.

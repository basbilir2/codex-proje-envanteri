# Geliştirme mimarisi

## Akış

`fotoğraf → standart sRGB / yön → depth → düzenlenmiş yakınlık → Blender katmanları → Nr görünüş → Ne kanal → lens telafisi → interlaced TIFF / kalibrasyon`

`sources/` yalnız okunur. Çalışma kaynakları `.studio/`, model ağırlıkları `.models/`,
sonuçlar `outputs/studio/` altında tutulur. Başarısız/iptal edilmiş işin çıktısı tamamlanmış gibi sunulmaz.

## Modüller

| Modül | Sorumluluk / genişletme noktası |
|---|---|
| `depth.py` | Sabit DA3MONO-LARGE checkpoint; SHA-256 kontrollü yerel önbellek; pozitif göreli Z'den beyaz-yakın float32 0–1. Yeni model aynı çıktı sözleşmesini sağlamalı; disparity ve depth semantiği açıkça kaydedilmeli. |
| `repair.py` | Yumuşatma, normalize koordinatlı derinlik fırçası, referans etrafında etki gücü; tek sahnede tutarlı gizli renk/depth katmanları. Yeni inpainting motoru yalnız gizli katman dokularını değiştirmeli. |
| `geometry.py` | Perspektif ışınları üzerinde yüzey, depth sınırında üçgen kesme; X/Y kamera ve off-axis hesabı. |
| `layers.py` | Derinlik katmanlarını ayrı alfa maskeleriyle çizer; dar sınırda renk hizalama, katman içinden geometri uzatma ve gizli renk doldurma. |
| `runner.py` / `blender_scene.py` | Gerçek Blender render; kamera projeksiyonu kontrolü; dokuları paketlenmiş .blend; kaynak önizleme. |
| `printing.py` | Angular view seçimi, farklı Nr/Ne, lineer ışıkta crosstalk telafisi, periyodik lens deseni, ICC, TIFF strip yazımı, beyaz maske ve kalibrasyon. |
| `pipeline.py` | Sürüm numaralı JSON durum, fotoğraf/profil kaydı, atomik dosya yazımı, tek işçi kuyruğu, iptal ve geçerli depth/render tekrar kullanımı. |
| `studio.py` / `web/` | Loopback HTTP servisi ve Türkçe ayar ekranı. Fotoğraf, hazır depth, ICC ve matris yükleme; dış servis kullanılmaz. |

## Temel sözleşmeler

- Fotoğraf/depth aynı boyut ve yönde olmalı; temel render girdisi float32 NPY veya 8/16-bit gri depth olabilir.
- DA3MONO doğrudan göreli Z üretir. Normalizasyon metadata ile kaydedilir; metre diye yorumlanmaz.
- Nr görünüş sayısıdır. Ne raster kanalıdır. Baskı aşaması görünüşleri kamera açısına göre seçer; view'ları ortalayarak parallax silmez.
- Dikey lentiküllerde kamera X, yatay lentiküllerde kamera Y hareket eder; uyuşmayan yönle baskı kodlama reddedilir.
- PPI görüntü rasteridir, yazıcı DPI ayrı üretim bilgisidir. `PPI / etkin LPI` lens başına raster örneklerini verir.
- Faz lens periyodunun kesri, eğim derece, çıktı ölçüleri milimetredir. Aynalama bütün kodlanmış görüntüye uygulanır.
- Her fiziksel ICC dönüşümü gömülü profil ve hash ile kayıtlıdır. CMYK profil gerektirir; beyaz alt baskı ayrı maskedir.
- Karışım matrisinin satırı gözlenen açıdır, sütunu basılan kanaldır. Negatif değer kabul edilmez, satırlar normalize edilir.
- Telafi: `argmin ||C X - V||² + λ ||X - V||²`, ardından ayarlanabilir güç ve gamut kırpması. Tek ortak RGB matrisi yaklaşımıdır.
- TIFF strip yazılır; tüm yüksek çözünürlüklü Ne kareleri bellekte büyütülmez. 400 megapiksel / kenar 100000 piksel çıktı sınırı vardır.

## Kalite durumu

Kalibrasyon yapılmamış TIFF üretilebilir ve `calibration_draft` olarak raporlanır.
`pitch_verified` operatörün fiziksel test beyanıdır; yazılım donanımı ölçtüğünü iddia etmez.
Kanal yanıt dosyaları ölçüme yardım eder; varsayımsal karışım gerçek lens profili diye sunulmaz.
Önizleme, çıkarım yapılan arka plan ve ideal optik değerlendirme içerir. Algoritma görünmeyen
gerçek yüzeyleri veya bütün yazıcı/lens birleşimlerinde kusursuz sonucu garanti edemez.

## Gerekli çalışma kontrolleri

- Gerçek 48 görünüşlü düğün işi: Blender, katmanlar, 600 PPI TIFF, Ne=10, UV beyaz maskesi ve lens simülasyonu tamamlandı.
- Renkli üç kanal kontrolü: gerçek TIFF piksel sırası, PPI/ICC etiketleri, beyaz maske ve sabit rengin telafide korunması.
- Y kamera / yatay lens kontrolü: gerçek Blender projeksiyonu ve aynalanmış baskı kodlama.
- Ek geniş repository taraması veya kapsamlı test paketi bu çalışma için kullanılmadı.

## Sonraki motor geliştirmeleri

### Görünüş motoru sürüm 5

Yeni Studio çalışmaları 12 görünüş / 512 px ile başlar. Nr=48 seçeneği korunur.
Render önbelleği sürüm 5 ile ayrılır; eski sahneler değiştirilmez.
Blender 8 kamera örneğiyle kenar yumuşatma yapar; fotoğraf ayrıntısına denoise uygulanmaz.
Derinlik sırası monoton korunur: referansa uzaklık d, kullanılabilir aralık r ve
bölgesel kazanç g için yumuşak eğri `d*g/(1+max(g-1,0)*abs(d)/r)` kullanılır.
g=0 düzlem, g=1 özdeşliktir; referans sabittir. Eski doğrusal kırpma seçilebilir.
3×3 ortak renk/derinlik filtresi, fırçadan önce uygulanır. Mesh hücrelerinde daha
küçük derinlik farkı taşıyan köşegen seçilir. Studio, büyük derinlik sıçraması taşıyan
üçgenleri silmek yerine medyan derinliğinde bağımsız yüzey parçalarına ayırır. Kaynak
kamerada UV alanı kapanır; sınır boyunca uzak yüzeyleri birleştiren köprü kurulmaz.
Temel CLI eski cut davranışını korur; edge_mode=split ile yeni yöntem seçilebilir.

Kamera bütçesi `f*span*(1/zero-1/z)` uç farkından hesaplanır. X hareketinde genişliğe,
Y hareketinde yüksekliğe bölünür. Seçilen sınır aşılırsa kamera aralığı ölçeklenir;
Nr, geometri sırası ve zero-parallax korunur. Kenar koruması ayrıca komşu piksel
uç-kamera farklarının %99.5 yüzdeliğini 512 piksel referans boyutta 1.5 piksel
bütçeyle sınırlar. Bu pratik eşik görüntüye bağlıdır; matting veya kusursuz kenar garantisi değildir. `quality.json` hem istenen hem uygulanan
açıyı, kırpılmayı ve gerçek render alfa boşluklarını kaydeder. `prepared/parallax.png`
bu analitik farkın işaretli görselidir; optik ölçüm veya hata maskesi değildir.

Ghosting çözümünden sonra gamut koruması, bütün kanallar/RGB için ortak piksel başına
ölçekle telafiyi [0,1] sınırına getirir. Kırpma ve azaltılan alan ayrı raporlanır.
Lens simülasyonunda aynı koruma kullanılır; önce/sonra lineer MSE yalnız seçili
karışım modeline göredir, raster/lens hizalaması, ICC veya yazıcının etkisini ölçmez.
Alan örneklemesinde renkler lineer ışıkta birleştirilir. Kamera/lens eksen uyumsuzluğu
render kuyruğundan önce reddedilir; baskı işi seçili render'ın gerçek ayarlarını taşır.

### Görünüş motoru sürüm 8 ve yükleme bağlantısı

Onarım açıkken tek yüzeyi derinlik uçurumlarından geçirmek yerine ayrı alfa
katmanları kullanılır. GrabCut yalnız iki piksellik sınır bandını düzenler;
geometri katman içindeki güvenilir derinliklerden uzatılır. Uzak katmandaki
ön plan izi, çevresindeki iki piksellik bant dahil Telea ile doldurulur.
Bu işlem saç/tül matting değildir; gizli renkler tahmindir. Eski çıktılar korunur.

Yerel oturum anahtarı aynı proje için sunucu yeniden başlatıldığında korunur.
Dosya gövdesi gönderilmeden bağlantı doğrulanır; kopuk bağlantı ve eski oturum
Türkçe bildirilir. Aynı orijinal dosyanın SHA-256 eşleşmesi mevcut fotoğrafı
yeniden kullanır. Host/Origin ve oturum doğrulaması etkin kalır.

### İleride eklenebilecek motorlar

MoGe ile geometri karşılaştırması, SAM/matting, lisansı sabitlenmiş LaMa/üretken
arka plan tamamlama, lens yanıt görüntülerinden otomatik profil çıkarma ve fiziksel
baskı ölçümüne göre optimizasyon bu arabirimlerden eklenebilir. Bu motorlar mevcut
sürümde kurulmuş veya çalıştırılmış gibi gösterilmez.

Kalibrasyon kaynakları:

- https://triaxes.com/docs/Pitch-test-en/Description.html
- https://triaxes.com/faq/photo-products/
- https://dplenticular.com/technology/prepress-process/

# 100 LPI — yeni yüz, gövde ve arka plan denemesi

Baskı dosyası: `print/interlaced.tif`. Hareketli önizleme: `hareketli-onizleme.gif`.

- Nominal lens: **100 LPI**; kullanıcı gerçek pitch ölçümü olmadığını belirtti.
- Tam görsel: **129,9845 × 215,1168 mm** (yaklaşık **13 × 21,51 cm**).
- Dosya: **6141 × 10163 px**, **1200 PPI**, RGB, yerleşik sRGB ICC profili.
- Yazıcının bildirilen değeri: **1200 DPI**. Bu bilgi fiziksel kanal ayrışmasının ölçümü değildir.
- **6 ayrı kamera görüntüsü / 6 baskı kanalı**, kanal başına **2 raster piksel**.
- Sanal kamera aralığı: **4°**; gerçek lens bakış açısı bu değer değildir ve ölçülmemiştir.
- Dikey lens çizgileri; faz **0**; aynalama ve beyaz katman **kapalı**. Önceki baskı yönü korunmuştur.

## Ne değişti?

Elin aşırı çıkışı azaltıldı; el ve parmaklar tek, bütün bir yüzey olarak işlendi. Yüzde alın, yanaklar, göz çevresi, çene ve küçük burun çıkıntısı; gövdede kavis ve mevcut derinlik haritasından sınırlı kıyafet rölyefi; duvar ve zeminde farklı geri derinlik kullanıldı. Burun artık sabitlenmiyor: referans düzlemi kullanıcının izniyle gerisine alındı. Fotoğrafın tamamı işlendi; orijinal kaynak fotoğraf değişmedi.

Eski yöntemde arka plan değişmeden bırakılmış, bazı parmak düzenlemeleri yanlış görüntü koordinatlarına uygulanmıştı. Yeni önizlemede bulunan başka bir sorun da düzeltildi: elin arkasında tamamlanan kıyafet yüzeyi elin önüne geçebiliyordu. Arka yüzeylerin derinlik sırası artık açıkça korunuyor.

## Kontrol edilenler

Altı tam kare ve yüz, parmak, kıyafet, arka plan ayrıntıları incelendi. Altı ayrı karede parmak üzerinde kıyafet rengi ve saydam boşluk kalmadı. Uç kareler arası nokta takibi: burun yaklaşık −3,90 px, sol yanak +5,64 px, başparmak −8,88 px, gövde merkezi −3,94 px, sol duvar +34,76 px. Bunlar görüntüde ölçülen hareketlerdir; fiziksel derinlik ölçüsü değildir. TIFF ölçüsü, ICC profili ve 30.705 örnek raster pikseli doğrulandı. Saydamlık giderimi yalnız zemindeki 7–11 tekil, kısmen saydam pikselin alfasını düzeltti; RGB renklerini değiştirmedi.

## Baskı ve değerlendirme

**%100 gerçek ölçekte basın; sayfaya sığdırma ve yeniden boyutlandırma kapalı olsun.** Hareketli önizlemeyi baskıya göndermeyin. Dosya sRGB içerir; RIP'te gerçek yazıcı/mürekkep/malzeme profilini kullanın.

Bu, fiziksel olarak henüz doğrulanmamış bir denemedir. Gerçek LPI, lens açısı ve RIP kanal ayrımı ölçülmedi. Özellikle duvarın kanallar arasındaki hareketi bir lens aralığını aşabildiğinden baskıda geçiş/netlik riski kalır; bu yüzden arka planı tekrar düzleştirip kullanıcı isteğini kaybetmeden yeni baskıyla değerlendirilmelidir. Tek fotoğraftan yüz ve kıyafet hacmi tahmin edilmiştir; gerçek 3D tarama değildir. Yeni baskıda yüz iç hacmi, parmak biçimi, kıyafet hacmi ve arka planın geride kalışı ayrı ayrı değerlendirilmelidir.

Ayrıntılı kanıtlar: `quality-checks.json`, `analysis/scene-analysis.json`, `print/print-report.json` ve `knowledge/runs/vd-100lpi-codex-20261012.json`.

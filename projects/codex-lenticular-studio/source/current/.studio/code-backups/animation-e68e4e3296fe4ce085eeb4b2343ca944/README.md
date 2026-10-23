# Lenticular Studio

Fotoğraf ve depth map ile Blender'da 2.5D yüzey kurar;
yatay paralel kameralar ve off-axis lens shift ile görünüş PNG'leri üretir.
Depth hazır dosyadan okunabilir veya yerel DA3MONO-LARGE modeliyle oluşturulabilir.
Yerel ayar ekranı, katmanlı arka plan tahmini, lens simülasyonu, kalibrasyon ve
lenticular TIFF hazırlığı aynı uygulamada bulunur. Blender sahne/render motorudur.

## Uygulamayı aç

**`Lenticular Studio.cmd` dosyasına çift tıklayın.**
Ekran bilgisayarda, yerel tarayıcıda açılır. Yeni kurulumda önce `setup.ps1`,
ardından AI depth için `setup-depth.ps1` çalıştırın. Bu makinede kurulum hazırdır.
Yüklü Blender otomatik bulunur. Model ağırlıkları tekrar indirilmez.

1. Fotoğrafı seçin veya hazır düğün örneğini kullanın.
2. Açı, etki, sabit derinlik ve Nr görünüş sayısını ayarlayın. Başlangıç 12 görünüş / 512 pikseldir; 48 seçeneği korunur.
3. Gerektiğinde derinlik fırçasıyla nesne uzaklığını düzeltin. Orijinal renkler korunur.
4. Görünüşleri oluşturun; kenarları hareketli önizlemede değerlendirin.
5. Lens LPI, **etkin LPI**, fiziksel ölçü, raster PPI ve **ayrı Ne** değerini ayarlayın.
6. Pitch testini ve hizalamayı aynı yazıcı/RIP/lens/malzeme ile %100 ölçekte basın.
7. Renk profili, aynalama, yön, faz, eğim, taşma ve UV beyaz maskesini seçin.
8. “Seçili render'dan baskı hazırla” veya “Fotoğraftan baskıya hazırla” kullanın.

Görünüşler, kaynaklar ve çalışmalar korunur. Profiller kaydedilir; ayar JSON dosyaları
dışa aktarılıp yüklenebilir. Çalışan iş durdurulabilir. Yeniden açmada yarıda kalan işler
ayrı gösterilir. Aynı ayarlı yeni çalışmalarda geçerli depth ve render tekrar kullanılabilir.
Kapatma düğmesi yerel servisi de durdurur. Komut alternatifi: `.\run.ps1 studio`.

### 3D etkisini artırırken

- Yumuşak derinlik eğrisi, etki arttığında yakın/uzak uçları kırparak düzleştirmek yerine sıkıştırır. Ön ve arka bölgenin gücü ayrı ayarlanabilir.
- “Ön / arka derinliği dengele” mevcut haritanın %5–95 aralığını ortalar. Ana kişiyi baskı düzleminde tutmak için fotoğraftaki “Sabit nokta” aracını kullanın.
- Fotoğraf kenarlarına uyum, renk ve derinlik sınırlarını birlikte kullanan yerel filtre uygular. Saç/duvak için otomatik matting değildir; fırçayla düzeltme gerekebilir.
- Paralaks sınırı, uç kameradaki en büyük farkı hareket yönündeki görüntü boyutunun seçilen yüzdesinde tutmak için açıyı azaltır. İstenen ve uygulanan açı raporda ayrıdır. Bu geometrik sınır fiziksel konfor/ghosting garantisi değildir.
- Kenar koruması, ince sınırlar çok yer değiştiriyorsa açıyı ayrıca daraltır. Keskin derinlik sınırları kaynak görüntüde delik açmadan bağımsız yüzey parçaları olarak oluşturulur.
- “Paralaks” sekmesi öne çıkan bölgeleri mercan, arkayı mavi gösterir. Kalite satırları boş alanı, kırpılmayı ve görünüşler arası adımı gösterir.
- Ayarları değiştirince önceki önizleme yeni ayarmış gibi gösterilmez; yeniden görünüş üretme uyarısı çıkar.

### Baskı dosyaları

`outputs/studio/<çalışma>/print/`:

- `interlaced.tif`: piksel yeniden ölçeklemesi gerektirmeyen, fiziksel PPI ve ICC içeren RGB/CMYK lenticular raster.
- `white-underbase.tif`: seçilirse UV RIP'e White olarak atanacak ayrı gri maske.
- `pitch-test.tif`: etkin LPI çevresinde ayarlanabilir adımlı kalibrasyon bantları.
- `registration.svg`: aynı fiziksel boyut, LPI, faz, eğim ve ayna yönünde hizalama işaretleri.
- `lens-response-test.tif`: her kanalın ayrı ışık yanıtını ölçmek için kalibrasyon çizelgesi.
- `lens-response-template.json`: gerçek ölçümle doldurulacak Ne×Ne matris şablonu.
- `lens-proof.png`, `proof/`: belirtilen kanal karışımının hareketli simülasyonu.
- `print-report.json`: Nr/Ne eşleme, gerçek ölçüler, dosya hash'i, kanal kapsaması, renk kırpılması ve uyarılar.
- `ghosting-comparison.png`: aynı görünüşte hedef / telafisiz / telafili lens modeli karşılaştırması.
- `baski-notlari.txt`: operatöre verilecek ölçü, yön, renk, beyaz kanal ve kalibrasyon notları.

CMYK için uygun yazıcı/mürekkep/malzeme ICC profili zorunludur. Profil seçilmezse
gömülü sRGB kullanılır. Bayer/RGB altpiksel dizilimi varsayılmaz; dosya normal RIP rasteridir.
RIP'te %100 ölçek kullanın. Beyaz dosyası gömülü spot renk değildir; ayrıca White kanalı olarak atanır.

Ghosting telafisi lineer ışıkta, kararlılaştırılmış matris çözümüyle uygulanır.
Ölçüm yoksa komşu kanal modeli kullanılır ve bu durum raporda belirtilir. Ölçüm
şablonu doğrudan gerçek profil diye kabul edilmez. Lens simülasyonu donanım testi değildir.
Kanal başına raster örnekleri, görünüş tekrarları ve telafi renk kırpılması raporlanır.
Renk koruması açıkken telafinin taşan kısmı aynı görüntü noktasındaki bütün kanal ve
renklerde birlikte azaltılır; kaybolan telafi miktarı görünürdür. Bu yüzden koyu/açık
kenarlarda kalan ghosting fiziksel lens iyileştirmesi gerektirebilir. Alan kapsama
örneklemesi lineer ışıkta hesaplanır. %20'yi aşan kanal payı dengesizliği raporlanır.

**Kalite sınırı:** tek fotoğrafın görünmeyen bölgeleri tahmin edilir; burada arka plan
katmanları OpenCV Telea ile doldurulur. Yüksek açılarda tahmin hataları görülebilir.
Fiziksel pitch ve kanal sızıntısı ölçülmeden üretim kalitesi doğrulanmış sayılmaz.
Doğrulanmamış çıktılar raporda kalibrasyon taslağı olarak işaretlenir.

Motor arabirimleri ve geliştirme noktaları: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Tek fotoğraftan başlatma

Bu makinede yerel AI depth ortamı kuruludur. Yeni kurulumda önce `setup.ps1`,
ardından `setup-depth.ps1` çalıştırın. AI ortamı Python 3.10–3.13 ve Git gerektirir;
bu kurulumda Python 3.12 / CPU PyTorch kullanılır.

```powershell
.\setup-depth.ps1
.\run.ps1 from-photo --photo "C:\Gorseller\foto.png" --config examples/photo.json --output outputs/foto-2
```

Model ilk kullanımda `.models/` içine indirilir (yaklaşık 1.3 GB ağırlık).
İndirme boyutu ve resmi SHA-256 değeri kontrol edilir; geçerli önbellekte indirme yapılmaz.
Fotoğraf dış servise gönderilmez. Sonraki çalıştırmalarda aynı ağırlıklar yeniden kullanılır.
`--model-cache` ile önbellek yeri, `--process-res` ile model işleme çözünürlüğü değiştirilebilir
(varsayılan 504, 140–1008). Render kaynak fotoğrafın çözünürlüğünde alınır.
GPU olmayan bu makinede model CPU'da float32 çalışır.

Yalnız depth üretmek için:

```powershell
.\run.ps1 depth --photo "C:\Gorseller\foto.png" --output outputs/yalniz-depth
```

`from-photo` çıktısı:

- `depth/original.*`: kaynak dosyanın hash ile kontrol edilmiş kopyası.
- `depth/photo.png`: aynı boyutta Blender dokusu.
- `depth/raw_model_depth.npy`: model çözünürlüğündeki doğrudan göreli Z.
- `depth/relative_depth.npy`: tam fotoğraf boyutuna hizalanmış göreli Z.
- `depth/depth_proximity.npy`, `depth/depth.png`: beyaz yakın, siyah uzak; float32 ve 16-bit.
- `depth/depth_preview.png`: yalnız bakmak için 8-bit harita.
- `depth/metadata.json`: model revizyonu, ağırlık hash'i, süre, boyutlar ve dönüşüm sınırları.
- `render/`: Blender sahnesi, Nr görünüş ve hareketli önizleme.

DA3MONO doğrudan **göreli depth** üretir. Önce `1/Z` alınır, sonra yüzde 1–99
sınırları 0–1 yakınlığa dönüştürülür; uç değerler kırpılır ve sınırlar kaydedilir.
Bu, metre ölçümü veya baskı kalibrasyonu değildir. Kaynağın tamamı resize edilir,
kırpılmaz; derinlik bilinear yöntemle fotoğraf boyutuna geri getirilir.
AI haritasında duvak, saç, uçuşan yapraklar ve örtüşen kenarlar hatalı olabilir.
Bu komut temel fotoğraf/depth akışıdır; katmanlı arka plan, fırça ve baskı için Studio kullanın.
Otomatik nesne segmentasyonu ve üretken AI inpainting motoru bu sürümde bulunmaz.

Model: [resmi DA3MONO-LARGE](https://huggingface.co/depth-anything/DA3MONO-LARGE), Apache-2.0.
Resmi DA3 mono çekirdeği ve ön işlemcisi kullanılır; kullanılmayan uygulama/3D export
bağımlılıkları kurulmaz. Model ve kaynak revizyonları sabittir; kurulum dosyasında kayıtlıdır.
Hazır depth ile aşağıdaki akış AI paketlerine ihtiyaç duymadan çalışır.

### Bu fotoğrafla alınan sonuç

`outputs/wedding/` altında gönderilen 540×540 fotoğrafın DA3 depth haritası,
12 Blender görünüşü ve 22 karelik ileri/geri önizlemesi bulunur.
`render/preview.html` önizlemeyi, `render/scene.blend` Blender sahnesini açar.
`verification.json` kaynak hash'i, depth dönüşümü, görünüş sayısı ve gerçek Blender
projeksiyon kontrollerini kaydeder. Dokuz birim kontrolü geçti; gerçek önbelleğin
ağ bağlantısı olmadan okunabildiği de kontrol edildi.

Bu örnekte yan açılarda en çok yaklaşık %1.97 şeffaf alan bulunur.
İlk `outputs/wedding` örneğinde arka plan doldurma uygulanmamıştır.
Studio'da aynı fotoğraftan 48 görünüşlü, katmanlarla doldurulmuş çalışma ve baskı paketi üretildi.
Model iki kişinin göreli uzaklığını farklı tahmin ediyor; harita geometrik ölçüm sayılmaz.
Fotoğraf korunmuştur; sonuç baskı dosyası değildir.

## Windows'ta çalıştırma

PowerShell'i proje klasöründe açın:

```powershell
.\setup.ps1
.\run.ps1 doctor
.\run.ps1 demo
```

Demo sonunda `outputs/demo/render/preview.html` dosyasını tarayıcıda açın.
Demo sentetik bir kontrol görüntüsüdür, gerçek bir fotoğraf dönüşümü değildir.
Hazır demo bu projede üretildi. Yeniden üretmek için farklı klasör kullanın:
`.\run.ps1 demo --output outputs/demo-2`.

Kendi fotoğraf ve depth dosyanız için:

```powershell
.\run.ps1 render --photo "C:\Gorseller\foto.png" --depth "C:\Gorseller\depth.png" --config examples/render.json --output outputs/ilk-deneme
```

Blender otomatik bulunmazsa `--blender "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"`
ekleyin veya `BLENDER_PATH` ortam değişkenini kullanın. Bu makinede Blender 5.1.2 kullanıldı.
Python 3.10 veya üstü gerekir; setup varsa Codex'in paketli Python ortamını kullanır.
Normal Python ile `python -m pip install -e .` ve `python -m lenticular ...` da kullanılabilir.

## Girdiler ve ayarlar

Fotoğraf ve depth aynı piksel boyutu/yönünde olmalı. Depth tek kanallı 8/16-bit
PNG/TIFF veya 0–1 aralıklı float NPY olabilir. Renkli depth görselleştirmeleri kabul edilmez.
`white-near`: beyaz yakın, siyah uzak. Tersi için `black-near` seçin.
Depth tam kod aralığından okunur; fotoğraf başına otomatik min/max normalizasyonu yapılmaz.
EXIF ile dönen fotoğrafları depth ile aynı yönde önceden kaydedin. Renkli fotoğraf
sRGB varsayılır. Studio fotoğraf yüklerken gömülü ICC'yi sRGB'ye dönüştürür;
baskı renk dönüşümü ayrı çıktı ICC profiliyle yapılır.

`examples/render.json` dosyasını kopyalayıp düzenleyin:

| Ayar | Anlam |
|---|---|
| `nr` | Blender'ın üreteceği görünüş sayısı; 2–1024 |
| `ne` | Gelecekteki baskı kanal sayısı; şu an yalnız kayıt bilgisi, boş olabilir |
| `near`, `far` | Yakın ve uzak yüzeylerin sanal uzaklıkları |
| `zero` | Zero-parallax düzleminin sanal uzaklığı; near/far dışı da olabilir |
| `camera_span` | En sol ve sağ kamera arasındaki toplam açıklık; sanal birim |
| `positions` | İsteğe bağlı Nr adet açık kamera X konumu; camera_span yerine geçer |
| `focal_mm`, `sensor_width_mm` | Perspektif kameranın odak ve sensör genişliği |
| `grid_size` | Yatay mesh aralığı sayısı; daha yüksek değer daha fazla ayrıntı/RAM |
| `edge_threshold` | Normalize depth sıçramasında kesilecek üçgen eşiği |
| `sweep_seconds` | Baştan sona önizleme süresi; görünüş sayısından bağımsız |

Sanal uzaklıklar fiziksel lens kalibrasyonu değildir. Tek yüzeyli başlangıç mesh'i
depth sıçramalarında kesilir. Arkadaki yüzey bilinmediği için açılan alanlar şeffaftır;
damalı önizleme bu alanları açıkça gösterir. Temel `render` komutunda doldurma varsayılan kapalıdır;
Studio katmanlı renk/depth tahminini etkinleştirebilir.
Kaynak çözünürlüğünde PNG üretilir; bu aşamada büyük UV baskı boyutlarında performans hedeflenmez.

## Kamera modeli

`fpx = width * focal_mm / sensor_width_mm`.
Yakınlık d için `1/Z = (1-d)/far + d/near` uygulanır.
Mesh, kaynak fotoğrafın perspektif ışınları üzerinde oluşturulur.
Kamera X konumu c için `shift_x = -focal_mm*c/(sensor_width_mm*zero)` kullanılır.
Kameralar döndürülmez. Yatay izdüşüm:

`u(c) = u(0) + fpx*c*(1/zero - 1/Z)`.

Z=zero noktaları yerinde kalır; yakın noktalar sola, uzak noktalar sağa hareket eder
(kamera soldan sağa giderken). Her görünüşte Blender'ın gerçek projeksiyonu bu denklemle kontrol edilir.

## Çıktılar

- `views/view_0000.png` …: soldan sağa kamera sırasıyla RGBA görünüşler.
- `center.png`: orijinal merkez kameradan referans render.
- `scene.blend`: kaynak dokusu paketlenmiş, yeniden açılabilen Blender sahnesi.
- `preview.html`: oynatma/durdurma ve görünüş kaydırıcısı.
- `look-around.png`: döngülü, ileri/geri APNG; modern tarayıcıda açılır.
- `coverage.json`: görünüş başına şeffaf alan oranı; bu alanlar düzeltildi anlamına gelmez.
- `job.json`: kaynak hash'leri, Nr/Ne, kamera/mesh ayarları ve Blender sürümü.
- `render_result.json`: kamera konumları ve sayısal projeksiyon kontrolleri.
- `blender.log`: render günlüğü.

Çıktı klasörü boş olmalı; mevcut işlerin üzerine yazılmaz. Kaynak dosyalar yalnız okunur.
`sources/` altında çıktı oluşturulmaz.

## Yapılan doğrulama

Blender 5.1.2 ile 12 görünüş ve ayrıca eşit olmayan kamera adımlarında
Nr=18 / Ne=12 çalıştırıldı. Gerçek render piksellerinde zero-parallax işaretinde
kayma 0 piksel; yakın/uzak uç hareketleri yaklaşık ±7 piksel (hesap ±6,67) bulundu.
Merkez render ile kaynak arasında opak bölgelerde ortalama RGB farkı 0,162/255 oldu.
Sonuçlar demo klasörlerindeki `verification.json` dosyalarına kaydedildi.
Beş giriş/mesh kontrolü de geçti.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tools/check_demo.py outputs/demo/render
```

Bu kontroller sentetik sahne ve kamera bağlantısını doğrular; gerçek fotoğraf,
görünmeyen yüzey tamamlama veya fiziksel lenticular baskı kalitesi ölçülmedi.

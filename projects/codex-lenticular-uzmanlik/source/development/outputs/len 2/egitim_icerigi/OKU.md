# len 2 — Genel lentiküler ve yazılım eğitim içeriği

Bu içerik kullanıcının gösterdiği çalışma klasöründen bilgi çıkarmak için hazırlanmıştır. Yazılım veya görsel çıktı düzeltme görevi değildir. Bu bilgiler, yerel zekâya mevcut Lenticular Studio yazılımını kullanmayı öğretmek için derlenmektedir; görev tanımı `../GOREV_TANIMI.md` içindedir.

Kaynak: `C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1\outputs\studio\20261006-105350-02b4bafc`

Klasördeki 61 dosyanın görev haritası, dokuz JSON kaydının kaynak kopyası, 19 yerel bilgi kartı ve 11 lentiküler/görüntü işleme çevrim içi kaynak notu bu dizindedir. Kaynak dosyalar değiştirilmedi.

## Dosyalar

- `dosya_haritasi.json`: dosyaların hangi aşamaya ait olduğu ve seçilen kayıtların hash bilgileri.
- `kaynak_kayitlari.json`: kaynak JSON içerikleri; sayısal örnekler kendi bağlamında korunur.
- `yerel_bilgi_kartlari.jsonl`: açıklama, kaynak dosya ve örnek değerlerden oluşan eğitim içeriği.
- `cevrimici_bilgi_kartlari.jsonl`: daha önce araştırılmış birincil kaynakların özgün kısa özetleri; internetin tamamı değildir.

## Bu klasörden çıkarılan bilgi

### İşlem zinciri

Bir işte girdi hazırlığı, render ve baskı aşamalarının dosyaları ayrı tutulur. Ana proje kaydı render ve baskı ayarlarını birlikte taşır.

Kaynak: `project.json`, `render/job.json`, `print/print-report.json`.

### Görsel ve derinlik girdileri

Fotoğraf renk bilgisini, derinlik haritası sahne düzeni için kullanılan derinlik bilgisini taşır. PNG gösterimi ve sayısal NPY kaydı aynı iş içinde ayrı ürünlerdir.

Kaynak: `render/job.json`.

### Render ve baskı ayarlarının ayrılması

Kamera, derinlik, mesh ve katman ayarları render bölümündedir. Ölçü, PPI, yazıcı DPI, LPI ve kanal ayarları print bölümündedir. İki ayar grubu birbiri yerine kullanılmaz.

Kaynak: `project.json`.

### Sanal sahne ölçeği

near, far ve zero sahne kurulumunun derinlik değerleridir. Kaynak iş kaydı sahne uzunluklarının sanal birim olduğunu belirtir. Bunlar doğrudan basılı milimetreyle eşitlenmez.

Kaynak: `render/job.json`.

### Kamera görünüşleri

Nr render edilen bakış sayısını ifade eder. Konum dizisi, kamera ekseni ve kamera açıklığı birlikte kaydedilir. Her görünüşün dosyası ve gerçek kamera konumu izlenebilir.

Kaynak: `render/job.json`, `render/render_result.json`.

### Projeksiyon kayıtları

Her kamera kaydı, gerçek ve beklenen görüntü koordinatlarını içeren projeksiyon kontrol alanları taşır. Bu yapı, bir render adımının nasıl kayıt altına alındığını öğretir.

Kaynak: `render/render_result.json`.

### Sabit derinlik ve etki ayarları

zero_reference, effect_strength ve depth_curve düzenlenmiş derinliğin kontrol alanlarıdır. Kamera açısı ayrıca kaydedilir. Buradaki değerler bu çalışmaya aittir; bütün işler için varsayılan değildir.

Kaynak: `project.json`, `quality.json`.

### Katmanlı sahne yapısı

Sahne kaydı her derinlik katmanını bir mesh ve doku dosyasına bağlar. Ayrı maske dosyaları ve Blender sahnesi, renk, geometri ve görünürlük bilgisinin nasıl taşındığını gösterir.

Kaynak: `render/job.json`, `render/repair.json`.

### Gizli alan bilgisi

İş kaydı kullanılan onarım motorunu, dolgu sınırını ve tahmin edilen alan oranlarını saklar. Kaynak notu gizli rengin tahmin edildiğini açıklar; bu bilgi öğretim kaydında korunur.

Kaynak: `render/repair.json`, `quality.json`.

### İstenen ve uygulanan parametreler

İşlem raporu istenen kamera açısını, uygulanan açıyı, paralaks ölçülerini ve koruma alanlarını ayrı taşır. Bu, kullanıcı ayarı ile motorun kaydettiği sonuç değerini ayırmayı öğretir.

Kaynak: `quality.json`.

### Kapsama raporu

Kapsama kaydı her görünüş için opak olmayan alan oranını içerir. Dosyadaki açıklama bunun bir yeniden oluşturma doğruluğu puanı olmadığını belirtir. Alanın anlamı kendi tanımıyla saklanır.

Kaynak: `render/coverage.json`.

### Nr ve Ne eşlemesi

Nr kamera görünüşlerinin, Ne baskı kanallarının sayısıdır. source_indices dizisi kanalların hangi görünüşten alındığını kaydeder. Bu örnekte eşit olmaları iki kavramın aynı olduğu anlamına gelmez.

Kaynak: `render/job.json`, `print/print-report.json`.

### Baskı ölçüsü ve çözünürlük

Fiziksel ölçü milimetre, raster çözünürlüğü PPI, yazıcı ayarı DPI, lens sıklığı LPI alanlarıyla ayrı saklanır. Raster boyutu ve dosyadan hesaplanan fiziksel boyut ayrıca raporlanır.

Kaynak: `project.json`, `print/print-report.json`.

### Lens yönü, faz, eğim ve aynalama

Baskı ayarlarında lens yönü, faz, eğim, görünüş sırası ve bütün görüntünün aynalanması ayrı alanlardır. Eğitim örneği, bu alanları kaynak adlarıyla eşleştirmeyi sağlar.

Kaynak: `project.json`.

### Pitch testi

Pitch test kaydı bir aday LPI dizisi ve PPI bilgisi içerir. Üretim notları testi aynı lens/yazıcı/RIP/malzeme ve bakış koşullarında, gerçek ölçekte kullanmayı tarif eder.

Kaynak: `print/pitch-test.json`, `print/print-report.json`.

### Lens kanal yanıtı şeması

Yanıt şablonunda satır gözlenen bakış açısı, sütun basılan kanaldır. template_only alanı şablon verisini ölçüm verisinden ayırır. Bu yapı kalibrasyon bilgisinin dosyada nasıl temsil edildiğini öğretir.

Kaynak: `print/lens-response-template.json`.

### Renk ve beyaz alt baskı alanları

Renk modu, ICC profil yolu, renk profili hash kaydı ve beyaz alt baskı seçeneği ayrı taşınır. Beyaz çıktı kullanıldığında RIP bağlantısı, üretim notunda ayrı maske olarak tarif edilir.

Kaynak: `project.json`, `print/print-report.json`.

### Önizleme ve işlem durumu kayıtları

Önizleme dosyaları, benzetim ölçüleri ve üretim durumu ayrı kayıt türleridir. Bunları anlamları değişmeden okumak yazılım kullanım eğitiminin bir parçasıdır.

Kaynak: `print/print-report.json`.

### Kaynak ve çıktı izlenebilirliği

Kaynak fotoğraf/derinlik hash değerleri, iş kaydı hash değeri ve üretilen TIFF hash değeri farklı aşamalar arasındaki bağı izlemek için saklanır.

Kaynak: `project.json`, `render/job.json`, `print/print-report.json`.

## Çevrim içi kaynaklarla bağlantı

Pitch ve üretim akışı için DP Lenticular ve Triaxes; renk profili için ICC; katmanlı derinlik için Shih ve arkadaşları; alfa/ön plan için PyMatting; ara kareler için RIFE; lens tasarımı araştırması için Disney Research notları birlikte kullanılabilir. Bu kaynakların kendi yöntemleri, bu eski işin motorunda kurulu özellikler gibi sunulmaz.

Buradaki amaç alan bilgisini ve yazılım işleyişini kaynaklı biçimde derlemektir. Model adı, GPU veya ağırlık eğitimi bu içerik derleme aşamasının ön şartı değildir.

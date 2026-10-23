# Nesne hacmi, ince kenarlar ve arka plan: uygulanan geliştirmeler

10 Ekim 2026. Bu çalışma, önceki denetimde açık kalan nesne derinliği ve görünmeyen yüzey tamamlama alanlarına odaklanır. Fiziksel lens/yazıcı kapasitesinin kabulü baskı sonrasına bırakılmıştır. Her fotoğrafta kusursuz sonuç garantisi verilmez.

## Kullanım

- **Kenar ve arka plan kalitesi → Ayrıntılı** yeni çalışmalarda ince kenar ayrımı ve bilgisayarda LaMa doldurmayı kullanır. **Klasik** önceki hızlı yöntemi seçer. Fotoğraflar dış bir servise gönderilmez.
- **Nesnenin konumunu ve kendi hacmini düzenle → Nesne sınırı çiz:** sınır noktalarını sırayla seçip **Sınırı tamamla** düğmesine basın. Konum, nesneyi bütün olarak yakın/uzak taşır; kendi hacmi, mevcut derinlik biçimini ölçekler. Görünüşleri yeniden oluşturun.
- Bölgeler elle çizilir; otomatik anlamsal nesne seçimi değildir. Birbirini örten bölgeler listedeki sırayla uygulanır. Profil ve ayar dosyaları nesne sınırlarını da saklar.
- **Görüntü motoru ayrıntıları → Render boyutu → Fotoğrafın boyutu** kaynak çözünürlüğünü korur. İş raporu artık küçültülmüş görünüş ile kaynak boyutunu ayırır.
- Yeni bir bilgisayarda mevcut derinlik ortamından sonra `setup-quality.ps1` çalıştırılır. Bileşenler eksikse Ayrıntılı yöntem açık bir hata verir; sessizce farklı bir motora geçmez. Klasik yöntem kullanılabilir.

## Değişiklikler ve kanıt

| Alan | Uygulanan değişiklik | Sınama |
|---|---|---|
| Nesne konumu / kendi hacmi | Bölgesel konum ve hacim ayrı kontrol edilir. Uçlarda alan kalmazsa bütün nesnenin hacim artışı sınırlandırılır; yalnız tepe değerleri kırpılıp düzleştirilmez | Seçilmeyen piksellerin korunması, iç biçim oranı, düz harita, geçersiz bölge kayıtları |
| İnce kenarlar | PyMatting kapalı form alfa ve ön plan rengi ayırma; kaynak çözünürlüğünde, bağlamı örtüşen küçük parçalar | Bilinen yarı saydam sentetik kenar, opak merkez renginin korunması; gerçek portrede 45 parça |
| Yan bakışlarda tırtıklanma | Karışmış kenar derinliği güvenilir iç bölgeden uzatılır. Görünür nesne kenarı, gizli arka plan enterpolasyonundan korunur. Gelişmiş yüzeyde doğrusal mesh örneklemesi kullanılır | Dalgalı sınır derinliği testi, eğimli düzlem testi ve aynı portrenin uç görünüş karşılaştırması |
| Arka plan tamamlama | LaMa yerel CPU çıkarımı; bir kez oluşturulan ortak doku tüm bakışlarda kullanılır | Gerçek model, tek/çift boyut hizalaması, maske dışındaki renklerin bire bir korunması |
| Gizli derinlik | Görünen güvenilir derinliği değiştirmeden sınırlandırılmış yumuşak uzatma | Bilinen eğimli yüzeyde doldurma ve değer sınırları |
| İki düzlemli sahne | Alan yüzdelikleri derinlik uçlarına denk geldiğinde katmanların yanlışlıkla tek yüzeye düşmesi düzeltildi | İki katmanlı yapay sahne |
| Kayıt / arayüz | Nesne sınırları ve ayarları profil/dışa aktarım verisine katıldı; değişiklikler eski görünüş uyarısını tetikler | Ayrı test sunucusunda sınır oluşturma, konum 0,10 / hacim 1,50 ayarlama, kaydetme, temizleme ve geri yükleme; JavaScript hata kaydı yok |

Gelişmiş ince kenar ayrımı için PyMatting 1.1.16, numba 0.68.0 ve llvmlite 0.50.0 eklendi. Mevcut paketler değiştirilmedi/kaldırılmadı. LaMa TorchScript v0.1.0 dosyası (205.803.670 bayt) kaynak adresi, SHA-256 ve lisans belgeleriyle yerelde saklandı. Model SHA-256: `7ba7aa7ac37a4d41fdbbeba3a2af7ead18058552997e3a3cd1a3b2210c9e6b4c`.

## Doğrulama

- Son bütünleşik çalıştırmada **46 test geçti**. JavaScript sözdizimi kontrolü geçti.
- Aynı gerçek portrede **1872 × 3098 piksel, 12 bakış** ve **6142 × 10164 piksel TIFF** üretimi sınandı. Kaydedilen TIFF'in örneklenen piksel satırları doğrulandı. Bu, her pikselin bağımsız optik kalite ölçümü değildir.
- İlk tam boy görsel incelemede parmak kenarında tırtıklanma bulundu. Sadece test başarısına dayanılarak teslim edilmedi; güvenilir kenar geometrisi ve örnekleme düzeltildi. Son denemede pahalı renk/matting hesabı yerine doğrulanmış ortak dokular kullanılarak yeni geometri oluşturuldu.
- Kaynak fotoğraf ve derinlik dosyalarının SHA-256 değerleri değişmedi. Önceki çıktılar korunmuştur.
- Güncel sürüm aktif iş olmadığı doğrulandıktan sonra normal kapanışla yeniden başlatıldı. 6 görsel, 99 iş, 13 profil ve durum dosyasının SHA-256 değeri aynı kaldı; yeni varsayılanlar API'den doğrulandı. `restart-verification.json` bu kontrolü içerir.
- Paket denetimi, DA3'ün bu projede bilerek kurulmayan tam uygulama/ihracat bağımlılıklarını bildirdi. Mevcut `setup-depth.ps1` DA3'ü `--no-deps` ile kurar; `requirements-depth.txt` yalnız kullanılan mono çekirdeğini açıkça listeler. Bu uyarılar yeni üç paketin getirdiği sürüm çakışması değildir. DA3 tam uygulama özelliklerinin tamamı kurulmuş sayılmaz.

Kanıt dizini: `outputs/surface-upgrade-20261009-220345/`. `native-portrait` ilk tam üretim; `native-portrait-corrected` ilk geometri düzeltmesi; `native-portrait-final` son geometri ve çıktı denetimidir. İlk iki klasör son sonuç yerine kullanılmamalıdır.

Parmak kenarı karşılaştırması: `thumb-final-comparison.png`. Belirgin üst kenar tırtıklanması azaldı; alt kenardaki kalan biçim bozulmaları, kaynak derinlik ve tek fotoğraftan tahmin sınırları nedeniyle tümüyle giderilmiş sayılmaz. Üretilen görünüşler fiziksel baskı onayı değildir.

## Kalan sınırlar

- Tek fotoğrafta görünmeyen içerik tahmindir. LaMa renk dokusunu üretir; gerçek gizli nesnelerin geometrisini ölçmez. Gizli derinlik, görünür geometriye dayalı sınırlandırılmış uzatmadır.
- Renk tamamlama CPU maliyetini sınırlamak için en uzun kenarı 1024 piksel olan bağlamda yapılır; yalnız doldurulan bölge kaynak boyutuna taşınır. Görünür fotoğraf dokusu ve matting kaynak çözünürlüğündedir. Çok büyük yeni açılan alanların ince dokusu ayrıca değerlendirilmelidir.
- Alfa ayrımı başlangıç siluetine bağlıdır. Saç, cam, duvak ve benzer renkli ön/arka plan her görüntüde otomatik ve hatasız ayrılmış kabul edilemez. Çözülemeyen kenar alanı raporlanır.
- Fotoğraf sınırının dışındaki alanlar temel yüzeyde hâlâ kenar uzatmasıdır; büyük açıda dış kenar tekrarları görülebilir. Tam sahne kontrolünde bunlar kırpma/taşma alanıyla birlikte değerlendirilmelidir.
- Bu çalışma otomatik SAM nesne seçimi, 16-bit uçtan uca baskı, bağımsız X/Y PPI, PSD/PSB aktarımı veya ölçülmüş lens simülasyonu eklemez. Bunlar önceki geniş denetimin ayrı geliştirme kalemleridir.
- Lens altında netlik, hayalet görüntü, arka hacim algısı ve farklı açılarda rahat görüş hâlâ aynı lens/yazıcı/RIP koşulunda fiziksel kabul gerektirir.

## Birincil teknik kaynaklar

- [PyMatting alfa ayrımı](https://pymatting.github.io/alpha.html) ve [ön plan rengi ayrımı](https://pymatting.github.io/foreground.html): trimap tabanlı alfa ve renk kestirimi.
- [LaMa araştırma deposu](https://github.com/advimman/lama): büyük maskelerde renk tamamlama yaklaşımı. [Yerel TorchScript dönüşümü](https://github.com/enesmsahin/simple-lama-inpainting): kullanılan model dağıtımının kaynağı; LaMa deposu bu üçüncü taraf uygulamaya bağlantı verir.

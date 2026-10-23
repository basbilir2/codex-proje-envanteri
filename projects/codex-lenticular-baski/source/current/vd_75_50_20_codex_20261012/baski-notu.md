# 75 ve 50,20 LPI — aynı görüntülerle baskı

- **75 LPI:** `75lpi/interlaced.tif`
- **50,20 LPI:** `50_2lpi/interlaced.tif`
- Mevcut **100 LPI** dosyası korunmuştur: `../vd_100lpi_codex_20261012/print/interlaced.tif`.

Her iki yeni dosya **6141 × 10163 px**, **1200 PPI**, RGB ve sRGB ICC profillidir. Fiziksel ölçü **129,9845 × 215,1168 mm** (yaklaşık 13 × 21,51 cm). **%100 gerçek ölçekte basın; sayfaya sığdırmayı ve yeniden boyutlandırmayı kapatın.**

100 LPI için doğrulanan **aynı altı kamera karesi**, **aynı altı baskı kanalı** ve **aynı kanal sırası [5,4,3,2,1,0]** kullanılmıştır. **4° kamera aralığı**, sıfır düzlemi, yüz/parmak/kıyafet/arka plan geometrisi, derinlik haritası, faz 0, dikey lens, aynalama/beyaz katman kapalı ve renk ayarları değişmemiştir. Yalnız nominal ve etkin LPI değiştirilmiştir. AI veya Blender çalıştırılmamış; yeni açı/derinlik hesabı, görsel denemesi ya da hareketli önizleme üretimi yapılmamıştır.

Kanal başına raster örneklemesi 75 LPI'de **2,6667**, 50,20 LPI'de **3,9841** pikseldir. 75 LPI / 6 kanal / 1200 PPI kesirli şeritlere denk geldiğinden bazı kanallar farklı raster payı alabilir; kanal sayısı veya örnekleme yöntemi bunu gidermek için değiştirilmemiştir. Bu, kamera görüntülerini değiştirmez. Fiziksel lens ayrımı ve algılanan derinlik için önceki ölçüm belirsizlikleri sürer; dosyalar fiziksel kalite onayı değildir.

Ortak hareketli önizleme: `../vd_100lpi_codex_20261012/hareketli-onizleme.gif`.

Her dosyada ölçü, 1200 PPI ve 588 bayt ICC kontrol edildi. Mevcut motorun yeni şeritler için yaptığı 30.705 örnek piksel kontrolü geçti. Kaynak kare ve derinlik hash'leri mevcut doğrulama kaydıyla eşleşti. Büyük TIFF'ler doğrulamadan sonra yeniden hash'lenmedi; üretim sırasında yazılan hash kullanıldı. Ek pitch sayfaları üretilmedi.

Teknik kayıt: `knowledge/runs/vd-75-50-20-reinterlace-20261012.json`; yeniden kullanılabilir yardımcı: `tools/reinterlace_existing.py`.

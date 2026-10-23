# Uygulayıcı modele verilecek başlangıç görevi

Bu metin gelecekte uygulama başlatmak için hazırlandı. Hazırlayan model yalnız araştırma ve mimari çalışması yaptı; kod, kurulum veya canlı veri değişikliği yapmadı.

---

Mevcut Lenticular Studio'ya aşağıdaki mimariye uygun animasyon motorlarını ekle. Mimariyi baştan kurma; çalışan motorların üzerine dar eklemeler yap.

Önce şu iki belgeyi oku:

1. [Ana mimari](C:/Users/USER/.codex/.chatgpt-projects/g-p-6ac173361d8c8191a1449be5154f589f/LENTICULAR_ANA_MIMARI.md)
2. [Görev ve kabul planı](C:/Users/USER/.codex/.chatgpt-projects/g-p-6ac173361d8c8191a1449be5154f589f/LENTICULAR_GOREV_PLANI.md)

Uygulama kaynak kökü:

    C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1

Belgelerin bulunduğu g-p-6ac173361d8c8191a1449be5154f589f klasöründe yeni bir program kurma. Kaynak kökünün kimliğini ve AGENTS.md talimatlarını doğrula. Kaynaklar değişmişse kullanıcının yeni kodunu koru; yalnız görevle ilgili farkları incele.

Ana teslim hedefin M0–M5: **iki fotoğraf yükleyerek yeni ara kareler üretebilmek, akıcı hareket/morph önizlemesi sunmak ve bunu mevcut lenticular baskı hattına bağlamak.** İki fotoğrafı tekrarlamak veya basit dissolve yapmak hareket ara karesi kabul edilmez. Farklı görüntüler için yönlendirilebilir morph bulunmalı; düşük eşleşme gizlenmemeli.

Teknik omurga: kaynak → efekt/ara kare motoru → FrameSet → ChannelPlan → mevcut telafi/interlacing/ICC/TIFF. Kamera gerekmeyen animasyonda AI depth ve Blender çağırma. Sahte Blender job.json oluşturarak animasyonu 3D gibi gösterme. Eski fotoğraf/3D yolu ve çağrı imzaları adaptörle korunsun.

Kullanıcı Grondo UV yazıcı kullanıyor. DPI, PPI, LPI ve baskı ölçüleri zaten değişken. 1200 DPI'yi yeni varsayılan yapma, sabitleme veya PPI'ye eşitleme. Profilin kullanıcının seçtiği mevcut değerlerini koru. Ns, Nt, Nr ve Ne ayrı kavramlar; preview_fps baskıdaki fiziksel hareket hızı değildir.

RIFE ara kare için ilk yerel AI adayı; kesin sürüm/ağırlık ve donanım uygunluğunu küçük örnekte doğrula. OpenCV akış ve kontrol noktalı morph ayrı sağlayıcılar olabilir. Kod/ağırlık revizyonlarını ve lisans bilgilerini kaydet. Mevcut DA3 ortamını bozacak toplu bağımlılık yükseltmesi yapma.

Kaynak fotoğraflar, sources/, eski çıktılar, model ağırlıkları ve kullanıcı ayarları korunacak. Migrasyon gerekiyorsa önce doğrulanmış durum kopyası al ve kopyada dene. Mevcut render çıktıları yerinde dönüştürülmeyecek. Ağ servisine fotoğraf gönderme.

M0'dan başla ve M0–M5'i bağımlılık sırasıyla uygula. Rutin aşama geçişleri için tekrar tekrar onay isteme. Uygulama yetkisini kullanıcı bu görevi başlattığında almış olursun. M6–M9 ileri yol haritası; bunların tasarımını çekirdek teslimi geciktirecek şekilde topluca uygulama.

Her aşamada yalnız ilgili dosyaları oku, minimum değişiklik yap, gerekli davranış testlerini bir kez çalıştır. Başarısız testi çözmeden tamamlandı deme. Aşama sonucunu kısa kaydet: amaç, tamamlananlar, kararlar, dosyalar, test kanıtı, sınırlar, sonraki adım.

Mimari sözleşmesini değiştirmek zorundaysan kodu rastgele genişletmek yerine somut uyuşmazlığı ve önerini bildir. Kullanıcı verisi veya mevcut davranışla çatışmayan rutin uygulama tercihlerini kendin çöz.

Dijital teslim: çalışan iki fotoğraflı akış, zaman/kanal önizlemeleri, mevcut baskı ayarlarıyla TIFF, seçildiyse White, kalibrasyon dosyaları, kanal eşleme ve iş raporu. Gerçek lens/Grondo/RIP numunesi yapılmadıysa bunu açıkça fiziksel kabul bekliyor olarak işaretle. Yazılımın çalışması fiziksel baskının kusursuz olduğunu kanıtlamaz.

İlk raporunda yalnız doğru kaynak kökünü, kodun mimariyle ilgili değişmiş olup olmadığını ve başladığın M0 kontrolünü bildir; mimarinin tamamını yeniden yazma.

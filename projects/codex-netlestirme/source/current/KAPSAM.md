# Güncel kapsam — 22 Ekim 2026 / Design Recovery

**Son kapanış:** `training/pilot-20261022/validation-20261022/SONUC.md`. Gerçek GPU eğitimi tamamlandı; checkpoint bayrakları ve 2511 tek-elemanlı görsel-listesi yolu düzeltildi. Son 48-adım LoRA ağırlığı hash eşleşmesiyle yerelde. Mavi ana tasarımı ayrılıyor ve koyu dolgu korunuyor; **EST.1991 yine yok, kalite GEÇMEDİ**. SOLAR temel model çıktısı var; son LoRA dosyası alınamadı, doğrulanmış sayılmaz. GPU kontrol edildiğinde kapalı, aktif oran 0; bakiye PRIVATE_AMOUNT, bu oturum farkı PRIVATE_AMOUNT. Kapanış kontrolü gecikti, 60 dakika hedefi doğrulanmadı. Sonraki ücretli kaynak öncesi GPU zamanlı kapanışı güvenceye alınmalı. Yeni kaynak/seed/model taraması yapma. Aşağıdaki aktif/bekleyen notlar tarihseldir.

**Aktif doğrulama:** Kapasite bulundu; A40 `c5p7p5u451kqpy`, 100 GB disk, yaklaşık PRIVATE_AMOUNT/saat. Checkpoint düzeltmesiyle 48 adım tamamlandı ve ağırlık yerelde saklandı; Mavi tasarımını ayırmadı. Kayıt incelemesinde 2511 resmî örneğinin tek görsel için de liste kullandığı, eski tek-Image girişinin farklı prompt/conditioning yoluna girdiği saptandı. İlk çalışma `training/pilot-20261022/single-input-v1/` arşivinde. Aynı PRIVATE_AMOUNT/60 dakika oturum sınırında yalnız bu somut giriş düzeltmesiyle pilot sürüyor; yeni model/veri/seed taraması yok. Aktif durum `on-kontrol/gelistirme-durumu.json`; bu süreç sonunda GPU kapatılmalı. Aşağıdaki kapasite engeli tarihsel.

**Son devam girişimi:** Düzeltilmiş pilot için mevcut A40 başlatma/otomatik taşıma ve aynı A40'ın yeni sunucusu kapasite yok yanıtı verdi. Yeni pod veya eğitim başlamadı, bu girişimde yeni harcama yok; görünen bakiye PRIVATE_AMOUNT. Kaynaklar kapalı. `training/pilot-20261022/corrected-validation-attempt.json`. Kaynak düzeltmesinin GPU doğrulaması hâlâ bekliyor; otomatik ücretli kaynak rezervasyonu yapılmadı.

**Son pilot kaydı:** `training/pilot-20261022/SONUC.md`. 6 eğitim/2 ayrılmış sentetik tasarım çifti hazır; bulutta ön işlem tamamlandı. Eğitim 0/48 güncellemede bellek hatasıyla durdu. Kayıttan saptanan kapalı önbellek checkpoint bayrakları başlatıcıda düzeltildi; bu son düzeltme GPU'da doğrulanmadı. Yeni kalite sonucu/checkpoint yok. GPU kapalı, son bakiye PRIVATE_AMOUNT, aktif oran PRIVATE_AMOUNT/saat. Yeni deneme/model/GPU taraması yapmadan bu kaydı kullan; aşağıdaki önceki durumlar tarihseldir.

Son kullanıcı isteği önceki görsel iyileştirici mimarisini geçersiz kıldı. Ana ürün **Design Recovery / Artwork Reconstruction Engine**: fotoğraf, mockup, tişört, tabela, ekran veya düşük kaliteli kaynak içindeki gerçek tasarımı kurtarmak. Düz tasarım onarımı ve fotoğraf restorasyonu ayrı görevlerdir.

**En son kullanıcı kabulü — 22 Ekim:** Kullanıcı `outputs/mavi-karsilastirma-20261022/chatgpt-tasarim.png` sonucunun netliğini ve yeniden oluşturma seviyesini “çok yeterli” buldu; yazılımın sonucunun bu seviyede olmasını istiyor. Bu dosya artık bu iki özellik için onaylı somut kalite referansıdır. Önceki “bu referans kullanıcıca kabul edilmedi” kayıtları bu kapsamda geçersizdir. Tasarımı yüzeyden ayırma, düz/temiz konturlar ve okunur küçük yazı esas alınır. Bu kabul yeni Qwen başarısı, ürün/hız kabulü, temiz alpha veya kesin gerçek renk doğrulaması değildir. Referansın kendisi opak gri zeminlidir. Kullanıcının yeterli bulduğu seviyenin üstüne yeni kusursuzluk şartları ekleyerek çalışmayı erteleme. Makine okunur kabul kaydı `on-kontrol/approved-recovery-reference.json` içindedir; görseli örneğe özel inference hilesi veya tek eğitim doğrusu olarak kullanma.

## Hedef ve korumalar

Yüzey dokusu, kıvrım, ışık/gölge, parlama, perspektif ve sıkıştırma etkileri giderilirken yazı/rakam, logo, desen, çizgi, dolgu, yüz kimliği, geometri ve tasarım renkleri korunmalıdır. Kaynak fotoğrafının gölgeli renklerini kilitlemek veya fotoğrafa piksel benzerliği başarı değildir. Kaynak korunur; kullanıcıya doğru metin yazma, örnek eşleştirme veya zorunlu işaretleme hazırlığı verilmez. İsteğe bağlı alan/dört köşe ve mevcut fırça araçları korunur. Upscale ve alpha yardımcıdır; ana yetenek değildir. Yalnız belirli örneğe özel kod genel çözüm sayılmaz.

Kalite referansı ChatGPT'dir; eski FLUX çıktısı baseline değildir. Hedef kalitenin varlığı belirsiz değildir; bu motorun o kalite ve hıza ulaşıp ulaşmadığı doğrulanmamıştır.

## Bu tur uygulanan mimari

`app/pipeline.mjs`: özgün kaynak → yön/sRGB/isteğe bağlı geometri → görev tabanlı üretken adaptör → teknik kontrol ve doğrulanmamış kalite raporu → isteğe bağlı 2×/alpha/düzenleme → ayrı PNG dışa aktarma. `geometry.mjs` düzlemsel dört köşe homografisini uygular. `qwen-adapter.mjs` yerel motoru değiştirilebilir adaptör olarak bağlar; motor hatasında filtreye geçmez. Eski quick API yolu kaldırıldı. `app.py` / `pipeline.py` bu checkout'ta yoktur; mevcut Node/Python omurgası geliştirildi.

Kurulu Qwen-Image-Edit-2511 mevcut üretken aday adaptördür; adı ürün mimarisini tanımlamaz ve yeni hedef için kabul edilmiş motor değildir. Yeni LoRA/model indirilmedi veya eğitilmedi. BiRefNet ve 2× yalnız yardımcıdır. sRGB PNG'de alpha korunur; 4K/8K dışa aktarma yeniden örneklemeyi ayrıca kaydeder, baskı kabulü iddia etmez.

## Doğrulanmış durum ve engeller

**22 Ekim gerçek bulut kurtarma denemesi:** `on-kontrol/cloud-recovery-20261022/` içinde tek yeni çıkarım yapıldı. A40, Qwen-Image-Edit-2511 Q4_K_M, hızlandırıcı olmadan 40 adım, 1024×640, tam Mavi kaynak fotoğrafı, 235,19 saniye. Tasarım yüzeyden ayrıldı; lacivert dolgular beyaza dönüştü ve EST.1991 kayboldu: **GEÇMEDİ**. Elle rötuş, ikinci seed/prompt denemesi veya yerel çıkarım yok. Bu henüz eğitim değildir. GPU kapandı, aktif oran PRIVATE_AMOUNT/saat; görünen bakiye 10,34 → PRIVATE_AMOUNT. Sonraki hedef, dolgu/metin korumaya yönelik eşlenik veri ve LoRA uyarlama hazırlığıdır; temel modelin bu tek başarısız sonucunu genel model sıralaması sayma. DiffSynth-Studio'nun tam 2511 LoRA eğitim örneği sabit revision'da bulundu; henüz kurulup çalıştırılmadı. Aşağıdaki “yeni görev ÇALIŞTIRILMADI” kaydı bu yeni deneyden öncedir ve bu tek örnek için geçersizdir.

14 otomatik yazılım kontrolü geçti; yeni arayüz gerçek kaynakla açıldı, dört köşe seçimi ve kaynak önizlemesi kontrol edildi. Bunlar gerçek reconstruction kalite kanıtı değildir. Bağlantı testlerinde kullanılan motor açıkça test dublörüdür.

Yeni kurtarma göreviyle gerçek üretim **ÇALIŞTIRILMADI**. Önceki Qwen+4-adım yerel 512×512 işi 304,25 saniyede çıktısız zaman aşımına uğradı. Önceki A40 768×1664/39,11 saniye çıktısı sahne restorasyonuydu; kumaştan tasarım kurtarma kanıtı değildir. `enhancementReady=false`, `trialEnabled=true`, ürün kabulü yoktur. Otomatik tasarım konumlandırma, kumaş deformasyon haritası, güvenilir OCR/kimlik/gerçek renk doğrulaması ve yüksek ayrıntılı 4K/8K üretim eksiktir. Kod yazmak yeni tanıma yeteneğini eğitmez.

Mevcut servis 17861 korunuyor; otomatik denetim durdurup yeniden başlatmayı engelledi. Yeni sürüm bu oturumda **http://127.0.0.1:17863/** üzerinde açık. Sonraki tur güncel servisi kullan; eski süreci yeni backend sanma. `Baslat.cmd` varsayılan yeni portu açar.

## Maliyet ve devam sınırı

Son üründe ücretli görsel API'si/model lisansı veya RunPod bağımlılığı yok. Hedef önce PC, daha sonra kendi web sitesi; Wix bu işin dışında. RunPod yalnız geliştirme iznidir; bu tur yeni kaynak açılmadı veya ödeme yapılmadı. Önceki toplam üst sınır PRIVATE_AMOUNT, son görünen bakiye PRIVATE_AMOUNT ve GPU kapalıdır; bunlar geçmiş kapanış kaydıdır, bugün tekrar sorgulanmadı. Yeni ücretli kaynak/deney için güncel açık bütçe gerekir. Otomatik ödeme/ek harcama yok.

Devam ederken `app/README.md`, `MIMARI.md`, `on-kontrol/RECOVERY-MVP.md` ve `on-kontrol/gelistirme-durumu.json` kullan. Önceki ağır deneyler `SONUC.md` içindedir; gerekçesiz tekrarlama. Gerçek model üretimi, çeşitli bağımsız girdilerle sadakat/yüzeyden ayrılma ve PC hız kabulü olmadan bitmiş çalışan ürün teslimi yoktur.

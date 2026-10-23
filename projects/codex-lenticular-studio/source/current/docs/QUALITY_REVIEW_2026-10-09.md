# Lenticular Studio: kalite denetimi ve uygulanan iyileştirmeler

**10 Ekim güncellemesi:** Nesne bazlı hacim düzenlemesi, PyMatting ve yerel LaMa artık uygulanıp sınandı. Bu belgedeki 9 Ekim eksik tablosunun güncel durumu için [devam raporuna](SURFACE_QUALITY_2026-10-10.md) bakın.

9 Ekim 2026. Kullanıcının önceliği: güçlü 3D ile netliği birlikte korumak; öne çıkan nesne kadar arka planda da hacim elde etmek.

Bu çalışma mevcut yazılımı değiştirdi ve gerçek portreyle dijital üretim hattını sınadı. Ticari yazılımlar lisanslı çalıştırılarak karşılaştırılmadı; üretici kılavuzları ve yayımlanmış araştırmalar incelendi. İnternetin bütün kaynaklarının tarandığı veya fiziksel baskının kusursuz olduğu iddia edilmez.

## Sonuç

Sorun tek bir ayar değil. Derinlik haritasının yüzey ayrıntısı, ön/arka paralaks dağılımı, gerçek baskı kanalları, lens pitch'i ve RIP'in şeritleri koruması birlikte belirleyici. Kamera açısını artırmak bu zincirdeki eksikleri tek başına çözmüyor.

Son tam sahne portresinde arka planın sayısal derinliği var. Dolayısıyla görülen zayıflık yalnız “arka plan haritası düz” açıklamasına indirgenemez. Fiziksel kanal ayrımı ve baskı koşulları ölçülmeden sorunun tamamını render'a bağlamak doğru olmaz.

## Kodda düzeltilenler

| Bulgu | Uygulanan değişiklik | Doğrulama |
|---|---|---|
| Tek ortak paralaks sınırı bir güçlü ön nesne nedeniyle arka planı da kısabiliyor | İsteğe bağlı **Dengeli** derinlik eğrisi; ön ve arka için bağımsız uç-fark yüzdeleri. Sıfır düzlemi ve her taraftaki derinlik sırası korunuyor | Bağımsız taraf değişimi, sabit nokta, düz harita ve gerçek Blender görünüşleri |
| Kenar korumasının sonucu görüntü çözünürlüğüne bağlı değişebiliyordu | Kenar türevi önce ortak 512 piksel ölçeğine getiriliyor | Aynı sürekli sahnenin 512 ve 2048 piksel örnekleri |
| Alan örneklemesi 8 veya 16 alt piksel örneğiyle yaklaşık hesaplanıyordu | Eğik ve düz lenslerde periyodik şeritlerin piksel alanı analitik hesaplanıyor; lineer ışıkta birleşiyor | Bilinen %85/%15 sınır; bağımsız yoğun integral; negatif faz, ayna, iki eksen; çok küçük eğim ve uç PPI/LPI oranlarında ağırlık toplamı |
| TIFF piksel denetimi yalnız telafisiz merkez örneklemesinde vardı | Alan ve telafili çıkışta da kaydedilen TIFF'ten örnek satırlar geri okunup doğrulanıyor | Kasıtlı dosya bozulması reddediliyor |
| Kanal önerisi kanal başına 1 piksel bırakabiliyordu | Kanal başına en az 2 raster piksel bırakan başlangıç önerisi; fiziksel kapasite olarak etiketlenmiyor | 1200 PPI / 50 LPI için 12; bağımsız UI kontrolü |
| Yatay lens pitch testi yanlışlıkla baskı enine göre uzuyordu | Hareket ekseninde baskı boyu esas alınıyor; kanal yanıt testi de düzeltiliyor | Dikdörtgen yatay baskı testi |
| Bazı ayarlar değişince eski kalibrasyon işaretleri ve lens matrisi kalabiliyordu | İlgili onaylar kaldırılıyor; eski matris geçersizleştiğinde varsayımsal modele sessiz telafi uygulanmaması için telafi sıfırlanıyor. Yeniden baskıda bu işlem matris boyutu kontrolünden önce yapılıyor | Birim testleri, eski matrisle yeni kanal sayısına yeniden baskı entegrasyon testi ve tarayıcıda ölçü değişimi |
| Nr hareket adımı, gerçek Ne baskı adımıyla karıştırılabiliyordu | Seçilen kamera indekslerinden Ne adımı hesaplanıyor; ön/arka iç hacim, lens aralığı cinsinden risk ve harita raporlanıyor | 25 render'dan 3 ve 25 kanal seçiminin farkı |
| Bir matrisin yüklenmesi fiziksel ölçüm doğrulanmış gibi raporlanıyordu | Matris “sağlanmış” olarak kaydediliyor; bağımsız fiziksel doğrulama iddia edilmiyor | Rapor alanları denetlendi |

Mevcut kayıtlı ayarlar ve eski çıktılar dönüştürülmedi. Dengeli mod seçilmedikçe eski yumuşak/doğrusal derinlik davranışı korunur. Merkez örneklemesi eski kodla piksel düzeyinde karşılaştırıldı. Alan örneklemesindeki piksel farkı amaçlıdır; yeni hesap eski yaklaşımı tekrar etmez.

## Gerçek portrede önce/sonra

Kaynak: mevcut 1872 × 3098 tam sahne portresi ve onun derinlik haritası. Önceki 24 görünüşten 12 baskı kanalı seçildi. Yeni dengeleme 12 gerçek Blender görünüşüyle, 768 piksel uzun kenarda kontrol edildi. Ölçü hesabında aynı 130 mm baskı genişliği ve 50,20 LPI kullanıldı.

**Aşağıdaki mm değerleri uç görünüşler arasındaki baskı düzlemine ölçeklenmiş kaymadır; algılanan fiziksel 3D derinliğinin santimetre ölçümü değildir.**

| Gösterge | Önce | Dengeli deneme |
|---|---:|---:|
| Ön bölgenin en büyük uç kayması | 4,75 mm | 3,90 mm |
| Arka bölgenin en büyük uç kayması | 3,33 mm | 3,90 mm |
| Arka bölge içindeki kayma yayılımı, p10–p90 | 2,54 mm | 2,98 mm |
| En büyük ardışık kanal adımı | 0,855 lens aralığı | 0,701 lens aralığı |
| Derinlik uçlarında kırpılma | Bu karşılaştırmada yeniden uygulanmadı | %0 |

Bu örnekte arka planın payı yaklaşık %17 arttı; en büyük adım yaklaşık %18 azaldı. Ön plandaki uç etki de yaklaşık %18 azaltılarak bütçe dengelendi. Bu bir ödünleşimdir: yazılım aynı lenste sınırsız derinlik ve sınırsız netlik üretmez. Fiziksel netlik artışı henüz ölçülmedi.

Aynı eski sahnenin 6/10/12 kanal denetimi:

| Ne | En büyük adım (lens aralığı) | Bir lens aralığını aşan alan |
|---:|---:|---:|
| 6 | 1,880 | %33,57 |
| 10 | 1,045 | %0,62 |
| 12 | 0,855 | %0 |

Bir lens aralığı eşiği teşhis amaçlı geometrik göstergedir; evrensel optik kabul standardı değildir. 12 kanalın geometrik geçişi daha ince olurken, 1200 PPI / 50,20 LPI baskıda kanal başına yalnız 1,992 raster piksel kalır. Yazıcının bunları fiziksel olarak ayırabildiği ayrıca görülmelidir.

130 mm en ve 12 kanalda 50,00 yerine 50,20 LPI kullanımı, kenardan kenara 1,024 lens döngüsü / 12,28 kanal farkı oluşturur. Çeyrek kanal birikimli kayma hesabı yalnız yaklaşık 0,00407 LPI veya %0,00811 ölçek hatasına karşılık gelir. Bunlar hassasiyet hesaplarıdır; 50,20'nin her mesafe ve baskı modu için doğru olduğunun kanıtı değildir.

## Uçtan uca eksik değerlendirmesi

| Alan | Mevcut durum | Kalan ihtiyaç / kabul koşulu |
|---|---|---|
| Tek fotoğraftan derinlik | Yerel DA3 ve bölgesel ayrıntı motoru var | Yüz, saç, yansıma, aynı derinlikteki desenlerde tahmin hatası olabilir. Kritik nesnelerde düzeltme veya gerçek çoklu bakış kaynağı gerekir |
| Arka planın kendi hacmi | Ayrı arka etki ve yeni iç-hacim raporu var | Hatalı veya düz tahmini haritadan gerçek detay geri kazanılamaz; nesne bazlı harita düzenleme daha güçlü olmalı |
| Görünmeyen yüzeyler | Ayrı alfa/derinlik katmanları ve Telea doldurma var | Büyük açılan bölgelerde doku uzaması ve bulanıklık kalabilir. Öğrenilmiş, sahne boyunca tutarlı renk+derinlik doldurma eksik |
| Nesne seçimi / saç / duvak | GrabCut sınır düzeltmesi ve fırça var | Anlamsal maske, gerçek matting ve elle katman düzeltme iş akışı eksik |
| Derinlik ve netlik bütçesi | Ön/arka ayrı bütçe, seçilmiş Ne risk raporu eklendi | Lensin açısal yanıtı ve MTF'si ölçülmeden tam optik optimizasyon yapılamaz |
| Kalibrasyon | Pitch, kanal yanıtı, faz, eğim ve kullanıcı onayları var | Lens partisi + RIP modu + mesafe + malzeme için ölçüm kanıtı taşıyan profil ve fotoğraftan otomatik ölçüm eksik |
| Renk | ICC çıkış, sRGB kaynak ve ayrı beyaz maske var | 16-bit uçtan uca işleme, nesneye özel beyaz ve yarı saydam kaynaklarda gelişmiş alfa/renk yönetimi eksik |
| Çözünürlük / büyük baskı | Şerit akışlı TIFF ve sınırlı kaynak önbelleği var | Bağımsız X/Y PPI, çoklu panel ve profesyonel PSD/PSB katman aktarımı eksik |
| Önizleme | Zaman/kamera, kanal ve varsayımsal karışım önizlemesi var | Gerçek optik lens PSF/MTF, izleyici konumu, pupil açıklığı ve RIP davranışını içeren doğrulanmış simülatör yok |
| Animasyon | FrameSet, RIFE, optik akış, morph, flip/sekans/zoom var | Yeni motor eklemek 3D portredeki optik netlik sorununu tek başına çözmez; hareket belirsizliği devam eder |
| Fiziksel kabul | Önceki fotoğraf/video gözlemleri var | Aynı dosyanın gerçek lens altında iki göz ve farklı açılarla, aynı baskı koşulunda değerlendirilmesi gerekli |

SAM2, LaMa, bağlama duyarlı katmanlı derinlik tamamlama ve MoGe alternatifleri incelendi; bu turda bu motorlar kurulmuş veya kalite üstünlükleri bu portrede ölçülmüş değildir. Donanımda AMD Radeon Graphics görüldü; mevcut derinlik hattı CPU kullanıyor. CUDA odaklı en yeni modelin doğrudan kurulması bu ortamda doğrulanmış bir çözüm değildir. Ağır bağımlılıkları mevcut çalışan ortama topluca eklemek yerine, model revizyonu/lisansı ve CPU/AMD uyumu sabitlenmiş ayrı karşılaştırma gerekir.

Öncelik sırası: (1) gerçek kanal ayrımı ve baskı profilini ölçmek, (2) nesne bazlı derinlik/matting ve tutarlı arka plan tamamlama, (3) ölçülmüş optikle derinlik optimizasyonu, (4) 16-bit, X/Y PPI, PSD/PSB ve panel iş akışı. Bu gelişmiş kalemler tamamlandı diye işaretlenmemiştir.

## Doğrulama ve koruma

- Değişiklik öncesi 29 test geçti. İlk bütünleşik doğrulamada 37 test ve JavaScript sözdizimi kontrolü geçti. Son öz denetimde bulunan iki sınır durumu düzeltildikten sonra ilgili 9 testin tamamı geçti (toplam test sayısı artık 38; son iki düzeltme sonrası tüm paket gereksiz yere yeniden çalıştırılmadı).
- Gerçek portrede 12 Blender görünüşü, boş alan denetimi ve 1200 × 1986 piksellik alan örneklemeli QA TIFF üretildi. Kaydedilen TIFF'ten kanal örnekleri doğrulandı.
- Bu küçük TIFF üretim baskısı değildir; 768 piksel render yalnız yazılım doğrulaması için kullanıldı.
- Kaynak fotoğraf ve derinlik dosyalarının SHA-256 değerleri önce/sonra aynı.
- Kod ve uygulama durumu değiştirmeden önce hash doğrulamalı yedeklendi. `sources/`, modeller ve geçmiş çıktılar korunmuştur.
- Tarayıcıda Dengeli modun açılması, ilgili çarpanların devre dışı kalması, 12 kanal önerisi ve ölçü değişince pitch onayının kaldırılması doğrulandı.
- Son düzeltmelerden sonra aktif iş olmadığı kontrol edilerek uygulama normal kapanışla yeniden başlatıldı. API yanıtı doğrulandı; 6 görsel, 99 iş, 13 profil ve durum dosyasının SHA-256 değeri değişmedi. Kanıt: `final-restart-verification.json`. Ayrı test sunucusu kapatıldı.

Kanıt klasörü: `outputs/quality-upgrade-20261009-205235/`. Son karşılaştırma: `portrait-check-v2/comparison.json`. `portrait-check/` ilk deneydir; son değerlendirme için v2 kullanılır.

## İncelenen kaynaklar

15 kaynak dosyası `docs/research/2026-10-09/` altında, indirme adresi ve SHA-256 ile `sources.json` içinde kayıtlıdır. PDF'lerin ilgili metinleri ve şekilleri incelendi; yerel arşiv bütün belgelerin her satırına ilişkin bir doğrulama iddiası değildir.

1. [Triaxes: ön ve arka paralaks](https://triaxes.com/docs/3dmk11-en/26Backgroundandforegroundparalla.html) — bağımsız ön/arka bütçe yaklaşımı.
2. [Triaxes: katmanlı 2D–3D dönüşüm](https://triaxes.com/docs/3dmk10/3DMasterKit-en/432Dto3Dconversion.html) — açılan arka planın ayrı katmanlarla tamamlanması.
3. [Triaxes Legend](https://triaxes.com/legend/) — doğrudan lense baskı ve profesyonel üretim iş akışı.
4. [Triaxes pitch kılavuzu](https://triaxes.com/downloads/Pitch-test-en.pdf) — aynı baskı koşulunda pitch sınama.
5. [Imagiam özellikleri](https://www.imagiam.com/lenticular-software/features) — ICC, 16-bit, X/Y çözünürlük, katman ve büyük dosya karşılaştırması.
6. [3DZ Suite](https://www.lenticularsoftware.de/onlinetools/index.htm) ve [pitch kılavuzu](https://www.lenticularsoftware.de/onlinetools/Pitchtest/anleitung.htm) — optik/mekanik pitch ayrımı, hizalama ve alt piksel işleme.
7. [HumanEyes üretici/distribütör özeti](https://dplenticular.com/lenticular-software/software-applications/human-eyes/) — içerikten baskıya bütünleşik iş akışı; ürünün güncel kurulumu sınanmadı.
8. [Tompkin vd., Content-adaptive Lenticular Prints, 2013](https://dspace.mit.edu/entities/publication/c187ad9e-fc13-49ce-bc82-46b01a638f13) — uzamsal/açısal örnekleme ödünleşimi. Yöntem özel lens dizisi de değiştirir; mevcut 50 LPI levhada yalnız kod ekleyerek eşdeğer sonuç alınacağı varsayılmadı.
9. [Hwang vd., 3D Display Calibration by Visual Pattern Analysis](https://arxiv.org/abs/1606.07166) — pitch, eğim, aralık ve fazın görüntülerden kestirimi. Ekran modelinin baskıya doğrudan doğrulanmış aktarımı yapılmadı.
10. [Shih vd., 3D Photography Using Context-aware Layered Depth Inpainting, 2020](https://shihmengli.github.io/3D-Photo-Inpainting/) — ortak katmanlı renk/derinlik tamamlama; gizli içerik tahmindir.
11. [Depth Anything 3](https://github.com/ByteDance-Seed/Depth-Anything-3) — mevcut yerel model ailesi ve geometrik tahmin kapsamı.
12. [Microsoft MoGe](https://github.com/microsoft/MoGe) — alternatif geometri ve normal haritaları; yerel karşılaştırma yapılmadı.
13. [SAM2](https://github.com/facebookresearch/sam2) — anlamsal nesne seçimi adayı; matting ile aynı işlem değildir.
14. [LaMa](https://github.com/advimman/lama) — büyük maske doldurma adayı; çoklu görünüş tutarlılığı ayrıca sağlanmalıdır.

Üreticilerin pazarlama beyanları bağımsız karşılaştırma sonucu olarak kullanılmadı. Kaynaklardan yöntem ve kabul ölçütü çıkarıldı; kapalı ticari algoritmaların bire bir kopyalandığı iddia edilmez.

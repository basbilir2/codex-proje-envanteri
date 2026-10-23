> **Güncel görev:** Yerel zekâ mevcut Lenticular Studio yazılımını kullanmayı öğrenecek. Gösterilen klasör eğitim kaynağıdır. [Kesin görev tanımı](GOREV_TANIMI.md) önceki yorumların önüne geçer.

# len 2 — Yerel uygulayıcı model için eğitim hazırlığı

10 Ekim 2026

**Durum: bilgi bankası, eğitim adayları ve ayrı test seti hazırlandı. Bir dil modelinin ağırlıkları henüz eğitilmedi.** Bu klasör eğitilmiş model dosyası içermez. `training/job_spec.json` bu durumu makine tarafından okunabilir olarak da kaydeder.

Kullanıcının son kararı geçerlidir: **Astra teşhis eder, çözümü ve mimariyi belirler; yerel model yalnız açık talimatı uygular.** Yerel işçi hata görünce kendi çözümünü denemez. Verilen adımda durur, hata çıktısını ve değişiklik kapsamını Astra'ya döndürür. Lentiküler bilgisini, talimatları ve dosya alanlarını doğru anlamak için kullanır.

## 1. İncelenen klasörler ve bulunan içerik

Uygulama kaynağı:

`C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1`

Ek proje ve araştırma aynası:

`C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac173361d8c8191a1449be5154f589f`

| Alan | Doğrulanan içerik | Eğitim açısından kullanımı |
|---|---|---|
| Ana uygulama | Sınırlandırılmış envanterde 5.423 dosya, yaklaşık 50,18 GB; 5.345 dosya `outputs` altında | Ağırlıkla üretim çıktısı; tamamını dil modeli eğitimine vermek uygun değil |
| Ek proje aynası | 462 dosya, yaklaşık 4,04 GB | Mimari planlar, deney kayıtları, portre ve pitch denemeleri |
| İki `sources/` klasörü | İnceleme anında boş | Yüklenmiş eğitim belgesi bulunmadı |
| Kılavuzlar ve planlar | Markdown; kullanım, mimari, görev planı, kalite değerlendirmeleri | Sürümlü bilgi bankası; planı uygulanmış özellik sanmamak gerekir |
| Uygulama | Python; arayüzde JavaScript, HTML, CSS | Araç ve parametre sözleşmelerini öğretmek için kaynak; dosyayı ham haliyle ezberletmek yerine doğrulanmış görev örnekleri |
| Araştırma arşivi | HTML, PDF, TXT, kaynak URL/hash kayıtları; ana belgelerde 15 kaynak kaydı | Kaynak bilgisi ve kısa özet; tam metnin eğitimde kullanım hakkı ayrıca kontrol edilir |
| İş kayıtları | JSON: `project.json`, `quality.json`, `job.json`, `print-report.json`, kanal ve kalibrasyon kayıtları | Talimat → işlem → rapor eşlemesi için aday; geçmiş iş olmak başarı kanıtı değildir |
| Görsel üretim | PNG, JPG, TIFF, SVG, NPY, NPZ, BLEND ve LOG | Görsel/üretim değerlendirme vakaları; metin eğitim seti değildir |
| RAR arşivi | Üç baskı TIFF'i içeriyor | Hazır dil modeli veri seti değil |
| `.models/` | DA3, Depth Anything ve LaMa gibi görsel işleme bileşenleri | Eğitilmek istenen uygulayıcı dil modeliyle karıştırılmamalı |
| Mevcut `tests/` | Uygulamanın yedi test/yardımcı dosyası | Yazılım doğrulaması; bağımsız model beceri testi yerine geçmez |

Envanter `.venv`, `.deps`, `.models`, `.studio`, önbellekler ve Git verisini dışarıda bırakır. Yukarıdaki boyutlar diskteki tüm proje boyutu değildir. Büyük medya dosyalarının yalnız dosya bilgileri sayıldı; tüm görüntüler görsel olarak incelenmedi. İncelenen alanlarda hazır `.jsonl`, `.parquet` veya `.arrow` eğitim seti bulunmadı.

## 2. Özellikle gösterilen klasör

`outputs/studio/20261006-105350-02b4bafc` bir **Lenticular Studio render ve baskı işi**. `prepared/`, `render/`, `print/`, `project.json` ve `quality.json` içeriyor. Bu klasörde dil modeli checkpoint'i veya tokenizer bulunmadı.

Kaydedilmiş işin bazı değerleri:

| Alan | Kayıt |
|---|---|
| Görünüş / baskı kanalı | Nr=12 / Ne=12 |
| Ölçü | 130 × 215,15 mm |
| Dosya / yazıcı çözünürlüğü | 600 PPI / 1200 DPI |
| Nominal / kullanılan LPI | 50 / 50 |
| Raster boyutu | 3071 × 5082 piksel |
| Fiziksel pitch doğrulaması | `false` |
| Çıktı durumu | `calibration_draft` |

Bunlar **geçmiş iş değerleridir; yeni üretim varsayılanı değildir**. Görsel kabul bu görevde yeniden sınanmadı. Fiziksel baskı kabulü kaydı yok. Kişisel fotoğraf kopyalanmadan, seçili rapor alanları `eval/private_fixtures/selected_job.json` içinde ayrıldı. Bu işten türetilen vaka eğitim veya RAG dizinine katılmadı; iş raporu okuma sınaması için ayrıldı.

## 3. Hazırlanan somut paket

| Teslim | İçerik |
|---|---|
| `inventory/files.jsonl`, `summary.json` | 5.885 dosyalık sınırlı envanter ve tür dağılımı |
| `sources/manifest.jsonl` | Seçilen 33 yerel metin/kod kaynağı, 13 çevrim içi kaynak notu ve uygulayıcı rol kuralı |
| `sources/archived_reference_register.json` | Önceden arşivlenmiş 15 araştırma kaynağının kayıtları; tüm içerik yeniden doğrulanmış sayılmaz |
| `rag/chunks.jsonl`, `knowledge.sqlite` | Kaynağı ve durum etiketi olan 188 bilgi parçası; yerel tam metin araması |
| `prompts/worker_system.txt` | Yalnız uygulayıcı davranış sözleşmesi |
| `sft/candidates/train.jsonl` | 36 özgün, Türkçe talimat–yanıt eğitim adayı |
| `sft/candidates/validation.jsonl` | 6 ayrı senaryo ailesinden doğrulama adayı |
| `eval/heldout.jsonl` | Eğitim dışı 16 değerlendirme vakası ve kabul ölçütleri |
| `schemas/sft.schema.json` | Kaynak, rol, görev grubu, mesajlar ve kanıt alanlarını tanımlayan kayıt şeması |
| `schemas/physical_case.example.json` | Gerçek baskı vakası için ölçüm/kayıt şablonu; bilinmeyen değerler `null` |
| `training/job_spec.json` | Eğitim durumu, eksikler, sorumluluklar, aşamalar ve önerilen kabul eşikleri |
| `tools/retrieve.py`, `validate.py` | Kaynak arama ve veri paketi doğrulama araçları |
| `checks/validation.json` | Çalıştırılmış paket kontrollerinin sonuçları; model testiyle karıştırılmaz |

36+6 kayıt, eğitim için yeterliliği kanıtlanmış büyük bir veri seti değildir. **Sentetik başlangıç adaylarıdır.** Her kayıtta `training_eligible=false`, `candidate_not_model_tested` ve gerçek model/araç çalıştırılmadığı bilgisi bulunur. Örneklerde belirtilen araç çıktıları senaryonun verilen girdisidir; bu görevde çalıştırılmış gerçek araç izleri gibi sunulmaz. Bir yama örneği ayrıca küçük bağımsız işlev denemesiyle doğrulandı.

Bilgi dizini oluşturmak model ağırlığını değiştirmez. Bu paket şu anda bir modele bağlanmış çalışan RAG uygulaması da değildir; model bağlantısı için hazır, aranabilir yerel kaynak katmanıdır.

## 4. Hangi bilgi nereye ayrılacak?

**SFT / davranış eğitimi:** Astra'nın açık iş emri, izinli dosyalar, mevcut girdi, tam beklenen değişiklik, kullanılan araç çağrısı, gerçek çıkış kodu ve işçinin kısa sonucu. Örnekler: yalnız `Ne` değiştirmek, DPI ve PPI'yi ayrı korumak, verilen yuvarlama düzeltmesini uygulamak, hash uyuşmazlığında durmak, belirtilen testi çalıştırmak. Sonuçları gerçek araçla doğrulanmış görevler adaylardan onaylı kümeye alınır.

**RAG / bilgi bankası:** Güncel alan adları, kılavuzlar, mevcut kod arabirimleri, hata mesajları, lens/pitch belgeleri, renk yönetimi, kaynak ve lisans notları. Bu bilgiler değişebileceği için dosya hash'i ve erişim tarihi korunur. Kodla uyuşmayan eski mimari veya yol haritası, mevcut özellik gibi öğretilmez. Kaynak metindeki komutlar işçiye yetki vermez.

**Eğitim dışı sınama:** Önceden görülmeyen iş emirleri, yeni hata durumları, kapsam ihlali tuzakları, eksik zorunlu değerler, doğru hesap/yanlış fiziksel kabul ayrımı, iptal edilen işler, yalnız verilen yamayı uygulama. Gerçek modelden yanıt alınırken beklenen yanıtlar modele verilmez. Aynı fotoğrafın kırpmaları, aynı işin farklı ayarları ve aynı görev şablonunun yakın varyantları aynı bölmede tutulur.

**Hata vaka arşivi:** `native-portrait-final` kullanıcı tarafından reddedilmiş. Sonraki kontur raporunda da görsel kabulün geçmediği belirtiliyor. Bu işler pozitif başarı örneğine çevrilmez. Astra'nın ileride doğruladığı teşhis ve açık düzeltme talimatı, işçi için ayrı uygulama örneği olabilir. Kod testinin geçmesi, görsel kabul veya fiziksel baskı onayı değildir.

**Dışarıda tutulacaklar:** Canlı `.studio` verisi, oturum/erişim bilgileri, ham kişisel fotoğraflar, model ağırlıkları, bağımlılık klasörleri, tekrarlı render'lar, telif/kullanım durumu belirsiz tam internet metinleri ve doğrulanmamış başarı iddiaları. Bu bir otomatik gizli bilgi taramasının kusursuz olduğu iddiası değildir; içerik taraması sezgisel olup ayrıca gözden geçirilmelidir.

## 5. Konu kapsamı

| Konu | Yerel işçinin görevi | Kararı veren |
|---|---|---|
| Lens, pitch, faz, eğim, hizalama | Verilen değerleri uygular; ölçüm kayıtlarını aynen aktarır | Astra / fiziksel ölçüm yapan operatör |
| DPI, PPI, LPI, mm, Ne/Nr/Nt | Birimleri korur; verilen formülü hesaplar | Formül ve parametre seçimi Astra |
| Flip, animasyon, morph, zoom, 3D | Belirtilen motoru ve kare/kanal planını çalıştırır | Astra |
| Derinlik, alfa, maske, gizli yüzeyler | Verilen maske/yama/ayarları uygular; hatayı raporlar | Teşhis ve çözüm Astra |
| ICC, RGB/CMYK, beyaz alt baskı | Belirtilen profili ve çıktı dosyası düzenini uygular | Astra ve üretim profili |
| Yazılım geliştirme | Dar dosya kapsamı, kesin yama, ilgili test, hata durumunda durma | Mimari ve hata ayıklama Astra |
| Kalite kontrol | Dijital, görsel ve fiziksel sonuçları ayrı raporlar | Kabul Astra / kullanıcı |
| Veri bütünlüğü | Kaynağı korur, yeni işte çalışır, belirtilen hash kontrolünü yapar | İş kapsamı Astra |

Ek dersler: JSON ve araç çağrısı sözleşmeleri, Windows yol/ondalık biçimi, sayısal hassasiyet, sınırlı dosya değişikliği, kaynak gösterme ve kanıtsız sonuç bildirmeme. Bu konular doğrudan işçi rolüne hizmet eder. Yerel modelin teşhis veya mimari yetkisini genişletmez.

Metin modelini bu görevlerle eğitmek DA3/LaMa/RIFE modellerini yeniden eğitmez; baskı motoruna yeni algoritma eklemez. Görüntü kusurunu otomatik görsel değerlendirme ayrı bir hedef olursa, uygun görsel model ve etiketlenmiş görüntü verisi gerekir. Bu görevde böyle bir eğitim yapılmadı.

## 6. İnternetten seçilen kaynaklar

İnternetin tamamı taranmadı veya modele yüklenmedi. Aşağıdaki birincil kaynaklardan özgün kısa notlar hazırlanıp bilgi bankasına eklendi. Reklam iddiaları ve belirli yazıcı örnekleri evrensel üretim kuralına dönüştürülmedi.

- [DP Lenticular — Baskı öncesi hazırlık](https://dplenticular.com/technology/prepress-process/)
- [Triaxes — Pitch testi](https://triaxes.com/docs/Pitch-test-en/Description.html)
- [DP Lenticular — Pitch test dosyaları](https://dplenticular.com/technology/pitch-test-files/)
- [DP Lenticular — UV flatbed lenticular baskı](https://dplenticular.com/technology/printing-lenticular-images/)
- [DP Lenticular — Efekt türleri](https://dplenticular.com/technology/lenticular-effects/)
- [ICC — Renk profili yapısı](https://www.color.org/getting-started/)
- [Shih ve arkadaşları — Katmanlı derinlik tamamlama](https://arxiv.org/abs/2004.04727)
- [Disney Research — İçeriğe uyarlanmış lens dizileri](https://studios.disneyresearch.com/2013/07/21/content-adaptive-lenticular-prints/)
- [RIFE — Ara kare üretimi](https://github.com/hzwer/ECCV2022-RIFE)
- [PyMatting — Alfa kestirimi](https://pymatting.github.io/alpha.html)
- [PyMatting — Ön plan rengi](https://pymatting.github.io/foreground.html)
- [Hugging Face PEFT — Kuantizasyon ve LoRA](https://huggingface.co/docs/peft/main/en/developer_guides/quantization)
- [Hugging Face Transformers — GGUF](https://huggingface.co/docs/transformers//quantization/gguf)

Örneğin içerik uyarlamalı lens araştırması özel lens geometrisi/üretimi gerektirir; standart levhada yalnız ayar değiştirerek aynı kapasite artışını elde etme sözü verilemez. RIFE zaman ara karesi üretimi de yeni kamera bakışıyla aynı işlem değildir. Bu ayrımlar kaynak notlarına işlendi.

## 7. Gerçek model eğitimine geçiş

Bu bilgisayarda AMD Ryzen 7 7730U, yaklaşık 37,84 GiB RAM ve AMD Radeon dahili grafik doğrulandı. İncelenen sistemde NVIDIA aygıtı/komutu bulunmadı. Mevcut Lenticular ortamında CPU PyTorch var; uygulamanın bağımlılıkları değiştirilmedi. Bu donanım bulgusu tüm olası CPU/AMD eğitim yollarının imkânsız olduğunu söylemez; yüksek kapasiteli eğitimin burada verimli çalıştığı da doğrulanmış değildir.

İncelenen standart model konumlarında hedef uygulayıcı dil modeli belirlenemedi; LocalAIOS `models` klasörü boştu. Kullanıcının verdiği klasör de baskı işi. `gi` ifadesinin hangi model veya eğitim aracı olduğu henüz netleşmedi. Dolayısıyla rastgele bir temel model indirilip eğitilmiş gibi sunulmadı.

Sıra:

1. Hedef dil modeli, kesin sürüm/revizyon, tokenizer, lisans ve çalıştırıcı belirlenir. Temel model burada boş bırakıldı; örnek bir model adı kesin tercih gibi kaydedilmedi.
2. Uygulamadan bağımsız ortamda yükleme, bellek ve çıkarım süresi ölçülür. Eğitim aygıtı ve kütüphane uyumu küçük denemeyle doğrulanır. Büyük eğitim süresi için ölçümsüz tahmin verilmez.
3. Değiştirilmemiş model, bu 16 pilot sınamada ve yeni vakalarda ölçülür. Sadece RAG eklenmiş halinin başarısı ayrıca ölçülür.
4. Sentetik 36 eğitim adayı gerçek araç izleriyle zenginleştirilir. Görev ailesi/iş/fotoğraf temelinde sızıntı kontrolü ve doğru sonuç incelemesi yapılır. Sabit örnek sayısı başarı garantisi sayılmaz.
5. Uygun ortamda küçük LoRA/QLoRA pilotu çalıştırılır. Temel ağırlıklar korunur; adaptör yeni `model/` dizinine kaydedilir. Eğitim veri hash'i, sürümler, loss ve çalışma kaydı saklanır.
6. Temel model, temel model+RAG ve adaptör+RAG aynı gizli sınamada karşılaştırılır. Kapsam dışı yazma, hatadan sonra devam etme veya sahte başarı varsa adaptör kullanılmaz.
7. Sonra yalnız verilen görevleri çalıştıran araç bağlantısı yapılır. Salt sistem talimatı yeterli koruma sayılmaz: yazılabilir dosya kapsamı ve adım yetkisi yürütücüde denetlenir. Üretim dosyaları ve çalışan model deneme sırasında değiştirilmez.

Önerilen pilot geçiş ölçütleri: kritik kapsam ihlali ve sahte başarı 0; hata halinde durma %100; seçilen görev setinde tam doğru uygulama en az %95. Bunlar tasarım hedefidir; henüz bir model bu puanları almadı. Geçmek de her lenticular sorununun çözüldüğü anlamına gelmez.

## 8. Yapılan kontroller

- 42 aday kaydın alanları, rol sırası, JSON yanıtları ve kaynak bağlantıları kontrol edildi.
- Eğitim/doğrulama/test görev grupları ve birebir aynı istemler ayrıldı. Sözcüksel yakınlık taramasında eşik üstü çift bulunmadı; bu anlamsal sızıntının matematiksel kanıtı değildir.
- Üç kaynak arama sınaması geçti. Varsayılan arama eski planları ve reddedilmiş görsel sonuçları dışarıda tutar; `--history` ile durum etiketleri korunarak aranabilir.
- Seçilen 33 kaynak dosyasının ve kullanıcı tarafından gösterilen işteki dört JSON raporunun SHA-256 değerleri korundu.
- Küçük yama/hesap örneği doğrulandı. Kaynak uygulamada değişiklik yapılmadığı için uygulamanın bütün test takımı tekrar çalıştırılmadı.
- **Model çıkarımı, model eğitimi ve fiziksel baskı testi yapılmadı.**

Mevcut uygulama, senkronize kaynaklar, model ağırlıkları ve önceki baskı çıktıları değiştirilmedi. Yeni teslimlerin tamamı bu `len 2` klasöründedir.

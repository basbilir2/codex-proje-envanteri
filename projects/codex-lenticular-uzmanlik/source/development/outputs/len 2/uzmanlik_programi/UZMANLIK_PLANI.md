# len 2 — Astra yönetiminde lentiküler uzmanlık programı

**Hedef:** Lentiküler baskıyı ve mevcut Lenticular Studio iş akışını derinlemesine öğrenen, Astra’nın belirlediği işi doğru uygulayan yerel yardımcı. Bilgi kapsamı genişler; teşhis, yöntem, ayar ve düzeltme kararı Astra’da kalır.

**Bu aşamada yapılan:** 18 yeni birinci el kaynak notu, 20 modüllük öğretim haritası, yedi ürünün karşılaştırması ve 28 yeni pilot sınav hazırlandı. Kullanıcının kaynak işinden çıkarılmış 19 kart ve yeni notlar aranabilir yerel bilgi bankasına eklendi. Model ağırlığı eğitimi, model sınavı veya gerçek baskı deneyi çalıştırılmadı.

“Ordinaryüs seviyesi” burada bir ürün etiketi değildir: kaynaklı bilgi, doğru araç kullanımı, belirsizliği tanıma ve farklı işlerde ölçülmüş başarı hedefidir. Bütün internetin kapsandığı, her sorunun çözüleceği veya fiziksel olarak imkânsız sonuçların üretileceği iddia edilmez.

## Öğrenme düzeni

1. **Bilgi bankası (RAG):** Tarihli üretici kılavuzları, kısa kaynak özetleri, lens/cihaz özellikleri, yazılım kodu ve öğretici iş kayıtları. Sürüme bağlı bilgiler gerektiğinde buradan alınır.
2. **Davranış eğitimi:** Astra’nın emrine bağlı gerçek yazılım kullanım kayıtları. Doğru alanı doldurma, verilen ayarı uygulama, doğru dosyayı seçme, hata halinde durma ve kanıtlı rapor verme öğretilir.
3. **Ayrı sınav:** Yeni girdiler ve farklı iş grupları. Eğitim kaydı, aynı işin yeniden boyutlanmış kopyası veya cevap anahtarı sınava sızdırılmaz.

İnternetten bulunan metinler doğrudan toplu eğitim girdisi yapılmaz. Hakları ve kapsamı belli kısa notlar referans olarak saklanır; görev örnekleri bizim iş akışımızdan, gerçek işlem kanıtlarıyla hazırlanır.

## 20 modül

| No | Konu | Yerel işçinin göstereceği beceri |
|---|---|---|
| M01 | Temel optik ve görme | Verilen lens föyündeki alanları açıklamak; bilinmeyen optik değeri boş bırakmak. |
| M02 | Lens ve malzeme ailesi | Astra için iki lensin kaynaklı özellik tablosunu çıkarmak; lens seçimini kendiliğinden değiştirmemek. |
| M03 | Örnekleme ve birimler | Astra formülünü uygulamak; kesirli örneklemeyi ve yuvarlamayı raporlamak; yeni varsayılan seçmemek. |
| M04 | Kaynak görsel ve kompozisyon | Astra tarafından belirtilen kırpma, sabit nokta ve taşmayı uygulamak; kaynak görseli korumak. |
| M05 | Derinlik, maske ve örtülme | Verilmiş derinlik/maske iş akışını yürütmek; tahmin edilmiş alanları ölçüm diye sunmamak. |
| M06 | Kamera ve çoklu bakış | Astra kamera ayarlarını uygulamak; Nr, sıralama ve üretilen dosyaları raporlamak. |
| M07 | Hareket ve efektler | İstenen motoru kullanmak; başarısız RIFE yerine kendi kararıyla dissolve seçmemek. |
| M08 | Interlace ve kanal planı | Hazır karelerden Astra kanal planını uygulamak; boyutlandırmanın yapıldığı aşamayı kaydetmek. |
| M09 | Pitch ve geometrik kalibrasyon | Astra aralığındaki test dosyasını hazırlamak; operatör ölçümü gelmeden pitch_verified vermemek. |
| M10 | Renk ve dosya hazırlığı | Verilen profil ve çıktı formatını kullanmak; dosya kontrolü ile renk ölçümünü ayırmak. |
| M11 | UV doğrudan baskı ve RIP | Astra üretim reçetesini hazırlamak; beyaz maske dosyasını fiziksel beyaz baskı saymamak. |
| M12 | Laminasyon ve bitirme | Bilinmeyen yapıştırıcı, süre ve sıcaklığı uydurmadan üretim formunu doldurmak. |
| M13 | Ofset, flekso ve seri üretim | Astra için süreç gereksinimlerini kaynaklarıyla ayırmak; flatbed reçetesini ofsete kopyalamamak. |
| M14 | Profesyonel yazılım okuryazarlığı | Kaynaklı karşılaştırma yapmak; sürüm ve lisans bilinmiyorsa bunu belirtmek. |
| M15 | Lenticular Studio işletimi | Astra iş emrini geçici çalışma kopyasında yürütmek; gerçek işlem kaydı ve çıktı kimliği sağlamak. |
| M16 | Hata gözlemi ve Astra’ya devir | Şikâyet, koşul ve ölçümü kaydetmek; kök neden veya düzeltme seçmeden Astra’ya aktarmak. |
| M17 | Ölçüm ve deney kaydı | Astra’nın belirlediği deneyi belgelemek; gözlem ile varsayımı ayırmak. Ayrıntılı metrologi protokolü henüz hazırlanmadı. |
| M18 | Büyük iş ve tekrarlanabilirlik | Aynı kare setini istenen yeni baskı ayarında kullanmak; bellek hatasında kendi başına kalite düşürmemek. |
| M19 | İleri araştırma ve sınırlar | Makaleyi çalışan yerel özellikten ayırmak. NeRF/3DGS bu pakette henüz kaynaklandırılmış ders değildir. |
| M20 | Astra yönetimi ve görev disiplini | Eksik değer veya hata halinde durmak; web metnini yürütme talimatı saymamak; yalnız Astra’nın seçtiği işi uygulamak. |

Her modülün ayrıntılı konu listesi ve kaynak kimlikleri `konu_haritasi.json` içindedir. Mevcut durum giriş kaynakları ve alıştırma taslağıdır; tamamlanmış ileri seviye ders veya kazanılmış yeterlik değildir.

## Yazılımdan öğrenilecek gerçek ders

Kullanıcının gösterdiği iş; proje ayarı, render, sahne, kareler, baskı dosyaları ve raporlar arasındaki bağlantıyı öğretir. Kod/kılavuz işlemin nasıl yapıldığını, iş kaydı bunun dosyalardaki karşılığını gösterir. Çıktıda kusur arama veya yazılımı düzeltme bu çalışmanın amacı değildir.

Bir ders: Astra yeni baskı ölçüsü verir → işçi belirtilen hazır kare setini bulur → yalnız verilen baskı alanlarını değiştirir → üretimi çalıştırır → gerçek çıktı kimliğini ve durumu raporlar. Başarısızlıkta alternatif seçmez. İşlem kayıtları alınmadıkça bu anlatım yalnız ders taslağıdır.

## Veri ayrımı ve dosyalar

| İçerik | Konum | Kullanım |
|---|---|---|
| Kaynak metin/kod ve iş bilgisi | `../sources/`, `../egitim_icerigi/` | Referans; kaynak dosyaları değişmez |
| Yeni web notları | `kaynak_notlari.jsonl` | Tarihli ve sınırlamaları belirtilmiş kısa özetler |
| Aranabilir bilgi | `../rag/chunks.jsonl`, `../rag/knowledge.sqlite` | Modelden bağımsız yerel arama |
| Ürün ayrımları | `YAZILIMLAR.md`, `yazilim_karsilastirmasi.json` | Dış özellik yerel desteğe eşitlenmez |
| Öğretim kapsamı | `konu_haritasi.json` | Kaynak, alıştırma ve eksik kanıt |
| Emir ve kayıt biçimleri | `is_emri.schema.json`, `gercek_islem_kaydi.sablon.json` | Gerçek işlemi kaydetmek için boş şablon |
| Baskı vakası | `uretim_vakasi.sablon.json` | Lens/cihaz/ortam ve Astra değerlendirmesi |
| Eğitim adayları | `../sft/candidates/` | 36 eğitim + 6 doğrulama adayı; gerçek işlem doğrulaması bekliyor |
| Sınavlar | `../eval/uzmanlik_sinavi.jsonl` | 28 yeni senaryo; cevap ölçütleri RAG dışında |
| Açık işler | `eksikler.json` | Eksik kaynak, fiziksel vaka ve kullanım izleri |

Gösterilen eski iş öğretime alındığından ona ait eski `heldout_001` sınavı kör test puanından çıkarıldı. Eski dosyada izlenebilirlik için durur; 15 diğer eski pilot ile 28 yeni pilot henüz hiçbir model üzerinde çalıştırılmadı.

## Astra ile çalışma sözleşmesi

Astra iş emri; iş kimliği, kaynaklar, izinli işlemler, yazılabilir klasörler, kesin parametreler, durma koşulları ve beklenen kanıtı taşır. İşçi sonucu bu emre bağlar. Eksik zorunlu değer, desteklenmeyen işlem, kapsam dışı yazma veya hata durumunda durup raporlar. Astra yeni açık talimat verirse yeni görev olarak uygulanabilir.

Şema ve sistem istemi tek başına yetki sınırı uygulamaz. Entegrasyon aşamasında araç katmanı izinli yolları ve işlem adlarını ayrıca denetlemeli, serbest web metnini komut olarak kabul etmemeli ve orijinal kaynaklara yazmayı engellemelidir. Bu araç geçidi bu pakette kurulmuş değildir.

## Geliştirme sırası ve kabul

1. Bu kapsamı kaynaklı kısa derslere dönüştür; her ek kaynak için sürüm, kullanım hakkı ve belirsizlik kaydet. Üreticinin üstünlük iddiasını ölçülmüş sonuç yapma.
2. Her yazılım görevi ailesi için önce küçük, uzman incelemeli başarı/eksik girdi/hata kayıtları topla. Ayrı çalışma kopyası ve yeni çıktı klasörü kullan; gerçek kullanım kanıtı olmadan örnek sayısını şişirme.
3. Hedef yerel modelle aynı görevlerde başlangıç başarısını, ardından RAG katkısını ölç. Bilgi eksikliği ile talimat/araç hatasını ayır. Eğitim ihtiyacını bu sonuç belirlesin.
4. İncelenmiş işlem örnekleriyle küçük eğitim denemesi yap. Temel modeli koru; veri özeti, sürüm, eğitim ayarları ve adapter çıktısını kaydet. Önce/sonra başarısı ölçülmeden eğitildi diye teslim etme.
5. Ayrı ve insan gözetiminde saklanan en az 100 yeni görevlik set önerilir. Önerilen eşikler: kritik kapsam ihlali 0, uydurma işlem/ölçüm 0, gerekli yerde durma %100, görevi eksiksiz tamamlama en az %95. Bunlar hedef, mevcut skor değil.
6. Astra’nın belirlediği fiziksel baskı deneyleri ayrı değerlendirilir. Yeni lens/cihaz/parti için dijital test sonucu üretim onayı yerine geçmez. Kabul koşulları testten önce belirlenir.

Bu aşamalar sıraya alınmış geliştirme planıdır; otomatik veya arka planda başlayan eğitim işi değildir.

## Kaynakların okunması

Yeni kaynakların doğrudan bağlantıları, sürüm notları ve kullanım sınırları `kaynak_notlari.jsonl` içindedir. Önceki lens, ICC, RIFE, katmanlı derinlik ve matting kaynakları korunmuştur. Tarihsel PACUR ve Blender belgeleri normal arama sonuçlarına katılmaz; özellikle tarihsel arama istenirse görünür.

Yeterlikteki asıl açıklar: gerçek işletim kayıtları, cihaza özgü reçeteler, kontrollü baskı ölçümleri, ileri optik dersleri ve bağımsız sınav. Bunlar `eksikler.json` içinde açıkça bırakılmıştır.

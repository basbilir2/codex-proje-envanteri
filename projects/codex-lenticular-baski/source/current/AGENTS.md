# Lentiküler proje çalışma belleği

Bu yönergeler yalnız aktif çalışma projesi C:\Users\USER\Documents\lenticular baskı veya bu projenin bir alt klasörü olduğunda geçerlidir.

Her yeni işe başlamadan önce PROJE-OGRENME.md içindeki kısa özeti, konu dizinini ve yapılacak işle ilgili bölümleri oku. Diğer proje ve sohbetlerde bu öğrenme dosyasını yükleme veya uygulama.

Bu projedeki her geliştirme, hata düzeltmesi, üretim veya baskı geri bildirimi sonunda yeni bilgileri PROJE-OGRENME.md dosyasına kaydet. Geçerli kayıtları ve önbellekleri kullan; gereksiz tarama ve tekrar üretim yapma.

Her yeni işte önce `knowledge/snapshot.md`, `knowledge/verified-facts.json` ve varsa `knowledge/current-task.json` oku. Ardından yalnız ilgili planı/raporu oku. Klasörleri ve yazılımı baştan tarama; uzun geçmişi bağlama taşıma.

- Asıl yazılım: `C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1`. Python: aynı kökün `.venv\Scripts\python.exe`. Bu klasör üretim ve çalışma belleğidir. `sources/` daima salt okunur.
- Mevcut istekte kod geliştirme yerine mevcut motorları kullan. Çalışan yordamı yeniden yazma. Dar yardımcı gerekiyorsa `tools/` altında parametreli ve yeniden kullanılabilir olsun; her iş için farklı büyük betik kopyalama.
- Planlayıcı: `tools/lens_plan.py --lpi 75 100`. Aynı girdilerde mevcut planı döndürür. Geçerli `current-task.json` varsa hesaplamayı da tekrar çalıştırma.
- Önbelleği yalnız dosya varlığıyla kullanma. Kaynak hash'i, model/sürüm, derinlik tarifi, depth hash'i ve ilgili motor hash'lerini doğrula. Renderde ayrıca render ayarları, bütün beklenen kareler ve kalite raporu eşleşmeli. Baskı kimliğinde PPI/ölçü/LPI/Ne/faz/renk/ICC dahil olsun. Büyük TIFF'leri gereksiz yere tekrar hash'leme; dosya değişmediyse önceki doğrulamayı kullan.
- LPI veya baskı ayarı değişmesi tek başına AI derinliğini geçersiz kılmaz. Kamera açısı, düzenlenmiş derinlik veya Nr değişmesi renderi; LPI/Ne/faz/ölçü/ICC değişmesi baskı çıktısını geçersiz kılar. Yalnız etkilenen aşamayı üret.
- `execute_vd_plan.py` eski 50,20 LPI işine bağlıdır ve bazı önbellek kontrolleri yalnız dosya varlığına dayanır. Yeni plan için körlemesine çalıştırma; mevcut yordamları doğru plan/manifest ile kullan.
- Nr kamera görüşü, Ne baskı kanalı, Nt zaman karesidir. Lens LPI, dosya PPI ve yazıcı DPI ayrı değerlerdir. İki raster piksel/kanal başlangıç kuralıdır; optik kapasiteyi veya lens açısını kanıtlamaz. Ölçülmemiş `pitch_verified`, `raster_ppi_verified`, `lens_angle_verified` false kalır.
- Üç güç varyantında kaynak, burun referansı ve ortak derinlik aynı olsun. Farklı LPI sayfaları ayrı lens ister. Şerit fazı, ICC ve %100 baskı ölçeği korunmalı. Temiz önizleme doğrudan kamera karelerinden yapılmalı.
- Her sonuçta `planned`, `rendered`, `verified_digital`, `verified_physical` durumlarını ayrı kaydet. Rapor yoksa tamamlandı deme. Görsel/teknik sorun varsa aynı ayarlarla tekrar çalıştırma; kısa kanıt ve sonraki tek adımı sun.

## İş sonunda kayıt

`knowledge/snapshot.md` kısa kalsın: amaç, tamamlanan, değişen dosyalar, sorun, sonraki adım. İş kimliği, input/parametre hash'leri, kullanılan plan, çıktı yolları ve kontrol sonuçları için `knowledge/runs/<run-id>.json` yaz. Böylece başarılı çıktılar sonraki işte bulunur.

Bir hatayı düzelttiğinde `knowledge/lessons.jsonl` dosyasına neden, dar çözüm, kanıt yolu ve doğrulama durumu içeren bir kayıt ekle; aynı dersi tekrar ekleme. Denenmemiş tahmini doğrulanmış kurala yükseltme. Kullanıcının gerçek baskı gözlemini `feedback-template.json` şemasıyla ayrı kaydet; tek gözlemden bütün lenslere varsayılan değiştirme.

Bu yapı proje deneyimini ve yordamlarını biriktirir. Model ağırlıklarını eğitmez; kaynak taramasını tamamen yasaklamaz. Kayıtla dosya çelişirse yalnız çelişen girdiyi incele ve kaydı kanıtla güncelle.

# TrendyBrander Proje Durumu

## Yetkili nihai yerel durum - 2026-08-02

Bu bolum, dosyanin altindaki tum tarihsel sayac ve durum notlarindan daha yenidir.

- Sonuc: `LOCAL_PRE_CREDENTIAL_READY`; `tests/results/production-readiness-report.json` icinde **40/40 PASS**.
- Sekiz deterministik pakette toplam **197 test PASS**: runtime 61, guvenlik 80, disk 5, scheduler/worker 5, worker hatti 20, orkestrasyon 11, servis yetkisi 7, hesap/onay baglama 8.
- Gercek model, dis servis ve yayin cagrisi yapilmadi; butun n8n workflow'lari pasif ve mevcut `01 - Ajans Ana Akis` korundu.
- Model kullanimi eksik veya gecersizse sifir maliyet yazilmaz: tam gorev butcesi rezerve edilir ve islem kapali-guvenli sonlanir. Gercek giris/cikis tokenlari sert limitleri asarsa sonuc kabul edilmez.
- Model aktivasyonu, resmi HTTPS fiyat kaynagi ile dogrulanmis ve imzalanmis fiyat/billing kaydi olmadan acilmaz.
- Bagimsiz denetim `VETO` veya `HUMAN_REVIEW` verirse, bagimsizlik yoksa, risk yuksek/kritikse ya da guven esigi saglanmazsa onay paketi olusmaz; gorev bloklanir.
- Bagimsizlik model beyanindan alinmaz: runtime, Ordinaryus ve denetci icin kaydedilen gercek saglayici/model ailesini karsilastirir; ayni saglayici veya aile kesinlikle bagimsiz sayilmaz.
- Pasif `ProdModelAdapter18A` workflow'u token kullanim metadatasini zorunlu tutacak sekilde guncellendi; veritabani `quick_check=ok`, aktif workflow sayisi sifir.
- Token mimarisi tum gecmisi tekrar gondermez. On gorev paketi secilmis marka ozeti, ilgili hafiza dilimi ve gerekli son ciktilarla sert butce altinda dogrulandi.
- Altmis kompakt ve altmis tam baglamli gercek golge kosusu, credential ve kullanici onayi olmadan yapilmaz; worker ve scheduler bu nedenle bilerek `setup_required` durumundadir.
- Yerel dosya/runtime katmani tamamdir. Kalanlar yalniz kullanici veya harici kanit kapilaridir: onay parolasi, Gemini/Header Auth ve hedef hesap credentiallari, gercek golge kalite kabulu ve farkli fiziksel ortamda bagimsiz geri-yukleme/acilis provasi.

Asagidaki bolumler tarihsel kurulum kaydidir; buradaki nihai durum onlara gore yetkilidir.

## Yetkili son durum — 2026-08-02

Bu bölüm aşağıdaki tarihsel aşama notlarından daha yenidir ve mevcut durumu temsil eder.

- Durum: `LOCAL_PRE_CREDENTIAL_READY`.
- Nihai yerel kabul: `tests/results/production-readiness-report.json` — **37/37 PASS**.
- Yerel servisler: n8n, Ajans Merkezi, transactional runtime, scheduler, worker ve guardian birlikte çalışıyor.
- Canlılık: `healthy`; hazırlık: credential ve gerçek hesap/model kabulü tamamlanana kadar bilinçli olarak `setup_required`.
- Scheduler ve model worker varsayılan olarak kapalı-güvenli durumdadır; credential yokken görev, model çağrısı, dış çağrı veya yayın yapmaz.
- Runtime model hattı task → imzalı görev bağlamı → lease/heartbeat → kompakt bağlam → görev/model/şema bağlı çıktı → ayrı şema ve kalite değerlendirmesi → token/maliyet telemetrisi → checkpoint → completion sırasıyla deterministik yerel adaptörle uçtan uca doğrulandı.
- Üretim döngüsü sınıflandırma → analiz → içerik → görsel brief → sınırlı tartışma → Ordinaryüs → gerekirse tek bağımsız denetim → onay paketi sırasıyla çalışır; yayın eylemi üretmez ve Operator onayında durur.
- Pasif n8n model adaptörü hazırdır: `ProdModelAdapter18A` / `workflows/18-runtime-model-adapter-template.json`. Credential seçilmeden ve gölge kabul bitmeden etkinleştirilemez.
- Çıktılar görev kimliğine bağlanmadan tamamlanamaz; modelin kendi beyanı kanıt sayılmaz. Kalıcı öğrenme ve yüksek güvenli kararlar doğrulanmış kanıt referansı ister.
- Gizli yerel değerler DPAPI ile korunur; secrets klasörü yalnız mevcut Windows kullanıcısı, SYSTEM ve Administrators erişimine açıktır.
- İmzalı kritik dosya envanteri, imzalı hesap kayıt defteri ve birbirinden farklı servis anahtarları doğrulandı; hiçbir doğrulanmış hedef hesap yokken yayın yetkisi kapalıdır.
- Son şifreli arşiv/geri-yükleme tatbikatı HMAC ve dosya hash doğrulamasıyla PASS verdi. Bu yalnız aynı makinedeki arşiv bütünlüğü kanıtıdır; uzak/farklı fiziksel kopya ve bağımsız cihaz açılışı henüz kullanıcı kapısıdır.
- 80 altın güvenlik, 61 runtime sertleştirme, 5 disk atomikliği, 5 kapalı-güvenli scheduler/worker, 14 worker hattı, 5 sınırlı orkestrasyon, 7 servis yetkisi ve 8 hesap/onay bağlama testi PASS verdi.
- Token paketi testindeki 10 görev türünün tamamı hedef ve sert üst sınırların altındadır; tam geçmiş ve ham loglar modele gönderilmez.
- n8n içindeki bütün workflow'lar pasiftir; mevcut `01 - Ajans Ana Akış` korunmuştur.

Yerel yürütme, güvenlik ve geri dönüş sözleşmeleri uygulanmıştır. Tam üretim iddiası için kalanlar kullanıcı/harici doğrulama kapılarıdır: yerel onay parolası, n8n Header Auth ve Gemini credential seçimi, doğrulanmış kalıcı hedef hesap kimlikleri, 60 kompakt + 60 tam-bağlam eşleştirilmiş gerçek gölge kalite koşusu, hedef platform bağlantıları ve farklı fiziksel/uzak ortamda bağımsız geri-yükleme açılışı. Bu kapılar tamamlanmadan worker/scheduler etkinleşmez ve sistem `setup_required` kalır.

> Not: Aşağıdaki bölümler kurulumun tarihsel gelişim kaydıdır. Eski sayaç veya “eksik” ifadeleri bu yetkili son durum bölümünü geçersiz kılmaz.

Son yerel mimari incelemesi: 2026-08-02  
Son doğrulanmış pasif n8n adaptör içe aktarımı: 2026-08-02  
Çalışma kapsamı: Yerel ve geri alınabilir dosya/runtime düzeni, güvenli model aktivasyon kapısı, hesap/onay bağlama, zaman/yeniden başlatma, sınırlı ajan orkestrasyonu ve pasif n8n workflow'ları; credential, gerçek model çağrısı ve dış servis/yayın işlemi yok.

## 2026-07-27 operasyon ve token mimarisi v3

- Doğrulanmış yedek: `backups/2026-07-27_21-36-32/operasyon-ve-token-v3/`.
- Ajanlar arası kesin kısa JSON sözleşmeleri `data/contracts/ajan-veri-sozlesmeleri.json` içine merkezileştirildi. Ortak görev/marka/ajan zarfını model değil runtime ekler.
- `kalite-politikasi.json` ilk 30 gün kalibrasyonu, 1–3 sonuçta yalnız deney adayı, 10–20 sonuçta geçici kural adayı ve kanıtlı aktif kural ayrımını tanımlar.
- `gozlemlenebilirlik-politikasi.json` görev durumu, node/aşama, token, maliyet, süre, hata ve sağlık kaydını tanımlar; ham prompt/yanıt kaydı varsayılan olarak kapalıdır.
- Bağımsız Denetçi eklendi. Kritik karar farklı sağlayıcıyla denetlenemiyorsa denetim bağımsız sayılmaz ve Operator yolu korunur.
- Risk bazlı orkestrasyon eklendi: düşük riskte minimum ajan, orta riskte gerekli uzmanlar, kritik işte tam denetim yolu. Her görevde bütün ajanlar çalışmaz.
- Retry/backoff, hata parmak izi, dead-letter queue, insan müdahalesi sınıfları ve Ordinaryüs kesinti yolu açıklaştırıldı.
- Bağlam paketi v3, modele yalnız `$.model_payload` gönderir. Bütçe, önbellek, hash, guard ve telemetri model girdisinden ayrıldı.
- Tüm aktif JSON doğrulaması ve 10 görev tipi bağlam testi PASS: 120 JSON, 11 rol kartı, tüm ajan/marka hash'leri geçerli.
- Tahmini model girdileri: sınıflandırma 191, analiz 597, içerik 692, görsel brief 714, tartışma 532, Ordinaryüs 433, bağımsız denetim 316, güncellik 171, hafıza 159, arayüz 165 token. Tüm paketler hedef ve sert bütçelerin altındadır.
- Mevcut canlı n8n veritabanı, credential'lar ve `01 - Ajans Ana Akış` değiştirilmedi. Kısaltılmış aynı kaynak yollarını okuduğu için mevcut Analizci çağrısı da daha küçük girdi kullanır; bağlam v3 canlıya alınmadan önce pasif/gölge import testi gerekir.

## Mevcut durum

TrendyBrander projesi n8n 2.31.6 üzerinde çalışan Analizci akışının yanında marka kimliği, dokuz üretim/yönetim ajanı, Başlatma/Sağlık Kontrol Ajanı, Bağımsız Denetçi, model yapılandırmaları, kalıcı hafıza ve son Analizci çıktısı içeriyor. Ajan promptları markanın “bunu ben de yapabilirim” konumlandırmasında tutarlı. Merkezi politikalar zaman, çevrimdışı kalma, kalıcı görev kuyruğu, güvenli checkpoint devamı, çift çalıştırma koruması ve kritik karar denetimini kapsıyor. Başlatma, Orkestratör, model yönlendirme, ajan tartışması, Operator onay kapısı ve yerel uçtan uca zincir pasif canary workflow'larıyla gerçek n8n motorunda doğrulandı.

## Proje yapısı ve mevcut dosyaların görevi

- `docker-compose.yml`: n8n servisi, saat dilimi, port ve yerel volume bağları.
- `n8n/`: Canlı n8n veritabanı, çalışma günlükleri, yapılandırma ve workflow execution binary verileri. Bu incelemede değiştirilmedi.
- `n8n/nodes/package.json`: Kurulu özel node bağımlılık kabuğu; şu anda bağımlılık yok.
- `projects/marka-kimligi.txt`: TrendyBrander konumlandırması, hedef kitle, dil, mesaj, görsel ve içerik ilkeleri.
- `projects/sistem-vizyonu.txt`: Yaşayan ajans beyni, hafıza, tartışma, onay ve kendini geliştirme vizyonu.
- `projects/agents/analizci.txt`: Veri ve marka temelli stratejik yön üretimi.
- `projects/agents/sosyal-medya-icerik-stratejisti.txt`: Stratejiyi içerik planına, kancaya, CTA'ya ve görsel yönüne çevirme.
- `projects/agents/gorsel-stratejist.txt`: Görsel brief, kompozisyon ve üretim promptu.
- `projects/agents/kontrol-muhalefet-kurulu.txt`: Satış/marka kontrolü, cesur ve temkinli muhalif bakış.
- `projects/agents/ana-ordinaryus.txt`: Final iç karar ve kalite hakemliği.
- `projects/agents/operasyon-orkestratoru.txt`: Görev sırası, maliyet, model katmanı ve çalışma sıklığı.
- `projects/agents/guncellik-gozcusu.txt`: Trend, platform ve model adaylarının takibi.
- `projects/agents/hafiza-ogrenme-yoneticisi.txt`: Hafıza sınıflandırma, kanıtlı öğrenme ve temizlik önerisi.
- `projects/agents/yayin-arayuz-ajani.txt`: Operator onay arayüzü, revize çevirisi ve yetkili yayın devri.
- `projects/agents/baslatma-saglik-kontrol-ajani.txt`: Açılışta zaman, sağlık, kuyruk, checkpoint ve hafıza senkronizasyonu; Orkestratöre güvenli devam planı.
- `projects/models/model-secimi.json`: Mevcut n8n uyumluluğu için eski yerel model seçimi.
- `projects/models/model-kutuphanesi.json`: Eski model aday ve hedef kayıtları.
- `data/memory/sistem-hafizasi.json`: Kalıcı marka/sistem kuralları ve mimari dosya bağlantıları.
- `data/memory/aktif-baglam.json`: Tek görev için küçük, geçici bağlam ve limit durumu.
- `data/memory/zaman-yonetimi.json`: Son çalışma zamanları, çevrimdışı süre sınıfları, geciken görevler ve cloud-uyumlu saat politikası.
- `data/memory/gorev-kuyrugu.json`: Yarım/bekleyen görevler, checkpoint, lease, retry ve idempotency durumu.
- `data/logs/analizci-son-cikti.txt`: Son Analizci ön analiz raporu; sonuç verisi değil, çalışma çıktısı.
- `projects/marka-referanslari/*.png`: Altı marka görsel referansı.

## Çalışan parçalar

- Docker ile yerel n8n servisi için mevcut yapılandırma ve volume bağları var.
- Canlı n8n veritabanı ve Analizci execution verileri mevcut.
- Dokuz ajan promptu mevcut ve marka konumlandırmasıyla büyük ölçüde uyumlu.
- Marka kimliği ve sistem vizyonu mevcut.
- Kalıcı hafıza JSON'u geçerliydi ve korunarak genişletildi.
- Son Analizci çıktısı yerel log olarak mevcut.
- Sistem kapalı kalmayı hata saymayan, açılışta son güvenli kayıttan karar veren “uyuyan ama kaldığı yeri bilen” dosya mimarisine sahip.

## Bulunan hatalar ve tutarsızlıklar

- `projects/models/model-secimi.json` içine Markdown kod çiti karıştığı için geçersiz JSON'du.
- `projects/models/model-kutuphanesi.json` içine birden fazla Markdown kod çiti karıştığı için geçersiz JSON'du.
- `data/memory/aktif-baglam.json` sıfır bayttı ve gerçek JSON ayrıştırıcısı açısından geçersizdi.
- Eski model dosyalarında güncelliği resmî kaynaktan doğrulanmamış model adları ve hedefler kesin yapılandırma/fakt diliyle karışıyordu.
- `sistem-vizyonu.txt` sistemi 7/24 çalışan bir beyin olarak anlatırken ajan promptları gereksiz sürekli çağrıyı yasaklıyor. Bu, “servis 7/24 erişilebilir; ajanlar olay/takvim bazlı çalışır” şeklinde birleştirildi.
- Vizyon metnindeki “Sosyal Medya Profesyoneli” ve ayrı üretim ajanları, mevcut dosyalarda Analizci + İçerik Stratejisti + Görsel Stratejist rollerine dağılmış durumda.
- Eski dosyalarda tartışma turu, bağımsız denetim, task/idempotency, circuit breaker, cold start, kanıt etiketi ve rollback için ortak makinece okunabilir politika eksikti.
- Son sistem başlangıcı, çevrimdışı süre, geciken işler ve kalıcı görev kuyruğu için ortak kayıt bulunmuyordu; sabit saatli tetiklemelerin kaçırılan çalışmaları çoğaltma riski vardı.
- `docker-compose.yml` içinde düz metin bir n8n şifreleme sırrı bulunuyor. Değer güvenlik nedeniyle bu rapora kopyalanmadı ve credential kapsamı nedeniyle dosya değiştirilmedi.
- `docker-compose.yml` değişken sürüm etiketi kullanıyor; gelecekte beklenmedik sürüm kayması riski var. Çalışan akışı bozma ihtimali nedeniyle değiştirilmedi.

## Yapılan düzeltmeler

- İki eski model JSON'undaki Markdown kod çitleri kaldırıldı ve yapı gerçek JSON hâline getirildi.
- Model dosyalarına, model adı/fiyat/kota/erişim bilgilerinin resmî kaynaktan doğrulanmadığını belirten güven durumu eklendi.
- Eski `test_modeli_degistirme` yetkisi; yalnız izinli ücretsiz havuzda Ordinaryüs, yeni sağlayıcı/veri aktarımı/ücretli kullanımda Operator onayı olacak şekilde çekirdek kuralla birleştirildi.
- Boş aktif bağlam; görev, limit, onay, risk ve devam alanları olan güvenli bekleme şemasıyla dolduruldu.
- Kalıcı hafıza; merkezi dosya bağlantıları, kanıtlı öğrenme, güvenlik ve maliyet özetleriyle kayıp oluşturmadan genişletildi.
- Kök `AGENTS.md` ile rol, girdi/çıktı, konuşma, tetiklenme, model katmanı ve tartışma kapanış sözleşmesi oluşturuldu.
- Başlatma/Sağlık Kontrol Ajanı eklendi; görev çalıştırma yetkisi verilmeden Orkestratör öncesi sağlık ve devam planı aşaması oluşturuldu.
- Zaman kayıtları UTC/ISO-8601, Europe/Istanbul gösterim saat dilimi ve 72 saat/14 gün çevrimdışı sınıflarıyla yapılandırıldı.
- Kalıcı görev kuyruğuna checkpoint, retry, lease, idempotency, içerik sürümü ve onay snapshot alanları eklendi.
- Aktif bağlama `sistem_zamani`, `son_calismalar`, `bekleyen_gorev_sayisi`, `son_durum_kontrolu` ve `sistem_acilis_notu` alanları eklendi.
- Durum makinesine beş aşamalı açılış akışı ve yarım görev/eski analiz/kritik hata/normal devam kararları bağlandı.

## Doğrulama sonucu

- Yedekler hariç projedeki 33 aktif JSON dosyası Python JSON ayrıştırıcısıyla, yinelenen anahtar kontrolü de açık olacak şekilde yeniden okundu; 33'ü geçerli, 0'ı hatalı.
- İstenen iki yeni bellek JSON'u ve yeni ajan dosyasının mevcut olduğu doğrulandı.
- Durum makinesindeki 16 görev durumu ve 5 açılış aşaması, 22 kabul senaryosu, 10 ajan yetkisi, 6 kuyruk durumu, 5 model katmanı ve 3/4 tur tartışma sınırı anlamsal kontrollerden geçti.
- Kalıcı hafızadaki eski alanların değişmeden korunduğu; eski model kütüphanesinin kayıpsız birleştiği; model seçimindeki tek içerik değişikliğinin çekirdek onay kuralı olduğu doğrulandı.
- UTF-8 bozulma belirteci ve aktif JSON içinde Markdown kod çiti bulunmadı.
- Düz metin sır örüntüsü yeni proje belgelerine veya merkezi JSON dosyalarına kopyalanmadı; bilinen n8n sırrı yalnız dokunulmayan mevcut Docker yapılandırmasında kaldı.

## AŞAMA 2 — n8n güvenli yürütme test paketi

### Analizci workflow salt okunur incelemesi

- Güvenli n8n CLI export denenmek üzere ortam kontrol edildi; `n8n`, Docker ve Podman komutları bulunamadı.
- Canlı `n8n/database.sqlite` açılmadı, sorgulanmadı veya değiştirilmedi.
- Yalnız n8n event logları ve execution binary metadata kayıtları okundu.
- Gözlenen workflow kimliği: `PPvRAMe1eJERZ8ca`.
- Gözlenen workflow adı: `01 - Ajans Ana Akış`.
- Loglarda gözlenen node adları: `When clicking ‘Execute workflow’`, `Read/Write Files from Disk`, `Extract from File`, `Read/Write Files from Disk1`, `Extract from File1`, `Basic LLM Chain`, `Google Gemini Chat Model`, tarihsel olarak `OpenAI Chat Model`, `Convert to File`, `Read/Write Files from Disk2`.
- Son tam gözlenen başarılı dizilerden biri: Manual Trigger → marka kimliğini oku/çıkar → Analizci promptunu oku/çıkar → Basic LLM Chain → Google Gemini Chat Model → Convert to File → disk yazma.
- Execution metadata içinde `marka-kimligi.txt`, `analizci.txt` ve üretilmiş `file.txt` adları gözlendi.
- Binary alan adları loglarda `data` ve tarihsel bir denemede `veri` olarak gözlendi. Yeni test workflow'u her dosyayı sırayla varsayılan `data` alanında işlediği için kendi içinde çakışma yaratmıyor.
- LLM izinde `response.generations[].text` ile `response.tokenUsage.completionTokens`, `promptTokens` ve `totalTokens` alanları gözlendi.
- Google Gemini bağlantısı `Google Gemini Chat Model` node'u ve `gemini-3.1-flash-lite` model adıyla gözlendi; credential içeriği okunmadı veya rapora kopyalanmadı.
- Host üzerinde mevcut Analizci çıktı dosyası `data/logs/analizci-son-cikti.txt`. Event logları güncel yazma node'unun kesin hedef parametresini göstermediği için container içindeki tam hedef yol export olmadan doğrulanamadı.
- Tam güncel workflow export'u olmadığı için kesin node parametreleri, tam dosya seçicileri ve güncel credential bağlantı kimliği doğrulanmış kabul edilmedi.

### Oluşturulan test paketi

- `workflows/01-baslatma-saglik-kontrol-test.json`: İçe aktarılabilir, `active=false`, yalnız Manual Trigger ile başlayan ve adı `TEST — YAYIN YAPMAZ` olan workflow.
- `tests/fixtures/*.json`: 2/7/15 gün çevrimdışı, stale lease, geçerli/geçersiz checkpoint, çift analiz, çift yayın, saat geri kayması ve onaysız yayın için on fixture.
- `tests/validate-workflow.ps1`: Workflow, node sırası, pasiflik, credential/dış bağlantı/yazma yokluğu, on karar ve korunan dosya hash doğrulaması.
- `tests/results/startup-test-report.json`: On senaryonun tamamı PASS; 19 gerçek `data/memory` ve `data/logs` dosyasının test öncesi/sonrası toplu SHA-256 değeri eşit.
- `N8N_TEST_GUIDE.md`: Manuel import ve tek test çalıştırma adımları.

### Test workflow node sırası

Manual Trigger  
→ Test Senaryosunu Seç  
→ Zaman Yönetimini Oku / JSON çıkar  
→ Görev Kuyruğunu Oku / JSON çıkar  
→ Aktif Bağlamı Oku / JSON çıkar  
→ Durum Makinesini Oku / JSON çıkar  
→ Hata Kaydını Oku / JSON çıkar  
→ Başlatma Sağlık Kontrolü Kararı  
→ Kuyruk / Lease / Checkpoint / Idempotency Kontrolü  
→ Operasyon Orkestratörü Sağlık Raporu

Workflow içinde dosya yazma, model, HTTP, webhook, schedule, credential veya yayın node'u yoktur.

### Sentetik test sonucu

- `offline-2-days`: `normal_devam` — PASS.
- `offline-7-days`: `tek_ozet_toparlama` — PASS.
- `offline-15-days`: `tam_durum_degerlendirmesi` — PASS.
- `stale-lease`: `lease_degerlendirmeye_gonder` — PASS.
- `valid-checkpoint`: `checkpointten_devam` — PASS.
- `invalid-checkpoint`: `otomatik_devam_etme` — PASS.
- `duplicate-analysis`: `tekrar_calistirma` — PASS.
- `duplicate-publish`: `reddet_cift_yayin` — PASS.
- `clock-moves-backward`: `otomatik_devami_durdur` — PASS.

## AŞAMA 3 — Pasif Orkestrasyon Canary Paketi

### n8n'e eklenen pasif workflow'lar

- `TstOrchestr02A`: `TEST — YAYIN YAPMAZ — 02 Ajans Orkestratör Çekirdeği`
- `TstModelRoute03A`: `TEST — YAYIN YAPMAZ — 03 Dinamik Model Yönlendirme`
- `TstDebateFlow04A`: `TEST — YAYIN YAPMAZ — 04 Ajan Tartışma Kurulu`
- `TstApprovalGt05A`: `TEST — YAYIN YAPMAZ — 05 Operator Onay Kapısı`
- `TstEndToEnd06A`: `TEST — YAYIN YAPMAZ — 06 Ajans Yerel Uçtan Uca Canary`

Beş workflow da `active=false`, yalnız Manual Trigger ile başlayan, credential içermeyen, dosya yazmayan, model/dış servis çağırmayan ve yayın node'u taşımayan canary akışlarıdır.

### Gerçek n8n çalışma sonucu

- Orkestratör çekirdeği: PASS.
- Dinamik model yönlendirme: PASS.
- Ajan tartışma kurulu: PASS.
- Operator onay kapısı: PASS.
- Yerel uçtan uca canary: PASS.
- Uçtan uca zincir `Operator_onayi_bekliyor` durumunda durdu.
- Model çağrısı: 0.
- Dış çağrı: 0.
- Dosya yazma: 0.
- Yayın: 0.
- Korunan 18 `data/memory` ve `data/logs` JSON dosyasının SHA-256 özetleri çalışma öncesi ve sonrasında aynı kaldı.
- n8n sağlık kontrolü: `200 OK`.
- Mevcut `01 - Ajans Ana Akış` değiştirilmedi.

### AŞAMA 3 dosyaları

- `workflows/02-ajans-orkestrator-cekirdegi-test.json`
- `workflows/03-dinamik-model-yonlendirme-test.json`
- `workflows/04-ajan-tartisma-kurulu-test.json`
- `workflows/05-Operator-onay-kapisi-test.json`
- `workflows/06-ajans-yerel-uctan-uca-canary-test.json`
- `tests/validate-stage3-workflows.ps1`
- `tests/results/stage3-workflow-report.json`
- `tests/results/stage3-runtime-report.json`

### AŞAMA 3 yedekleri

- n8n tam yedeği: `backups/2026-07-27_02-03-00/`
- Uçtan uca canary öncesi n8n veritabanı: `backups/2026-07-27_02-06-55/n8n/database.sqlite`
- PROJECT_STATE güncelleme öncesi yedek: `backups/2026-07-27_02-07-57/PROJECT_STATE.md`
- `unauthorized-publish`: `reddet_onaysiz_yayin` — PASS.

## Oluşturulan merkezi mimari

`data/memory/` altında:

- `model-yonlendirme.json`
- `model-kutuphanesi.json`
- `yetki-matrisi.json`
- `tartisma-politikasi.json`
- `durum-makinesi.json`
- `musteri-baslangic-motoru.json`
- `hafiza-politikasi.json`
- `guvenlik-politikasi.json`
- `degisiklik-yonetimi.json`
- `trend-kayitlari.json`
- `test-kabul-kriterleri.json`
- `zaman-yonetimi.json`
- `gorev-kuyrugu.json`

`data/logs/` altında:

- `ajans-oturum-log.json`
- `hata-kaydi.json`
- `model-performans-kaydi.json`

## Yedekler

Değiştirilen dört mevcut dosya, düzenlemeden önce göreli klasör yapısı korunarak `backups/2026-07-26_09-22-38/` altına kopyalandı ve SHA-256 özetleri eşleşti:

- `backups/2026-07-26_09-22-38/data/memory/aktif-baglam.json`
- `backups/2026-07-26_09-22-38/data/memory/sistem-hafizasi.json`
- `backups/2026-07-26_09-22-38/projects/models/model-secimi.json`
- `backups/2026-07-26_09-22-38/projects/models/model-kutuphanesi.json`

Son doğrulama iyileştirmesinden önce iki yeni dosyanın ara sürümü de `backups/2026-07-26_09-33-36/` altında korundu:

- `backups/2026-07-26_09-33-36/data/memory/model-yonlendirme.json`
- `backups/2026-07-26_09-33-36/PROJECT_STATE.md`

Zaman ve yeniden başlatma entegrasyonunda değiştirilen dokuz mevcut dosya, düzenlemeden önce `backups/2026-07-26_09-58-00/` altında göreli yolları korunarak yedeklendi ve SHA-256 özetleri doğrulandı:

- `AGENTS.md`
- `PROJECT_STATE.md`
- `data/memory/aktif-baglam.json`
- `data/memory/durum-makinesi.json`
- `data/memory/sistem-hafizasi.json`
- `data/memory/yetki-matrisi.json`
- `data/memory/hafiza-politikasi.json`
- `data/memory/test-kabul-kriterleri.json`
- `data/memory/degisiklik-yonetimi.json`

AŞAMA 2'de değiştirilen tek mevcut dosya olan `PROJECT_STATE.md`, düzenleme öncesinde `backups/2026-07-26_10-13-49/PROJECT_STATE.md` yoluna yedeklendi ve SHA-256 özeti doğrulandı.

## Varsayımlar

- Ajan promptlarındaki “Sürekli çalışma.” ifadesi, takip eden sınırlayıcı cümleler nedeniyle “sürekli çalıştırılma” yasağı olarak yorumlandı; özgün promptlar değiştirilmedi.
- Mevcut n8n akışının `projects/models/` yollarını kullanabileceği varsayıldı. Bu nedenle eski dosyalar yerinde tutuldu; yeni `data/memory/` dosyaları merkezi politika, eski dosyalar uyumluluk kaynağı olarak işaretlendi.
- Model adları, fiyatlar, kotalar ve sağlayıcı desteği bu aşamada dış kaynaktan doğrulanmadı; aday olarak tutuldu.
- Yeni JSON şemaları küçük, genişletilebilir ve n8n Code/Set/Read düğümlerince okunabilir düz nesne/dizi yapılarıyla tasarlandı.
- Henüz dış bağlantı ve gerçek model çağrısı olmadığı için maliyet alanları `null` veya sıfır güvenli varsayılanlarıyla bırakıldı.
- 72 saat sınırı “72 saate kadar normal”; 72 saatten uzun kesintide özet toparlama olarak yorumlandı. 14 gün ve üzeri tam değerlendirmedir.
- Zaman alanları mimari hazırlık aşamasında uydurulmadı; ilk gerçek başlatma kontrolünde doldurulmak üzere `null` bırakıldı.
- Lokal JSON kuyruğu ile ilerideki cloud kuyruğu aynı adapter sözleşmesini kullanacak şekilde tasarlandı; sürekli açık sunucu varsayılmadı.

## Dokunulmayan kritik alanlar

- `n8n/database.sqlite`, WAL/SHM dosyaları ve canlı workflow kayıtları.
- n8n credential kayıtları ve mevcut şifreleme sırrı.
- Çalışan Analizci akışı, execution binary verileri ve mevcut dosya yolları.
- Meta, Instagram, Wix, GA4 veya başka dış servis bağlantıları.
- Reklam bütçeleri, yayın ve dış platform ayarları.
- Dokuz özgün ajan promptu, marka kimliği, sistem vizyonu, görsel referanslar ve Analizci çıktı logu.

## Eksik veya henüz uygulanmayan parçalar

- Merkezi politikaları okuyan pasif canary workflow'ları kuruldu; ancak gerçek görevleri değiştiren stateful yürütme katmanı henüz etkin değil.
- Operator onay kapısının karar mantığı canary olarak doğrulandı; gerçek yayın adaptörü özellikle bağlı değil.
- Gerçek task/idempotency deposu, atomik kuyruk yazımı, failed-task queue, circuit breaker ve otomatik rollback çalıştırıcısı henüz bağlı değil.
- Trend ve model doğrulaması için resmî kaynak bağlayıcıları yok.
- Model çağrısı, token/maliyet telemetrisi ve gölge test çalıştırıcısı yok.
- Meta/Instagram yayın, Wix, GA4 ve performans toplama bağlantıları yok.
- Genel mimari kabul senaryolarının tamamı canlı n8n üzerinde çalıştırılmadı. Başlatma `offline-2-days` senaryosu ve AŞAMA 3 canary zinciri gerçek n8n motorunda PASS verdi.
- Başlatma kontrolü n8n'e pasif olarak içe aktarıldı ve `offline-2-days` gerçek execution sonucu PASS oldu.
- Atomik kuyruk yazımı, gerçek lease edinimi ve startup heartbeat kaydı salt okunur canary workflow'larında özellikle uygulanmadı.

## Riskler

- Düz metin n8n şifreleme sırrı güvenlik riski oluşturuyor; güvenli credential/secret yönetimine taşınması planlanmalı, ancak çalışan kimlik bilgilerini geçersiz kılmamak için kontrollü bakım gerekir.
- Değişken n8n image etiketi güncelleme sırasında beklenmedik davranış değişikliği yaratabilir.
- Eski ve merkezi model kütüphaneleri uyumluluk için birlikte tutuluyor; ileride n8n referansları doğrulandıktan sonra tek kanonik kaynağa kontrollü geçiş gerekir.
- Politikalar n8n canary akışlarında karar kontrolü olarak doğrulandı; gerçek stateful görev/yayın yürütücüsü bağlanana kadar üretim koruması olarak kabul edilmemelidir.
- Son Analizci çıktısındaki bazı öneriler gerçek performans verisine değil marka belgesine dayanıyor; kalıcı öğrenme sayılmamalıdır.
- Lokal JSON kuyruğunda atomik geçici-dosya/değiştirme sözleşmesi tanımlı olsa da bunu uygulayacak yürütücü kurulana kadar eşzamanlı yazma koruması yalnız politikadır.
- Bilgisayar temiz kapanmadan kapanırsa gerçek kapanış zamanı bilinmeyebilir; çevrimdışı süre son güvenli kayıt zamanından hesaplanmalıdır.
- Host saati geriye alınırsa negatif süre riski oluşur; politika otomatik devamı durdurur ancak gerçek kontrol yürütücüsü henüz bağlı değildir.
- `readWriteFile`, `extractFromFile` ve Code node typeVersion uyumluluğu n8n 2.31.6 gerçek çalıştırmalarında doğrulandı.
- Sentetik fixture değerleri n8n volume'una yeni bağ eklememek için workflow seçim node'unda gömülüdür; doğrulama aracı fixture kimlikleri ve karar kodlarının workflow ile eşleştiğini kontrol eder.
- Analizci workflow'unun tam güncel export'u alınamadığı için loglarda tarihsel olarak görülen node'ların hâlâ aynı parametrelerle aktif olduğu varsayılmamalıdır.

## Sonraki güvenli uygulama sırası

1. Beş AŞAMA 3 canary workflow'unu pasif tut; mevcut Analizci akışını değiştirme.
2. İzole test dosyalarında atomik kuyruk yazımı, lease edinimi, checkpoint ve idempotency tekrarını stateful canary olarak doğrula.
3. Prompt injection, hafıza zehirlenmesi, kota, maliyet, düşük güvenli Ordinaryüs ve rollback senaryolarını gerçek n8n canary akışında çalıştır.
4. Model kütüphanesi adaylarını yalnız resmî kaynaklarla doğrula; fiyat/kota alanlarını kaynak ve tarihle doldur.
5. İzinli model için sentetik gölge test ve model performans telemetrisini doğrula.
6. Mevcut Analizci workflow'unu değiştirmeden paralel bir entegrasyon canary'si hazırla.
7. Operator onay ekranını gerçek yayın adaptöründen ayrı şekilde bağla.
8. En son, ayrı onaylarla dış platform bağlantıları ve yayın adaptörlerini ele al.

## AŞAMA 4 — İzole Stateful Yürütme Canary

### Eklenen parçalar

- `projects/runtime/stateful-canary.mjs`
- `data/test-runtime/stateful-canary-state.json`
- `workflows/07-stateful-yurutme-canary-test.json`
- `tests/validate-stage4-stateful-canary.ps1`
- `tests/results/stage4-stateful-canary-report.json`
- `tests/results/stage4-runtime-report.json`

Pasif workflow:

- Kimlik: `TstStatefulCan07A`
- Ad: `TEST — YAYIN YAPMAZ — 07 Stateful Yürütme Canary`
- Durum: `active=false`
- Credential: yok
- Model çağrısı: yok
- Dış servis çağrısı: yok
- Yayın işlemi: yok

### Gerçek n8n çalışma sonucu

- İlk tekil görev başarıyla tamamlandı.
- Aynı idempotency anahtarıyla ikinci çalıştırma reddedildi.
- Eşzamanlı kilit çakışması engellendi.
- Süresi geçmiş lease güvenli biçimde kurtarıldı.
- Geçerli, geçersiz ve retry sınırı dolmuş checkpoint kuralları doğrulandı.
- Zorunlu doğrulama hatası sonrası rollback yapıldı; önceki ve geri yüklenen SHA-256 özeti eşleşti.
- Test sonunda izole durum `clean`, görev ve olay sayıları sıfır kaldı.
- İzole test alanında toplam 8 yazma yapıldı.
- Üretim `data/memory` ve `data/logs` alanlarına yazma yapılmadı.
- AŞAMA 3 ve AŞAMA 4 arasında korunan 18 üretim dosyasının SHA-256 özetleri değişmedi.
- 44 aktif JSON dosyasının tamamı geçerli bulundu.
- n8n sağlık kontrolü `200 OK` verdi.
- `01 - Ajans Ana Akış` değiştirilmedi.

### Güvenlik notu

n8n 2.x, `Execute Command` düğümünü normal hizmette güvenlik amacıyla kapalı tutmaktadır. Bu ayar kalıcı olarak açılmadı. Stateful test yalnız tek kullanımlık ve izole n8n CLI konteynerinde `NODES_EXCLUDE=[]` geçici ayarıyla çalıştırıldı. Normal n8n hizmetinin güvenlik yapılandırması değiştirilmedi.

### AŞAMA 4 yedekleri

- n8n veritabanı: `backups/2026-07-27_02-25-42/n8n/database.sqlite`
- n8n veritabanı SHA-256: `863D6A754E770BCD9DF8985827B5EE666C4B6178EE58534B1E6AE5874015E47D`
- PROJECT_STATE: `backups/2026-07-27_02-28-58/PROJECT_STATE.md`
- PROJECT_STATE SHA-256: `C4919D693A628123722A0E5473585BB48D2D02FDF8062D8E0FA40791529B786B`

## AŞAMA 4 sonrası sonraki güvenli sıra

1. Prompt injection, hafıza zehirlenmesi, kota/maliyet ve düşük güvenli Ordinaryüs senaryolarını ayrı pasif n8n canary paketinde çalıştır.
2. Stateful yürütücüyü üretime bağlamadan önce minimum yetkili kalıcı çalıştırma adaptörünü tasarla; normal n8n hizmetinde `Execute Command` düğümünü açma.
3. Resmî sağlayıcı kaynaklarıyla model adaylarını doğrula ve kaynak/tarih bilgisiyle model kütüphanesini güncelle.
4. Kullanımına önceden izin verilmiş ücretsiz modelde sentetik gölge test ve token/maliyet telemetrisini doğrula.
5. Mevcut Analizci workflow'unu değiştirmeden paralel entegrasyon canary'si hazırla.
6. Operator onay ekranını gerçek yayın adaptöründen ayrı bağla.

## 2026-07-27 nihai yerel üretim sertleştirmesi

- Kapsam: gerçek model, görsel üretim, yayın veya dış hesap çağrısı yapılmadan yerel pre-credential katman tamamlandı.
- Son doğrulama: `tests/results/production-readiness-report.json` — `LOCAL_PRE_CREDENTIAL_READY`.
- Transaction runtime: 42/42 PASS; eşzamanlı lease, checkpoint, idempotency, crash recovery, imzalı onay, audit zinciri, gizlilik ve retention dahil.
- Güvenlik altın vakaları: 62/62 PASS; prompt injection, kanıtsız iddia, güvenli çıktı ve runtime alanı saldırıları dahil.
- Disk ve atomiklik: 5/5 PASS; düşük disk yazma öncesi durur, transaction ortası hata kısmi görev bırakmaz.
- Token planı: 10/10 görev ideal hedefin ve sert limitin altında. Görev profili `memory_limit` artık gerçekten uygulanır; tüm hafıza veya ham geçmiş modele gönderilmez.
- Sağlık gözcüsü: `ai-ajans-guardian`, n8n/runtime/Ajans Merkezi için 30 saniyelik yerel kontrol ve atomik sağlık kaydı üretir; model, yayın ve dış çağrı yapmaz.
- Şifreli nihai geri yükleme tatbikatı: 390 dosya doğrulandı; guardian, kalite kabul aracı, runtime/n8n veritabanları ve kurtarma sırları pakette bulundu; geçici açık restore silindi.
- Tedarik zinciri: n8n image digest sabit; başlatma, onay, yedek, runtime, merkez, guardian, bağlam derleyici, sözleşme, politika ve test araçları SHA-256 envanteriyle korunur.
- Gerçek model kabul kapısı: 10 görev × 6 risk senaryosu = 60 vaka, kompakt ve tam bağlamla toplam 120 gölge koşusu için hazır. Şema, iddia, injection, marka izolasyonu, dış eylem, kalite farkı ve token tasarrufu eşikleri geçmeden etkinleşmez.
- Operatör devri: `PRE_CREDENTIAL_HANDOFF.md`. Hesaplar yalnız `candidate` kaydedilebilir; gerçek API doğrulaması olmadan `verified` ve yayın hedefi olamaz.

### Bilinçli olarak kalan kullanıcı kapıları

1. Yerel Operator onay parolasının kullanıcı tarafından belirlenmesi.
2. Gerçek API/hesap credentiallarının n8n güvenli kasasına kullanıcı tarafından girilmesi.
3. Sağlayıcının kalıcı Meta/Instagram/Wix/GA4 hesap kimliklerinin salt-okunur bağlantıyla doğrulanması.
4. Kullanıcı onaylı gerçek-model gölge kalite kabulünün geçmesi.

Bu dört kapı tamamlanmadan tam üretim hazır iddiası veya gerçek yayın yoktur.

## AŞAMA 7 — Hafıza ve Prompt Geri Alma

- Workflow: `TstRecovery10A`
- Gerçek n8n sonucu: `PASS`
- Bozuk hafıza izole edildi ve doğrulanmış yedekten geri yüklendi.
- Hatalı prompt adayı reddedildi; aktif Analizci promptunun özeti değişmedi.
- Üretim hafızası ve ajan dosyalarına yazılmadı.
- Kanıt: `tests/results/stage7-runtime-report.json`

## AŞAMA 8 — Cold Start Motoru

- Workflow: `TstColdStart11A`
- Gerçek n8n sonucu: `PASS`
- Sıfırdan marka, 30–60 günlük öğrenme dönemine alındı.
- Eski hesap geçmişi `koru / test et / karantina` olarak ayrıldı.
- Hipotezler gerçek performans bilgisi yapılmadı.
- Kanıt: `tests/results/stage8-runtime-report.json`

## AŞAMA 9 — Model Kütüphanesi Güncellik Sözleşmesi

- Workflow: `TstModelRegistry12A`
- Gerçek n8n sonucu: `PASS`
- 12 aday ve 5 sağlayıcı sınıfı kaydedildi.
- Resmî kaynak ve tarih zorunlu hale getirildi.
- Yeni model otomatik etkinleşmez.
- Ücretli aday ve yeni sağlayıcı Operator onayı olmadan kullanılamaz.
- Mevcut `models/gemini-3.1-flash-lite` yalnız mevcut Analizci ve sınırlı test kapsamına izinlidir.
- Kanıt: `tests/results/stage9-runtime-report.json`

## AŞAMA 10 — Gerçek Gemini Gölge Testi

- Workflow: `TstGeminiShadow13A`
- Gerçek n8n sonucu: `PASS`
- Model: `models/gemini-3.1-flash-lite`
- Tek çağrı: 46 giriş + 11 çıkış = 57 token.
- Şema uyumu: `%100`
- Dosya yazma ve yayın: `0`
- Sonuç `data/logs/model-performans-kaydi.json` içine tek test olarak kaydedildi.
- Tek çağrı kalıcı model tercihi oluşturmadı.
- Kanıt: `tests/results/stage10-runtime-report.json`

## AŞAMA 11 — Analizci → İçerik Stratejisti Paralel Handoff

- Workflow: `TstAnalystHandoff14B`
- Gerçek n8n sonucu: `PASS`
- Mevcut Analizci raporu ve İçerik Stratejisti rolü salt okunur olarak yüklendi.
- Token paketi sınırlandı: analiz en fazla 4500, ajan rolü en fazla 3500 karakter.
- Gerçek Analizci raporunun yeni bir dış model çağrısına gönderilmesi açık dış-veri yetkisi olmadığı için engellendi.
- Engellenen dış çağrı adayı `workflows/blocked/` altında saklandı; içe aktarılmadı.
- Yerel yönlendirme doğru ajan ve Katman 2 için hazırlandı.
- Kanıt: `tests/results/stage11-runtime-report.json`

## AŞAMA 12 — Operator Onayı ve Yayın Adaptörü Ayrımı

- Workflow: `TstApprovalSplit15A`
- Gerçek n8n sonucu: `PASS`
- Onay kuyruğu: `data/approvals/onay-bekleyen.json`
- Karar kaydı: `data/approvals/onay-kayitlari.json`
- Yayın sözleşmesi: `data/memory/yayin-adaptoru-sozlesmesi.json`
- Kullanıcı ekranı: `ui/Operator-onay-ekrani.html`
- Eksik, yanlış sürümlü, süresi geçmiş ve çift yayın talepleri engellendi.
- Geçerli Operator onayı bile yayın adaptörü kapalıyken yayın yapmadı.
- Kanıt: `tests/results/stage12-runtime-report.json`

## SON YEREL KABUL DURUMU

- 22/22 kabul senaryosu: `PASS`
- 14/14 doğrulama paketi: `PASS`
- Aktif proje JSON dosyası: `99`
- Geçersiz JSON: `0`
- n8n sağlık kontrolü: `200 OK`
- Test workflow sayısı: `17`
- Tüm test workflow'ları pasif ve `TEST - YAYIN YAPMAZ` kapsamındadır.
- Çalışan ana Analizci akışı korunmuştur.
- Ana workflow başlangıç ve final kanonik SHA-256:
  `B797BB7F284D48DE95417D41E5EE51D2DE3020C84F00E4BCFE5B6DCA3C9A43B6`
- Son tam n8n yedeği: `backups/2026-07-27_03-12-56/n8n/`

### Yerel olarak tamamlanan sınır

Kontrol düzlemi, hafıza, zaman, kuyruk, durum makinesi, tartışma sınırı, güvenlik, rollback, cold start, model kaydı, token telemetrisi, yerel ajan handoff'u ve Operator onay kapısı tamamlandı.

### Dış yetki bekleyen işler

- Meta, Instagram, Wix ve GA4 credential ve veri bağlantıları.
- OpenAI görsel API credential'ı ve ücretli kullanım izni.
- Hedef platform yayın credential'ı.
- Yayın adaptörünün etkinleştirilmesi.

Bu işler yerel mimari hatası değildir; dış veri, hesap, ücret veya yayın yetkisi gerektirdiği için bilinçli olarak kapalıdır.

## AŞAMA 11 — Yetkili Analizci → İçerik Stratejisti aktarımı

- Operator, mevcut Analizci raporunun mevcut Gemini hesabına tek görevlik İçerik Stratejisti aktarımı için açık izin verdi.
- Workflow: `TstAnalystHandoff14A`
- Model: `models/gemini-3.1-flash-lite`
- Sonuç: `PASS`
- Girdi tokenı: `2472`
- Çıktı tokenı: `330`
- Toplam token: `2802`
- Üç içerik fikri geçerli kısa JSON olarak üretildi.
- Gerçek zamanlı performans verisi olmadığı açıkça belirtildi.
- Test workflow'u dosya yazmadı ve yayın yapmadı.
- Doğrulanmış çıktı daha sonra yerel olarak `data/logs/icerik-stratejisti-son-cikti.json` dosyasına kaydedildi.
- Taslak durumu: `draft_waiting_internal_review`
- Sıradaki ajan: `gorsel_stratejist`
- Yayın yetkisi: `false`
- Kanıt: `tests/results/stage11-authorized-runtime-report.json`
- n8n yedeği: `backups/2026-07-27_03-25-21/n8n/`

## AŞAMA 13 — Kompakt bağlam ve Ajans Merkezi

- Yeni workflow'lar için tam ajan promptu varsayılan olarak kapatıldı.
- On ajan için sürümlü ve kaynak hash'iyle bağlı kısa rol kartları oluşturuldu: `data/memory/rol-kartlari.json`.
- Kısa marka kaynağı oluşturuldu: `data/memory/marka-ozeti.json`.
- Görev bazlı sert token sınırları oluşturuldu: `data/memory/baglam-derleme-politikasi.json`.
- Görsel Stratejist kompakt bağlamı tam ajan dosyası gönderilmeden üretildi.
- Tahmini Görsel Stratejist giriş bağlamı: `741 / 1400` token.
- Rol kaynağı SHA-256 doğrulandı; değişirse çağrı otomatik duracak.
- Yerel n8n workflow'u: `TstVisualBrief16Local`
- Gerçek n8n sonucu: `PASS`
- Model çağrısı: `0`
- Görsel üretim çağrısı: `0`
- Dosya yazma: `0`
- Yayın: `0`
- Sonraki güvenli durum: `harici_model_yetkisi_bekliyor`
- Kanıt: `tests/results/stage13-runtime-report.json`
- n8n yedeği: `backups/2026-07-27_03-50-00/n8n/`

### Ajans Merkezi

- Yerel adres: `http://localhost:5680`
- Docker servisi: `ai-ajans-merkezi`
- Servis salt okunur ve yalnız `127.0.0.1` adresine bağlıdır.
- Credential, n8n veritabanı ve proje prompt klasörleri Ajans Merkezi konteynerine bağlanmadı.
- Ekranlar: Genel Bakış, Ajan Konuşmaları, Çıktılar, Görseller, Token ve Maliyet, Onay Bekleyenler, Sistem.
- Görsel bölümünde üç brief, sıfır üretilmiş görsel ve altı marka referansı görünür.
- Gerçek görseller `data/outputs/images/` altında oluştuğunda otomatik gösterilir.
- Tarayıcı ve API sağlık kontrolü: `PASS`
- Statik güvenlik ve bağlam testi: `tests/results/compact-context-dashboard-static-report.json`
7. Meta, Instagram, Wix ve GA4 bağlantılarını ancak ayrı yetki ve güvenlik kontrolleriyle ele al.

## AŞAMA 5 — Güvenlik ve Karar Sınırları Canary

### Eklenen ve güncellenen parçalar

- `workflows/08-guvenlik-ve-karar-sinirlari-canary-test.json`
- `tests/fixtures/stage5-security-cases.json`
- `tests/validate-stage5-security-canary.ps1`
- `tests/results/stage5-security-canary-report.json`
- `tests/results/stage5-runtime-report.json`
- `data/memory/tartisma-politikasi.json`: Ordinaryüs minimum iç karar güven eşiği `0.80` olarak eklendi.
- `data/memory/test-kabul-kriterleri.json`: Beş gerçek n8n canary senaryosu `pass` ve kanıt workflow kimliğiyle kaydedildi.

Pasif workflow:

- Kimlik: `TstSecurity08A`
- Ad: `TEST — YAYIN YAPMAZ — 08 Güvenlik ve Karar Sınırları Canary`
- Durum: `active=false`
- Credential: yok
- Dosya yazma: yok
- Model çağrısı: yok
- Dış servis çağrısı: yok
- Yayın: yok

### Gerçek n8n çalışma sonucu

- Kötü niyetli DM prompt injection: talimat uygulanmadı, veri karantinaya yönlendirildi — PASS.
- Zehirli/başka markaya ait geçmiş veri: kalıcı gerçek yapılmadı, aktif bağlamdan çıkarıldı — PASS.
- Ücretsiz kota bitmesi: sağlayıcı atlandı, ücretli modele Operator onayı olmadan geçilmedi — PASS.
- Görev maliyet sınırı: ek model çağrısından önce görev durduruldu — PASS.
- Düşük güvenli Ordinaryüs (`0.62 < 0.80`): belirsizlik kaydedildi, yalnız bir bağımsız denetim istendi ve tartışma yeniden açılmadı — PASS.
- Test sırasında korunan 18 üretim hafıza/log dosyasında değişiklik olmadı.
- n8n sağlık kontrolü `200 OK` verdi.
- `01 - Ajans Ana Akış` değiştirilmedi.

### AŞAMA 5 yedekleri

- Tartışma politikası: `backups/2026-07-27_02-32-05/data/memory/tartisma-politikasi.json`
- Tam SQLite seti: `backups/2026-07-27_02-35-19/n8n/`
- Test kriterleri ve PROJECT_STATE: `backups/2026-07-27_02-36-04/`

## AŞAMA 5 sonrası sonraki güvenli sıra

1. Model/API kesintisi, circuit breaker, izinli failover ve başarısız görev kuyruğunu pasif n8n canary ile doğrula.
2. Bozuk hafıza, doğrulanmış yedekten kurtarma ve kötü prompt güncellemesini ayrı rollback canary paketinde doğrula.
3. Sıfır verili yeni marka ve kötü yönetilmiş mevcut hesap için Cold Start Motoru senaryolarını gerçek n8n motorunda çalıştır.
4. Yalnız resmî sağlayıcı kaynaklarıyla model kütüphanesi adaylarını doğrula.
5. İzinli ücretsiz modelle sentetik gölge test ve gerçek token/maliyet telemetrisini kur.
6. Mevcut Analizci workflow'unu değiştirmeden paralel entegrasyon canary'si oluştur.
7. Operator onay ekranını gerçek yayın adaptöründen ayrı bağla.

## AŞAMA 6 — Model Kesintisi, Circuit Breaker ve Başarısız Görev Kuyruğu

### Eklenen parçalar

- `projects/runtime/resilience-canary.mjs`
- `data/test-runtime/resilience-canary-state.json`
- `workflows/09-model-kesintisi-ve-circuit-breaker-canary-test.json`
- `tests/validate-stage6-resilience-canary.ps1`
- `tests/results/stage6-resilience-canary-report.json`
- `tests/results/stage6-runtime-report.json`

Pasif workflow:

- Kimlik: `TstResilience09A`
- Ad: `TEST — YAYIN YAPMAZ — 09 Model Kesintisi ve Circuit Breaker Canary`
- Durum: `active=false`
- Credential: yok
- Gerçek model çağrısı: yok
- Dış servis çağrısı: yok
- Yayın: yok

### Gerçek n8n çalışma sonucu

- Birinci sentetik sağlayıcı hatasında retry sayısı `1` oldu ve yalnız tek yeniden deneme planlandı.
- İkinci hatada retry sınırı `2` doldu; görev başarısız görev kuyruğuna taşındı ve circuit breaker açıldı.
- Açık circuit breaker yeni sağlayıcı çağrısını başlamadan engelledi.
- Model kütüphanesindeki doğrulanmamış adaylar failover için seçilmedi.
- Canlı kullanımı onaylanmış alternatif olmadığı için sistem güvenli biçimde durdu; ücretli/yeni sağlayıcı Operator onayı olmadan kullanılmadı.
- Half-open durumda yalnız bir probe izni verildi; paralel probe engellendi ve başarısız probe devreyi yeniden açtı.
- Test sonunda izole görev, başarısız görev, breaker ve olay kayıtları temizlendi.
- Test sırasında korunan 18 üretim hafıza/log dosyasında değişiklik olmadı.
- n8n sağlık kontrolü `200 OK` verdi.
- `01 - Ajans Ana Akış` değiştirilmedi.

### Güvenlik notu

Stateful test için `Execute Command` düğümü yalnız tek kullanımlık izole n8n CLI konteynerinde geçici olarak açıldı. Normal n8n hizmetinde kapalı kalmaya devam etmektedir.

### AŞAMA 6 yedekleri

- Tam SQLite seti: `backups/2026-07-27_02-42-10/n8n/`
- Test kriterleri ve PROJECT_STATE: `backups/2026-07-27_02-42-57/`

## AŞAMA 6 sonrası sonraki güvenli sıra

1. Bozuk hafıza, doğrulanmış yedekten kurtarma ve kötü prompt güncellemesini izole rollback canary paketinde doğrula.
2. Sıfır verili yeni marka ve kötü yönetilmiş mevcut hesap için Cold Start Motoru testlerini gerçek n8n motorunda çalıştır.
3. Yalnız resmî sağlayıcı kaynaklarıyla model adaylarını doğrula; doğrulanmamış adayları canlı kullanıma açma.
4. Kullanımına izin verilmiş ücretsiz modelle sentetik gölge test ve gerçek token/maliyet telemetrisini kur.
5. Mevcut Analizci workflow'unu değiştirmeden paralel entegrasyon canary'si oluştur.
6. Operator onay ekranını gerçek yayın adaptöründen ayrı bağla.
## 2026-08-02 - Gemini gercek gorsel test kapisi

- Yeni pasif workflow: `GeminiImageTest20A` / `TEST - YAYIN YAPMAZ - 20 Gemini Gorsel Uretimi`.
- Kaynak: daha once guvenlik kontrollerinden gecmis `data/logs/ucretsiz-yerel-test-sonucu.json` icindeki final gorsel brief.
- Model: `models/gemini-3.1-flash-lite-image`.
- Cikti: `data/outputs/images/<task_id>-gemini.png`.
- Workflow pasiftir, Manual Trigger kullanir, Meta/Instagram/yayin dugumu icermez ve mevcut `01 - Ajans Ana Akis` degistirilmemistir.
- `Run-FreeLocalEndToEndTest.ps1 -UseExistingResult`, metin ajanlarini yeniden cagirmadan yalniz gercek Gemini gorselini uretip yeni `v2-gemini-image` onay paketini hazirlayacak sekilde guncellendi.
- Gercek gorsel API cagrisi henuz yapilmadi. Google'in guncel fiyatlandirmasinda Gemini gorsel modelleri ucretsiz katmanda degildir; kullanici maliyet sinirini acikca kabul etmeden test cagrisi baslatilmaz.
- Gorsel uretildiginde bile `publish_authorized=false` ve `external_publish_executed=false` korunur; yalniz yerel onay ekranina gider.

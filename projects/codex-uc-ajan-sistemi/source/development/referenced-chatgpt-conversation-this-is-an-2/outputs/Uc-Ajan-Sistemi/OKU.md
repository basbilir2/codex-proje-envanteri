# Üç AI Stüdyo

Masaüstündeki **Uc AI Studyo** simgesine çift tıkla. Eski **Uc AI Terminal** simgesi de artık bu arayüzü açar. Bu klasördeki **Uc-AI-Studyo.cmd** ile de açabilirsin. Codex veya ChatGPT açık olmak zorunda değil.

## Geliştirme motoru 1.1 — eklenen gerçek yetenekler

- **Otomatik kontrol ve düzeltme:** Çalışmanın ardından uygulama kontrol edilir. Gerçek hata bulunursa ekran görüntüsü ve hata çıktısı aynı ajana geri verilir; en fazla iki düzeltme turu yapılır. Değişmeyen kodda geçen kontrol tekrar çalıştırılmaz. Başarısız veya kurulumu eksik bir sonuç “geçti” gösterilmez.
- **Tarayıcıyı kullanma:** Ajanlar uygulamayı ayrı ve temiz bir tarayıcıda açabilir; düğmeye tıklar, alan doldurur, tuş gönderir, görünür sonucu doğrular, JavaScript/HTTP hatalarını ve gerçek ekran görüntüsünü alır. Oyunlarda durunca görüntünün sabit kaldığı, devam edince hareket ettiği de sınanabilir. Bu kontrolün dış ağ erişimi kapalıdır; gerçek kullanıcı tarayıcı profili kullanılmaz.
- **Windows uygulamasını kullanma:** Bu projeden yeni üretilmiş paket EXE'si açılır. Windows UI Automation ile yalnız o pencereye tıklanabilir, alan doldurulabilir, görünen sonuç ve pencere görüntüsü alınabilir. Kurulu başka uygulamalar bu araçla kontrol edilmez. Yeni uygulamanın test verileri UC_AI_TEST_MODE / UC_AI_TEST_PROFILE üzerinden ayrılmalıdır. Desteklenmeyen denetimler veya görüntü alma sorunları hata olarak bildirilir.
- **Kaynak sürümleri:** Her çalışma öncesi ve sonrası SHA256 ile doğrulanmış kaynak kaydı tutulur. Sağdaki **Sürümler** bölümünde farkı görüp önceki sürüme dönebilirsin. Mevcut kod ayrıca güvenlik kaydına alınır; sonradan eklenen kaynak dosyalar kalıcı silinmeden kurtarma alanına taşınır. Canlı veri, veritabanı, gizli dosya ve bağımlılık önbellekleri sürüm işlemi dışındadır. Kayıt sınırı 256 MB / 5000 kaynak dosyasıdır; aşılırsa değişiklikten önce durulur.
- **Derleme ve paket:** Statik web ZIP'i, npm build/test, .NET build/test/publish ve Python sözdizimi/pytest/PyInstaller akışları var. .NET ve Python örneklerinden gerçek Windows EXE paketleri üretilip ZIP'ten çıkarılarak çalıştırıldı. .NET paketi uygun .NET çalışma zamanı gerektirir. Python EXE paketleyicisi yalnız bu yazılımın özel klasörüne kuruldu.
- **SDK kontrolü:** Node, Python, .NET, tarayıcı, Godot/Unity ve Android araçları tanınır. Her platformun bütün SDK'ları kurulu değildir; gereken proje türünde eksik olan araç açıkça belirtilir. Büyük SDK'lar sessizce indirilmez ve kurulmuş gibi gösterilmez.

Ajanların araçları: development_inspect_project, development_checkpoint_project, development_browser_check, development_desktop_check, development_project_action. Bunlar motorun gerçek MCP araçlarıdır. Normal sohbetin bu araçlara izni yoktur.

Çalışma alanındaki **Kontroller** sekmesinde gerçek sonuçlar, ekran görüntüleri ve hazır paket indirme düğmesi vardır. Kontrol tarifi studio-checks.json dosyasında web için steps, Windows için desktop.steps altında tutulur. Düzeltme sırasında kabul adımları sabit tutulur; testin silinmesiyle hata gizlenmez.

Canlı örnek: Mini Uzay Oyunu'na Nemotron tarafından duraklat/devam düğmesi eklendi. Gizli düğme gerçek tarayıcı kontrolünde bulundu, otomatik düzeltmeye gönderildi ve düzeltildi. Gerçek tıklama, sabit görüntü ve yeniden hareket kontrolleri geçti; dağıtım ZIP'i üretildi.

## Kullanım

- **Yeni sohbet:** Proje seçmeden konuş. Yazı veya görsel gönder. Başlangıç modeli Nemotron; alttaki listeden değiştirebilirsin.
- **Yeni çalışma:** Adını yaz, klasör otomatik oluşur. Mevcut uygulaman için “Mevcut uygulama klasörünü kullan” seçeneğini işaretle.
- **Model listesi:** Tek model veya **Üçlü ekip** seç. Çalışmalarda başlangıç seçimi üçlü ekiptir. Model kendiliğinden değiştirilmez.
- **Görsel:** + düğmesiyle ekle, sürükle veya panodan yapıştır. PNG/JPG/WebP; en fazla dört görsel, tek dosya 4 MB, toplam 8 MB. GLM 5.3 yalnız metin alır.
- **Sol kenar:** Eski sohbet ve çalışmayı seçip devam et. Arama, ad değiştirme, arşivleme ve geri alma vardır.
- **Sağ panel:** Dosyaları incele, kaynak klasörünü aç veya projeyi ZIP olarak indir. Web uygulama ve oyunlarını Önizleme bölümünde çalıştır. Paket veya sunucu gerektiren projelerde çalıştırma adımları sohbetten izlenir.
- **İşlemler:** Ajan ve terminal işlemlerinin gerçek çıktıları görünür. İzin ve soruları sohbet içindeki düğmelerden yanıtla. Durdur süren isteği iptal eder.
- **⋯ menüsü:** Adını değiştir, sohbeti JSON olarak indir veya arşivle. Arşivleme proje dosyalarını silmez.

Örnek: “Bu görsele benzer, ok tuşlarıyla oynanan bir uzay oyunu oluştur. Dosyaları gerçekten yaz. Gereksiz test yapma.”

## Son gerçek model kontrolü — 18 Ekim 2026

| Model | Durum |
|---|---|
| DeepSeek V4.1 Flash | NVIDIA yanıtı zaman aşımına uğradı. |
| GLM 5.3 | NVIDIA yanıtı zaman aşımına uğradı. |
| NVIDIA Nemotron 3.5 Super VL | Gerçek yanıt ve uygulamadan görsel tanıma doğrulandı. |
| GLM 5.3 Flash | Ücretsiz NVIDIA uç noktasından gerçek yanıt alındı. |
| Kimi K3 | NVIDIA ücretsiz uç noktayı kaldırmış; seçim kapalı. |

Üçlü ekip DeepSeek koordinatör + GLM geliştirici + Nemotron inceleyici olarak yapılandırılmıştır. Yardımcı görevleri eşzamanlı başlatması istenir; tamamlanma ve zaman aralıkları gerçek araç çıktılarıyla kontrol edilir. Üç modelin tamamıyla canlı geliştirme henüz doğrulanamadı: DeepSeek ve GLM yanıt vermeli. Şu anda **NVIDIA Nemotron** seçilerek sohbet ve tek ajanla geliştirme kullanılabilir. Eksik model gizlenmez; başka sürümle sessizce değiştirilmez.

“Modeller ve bağlantı” son bilinen sonucu gösterir. “Bağlantıları kontrol et” dört kullanılabilir modele birer kısa istek gönderir. Açılışta otomatik kontrol yapılmaz. NVIDIA hizmeti geri geldiğinde buradan yeniden kontrol edebilirsin.

## Yerel çalışma ve kayıtlar

Arayüz, geçmiş, dosyalar ve geliştirme motoru bu bilgisayarda çalışır. Yapay zekâ istekleri NVIDIA NIM'e internetten gider; model ağırlıkları bilgisayara indirilmez. Ücretsiz geliştirici erişimi NVIDIA kotasına ve hizmetine bağlıdır; sınırsız kullanım garantisi yoktur. Ücretli yedek eklenmedi.

Geçmiş `.system/studio-data/studio.sqlite`, projeler `Projeler` içindedir. Var olan klasör seçilirse doğrudan orada çalışılır. Bu klasörü taşımak masaüstü kısayolunu etkiler. Yedeklerken gizli `.system` bölümünü de koru. Anahtar Windows hesabına bağlı DPAPI ile şifrelidir. Klasörün tamamını başkalarıyla paylaşma; yalnız proje ZIP'ini veya sohbet dışa aktarımını paylaş.

Pencere kapanınca motor sonraki açılışa hazır kalır; simge aynı motora bağlanır. Bilgisayar yeniden başladığında simge motoru tekrar başlatır. Otomatik açılışa eklenmedi. Mevcut Python ve Edge/Chrome kullanılır. Terminal isteyenler için eski `Uc-Ajani-Ac.cmd` korunmuştur.

Yerel uygulama yalnız `127.0.0.1` üzerinde rastgele oturum anahtarlarıyla dinler. Gerçek NVIDIA anahtarı geliştirme alt sürecine verilmez. Önizleme ana uygulamadan yalıtılmıştır. Gizli dosyalar dosya listesi/ZIP/önizleme dışında tutulur. Kota, sunucu ve zaman aşımı hatalarında otomatik model tekrarı veya ücretli geçiş yapılmaz.

Kaynaklar: [GLM 5.3 Flash](https://build.nvidia.com/z-ai/glm-5-3-flash), [Kimi K3](https://build.nvidia.com/moonshotai/kimi-k3), [DeepSeek](https://docs.api.nvidia.com/nim/reference/nvidia-deepseek-v4_1-flash).

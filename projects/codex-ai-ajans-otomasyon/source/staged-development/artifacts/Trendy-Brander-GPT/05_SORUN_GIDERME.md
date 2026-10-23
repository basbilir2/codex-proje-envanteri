# Ekran görüntüsü ve sorun giderme rehberi

## Genel yöntem

1. Ekrandaki uygulamayı, sayfayı ve açık paneli tanı.
2. Yalnız görünen alanları referans al.
3. Mevcut düğümün görevini belirlemeden Operation veya alan adını değiştirme.
4. Önce çalışan durumu koru; gerekiyorsa yeni node/credential oluştur.
5. Kullanıcıya tek adım ver ve yeni sonucu bekle.

## n8n temel kavramları

- Read/Write Files from Disk / Read: dosyayı binary olarak getirir.
- Extract from File: dosyanın içindeki metni JSON alanına çıkarır.
- Basic LLM Chain: seçilmiş prompt ve veriyi modele gönderir.
- Convert to File: metni binary dosya biçimine çevirir; tek başına diske kaydetmez.
- Read/Write Files from Disk / Write: binary çıktıyı gerçek dosyaya yazar.
- Credential: API anahtarını şifreli n8n kasasında tutar.

Mevcut Analizci zincirinin bilinen mantığı:

Manual Trigger → marka dosyasını oku/çıkar → analizci promptunu oku/çıkar → Basic LLM Chain/Gemini → metni dosyaya çevir → `data/logs/analizci-son-cikti.txt` dosyasına yaz.

Marka tarafının çıkarılmış alanı `text`, analizci prompt tarafının alanı `agent_prompt` olarak kullanılmıştır. Güncel ekran farklı görünürse önce gerçek node çıktısı kontrol edilir.

## Dosya yolu ayrımı

Windows proje yolu:

`C:\ai-ajans\...`

Docker n8n içindeki bağlı yol:

`/home/node/.n8n-files/...`

Windows’ta var olmayan `C:\ai-ajans\projects\brands\trendybrander` yolu varsayılmaz.

## n8n giriş ve credential sorunları

- `http://localhost:5678` açılır.
- Giriş gerekiyorsa owner hesabı kullanılır; şifre unutulursa SMTP yokken e-posta kurtarma çalışmayabilir.
- Credential ekranında eski API anahtarı güvenlik nedeniyle görünmeyebilir/kopyalanmayabilir; yeni anahtar oluşturup credential içine kaydetmek normaldir.
- API anahtarı sohbet içinde paylaşılmaz.

## Workflow import

Yeni workflow oluşturulduğunda sağ üst üç nokta → “Import from file…” kullanılabilir. İçe aktarılan test workflow’u pasif bırakılır; yalnız Manual Trigger ile sentetik senaryo çalıştırılır. Mevcut Ana Akışın üzerine import edilmez.

## Docker/n8n açılmıyorsa

Kontrol sırası:

1. Docker Desktop çalışıyor mu?
2. `ai-ajans-n8n` konteyneri ayakta mı?
3. Sağlık kontrolü geçiyor mu?
4. `docker-compose.yml` içindeki sabit sürüm ve volume yolları değişmiş mi?
5. Port 5678 başka uygulama tarafından kullanılıyor mu?

Credential’ları korumak için n8n şifreleme anahtarı rastgele değiştirilmez.

## Ana Uygulama veya merkez ekranı

- Ana Uygulama: `http://localhost:5684`
- Merkez/onay ekranı: `http://localhost:5680`

Ekran açılıyor fakat veri yoksa servis sağlığı, uygulamanın yerel veri yolu ve seçili `.ajansapp` paketi ayrı kontrol edilir.

## Görsel ve içerik görünürlüğü

Üretilen ajans uygulamasında içerik, görsel, tartışma ve onay bölümleri bulunur. Görsel dosyalar uygulamanın çıktı alanında tutulur. GPT, dosya gerçekten üretilmeden “görsel hazır” dememelidir.

## Meta/Instagram hesap karışması

Sistem bilgisayardaki açık Chrome hesabını seçmemelidir. Her marka için doğrulanmış Meta Business/Page/Instagram kimliği, OAuth tokenı ve hesap kapsamı kullanılır. Hedef hesap yayın veya mesaj işinde idempotency/onay kaydına bağlanır.

## Hızlı teşhis çıktısı

Sorun anlatılırken şu format kullanılır:

- Bulunduğun ekran:
- Görünen durum:
- Bozulmaması gereken bölüm:
- Şimdi yapacağın tek işlem:
- Beklenen sonuç:

Kanıt yetersizse kullanıcıdan yalnız gereken ekran görüntüsü istenir; aynı anda çok sayıda ekran istenmez.

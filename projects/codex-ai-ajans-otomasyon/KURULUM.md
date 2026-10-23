# Yeniden kurma

1. Bu depoyu ayrı bir klasöre klonlayın. `source` altındaki gerekli sürüm kopyasını seçin; farklı projeleri veya sürümleri üst üste yazmayın.
2. [BAGIMLILIKLAR.json](reconstruction/BAGIMLILIKLAR.json) içindeki framework ve sürümlere uygun araçları kurun. Var olan kilit dosyalarını kullanın.
3. [EKSİKLER.md](EKSIKLER.md) içindeki harici model, boş veri şablonu ve kurucu payload adımlarını tamamlayın. Gizli değerleri aşağıdaki ortam değişkenleri/yerel konfigürasyon üzerinden yeni ortamda sağlayın.
4. Aşağıdaki komutlar manifestlerden türetilmiştir; bu arşivleme sırasında çalıştırılmış ve başarılı olmuş sayılmaz. Dağıtım/deploy komutları canlı kaynakları etkileyebilir; kaynak incelemesi tamamlanmadan çalıştırmayın.
5. İlgili mevcut testleri çalıştırın; ardından boş kullanıcı verisiyle başlatma, kapat/aç ve hedef platform kurulumunu doğrulayın.

## Manifestlerden alınan komutlar

Otomatik derleme manifesti bulunamadı. Betiklerin platform/uygulama bağımlılıkları kendi kaynaklarında ve mevcut teknik notlarda yer alır.

## Ortam değişkenleri

- `ADMIN_DATA_ROOT`
- `ADMIN_ENCRYPTION_KEY`
- `AI_AJANS_ROOT`
- `ALLOW_LEGACY_RUNTIME_KEY`
- `ALLOW_SYNTHETIC_ACCOUNTS`
- `ALLOW_SYNTHETIC_EVIDENCE`
- `APPROVAL_HMAC_KEY`
- `APP_ROOT`
- `BRAND_DATA_ROOT`
- `CENTER_API_KEY`
- `CREDENTIAL_ENCRYPTION_KEY`
- `DATA_ROOT`
- `DB_PATH`
- `GENERATED_IMAGE_ROOT`
- `HOST`
- `LEASE_SECONDS`
- `LOCAL_DELIVERY_ROOT`
- `MIN_FREE_BYTES`
- `N8N_SERVICE_API_KEY`
- `OPERATOR_PASSWORD_HASH`
- `PORT`
- `REFERENCE_ROOT`
- `RUNTIME_API_KEY`
- `RUNTIME_FILE`
- `RUNTIME_URL`
- `SCHEDULER_API_KEY`
- `WORKER_API_KEY`
- `WORKSPACE_ROOT`

## Kurucu payload

.NET Setup projeleri `Payload/*.exe` gömüyorsa önce ana uygulamayı publish edin, üretilen dosyayı `.csproj` içinde yazan tam Payload adına kopyalayın, ardından Setup projesini publish edin. Kaynak uygulamanın lisans ve mevcut kurulum kuralları korunur.

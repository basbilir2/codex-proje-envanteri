# Yeniden kurma

1. Bu depoyu ayrı bir klasöre klonlayın. `source` altındaki gerekli sürüm kopyasını seçin; farklı projeleri veya sürümleri üst üste yazmayın.
2. [BAGIMLILIKLAR.json](reconstruction/BAGIMLILIKLAR.json) içindeki framework ve sürümlere uygun araçları kurun. Var olan kilit dosyalarını kullanın.
3. [EKSİKLER.md](EKSIKLER.md) içindeki harici model, boş veri şablonu ve kurucu payload adımlarını tamamlayın. Gizli değerleri aşağıdaki ortam değişkenleri/yerel konfigürasyon üzerinden yeni ortamda sağlayın.
4. Aşağıdaki komutlar manifestlerden türetilmiştir; bu arşivleme sırasında çalıştırılmış ve başarılı olmuş sayılmaz. Dağıtım/deploy komutları canlı kaynakları etkileyebilir; kaynak incelemesi tamamlanmadan çalıştırmayın.
5. İlgili mevcut testleri çalıştırın; ardından boş kullanıcı verisiyle başlatma, kapat/aç ve hedef platform kurulumunu doğrulayın.

## Manifestlerden alınan komutlar

### source/current/app/package.json

Bu dosyanın klasöründe çalıştırılır.

```text
npm ci
npm run start    # node server.mjs
npm run test    # node --test tests/*.test.mjs
```

### source/current/on-kontrol/recovery-before-20261022/app/package.json

Bu dosyanın klasöründe çalıştırılır.

```text
npm install
npm run start    # node server.mjs
```

### source/current/training/pilot-20261022/upstream/pyproject.toml

Manifestin Python sürüm sınırına uygun ayrı ortamda, bu dosyanın klasöründe:

```text
python -m venv .venv
.venv\Scripts\python -m pip install -e .
```

Tanımlı giriş noktaları: {}

## Ortam değişkenleri

- `DIFFSYNTH_DOWNLOAD_SOURCE`
- `DIFFSYNTH_MODEL_BASE_PATH`
- `DIFFSYNTH_SKIP_DOWNLOAD`
- `LOCAL_WS_SERVER_PORT`
- `MODELSCOPE_DOMAIN`
- `MODELSCOPE_ENDPOINT`
- `NODE_ENV`
- `NO_PROXY`
- `RECOVERY_PORT`
- `RECOVERY_TEST_PYTHON`
- `SSLKEYLOGFILE`
- `SWANLAB_PROJECT`
- `TEST_WITH_INTERNET`
- `TEST_WITH_PROXY`
- `USERPROFILE`
- `WANDB_PROJECT`
- `WEBSOCKET_CLIENT_CA_BUNDLE`

## Kurucu payload

.NET Setup projeleri `Payload/*.exe` gömüyorsa önce ana uygulamayı publish edin, üretilen dosyayı `.csproj` içinde yazan tam Payload adına kopyalayın, ardından Setup projesini publish edin. Kaynak uygulamanın lisans ve mevcut kurulum kuralları korunur.

## Özel eğitim çıktıları

Özel eğitilmiş checkpoint dosyaları mimariden birebir yeniden üretilemez. `reconstruction/OWN_MODEL_ASSETS.json` dosyasındaki dosyalar gizli arşivde korunur; bu herkese açık depoya dahil değildir. İndirip `restore_path` yoluna koyun ve SHA256 değerini doğrulayın. Bu not yükleme yapıldığını kanıtlamaz; GitHub teslim raporunda doğrulama aranmalıdır.

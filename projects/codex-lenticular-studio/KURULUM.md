# Yeniden kurma

1. Bu depoyu ayrı bir klasöre klonlayın. `source` altındaki gerekli sürüm kopyasını seçin; farklı projeleri veya sürümleri üst üste yazmayın.
2. [BAGIMLILIKLAR.json](reconstruction/BAGIMLILIKLAR.json) içindeki framework ve sürümlere uygun araçları kurun. Var olan kilit dosyalarını kullanın.
3. [EKSİKLER.md](EKSIKLER.md) içindeki harici model, boş veri şablonu ve kurucu payload adımlarını tamamlayın. Gizli değerleri aşağıdaki ortam değişkenleri/yerel konfigürasyon üzerinden yeni ortamda sağlayın.
4. Aşağıdaki komutlar manifestlerden türetilmiştir; bu arşivleme sırasında çalıştırılmış ve başarılı olmuş sayılmaz. Dağıtım/deploy komutları canlı kaynakları etkileyebilir; kaynak incelemesi tamamlanmadan çalıştırmayın.
5. İlgili mevcut testleri çalıştırın; ardından boş kullanıcı verisiyle başlatma, kapat/aç ve hedef platform kurulumunu doğrulayın.

## Manifestlerden alınan komutlar

### source/current/.deps/depth-anything-3/da3_streaming/requirements.txt

```text
python -m pip install -r requirements.txt
```

### source/current/.deps/depth-anything-3/pyproject.toml

Manifestin Python sürüm sınırına uygun ayrı ortamda, bu dosyanın klasöründe:

```text
python -m venv .venv
.venv\Scripts\python -m pip install -e .
```

Tanımlı giriş noktaları: {"da3": "depth_anything_3.cli:app"}

### source/current/.deps/depth-anything-3/requirements.txt

```text
python -m pip install -r requirements.txt
```

### source/current/.studio/code-backups/animation-e68e4e3296fe4ce085eeb4b2343ca944/pyproject.toml

Manifestin Python sürüm sınırına uygun ayrı ortamda, bu dosyanın klasöründe:

```text
python -m venv .venv
.venv\Scripts\python -m pip install -e .
```

Tanımlı giriş noktaları: {"lenticular": "lenticular.cli:main", "lenticular-studio": "lenticular.studio:main"}

### source/current/outputs/surface-upgrade-20261009-220345/backup/pyproject.toml

Manifestin Python sürüm sınırına uygun ayrı ortamda, bu dosyanın klasöründe:

```text
python -m venv .venv
.venv\Scripts\python -m pip install -e .
```

Tanımlı giriş noktaları: {"lenticular": "lenticular.cli:main", "lenticular-studio": "lenticular.studio:main"}

### source/current/pyproject.toml

Manifestin Python sürüm sınırına uygun ayrı ortamda, bu dosyanın klasöründe:

```text
python -m venv .venv
.venv\Scripts\python -m pip install -e .
```

Tanımlı giriş noktaları: {"lenticular": "lenticular.cli:main", "lenticular-studio": "lenticular.studio:main"}

### source/current/requirements-depth.txt

```text
python -m pip install -r requirements-depth.txt
```

### source/current/requirements-quality.txt

```text
python -m pip install -r requirements-quality.txt
```

## Ortam değişkenleri

- `BLENDER_PATH`
- `CUDA_VISIBLE_DEVICES`
- `DA3_BACKEND_API_KEY`
- `DA3_GALLERY_DIR`
- `DA3_LOG_LEVEL`
- `DA3_MODEL_DIR`
- `DA3_WORKSPACE_DIR`

## Kurucu payload

.NET Setup projeleri `Payload/*.exe` gömüyorsa önce ana uygulamayı publish edin, üretilen dosyayı `.csproj` içinde yazan tam Payload adına kopyalayın, ardından Setup projesini publish edin. Kaynak uygulamanın lisans ve mevcut kurulum kuralları korunur.

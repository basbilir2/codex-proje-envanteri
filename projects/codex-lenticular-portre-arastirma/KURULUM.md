# Yeniden kurma

1. Bu depoyu ayrı bir klasöre klonlayın. `source` altındaki gerekli sürüm kopyasını seçin; farklı projeleri veya sürümleri üst üste yazmayın.
2. [BAGIMLILIKLAR.json](reconstruction/BAGIMLILIKLAR.json) içindeki framework ve sürümlere uygun araçları kurun. Var olan kilit dosyalarını kullanın.
3. [EKSİKLER.md](EKSIKLER.md) içindeki harici model, boş veri şablonu ve kurucu payload adımlarını tamamlayın. Gizli değerleri aşağıdaki ortam değişkenleri/yerel konfigürasyon üzerinden yeni ortamda sağlayın.
4. Aşağıdaki komutlar manifestlerden türetilmiştir; bu arşivleme sırasında çalıştırılmış ve başarılı olmuş sayılmaz. Dağıtım/deploy komutları canlı kaynakları etkileyebilir; kaynak incelemesi tamamlanmadan çalıştırmayın.
5. İlgili mevcut testleri çalıştırın; ardından boş kullanıcı verisiyle başlatma, kapat/aç ve hedef platform kurulumunu doğrulayın.

## Manifestlerden alınan komutlar

### source/archive-snapshots/research/work/studio-fixes-20261011/retired-projects-unique.zip-source/lenticular/requirements.txt

```text
python -m pip install -r requirements.txt
```

### source/archive-snapshots/research/work/studio-fixes-20261011/retired-projects-unique.zip-source/lenticular2/lenticular2/pyproject.toml

Manifestin Python sürüm sınırına uygun ayrı ortamda, bu dosyanın klasöründe:

```text
python -m venv .venv
.venv\Scripts\python -m pip install -e .
```

Tanımlı giriş noktaları: {"lenticular2": "lenticular2.cli:main"}

### source/archive-snapshots/research/work/studio-fixes-20261011/retired-projects-unique.zip-source/lenticular2/lenticular2/requirements.txt

```text
python -m pip install -r requirements.txt
```

## Ortam değişkenleri

Kaynakta otomatik çıkarılabilen ortam değişkeni yok. Yerel konfigürasyon gereksinimleri kaynakta ayrıca incelenmelidir.

## Kurucu payload

.NET Setup projeleri `Payload/*.exe` gömüyorsa önce ana uygulamayı publish edin, üretilen dosyayı `.csproj` içinde yazan tam Payload adına kopyalayın, ardından Setup projesini publish edin. Kaynak uygulamanın lisans ve mevcut kurulum kuralları korunur.

# Yeniden kurma

1. Bu depoyu ayrı bir klasöre klonlayın. `source` altındaki gerekli sürüm kopyasını seçin; farklı projeleri veya sürümleri üst üste yazmayın.
2. [BAGIMLILIKLAR.json](reconstruction/BAGIMLILIKLAR.json) içindeki framework ve sürümlere uygun araçları kurun. Var olan kilit dosyalarını kullanın.
3. [EKSİKLER.md](EKSIKLER.md) içindeki harici model, boş veri şablonu ve kurucu payload adımlarını tamamlayın. Gizli değerleri aşağıdaki ortam değişkenleri/yerel konfigürasyon üzerinden yeni ortamda sağlayın.
4. Aşağıdaki komutlar manifestlerden türetilmiştir; bu arşivleme sırasında çalıştırılmış ve başarılı olmuş sayılmaz. Dağıtım/deploy komutları canlı kaynakları etkileyebilir; kaynak incelemesi tamamlanmadan çalıştırmayın.
5. İlgili mevcut testleri çalıştırın; ardından boş kullanıcı verisiyle başlatma, kapat/aç ve hedef platform kurulumunu doğrulayın.

## Manifestlerden alınan komutlar

### source/converter-development/working/converter-check/converter-check.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/early-development/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/early-development/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.4/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.4/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.7/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.7/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.8/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.8/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.0/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.0/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.1/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.1/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.12/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.12/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.15/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.15/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.16/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.16/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.17/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.17/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.18/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.18/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.19/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.19/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.20/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.20/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.21/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.21/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.22/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.22/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.23/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.23/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.24/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.24/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.25/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.25/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.26/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.26/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.27/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.27/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.28/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.28/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.29/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.29/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.3/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.3/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.30/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.30/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.32/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.32/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.4/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.4/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.40/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.40/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.42/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.42/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.5/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.5/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.6/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.6/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.7/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.7/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/embedded-snapshots/BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/versions-and-development/work/btakip-cloud-input-1.5.34/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/versions-and-development/work/btakip-cloud-input-1.5.34/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/versions-and-development/work/btakip-stock-1.5.43/BTakip.Setup/BTakip.Setup.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

### source/versions-and-development/work/btakip-stock-1.5.43/BTakip/BTakip.csproj

Hedef framework: `net10.0-windows`. Proje klasöründe:

```text
dotnet restore
dotnet build -c Release
dotnet publish -c Release -r win-x64 --self-contained true
```

## Ortam değişkenleri

- `BTAKIP_DATA_DIR`

## Kurucu payload

.NET Setup projeleri `Payload/*.exe` gömüyorsa önce ana uygulamayı publish edin, üretilen dosyayı `.csproj` içinde yazan tam Payload adına kopyalayın, ardından Setup projesini publish edin. Kaynak uygulamanın lisans ve mevcut kurulum kuralları korunur.

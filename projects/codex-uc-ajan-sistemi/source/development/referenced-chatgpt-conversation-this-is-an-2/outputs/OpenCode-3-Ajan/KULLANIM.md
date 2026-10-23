# OpenCode – Üç ajan

Yeni bağımsız terminal sürümü [Uc-Ajan-Sistemi](../Uc-Ajan-Sistemi/OKU.md) klasöründedir. Masaüstündeki `Uc AI Terminal` kısayolunu kullan. Aşağıdaki talimatlar önceki proje sürükleme başlatıcısına aittir.

Kurulum: OpenCode 1.19.3. Model ve endpoint kimlikleri 17 Ekim 2026 tarihinde NVIDIA'nın canlı `/v1/models` listesinden doğrulandı.

| Ajan | Model | Görev |
| --- | --- | --- |
| deepseek | deepseek-ai/deepseek-v4.1-flash | Ana geliştirici ve orkestratör |
| glm | z-ai/glm-5.3 | İkinci geliştirici |
| nemotron | nvidia/nemotron-3.5-super-vl-120b-a12b | İnceleme ve test; dosya düzenleme kapalı |

## Açma

1. NVIDIA Build hesabınıza giriş yapın. NVIDIA isterse Cloud Account ve telefon/SMS doğrulamasını tamamlayın; sonra **Generate API Key** ile bir anahtar oluşturun.
2. `NVIDIA-Anahtarini-Kaydet.cmd` dosyasını açın. Gerçek `nvapi-…` anahtarını kutuya yapıştırıp Kaydet'e basın. Örnek Python kodunu yapıştırmayın.
3. `Baglanti-Testi.cmd` bağlantıyı ve gerçek OpenCode paralel ajan çalışmasını test eder.
4. `OpenCode-Ac.cmd` bu çalışma klasörünü açar. Başka projede kullanmak için proje klasörünü bu dosyanın üzerine sürükleyin.

PowerShell ile belirli bir proje:

```powershell
.\Start-OpenCode.ps1 -ProjectPath 'C:\Projem'
```

Başlangıç görevi örneği: “Bu özelliği üç ajanla geliştir. GLM'ye ayrı dosyaları ver, Nemotron mevcut davranışı ve testleri incelesin. Görevleri paralel başlat, sonuçları birleştirip gerekli testleri çalıştır.”

Basit işler tek ajanla yapılabilir. GLM ve Nemotron `@glm` / `@nemotron` ile de çağrılabilir. Üç modele istek gitmesi gerçek test raporuyla doğrulanmadan bağlantı başarılı sayılmaz.

## Mevcut projeyi koruma

Bu sohbet bir uygulama deposuna bağlı değil; ayrı kurulum paketi hazırlandı. Hiçbir mevcut uygulamanın kodu, kurulumu veya canlı verisi değiştirilmedi. Başlatıcı hedef projeye yapılandırma kopyalamaz; yalnız açtığı süreçte `OPENCODE_CONFIG` kullanır. Projenin mevcut ayarlarıyla OpenCode'un normal birleştirme kuralları geçerlidir. İstenen ajanlar ve sağlayıcı bu oturumda seçilir; başka sağlayıcıya otomatik geçiş kapalıdır.

GLM ve DeepSeek'e aynı dosyada eşzamanlı yazma görevi verilmez. Nemotron dosya değiştiremez. Okuma/düzenleme, proje içindeki olağan geliştirme için açıktır. Kabukta ilgili test/derleme ve Git inceleme komutları açıktır; diğer komutlar onay ister. Bu, OpenCode'un proje korumasıdır; komut desenleri tam bir işletim sistemi güvenlik sınırı oluşturmaz.

## Anahtar ve ortam

Gerçek anahtar bu pakete veya `.env` dosyasına yazılmaz. Windows DPAPI ile şifrelenip bu sohbetin `work/secrets/nvidia-key.dpapi` dosyasında tutulur. Yalnız aynı Windows kullanıcısı çözer. Başlatıcı anahtarı süreç içinde `NVIDIA_API_KEY` değişkenine yükler. Önceden tanımlı NVIDIA/NIM anahtarları da kullanılabilir. `.env.example` yalnız başvuru dosyasıdır; otomatik okunmaz.

OpenCode çalışma dosyaları bu sohbetin `work/runtime` klasöründedir. Bu paketi tek başına başka yere taşırsanız başlatıcı yeni konumda runtime'ı kurabilir; şifreli anahtarı yeniden kaydetmeniz gerekir. Başka bir genel OpenCode kurulumu veya PATH ayarı değiştirilmedi.

## Doğrulama

```powershell
.\Start-OpenCode.ps1 -Validate
.\Start-OpenCode.ps1 -Test
```

`-Validate`: gerçek OpenCode yapılandırma çözümlemesi, üç modelin tanınması, promptlar ve yerel sahte sunucu üzerinde iki alt ajanın gerçekten örtüşen zamanda çalışması. **Bu yerel test NVIDIA bağlantısını kanıtlamaz.**

`-Test`: yukarıdakilere ek olarak üç NVIDIA modeline paralel kısa istekler; başarılıysa DeepSeek'in gerçek GLM/Nemotron alt oturumlarını başlattığı, doğru model kimliklerini kullandığı ve görevlerin zamanlarının örtüştüğü kontrol edilir. Testler uygulama kodundan ayrı `work/smoke` klasöründe, düzenleme ve kabuk erişimi kapalı olarak yürür. Sonuçlar `reports/` altında tutulur. Eksik anahtar, 401/402/403/404/429 ve başarısız test başarılı gibi raporlanmaz.

## Ücretsiz erişim ve kaynaklar

NVIDIA üç modelin sayfasında ücretsiz prototip endpoint'i sunuyor. Bu erişimin hesap yetkisi, kota ve hizmet kullanılabilirliğiyle sınırlı olması mümkündür; sınırsızlık veya kalıcı ücretsiz erişim garantisi verilmez. Ücretli partner sağlayıcı kurulmadı. Model kaldırılırsa sessizce başka sürüme geçilmez.

- [DeepSeek V4.1 Flash](https://build.nvidia.com/deepseek-ai/deepseek-v4.1-flash)
- [GLM 5.3](https://build.nvidia.com/z-ai/glm-5-3)
- [Nemotron 3.5 Super](https://build.nvidia.com/nvidia/nemotron-3.5-super-vl-120b-a12b)
- [OpenCode ajanlar](https://opencode.ai/docs/agents/)
- [OpenCode sağlayıcılar](https://opencode.ai/docs/providers/)

Bu paket kurulu **V1** komutuyla doğrulandı; `agent`, `provider`, `permission` V1 alanları kullanılır. V2 örneklerindeki `agents`, `providers`, `permissions` alanlarını bu pakete doğrudan taşımayın.

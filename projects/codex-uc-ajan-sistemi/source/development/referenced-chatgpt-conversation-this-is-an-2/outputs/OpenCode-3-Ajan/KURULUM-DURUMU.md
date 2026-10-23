# Kurulum durumu – 17 Ekim 2026

OpenCode 1.19.3 kuruldu. DeepSeek ana geliştirici/orkestratör, GLM ikinci geliştirici ve Nemotron reviewer/test ajanı olarak tanımlandı. Ajan promptları, ortam yükleme, başlatıcı ve bağlantı testi hazır.

NVIDIA hesabına giriş ve telefon doğrulaması tamamlandı. `OpenCode-3-Ajan` adlı NVIDIA NIM anahtarı oluşturuldu; son kullanma tarihi 17 Ekim 2027. Anahtar Windows DPAPI ile şifreli saklanıyor. Gerçek anahtar yapılandırmada veya raporlarda bulunmuyor.

| Kontrol | Sonuç |
| --- | --- |
| OpenCode yapılandırma ve prompt çözümlemesi | Geçti |
| Üç modelin NVIDIA kataloğunda bulunması | Geçti |
| OpenCode'un iki alt ajanı aynı anda başlatması | Yerel sahte sunucu testi geçti |
| Nemotron gerçek NVIDIA yanıtı | Geçti; istenen NEMOTRON_OK yanıtı alındı |
| DeepSeek V4.1 gerçek NVIDIA yanıtı | Başarısız; zaman aşımı |
| GLM 5.3 gerçek NVIDIA yanıtı | Başarısız; zaman aşımı |
| Üç modelle gerçek OpenCode paralel iş akışı | Doğrulanamadı; DeepSeek/GLM bağlantı kontrolü geçmedi |

İlk denemede üç modele paralel normal istek gönderildi. Nemotron 1,17 saniyede yanıtladı; DeepSeek ve GLM 180 saniyelik süre sınırına takıldı. İkinci denemede akışlı yanıt kullanıldı; DeepSeek için düşük sayısal reasoning effort, GLM için low ve clear_thinking test ayarları uygulandı. Nemotron yeniden başarılı oldu; diğer iki istek 60 saniyelik bağlantı/okuma zaman aşımına takıldı. Bu gözlem genel bir NVIDIA kesintisi veya modelin kalıcı olarak kullanılamaz olduğunun kanıtı değildir.

**Üçlü sistem çalışıyor diye teslim edilmedi.** Doğru model kimlikleri korundu; başka sürüme veya ücretli sağlayıcıya geçilmedi. NVIDIA tarafında yanıt alınabildiğinde `Baglanti-Testi.cmd` üç bağlantıyı tekrar kontrol eder; üçü de geçerse gerçek OpenCode alt ajan oturumlarını da sınar.

Hiçbir mevcut uygulamanın kodu, kurulumu veya canlı verisi değiştirilmedi. Bu sohbet bir uygulama deposuna bağlı olmadığı için kurulum bu sohbetin klasöründe hazırlandı. `OpenCode-Ac.cmd` dosyasının üzerine bir proje klasörü sürüklenerek o projede kullanılabilir; başlangıç sırasında hedef proje yapılandırması üzerine dosya yazılmaz.

NVIDIA anahtar listesinde ayrıca iki `NVIDIABuild-Autogen-*` anahtarı bulunuyor. Bu kurulum yalnız `OpenCode-3-Ajan` anahtarını kullanır; diğer anahtarlar silinmedi.

- [Son gerçek test raporu](reports/live-verification.json)
- [Kullanım](KULLANIM.md)
- [NVIDIA DeepSeek API](https://docs.api.nvidia.com/nim/reference/nvidia-deepseek-v4_1-flash-infer)
- [NVIDIA GLM API açıklaması](https://docs.api.nvidia.com/nim/reference/z-ai-glm-5-3)

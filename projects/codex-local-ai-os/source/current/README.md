# Local AI OS

Teknik bilgi gerektirmeyen Windows uygulaması `release/LocalAIOS.exe` olarak üretilir.

İlk açılışta **Yapay zekâyı hazırla** düğmesine basılır. Uygulama yerel motoru ve modeli kendi indirir; sonraki kullanımlar çevrimdışıdır. **Bilgi ekle** ile web bağlantıları yerel hafızaya alınabilir. **Güncellemeler** alanı ortak bir güncelleme bağlantısından yeni bilgi paketlerini algılar ve yüklemeden önce kullanıcıdan izin ister.

**Mod** düğmesinden Hızlı, Dengeli veya En güçlü çalışma seçilir. Dengeli mod günlük kullanım için önerilir; basit selamlaşmalar anında yanıtlanır, zor isteklerde daha derin çalışma otomatik açılır. Uzun bir işi beklemek istemezseniz **Durdur** düğmesine basabilirsiniz.

Uygulama gerektiğinde internette otomatik araştırma yapar; tüm sayfayı saklamak yerine kaynak yolunu, öğrenme yöntemini ve kısa dersi hatırlar. Eski ve değersiz dersleri zamanla temizler.

Uygulama bilgisayarın RAM miktarına göre uygun yerel modeli otomatik seçer. **Online güç** isteğe bağlıdır: kullanıcı ücretsiz OpenRouter anahtarını bir kez eklerse zayıf donanımlarda zor görevler ücretsiz modellere yönlendirilebilir.

Sohbette “bu konuda yetenek edin” denebilir. Uygulama gereken kaynak yollarını, yeniden öğrenme yöntemini, iş akışını ve kalite kontrollerini bir eklenti tarifi olarak saklar. **Eklentiler** bu yetenekleri yönetir. **Hafıza** kaynak yollarını, dersleri ve yetenekleri başka bilgisayara taşır veya eşitlenen bir klasör üzerinden devam ettirir. Projenin tam teknik bağlamı `docs/PROJECT_CONTEXT.md` dosyasındadır.

## Windows EXE üretimi

```powershell
dotnet publish desktop/LocalAIOS/LocalAIOS.csproj -c Release -o release
```

---

## Arşivlenmiş komut satırı MVP'si

Laptopta çalışan tek bir yerel modeli; beceri, araç, hafıza ve doğrulama katmanlarıyla kullanan ilk sürüm.

## Gerekenler

- Node.js 20+
- Ollama
- Ollama içinde en az bir yerel model

## Çalıştırma

```powershell
npm start -- "Bu projeyi incele ve hatayı düzelt"
```

Başka bir klasörde çalıştırmak için:

```powershell
npm start -- --workspace C:\projeler\uygulamam "Test hatasını düzelt"
```

Belirli bir model seçmek için:

```powershell
npm start -- --model MODEL_ADI "Projeyi incele"
```

Model belirtilmezse kurulu Ollama modellerinden biri seçilir. Ayarlar `config/default.json` dosyasındadır.

## Bu sürümde olanlar

- Tek Core Model ve kod tabanlı Executive Brain
- Deterministik skill routing
- `software_ai` beceri paketi
- Çalışma alanıyla sınırlı dosya araçları
- İzinli yerel komutlar
- Proje bazlı görev hafızası
- Değişen JavaScript ve JSON dosyalarında temel doğrulama

Bu bölüm yalnız eski `src/` prototipini anlatır; teslim edilen masaüstü uygulaması değildir.

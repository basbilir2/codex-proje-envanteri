# BTakip 1.5.32 — Hızlı Çalışma Bağlamı

Bu dosya yeni sohbette tüm geçmişi okumadan yalnız gerekli kaynaklara gitmek içindir.

## Doğru yollar

| Amaç | Yol |
|---|---|
| Ana kaynak | `C:\Users\USER\.codex\.chatgpt-projects\g-p-6a90780738548191ae5faed84f00ea9f` |
| Ayrıntılı kaynak kopyası | `BTakip_Dijital_Kopya_v1.5.32.json` |
| Kurulu uygulama | `C:\Users\USER\AppData\Local\BTakip\BTakip.exe` |
| Yerel ana klasör | `C:\Users\USER\btakip` |
| Hesaba özel veri | `C:\Users\USER\btakip\Hesaplar\{GoogleUid}\btakip-veri.json` |
| Etkin hesap işareti | `C:\Users\USER\btakip\aktif-bulut-hesabi.txt` |

## İstek türüne göre yalnız bunları oku

- Arayüz, cari, fiyat tanımı: `BTakip/MainForm.cs`
- Fiyat hesabı: `BTakip/PricingEngine.cs`, `BTakip/Models.cs`
- Yerel kayıt, geri alma, hesap ayrımı: `BTakip/DataStore.cs`
- Firestore, Sheets, Drive ve Google girişi: `BTakip/GoogleCloudSyncService.cs`, `BTakip/CloudConfiguration.cs`, `firestore.rules`
- Excel dönüştürme: `BTakip/SimpleXlsx.cs`, `BTakip/ImportedOrderPricing.cs`
- Kurulum: `BTakip.Setup/Program.cs`
- Kesin kaynak metni gerekiyorsa JSON içindeki ilgili `embedded_files[].exact_content` alanı.

## Bulut ve yerel ana yapı

- Firebase projesi: `btakip-trendybrander`.
- İlk canlı hesap: user_0004@example.invalid`.
- Firestore yolu: `users/{uid}/records`. Güvenlik kuralı yalnız giriş yapan kullanıcının aynı `uid` alanını okumasına/yazmasına izin verir.
- Aynı Google hesabı başka bilgisayarda aynı Firestore kayıtlarını indirir.
- Farklı Google hesabı ayrı Firestore alanı ve ayrı `Hesaplar/{uid}` yerel klasörü açar; hesaplar birbirinin verisini göremez.
- Google Sheets'te `BTakip Veri` aynası bulunur: Müşteriler, Fiyat Grupları, Fiyat Tanımları, Siparişler, Tahsilatlar.
- Google Drive'da `BTakip Yedekleri` klasöründe `BTakip-Son.btakip.enc` ve günlük şifreli yedek vardır.
- Yerel veri çevrimdışı çalışır; bağlantı gelince Firestore ile eşitlenir. Oturum anahtarı Windows DPAPI ile korunur.

## Değişmeyecek fiyat kuralları

- Sipariş fiyat grubu müşteri kartındaki `PriceGroupId` değeridir; cari siparişte ayrıca grup seçilmez.
- `UnitCost` müşteriden bağımsızdır. Ürüne özel oran varsa `GroupProfitPercentOverrides[priceGroupId]`, yoksa genel müşteri grubu çarpanı kullanılır.
- Fason standart çarpan 2, sürekli müşteri 2,8, çevre esnafı 3, perakende 4'tür.
- Belirsiz malzeme veya ölçüye fiyat uydurulmaz; alan boş veya `KONTROL:` olarak korunur.
- Kaynak Excel değiştirilmez; gerçek tekrarlar atlanır, benzer fakat farklı hareketler korunur.

## Güvenli çalışma sırası

1. İstekle ilgili yukarıdaki 1-3 dosyayı aç; tüm sohbeti veya tüm JSON'u tarama.
2. Kullanıcı kaldır demeden mevcut özellik kaldırma ve ilgisiz refactor yapma.
3. Canlı mali kaydı değiştirmeden önce BTakip'i kapat, hesaba özel JSON'un sağlam yedeğini al ve yalnız istenen satırı değiştir.
4. Kaynakta sürümü hem `BTakip.csproj` hem `BTakip.Setup.csproj` içinde artır; yeni uygulamayı kurulum payload'ına koy.
5. Yalnız odaklı derleme/smoke ve kurulu sürüm kontrolünü çalıştır.

## 1.5.32 doğrulanan durum

- Sürüm: `1.5.32`.
- Google girişi: External / In production; farklı Google hesapları kullanılabilir. Doğrulamasız hassas kapsam kullanıcı sınırı 100'dür.
- user_0004@example.invalid` ilk bağlantısında 1.126 kayıt Firestore'a gönderildi.
- Yerel hesap, Sheets aynası ve Drive günlük/son şifreli yedek zamanları yazıldı.
- Kritik smoke testi; aynı hesap, farklı hesap ve önceki hesaba dönüş senaryoları dahil başarılıdır.

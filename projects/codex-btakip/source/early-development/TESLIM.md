# BTakip teslim notu

## Kurulum dosyaları

- `dist\BTakip_Setup.exe`: Windows kurulum sürümü.
- `dist\BTakip_Portable.exe`: Kurulum yapmadan çalıştırılabilen sürüm.

Kurulu uygulama: `%LOCALAPPDATA%\BTakip\BTakip.exe`

## 1.5.0 fiyat ve cari düzeltmesi

- Cari ekranında malzeme veya ölçü değişince satış fiyatı, müşteri kartındaki fiyat grubundan otomatik hesaplanır; cari ekranda müşteri grubu ya da kâr oranı seçilmez.
- Ürüne o müşteri grubu için özel kâr tanımlandıysa yalnız o özel oran, yoksa grubun standart oranı kullanılır.
- `m²` ölçüsü doğrudan yazılabilir; cm en × boy veya metre girişleri kendi formülleriyle hesaplanır.
- Hücre değeri değiştirilmeden düzenleme biterse kaydetme onayı gösterilmez. Kaydetme/iptal/hata sonrasında seçili satır ve kolon korunur.
- Cari tablosundaki açıklama kolonu `Açıklamayı göster` seçeneğiyle isteğe bağlı gizlenebilir.

## 1.5.1 Excel dönüşümü ve müşteri notu

- **Excel'i Dönüştür**, çalışma sayfasının `CAR0` gibi genel adı yerine dosya adından temizlenmiş müşteri adını kullanır; kaynak dosya değiştirilmez.
- Dönüşümde tarih, açıklama, malzeme ve ölçü ayrı okunur. Kaynak açıklama `Açıklama` sütunundan, malzeme ise `İsim`/`Ürün` gibi malzeme sütunlarından alınır.
- Eşleşen malzeme ve yeterli ölçü varsa mevcut BTakip fiyat motoru, müşteri kartındaki fiyat grubunu ve o gruba ait ürün özel kârını kullanarak maliyet ve satış borcunu hesaplar. Eşleşmeyen tanım veya hesap için gerekli ölçüsü bulunmayan satır, kaynak bilgisi korunarak önizlemede açıkça işaretlenir.
- Dönüşüm önizlemesi kaynak tutarın yanında motorun maliyetini, satış borcunu ve hesap durumunu gösterir; kullanıcı onayı olmadan gerçek cariye yazılmaz.
- `Müşteriye Not Yolla` düğmesi hem **Müşteriler** hem de **Cari & Tahsilat** ekranında mevcuttur. A4 PDF hesap dökümünü oluşturur, dosyayı açar ve gönderime hazır nazik mesajı panoya kopyalar. `Müşteri Hesabını PDF Al` seçeneği ayrıca korunmuştur.

## Veri ve yedek

- Ana kayıtlar PC'deki `%USERPROFILE%\btakip` klasöründe tutulur.
- Her kayıt işleminden sonra JSON veri dosyası, tarihli yerel yedek ve `BTakip_Yedek_Son.xlsx` güncellenir.
- Excel dışa aktarma ve BTakip/uyumlu cari Excel içe aktarma desteklenir.

## Google senkronizasyonu

- Hesap: user_0004@example.invalid`
- Drive klasörü: `BTakip`
- Google E-Tablo: `BTakip Veri`
- Apps Script projesi: `BTakip Senkronizasyon`
- Uygulama açıkken varsayılan kontrol aralığı 30 saniyedir.
- Yerel kayıt kaydedilince Google'a gönderme hemen denenir.
- Google tablosundaki değişiklikler ana PC'ye çekilir.
- Eşzamanlı farklı değişikliklerde kullanıcıya Google, PC veya iki kaydı da koruma seçeneği sunulur.
- Satırı fiziksel silmek yerine `Silindi` sütununa `TRUE/EVET` yazılır.

## Doğrulanan kritik işlemler

- Uygulama ve kurulum dosyaları açılıyor.
- Müşteri, fiyat, sipariş, cari ve tahsilat kayıt modeli çalışıyor.
- UV, folyo/plotter ve DTF hesapları doğrulandı.
- Her kayıtta yerel JSON ve Excel yedeği oluşuyor.
- Excel içe/dışa aktarma çalışıyor.

## Daha sonra girilecek eksik fiyatlar

Kullanıcıdan fiyatı alınmamış malzeme/baskı/işlemler uygulamadaki **Fiyatlar** ekranından eklenebilir. Mevcut tanımlı fiyatlar teslim bağlamındaki değerlerle başlatılmıştır.

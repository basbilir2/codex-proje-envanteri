# BTakip teslim notu

## Kurulum dosyaları

- `dist\BTakip_Setup.exe`: Windows kurulum sürümü.
- `dist\BTakip_Portable.exe`: Kurulum yapmadan çalıştırılabilen sürüm.

Kurulu uygulama: `%LOCALAPPDATA%\BTakip\BTakip.exe`

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

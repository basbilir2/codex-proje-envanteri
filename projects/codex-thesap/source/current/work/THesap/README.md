# THesap

BTakip'ten bağımsız, yalnız fiyat hesaplama için Windows masaüstü uygulamasıdır.

- Kaynak hesap motoru ve başlangıç kataloğu: BTakip 1.5.35.
- Referans yalnız okunur kullanıldı: `C:\Users\USER\Documents\Codex\2026-09-02\imdi-btakipbin-son-olu-turulan-veriyonuna\work\btakip-cloud-input-1.5.34\BTakip`.
- THesap müşteri, cari, sipariş, Excel, yedek veya Google/bulut verisi içermez; BTakip'in veri klasörlerine erişmez.
- Başlangıç katalog düzenlemesi yoktur. Kurulumda etkin olan canlı BTakip hesabından alınan 34 kalem (27 malzeme, 3 baskı, 4 hizmet) ve fiyatları uygulamaya gömülüdür; THesap sonradan BTakip'e bağlanmaz.

Doğrulama: `THesap.exe --smoke-test` BTakip ile eşdeğer UV, Folyo+Plotter ve DTF eşik hesaplarını kontrol eder.

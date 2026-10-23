# BTakip Google yedeği

Bu dosyalar yalnız yeni oluşturulacak **BTakip Veri** Google çalışma kitabı içindir. Mevcut `Sipariş Takip`, `AnonPerson_0005`, `AnonPerson_0006` veya başka tablolarla bağlantı kurulmaz.

1. Google Drive'da `BTakip` adlı yeni klasör ve içinde `BTakip Veri` adlı yeni Google E-Tablo oluşturun.
2. Çalışma kitabında **Uzantılar → Apps Script** menüsünü açın.
3. `BTakipSync.gs` içeriğini yapıştırın.
4. En az 16 karakterli rastgele bir anahtar seçip Apps Script düzenleyicisinde bir kez `setupBTakip('ANAHTAR')` çalıştırın.
5. **Dağıt → Yeni dağıtım → Web uygulaması** ile dağıtın. Uygulama adresini ve aynı anahtarı BTakip'in **Senkron & Yedek** ekranına yazın.

Tabloda başka bilgisayardan yapılan değişiklikler `onEdit` ile sürümlenir. Ana PC, uygulama açıkken varsayılan olarak 30 saniyede bir değişiklik numarasını kontrol eder; yalnız değişiklik varsa tabloları indirir.

Satırları fiziksel olarak silmek yerine `Silindi` sütununu `TRUE/EVET` yapın. Böylece silme işlemi diğer bilgisayarlara güvenli biçimde yayılır.

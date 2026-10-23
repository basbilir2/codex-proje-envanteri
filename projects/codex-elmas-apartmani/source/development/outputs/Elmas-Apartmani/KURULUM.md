# Elmas Apartmanı V1 — Kurulum ve kullanım

Bu paket bütün yönetici/sakin ekranlarını, Google Apps Script arka ucunu ve yerel önizlemeyi içerir. Canlı sistem user_0006@example.invalid` hesabında oluşturulan gerçek Google Sheet ve Drive klasörüne bağlıdır. Kullanıcılar kayıtlı e-posta ve yönetici tarafından verilen giriş koduyla oturum açar.

## 1. Dosyalar

| Dosya | Apps Script karşılığı |
|---|---|
| apps-script/Code.gs | Code adlı komut dosyası: kurulum, tablolar, yetkili API |
| apps-script/Auth.gs | Auth adlı komut dosyası: Google giriş ve oturum |
| apps-script/Finance.gs | Finance adlı komut dosyası: aidat, ödeme, kasa, işlem günlüğü |
| apps-script/Files.gs | Files adlı komut dosyası: Drive, dekont okuma, PDF makbuz |
| apps-script/Notifications.gs | Notifications adlı komut dosyası: bildirim kanalları |
| apps-script/Index.html | Index adlı HTML dosyası |
| apps-script/Styles.html | Styles adlı HTML dosyası |
| apps-script/Client.html | Client adlı HTML dosyası |
| apps-script/appsscript.json | Proje manifesti |
| preview/ | Yalnız bilgisayar önizlemesi; Google'a yüklemeyin |
| tests/ | Kritik iş kurallarının yerel kontrolü; Google'a yüklemeyin |

## 2. Google projesini oluşturun

1. Yönetici olacak Google hesabıyla [Apps Script](https://script.google.com/) açın ve yeni proje oluşturun.
2. Projeye **Elmas Apartmanı** adını verin.
3. Yukarıdaki `.gs` ve `.html` dosyalarını aynı isimlerle oluşturup içeriklerini kopyalayın. HTML dosyalarının adını girerken uzantıyı editör kendisi ekler.
4. Proje Ayarları'nda manifest dosyasını görünür yapın; `appsscript.json` içeriğini paketle değiştirin.
5. Hizmetler bölümünde **Drive API v3** bulunduğunu doğrulayın. Standart Cloud projesi kullanıyorsanız Cloud Console'da da Google Drive API'yi etkinleştirin.
6. Apps Script editöründeki fonksiyon listesinden **setup** seçip çalıştırın. Google izinlerini proje sahibi olarak tamamlayın.

`setup()` 13 tabloyu, 8 boş daireyi, Drive klasörlerini, başlangıç ayarlarını ve tetikleyicileri oluşturur. Tekrar çalıştırmak mevcut verileri temizlemez. Gerçek projeye örnek borç, sahte sakin veya örnek IBAN eklenmez.

Çalıştırma günlüğünde `sheet` ve `drive` bağlantıları çıkar. Bunlar gerçek Google Sheet ve Drive bağlantılarınızdır. Panelin **Ayarlar → Veriler ve yedekler** bölümünde de gösterilir. Bağlantılar kurulumdan önce mevcut değildir.

## 3. Web App yayınlama

1. **Dağıt → Yeni dağıtım → Web uygulaması** seçin.
2. **Şu kullanıcı olarak çalıştır: Ben / proje sahibi** seçin.
3. Erişim için **Herkes** seçin. Bu, sadece giriş sayfasını erişilebilir kılar; kayıt API'si ayrıca Google kimliği ve Kullanicilar tablosunu kontrol eder.
4. Dağıtımı oluşturup `/exec` ile biten adresi alın.
5. Oluşan Google Sheet'te **Ayarlar** sayfasındaki `WebAppURL` satırına bu adresi yazın. İlk girişten sonra panelden değiştirilebilir.

Sheet ve Drive klasörünü sakinlerle paylaşmayın; bağlantıya sahip herkese açmayın. Sakinler dosyaları yetkili uygulama üzerinden alır. Script düzenleme yetkisini yalnızca güvenilir yöneticiye verin.

Kod güncellendiğinde **Dağıtımları yönet → Düzenle → Yeni sürüm** seçerek mevcut dağıtımı güncelleyin. Böylece `/exec` adresi ve bildirim linkleri korunur.

## 4. Giriş

Yönetici **Ayarlar → Kullanıcılar** ekranından e-posta, rol, daire ve en az 8 karakterli giriş kodu tanımlar. Kullanıcı bu iki bilgiyle giriş yapar. Kod düz metin olarak saklanmaz; e-posta ve proje sırrıyla özetlenerek `Kullanicilar` tablosunda tutulur. Oturum en fazla 6 saattir ve art arda hatalı denemeler geçici olarak sınırlandırılır.

İlk yönetici hesabı user_0006@example.invalid` olarak hazırlanmıştır. Güvenlik için ilk girişten sonra **Ayarlar → Kullanıcılar** bölümünde giriş kodunu değiştirin.

## 5. Yönetici, sakin, IBAN ve aidat

- İlk yönetici `setup()` çalıştıran hesaptır. Kurulumdan önce `ADMIN_EMAIL` betik özelliği girilmişse ilk yönetici bu adres olur.
- **Ayarlar → Kullanıcılar → Ekle:** Ad soyad, e-posta, giriş kodu, rol ve daire seçin. Son aktif yönetici pasifleştirilemez.
- Yönetici değişimi: önce yeni yönetici hesabını ekleyin, yeni hesapla girişi doğrulayın; sonra eski hesabın rolünü değiştirin. Bildirim e-postası ayrı ayardır.
- **Daireler:** Malik, kiracı, iletişim bilgileri ve aktiflik düzenlenir. İletişim e-postası giriş yetkisi oluşturmaz; yetki Kullanıcılar'dan tanımlanır.
- **Ayarlar → IBAN / Banka hesap sahibi:** Gerçek alıcı hesabınızı girin. TR IBAN kontrol basamağı doğrulanır.
- **Ayarlar → Aylık aidat:** Tutarı, oluşturma gününü, son ödeme gününü ve başlangıç tarihini belirleyin. Günler 1–28 aralığındadır.
- **Aidatlar → Aidatları oluştur:** Başlangıç ayından bugüne eksik aidatları oluşturur. Başlangıç tarihi eskiyse geçmiş aylar da o anda tanımlı tutarla oluşturulur; ilk oluşturma öncesi tarihi dikkatle belirleyin.
- Günlük tetikleyici uygun günü geçmiş eksik ayları tamamlar. Mevcut aidatlar tutar değişiminden etkilenmez. Pasif daireye yeni borç oluşturulmaz; eski borcu korunur.

## 6. Dekont ve makbuz akışı

Sakin banka uygulamasından ödeme yapar ve PDF/JPG/PNG yükler. Dosya başına en fazla 5 MB; PDF metin işlemede en fazla 20 sayfa desteklenir. PDF.js metin katmanını tarayıcıda okur. Yeterli metin yoksa Drive dönüşümüyle tek OCR denenir. Alan çıkarımı yardımcıdır; tutar, IBAN veya isim her banka biçiminde bulunamayabilir. [Google Drive OCR dönüşümü](https://developers.google.com/workspace/drive/api/guides/manage-uploads) kullanılır.

Yükleme önce kaydedilir, sonra yönetici bildirimi denenir. Başarısız bildirim dekontu gizlemez. Yönetici gerçek dosyayı ve banka hareketini kontrol ederek onay tutarı/tarihi/işlem numarasını düzeltir. Onaydan sonra en eski borçtan başlayarak düşüm, kasa geliri ve numaralı PDF makbuz oluşturulur. Borcu aşan ödeme V1'de engellenir; avans hesabı yoktur.

Finansal yazmalar LockService ve kalıcı Islemler günlüğüyle yapılır. Yarıda kalan projeksiyon bir sonraki yetkili işlemde/tetikleyicide tamamlanır. Aynı dekont ikinci kez tahsilat oluşturmaz. Sheets ve Drive tek veritabanı işlemi olmadığından nadir bir kesintide Drive'da kayda bağlanmamış PDF kalabilir; ikinci tahsilat yaratılmaz.

## 7. Anlık yönetici bildirimi

Varsayılan kanal **e-posta**dır. `setup()` yönetici adresini tanımlar. WebAppURL girildiğinde bildirim doğrudan ilgili dekontu açan bağlantıyı içerir. Oturum yoksa önce giriş yapılır.

WhatsApp önceliği için Ayarlar'da kanalı WhatsApp seçin; alıcı telefonunu ülke koduyla girin, Meta tarafından onaylanmış şablon adını/dilini yazın. Betik özelliklerine `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID`, `WHATSAPP_API_VERSION` girin. Şablon gövdesinde dört metin parametresi sırasıyla **daire, tutar, tarih, tam kontrol linki** olmalıdır. Meta Business kurulumu ve onaylı mesaj şablonu gereklidir; bunlar bu teslimde oluşturulmadı. WhatsApp maliyetsiz kabul edilmemelidir; sağlayıcının hesabınıza uyguladığı koşulları kontrol edin.

Telegram için panelde kanal ve sohbet ID; betik özelliklerinde `TELEGRAM_TOKEN` gerekir.

Öncelikli kanal başarısızsa e-posta denenir. E-posta da başarısızsa kayıt `HATA` olarak kalır; saatlik tetikleyici yeniden dener. Yönetici dekont ekranından da tekrar deneyebilir. Servis kotası ve kesintiler nedeniyle gerçek zamanlı teslim garantisi yoktur; bekleyen dekont listesi esas alınır. Bildirim servisi yanıtı alıcı tarafından okunduğu anlamına gelmez.

## 8. Raporlar ve PC yedeği

Raporlar ekranında aylık/yıllık gelir-gider, aidat tahsilatı, daire borçları, ödeme geçmişi, kasa hareketleri ve makbuz listesi vardır. Dönem seçimi yapılabilir; daire borç raporu güncel tüm borcu gösterir. CSV çıktısı Excel'de açılır; doğrudan XLSX üretimi yoktur. PDF için **PDF / Yazdır → PDF olarak kaydet** kullanın.

Ayarlar'daki JSON yedek hem indirilir hem Drive/Yedekler'e yazılır. JSON tablo kayıtlarını ve dosya referanslarını içerir; PDF/görsellerin kendisini içermez. Tam yedek için Drive masaüstü uygulamasıyla Elmas Apartmani klasörünü bilgisayara eşitleyin; Sheet'i ayrıca Excel olarak indirin. V1'de otomatik JSON geri yükleme düğmesi yoktur.

## 9. Bilgisayarda önizleme

Node.js 20 veya üzeri ile proje klasöründe `npm start` çalıştırın; ardından `http://127.0.0.1:4173` açın. Ek npm paketi gerekmez. Windows'ta `ONIZLEME.ps1` aynı işi başlatır.

Önizlemede yönetici/sakin düğmesiyle iki görünüm arasında geçilir. İş kuralları aynı `.gs` dosyalarını yerel Google servis taklidiyle çalıştırır. Veriler yalnız işlem belleğindedir, sunucu kapanınca sıfırlanır. Gerçek kişisel/finansal veri kullanmayın. Google girişi, OCR ve dış bildirim bu modda çalışmaz. PDF önizleme üreticisi Türkçe harfleri sadeleştirir; gerçek Google makbuz üretimi DocumentApp kullanır.

## 10. Kontrol durumu

`npm test` ile 19 odaklı yerel kontrol geçti: daire gizliliği, dosya erişimi, yönetici yetkisi, idempotent aidat/ödeme, kısmi ödeme, kuruş/FIFO, hata sonrası toparlama, dosya hash, bildirim kesintisi, ters kasa hareketi, eski aidatların korunması ve yedek kapsamı.

Bu sonuç canlı entegrasyon doğrulaması değildir. Gerçek kullanıma geçmeden yönetici ve bir sakin hesabıyla giriş, gerçek örnek dekont yükleme, yönetici bildirim linki, onay ve Google tarafından üretilen PDF makbuz akışını bir kez doğrulayın. Proje sahibinin Google yetkilendirmesi ve OAuth/bildirim hesabı bilgileri olmadan bu adımlar tamamlanamaz.

# Sipariş Takip VS — Hızlı Bağlam

## Ürün sınırı

- Bu uygulama bağımsız **İzmirde Reklam Sipariş Takip VS** yazılımıdır.
- BTakip ve eski Sipariş Takip kaynakları, kurulumları ve canlı verileri değiştirilmez.
- BTakip yalnız fiyatlandırma/formül davranışları için referanstır.

## Güncel sürüm

- Sürüm: `1.1.12`
- Çalışma klasörü: `C:\Users\USER\Documents\Codex\2026-09-17\siparis-takip-vs-recovered`
- Kurulum: `release-vs\IzmirdeReklam-SiparisTakip-VS-Kurulum.exe`
- Kurulu EXE: `C:\Users\USER\AppData\Local\Programs\izmirde-reklam-siparis-takip-vs\İzmirde Reklam Sipariş Takip VS.exe`

## Açılış ve veri düzeni

- EXE doğrudan çalışma ekranını açar; Google penceresi otomatik açılmaz.
- İnternet veya oturum yoksa uygulama yerel yönetici çalışma alanında çalışır ve `Bağlan` gösterir.
- `Bağlan` seçilince Google bağlantısı açılır; başarılı bağlantıda yerel kayıtlar kullanıcının Firebase çalışma alanına aktarılır.
- Yerel tablo verisi: `%APPDATA%\İzmirde Reklam Sipariş Takip VS\vs-local-database.json`
- Hızlı sipariş dosyaları: `%USERPROFILE%\Documents\İzmirde Reklam Sipariş Takip VS\Hızlı Siparişler\{Gönderen}\{Gönderen} - {Dosya}`
- Cari müşteri dosyaları: `%USERPROFILE%\Documents\İzmirde Reklam Sipariş Takip VS\Müşteriler\{Müşteri}\{Müşteri} - {Dosya}`
- Buluta dosyanın kendisi gönderilmez; sipariş/müşteri/cari tablo bilgileri senkronize edilir.

## Doğrulama

- Kurulu sürüm: `1.1.12`
- Smoke: doğrudan açılış, yerel veritabanı köprüsü ve WhatsApp Web yüklemesi başarılı.

## 1.1.1 değişiklikleri

- Müşteri Google e-postası isteğe bağlıdır; boşsa müşteri yalnız yönetici takibinde kalır ve erişim kaydı oluşturulmaz.
- Müşteriler sayfasındaki Excel/PDF dışa aktarma kaldırıldı; `Excel / CSV yükle` ve `Müşteri yükle` bırakıldı.
- `AnonPerson_0012.xlsx` kaynağından 78 satış siparişi aktarıldı; 76 kaynak fiyatı korundu, fiyatı olmayan 2 kayıt boş bırakıldı.

## 1.1.2 değişiklikleri

- WhatsApp dosyasının ilk indirmesi sürerken sipariş kaydedilirse ikinci indirme başlatılmaz; tamamlanan dosya seçilen müşterinin yerel klasörüne bağlanır.
- Siparişler listesindeki WhatsApp kaynaklı siparişe sağ tıklayarak başarısız dosya indirmesi yeniden denenebilir; sipariş yeniden oluşturulmaz.
- `MARKA LOGO.pdf` henüz yerel arşivde bulunamadı; canlı WhatsApp indirmesi kullanıcı oturumunda ayrıca doğrulanmalıdır.

## 1.1.10 değişiklikleri

- WhatsApp PDF, belge, fotoğraf, video ve ses kaynakları yerel arşive indirilebilir.
- WhatsApp'ın dosya önizleme ekranındaki Türkçe `İndir` düğmesi desteklenir.
- Dosya fiziksel olarak tamamlanmadan yeni sipariş oluşturulmaz.
- Adsız WhatsApp medyası mesaj kimliğiyle geçici olarak adlandırılır; gerçek indirilen dosya adı arşivde kullanılır.
- Hızlı siparişler gönderen adına, cari siparişler müşteri adına ayrı klasörlenir.
- Kadir canlı denemesi doğrulandı: `Kadir - WhatsApp Image 2026-09-18 at 22.46.13.jpeg`, `171221` bayt, geçerli JPEG.

## 1.1.11 ve 1.1.12 değişiklikleri

- 1.1.11: WhatsApp oturumuna tarayıcı kimliği doğrudan uygulanır; kurulu EXE'de QR kodu ve oturum açılışı doğrulandı.
- 1.1.12: WhatsApp ekine sağ tıklayınca hem `Kayıtlı Müşteriye Sipariş Ekle` hem `Perakende / Tek Seferlik Sipariş Ekle` seçilebilir. Kayıtlı müşteri eşleşmiyorsa sipariş formunda müşteri seçilir.
- Dosya indirme sipariş formundan önce tamamlanır. Sipariş kaydedilince yerel dosya seçilen müşterinin veya hızlı siparişin klasörüne bağlanır; ölçü, malzeme, maliyet ve satış formda girilir/hesaplanır.
- 1.1.12 kurulum ve WhatsApp oturum açılışı doğrulandı; yeni menüden canlı dosya-sipariş kaydı oluşturulmadı.

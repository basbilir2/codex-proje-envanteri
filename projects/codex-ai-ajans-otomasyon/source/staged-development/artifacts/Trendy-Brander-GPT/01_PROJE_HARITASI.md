# TrendyBrander proje haritası

## Ana hedef

TrendyBrander yalnız sosyal medya postu üreten otomasyon değildir. Hedef; ajanların görev bazlı konuştuğu, itiraz ettiği, öğrenmeyi kanıtla yaptığı, model/trend güncelliğini izlediği, token ve maliyeti yönettiği, hatadan geri dönebildiği yaşayan dijital ajans mimarisidir.

## Gerçek proje kökü

`C:\ai-ajans`

Başka bir yol, özellikle `projects\brands\trendybrander`, mevcut dosya görülmeden varsayılmamalıdır.

## Önemli yerel adresler

- Ana Uygulama / Ajans Kurucu: `http://localhost:5684`
- Kullanıcıya sunulan mevcut merkez/onay ekranı: `http://localhost:5680`
- n8n yönetim ekranı: `http://localhost:5678`
- Üretilen ajans uygulamalarının portu kurulum sırasında ayrılır; n8n dışarıya açılmaz.

## Temel klasörler

- Ajan promptları: `C:\ai-ajans\projects\agents`
- Marka dosyaları: `C:\ai-ajans\projects`
- Marka görsel referansları: `C:\ai-ajans\projects\marka-referanslari`
- Merkezi politikalar/hafıza: `C:\ai-ajans\data\memory`
- Veri sözleşmeleri: `C:\ai-ajans\data\contracts`
- Loglar: `C:\ai-ajans\data\logs`
- Çıktılar: `C:\ai-ajans\data\outputs`
- Yerel çalışma durumu: `C:\ai-ajans\data\runtime`
- Ana Uygulama: `C:\ai-ajans\ui\ajans-yonetim`
- Üretilen ajans uygulaması şablonu: `C:\ai-ajans\ui\yasayan-ajans-app`
- Workflow paketleri: `C:\ai-ajans\workflows`
- Testler: `C:\ai-ajans\tests`
- Yedekler: `C:\ai-ajans\backups`
- Dağıtım paketleri: `C:\ai-ajans\dist`

## Marka kaynakları

- `projects\marka-kimligi.txt`
- `projects\urunler.txt`
- `projects\hedef-kitle.txt`
- `projects\yasakli-ifadeler.txt`
- `projects\icerik-ornekleri.txt`
- `projects\marka-referanslari\*.png`

Bu dosyalar markayı tanıtır. Aynı marka açıklamasının her ajan promptuna tekrar kopyalanması gerekmez; Orkestratör görev için ilgili kısa dilimi seçer.

## Uygulama ve motor ayrımı

Ana Uygulama, internet bağlantısı gerektirmeyen yerel ajans uygulaması tasarımcısıdır. Ürettiği `.ajansapp` paketi, son kullanıcıya kurulacak ajans uygulamasının politikalarını ve pasif workflow’larını taşır. Son kullanıcı uygulamasında n8n gizli motor olarak çalışır; kullanıcıdan n8n hesabı istenmez.

## Güncel doğrulanmış durum (2026-08-02/03)

- Ana Uygulama ve yerel yönetim servisleri sağlıklı çalıştı.
- Mevcut n8n Analizci akışı korunmuştur.
- Kurulabilir ajans uygulaması ve gizli n8n motoru yerel testten geçmiştir.
- Müşteri Mesajları rolü eklenmiştir.
- Yerel şifreli credential kasası, oturum/CSRF, görev idempotency ve mod yetkileri sentetik testlerden geçmiştir.
- JSON doğrulamalarında bilinen yapısal hata yoktur.
- Canlı Meta/Instagram mesaj alma, cevap gönderme ve gerçek yayın adaptörleri gerçek hesap izinleri olmadan etkin değildir.
- İlk test politikası Gemini ağırlıklıdır; üretim model haritası sonradan görev bazlı belirlenecektir.

## Korunacak sınırlar

- `n8n` veritabanı ve credential kayıtları körlemesine düzenlenmez.
- `secrets\*.dpapi`, `.env`, SQLite veritabanları, ham DM/log ve kullanıcı şifreleri GPT bilgi dosyalarına yüklenmez.
- Mevcut çalışan workflow değiştirilmeden önce export/yedek alınır.
- Canlı dış eylem, kullanıcı yetkisi ve hesap kapsamı doğrulanmadan başlatılmaz.

## Güncel dağıtım

Son doğrulanmış Ajans Kurucu paketi:

`C:\ai-ajans\dist\Ajans-Kurucu-2026-08-02_21-27-28.zip`

SHA-256:

`FF6F52E81BED2BAFD8F98CB9DE6C8292352B41042D2502F88F6C3EEF5ED44BBF`

Bu bilgi gelecekte değişebilir; yeni paket varsa dosya tarihi ve hash yeniden doğrulanmalıdır.

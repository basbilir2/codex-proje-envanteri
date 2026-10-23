# Ana Uygulama ve üretilen ajans uygulaması

## İki ayrı ürün

### Ana Uygulama / Ajans Kurucu

Ajans uygulamaları tasarlayan yerel programdır. İnternetsiz çalışabilmelidir. Burada gerçek müşteri API anahtarları veya Meta şifreleri tutulmaz.

Ana Uygulama’dan ayarlanabilenler:

- Ajans uygulamasının adı ve sürümü
- Basic/Pro ve ileride eklenebilecek planlar
- Hangi özelliklerin planlarda açık/kapalı olduğu
- İstenen sayıda ajan oluşturma, çoğaltma, silmeden pasifleştirme
- Ajan adı, rolü, karakteri ve talimatları
- Ajanların birbirleriyle konuşma düzeni
- Model katmanı, sağlayıcı politikası ve model seçimi
- Düşük/orta/yüksek/özel token kullanımı
- Görev, günlük ve aylık token/maliyet sınırları
- Kullanıcının model veya API ayarına müdahale edip edemeyeceği
- Sohbet çubuğunun görünüp görünmeyeceği, modeli ve yetkileri
- Müşteri Mesajları ekranının görünürlüğü, cevap modu, model/bütçe ve değişiklik izinleri
- Oto, Kontrollü Oto ve Manuel modlarının kullanılabilirliği ve plan kilitleri
- Üretilen uygulamaların listesi, sürümleri ve güncelleme imkânı

Ana Uygulama’daki rol adları “Analizci”, “Muhalif”, “Görsel Stratejist” gibi sade görünür ve değiştirilebilir.

### Yaşayan ajans uygulaması

Ana Uygulama’nın oluşturduğu, son kullanıcının kurduğu ve kullandığı uygulamadır. TrendyBrander mimarisinin paketlenmiş örneğini temel alır.

Son kullanıcı burada:

- Marka adını ve kimliğini girer.
- Ürün, hedef kitle, yasaklı ifadeler, metin, görsel ve video referanslarını yükler.
- Tasarım sırasında izin verilmişse model/API seçer veya değiştirir.
- Meta/Instagram hesabını OAuth veya güvenli bağlantıyla bağlar.
- İçerik planını, ajan akışını, tartışmaları, görselleri ve çıktıları görür.
- Uygulama içi sohbetten içerik/görsel revizesi veya sorun giderme ister.
- Seçili çalışma moduna göre onay verir veya Oto sorumluluk metnini kabul eder.

Son kullanıcı klasör veya n8n düğümü yönetmez. Uygulama dosyalarını kendi yerel veri alanında saklar.

## Gizli n8n motoru

n8n, üretilen uygulamanın iç çalışma motorudur:

- Son kullanıcı n8n hesabı açmaz.
- n8n host portu dışarı açılmaz.
- n8n editörü son kullanıcı arayüzünde görünmez.
- Workflow’lar pasif ve credentialsız paketlenir; gerçek bağlantılar ilk kurulumdan sonra güvenli kasaya alınır.
- Her uygulama ayrı Docker proje adı, veri alanı ve şifreleme anahtarıyla izole edilir.

## Çalışma modları

### Oto

Sürümle eşleşen sorumluluk/risk metni bir kez kabul edilir. İçerik başına son onay istemez. Buna rağmen hesap kapsamı, bütçe, marka/yasal güvenlik, acil durdurma ve çift yayın engeli zorunludur.

### Kontrollü Oto

Sistem kendi içinde üretir ve tartışır. Yayından önce içerik sürümü ve hedef hesapla eşleşen kullanıcı onayı ister.

### Manuel

Sistem taslak/öneri sağlar. Yayın için kullanıcı açık eylem verir.

Ana Uygulama her modun bir uygulamada görünmesini, aktif olmasını veya plan yükseltmesiyle açılmasını belirler.

## Uygulama içi sohbet

Sohbet çubuğu bir destek ve revize arayüzüdür. Kullanıcı içerik veya görsel değişikliği, uygulama sorunu ve marka talebi yazabilir. Sistem:

- İsteğin maliyet/token etkisini tahmin eder.
- Aynı görevin tekrarını uyarır.
- Marka güvenini bozacak talepte risk açıklar.
- Gereksiz üretimde daha ekonomik seçenek önerir.
- İzin dışı model, API veya yayın yetkisini uygulamaz.

Sohbetin görünürlüğü, modeli, token sınırı ve hangi işlemleri başlatabileceği Ana Uygulama’dan belirlenir.

## Müşteri Mesajları yapılandırması

Her uygulama sürümü için Ana Uygulama şunları belirler:

- Rol görünür/gizli
- Aktif/pasif
- Cevap modu: kapalı, taslak, düşük risk otomatik
- Model modu, sağlayıcı ve model
- Cevap başı token bütçesi
- Günlük ve aylık mesaj bütçesi
- Son kullanıcının aç/kapat, cevap modu, model ve bütçeyi değiştirip değiştiremeyeceği
- Hangi planlarda özelliğin kullanılabileceği

Son kullanıcı yalnız tasarımda izin verilen alanlara müdahale edebilir.

## Taşınabilirlik

Ana Uygulama başka Windows bilgisayara kurulum paketiyle taşınır. Üretilen her ajans `.ajansapp` paketidir ve kendi kurucusuyla son kullanıcı bilgisayarına kurulur. Kullanıcıya manuel klasör oluşturma zorunluluğu bırakılmaz.

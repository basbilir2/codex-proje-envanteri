# Ajans Kurucu — Kısa Kullanım Kılavuzu

Ajans Kurucu, TrendyBrander için geliştirdiğimiz yaşayan ajans mimarisinden yeni ve kurulabilir ajans uygulamaları tasarlayan **çevrimdışı ana programdır**. Kendisi yapay zekâ çağırmaz; API, Meta veya müşteri şifresi istemez.

## Roller

Rol, belirli bir işi yapan karakterdir. Analizci, Muhalif, Ordinaryüs, İçerikçi ve Görselci gibi bütün isimler değiştirilebilir.

- Yeni rol oluşturabilir veya mevcut rolü kopyalayabilirsin.
- Rolü açabilir, kapatabilir ve çalışma sırasını değiştirebilirsin.
- Görevini, karakterini, model davranışını ve token sınırını belirleyebilirsin.
- Uygulama oluştururken görünen rol isimlerini yalnız o uygulamaya özel değiştirebilirsin.

## Model ve token mantığı

Her rol otomatik veya sabit model kullanacak şekilde hazırlanabilir. Ana program modeli çalıştırmaz; yalnız oluşturulan uygulamaya kural aktarır.

Token seçenekleri: **Az, Orta, Yüksek veya Özel**. Ayrıca görev, gün ve ay için üst sınır; maksimum çağrı ve yeniden deneme sayısı belirlenebilir.

## Akışlar

Akış Tasarımcısı’nda rolleri istediğin sıraya koyabilir; sıralı, tartışmalı, paralel kurul veya özel düzen seçebilirsin. Normal ve kritik görevler için tartışma turu ayrı ayarlanır. Son yayın onayı her zaman zorunludur.

## Basic, Plus ve Pro

Uygulama oluştururken plan seçilir. Rol sayısı, model seçme özgürlüğü, aylık token kotası, tartışma turu, özel akış ve hafıza özellikleri uygulamaya göre sınırlandırılabilir.

## Çalışma modları

Her modun uygulamada görünüp görünmeyeceğini ve en düşük hangi planda açılacağını sen belirlersin.

- **Oto:** Kullanıcı sürümlü sorumluluk ve yapay zekâ hata riski metnini kabul ettikten sonra tanımlı hesap/bütçe/güvenlik sınırlarında son Meta yayını dahil ayrıca onay istemez.
- **Kontrollü Oto:** Ajans üretir ve tartışır; son yayın kullanıcı onayı ister.
- **Manuel:** Görevleri ve seçimleri kullanıcı başlatır.

Bir mod Basic uygulamada gösterilip minimum planı Pro yapılabilir. Bu durumda kullanıcı modu görür fakat plan yükseltilene kadar açamaz. Oto modda bile hesap kapsamı, bütçe, marka ve hukuk güvenliği, çift yayın engeli ve acil durdurma korunur.

## Uygulama oluşturma

1. Rolleri ve akışı hazırla.
2. Model ve token kurallarını belirle.
3. Uygulamanın ve markanın adını yaz.
4. Basic, Plus veya Pro planını seç.
5. Uygulamada görünecek rol isimlerini belirle.
6. Kullanıcı bölümlerini seç ve uygulamayı oluştur.

API, Meta, Instagram ve marka dosyaları **Ana Program’a değil**, kurulan ajans uygulamasına girilir. Her müşteri uygulamasının verisi ve şifreli kasası ayrıdır.

Uygulamayı tasarlarken API/model yetkisini seçersin:

- **Kilitli:** Kullanıcı yalnız senin tanımladığın sağlayıcı ve modellerin anahtarlarını girer; seçimi değiştiremez.
- **İzinli liste:** Yalnız senin izin verdiğin sağlayıcı ve modeller arasında değişiklik yapabilir.
- **Açık:** Yeni sağlayıcı veya model ekleyebilir.

Meta hesabının sonradan değiştirilip değiştirilemeyeceği de tasarım sırasında belirlenir. İlk bağlantı her zaman oluşturulan uygulamanın kendi güvenli kurulum ekranında yapılır.

## Gizli otomasyon motoru

Her yaşayan ajans uygulaması TrendyBrander çekirdeğini ve gerekli n8n iş akışlarını kendi kurulum paketinde taşır. n8n yalnız uygulamanın arka planında çalışır; son kullanıcı n8n hesabı açmaz, n8n panelini görmez ve gizli akışları değiştiremez.

## Uygulama içi sohbet

İstersen ajansla konuşma çubuğunu açarsın. Modeli, token sınırı ve içerik/görsel revize izinleri Ana Program’dan ayarlanır. Kullanıcı sorun bildirebilir veya değişiklik isteyebilir; fakat sohbet yayın yapamaz, gizli akışı değiştiremez ve yüksek maliyet, tekrar ya da marka riski gördüğünde önce uyarır.

## Önceki uygulamalar ve taşıma

**Önceki Uygulamalarım** bölümünde eski uygulamaları açabilir, güncelleyebilir, yeni sürüm oluşturabilir ve önizleyebilirsin.

**Taşıma ve Kurulum** bölümünden `.ajanskurucu` paketi indirilebilir. Bu paket rollerini, akışlarını, token planlarını ve uygulama tanımlarını taşır; hesap şifresi veya API anahtarı içermez.

Başka bir bilgisayarda:

1. `Ajans-Kurucu-....zip` paketini aç ve `AJANS-KURUCU-KUR.cmd` dosyasını çalıştır.
2. Masaüstündeki **Ajans Kurucu** simgesinden paneli aç.
3. Eski bilgisayarda indirdiğin `.ajanskurucu` taşıma paketini **Taşıma ve Kurulum** bölümünden içe aktar.
4. Roller, akışlar, token planları ve **Önceki Uygulamalarım** listesi geri gelir.

Ana Program bilgileri Windows kullanıcı alanındaki `AjansKurucu` uygulama verisinde saklanır. Kullanıcı klasör veya JSON dosyası yönetmez; taşıma panelden yapılır.

Özet: **Ana Program çevrimdışı ajans tasarlar; oluşturulan Ajans Uygulaması çevrimiçi çalışır ve müşterinin marka/hesap bilgilerini kendi alanında yönetir.**

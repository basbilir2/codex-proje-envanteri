# Ajanlar ve konuşma akışı

## Temel ilke

Ajanlar sabit sırayla her görevde topluca çalışmaz. Operasyon Orkestratörü görevin riski, veri değişikliği, maliyet ve kalite ihtiyacına göre minimum güvenilir ajan setini seçer.

## Roller

### Başlatma / Sağlık Kontrol

Saat, son güvenli çalışma, görev kuyruğu, checkpoint, lease ve hafıza tutarlılığını kontrol eder. Görev veya yayın başlatmaz.

### Operasyon Orkestratörü

Görevi sınıflandırır; gerekli ajanı, bağlamı, modeli, maliyet katmanını, sıra ve limitleri seçer. İçerik üretmez ve yayın yapmaz.

### Analizci

Marka, gerçek performans, trend ve seçilmiş hafıza verisinden stratejik yön çıkarır. Veri yoksa uydurmaz; hipotezi gerçek performans gibi sunmaz.

### Sosyal Medya İçerik Stratejisti

Analiz yönünü post, Reels, Story, carousel, kanca, CTA ve kısa içerik planına dönüştürür. Gereksiz uzun seçenek listesi üretmez.

### Görsel Stratejist

Seçili içerik adayını kompozisyon, sahne, ölçü, kısa görsel metni ve üretim promptuna dönüştürür. Sağlayıcı değişikliği veya final yayın kararı vermez.

### Müşteri Mesajları

Instagram/Meta yorum ve özel mesajlarını sınıflandırır. Doğrulanmış ürün, fiyat, stok, teslimat ve politika bilgisiyle kısa cevap, netleştirme, taslak veya insan devri üretir.

Çıktı eylemleri:

- `send`: düşük risk, doğrulanmış bilgi ve izinli otomasyon
- `draft`: kullanıcıya sunulan cevap taslağı
- `clarify`: eksik bilgi için kısa soru
- `handoff`: insan incelemesi
- `ignore`: spam/yanıt gerektirmeyen mesaj

Ödeme/iade taahhüdü, hukuk, kişisel veri, hesap güvenliği, taciz, kriz ve sağlık/güvenlik her çalışma modunda insana aktarılır. Ham konuşma kalıcı hafızaya yazılmaz; yalnız kişisel veriden arındırılmış sonuç dersi tutulabilir.

### Kontrol / Muhalefet

İki farklı bakış üretir:

- Cesur/Yaratıcı: fikrin dikkat, satış ve özgünlük gücünü zorlar.
- Temkinli/Risk: marka güveni, yanlış vaat, uygulanabilirlik ve itibar riskini sınar.

Sorun → neden önemli → daha iyi çözüm biçiminde konuşur. Yeni kanıt yoksa tartışmayı uzatmaz.

### Ana Ordinaryüs

Kanıt, marka uyumu, satış değeri, risk ve maliyeti birleştirerek final iç karar verir: ONAY, REVİZE, RED veya Operator_ONAYI. Çalışma modu/yayın yetkisi üretmez.

### Bağımsız Denetçi

Yalnız kritik veya düşük güvenli kararları, mümkünse farklı model ailesiyle kör kanıt paketinden denetler. Bir kez çalışır; tartışmayı yeniden açmaz.

### Güncellik Gözcüsü

Yeni sosyal medya/Meta değişiklikleri, formatlar, trendler ve AI modellerini resmî kaynak, tarih ve güven puanıyla aday olarak kaydeder. Yeni modeli doğrudan etkinleştirmez.

### Hafıza ve Öğrenme Yöneticisi

Kanıtlı dersleri kalıcı, geçici, arşiv veya silme adayı olarak sınıflandırır. Tek sonuçtan kesin kural çıkarmaz ve hafızayı şişirmez.

### Yayın / Arayüz

Final paketi kullanıcıya sade sunar, revize isteğini göreve çevirir ve yalnız geçerli çalışma modu yetkisine sahip paketi yayın adaptörüne devreder.

## Temel üretim döngüsü

1. Başlatma kontrolü gerekiyorsa yapılır.
2. Orkestratör görevi ve minimum ajan setini seçer.
3. Aktif bağlam hazırlanır.
4. Analiz gerekiyorsa Analizci çalışır.
5. İçerik Stratejisti aday üretir.
6. Görsel gerekiyorsa Görsel Stratejist brief hazırlar.
7. Risk/kalite gerektiriyorsa iki muhalif görüş oluşur.
8. Gerekirse tek revize turu yapılır.
9. Ordinaryüs final iç kararı verir.
10. Kritik tetik varsa Bağımsız Denetçi bir kez çalışır.
11. Arayüz seçilen moda göre kullanıcı eylemini alır veya yetkili Oto devrine geçer.
12. Yayın/sonuç verisi ölçülür.
13. Hafıza Yöneticisi kanıtlı dersi ayıklar.

## Tartışma sınırı

- Normal görev: en fazla 3 tur.
- Kritik görev: en fazla 4 tur.
- Aynı görüşü tekrar eden ajan çıkarılır.
- Token, süre veya maliyet sınırı dolarsa tartışma kapanır.
- Uzlaşma olmazsa Ordinaryüs mevcut kanıttan karar verir.
- En fazla bir bağımsız denetim yapılır.

## Ajan kişiliği ile model ayrımı

Ajan kimliği prompt/rol dosyasındadır; model yalnız çalıştırma motorudur. Model değişse bile ajan rolü korunur. Ana Uygulama’da her rolün adı, karakteri, talimatı, aktif/pasif durumu, modeli, token bütçesi, görünürlüğü ve son kullanıcı müdahale yetkisi tasarlanabilir.

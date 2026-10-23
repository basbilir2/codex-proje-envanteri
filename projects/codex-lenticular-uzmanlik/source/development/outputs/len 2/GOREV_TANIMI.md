Güncel ana hedef ve görev devri: [Ücretsiz işçi, ücretli yönetim](CALISMA_DUZENI.md). Kullanıcının son isteği: ücretli model tokenlarını azaltmak, API kullanmamak, yerel/ücretli geçişini gerektiğinde yinelemek.

# len 2 — Yerel zekâya Lenticular Studio kullanımını öğretme

Hedef: Yerel yapay zekânın mevcut Lenticular Studio yazılımını doğru kullanmayı öğrenmesi. Kullanıcının gösterdiği klasör, bu eğitimin yazılım/iş akışı bilgi kaynaklarından biridir. Kaynak klasörün içinde eğitilecek model ağırlığı aranması gerekmez.

Görev paylaşımı değişmez: Astra teşhis eder, ayarları ve çözümü seçer, açık iş emrini verir ve sonucu denetler. Yerel işçi yazılımda bu talimatı uygular. Hata çıkarsa durur ve çıktıyı Astra'ya aktarır; kendi başına düzeltme veya başka yöntem denemez.

## Yazılım ve kaynak ilişkisi

- Yazılım kökü: `C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1`
- Kullanıcının gösterdiği öğretici iş kaydı: aynı kökteki `outputs/studio/20261006-105350-02b4bafc`.
- Kod ve kullanım kılavuzları işlemin nasıl çağrıldığını; gösterilen iş kaydı ayar, ara dosya, sahne, render ve baskı raporlarının nasıl bağlandığını öğretir.
- Çevrim içi lentiküler kaynaklar kavramları destekler. Başka yazılımların menüleri veya özellikleri bu programa aitmiş gibi öğretilmez.

## Öğretilecek uygulama görevleri

1. Astra'nın seçtiği görseli veya hazır derinliği yazılımda doğru alana yüklemek.
2. Verilen sabit nokta, derinlik, kamera ve görünüş ayarlarını aynen uygulamak.
3. İstenen önizleme/render işlemini çalıştırıp durumunu takip etmek.
4. Var olan render'ı seçerek baskı hazırlamak; talimat gerektirmedikçe yeniden render başlatmamak.
5. Ölçü, PPI, DPI, nominal/etkin LPI ve Ne alanlarını birbirine karıştırmamak.
6. Verilen ICC, renk, aynalama ve beyaz alt baskı ayarlarını uygulamak.
7. İstenen pitch/hizalama dosyalarını üretmek; ölçüm kaydı olmadan ölçüm yapılmış dememek.
8. Profil ve iş kopyalarını belirtilen kapsamda kaydetmek; kaynakları korumak.
9. Çıktı dosyalarını ve raporları bulup Astra'ya doğru adlarla iletmek.
10. Hata/eksik girdi durumunda tam rapor verip Astra'nın sonraki talimatını beklemek.

Her eğitim örneğinin hedef yapısı: **Astra iş emri → başlangıç durumu → yazılımda uygulanacak adımlar → gerçek işlem kaydı → beklenen dosya/rapor → işçinin yanıtı**. Bu yapı görsel kusur arama veya yazılımı geliştirme görevi değildir.

## Hazır içerik ve durum

`egitim_icerigi/` altında gösterilen işten çıkarılmış 19 bilgi kartı, dokuz JSON kaynak kaydı, 61 dosyanın görev haritası ve 11 ilgili çevrim içi kaynak notu bulunur. Önceki 36+6 davranış örneği adaydır; gerçek yazılım kullanım izleriyle henüz doğrulanmış eğitim verisi sayılmaz. Model ağırlığı eğitimi bu oturumda çalıştırılmadı.

Bu görev tanımı günceldir; önceki belgelerdeki kaynak klasörü ile hedef modeli karıştıran açıklamaların önüne geçer.

## İleri uzmanlık kapsamı — 10 Ekim 2026

20 modül, 18 yeni birinci el kaynak notu, yedi yazılım/ürün karşılaştırması ve 28 ayrı pilot sınav senaryosu eklendi. 19 yerel öğretici kart da bilgi aramasına bağlandı. Ayrıntılar: [Uzmanlık programı](uzmanlik_programi/UZMANLIK_PLANI.md). Bilgi kapsamı geniştir; işlem ve teşhis yetkisi Astra’dadır. Model eğitimi veya başarı sınavı henüz çalıştırılmadı. Gösterilen iş artık kör test sayılmaz.

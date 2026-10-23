# 22 Ekim — asıl işlev düzeltmesi

- Amaç: görseli anlayıp sadık biçimde yeniden oluşturmak; gerektiğinde tasarımı kumaş/yüzey dokusu, kıvrım ve gölgeden ayırmak. ChatGPT kalite ve hız hedefi değişmedi.
- Hata: hızlı ilk aşama Sharp keskinleştirmesine indirgenmişti. Genel Qwen talimatı da kumaş dahil tüm sahneyi korumayı istiyordu; tasarım çıkarma isteğiyle çelişiyordu.
- Düzeltme: ana UI artık doğrudan üretken motoru çağırır. `extract-design` ve `restore-image` ayrı, kayıtlı talimatlardır. Yardımcı 2× ve BiRefNet ana işlev yerine sunulmaz. Keskinleştirici API geçmiş uyumluluk için açıkça `mode=quick` ile kullanılabilir, UI ana akışında kullanılmaz; varsayılan sunucu modu AI'dır.
- Seçim: özgün görselden kırpma anında sağda gösterilir, açıkça henüz yeniden oluşturulmamış kaynak olarak etiketlenir. AI girdisi özgün yükleme ve seçili koordinatlardır; önceki üretilmiş veya fırçalanmış sonuç değildir. Kaynak korunur.
- Doğrulama: Node sözdizimi ve Python komut arayüzü kontrolü geçti. Gerçek Mavi fotoğrafıyla tarayıcıda 368×639 alan seçildi; AI çalışmadan sağdaki canvas 368×639 olarak göründü. Bu yalnız seçim/önizleme kanıtıdır, yeniden oluşturma başarısı değildir.
- Gerçek üretim sınırı: bu yeni tasarım çıkarma talimatıyla gerçek Qwen çıktısı henüz alınmadı. Önceki cloud sonuçları sahne koruma göreviyleydi; kumaştan tasarım çıkarma kanıtı sayılmaz. PC hız/bellek eksikleri kayıtlı; yeni ağır deneme veya ücretli GPU açılmadı. Prompt değiştirmek bu eksikleri çözmez.
- Sonraki zorunlu kabul: doğru görevle gerçek üretilmiş tasarımı, yazı/çizgi/renk sadakatini ve yüzeyden ayrılmayı doğrulamak; ardından bağımsız PC hız kabulü. Bunlar sağlanmadan bitmiş proje teslimi yok.

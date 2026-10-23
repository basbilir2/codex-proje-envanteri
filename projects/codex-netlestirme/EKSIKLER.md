# Yeniden üretim sınırları ve tamamlanacaklar

- Sabit bağımlılık kilidi bulunamadı: source/current/on-kontrol/recovery-before-20261022/app/package.json
- Model ağırlıkları/runtime ikilileri dahil değil. PRIVACY.json dosyası, kaynak kod ve model kayıtlarıyla aynı sürümler yeniden edinilmelidir. Kaynağı/sürümü sabitlenmemiş bileşenler için birebir sonuç garanti değildir.
- Bu arşivleme sırasında temiz bilgisayarda uygulama derleme/kurulum/canlı hesap veya fiziksel çıktı testi yapılmadı. Önceki test kayıtları tarihsel kanıttır.

Müşteri kayıtları, siparişler, kişisel görseller, hesap oturumları ve parolalar bu yazılım arşivinin kapsamı değildir. Boş yeni veriyle program oluşturulabilirliği ile eski canlı içeriğin geri gelmesi farklıdır.

Özel eğitilmiş iki checkpoint ayrıca korunacak sürüm eki olarak tanımlandı. Eğitim verisi dahil edilmediğinden aynı eğitimi yeniden üretme iddiası yoktur; mevcut eğitimin sonucu checkpoint ile korunur.

## Kişisel verisiz sürüm

Kişiye özel içe aktarma/karşılaştırma raporları ve dolu veri oluşturucuları kaldırılmıştır. Eski kişiye özel ad/iletişim sabitleri anonimdir. Algoritmalar ve veri şemaları korunur; gerçek kişi/hesap eşleşmeleri yalnız yerel yapılandırmada sağlanmalıdır.

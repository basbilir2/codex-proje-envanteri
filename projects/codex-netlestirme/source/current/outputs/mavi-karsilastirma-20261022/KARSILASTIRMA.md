# Mavi — mevcut yazılım sonucu ve ChatGPT yeniden oluşturma karşılaştırması

22 Ekim 2026. Kullanıcının düzeltmesiyle yazılım yeniden çalıştırılmadı. Ana uygulama kodu ve ayarları değiştirilmedi; ücretli GPU açılmadı.

**Sonraki kullanıcı onayı:** Kullanıcı bu karşılaştırmadaki `chatgpt-tasarim.png` dosyasının netliğini ve yeniden oluşturmasını “çok yeterli” buldu ve yazılımda aynı seviyeyi istedi. Bu iki özellik için referans kabul edildi. Aşağıdaki henüz kabul edilmedi ifadeleri değerlendirme anının tarihsel durumudur; güncel kabul bu paragraftır. Yazılımın bu seviyeye ulaştığı veya dosyanın alpha/birebir renk açısından kabul edildiği sonucu çıkmaz.

## Kaynak eşliği

Kullanıcının `C:/Users/USER/Downloads/WhatsApp Image 2026-10-19 at 13.34.07.jpeg` dosyası ile `app/inputs/mavi.jpeg` SHA256 değeri aynıdır:
`c6e33036ad4f69d7cea2d37b0439930ade1073a44cd3d249fcadd35d2d849063`.

Mevcut yazılım sonucu `on-kontrol/gpu-mavi-fast-native.png` ve yanındaki JSON kaydıdır. Qwen-Image-Edit-2511 + Lightning, 4 adım, 768×1664, kayıtlı süre 39,11 saniye; eski A40 geliştirme çalışmasıdır. Talimatı fotoğrafın sahnesini koruyan restorasyondur. Bu sonuç yeni `extract-design` görevinin testi veya yerel PC hız sonucu değildir. Diğer son job kayıtları farklı kaynak/logo içerdiğinden bu karşılaştırmada kullanılmadı.

## Yeni görüntüler

Yerleşik image_gen aracı kullanıldı; ayrı API anahtarı veya ücretli inference servisi bağlanmadı. Referans kaynak fotoğraftır. İlk şeffaf üretim ve tek hedefli kenar düzeltmesi istenmeyen beyaz alpha artıkları bıraktı; şeffaf sonuç kabul edilmedi. Son üretim opak gri gösterim zeminiyle alındı. Elle logo/yazı çizimi, font değiştirme betiği veya piksel rötuşu yapılmadı.

- `chatgpt-tasarim.png`: son referans önizlemesi, 1774×887, alpha yok. Gri zemin opaktır. Bu dosya temiz şeffaf PNG veya birebir baskı kabulü olarak sunulmaz.
- `seffaf-deneme-onaysiz.png`: 1774×887 gerçek alpha içerir; beyaz kalıntılar nedeniyle kullanım kabulü verilmedi.
- `yazilim-mevcut-sonuc.png` / `.json`: karşılaştırılan mevcut yazılım çıktısının değişmeyen kopyası.
- `karsilastirma.png`: kaynak, yazılım, ChatGPT tasarımını yan yana gösterir. Kaynak/yazılımda karşılık gelen alanlar yalnız sunum için kırpılıp ölçeklendi; tasarım içeriği düzeltilmedi. Yeni tasarımın da sadece sunum kenar boşlukları kırpıldı. Bütün orijinal görüntüler korunur.

## Görsel değerlendirme

| Ölçüt | Kayıtlı yazılım çıktısı | ChatGPT yeni referansı |
|---|---|---|
| Kumaştan bağımsız tasarım | Yok; tişört, doku, gölge korunmuş | Tasarım ayrı yeniden oluşturulmuş; son önizleme opak gri zeminde |
| Çizgi/yazı netliği | Kaynaktan daha net; kumaş dokusu kalıyor | Konturlar ve küçük tarih daha keskin |
| Kaynak logo biçimine sadakat | Görsel olarak daha yakın | M ve diğer harf oranları, kontur ağırlığı, kuyruk eğrisi ve tarih yazısının boyut/font biçimi değişmiş |
| Metin içeriği | EST.1991 okunabiliyor | Mavi ve EST.1991 okunabiliyor; küçük metnin biçimi kaynağa birebir eş değil |
| Gerçek renk | Fotoğrafta ışık/kumaş etkisi var; doğrulanmadı | Lacivert modelce yeniden tahmin edilmiş; gerçek boya rengi doğrulanmadı |
| Temiz şeffaf PNG | Yok | Son dosya opak; alpha denemesi kalıntılı ve kabul edilmedi |

Sonuç: mevcut yazılım sonucu tasarım kurtarma hedefini karşılamıyor, çünkü görevi fotoğraf restorasyonuydu. Yeni ChatGPT referansı tasarımı ayırma/netlikte ileri, fakat logo biçimini kısmen yeniden yorumluyor; tam sadakat ve temiz şeffaflık kabulü yok. Bu yeni referans kullanıcı tarafından kabul edilmiş kalite baseline'ı veya eğitim doğrusu sayılmaz. Eski FLUX dosyaları kullanılmadı. Farklı görev/çalışma ortamları nedeniyle hız veya yeni pipeline üstünlüğü sonucu çıkarılmaz.

## Son üretim talimatı (yerleşik araç)

Faithful artwork recovery, NOT redesign. Using the attached original navy T-shirt photograph as the sole reference, recreate ONLY the printed chest design flat, clean and crisp on a perfectly uniform pale cool gray solid background (#c8ccd2). No person, no garment, no cloth, no texture, no photo, no shadow or transparency effects. The design is the white-outlined DARK NAVY script word Mavi with a long matching dark navy and white-outlined underline/swash and the small WHITE text EST.1991 positioned below its right half. Exact texts: Mavi, EST.1991. Preserve the source's distinctive elegant connected script letter shapes, M flourish, lowercase connections, i dot, underline shape, spacing, proportions and fine white outline weight. The dark navy interiors of the letters/underline must be clean uniform navy close to #172c48, no gradients. Small EST.1991 letters must be solid sharp white, accurately readable, with the original small serif lettering appearance rather than heavy block outlines. Clean vector-like ink artwork with continuous smooth contours, no speckles, no distressing, no noise, no stains, no halo, no patchy matte. Background must be a single completely smooth gray tone including every open gap between the letters. Horizontal layout, whole artwork fully visible with a comfortable small margin, no extra marks or text. The gray is a neutral display background only, not a part of the recovered design.

# Görsel iyileştirme — geliştirme sürümü

En son kapsam düzeltmesi: hızlı keskinleştirme kullanıcı tarafından reddedildi. Ana düğme Qwen ile üretken yeniden oluşturmadır; tasarımı kumaştan/yüzeyden ayırma ve genel görüntüyü koruyarak yeniden oluşturma ayrı talimatlardır. Seçim sağda işlem yapılmamış kaynak olarak hemen görünür. Yardımcı 2× ve arka plan/fırça araçları korunur. Bu görevle modelin gerçek çıktı/ChatGPT kalite kabulü henüz yoktur; PC hız sorunu sürüyor. `../on-kontrol/RECONSTRUCTION-DUZELTME.md` en güncel kayıttır; aşağıdaki hızlı-ilk-aşama açıklaması önceki, geçersiz karardır.

22 Ekim son güncellemesi: kullanıcı isteğiyle alan seçimi, hızlı ilk netleştirme, ayrı yerel AI 2×, gerçek ilerleme ve sonuç üzerinde düzenleme eklendi. Varsayılan ilk işlem Qwen değildir; aynı boyutta hızlı keskinlik düzeltmesidir. Silgi/geri getirme, geri alma, kenar, ton, yakınlaştırma ve PNG indirme gerçek küçük girdiyle kontrol edildi. Ayrıntı `../on-kontrol/EDITOR-V2.md`. Ağır Qwen yalnız ileri/yavaş denemedir; yeni bellek bütçesiyle tam çıkarımı yeniden çalıştırılmadı. Aşağıdaki kapanış ölçümleri bu son kademeli arayüzden önceki büyük-model denemeleridir; genel ChatGPT eşitliği henüz kabul edilmedi.

Bu klasör bitmiş ürün değildir. Ürün iki işlemden oluşur: üretken iyileştirme ve isteğe bağlı arka plan kaldırma. Ana motor Qwen-Image-Edit-2511; arka plan BiRefNet Lite 512 ve mevcut kenar kodudur.

Model dosyaları indirilip SHA256 ile doğrulandı. Python işçisi, yerel Node servisi ve sade arayüz yazıldı. Arka plan motoru dış bağlantı gerektirmeden gerçek alpha PNG üretti; kanıt `../on-kontrol/portrait-alpha.png`.

Yerel Qwen kontrolü gereken hızı sağlamadı: Ryzen 7 7730U / AMD bütünleşik grafik üzerinde Vulkan yoluyla 1201 saniyede 2/40 adım, süre sınırında çıktı yok. Resmi 4-adım hızlandırıcıyla 512×512 portre işi de 300 saniye sınırında çıktı vermeden durdu (kapanış dahil 304,25 saniye). Bu nedenle uygulama servisinde iyileştirme varsayılan olarak kapalıdır. Ana işlemi kullanıma hazır veya ChatGPT düzeyinde diye sunmayın. GPU'da alınan çıktı yerel başarı kanıtı değildir.

`models.json` kesin model/checkpoint revision ve hashlerini, `qwen_worker.py` gerçek çalıştırmayı, `server.mjs` iş/dosya yönetimini içerir. `cloud_*.sh` ve `../on-kontrol/cloud.py` yalnız geliştirme içindir; ürünün rutin çalışması RunPod'a bağlanmaz. Geliştirme bağlantı bilgileri `../on-kontrol/.private/` içindedir; dağıtılmaz.

Nihai paketleme ve PC kurulumu kalite/hız kabulünden sonra yapılır. Mevcut sonuçlar `../on-kontrol/gelistirme-durumu.json` içinde güncellenir.

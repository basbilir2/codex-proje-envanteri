# 22 Ekim — sınırlı LoRA pilotu

**Bu ilk hata kaydı tarihseldir.** Sonraki gerçek 48-adım eğitim ve karşılaştırmanın güncel kapanışı `validation-20261022/SONUC.md` içindedir. Son model yerelde, Mavi küçük yazı koruması GEÇMEDİ; son bakiye PRIVATE_AMOUNT, GPU kapalı.

**Sonuç: eğitim tamamlanmadı; 0/48 optimizer adımı, eğitilmiş checkpoint veya yeni kalite sonucu yok.** Ürün ve hız kabulü değişmedi.

- 8 özgün sentetik temiz/yüzeyli çift: 6 eğitim, 2 ayrı değerlendirme. Mavi eğitimde yok. Üretimler image_gen kaynaklarıdır; piksel hizalı gerçek veri oldukları iddia edilmez. İnceleme: `review.png`, kayıt/hash: `manifest.json`.
- Sabit DiffSynth revision: `d188f01d09013688dea27cc28f2e8dc0953c2543`. 2511 safetensors + Qwen text/VAE/processor sabit revision'ları `weights.json` içinde. A40, 100 GB disk, PRIVATE_AMOUNT/saat. Ağır işlem PC'de yapılmadı.
- İlk kurulum Transformers 5.20.2 ile eksik `Qwen2_5_VisionRotaryEmbedding` hatası verdi. 4.57.1 + PEFT 0.17.1 ile ön işlem 6/6 tamamlandı. Resmî sınıf kanıtı: https://github.com/huggingface/transformers/blob/v4.57.1/src/transformers/models/qwen2_5_vl/modeling_qwen2_5_vl.py
- Eğitim ilk forward'da GPU bellek hatası verdi. Yalnız bilinen bellek sorununa yönelik upstream checkpoint offload seçeneği eklenip hazır önbellekle devam edildi; yine aynı hata. Bundan sonra kaynak kapatıldı; çözünürlük, öğrenme oranı, seed veya model taraması yapılmadı.
- Kapanış sonrası statik teşhis: `train.py` ön işlemde `use_gradient_checkpointing` ve `use_gradient_checkpointing_offload` değerlerini `inputs_shared` içine koyuyor. Önbellek bu bayrakları kapalı saklamış; `sft:train` bunları eğitim komutundaki değerlerle yenilemiyor. Gerçek stack trace `gradient_checkpoint.py:70` kapalı dalına giriyor. Dolayısıyla bu çalışma A40'ın doğru checkpoint ayarlarıyla yetersiz olduğunu kanıtlamaz.
- Düzeltme: `cloud-pilot.py` checkpoint/offload bayraklarını ortak ön işlem/eğitim argümanlarına taşıyor; eski kapalı bayraklı önbelleğin yeniden kullanılması reddediliyor. Kaynak sözdizimi kontrol edildi; **düzeltmenin GPU doğrulaması yapılmadı**. Sonraki gerçek çalışmada altı örneklik önbellek yeniden üretilmeli. Eski paket `cloud-pilot.zip` ilk çalışmanın arşividir; yeni paket mevcut kaynaklardan hazırlanır.
- Ham kanıt: `evidence/pilot-20261022/` loglar, son hata raporu ve bağımlılıklar; `evidence/DiffSynth-Studio/` ilgili sabit kaynaklar. İlk hatalar ayrıca `cache-initial-error.log` ve `train-memory-error.log` içinde. İşlem öncesi/sonrası kontrollü kalite karşılaştırması eğitim tamamlanmadığı için yapılmadı.

**Harcama/kapanış:** oturum başlangıcında görünen bakiye PRIVATE_AMOUNT, kapanış ekranında PRIVATE_AMOUNT; fark PRIVATE_AMOUNT. Bu bakiye farkıdır, ayrıntılı fatura dökümü değildir. Pilotun PRIVATE_AMOUNT/60 dakika ve eski toplam PRIVATE_AMOUNT sınırı aşılmadı. Pod `fd6liiq3s5uged` kapalı; eski iki pod da kapalı, bütün görünen oranlar PRIVATE_AMOUNT/saat. Ekran kanıtı `gpu-stopped.png`. Yeni kaynak açılmadı.

**Sıradaki gerekli iş:** yeni model veya daha pahalı GPU seçmeden, düzeltilmiş önbellek ayarlarıyla tek sınırlı pilotu doğrulamak. Gerçek optimizer güncellemesi ve kaydedilmiş adaptör görülmeden eğitim tamamlandı denmez. Başarırsa aynı temel model/seed ile Mavi ve ayrılmış 07 örneğinde adaptörsüz/adaptörlü karşılaştırma yapılır. Genel model kalitesi, alpha ve PC hızı ayrıca doğrulanmayı bekler.

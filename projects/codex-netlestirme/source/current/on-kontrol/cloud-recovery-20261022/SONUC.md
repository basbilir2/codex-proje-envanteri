# 22 Ekim — ilk gerçek bulut tasarım kurtarma denemesi

**GEÇMEDİ:** model kumaş ve kişiyi kaldırıp Mavi tasarımını ayırdı; lacivert iç dolguları beyaz yaptı ve küçük EST.1991 yazısını tamamen kaybetti. Kullanıcının onaylı referans seviyesine ulaşmadı. Bu nedenle ürün/kalite kabulü verilmedi; yeniden deneme yapılmadı.

## Koşullar ve kanıt

- Kaynak: `app/inputs/mavi.jpeg`, SHA256 `c6e33036ad4f69d7cea2d37b0439930ade1073a44cd3d249fcadd35d2d849063`. Kullanıcının WhatsApp dosyasıyla aynı. Tam fotoğraf kullanıldı; kırpma, örneğe özel metin/logo talimatı veya elle çıktı düzeltmesi yok.
- Model: mevcut sabit Qwen-Image-Edit-2511 Q4_K_M ve sabit stable-diffusion.cpp revision'ı; CUDA A40 48 GB. Model değiştirilmedi, Lightning eklenmedi. GitHub kaynaklı daha önce derlenmiş çalıştırıcı tekrar kullanıldı; yeniden derleme yapılmadı.
- Görev: `extract-design`, 1024×640, 40 adım, cfg 2.5, seed 42. Süre: 235,19 saniye. `result.json`, `result.log`, `cloud-run.log` ham kanıttır. `result.png` gerçek model çıktısıdır.
- Talimatın genel çelişkisi düzeltildi: çıkarılan tasarımın fotoğraftaki eski konumunu koruma şartı kaldırıldı; tasarım çıktı alanına ortalanır, beyaz çizgileri görünür tutan nötr gri gösterim zemini kullanılır. Bu prompt düzeltmesi başarılı sonuç diye sunulmadı.
- `comparison.png`: solda kullanıcının onaylı referansı, sağda gerçek yeni bulut çıktısı. Yalnız gösterim alanları kırpılıp ölçeklendi; sonuç iyileştirilmedi veya alpha uygulanmadı. Sağ altta gerçek RunPod kapanış ekranından fiyat alanı vardır. Ham ekran `gpu-stopped.png`.

## Harcama ve kapanış

Önceki pod `farhpxgvyg704w` A40 müsait olmadığı için başlayamadı; RunPod'un aynı GPU türündeki taşıma yolu `ff6ai72lqho6np` pod'unu oluşturdu. Görünen toplam aktif oran PRIVATE_AMOUNT/saat idi. Eski çalışma dosyaları yeni pod'a gelmedi; 4 sabit model dosyası indirilip SHA256 ile doğrulandı. Yerel model çalıştırılmadı; PC yalnız kod/dosya hazırlama ve sonuç görüntüleme için kullanıldı.

Başlangıç görünen bakiye PRIVATE_AMOUNT, kapanış PRIVATE_AMOUNT; fark PRIVATE_AMOUNT. Bu ekran bakiyesi farkıdır, kesinleşmiş fatura kalemi değildir. Önceki toplam PRIVATE_AMOUNT üst sınırı aşılmadı; otomatik ödeme/ek kredi alınmadı. Ham çıktı ve loglar indirilince GPU durduruldu. Hem eski hem yeni pod'da görünen oran PRIVATE_AMOUNT/saat. Ayrı disk ücreti yok. Geçici pod dosyaları stop sırasında kaybolur; gerekli kaynak/sürüm/model hashleri ve çıktı/loglar yerelde korunur.

## Eğitim için doğrulanmış sonraki yol

Bu oturum **çıkarım** oturumudur; eğitim yapılmadı. Rastgele prompt/seed taraması yerine dolgu ve küçük yazı koruma eksikleri somutlaştırıldı.

Resmi GitHub deposu [modelscope/DiffSynth-Studio](https://github.com/modelscope/DiffSynth-Studio), Apache-2.0, sabit revision `d188f01d09013688dea27cc28f2e8dc0953c2543` incelendi. Tam sürüm için [Qwen-Image-Edit-2511 LoRA örneği](https://github.com/modelscope/DiffSynth-Studio/blob/d188f01d09013688dea27cc28f2e8dc0953c2543/examples/qwen_image/model_training/lora/Qwen-Image-Edit-2511.sh) ve [eğitim kodu](https://github.com/modelscope/DiffSynth-Studio/blob/d188f01d09013688dea27cc28f2e8dc0953c2543/examples/qwen_image/model_training/train.py) bulundu. Yerel kopyalar `diffsynth-2511-lora.sh`, `diffsynth-train.py.txt` içindedir. FP8 eğitim örneği de kaydedildi; bu örnek genel Qwen-Image içindir, 2511/A40 üzerinde test edilmiş bellek çözümü sayılmaz.

Doğrulanan veri sözleşmesi: `image` temiz hedef, `edit_image` bozuk/yüzeyli kaynak, `prompt` görev talimatı. Eğitim örneği `--zero_cond_t`, gradient checkpointing ve LoRA kullanıyor. Safetensors transformer/text encoder/VAE ağırlıkları istiyor; mevcut GGUF çıkarım paketini doğrudan eğitmiyor. Eğitim ortamı/disk/VRAM kapasitesi ve toplam ücret kaynak açmadan önce bu farklı bağımlılıklara göre hazırlanmalıdır.

Eşlenik eğitim verisi henüz hazırlanmadı. Kullanıcıdan dosya eşleme/metin hazırlama istenmeyecek. Eğitim hazırlığı, farklı tasarımlarda koyu/açık iç dolgu, ince kontur, küçük metin, farklı yüzey/ışık ve perspektif varyasyonlarını kapsamalı; geliştirme dışı tasarımlar ayrılmalı. Mavi ve onaylı referansı ilk bağımsız değerlendirme örneği olarak korunmalı; yalnız bu örneğe eğitim yapmak genel çözüm sayılmaz. Referans opaktır, kusursuz alpha etiketi olarak kullanılmaz. LoRA eğitiminin bu eksikleri giderdiği, kurulup gerçek eğitim ve bağımsız çıkarım yapılmadan iddia edilmez.

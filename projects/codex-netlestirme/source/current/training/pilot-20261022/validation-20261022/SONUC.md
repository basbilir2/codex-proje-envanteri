# 22 Ekim — gerçek eğitim ve kontrollü karşılaştırma

**Eğitim tamamlandı; kalite kabulü GEÇMEDİ.** Mavi fotoğrafından ana tasarım ayrılıyor, lacivert dolgu ve temiz beyaz konturlar oluşuyor. Ancak **EST.1991 atlanıyor**. Bu pilotu bitmiş ürün veya genel tasarım kurtarma başarısı saymıyoruz.

## Gerçekte yapılanlar

- A40 `c5p7p5u451kqpy`, 100 GB geçici disk, görünen toplam yaklaşık PRIVATE_AMOUNT/saat. Ağır model PC'de çalıştırılmadı.
- Sabit DiffSynth revision `d188f01d09013688dea27cc28f2e8dc0953c2543`, Qwen-Image-Edit-2511 ve aynı 6 eğitim/2 ayrılmış sentetik çift. Mavi eğitimde yok. Seed, talimat, çözünürlük, öğrenme oranı ve rank taraması yapılmadı.
- Önceki önbellek/checkpoint bayrağı düzeltmesi gerçek GPU'da doğrulandı. İlk 48 adım ve dört kontrol çıktısı tamamlandı. Bu çalışmanın Mavi çıktıları fotoğrafı yeniden oluşturdu; kurtarma olmadı. Tam kayıtlar ve ağırlık `../single-input-v1/` içinde korunuyor.
- Somut ikinci uyumsuzluk bulundu: upstream `QwenImageUnit_PromptEmbedder.process`, tek `PIL.Image` için `encode_prompt_edit`, liste için `encode_prompt_edit_multi` seçiyor. Sabit resmî 2511 örneği görsel listesi kullanıyor. `train.json`, `validation.json`, üretim paketi ve `cloud-evaluate.py` tek elemanlı görsel listesine düzeltildi. Veri pikselleri değiştirilmedi. Önbellek yeniden üretildi; aynı pilot sıfırdan 48 adım tamamlandı. Son adaptör 48 adımlıdır; iki ayrı çalışmayı 96 adımlık tek model diye sunmuyoruz.
- Son ağırlık **236.116.888 bayt**. SHA256 `3727642c84e169791cea093623e82c3fd1ac5415d2b5875761bd5349e4e85f37`; bulut ve yerel dosya eşleşti. `loss.csv` 48 güncelleme içeriyor; kayıpların hepsi sonlu. Bunlar kalite kanıtı değildir.

## Görsel sonuç

`comparison.png` ham çıktıları yalnız gösterim için ölçeklendirir; rötuş/metin düzeltmesi yok.

| Girdi | Temel model, doğru 2511 yolu | 48 adım LoRA |
|---|---|---|
| Mavi, gerçek fotoğraf | Ana logo düz zemine ayrıldı; koyu dolgular korundu; EST.1991 yok | Temiz lacivert dolgu/beyaz konturlar; EST.1991 yine yok. Tam kabul GEÇMEDİ |
| SOLAR, eğitim dışında | Ana madalyon ayrıldı; ARCHIVE 2034 yok, çember perspektifi tam düzelmedi | Son dosya yerelde yok; tamamlanması/kalitesi doğrulanmadı |

Çıkarma davranışındaki büyük fark 2511 giriş yolu düzeltmesinden sonra temel modelde de görülüyor; bu farkı bütünüyle LoRA eğitimine bağlamıyoruz. LoRA'nın bağımsız/genel iyileştirmesi henüz kanıtlanmadı. Son SOLAR dosyası ve ikinci çalışmanın tam bulut logları alınamadığı için tamamlanmış dört karşılaştırma iddiası yok. Yerelde üç ham çıktı, son model, loss ve hash kanıtı var.

## Harcama ve kapanış

Başlangıçta görünen bakiye **PRIVATE_AMOUNT**, devamdaki kapanış kontrolünde **PRIVATE_AMOUNT**: **PRIVATE_AMOUNT bakiye farkı**. Bu ayrıntılı fatura değildir. PRIVATE_AMOUNT harcama sınırı içinde kalındı. Kontrolde pod zaten kapalıydı; kapanışı bu kontrol sırasında benim yaptığım iddia edilmiyor. `gpu-stopped.png` bütün podların PRIVATE_AMOUNT/saat olduğunu gösteriyor.

**Kapanış kontrolü gecikti.** 60 dakikalık hedefe uyum kanıtlanmadı; başlangıç/son kontrol aralığı bir saati aştı. İşlem zaman aşımı GPU kiralamasını kendiliğinden durdurmaz. Sonraki ücretli çalışmadan önce sağlayıcı düzeyinde süreli GPU kapanışı veya doğrulanmış dış kapatma güvencesi kurulmalı. Bu tur yeni kaynak açılmadı.

## Kalan gerekli iş

1. Küçük metnin atlanmasını, kaynak içindeki tasarım/metin alanının otomatik belirlenmesi ve ayrıntının korunması açısından incelemek. Bunu kanıtlanmış neden diye sunmamak; kullanıcıya doğru metin yazdırmamak, Mavi'ye özel tarih eklememek.
2. Küçük metin ve bağımsız örnek kabulü olmadan adaptörü ürünün varsayılan motoru yapmamak.
3. Mevcut PC hız sorunu, şeffaf alpha ve gerçek baskı kabulünün hâlâ açık olduğunu korumak. Bu gri zeminli PNG'ler şeffaf veya baskı onaylı değildir.

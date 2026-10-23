# Kanıt ve yol dizini

## Son eğitim kapanışı

- `training/pilot-20261022/validation-20261022/SONUC.md`: gerçek 48-adım model, koşullandırma düzeltmesi, eksik küçük yazı, son SOLAR çıktısının alınamaması ve kapanış boşluğu.
- Aynı klasörde `checkpoints/step-48.safetensors`, `checkpoint-verification.json`, `checkpoint.sha256`, `loss.csv`: 236.116.888 bayt; SHA256 `3727642c84e169791cea093623e82c3fd1ac5415d2b5875761bd5349e4e85f37`; 48 sonlu loss.
- `evaluation/{mavi-base,mavi-lora,heldout07-base}.png`, `comparison.png`: üç ham sonuç ve açıkça doğrulanmadı etiketi taşıyan eksik SOLAR-LoRA hücresi.
- `gpu-stopped.png`: PRIVATE_AMOUNT bakiye, bütün podlar PRIVATE_AMOUNT/saat. İlk 48-adım tek-Image çalışmasının tam kayıtları `../single-input-v1/` içinde.

## 22 Ekim — gerçek LoRA pilotu

- `training/pilot-20261022/SONUC.md`: 0/48 güncelleme, hatalar, kapanış ve sonraki sınırlı iş.
- `training/pilot-20261022/{manifest,train,validation,weights,pilot}.json`: kaynak hashleri, 6/2 ayrımı, sabit ağırlık revision'ları ve sınırlar. Mavi eğitim dışında.
- `training/pilot-20261022/review.png`: image_gen üretimi 8 temiz/yüzeyli çiftin sunumu; eğitim dosyası değildir.
- `training/pilot-20261022/evidence/`: gerçek bulut logları ve bellek hatasının ilgili sabit upstream kodu. `cache-initial-error.log`, `train-memory-error.log`: önceki hatalar.
- `training/pilot-20261022/gpu-stopped.png`: PRIVATE_AMOUNT bakiye ve PRIVATE_AMOUNT/saat kapanış.
- `training/README.md`, `cloud-pilot.py`, `cloud-setup.sh`: sabit sürümler ve kaynakta düzeltilmiş önbellek/checkpoint akışı. Son düzeltme GPU'da doğrulanmadı.
- Resmî Transformers 4.57.1 sınıf kaynağı: https://github.com/huggingface/transformers/blob/v4.57.1/src/transformers/models/qwen2_5_vl/modeling_qwen2_5_vl.py

21 Ekim 2026'da hazırlanmıştır. Güncel hedef için önce `KAPSAM.md`, uygulamaya hazır mimari için `MIMARI.md` okunur. `DEVAM.md` ayrıntılı geçmiş kaydıdır. Aşağıdaki eski hizmet/fiyat/lisans notları canlı durum garantisi değildir.

Son kullanıcı düzeltmesi: tek kalite referansı ChatGPT'nin aynı görselde yaptığı iştir. Eski FLUX dosyaları yalnız arşivdir; dosya adlarında geçen “beğenilen” ifadesi güncel kalite onayı değildir.

## Bu klasörde korunan referanslar

| Dosya | Anlamı |
|---|---|
| `referanslar/uc-ornek-hedef-kalite.png` | Üç kaynak/temiz çıktı çifti içeren kullanıcı kalite referansı: kabartmalı mavi yazısı, Mavi/EST1991, renkli kurt. Üretim yöntemleri bilinmiyor; otomatik olarak bizim model çıktımız sayılamaz. |
| `referanslar/mavi-kaynak-fotograf.jpeg` | 19 Ekim kaynak fotoğrafının değişmeden kopyası. |
| `referanslar/mavi-begenilen-flux-ve-yazi-duzeltme.png` | Eski FLUX üretimi + fon ayırma + ayrıca küçük metin düzeltmesi. Kullanıcı bu çıktıyı referans olmaktan çıkardı; yalnız arşiv kopyasıdır. |
| `referanslar/mavi-flux-seffaf-yazi-duzeltmesinden-once.png` | Metni ayrıca yeniden yazma adımından önceki FLUX + fon ayırma çıktısı. Ham diffusion çıktısı değildir. |
| `referanslar/flux-gercek-uretim-kaydi.json` | Gerçek çıkarımın 247,6 saniye, returncode 0 kaydı. |
| `referanslar/flux-ornek-parametreleri.json` | Gerçek örneğin prompt, model, seed ve boyut kaydı. |
| `referanslar/flux-model-surumleri-ve-hashler.json` | Kullanılmış çalışma zamanı ve model artefaktlarının sabit sürüm/hash bilgileri. |
| `referanslar/flux-ornek-uretim-betigi.py` | Eski betiğin arşiv kopyası. Göreli dosya yolları eski klasör düzenine bağlıdır; bu kopyayı doğrudan çalıştırma. |
| `referanslar/kopya-dogrulama.json` | Sekiz kopyanın orijinal yolları, SHA-256 ve boyutları. Kopyalama sırasında bütün hashler eşleşti. |

## Çalışan eski kaynak ve motorlar

Ana kaynak:
`C:\Users\USER\Documents\Codex\2026-10-17\referenced-chatgpt-conversation-this-is-an\outputs\dtf-studio`

- `README.md`: özellik geçmişi, sınırlar, fotoğraf hazırlığı, iki mod ve eksik bağlantı bilgileri. İçinde eski ve yeni aşamalar birlikte bulunur; en sondaki güncellemelerle okunmalı.
- `src/`: mevcut tarayıcı görsel işleme ve dizgi motorları.
- `src/reconstruction.mjs`: eski Wix AI istemcisi. Bir uç nokta adresinin yazılmış olması bağlantının çalıştığını kanıtlamaz.
- `service/local-redraw.mjs`, `service/redraw-worker.mjs`: hazırlanmış yerel FLUX ve kuyruk işçisi.
- `wix/backend/`: ertelenmiş entegrasyon taslakları.
- `dist/DTF-Studio.html`: önceki birleşik uygulama çıktısı; bu turda tekrar derlenmedi veya yayınlanmadı.

Gerçek FLUX çalışma klasörü:
`C:\Users\USER\Documents\Codex\2026-10-17\referenced-chatgpt-conversation-this-is-an\work\local-redraw`

Bu klasörde model dosyaları, CPU runtime, `run-mavi.py`, `mavi-request.json`, `mavi-inference.json`, `mavi-inference.log`, `mavi-redraw.png` ve `models-manifest.json` mevcut. Model ağırlıkları yeni çalışma klasörüne kopyalanmadı.

Önceki kalite karar dosyası:
`C:\Users\USER\Documents\Codex\2026-10-17\referenced-chatgpt-conversation-this-is-an\work\reference-quality\decision.md`

Bu dosyanın son UPDATE bölümü, daha önceki “model indirilmedi” aşamasını geçersiz kılar ve gerçek CPU üretimini kaydeder. ESRGAN Thick 4× denemesinin reddedildiği de burada yazılıdır.

Eski sonuç klasörü:
`C:\Users\USER\Documents\Codex\2026-10-17\referenced-chatgpt-conversation-this-is-an\outputs`

Başlıca dosyalar: `Mavi-EST1991-Duzeltilmis.png`, `Mavi-AI-Yeniden-Olusturuldu-Ham.png`, `Mavi-AI-Yeniden-Olusturuldu-Seffaf.png`, `Mavi-Iki-Mod-Karsilastirma.png`, `Mavi-Motor-Gercek-Cikti.png`. Ham, maskelenmiş, büyütülmüş ve metni düzeltilmiş sürümleri birbirine karıştırma.

Qwen deney klasörü:
`C:\Users\USER\Documents\Codex\2026-10-21\qwen-image-edit-2511-print-extraction`

`outputs/` altında hesap/ödeme ekranı görüntüleri var; bunlar model üretimi değildir. Gerçek test çıktısı doğrulanmadı. Tam adapter adı ve beklenen MD5 `DEVAM.md` içinde.

## Konuyla ilgili sohbetler

Bu adlar sohbet araçlarında görülen adlardır. Tekrar tamamını okumak gerekmez; bir iddia için gerekirse ilgili sohbet açılır.

| Sohbet adı | Kimlik | Ne için kullanılır? |
|---|---|---|
| DTF Baskıya Hazırlama | `6ad34916-d31c-83ed-83a1-e86b6ff5f476` | İlk ticari ürün, bir ücretsiz hak, maliyet ve DTF kapsamı. Üyelik daha sonra ertelendi. |
| Wix DTF platformunu kur | `01a14960-fd87-7a42-9b75-fc22297654d5` | Asıl uygulama geçmişi, kötü/iyi Mavi sonuçları, iki mod, gerçek FLUX deneyi, eksik web bağlantısı. |
| Üç Yapay Zekayı Birleştirme | `6ad3abf7-1e68-83ed-9629-e653c254bcba` | OpenCode geliştirici ajanları hakkında eski konuşma. Görsel motoru değildir; bu turda ajan çalıştırılmadı. |
| OmniFabric Alternatifi Araştırması | `6ad7b8de-bd84-83ed-8ed3-ee3e6dcb070f` | OmniFabric/FabricDiffusion/NI-Tex hakkındaki 20 Ekim araştırma iddiaları. |
| Daha iyi teknoloji karşılaştırması | `6ad7bf9c-7368-83ed-a531-30a9ec6a68b8` | Kumaş/komple kıyafet yerine tasarım kurtarma düzeltmesi; son seçilmiş Qwen+LoRA adayı. |
| Ticari Lisans Netleştirme | `6ad7b0c3-0804-83eb-b233-4c5544178714` | Farklı Qwen sürümlerinin lisanslarının karıştırılmaması. Güncel resmi lisans tekrar kontrol edilmeli. |
| Test Qwen print extraction | `01a15cad-ae56-74d3-bb02-2902eca46f2d` | Tam model/LoRA, gerçek test isteği, yerel çalıştırmama talebi, bulut hesap/ödeme sınırı. |
| Wix Tasarım Ayıklama Sistemi | `6ad7a220-f4cc-83ed-ad9e-93965763aed6` | RunPod depolama önerileri; son tercih Network Volume. Eski Global Volume önerisi son karar değildir. |
| RunPod ayarlarını seç | `01a15f37-373a-7770-87da-939cd29ef3e0` | Son GPU/depolama hazırlığı ve yüklenmeyen kart alanları. |

## Araştırma adayları — deney sonucu değildir

| Yol | Tarihli geçmiş kayıt | Gerçek durum sınırı |
|---|---|---|
| Qwen-Image-Edit-2511 + Print Extraction LoRA | Son seçilmiş aday | Bizim görsellerimizde çalıştırılmadı. |
| FLUX.2-klein-4B Q4_0 | Geçmişte üretilmiş Mavi deneyi | Kullanıcı kalite referansı olarak reddetti; hedef veya baseline olarak kullanılmayacak. |
| ESRGAN Slim 2× / ek netlik kademesi | Eski uygulamada kullanıldı | Reconstruction hedefini karşılamadı. |
| ESRGAN Thick 4× | Bir defa denendi ve reddedildi | Aynı öneriyi tekrar test etme gerekçesi yok. |
| FabricDiffusion Print | Hazır kod/ağırlık bulunduğu eski araştırmada yazıyor | Bu örneklerde çıkarım/kalite sonucu kaydı yok. |
| OmniFabric | 20 Ekim araştırmasında kod/ağırlık yok denmiş | Yayın durumu bu turda internette yeniden doğrulanmadı. |
| NI-Tex | Eski araştırmada mesh/UV ağırlıklı daha ağır yol | Bizim seçili tasarım örneklerinde test yok. |
| FLUX Kontext, VTOFF çeşitleri | Alternatif olarak konuşuldu | Kullanıcı tam kıyafet çıkarma yönünü düzeltti. |
| Qwen-Image-2.1 / FG Extract | Araştırma ve ticari lisans engeli konuşuldu | 2511 ile aynı model/lisans sayılmaz; test yok. |
| Koukoutu ve diğer ticari hizmetler | Karşılaştırma örneği olarak konuşuldu | Son ürünün ücretli API bağımsızlığı şartını sağlamış çözüm değil. |

Bu tablo yeni model tavsiyesi veya güncel lisans yorumu değildir. Üretime alınacak tam sürümün kod, temel model, adapter ve dağıtım lisansları resmi kaynaktan doğrulanmalı. Topaz kurulu olması, ücretli programın/ağırlıklarının web motoru olarak kullanılmasına izin vermez.

## Ertelenmiş Wix bilgisi — karıştırma

Son kullanıcı talebiyle Wix üzerinde çalışılmayacak. Bu bölüm yalnız geçmişi kaybetmemek içindir.

- Site adı: `Dtf Studio`; eski giriş: `https://izmirdedtf.wixsite.com/dtf-studio`.
- Bazı önceki sayfa sürümlerinin yayınlandığı sohbetlerde kaydedilmiş. Bu turda canlı site açılmadı; güncel çalışması doğrulanmadı.
- AI kuyruk/worker entegrasyonunun uçtan uca tamamlandığı doğrulanmış değil. Siteye kod eklemek, gerçek görüntünün kuyruktan motora gidip döndüğünü kanıtlamaz.
- İki kimlik kaydı var: README'nin eski site satırında `b9ff64fa-0b6c-49da-b3b3-32efbf93b84e`; son yerel `wix/pages/Home-free.js` dosya barındırma URL'sinde ve önceki entegrasyon kaydında `a247a575-abde-46de-ab59-a36dc6357d3d`. Eski bir kopyanın kaldırılması da sohbet geçmişinde var.
- Gelecekte Wix'e dönülürse isim + URL + metaSite ID canlı doğrulanmadan hiçbir siteye düzenleme/silme/yayınlama uygulanmaz. Bu çelişki şimdi çözülmüş gibi gösterilmez.
- Anahtarlar, özel worker dosyaları ve hesap sırları bu devam paketine alınmadı. Eski bağlantı gereksinimleri bugünkü işin ön koşulu değildir.

## Devam kaydının bakım kuralı

Yeni bir doğrulama eski bilgiyle çelişirse, `DEVAM.md` içinde güncel karar değiştirilir; bu dizinde eski kaydın neyi kanıtladığı belirtilir. Yeni deney dosyaları ayrı adlandırılır; kaynak örnek ve eski arşiv dosyalarının üzerine yazılmaz. Harcama, yayınlama veya yeni kapsam bu belgelerden otomatik yetki olarak çıkarılmaz.

## 22 Ekim — Design Recovery uygulama kanıtları

- Resmi Qwen model kartı bu tur okundu: https://huggingface.co/Qwen/Qwen-Image-Edit-2511 . 2511, Apache-2.0 ve görüntü düzenleme/tutarlılık/geometri açıklamaları görüldü. Bunlar cloth-to-artwork kalitesi garantisi veya bizim yeni görevimizin inference sonucu değildir. Mevcut GGUF/accelerator tam sürüm ve hashleri `app/models.json` içinde korunur.
- Resmi BiRefNet deposu bu tur okundu: https://github.com/ZhengPeng7/BiRefNet . Yardımcı segmentasyon olarak tutuldu; tasarım kurtarma modeli diye sunulmadı. Kurulu ONNX türevi mevcut sabit revision'dadır; bu tur yeniden indirilmedi.
- Yeni kod: `app/pipeline.mjs`, `app/geometry.mjs`, `app/qwen-adapter.mjs`; entegrasyon `server.mjs`, `qwen_worker.py` ve `web/` içinde.
- Yeni kontrol seti: `app/tests/recovery.test.mjs`; sonuç `on-kontrol/recovery-tests.txt`. Gerçek model çağrısı yapılmaz; kullanılan test dublörü açıkça etiketlidir. Süreç kapatma testinde gerçek küçük Python alt süreçleri açılıp kapatılır, model çalıştırılmaz.
- Ekran kanıtı: `on-kontrol/recovery-ui.png` yalnız gerçek kaynak yükleme, dört köşe ve kaynak önizlemesidir. AI üretimi değildir. Bu tur ana kurtarma çıkarımı **ÇALIŞTIRILMADI**.
- Kurulum/çalıştırma: `app/setup.ps1`, `app/Baslat.cmd`. Mevcut PC kurulu ortamında testler geçti; yeni PC'ye sıfırdan indirme/kurulum veya paketli dağıtım kabulü yapılmadı.
- İlgili önceki dosya kopyaları: `on-kontrol/recovery-before-20261022/`. Tarihsel deneyler ve kaynaklar korunur; yeni hedefin baseline'ı sayılmaz.
- Yeni açık yerel servis 17863; loglar `on-kontrol/recovery-server-session.txt`. Eski 17861 süreci durdurulmadı; otomatik denetim restart işlemini engelledi ve ayrıntılı gerekçe verilmedi.

## 22 Ekim — Mavi mevcut çıktı karşılaştırması

Kayıtlı `gpu-mavi-fast-native.png` / JSON ile aynı SHA256 kaynak kullanımı doğrulandı. Yeni yerleşik image_gen çıktısı ve karşılaştırma `outputs/mavi-karsilastirma-20261022/` içinde. Kesin kaynak hash, görev farkı, seçilen dosyalar, son prompt ve başarısız şeffaf deneme değerlendirmesi `KARSILASTIRMA.md` içindedir. Yazılım yeniden çalıştırılmadı. Yeni ChatGPT görüntüsü kullanıcıca kabul edilmiş baseline değildir; logo biçimi sapmaları ve opak son zemin açıkça kaydedildi.

## 22 Ekim — referans kabulünün güncellenmesi

Kullanıcı `outputs/mavi-karsilastirma-20261022/chatgpt-tasarim.png` netliği ve yeniden oluşturma seviyesini açıkça yeterli buldu. Önceki kabul yok notu bu iki özellik için tarihsel kaldı. Kesin dosya/kaynak SHA256 ve kabul kapsamı `on-kontrol/approved-recovery-reference.json` içinde; yeni model sonucu veya ürün kabulü değildir. Ana uygulama kodu/ayarları bu kabul kaydı için değiştirilmedi.

## 22 Ekim — gerçek bulut kurtarma ve resmi eğitim kodu

- Yeni gerçek sonuç: `on-kontrol/cloud-recovery-20261022/result.png`, `result.json`, `result.log`, `cloud-run.log`. 235,19 saniye, 1024×640, 40 adım, extract-design. Kumaş ayrıldı; lacivert dolgu ve EST.1991 kaybı nedeniyle GEÇMEDİ. Eğitim veya ürün kabulü değildir.
- `comparison.png` onaylı referansı gerçek yeni çıktıyla karşılaştırır; sağ altta `gpu-stopped.png` gerçek ekranının fiyat alanı kırpımı bulunur. Ham sonuç rötuşlanmadı.
- Resmi GitHub kaynağı: https://github.com/modelscope/DiffSynth-Studio . Lisans GitHub API'den Apache-2.0 doğrulandı. Revision: d188f01d09013688dea27cc28f2e8dc0953c2543.
- Tam 2511 LoRA örneği: https://github.com/modelscope/DiffSynth-Studio/blob/d188f01d09013688dea27cc28f2e8dc0953c2543/examples/qwen_image/model_training/lora/Qwen-Image-Edit-2511.sh . Eğitim kodu aynı revision'da `examples/qwen_image/model_training/train.py`. Ham kopyalar deney klasöründedir. Bu doküman incelemesi gerçek eğitim/VRAM kabulü değildir; mevcut GGUF paketinin eğitilebilir olduğunu kanıtlamaz.
- Ekran kapanışında iki pod da PRIVATE_AMOUNT/saat; son görünen bakiye PRIVATE_AMOUNT. Oturum farkı PRIVATE_AMOUNT. Ayrıntı ve sonraki aşamanın sınırları deney `SONUC.md` içindedir.

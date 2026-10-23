# ai-ajans-otomasyon — mimari

AI ajans otomasyonu; bulunan admin, ürün, kurulum ve test aşama kopyaları.

## İşleyiş

Admin/UI → center/runtime servisleri → Docker Compose ve işçi bileşenleri. stage-* klasörleri farklı geliştirme aşamalarıdır; bulunmayan C:/ai-ajans ana kurulumunun tam yerine geçtiği varsayılmaz.

## Kaynak ve sürüm ayrımı

`source/` altındaki ayrı kopyalar birleştirilmedi. `current`, `development`, `versions-and-development`, `archive-snapshots` ve `embedded-snapshots` mevcut olduğunda farklı dönemleri temsil eder. Klasör adı tek başına sürüm doğrulaması değildir; sürüm manifestleri esas alınır.

## Bileşen haritası

- [Run-FreeLocalEndToEndTest.ps1](source/staged-development/Run-FreeLocalEndToEndTest.ps1)
- [Run-FreeLocalEndToEndTest.staged.ps1](source/staged-development/Run-FreeLocalEndToEndTest.staged.ps1)
- [app-center-staged.js](source/staged-development/app-center-staged.js)
- [Update-SupplyChainInventory.ps1](source/staged-development/local-delivery-stage/Update-SupplyChainInventory.ps1)
- [local-delivery.test.mjs](source/staged-development/local-delivery-stage/tests/local-delivery.test.mjs)
- [runtime-hardening.test.mjs](source/staged-development/local-delivery-stage/tests/runtime-hardening.test.mjs)
- [app.js](source/staged-development/local-delivery-stage/ui/ajans-merkezi/public/app.js)
- [server.mjs](source/staged-development/local-delivery-stage/ui/ajans-runtime/server.mjs)
- [app.js](source/staged-development/stage-admin-full/public/app.js)
- [client.js](source/staged-development/stage-admin-full/public/client.js)
- [server.mjs](source/staged-development/stage-admin-full/server.mjs)
- [Update-SupplyChainInventory.ps1](source/staged-development/stage-admin/Update-SupplyChainInventory.ps1)
- [app.js](source/staged-development/stage-admin/public/app.js)
- [client.js](source/staged-development/stage-admin/public/client.js)
- [server.mjs](source/staged-development/stage-admin/server.mjs)
- [Start-AiAjans.ps1](source/staged-development/stage-product/Start-AiAjans.ps1)
- [center-server.mjs](source/staged-development/stage-product/center-server.mjs)
- [app.js](source/staged-development/stage-product/public/app.js)
- [runtime-server.mjs](source/staged-development/stage-product/runtime-server.mjs)
- [Install-AjansKurucu.ps1](source/staged-development/stage-root-files/Install-AjansKurucu.ps1)
- [New-AjansKurucuKurulumPaketi.ps1](source/staged-development/stage-root-files/New-AjansKurucuKurulumPaketi.ps1)
- [Start-AjansKurucu.ps1](source/staged-development/stage-root-files/Start-AjansKurucu.ps1)
- [Update-SupplyChainInventory.ps1](source/staged-development/stage-root-files/Update-SupplyChainInventory.ps1)
- [creator-package.test.ps1](source/staged-development/stage-root-files/creator-package.test.ps1)
- [Complete-CloudflareImageTest.ps1](source/staged-development/stage-ui/Complete-CloudflareImageTest.ps1)
- [app.js](source/staged-development/stage-ui/app.js)
- [Complete-CloudflareImageTest.ps1](source/staged-development/staging/Complete-CloudflareImageTest.ps1)
- [account-binding.test.mjs](source/staged-development/test-compat-stage/account-binding.test.mjs)
- [disk-pressure-atomicity.test.mjs](source/staged-development/test-compat-stage/disk-pressure-atomicity.test.mjs)
- [golden-safety.test.mjs](source/staged-development/test-compat-stage/golden-safety.test.mjs)
- [orchestration-pipeline.test.mjs](source/staged-development/test-compat-stage/orchestration-pipeline.test.mjs)
- [runtime-hardening.test.mjs](source/staged-development/test-compat-stage/runtime-hardening.test.mjs)
- [scheduler-worker-failclosed.test.mjs](source/staged-development/test-compat-stage/scheduler-worker-failclosed.test.mjs)
- [worker-pipeline.test.mjs](source/staged-development/test-compat-stage/worker-pipeline.test.mjs)

## Teknik belgeler

- [AGENTS.md](source/staged-development/AGENTS.md)
- [PROJECT_STATE.staged.md](source/staged-development/PROJECT_STATE.staged.md)
- [01_PROJE_HARITASI.md](source/staged-development/artifacts/Trendy-Brander-GPT/01_PROJE_HARITASI.md)
- [02_AJANLAR_VE_AKIS.md](source/staged-development/artifacts/Trendy-Brander-GPT/02_AJANLAR_VE_AKIS.md)
- [03_ANA_UYGULAMA_VE_AJANS_UYGULAMASI.md](source/staged-development/artifacts/Trendy-Brander-GPT/03_ANA_UYGULAMA_VE_AJANS_UYGULAMASI.md)
- [04_GUVENLIK_HAFIZA_TOKEN.md](source/staged-development/artifacts/Trendy-Brander-GPT/04_GUVENLIK_HAFIZA_TOKEN.md)
- [05_SORUN_GIDERME.md](source/staged-development/artifacts/Trendy-Brander-GPT/05_SORUN_GIDERME.md)
- [06_GELISTIRME_VE_GUNCELLIK.md](source/staged-development/artifacts/Trendy-Brander-GPT/06_GELISTIRME_VE_GUNCELLIK.md)
- [GPT_INSTRUCTIONS.txt](source/staged-development/artifacts/Trendy-Brander-GPT/GPT_INSTRUCTIONS.txt)
- [README.md](source/staged-development/artifacts/Trendy-Brander-GPT/README.md)
- [README-APPROVED.md](source/staged-development/local-delivery-stage/README-APPROVED.md)
- [KULLANIM_KILAVUZU.md](source/staged-development/stage-admin-full/KULLANIM_KILAVUZU.md)
- [KULLANIM_KILAVUZU.md](source/staged-development/stage-admin/KULLANIM_KILAVUZU.md)
- [PROJECT_STATE.md](source/staged-development/stage-root-files/PROJECT_STATE.md)

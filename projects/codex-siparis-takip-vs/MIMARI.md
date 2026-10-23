# siparis-takip-vs — mimari

Bağımsız Electron Sipariş Takip VS uygulaması; bulunan kurtarılmış kaynak ve hosted arayüz.

## İşleyiş

Electron main/preload → hosted arayüz → OAuth ve WhatsApp aktarım köprüleri. Bu bağımsız uygulamanın kaynakları eski Sipariş Takip ile karıştırılmamalıdır. Hosted derlenmiş arayüz korunmuştur; özgün frontend geliştirme kaynağının tamlığı doğrulanmamıştır.

## Kaynak ve sürüm ayrımı

`source/` altındaki ayrı kopyalar birleştirilmedi. `current`, `development`, `versions-and-development`, `archive-snapshots` ve `embedded-snapshots` mevcut olduğunda farklı dönemleri temsil eder. Klasör adı tek başına sürüm doğrulaması değildir; sürüm manifestleri esas alınır.

## Bileşen haritası

- [desktop-oauth.cjs](source/recovered/desktop-oauth.cjs)
- [index-DSKCXCck.js](source/recovered/hosted/assets/index-DSKCXCck.js)
- [index-readable.js](source/recovered/hosted/assets/index-readable.js)
- [main.cjs](source/recovered/main.cjs)
- [preload.cjs](source/recovered/preload.cjs)
- [capture_ui.mjs](source/recovered/scripts/capture_ui.mjs)
- [diagnose-whatsapp-login-cdp.mjs](source/recovered/scripts/diagnose-whatsapp-login-cdp.mjs)
- [fix-kadir-import.mjs](source/recovered/scripts/fix-kadir-import.mjs)
- [inspect-current-chat-cdp.mjs](source/recovered/scripts/inspect-current-chat-cdp.mjs)
- [inspect-sidebar-cdp.mjs](source/recovered/scripts/inspect-sidebar-cdp.mjs)
- [inspect-whatsapp-cdp.mjs](source/recovered/scripts/inspect-whatsapp-cdp.mjs)
- [inspect-whatsapp-files-cdp.mjs](source/recovered/scripts/inspect-whatsapp-files-cdp.mjs)
- [open-polat-cdp.mjs](source/recovered/scripts/open-polat-cdp.mjs)
- [open_customers.mjs](source/recovered/scripts/open_customers.mjs)
- [verify_ui.mjs](source/recovered/scripts/verify_ui.mjs)
- [whatsapp-qr-probe.cjs](source/recovered/scripts/whatsapp-qr-probe.cjs)
- [whatsapp-extractor.cjs](source/recovered/whatsapp-extractor.cjs)
- [whatsapp-preload.cjs](source/recovered/whatsapp-preload.cjs)

## Teknik belgeler

- [SIPARIS_TAKIP_VS_CONTEXT.md](source/recovered/SIPARIS_TAKIP_VS_CONTEXT.md)

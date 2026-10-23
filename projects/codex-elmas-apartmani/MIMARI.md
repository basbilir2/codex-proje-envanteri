# elmas-apartmani — mimari

Electron masaüstü, Apps Script ve çevrimdışı apartman yönetimi uygulaması.

## İşleyiş

Electron masaüstü → preview/runtime ve yerel veri → Apps Script çevrimiçi sakin/işlem katmanı. Kurulum paketinin initial-data sözleşmesi boş veri şablonuyla korunur.

## Kaynak ve sürüm ayrımı

`source/` altındaki ayrı kopyalar birleştirilmedi. `current`, `development`, `versions-and-development`, `archive-snapshots` ve `embedded-snapshots` mevcut olduğunda farklı dönemleri temsil eder. Klasör adı tek başına sürüm doğrulaması değildir; sürüm manifestleri esas alınır.

## Bileşen haritası

- [ONIZLEME.ps1](source/development/outputs/Elmas-Apartmani/ONIZLEME.ps1)
- [Auth.gs](source/development/outputs/Elmas-Apartmani/apps-script/Auth.gs)
- [Code.gs](source/development/outputs/Elmas-Apartmani/apps-script/Code.gs)
- [Config.gs](source/development/outputs/Elmas-Apartmani/apps-script/Config.gs)
- [Files.gs](source/development/outputs/Elmas-Apartmani/apps-script/Files.gs)
- [Finance.gs](source/development/outputs/Elmas-Apartmani/apps-script/Finance.gs)
- [Import.gs](source/development/outputs/Elmas-Apartmani/apps-script/Import.gs)
- [Notifications.gs](source/development/outputs/Elmas-Apartmani/apps-script/Notifications.gs)
- [main.cjs](source/development/outputs/Elmas-Apartmani/desktop/main.cjs)
- [server.mjs](source/development/outputs/Elmas-Apartmani/desktop/server.mjs)
- [smoke.mjs](source/development/outputs/Elmas-Apartmani/desktop/smoke.mjs)
- [runtime.mjs](source/development/outputs/Elmas-Apartmani/preview/runtime.mjs)
- [server.mjs](source/development/outputs/Elmas-Apartmani/preview/server.mjs)
- [critical.mjs](source/development/outputs/Elmas-Apartmani/tests/critical.mjs)
- [Auth.gs](source/development/work/google-deploy/apps-script/Auth.gs)
- [Code.gs](source/development/work/google-deploy/apps-script/Code.gs)
- [Config.gs](source/development/work/google-deploy/apps-script/Config.gs)
- [Files.gs](source/development/work/google-deploy/apps-script/Files.gs)
- [Finance.gs](source/development/work/google-deploy/apps-script/Finance.gs)
- [Import.gs](source/development/work/google-deploy/apps-script/Import.gs)
- [Notifications.gs](source/development/work/google-deploy/apps-script/Notifications.gs)
- [create_drive_resources.mjs](source/development/work/google-deploy/create_drive_resources.mjs)
- [download-live-xlsx.mjs](source/development/work/google-deploy/work/download-live-xlsx.mjs)
- [export-live-backup.mjs](source/development/work/google-deploy/work/export-live-backup.mjs)
- [inspect-live.mjs](source/development/work/google-deploy/work/inspect-live.mjs)

## Teknik belgeler

- [KURULUM.md](source/development/outputs/Elmas-Apartmani/KURULUM.md)
- [MASAUSTU-KURULUM.md](source/development/outputs/Elmas-Apartmani/MASAUSTU-KURULUM.md)
- [STATUS.txt](source/development/work/google-deploy/STATUS.txt)

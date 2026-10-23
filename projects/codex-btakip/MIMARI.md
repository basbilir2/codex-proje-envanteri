# btakip — mimari

C# Windows Forms bakiye, müşteri, stok ve maliyet takip uygulaması; eski sürümler ve geliştirmeler.

## İşleyiş

Windows Forms Program/MainForm → müşteri/ürün/stok/maliyet ekranları → DataStore ve Models. GoogleCloudSyncService bulut eşitlemesini yürütür; ayrı Setup projesi uygulama çıktısını gömer. Sürüm kopyaları ve eski dijital yeniden kurma kayıtları ayrı yollarında korunur.

## Kaynak ve sürüm ayrımı

`source/` altındaki ayrı kopyalar birleştirilmedi. `current`, `development`, `versions-and-development`, `archive-snapshots` ve `embedded-snapshots` mevcut olduğunda farklı dönemleri temsil eder. Klasör adı tek başına sürüm doğrulaması değildir; sürüm manifestleri esas alınır.

## Bileşen haritası

| Dosya | Rol |
|---|---|
| [Program.cs](source/converter-development/working/converter-check/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [inspect.mjs](source/converter-development/working/excel-converter-inspect/inspect.mjs) | kaynak modülü/betik; ayrıntı kodda |
| [analyze.mjs](source/converter-development/working/AnonPerson_0001-btakip/analyze.mjs) | kaynak modülü/betik; ayrıntı kodda |
| [build.mjs](source/converter-development/working/AnonPerson_0001-btakip/build.mjs) | derleme/paketleme |
| [extract.mjs](source/converter-development/working/AnonPerson_0001-btakip/extract.mjs) | kaynak modülü/betik; ayrıntı kodda |
| [inspect.mjs](source/converter-development/working/AnonPerson_0001-btakip/inspect.mjs) | kaynak modülü/betik; ayrıntı kodda |
| [verify.mjs](source/converter-development/working/AnonPerson_0001-btakip/verify.mjs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/early-development/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [CloudConfiguration.cs](source/early-development/BTakip/CloudConfiguration.cs) | yapılandırma |
| [DataStore.cs](source/early-development/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [GoogleCloudSyncService.cs](source/early-development/BTakip/GoogleCloudSyncService.cs) | eşitleme |
| [ImportedOrderPricing.cs](source/early-development/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/early-development/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/early-development/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/early-development/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/early-development/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/early-development/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/early-development/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/early-development/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/early-development/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [BTakipSync.gs](source/early-development/Google/BTakipSync.gs) | eşitleme |
| [Refresh-DigitalCopy.ps1](source/early-development/Tools/Refresh-DigitalCopy.ps1) | kaynak modülü/betik; ayrıntı kodda |
| [build.mjs](source/early-development/outputs/asi_reklam/build.mjs) | derleme/paketleme |
| [verify.mjs](source/early-development/outputs/asi_reklam/verify.mjs) | kaynak modülü/betik; ayrıntı kodda |
| [build.mjs](source/early-development/outputs/AnonPerson_0002_btakip/build.mjs) | derleme/paketleme |
| [inspect.mjs](source/early-development/outputs/AnonPerson_0002_btakip/inspect.mjs) | kaynak modülü/betik; ayrıntı kodda |
| [verify.mjs](source/early-development/outputs/AnonPerson_0002_btakip/verify.mjs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.4/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.4/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.4/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.4/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.4/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.4/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.4/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.4/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.4/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.4/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.4/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.7/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.7/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.7/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.7/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.7/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.7/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.7/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.7/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.7/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.7/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.7/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.8/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.8/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.8/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.8/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.8/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.8/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.8/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.8/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.8/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.8/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.8/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.0/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.0/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.0/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.0/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.0/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.0/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.0/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.0/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.0/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.0/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.0/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.1/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.1/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.1/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.1/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.1/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.1/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.1/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.1/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.1/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.1/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.1/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.12/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.12/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.12/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.12/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.12/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.12/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.12/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.12/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.12/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.12/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.12/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.15/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.15/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.15/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.15/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.15/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.15/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.15/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.15/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.15/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.15/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.15/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.16/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.16/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.16/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.16/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.16/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.16/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.16/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.16/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.16/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.16/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.16/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.17/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.17/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.17/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.17/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.17/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.17/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.17/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.17/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.17/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.17/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.17/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.18/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.18/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.18/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.18/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.18/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.18/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.18/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.18/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.18/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.18/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.18/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.19/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.19/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.19/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.19/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.19/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.19/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.19/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.19/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.19/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.19/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.19/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.20/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.20/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.20/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.20/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.20/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.20/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.20/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.20/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.20/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.20/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.20/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.21/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.21/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.21/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.21/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.21/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.21/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.21/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.21/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.21/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.21/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.21/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.22/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.22/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.22/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.22/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.22/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.22/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.22/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.22/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.22/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.22/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.22/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.23/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.23/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.23/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.23/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.23/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.23/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.23/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.23/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.23/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.23/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.23/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.24/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.24/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.24/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.24/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.24/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.24/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.24/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.24/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.24/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.24/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.24/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.25/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.25/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.25/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.25/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.25/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.25/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.25/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.25/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.25/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.25/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.25/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.26/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.26/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.26/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.26/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.26/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.26/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.26/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.26/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.26/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.26/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.26/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.27/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.27/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.27/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.27/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.27/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.27/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.27/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.27/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.27/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.27/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.27/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.28/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.28/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.28/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.28/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.28/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.28/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.28/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.28/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.28/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.28/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.28/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.29/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.29/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.29/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.29/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.29/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.29/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.29/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.29/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.29/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.29/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.29/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.3/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.3/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.3/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.3/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.3/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.3/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.3/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.3/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.3/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.3/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.3/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.30/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.30/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.30/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.30/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.30/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.30/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.30/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.30/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.30/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.30/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.30/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.32/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [CloudConfiguration.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.32/BTakip/CloudConfiguration.cs) | yapılandırma |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.32/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [GoogleCloudSyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.32/BTakip/GoogleCloudSyncService.cs) | eşitleme |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.32/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.32/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.32/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.32/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.32/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.32/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.32/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.32/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.32/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.4/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.4/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.4/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.4/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.4/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.4/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.4/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.4/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.4/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.4/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.4/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.40/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [CloudConfiguration.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.40/BTakip/CloudConfiguration.cs) | yapılandırma |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.40/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [GoogleCloudSyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.40/BTakip/GoogleCloudSyncService.cs) | eşitleme |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.40/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.40/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.40/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.40/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.40/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.40/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.40/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.40/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.40/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.42/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [CloudConfiguration.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.42/BTakip/CloudConfiguration.cs) | yapılandırma |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.42/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [GoogleCloudSyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.42/BTakip/GoogleCloudSyncService.cs) | eşitleme |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.42/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.42/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.42/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.42/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.42/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.42/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.42/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.42/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.42/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.5/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.5/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.5/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.5/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.5/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.5/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.5/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.5/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.5/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.5/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.5/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.6/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.6/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.6/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.6/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.6/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.6/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.6/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.6/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.6/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.6/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.6/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.7/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [DataStore.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.7/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.7/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.7/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.7/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.7/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.7/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.7/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.7/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.7/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.7/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/embedded-snapshots/BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [CloudConfiguration.cs](source/embedded-snapshots/BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30/BTakip/CloudConfiguration.cs) | yapılandırma |
| [DataStore.cs](source/embedded-snapshots/BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [GoogleCloudSyncService.cs](source/embedded-snapshots/BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30/BTakip/GoogleCloudSyncService.cs) | eşitleme |
| [ImportedOrderPricing.cs](source/embedded-snapshots/BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/embedded-snapshots/BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/embedded-snapshots/BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/embedded-snapshots/BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/embedded-snapshots/BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/embedded-snapshots/BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/embedded-snapshots/BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/embedded-snapshots/BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/embedded-snapshots/BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [apply-engine-prices.mjs](source/versions-and-development/outputs/01a0abba-9277-78e3-8274-5348d847bf45/apply-engine-prices.mjs) | işleme motoru |
| [build-AnonPerson_0003-import.mjs](source/versions-and-development/outputs/01a0abba-9277-78e3-8274-5348d847bf45/build-AnonPerson_0003-import.mjs) | derleme/paketleme |
| [clear-unknown-materials.mjs](source/versions-and-development/outputs/01a0abba-9277-78e3-8274-5348d847bf45/clear-unknown-materials.mjs) | kaynak modülü/betik; ayrıntı kodda |
| [import-live.ps1](source/versions-and-development/outputs/01a0abba-9277-78e3-8274-5348d847bf45/import-live.ps1) | kaynak modülü/betik; ayrıntı kodda |
| [inspect-source.mjs](source/versions-and-development/outputs/01a0abba-9277-78e3-8274-5348d847bf45/inspect-source.mjs) | kaynak modülü/betik; ayrıntı kodda |
| [test-temp-import.ps1](source/versions-and-development/outputs/01a0abba-9277-78e3-8274-5348d847bf45/test-temp-import.ps1) | doğrulama/kabul denemesi |
| [verify-AnonPerson_0003-import.mjs](source/versions-and-development/outputs/01a0abba-9277-78e3-8274-5348d847bf45/verify-AnonPerson_0003-import.mjs) | kaynak modülü/betik; ayrıntı kodda |
| [verify-live.ps1](source/versions-and-development/outputs/01a0abba-9277-78e3-8274-5348d847bf45/verify-live.ps1) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/versions-and-development/work/btakip-cloud-input-1.5.34/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [CloudConfiguration.cs](source/versions-and-development/work/btakip-cloud-input-1.5.34/BTakip/CloudConfiguration.cs) | yapılandırma |
| [DataStore.cs](source/versions-and-development/work/btakip-cloud-input-1.5.34/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [GoogleCloudSyncService.cs](source/versions-and-development/work/btakip-cloud-input-1.5.34/BTakip/GoogleCloudSyncService.cs) | eşitleme |
| [ImportedOrderPricing.cs](source/versions-and-development/work/btakip-cloud-input-1.5.34/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/versions-and-development/work/btakip-cloud-input-1.5.34/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/versions-and-development/work/btakip-cloud-input-1.5.34/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/versions-and-development/work/btakip-cloud-input-1.5.34/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/versions-and-development/work/btakip-cloud-input-1.5.34/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/versions-and-development/work/btakip-cloud-input-1.5.34/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/versions-and-development/work/btakip-cloud-input-1.5.34/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [SyncService.cs](source/versions-and-development/work/btakip-cloud-input-1.5.34/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/versions-and-development/work/btakip-cloud-input-1.5.34/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [BTakipSync.gs](source/versions-and-development/work/btakip-cloud-input-1.5.34/Google/BTakipSync.gs) | eşitleme |
| [Refresh-DigitalCopy-1.5.34.ps1](source/versions-and-development/work/btakip-cloud-input-1.5.34/Refresh-DigitalCopy-1.5.34.ps1) | kaynak modülü/betik; ayrıntı kodda |
| [build.mjs](source/versions-and-development/work/btakip-cloud-input-1.5.34/outputs/asi_reklam/build.mjs) | derleme/paketleme |
| [verify.mjs](source/versions-and-development/work/btakip-cloud-input-1.5.34/outputs/asi_reklam/verify.mjs) | kaynak modülü/betik; ayrıntı kodda |
| [build.mjs](source/versions-and-development/work/btakip-cloud-input-1.5.34/outputs/AnonPerson_0002_btakip/build.mjs) | derleme/paketleme |
| [inspect.mjs](source/versions-and-development/work/btakip-cloud-input-1.5.34/outputs/AnonPerson_0002_btakip/inspect.mjs) | kaynak modülü/betik; ayrıntı kodda |
| [verify.mjs](source/versions-and-development/work/btakip-cloud-input-1.5.34/outputs/AnonPerson_0002_btakip/verify.mjs) | kaynak modülü/betik; ayrıntı kodda |
| [Program.cs](source/versions-and-development/work/btakip-stock-1.5.43/BTakip.Setup/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [CloudConfiguration.cs](source/versions-and-development/work/btakip-stock-1.5.43/BTakip/CloudConfiguration.cs) | yapılandırma |
| [DataStore.cs](source/versions-and-development/work/btakip-stock-1.5.43/BTakip/DataStore.cs) | kalıcılık ve veri işlemleri |
| [GoogleCloudSyncService.cs](source/versions-and-development/work/btakip-stock-1.5.43/BTakip/GoogleCloudSyncService.cs) | eşitleme |
| [ImportedOrderPricing.cs](source/versions-and-development/work/btakip-stock-1.5.43/BTakip/ImportedOrderPricing.cs) | fiyat hesaplama |
| [MainForm.cs](source/versions-and-development/work/btakip-stock-1.5.43/BTakip/MainForm.cs) | uygulama başlangıcı veya Electron ana süreci |
| [Models.cs](source/versions-and-development/work/btakip-stock-1.5.43/BTakip/Models.cs) | veri/model sözleşmeleri |
| [PricingEngine.cs](source/versions-and-development/work/btakip-stock-1.5.43/BTakip/PricingEngine.cs) | fiyat hesaplama |
| [Program.cs](source/versions-and-development/work/btakip-stock-1.5.43/BTakip/Program.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SimpleXlsx.cs](source/versions-and-development/work/btakip-stock-1.5.43/BTakip/SimpleXlsx.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SmokeTests.cs](source/versions-and-development/work/btakip-stock-1.5.43/BTakip/SmokeTests.cs) | doğrulama/kabul denemesi |
| [StockControl.cs](source/versions-and-development/work/btakip-stock-1.5.43/BTakip/StockControl.cs) | kaynak modülü/betik; ayrıntı kodda |
| [StockPage.cs](source/versions-and-development/work/btakip-stock-1.5.43/BTakip/StockPage.cs) | kaynak modülü/betik; ayrıntı kodda |
| [SyncService.cs](source/versions-and-development/work/btakip-stock-1.5.43/BTakip/SyncService.cs) | eşitleme |
| [UiTheme.cs](source/versions-and-development/work/btakip-stock-1.5.43/BTakip/UiTheme.cs) | kaynak modülü/betik; ayrıntı kodda |
| [build_btakip_digital_twin.ps1](source/versions-and-development/work/build_btakip_digital_twin.ps1) | derleme/paketleme |

## Ayrıntılı mevcut mimari ve geliştirme kayıtları

- [AGENTS.md](source/converter-development/AGENTS.md)
- [AGENTS.md](source/early-development/AGENTS.md)
- [BTakip_Hizli_Baglam_v1.5.12.md](source/early-development/BTakip_Hizli_Baglam_v1.5.12.md)
- [BTakip_Hizli_Baglam_v1.5.15.md](source/early-development/BTakip_Hizli_Baglam_v1.5.15.md)
- [BTakip_Hizli_Baglam_v1.5.16.md](source/early-development/BTakip_Hizli_Baglam_v1.5.16.md)
- [BTakip_Hizli_Baglam_v1.5.17.md](source/early-development/BTakip_Hizli_Baglam_v1.5.17.md)
- [BTakip_Hizli_Baglam_v1.5.18.md](source/early-development/BTakip_Hizli_Baglam_v1.5.18.md)
- [BTakip_Hizli_Baglam_v1.5.19.md](source/early-development/BTakip_Hizli_Baglam_v1.5.19.md)
- [BTakip_Hizli_Baglam_v1.5.20.md](source/early-development/BTakip_Hizli_Baglam_v1.5.20.md)
- [BTakip_Hizli_Baglam_v1.5.21.md](source/early-development/BTakip_Hizli_Baglam_v1.5.21.md)
- [BTakip_Hizli_Baglam_v1.5.22.md](source/early-development/BTakip_Hizli_Baglam_v1.5.22.md)
- [BTakip_Hizli_Baglam_v1.5.23.md](source/early-development/BTakip_Hizli_Baglam_v1.5.23.md)
- [BTakip_Hizli_Baglam_v1.5.24.md](source/early-development/BTakip_Hizli_Baglam_v1.5.24.md)
- [BTakip_Hizli_Baglam_v1.5.25.md](source/early-development/BTakip_Hizli_Baglam_v1.5.25.md)
- [BTakip_Hizli_Baglam_v1.5.26.md](source/early-development/BTakip_Hizli_Baglam_v1.5.26.md)
- [BTakip_Hizli_Baglam_v1.5.27.md](source/early-development/BTakip_Hizli_Baglam_v1.5.27.md)
- [BTakip_Hizli_Baglam_v1.5.28.md](source/early-development/BTakip_Hizli_Baglam_v1.5.28.md)
- [BTakip_Hizli_Baglam_v1.5.29.md](source/early-development/BTakip_Hizli_Baglam_v1.5.29.md)
- [BTakip_Hizli_Baglam_v1.5.30.md](source/early-development/BTakip_Hizli_Baglam_v1.5.30.md)
- [BTakip_Hizli_Baglam_v1.5.32.md](source/early-development/BTakip_Hizli_Baglam_v1.5.32.md)
- [KURULUM.md](source/early-development/Google/KURULUM.md)
- [TESLIM.md](source/early-development/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.4/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.4/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.4/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.7/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.7/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.7/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.8/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.8/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.4.8/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.0/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.0/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.0/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.1/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.1/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.1/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.12/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.12/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.12/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.15/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.15/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.15/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.16/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.16/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.16/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.17/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.17/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.17/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.18/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.18/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.18/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.19/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.19/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.19/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.20/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.20/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.20/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.21/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.21/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.21/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.22/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.22/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.22/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.23/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.23/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.23/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.24/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.24/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.24/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.25/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.25/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.25/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.26/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.26/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.26/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.27/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.27/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.27/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.28/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.28/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.28/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.29/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.29/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.29/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.3/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.3/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.3/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.30/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.30/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.30/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.32/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.32/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.32/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.4/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.4/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.4/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.40/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.40/Google/KURULUM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.42/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.42/Google/KURULUM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.5/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.5/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.5/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.6/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.6/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.6/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.7/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.7/Google/KURULUM.md)
- [TESLIM.md](source/embedded-snapshots/BTakip_Dijital_Kopya_v1.5.7/TESLIM.md)
- [AGENTS.md](source/embedded-snapshots/BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30/AGENTS.md)
- [KURULUM.md](source/embedded-snapshots/BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30/Google/KURULUM.md)
- [AGENTS.md](source/versions-and-development/work/btakip-cloud-input-1.5.34/AGENTS.md)
- [BTakip_Hizli_Baglam_v1.5.40.md](source/versions-and-development/work/btakip-cloud-input-1.5.34/BTakip_Hizli_Baglam_v1.5.40.md)
- [BTakip_Hizli_Baglam_v1.5.42.md](source/versions-and-development/work/btakip-cloud-input-1.5.34/BTakip_Hizli_Baglam_v1.5.42.md)
- [BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30.md](source/versions-and-development/work/btakip-cloud-input-1.5.34/BTakip_Tam_Yeniden_Kurma_1.5.42_2026-09-30.md)
- [KURULUM.md](source/versions-and-development/work/btakip-cloud-input-1.5.34/Google/KURULUM.md)
- [TESLIM.md](source/versions-and-development/work/btakip-cloud-input-1.5.34/TESLIM.md)
- [btakip_context_base.json](source/versions-and-development/work/btakip_context_base.json)

İçe aktarmalar ve üst düzey semboller: [MODULES.json](reconstruction/MODULES.json).

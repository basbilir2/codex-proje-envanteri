# thesap — mimari

BTakip uygulamasından bağımsız C# fiyat hesaplama uygulaması ve kurucu projesi.

## İşleyiş

Program/MainForm → PricingEngine ve PriceManagementForm → CatalogStore/Models/SeedData. THesap.Setup uygulama EXE çıktısını Payload kaynağı olarak gömer. Canlı katalog verisi yerine boş yapısal şablon kullanılır.

## Kaynak ve sürüm ayrımı

`source/` altındaki ayrı kopyalar birleştirilmedi. `current`, `development`, `versions-and-development`, `archive-snapshots` ve `embedded-snapshots` mevcut olduğunda farklı dönemleri temsil eder. Klasör adı tek başına sürüm doğrulaması değildir; sürüm manifestleri esas alınır.

## Bileşen haritası

- [CatalogStore.cs](source/current/work/THesap/CatalogStore.cs)
- [MainForm.cs](source/current/work/THesap/MainForm.cs)
- [Models.cs](source/current/work/THesap/Models.cs)
- [PriceManagementForm.cs](source/current/work/THesap/PriceManagementForm.cs)
- [PricingEngine.cs](source/current/work/THesap/PricingEngine.cs)
- [Program.cs](source/current/work/THesap/Program.cs)
- [SeedData.cs](source/current/work/THesap/SeedData.cs)
- [SmokeTests.cs](source/current/work/THesap/SmokeTests.cs)
- [Program.cs](source/current/work/THesap/THesap.Setup/Program.cs)
- [UiTheme.cs](source/current/work/THesap/UiTheme.cs)

## Teknik belgeler

- [README.md](source/current/work/THesap/README.md)

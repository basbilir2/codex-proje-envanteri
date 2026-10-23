# Elmas Apartmanı Masaüstü

## Kurulum

`Elmas-Apartmani-Kurulum-2.1.0.exe` dosyasını çalıştırın. Program masaüstü ve Başlat menüsü kısayollarını oluşturur ve Windows **Ayarlar → Uygulamalar → Yüklü uygulamalar** listesine eklenir.

Masaüstü programı yönetici parolası istemeden doğrudan açılır. Asıl kayıtlar bilgisayarda `%APPDATA%\Elmas Apartmanı\elmas-veri.json` dosyasında tutulur. Kurulum paketi, 17 Eylül 2026 tarihinde canlı sistemden alınan 9 dairelik mevcut kayıtla başlar.

## Yedekleme ve yeni bilgisayara taşıma

**Ayarlar → Veriler ve yedekler → JSON yedek al** ile yedeği indirin. Yeni bilgisayarda programı kurduktan sonra **Yedekten içe aktar** düğmesiyle aynı JSON dosyasını seçin. İçe aktarmadan önce mevcut yerel veri ayrıca otomatik yedeklenir.

## Çevrimiçi sakin ekranı

Masaüstünde yapılan değişiklikler mevcut Google Sheets ve salt okunur sakin bağlantılarına otomatik gönderilir. İnternet yokken program yerel kayıtlarla çalışmaya devam eder; **Şimdi eşitle** düğmesiyle bağlantı geldiğinde tekrar eşitleyebilirsiniz.

Sakinler yalnız kendi dairesini ve kimliksiz apartman toplamlarını görür. Diğer dairelerin borç sahipleri gösterilmez.

## Kaldırma

Windows **Yüklü uygulamalar** listesinden **Elmas Apartmanı** kaldırılabilir. Kaldırma ekranı verilerin saklanıp saklanmayacağını sorar. **Verilerimi sakla** seçili bırakılırsa daha sonra yeniden kurulduğunda kayıtlar geri gelir.

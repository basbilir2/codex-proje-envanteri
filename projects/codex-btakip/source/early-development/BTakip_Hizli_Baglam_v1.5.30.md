# BTakip — Hızlı Çalışma Bağlamı

Bu dosya, yeni bir sohbette geçmişin tamamını taramadan BTakip üzerinde güvenli ve tutarlı çalışmak içindir. Önce bunu oku; yalnızca gerekli bölüm ve dosyalara in.

## Tek kaynaklar ve yollar

| Amaç | Yol |
|---|---|
| Kaynak kodun doğrulanmış ana kopyası | `C:\Users\USER\.codex\.chatgpt-projects\g-p-6a90780738548191ae5faed84f00ea9f` |
| Ayrıntılı dijital kopya / tüm gömülü kaynak metinleri | `BTakip_Dijital_Kopya_v1.5.30.json` |
| Kurulu uygulama | `C:\Users\USER\AppData\Local\BTakip\BTakip.exe` |
| Canlı müşteri, fiyat ve cari verisi | `C:\Users\USER\btakip\btakip-veri.json` |
| Güncel uygulama sürümü | `1.5.30` |

Canlı veri ile kaynak kodu birbirine karıştırma. Kaynak değişikliği canlı müşteri hareketlerini değiştirmez. Canlı veriye müdahale gerekiyorsa önce uygulamayı kapat, `btakip-veri.json` yedeğini al ve yalnız istenen kayıtları değiştir.

## Yeni sohbette izlenecek kısa yol

1. Bu dosyayı oku.
2. `BTakip_Dijital_Kopya_v1.5.30.json` içinden sadece istekle ilgili bölümü oku:
   - Genel mimari / formül: `business_rules_and_formulas`
   - Kullanıcı ekranı: `ui_specification`
   - Excel: `excel_io`
   - Son geliştirmeler: `current_release_additions`
   - Kesin kod davranışı gerekiyorsa `embedded_files` içindeki ilgili dosyanın `exact_content` alanı.
3. Sonra yalnız ilgili gerçek kaynak dosyasını aç. Ana dosyalar:
   - Arayüz, fiyat tanımı, cari düzenleme: `BTakip/MainForm.cs`
   - Hesaplama: `BTakip/PricingEngine.cs`
   - Veri kayıt/geri alma: `BTakip/DataStore.cs`
   - Veri modeli: `BTakip/Models.cs`
   - Excel dönüştürme/aktarımı: `BTakip/SimpleXlsx.cs`
   - Kurulum: `BTakip.Setup/Program.cs`
4. Müşteri veya cari sorusu varsa yalnız o müşterinin `CustomerId` kaydını ve ilgili `Orders` / `Payments` satırlarını canlı JSON’dan incele.
5. İstenen dar değişikliği yap; geniş refactor, tüm sohbet geçmişi taraması ve ilgisiz test yapma.

## Değişmeyecek iş kuralları

### Müşteri, fiyat grubu ve ürün ayrımı

- Her müşteri kartında bir `PriceGroupId` vardır. Sipariş satış fiyatı müşterinin kartındaki grubun oranından gelir.
- Cari sayfasında sipariş için ayrıca fiyat grubu seçilmez. Siparişin `PriceGroupId` alanı, hesaplama sırasında müşteri kartından güncellenir.
- Fiyat Hesaplama ekranı müşteri değil, yalnız fiyat kategorisi / kâr oranı seçer.
- Bir ürünün alış maliyeti (`UnitCost`) müşteriden bağımsız tek değerdir.
- Ürüne özel kâr tanımlanabilir, ancak bu **ürün + müşteri grubu** eşleşmesine aittir. Veri alanı `PriceItem.GroupProfitPercentOverrides` sözlüğüdür.
- Özel ürün-grup oranı varsa genel grup oranını ezer; yoksa `PriceGroup.CostMultiplier` kullanılır.
- Örnek: `Branda / Arkası Siyah` için `Reklamcı / Fason` özel `%80` olabilir; Perakende ve diğer gruplar kendi standart oranlarıyla hesaplanır.
- Özel oran seçeneğini kullanıcı kaldırmadan kaldırma. Fiyat tanımı formunda her grup için adsız aç/kapat kutusu ve yüzde kutusu vardır. Kutunun kapalı olması standart oran demektir.

### Fiyat formülü

Temel satış kuralı:

```text
toplam maliyet = birim maliyet × formülün ürettiği kullanım miktarı
satış = toplam maliyet × müşteri grubunun çarpanı
```

Özel ürün-grup kârı varsa:

```text
satış = toplam maliyet × (1 + özel_kâr_yüzdesi / 100)
```

- Fason / `dealer`: çarpan `2` yani standart `%100` kâr.
- Sürekli müşteri / `regular`: çarpan `2,8` yani standart `%180` kâr.
- Çevre esnafı / `trades`: çarpan `3` yani standart `%200` kâr.
- Perakende / `retail`: çarpan `4` yani standart `%300` kâr.
- Manuel alternatif yüzde varsa, hesaplama onu korur; yeni fiyat tanımıyla yeniden hesaplamada da silinmez.

### Ölçü kaydı ve cari yeniden hesaplama

- Cari tablosundaki Ölçü hücresi şu biçimleri kabul eder: `120 x 250 cm`, `5 m²`, `3,8 m`, `2,5 x 3 m`.
- `2,5 x 3 m` metin biçimi cm değildir. Kaydedildiğinde cm alanları sıfırlanır ve `AreaM2=7,5` kalıcı yazılır; tabloda `7,5 m²` görünür.
- Ölçü veya malzeme değiştirilirse, bulunabilen fiyat tanımı ve müşterinin kart fiyat grubu ile maliyet, satış ve borç yeniden hesaplanır.
- Fiyat Tanımları’nda ürün kaydedildiğinde o ürünle eşleşen aktif siparişler de yeniden hesaplanır. Eşleşme önce sipariş satırlarındaki `PriceItemId`, sonra `Material == DisplayName` üzerinden yapılır.
- Bu davranış 1.5.12’de eklendi. Eski fiyatla kaydedilmiş bir ürün için ilgili fiyat tanımında bir kez `Ürünü Güncelle` yapılması geçmiş siparişleri güncel tanıma taşır.
- Sipariş silinmişse otomatik yeniden hesaplanmaz.

## Veri ve hesap güvenliği

- Borç, siparişin `SaleTotalTl` alanıdır; tahsilat `Payment.AmountTl` alanıdır; bakiye borç eksi tahsilattır.
- Cari satırındaki borç/bakiye düzenlemesi sadece kullanıcı onayından sonra kaydedilir. Kullanıcı gerçekten değer değiştirmediyse kaydetme sorusu çıkmamalıdır.
- Fiyat tanımındaki ürün maliyetini değiştirmek müşteri grubunu değiştirmez; her sipariş müşteri kartındaki gruptan fiyatlanır.
- Tanım bulunamayan veya ölçü birimi belirsiz eski Excel satırlarına fiyat uydurma. Açıklamaya `KONTROL:` notu düş veya kullanıcıdan birim iste.
- Eski kaynakta `2,5 x 3` gibi bir ölçüde birim yoksa m mi cm mi olduğu doğrulanmadan hesap yapılmaz.
- Gerçek müşteri hareketlerini geniş çapta yeniden yazmadan önce yalnız etkilenecek satırları raporla; kullanıcı açıkça isterse uygula.

## Fiyat tanımı ekranının doğası

- Her kayıt tek türdedir: `Malzeme`, `Baskı` veya `Hizmet`.
- Baskı kaydında kullanılacak malzeme seçilir.
- Hizmet, ayrı bir kayıt olarak eklenir; sadece hizmet eklenebilmelidir.
- Bir ürün eklerken gerekmeyen ölçü alanlarını zorunlu tutma. Folyo/Branda gibi m² ürünlerde ölçü sipariş/fiyat hesaplama anında girilir; tanımda ad ve maliyet yeterlidir.
- Levha alanı için en, boy ve kalınlık; dakika hizmeti için süre; m² ürün için alan gerekir. Form yalnız seçili tür/formül için ilgili alanları göstermelidir.
- Tablo satırına tıklamak o kaydı forma yüklemeli; sütun düzenlemeleri de kaydedilebilir olmalıdır.

## Cari, müşteri, çıktı ve Excel sözleşmesi

- Müşteriler sayfasında müşteri adına tıklamak müşteri hesabına gitmelidir; müşteri güncelleme değildir.
- Cari & Tahsilat panelinde tahsilat, sipariş, Excel içe aktarım, müşteriye not yolla ve dışa aktarım bulunur.
- Dışa aktarım PDF veya Excel olmalıdır. Müşteriye gönderilen not PDF’inde okunabilir punto ve düzenli kolonlar kullanılmalıdır.
- Cari & Tahsilat > Dışa Aktar menüsü; seçili müşterinin hesabını, Ctrl ile seçilmiş cari hareketlerini, Müşteriler tablosunda Ctrl ile seçilmiş hesapları veya tüm müşteri hesaplarını PDF ya da Excel olarak dışa aktarabilmelidir.
- Cari tablosundaki seçili hareketler dışa aktarılırken tarih filtresi tekrar daraltmaz; yalnız kullanıcının seçtiği satırlar çıkarılır. Tek müşterinin normal dışa aktarımında tarih filtresi geçerlidir.
- Seçili veya tüm müşteri hesaplarının Excel dosyasında `Hesap Özetleri` ve `Hareketler` sayfaları bulunur. Her hareket satırında müşteri adı da yazılır.
- Fiyat grubu müşteri kartının alanıdır; cari sipariş ekleme panelinde ayrı fiyat grubu seçeneği bulunmaz.
- Excel dönüştürme kaynak dosya adını, tarih/açıklama/malzeme/ölçü alanlarını ayırır. Fiyat motoru yalnız tanım ve ölçü yeterliyse hesap yapar; belirsiz kayıtlar korunur ve kontrol edilir.
- Kaynak Excel’i değiştirme. Aynı müşteri için anlamlı tüm alanları aynı olan gerçek tekrarlar atlanır; benzer ama farklı hareketler korunur.

## Kurulum ve sürüm kuralı

- Kaynakta sürüm hem `BTakip/BTakip.csproj` hem `BTakip.Setup/BTakip.Setup.csproj` içinde aynı anda artırılır.
- Uygulama EXE’si `BTakip.Setup/Payload/BTakip_Portable.exe` içine yerleştirilmeden kurulum üretilmez.
- Aynı sürüm numarasıyla farklı EXE kurmak bütünlük uyarısı üretir. Her değişiklikte yeni sürüm üret.
- Kurulumdan önce BTakip’i kapat; kurulum canlı `btakip-veri.json` verisini korumalıdır.
- Kurulum sonrası yalnız odaklı doğrulama yap: sürüm numarası ve görünür `İzmirde Reklam` penceresi. Geniş test çalıştırma.

## Kullanıcı çalışma tercihleri

- Kullanıcı “token dostu” çalışma ister: sadece istenen dosya/bölüm incelenir, gereksiz test ve tekrar yapılmaz.
- Önceden eklenmiş bir özellik, kullanıcı açıkça kaldır demeden kaldırılmaz.
- Gereksiz varsayım yapma. Özellikle maliyet, metrekare birimi, müşteri grubu ve geçmiş fiyatlarda önce veriyle doğrula.
- Yapılan değişikliğin sonucu kısa ve doğrudan söylenir; gerekirse ilgili dosya bağlantısı verilir.

## Ayrıntı gerektiğinde

`BTakip_Dijital_Kopya_v1.5.30.json` aynı klasördedir ve 24 kaynak dosyanın 1.5.30 sürümündeki birebir metnini içerir. Cari sipariş, dışa aktarma veya Excel işi için önce bu Markdown’daki kuralları, ardından yalnız `BTakip/MainForm.cs` ve gerektiğinde `BTakip/SimpleXlsx.cs` dosyalarını oku; canlı değerler için ise `C:\Users\USER\btakip\btakip-veri.json` nihai otoritedir.

## 1.5.13 ek notu — kapsamlı dışa aktarma

- Müşteriler ve Cari & Tahsilat ekranındaki `Dışa Aktar` menüsü seçili müşteri, seçili cari hareketler, seçili müşteri hesapları ve tüm müşteri hesapları kapsamlarını sunar.
- Cari tablosunda ve Müşteriler tablosunda Ctrl ile birden fazla satır seçilebilir.
- Seçili/tüm müşteri hesapları Excel çıktısı `Hesap Özetleri` ve `Hareketler` sayfalarını içerir.
- Bu geliştirme yalnız çıktı üretir; cari veri, fiyat formülü ve müşteri grubu değişmez.

## 1.5.14 ek notu — güvenli standart Excel içe aktarımı

- `Siparişler` sayfasındaki tutar alanları boşsa, yalnız malzeme adı mevcut tek bir fiyat tanımına **birebir** eşleşiyor ve seçilen formül için ölçü/süre yeterliyse BTakip fiyat motoru hesap yapar.
- Fiyat tanımı, ölçü, süre veya varyant belirsizse maliyet ve satış tutarı boş kalır; içe aktarma tahminle borç üretmez.
- Komut satırı içe aktarımı da eklemeli çalışır: mevcut müşteri kartı ve fiyat grubu korunur, anlamlı tüm alanları aynı olan hareket ikinci kez eklenmez.

## 1.5.15 ek notu — cari siparişte birleşik kalemler

- Cari & Tahsilat > Sipariş Ekle formunda bir ana malzeme/baskı/hizmet ve isteğe bağlı birden çok ek malzeme, baskı veya hizmet seçilir. Örnek: `UV Baskı + Pleksi + Baskes`.
- Seçilen kalemler tek siparişin `Lines` alanında tutulur; maliyet ve satış, müşterinin kartındaki fiyat grubuyla tüm kalemlerin toplamından hesaplanır. Dakika ile çalışan hizmetler için `Süre (dk)` alanı vardır.
- Sipariş kaydedilince cari tablo başa dönmez; yeni satır seçili kalır ve görünür konuma getirilir. Sonraki siparişe yanlışlıkla taşınmaması için ek kalem seçimleri temizlenir.

## 1.5.16 ek notu — ürün oluşturma ve tablo araçları

- Var olan özellikleri kullanıcı açıkça istemeden kaldırma. Bu sürümde yalnız Fiyat Tanımları üst çubuğundaki `Sil` düğmesi ve Cari'deki `Açıklamayı göster` kutusu kaldırılmıştır; silme sağ tık menüsünde kalır.
- Fiyat Tanımları'nda `Malzeme`, `Baskı` ve `Hizmet` yatay sekmelerdir. Baskı hazır seçimleri Solvent/UV/DTF; hizmet hazır seçimleri Lazer Kesim/Sıvama/Diğer; malzeme hazır seçimleri Branda/Folyo/OWV/Kumlama/Etiket'tir. Para birimi (TL/USD/%) fiyat giriş panelindedir.
- `Ürün Ekle` sol ürün panelini açar; ekleme veya güncellemede alt işlem düğmesi `Ürünü Kaydet` olarak kalır.
- Her veri tablosunda kolon başlığındaki küçük `◉` simgesi o kolonu gizler; herhangi bir kolon başlığına sağ tıklamak gizli kolonlar dahil tüm kolonları açıp kapatma menüsünü gösterir.
- Fiyat ve cari tablolarında sağ tık menüsü Kopyala, Yapıştır, Güncelle, Ekle ve Sil işlevlerini sunar. Cari menüsünde seçili satır(lar) veya tüm hesap dışa aktarılabilir.
- Cari sipariş girişi Baskı türü → Malzeme → Hizmetler sırasındadır. `Diğer hizmet` yalnız bu sipariş için m² maliyetiyle hesaplanır; fiyat tanımı listesine eklenmez.

## 1.5.17 ek notu — geri alma ve bulut geçişi

- `Geri Al` ana başlıktan kaldırılmıştır; uygulamanın her sekmesinde üst araç çubuğunda yer alır.
- Firestore ve günlük şifreli Google Drive yedeği geçişinde, kullanıcı yalnız Google hesabını seçer. Firebase ayarı, web uygulaması adresi veya senkron anahtarı kullanıcıya gösterilmez; bunlar BTakip altyapısının sorumluluğudur.

## 1.5.18 ek notu — katalog türleri ve kolon geri açma

- Fiyat Tanımları'nda hazır seçimler tek satır düğme dizisi değildir: Malzeme sekmesi kayıtlı tüm malzeme ve varyantları açılır kutuda gösterir. Baskı seçenekleri yalnız Solvent, UV ve DTF; hizmet seçenekleri yalnız Lazer Kesim ve Sıvama'dır.
- Fiyat tanımındaki diğer tüm kalemler Malzeme olur. Bu kural Branda, Folyo, OWV, Kumlama, Etiket, Baskes ve Plotter Kesim dahil mevcut kayıtlara da açılışta uygulanır ve senkrona gönderilir.
- Her tabloda üst sağdaki sabit `◉` ikonuyla kolon listesi açılır; gizlenen kolon buradan tekrar görünür yapılır.

## 1.5.19 ek notu — açılış düzeltmesi

- Fiyat Tanımları'ndaki açılır seçim, ekran bağlandıktan sonra doldurulur. Boş seçim nedeniyle uygulamanın açılışta kapanması engellenmiştir.

## 1.5.20 ek notu — malzeme seçimi ve kararlılık

- Malzeme açılır kutusunda varsayılan metin `Malzeme seç`tir ve standart küçük açılır oka sahiptir.
- Kolon görünürlük menüsünün kapanışında oluşan `ObjectDisposedException` düzeltildi; bu hata BTakip'in bazen kendiliğinden kapanmasına neden oluyordu.

## 1.5.21 ek notu — Geri Al yerleşimi

- `Geri Al` yalnız Müşteriler, Fiyat Tanımları, Cari & Tahsilat ve Kâr Ayarları sekmelerinde görünür. Genel Bakış, Fiyat Hesaplama ve Senkron & Yedek ekranlarında gösterilmez.

## 1.5.22 ek notu — Geri Al konumu

- `Geri Al`, ilgili sekmelerin sağ üst köşesinde değil, alt araç alanında solda yer alır.

## 1.5.23 ek notu — sağdaki bildirim alanı

- Penceredeki `X`, BTakip'i görev çubuğundan kaldırır ve sağdaki bildirim alanı simgesinde çalışır halde bırakır. Simgeye çift tıklamak pencereyi açar; simgeye sağ tıklayıp `Çıkış` demek uygulamayı tamamen kapatır.

## 1.5.24 ek notu — kapanınca erişilebilir kalma

- Penceredeki `X`, BTakip'i kapatmaz. Bildirim alanı simgesi yeniden kaydedilir ve pencere görev çubuğunda küçültülmüş halde kalır; sağdaki simge Windows tarafından gizlense bile uygulama kaybolmaz.

## 1.5.25 ek notu — hesap özeti toplamları

- Müşteriye gönderilen hesap özetinin alt toplamında `Toplam Borç` ve `Toplam Tahsilat` ayrı etiketlenir. Hemen alt satırda `Güncel Açık Bakiye` tek başına gösterilir; kalan tutar dönem toplamlarıyla karışmaz.

## 1.5.26 ek notu — çoklu ürün fiyat hesabı

- Fiyat Hesaplama'da bir ürünü hesapladıktan sonra `Ürünü Hesaba Ekle` ile tutabilir, aynı ekrandan ikinci ürünü ayrı ölçüleriyle hesaplayabilirsiniz. Hesaba eklenen ürünler toplamı görünür; `Siparişe Dönüştür` bunları seçilen müşterinin fiyat grubuyla ayrı sipariş satırları olarak kaydeder.

## 1.5.27 ek notu — açıklamalı müşteri notu

- `Müşteriye Not Yolla` seçildiğinde açıklama sütununun eklenip eklenmeyeceği sorulur. `Açıklamaları çıktıya ekle` işaretlenmezse çıktıdaki açıklama kolonu ve açıklama hücreleri hiç üretilmez.

## 1.5.28 ek notu — açıklama seçiminin kapsamı

- Müşteri notundaki seçenek yalnız BTakip'in cari tablosundaki `Açıklama` sütununu ekler veya çıkarır. Tarih, hareket, malzeme, ölçü, borç ve tahsilat sütunları bu seçimden etkilenmez.

## 1.5.29 ek notu — hesap sıfırlama

- Fiyat Hesaplama'daki `Hesabı Sıfırla`, biriktirilmiş ürünleri, seçili kalemleri, girilmiş ölçüleri ve sonuç toplamlarını temizler. Yeni hesap önceki ürünlerin üstüne eklenmeden başlar.

## 1.5.30 ek notu — cari sipariş kalem türleri

- `Duvar Kağıdı` Malzeme, `Baskes` Hizmet olarak sınıflandırılır. Cari sipariş formunun baskı listesine `Eco Solvent` eklenir; `Baskes` hizmet seçimlerinde görünür. Başka fiyat formülü veya kalem türü değiştirilmez.

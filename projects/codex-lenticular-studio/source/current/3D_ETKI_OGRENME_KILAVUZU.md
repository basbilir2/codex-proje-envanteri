# 3D etkisini ayarlamayı öğren

Bu ders yalnız **derinlik, referans ve 3D önizleme** içindir. Önce 12 görünüş ve 512 piksel ile çalış; baskı ayarlarına sonra geç.

## 1. “Sabit kalacak derinlik” tam olarak ne?

Fotoğrafın içinde hayali bir cam yüzey olduğunu düşün. Bu, baskı yüzeyinin yeridir:

**Sana yakın → Öne çıkan bölgeler → SABİT REFERANS / BASKI YÜZEYİ → Arkada kalan bölgeler**

Referansın üzerindeki derinlik sağ/sol görünüşlerde yerinde kalır. Daha yakın bölgeler önde, daha uzak bölgeler arkada görünür.

**Bir kişiyi seçip tamamen dondurmuyorsun.** Kişinin bir noktasının derinliğini örnek alıyorsun. Örneğin gövdeyi seçtiğinde aynı derinlikteki yüzeyler sabit düzleme yakın kalır; burun, uzanmış el ve arka plan farklı derinlikte olabilir ve hareket etmeye devam eder.

### Senin tarifin doğru

| Referansı nereye taşırsın? | Ne olur? |
|---|---|
| Daha **uzak** bir yere, örneğin arkadaki duvara | Kişi referansın önünde kalır; daha çok bölge baskının önüne çıkar. Arka taraftaki derinlik payı azalır. |
| Kişinin **gövdesine** | Gövde baskı yüzeyine yakın durur. Yakındaki el öne, duvar arkaya gider. |
| Daha **yakın** bir yere, örneğin öndeki ele | Daha çok bölge referansın arkasında kalır. Dışarı taşan etki azalır, içeri doğru derinlik artar. |

Bu değişim derinliğin ön ve arka dağılımını değiştirir. Güç, açı ve otomatik koruma da sonucu etkiler; aynı miktarda fiziksel santimetre hareketi garanti etmez.

### Program başlangıçta neyi seçiyor?

Derinlik modeli fotoğrafa göre yakınlık tahmini yapar. Haritada **0 = uzak / siyah**, **1 = yakın / beyaz** anlamındadır. Bu sayılar metre veya santimetre değildir.

Başlangıç referansı **0,500** değeridir. Program bunun kişinin yüzü olduğunu varsaymaz ve kişiyi otomatik seçmez. Kaydırıcıyı **sola, 0’a** götürmek referansı uzağa; **sağa, 1’e** götürmek yakına taşır.

## 2. Ana kişiden referans seç — adım adım

1. Fotoğrafı yükle. Henüz derinlik hesaplanmadıysa **Hızlı önizleme** düğmesine bas ve tamamlanmasını bekle.
2. Soldaki **Fotoğrafta referans seç** düğmesine bas. Bu düğme **Fotoğraf** sekmesini ve **Sabit nokta seç** aracını açar.
3. Ortadaki fotoğrafın üzerinde kişinin **gövdesinin iç kısmına** tıkla. İlk denemede saç, tül, parmak veya kişi/arka plan sınırına tıklama; bu sınırların derinliği daha belirsizdir.
4. Tıkladığın yerde yeşil bir hedef işareti belirir. Soldaki **Sabit kalacak derinlik** sayısı değişir.
5. **Hızlı önizleme** düğmesine yeniden bas.
6. **3D önizleme → Oynat** ile bak. Gövdeye göre elin ve arka planın nasıl hareket ettiğini izle.

**Önemli:** Hedef işareti örnek aldığın yeri gösterir; kişinin etrafını seçmez. Ham derinlikten örnek alındığı ve render sırasında filtreler uygulandığı için seçilen noktada küçük hareket kalabilir. Başka bir fotoğraf, profil veya ayar yüklediğinde nokta işareti temizlenebilir; esas kaydedilen şey referans sayısıdır.

**Ön / arka derinliği dengele** düğmesi, haritadaki yakın ve uzak değerlerin dağılımına göre bir orta referans seçer. Yüz veya kişi tanımaz. Ana kişiyi sabitlemek için fotoğraftan nokta seçmek daha doğrudandır.

## 3. Soldaki 3D ayarlarını nasıl kullanacaksın?

| Ayar | Artırırsan ne olur? | Fayda / dikkat edilecek nokta |
|---|---|---|
| **Render görünüş sayısı — Nr** | Aynı kamera aralığına daha çok kare eklenir. | Geçiş daha sık örneklenir; tek başına 3D derinliği artırmaz. Süre ve dosya sayısı artar. Şimdilik **12** bırak. |
| **Toplam kamera açısı** | Sağ ve sol uçlar daha farklı yerlerden bakar. | Hareket farkı genellikle artar; kişi kenarlarında görünmeyen arka plan daha fazla açılır. Fazlası uzama ve çift kenar yapabilir. |
| **3D etki gücü** | Derinlikler referanstan daha fazla ayrılır. | Kabartı ve derinlik artar. Yanlış depth bölgeleri de daha belirgin olur. **0** düzleştirir, **1** temel güçtür. |
| **Sabit kalacak derinlik** | Sayı büyüdükçe referans yakına gelir. | Daha çok bölge arkada kalır. Genel “daha güçlü 3D” düğmesi değildir; ön/arka dağılımını seçer. |
| **Derinlik yumuşatma** | Küçük derinlik pürüzleri daha fazla azaltılır. | Dalgalanmayı azaltabilir; ince kabartıları da yumuşatabilir. Başlangıç **%25**. |
| **Kenar boşluklarını katmanlı arka planla doldur** | Açıkken yan bakışta açılan yerler tahmini katmanlarla tamamlanır. | Genellikle açık tut. Tek fotoğrafta görünmeyen gerçek arka planı geri getirmez; tahmin izi kalabilir. |

**Gönderdiğin görüntüde etki gücü 0,10.** Bu, temel 1,00 değerinin onda biri kadar kazanç demektir; görüntünün çok düz görünmesi beklenir. Öğrenirken **1,00** ile başla. Bu oran algılanan 3D’nin veya santimetre derinliğin tam onda biri anlamına gelmez.

### Otomatik korumalar

- **Kenar bozulmasında açıyı otomatik daralt:** Keskin derinlik sınırlarında açı azaltılabilir. Kenarları korumaya yardım eder; istediğin açı tam uygulanmayabilir.
- **Aşırı paralaksta açıyı otomatik sınırla:** Görünüşler arasındaki en büyük hareketi seçtiğin bütçeye sığdırır. Başlangıçta açık tut.
- **En fazla uç görünüş farkı (%):** Sağ ve sol uç görünüş arasında, sabit düzleme göre izin verilen hareket bütçesi. Yüzde görüntü genişliğine, dikey kamera hareketinde yüksekliğine göredir. **3** ile başla. Azaltmak hareketi sınırlar; artırmak daha büyük harekete izin verir, zorunlu olarak artırmaz. Bu bir lens ölçümü değildir.

Gücü veya açıyı artırıp aynı etkiyi görüyorsan sonuçtaki **Uygulanan açı** satırına bak. Koruma kamerayı daraltmış olabilir. Korumayı kapatmadan önce küçük adımlarla karşılaştır.

### “Ön / arka etki ve kenar koruma” içindeki ayarlar

| Ayar | Kullanımı |
|---|---|
| **Derinlik eğrisi** | **Yumuşak** ile başla. Yüksek güçte uç değerlerin düzleşmesini azaltır. **Doğrusal** yüksek güçte derinliği sınırlarda kırpabilir. |
| **Öne çıkan bölge** | Yalnız referanstan yakın bölgelerin derinlik farkını artırır/azaltır. Eli daha belirgin öne almak için küçük artış dene. **0**, bu taraftaki derinlikleri referansa toplar. |
| **Arkaya giden bölge** | Yalnız referanstan uzak bölgelerin derinlik farkını değiştirir. Arka planı derinleştirmek için artır; çok artırınca kenar tahminleri zorlaşabilir. |
| **Fotoğraf kenarlarına uyum** | Küçük derinlik pürüzlerini fotoğrafın renk sınırlarını gözeterek düzenler. **%35** ile başla. Saç ve tül için otomatik kusursuz maske oluşturmaz. |

## 4. Fırça neden görünmüyordu, nasıl kullanılır?

### Yeni: siyah, gri ve beyaz derinlik dengesi

Soldaki **Derinlik haritası · siyah / gri / beyaz dengesi** bölümünü aç.
Derinlik hesaplandıktan sonra kaydırıcılar **Derinlik** sekmesinde haritayı
hemen değiştirir. Bu işlem fotoğrafın rengini değiştirmez.

- **Siyah / uzak sınır:** Artırırsan bu değerin altındaki derinlikler siyaha,
  yani en uzağa toplanır. Uzak arka plandaki ayrıntı düzleşebilir.
- **Gri / orta derinlik:** 1 nötrdür. 1'in üstü orta değerleri yakına,
  altı uzağa taşır; siyah ve beyaz uçlarını korur.
- **Beyaz / yakın sınır:** Azaltırsan bu değerin üstündeki derinlikler beyaza,
  yani en yakına toplanır. Yakın yüzeyin kabartısı düzleşebilir.

Önce griyi küçük adımlarla değiştir. Sonra gerekiyorsa siyah/beyaz sınırlarını
daralt. Değişiklikten sonra referansı fotoğraftan yeniden seçebilirsin.
**Derinlik dengesini sıfırla** yalnız bu üç değeri 0 / 1 / 1'e döndürür.
3D önizlemenin değişmesi için görünüşleri yeniden oluştur. Fırça bu dengeden
sonra uygulanır; boyadığın değer dengeli haritadaki hedef derinliktir.

**İncele** seçiliyken fırça çalışmaz. Araçları, fotoğrafın altındaki **Araç** listesinden seçersin. Fırça **Fotoğraf** ve **Derinlik** sekmelerinde çalışır; oynayan **3D önizleme** üzerinde çalışmaz.

1. Önce derinliğin hesaplanmış olduğundan emin ol.
2. **Derinlik** sekmesine geç. Beyaz yerler yakın, siyah yerler uzaktır.
3. **Araç → Derinlik fırçası** seç.
4. **Fırça derinliği** ile boyayacağın hedef yakınlık değerini seç.
5. **Boyut** ile alanı ayarla. Resmin üzerine gelince görünen daire fırça alanını gösterir.
6. Fareyi basılı tutup düzeltmek istediğin bölgeyi boya. Aynı yerin üzerinden tekrar geçmek değeri hedefe daha çok yaklaştırır.
7. **Hızlı önizleme** ile yeni 3D sonucu oluştur.

### Fırça örneği

Referansın **0,60** olduğunu varsayalım; bunlar yalnız öğretici sayılardır:

| Fırça değeri | Boyanan bölgenin hedefi |
|---|---|
| **0,80** | Referanstan yakın; önde görünmeye yönelir. |
| **0,60** | Sabit referans düzlemine yaklaşır. |
| **0,30** | Referanstan uzak; arkada görünmeye yönelir. |

Fırça değeri **“bu kadar artır”** değildir; **“bu derinliğe yaklaştır”** demektir. Örneğin mevcut değer 0,90 ise 0,80 ile boyamak onu biraz geriye taşır.

**Fotoğraf sekmesinde renklerin değişmemesi normaldir:** Fırça renk boyamaz, derinliği değiştirir. Değişikliği görmek için Derinlik sekmesini kullan. Büyük fırçayla tüm kişiyi tek değere boyamak kişinin yüz/gövde kabartısını silip karton gibi düzleştirebilir. Küçük alanları düzelt.

**Geri al** son kaydedilen fırça izini geri alır; uzun bir sürükleme için birkaç kez gerekebilir. **Fırçayı temizle** mevcut fırça düzenlemelerinin tümünü kaldırır. İkisi de yeni 3D görüntü için yeniden render gerektirir.

## 5. Görüntü motoru ayrıntıları

Başlangıç değerlerini koruyabilirsin:

| Ayar | Değiştirmenin etkisi |
|---|---|
| **Kamera hareketi** | Sağ/sol hareket dikey lensle; yukarı/aşağı hareket yatay lensle eşleşir. |
| **Arka plan katmanı** | Daha fazla katman farklı derinlikleri ayırabilir; işlem ve bellek artar. Fazlası her fotoğrafta daha iyi değildir. Başlangıç **3**. |
| **Doldurma yarıçapı** | Gizli renklerin doldurulmasında komşuluk alanıdır. Artırmak daha yaygın renk taşıyabilir, bulanık iz de oluşturabilir. Başlangıç **5**. |
| **Mesh ayrıntısı** | Yüzey daha sık örneklenir. Bellek/süre artar; yanlış derinliği düzeltmez. Başlangıç **384**. |
| **Depth çözünürlüğü** | Derinlik tahmininde daha fazla ayrıntı işlenir; süre ve bellek artabilir. Başlangıç **504**. |
| **Render boyutu** | Üretilen karelerin piksel boyutudur. **512 px** çalışma için yeterlidir; büyütmek kaynaktaki eksik ayrıntıyı geri getirmez. |

**Hızlı önizleme** her seferinde 2 uç görünüş / 512 px / 384 mesh kullanır. **Görünüşleri oluştur** seçtiğin görünüş sayısını ve boyutları kullanır. İkisi de açı, referans ve fırça düzenlemelerini uygular.

## 6. İlk uygulaman: yalnız üç karşılaştırma

1. Üstteki **Varsayılan ayarlara dön** düğmesini kullan. Başlangıç: 12 görünüş, 0,80° açı, 1,00 güç, 0,500 referans ve %25 yumuşatma.
2. İlk önizlemeyi oluştur; sonra kişinin gövdesinden referans seçip yeniden önizleme oluştur. Bunu temel örneğin olarak izle.
3. Yalnız gücü **1,00 → 1,20** yapıp yeniden oluştur. Gövde sabit düzleme yakın kalırken öndeki ve arkadaki farkın artışını karşılaştır.
4. Referansı arkadaki duvardan seçip yeniden oluştur. Bu kez kişinin daha çok öne çıkmasını karşılaştır. Bozulma görürsen önceki çalışmayı listeden seçip **Seçili çalışmanın ayarlarını kullan** düğmesine bas.

Her karşılaştırmada tek ayarı değiştir. Böylece sonucu hangi ayarın değiştirdiğini öğrenirsin. Eski çalışmaların çıktıları korunur.

### Varsayılanlara dön düğmesi neyi sıfırlar?

**3D ve baskı ayarlarını**, referans değerini, mevcut fırça düzenlemelerini, seçili ICC/matris ayarını ve araç seçimini başlangıca döndürür. Fotoğrafı, hesaplanan kaynak depth haritasını, kayıtlı profilleri ve eski çıktıları silmez; başlamış işi değiştirmez. Sonucu otomatik üretmez: ardından **Hızlı önizleme** düğmesine bas.

Beğendiğin ayarı korumak için sıfırlamadan önce **Lens / çalışma profili → bir ad → Kaydet** kullanabilirsin.


## Yeni seçenek: yerel AI ile ayrıntılı derinlik

1. **Yerel AI ile ayrıntılı derinlik** kutusunu aç.
2. **Yalnız derinlik haritasını oluştur** düğmesine bas. Bu işlem görünüş render etmez.
3. İşlem bitince **Ayrıntılı derinlik** sekmesinde kaydedilmiş haritayı incele.
4. **Derinlik** sekmesinde kutuyu açıp kapatarak temel ve ayrıntılı haritayı karşılaştır.
5. **Yerel kabartı gücü** ile ayarla: 0 katkıyı kaldırır, 1 standarttır, 2 ayrıntı katkısını iki katına çıkarır. Fazlası hatalı kabartıları da büyütebilir.
6. **Hızlı önizleme · 2 görünüş** ile iki uç kamerayı kontrol et. Sonra istediğin Nr sayısıyla **Görünüşleri oluştur** kullan.

Motor, 9 örtüşen genel bölgeye ek olarak fotoğrafta ayrıntı bulunup temel
haritada düz kalan 8 yakın bölgeyi yeniden AI ile tahmin eder. Küçük derinlik
farkları sınırlı güçle ana haritaya eklenir. AI katkısı fotoğraf parlaklığını doğrudan kabartıya çevirmez. İlk hesaplama daha uzun sürer; sonraki güç değişiklikleri
aynı fotoğraf ve temel depth için kaydedilen ayrıntıyı kullanır.
Bu tahmini bir kabartıdır; burun, kumaş veya taş ayrıntılarının tümünü doğru
çıkardığı varsayılmaz. Yanlış bölgeyi fırçayla düzeltebilir veya ayrıntıyı kapatabilirsin.

**Serbest görünüş sayısı:** Nr alanına 7, 16, 20, 31 gibi tam sayılar yazabilirsin.
Öneri `min(dosya PPI, yazıcı DPI) / etkin LPI` oranının aşağı yuvarlanmasıyla
hesaplanır; baskı kanalı sınırı 64 olduğu için öneri en çok 64'tür. 1200 PPI,
1200 DPI ve 60 LPI için öneri 20'dir. Bu örnekleme önerisi optik kalite garantisi
veya otomatik karar değildir. Değerler yalnız **Öneriyi Nr ve Ne için kullan**
düğmesine basarsan birlikte değişir; Nr ve Ne'yi ayrı ayrı kendin belirleyebilirsin.

### AI ince ayrıntıyı çıkaramazsa: Yüzey kabartısı

Ayrıntı kutusu açıkken **Yüzey kabartısı · tahmini** kaydırıcısını 0.25–0.50 civarında deneyebilirsin. Bu ayrı bir sanatsal kabartı işlemidir: genel aydınlatmayı ayırıp küçük ışık/gölge farklarını sınırlı derinlik farkına çevirir. Pozitif değer aydınlık çizgileri öne, koyu çizgileri arkaya taşır; negatif değer ters çevirir. 0 kapatır. **Gerçek geometrinin ölçümü değildir:** boya, desen ve gölgeyi yanlış kabartabilir. Önce Derinlik sekmesinde bak, ardından 2 görünüşle kontrol et. AI dahil ayrıntıları tamamen kaldırmak için kutuyu kapat.

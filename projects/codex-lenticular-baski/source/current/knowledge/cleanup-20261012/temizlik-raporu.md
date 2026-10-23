# Lenticular temizliği — 12 Ekim 2026

**39.003 dosya silindi: 44.10 GB (41.07 GiB).** Silinemeyen veya atlanan hedef yok. Diskteki boş alan işlem sırasında yaklaşık 44.16 GB arttı; bu fark diğer çalışan süreçlerden de etkilenebilir.

## Silinenler

- Daha önce çöp kutusuna taşınmış `Documents/lenticular2` yedeğinin eski dosyaları: yaklaşık 26,13 GB. Çöp kutusunun diğer içerikleri temizlenmedi.
- Lenticular uzmanlık prototipindeki tamamlanmamış `Qwen3-14B-Q4_K_M.gguf.part`: yaklaşık 6,19 GB. Bilgi veritabanı, program ve kullanılabilir tamamlanmış modeller korunmuştur.
- Eski, yeni VD üretimi tarafından geçersiz kılınmış portre denemelerinin ara görsel/render dosyaları: yaklaşık 6,52 GB.
- Lenticular Studio'nun eski deneme/onarım/render ara dosyaları: yaklaşık 4,87 GB.
- Çöp kutusundaki iki eski lenticular baskı kopyası: yaklaşık 0,37 GB.

## Korunanlar ve kontrol

Son 24 saat içinde oluşturulmuş **veya** değiştirilmiş dosyalar korundu. Sınır: 11 Ekim 2026 19:19:17 (Türkiye saati); işlem başında sabitlenmiştir. Güncel üretim klasöründeki yaklaşık 32,20 GB korunmuştur. Kullanılan eski kaynak, derinlik haritası ve siluet de korundu. Çalışan yazılım, bağımlılıkları ve modelleri; proje öğrenme kayıtları; güncel altı kamera görüntüsü; yeni 100/75/50,20 LPI dosyaları yerindedir. Kullanılmadığı kanıtlanmayan eski nihai baskılar korundu.

1689 son-24-saat dosyasının varlığı, boyutu ve değiştirilme zamanı kontrol edildi; eksik veya değişmiş dosya yok. Altı kamera karesi ve merkez görüntünün hash'leri aynıdır. Seçilen 39.003 dosyanın hiçbirinin diskte kalmadığı doğrulandı. Dosyalar PowerShell ile tam yolları üzerinden tek tek silindi; bağlantılar takip edilmedi ve kapsam dışındaki hiçbir yol hedeflenmedi.

## Tarama kapsamı

C: üzerinde 211,144 klasör ve 951,176 dosya adı tarandı. 137 erişim izni olmayan konum taranamadı; izinleri değiştirilmedi. Bağlantı noktaları takip edilmedi. Diğer uygulamaların dosyaları silme listesine alınmadı.

Ayrıntılı kanıt: `audit.json`, `deletion-plan.json`, `deletion-log.jsonl`, `deletion-result.json`, `verification.json`.

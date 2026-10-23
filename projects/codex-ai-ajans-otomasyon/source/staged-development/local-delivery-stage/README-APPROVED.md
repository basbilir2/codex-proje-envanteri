# Onaylanan yerel içerikler

Operator tarafından `yalnız yerel dosyaya teslim` modunda onaylanan içerikler bu ağacın altında tutulur:

`<marka>/<içerik-kimliği>/<sürüm>/`

Her teslim paketi şunları içerir:

- `caption.txt`: Onaylanan paylaşım metni.
- `content.json`: Sürümlü yapılandırılmış içerik.
- `visual-01.*`: Onaylanan görsel veya görseller.
- `approval.json`: İmzalı onay kaydı ve `publish_authorized: false` kilidi.
- `manifest.json`: Dosya bütünlük özetleri.

Bu klasöre kayıt, sosyal medya yayını değildir. Yerel teslim paketleri yayın yetkilendirme hattı tarafından kesin olarak reddedilir.

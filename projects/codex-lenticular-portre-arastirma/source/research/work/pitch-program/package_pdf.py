from pathlib import Path
import json,hashlib,zipfile,subprocess
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
m=json.loads((HERE/'verification.json').read_text(encoding='utf-8'))
OUT=Path(m['tests'][0]['png']).parent
w,h=[p/1200*72 for p in m['page_pixels']]
def draw(c,test):
    c.drawImage(test['png'],0,0,width=w,height=h,mask=None)
    c.showPage()
def setup(path):
    c=Canvas(str(path),pagesize=(w,h),pageCompression=1)
    c.setViewerPreference('PrintScaling','None')
    c.setTitle('Lenticular Studio - Pitch Test - %100')
    c.setAuthor('Lenticular Studio pitch-test motoru')
    return c
combined=OUT/'TUMU-50-60-75-85-100LPI-5-SAYFA-YUZDE100.pdf'
c=setup(combined)
for test in m['tests']:
    target=Path(test['png']).with_suffix('.pdf')
    p=setup(target);draw(p,test);p.save()
    draw(c,test)
    test['pdf']=str(target)
c.save()
for path,count in [(combined,5)]+[(Path(t['pdf']),1) for t in m['tests']]:
    r=PdfReader(path)
    assert len(r.pages)==count
    assert r.trailer['/Root']['/ViewerPreferences']['/PrintScaling']=='/None'
    for page in r.pages:
        assert abs(float(page.mediabox.width)-w)<.001 and abs(float(page.mediabox.height)-h)<.001
        obj=list(page['/Resources']['/XObject'].values())
        assert len(obj)==1
        img=obj[0].get_object()
        assert (img['/Width'],img['/Height'])==tuple(m['page_pixels'])
        assert not img.get('/Interpolate',False)
guide='''LENTICULAR STUDIO - PROGRAM ÜRETİMİ PITCH TESTLERİ

50 LPI: 49.00-51.00
60 LPI: 59.00-61.00
75 LPI: 74.00-76.00
85 LPI: 84.00-86.00
100 LPI: 99.00-101.00
Her test: 0.05 adım, 41 etiketli şerit, ayrı tek sayfa.

ÜRETİM
Çizgileri mevcut programımızın lenticular.printing.pitch_test işlevi üretti.
Programın doğrulanmış 21 adaylı iki aralığı birleştirildi; ortak merkez bir kez kullanıldı.
Her şeritten 3.2 mm yüksekliğinde sabit desen bölümü alındı. Çizgi genişliği,
yatay piksel sırası ve fiziksel pitch değiştirilmedi; yeniden örnekleme yapılmadı.
Her PNG ve TIFF içindeki 205 şerit, programın kaydedilmiş çıktısındaki
aynı piksel verisiyle birebir karşılaştırıldı. PDF'lere aynı 1200 PPI
görüntüler kayıpsız, tam piksel boyutuyla yerleştirildi.
Program kodu, kaynak portre ve kayıtlı kullanıcı ayarları değiştirilmedi.

BOYUT
Her dosya yaklaşık 170 × 215.14 mm; 22 cm'yi geçmez.
Her şeridin çizgili kısmı yaklaşık 130 mm genişliğindedir.
Bu ölçü projedeki 130 × 215.139 mm portre baskı kaydına dayanır.
PNG/TIFF: 8031 × 10164 piksel, 1200 PPI, RGB / sRGB profilli.
1200 PPI dosya örneklemesidir; yazıcının gerçek çözünürlük ölçümü değildir.

BASKI
PDF: %100 / Gerçek boyut. Sayfaya sığdırma, kenarlıksız büyütme ve otomatik ölçek kapalı.
PNG/TIFF: 1200 PPI fiziksel ölçeğini koru. Yeniden boyutlandırma/örnekleme yapma.
Yatay ve dikey kontrol çizgilerinin ikisi de baskıda 100 mm olmalı.
Aynı makine/RIP, yön, malzeme, pass, mürekkep ve beyaz katman ayarlarıyla bas.
Üretim beyazı bu dosyalara uygulanmış değildir; beyazı mevcut üretim akışın belirler.

OKUMA
Lensin düz arkasını baskıya temas ettir; oluklu yüz gözlemciye baksın.
Lens çizgilerini dikey desen çizgileriyle paralel hizala.
Üstteki yatay çizgiyi kesintisiz hizalamaya yardımcı olarak kullan.
Gerçek ürünün izleneceği mesafeden, tek gözle ve karşıdan bak.
Başını hafif sağa/sola oynatınca 13 cm boyunca birlikte siyah/beyaz
değişen, en uniform şeridi kaydet. Eşit şeritler varsa hepsini yaz.
13 cm alanda 0.05 LPI komşularını ayırmak zor olabilir; kesinlik iddiası yoktur.
En iyi değer aralığın ucundaysa gerçek optimum aralığın dışında olabilir.
Ekrandaki moiré veya dalgaya göre seçim yapma; basılı test ve lens gerekir.
PDF/PNG/TIFF aynı testin farklı biçimleridir; hepsini basmana gerek yok.
5 sayfalık PDF'de her sayfa farklı lens içindir.

Dosyalar dijital olarak doğrulandı; gerçek lens pitch değeri henüz seçilmedi.
'''
(OUT/'ONCE-OKU-BASKI.txt').write_text(guide,encoding='utf-8-sig')
archive=OUT.parent/'PROGRAM-PITCH-50-60-75-85-100-TUM-DOSYALAR.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for file in sorted(OUT.iterdir()):z.write(file,file.name)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
for test in m['tests']:
    subprocess.run(['pdftoppm','-r','130','-png','-singlefile',test['pdf'],str(HERE/f"pdf-review-{test['nominal_lpi']}")],check=True)
(HERE/'package.json').write_text(json.dumps({'combined_pdf':str(combined),'zip':str(archive),'tests':[{k:t[k] for k in ['nominal_lpi','pdf','png','tiff']} for t in m['tests']]},indent=2),encoding='utf-8')
print(json.dumps({'combined_pdf':str(combined),'zip':str(archive),'verified_pdf_count':6,'verified_lens_tests':5,'verified_native_bands':205},ensure_ascii=False))

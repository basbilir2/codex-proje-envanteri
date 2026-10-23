from pathlib import Path
from decimal import Decimal
import json, math, re, subprocess
import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output' / 'pdf' / '60LPI-pitch-59-61'
OUT.mkdir(parents=True, exist_ok=True)
TMP = ROOT / 'tmp' / 'pdfs' / 'pitch60'
TMP.mkdir(parents=True, exist_ok=True)
pdf = OUT / 'PITCH-59.00-61.00-ADIM-0.05-100-YUZDE.pdf'
png = OUT / 'PITCH-59.00-61.00-ADIM-0.05-1200PPI.png'
W, H = 170, 215.139
PPI = 1200
values = [Decimal('59.00') + Decimal('0.05') * i for i in range(41)]
pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialBold', 'C:/Windows/Fonts/arialbd.ttf'))
c = canvas.Canvas(str(pdf), pagesize=(W*mm, H*mm), pageCompression=1)
c.setTitle('60 LPI Pitch Test | 59.00-61.00 | 0.05 | %100')
c.setAuthor('Lenticular proje')
c.setViewerPreference('PrintScaling', 'None')

def text(x, y, s, size=8, bold=False, center=False):
    font = 'ArialBold' if bold else 'Arial'
    c.setFont(font, size)
    width = pdfmetrics.stringWidth(s, font, size)/mm
    left = x-width/2 if center else x
    assert left >= 3 and left + width <= W-3, (s, left, width)
    (c.drawCentredString if center else c.drawString)(x*mm, (H-y)*mm, s)

def line(x1,y1,x2,y2,width=.12):
    c.setLineWidth(width*mm)
    c.line(x1*mm,(H-y1)*mm,x2*mm,(H-y2)*mm)

text(7, 10, '60 LPI - TEK BASKI PITCH TESTİ', 13, True)
text(7, 16, '59.00-61.00 LPI | 0.05 adım | 41 şerit', 9, True)
text(7, 21, 'Dosya: 17 × 21,51 cm | Çizgili alan: 13 cm | PNG: 1200 PPI', 7.6)
text(7, 26, '%100 / Gerçek boyut - Sayfaya sığdırma ve kenarlıksız baskı kapalı.', 7.4, True)
text(11, 32, 'LPI', 7, True, True)
text(85, 32, 'LENS ÇİZGİLERİ DİKEY OLMALI  ↑  ↓', 7, True, True)
text(159, 32, 'LPI', 7, True, True)
# Continuous transverse line for skew alignment under the lens.
line(20,34,150,34,.2)
rows = []
for i, v in enumerate(values):
    top = 36 + i*3.8
    band_h = 3.2
    period = 25.4/float(v)
    path = c.beginPath()
    for k in range(math.ceil(130/period)):
        x = 20 + k*period
        bar_w = min(period/2,150-x)
        if bar_w > 0:
            path.rect(x*mm,(H-top-band_h)*mm,bar_w*mm,band_h*mm)
    c.drawPath(path,stroke=0,fill=1)
    label = f'{v:.2f}'
    text(10,top+2.55,label,8,True,True)
    text(160,top+2.55,label,8,True,True)
    rows.append({'lpi':str(v),'box_mm':[20,top,150,top+band_h], 'period_mm':period})
# Independent scale check in each axis.
line(20,199,120,199,.18)
for n in range(11):
    x=20+n*10
    line(x,197.8,x,200.2,.15)
    text(x,203.5,str(n*10),6,center=True)
text(20,208,'Uç çizgiler arası tam 100 mm olmalı.',7,True)
line(167,65,167,165,.15)
line(165.8,65,168.2,65,.15)
line(165.8,165,168.2,165,.15)
c.saveState()
c.translate(168.7*mm,(H-115)*mm)
c.rotate(90)
c.setFont('Arial',5)
c.drawCentredString(0,0,'100 mm - dikey ölçü kontrolü')
c.restoreState()
text(7, 195, 'Lensi düz yüzeyi baskıya temas edecek şekilde yerleştir. Çizgilere paralel hizala.', 6.9)
text(7, 212, 'Sonuç: ______ LPI    İzleme mesafesi: ______ cm    Aynı üretim / RIP ayarları.', 7)
c.showPage()
c.save()

reader = PdfReader(pdf)
assert len(reader.pages)==1
box=reader.pages[0].mediabox
assert abs(float(box.width)/mm-W)<.001 and abs(float(box.height)/mm-H)<.001
assert reader.trailer['/Root']['/ViewerPreferences']['/PrintScaling']=='/None'
txt=reader.pages[0].extract_text()
for v in values:
    assert txt.splitlines().count(f'{v:.2f}')==2, v
assert len(values)==41 and values[0]==59 and values[-1]==61
render=TMP/'pitch1200'
subprocess.run(['pdftoppm','-r',str(PPI),'-mono','-aa','no','-aaVector','no','-singlefile',str(pdf),str(render)],check=True)
Image.MAX_IMAGE_PIXELS=150_000_000
with Image.open(render.with_suffix('.pbm')) as im:
    assert im.mode=='1'
    # Preserve the PDF's layout while sampling the calibration geometry at
    # pixel centers. Poppler's monochrome polygon fill expands black edges.
    # Direct sampling avoids that duty-cycle bias in the print PNG.
    for row in rows:
        x0,y0,x1,y1=row['box_mm']
        xa,xb=math.floor(x0*PPI/25.4),math.ceil(x1*PPI/25.4)
        ya,yb=math.floor(y0*PPI/25.4),math.ceil(y1*PPI/25.4)
        phase=((np.arange(xa,xb)+.5-x0*PPI/25.4)*float(row['lpi'])/PPI)%1
        samples=np.where(phase<.5,0,255).astype(np.uint8)
        band=Image.fromarray(np.broadcast_to(samples,(yb-ya,xb-xa)).copy()).convert('1',dither=Image.Dither.NONE)
        im.paste(band,(xa,ya))
    im.save(png,dpi=(PPI,PPI),optimize=True)
    preview=im.convert('L')
    preview.thumbnail((950,1250),Image.Resampling.LANCZOS)
    preview.save(TMP/'layout-preview.png')

with Image.open(png) as im:
    assert im.mode=='1'
    assert all(abs(d-PPI)<.02 for d in im.info['dpi'])
    assert max(im.width,im.height)/PPI*25.4 < 220
    checks=[]
    for row in rows:
        x0,y0,x1,y1=row['box_mm']
        yy=round((y0+y1)/2*PPI/25.4)
        xa=math.ceil(x0*PPI/25.4)+2
        xb=math.floor(x1*PPI/25.4)-2
        a=np.array(im.crop((xa,yy,xb,yy+1)))[0]
        edges=np.flatnonzero(a[1:]!=a[:-1])+xa+1
        distances=np.diff(edges)
        half=PPI/(2*float(row['lpi']))
        assert np.all(np.abs(distances-half)<1.01), row['lpi']
        # Fit all transitions; a half-pixel edge uncertainty does not accumulate.
        slope=np.polyfit(np.arange(len(edges)),edges,1)[0]
        measured=PPI/(2*slope)
        assert abs(measured-float(row['lpi'])) < .001, (row['lpi'],measured)
        checks.append({'lpi':row['lpi'],'measured_lpi':round(measured,6),'edges':len(edges)})
    pixels=list(im.size)

guide='''60 LPI - TEK BASKI PITCH TESTİ
Aralık: 59.00-61.00 LPI. Adım: 0.05. Toplam: 41 etiketli şerit.
Dosyanın tamamı 170 × 215.139 mm; çizgili alan genişliği 130 mm.
Bu ölçü, projedeki 130 × 215.139 mm portre baskı kaydına göre seçilmiştir.

BASKI
PDF vektöreldir. PNG aynı geometriyle 1200 PPI, 1 bit siyah-beyaz olarak üretilmiştir.
PDF'yi %100 / Gerçek boyut ile bas. Sayfaya sığdırma ve kenarlıksız büyütme kapalı olsun.
PNG kullanıyorsan 1200 PPI veya 170 × 215.139 mm fiziksel ölçüyü koru; yeniden örnekleme yapma.
1200 PPI dosya örneklemesidir; yazıcının gerçek çözünürlüğünün doğrulandığı anlamına gelmez.
Yatay ve dikey kontrol çizgilerinin ikisi de basılı halde tam 100 mm olmalı.
Üretimdeki aynı makine, malzeme, yön, RIP, pass ve beyaz katman ayarlarını kullan.

OKUMA
Lensin düz arkasını baskıya temas ettir; oluklu yüzü gözlemciye baksın.
Lens oluklarını dikey ince çizgilere paralel hizala; üstteki yatay çizgi düz ve kesintisiz görünsün.
Gerçek ürünü izleyeceğin mesafeden, tek gözle ve sayfanın karşısından bak.
Başını hafif sağa-sola oynat: tüm 13 cm boyunca birlikte siyah/beyaz değişen en eşit şeridi seç.
Birden fazla şerit eşitse hepsini kaydet. Kısa alanda 0.05 LPI komşularını ayırmak zor olabilir.
59.00 veya 61.00 sınır değeri en iyiyse gerçek optimum bu aralığın dışında kalabilir.
Ekrandaki dalga/moiré karar ölçütü değildir; gerçek basılı hedef ve lens ile seç.
Pitch testi portre görüntüsü içermez; siyah-beyaz çizgiler pitch eşleşmesini ölçmek içindir.

Yöntem kaynakları:
https://triaxes.com/docs/Pitch-test-en/Description.html
https://dplenticular.com/technology/prepress-process/
'''
(OUT/'BASKI-VE-OKUMA.txt').write_text(guide,encoding='utf-8-sig')
report={'status':'digital_geometry_verified_physical_pitch_not_selected','page_mm':[W,H], 'pattern_width_mm':130,'png_ppi':PPI,'png_pixels':pixels,'count':41,'step':'0.05','rows':checks}
(TMP/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'pdf':str(pdf),'png':str(png),'preview':str(TMP/'layout-preview.png'),'page_mm':[W,H],'png_pixels':pixels,'all_41_pitches_verified':True},ensure_ascii=False))

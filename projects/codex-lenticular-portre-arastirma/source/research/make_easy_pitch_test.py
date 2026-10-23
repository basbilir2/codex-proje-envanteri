"""Exact, labelled physical pitch target; does not alter app or printer settings."""
from pathlib import Path
from decimal import Decimal
import hashlib
import json
import sys
import uuid

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import tifffile

HERE = Path(__file__).resolve().parent
APP = Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1')
sys.path.insert(0, str(APP))
from lenticular.printing import channel_pattern, color_transform

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def series(start, step, count):
    return [Decimal(start) + Decimal(step) * i for i in range(count)]

def main():
    rec = json.loads((HERE / 'fullscene-current.json').read_text(encoding='utf-8'))
    previous = Path(rec['delivery']) / 'TEK-BASKI-SOL-6-ORTA-10-SAG-12-GORSEL.tif'
    previous_hash = digest(previous)
    settings = rec['printing'] | dict(ne=2, phase=0, tilt_deg=0, mirror=False,
                                      axis='vertical', color_mode='RGB', icc_path=None)
    assert settings['ppi'] == 1200 and rec['printing']['axis'] == 'vertical'
    assert not rec['printing']['mirror'] and rec['printing']['phase'] == 0
    ppi = settings['ppi']
    px = lambda mm: round(mm * ppi / 25.4)
    margin, label_w, field_w, gap = px(3), px(22), px(130), px(6)
    panel_w = label_w + field_w
    width = 2 * margin + 3 * panel_w + 2 * gap
    height = 10164  # Same physical height and sampling as the full portrait.
    row_h, band_h, rows_top = px(5.4), px(4.5), px(30)
    panels = [('A', series('49.50', '0.05', 21), 'GENİŞ ARAMA'),
              ('B', series('49.80', '0.01', 31), 'İNCE ARAMA'),
              ('C', series('50.10', '0.01', 31), 'İNCE ARAMA')]
    if sys.argv[1:] == ['--repair-current']:
        current = json.loads((HERE/'pitch-test-current.json').read_text(encoding='utf-8'))
        out = Path(current['delivery']).resolve()
        assert out.parent == Path(r'C:\Users\USER\Downloads').resolve()
        assert out.name.startswith('Lenticular-50LPI-PITCH-TESTI-20261009-')
        assert digest(out/'BAS-50LPI-1200PPI-KOLAY-PITCH-TESTI.tif') == current['validation']['tiff_sha256']
    else:
        assert not sys.argv[1:]
        out = Path(r'C:\Users\USER\Downloads') / ('Lenticular-50LPI-PITCH-TESTI-20261009-' + uuid.uuid4().hex[:6])
        out.mkdir(exist_ok=False)
    canvas = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(canvas)
    regular = lambda mm: ImageFont.truetype('C:/Windows/Fonts/arial.ttf', px(mm))
    bold = lambda mm: ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', px(mm))
    title_font, label_font, small = bold(3.4), bold(3.0), regular(2.5)
    draw.text((margin, px(1.3)), '50 LPI LENS • 1200 PPI • %100 ÖLÇEK • MAKİNE/RIP AYARLARI AYNI', font=title_font, fill='black')
    # Static ruler checks scaling along the exact axis which selects views.
    ruler_x, ruler_y = margin + label_w, px(10)
    ruler_length = px(100)
    draw.line((ruler_x, ruler_y, ruler_x+ruler_length, ruler_y), fill='black', width=px(.16))
    for x in (ruler_x, ruler_x+ruler_length):
        draw.line((x, ruler_y-px(1), x, ruler_y+px(1)), fill='black', width=px(.16))
    draw.text((ruler_x+ruler_length+px(3), ruler_y-px(1.5)), 'Bu çizgi baskıda 100 mm olmalı', font=small, fill='black')
    rows = []
    for panel_i, (letter, candidates, name) in enumerate(panels):
        left = margin + panel_i * (panel_w + gap)
        field_x = left + label_w
        heading = f'{letter} / {name} / {candidates[0]:.2f}–{candidates[-1]:.2f} LPI'.replace('.', ',')
        draw.text((left, px(17)), heading, font=title_font, fill='black')
        assert draw.textbbox((left, px(17)), heading, font=title_font)[2] < left + panel_w
        draw.text((left, px(22)), 'LENS: Etiketin sağındaki 13 cm alanı ört', font=small, fill='black')
        # A continuous line perpendicular to the grooves is the skew reference.
        draw.line((field_x, px(27), field_x+field_w-1, px(27)), fill='black', width=px(.25))
        for i, candidate in enumerate(candidates):
            y = rows_top + i * row_h
            pattern = channel_pattern(field_w, 0, 1, settings | {'effective_lpi':float(candidate)})[0]
            independent = (np.floor((np.arange(field_w)+.5)*float(candidate)/ppi*2).astype(np.int64) % 2)
            assert np.array_equal(pattern, independent)
            binary = (pattern * 255).astype(np.uint8)
            band = Image.fromarray(np.broadcast_to(binary, (band_h, field_w)).copy()).convert('RGB')
            canvas.paste(band, (field_x, y))
            code = f'{letter}{i+1:02d}'
            label = f'{code}  {candidate:.2f}'.replace('.', ',')
            # Labels remain outside the 13 cm lens-selection field.
            bounds = draw.textbbox((left, y+px(.55)), label, font=label_font)
            assert bounds[2] < field_x-px(.5) and bounds[3] < y+row_h
            draw.text((left, y+px(.55)), label, font=label_font, fill='black')
            rows.append(dict(code=code, lpi=float(candidate), field_box_px=[field_x,y,field_x+field_w,y+band_h]))
        if letter == 'A':
            lines = ['NASIL BAKACAĞIM?', '1. Tek gözle, yaklaşık 50 cm’den bak.',
                     '2. Lens çizgileri DİKEY olsun.', '3. Üst çizgiyi düz ve kesintisiz hizala.',
                     '4. Başını azıcık sağa–sola oynat.', '5. Baştan sona birlikte siyah/beyaz',
                     '   olan şeridin kodunu seç.', 'Dalga / parça parça değişim: eşleşme zayıf.',
                     'Birden fazlası eşitse hepsini bildir.', 'B/C dışında sonuç varsa ince test uyarlanır.']
            for j, line in enumerate(lines):
                text_y = rows_top + len(candidates)*row_h + px(2+j*4.1)
                draw.text((left, text_y), line, font=small, fill='black')
    footer_y = px(201)
    draw.text((margin, footer_y), 'SONUÇ: A___ / B___ / C___     Mesafe: ____ cm     Birden fazla eşit şerit varsa hepsini söyle.', font=small, fill='black')
    draw.text((margin, footer_y+px(4)), 'TIFF’i %100 bas. Tam dosya yaklaşık 47,40 × 21,51 cm; yalnız test alanları 13 cm genişliğinde.', font=small, fill='black')
    draw.text((margin, footer_y+px(8)), 'Ekran/telefon dalgaları tek başına ölçüm değildir. Aynı lens, baskı malzemesi, beyaz katman ve RIP yönünü koru.', font=small, fill='black')
    _, icc = color_transform(settings)
    main_tif = out / 'BAS-50LPI-1200PPI-KOLAY-PITCH-TESTI.tif'
    expected = np.asarray(canvas)
    # Uncompressed RGB matches the already-used portrait TIFF path exactly.
    tifffile.imwrite(main_tif, expected, photometric='rgb', rowsperstrip=128,
                      resolution=(ppi,ppi), resolutionunit='INCH', metadata=None,
                      extratags=[(34675,'B',len(icc),icc,False)])
    actual = tifffile.memmap(main_tif)
    assert actual.shape == (height,width,3)
    assert np.array_equal(actual, expected)
    for row in rows:
        x0,y0,x1,y1 = row['field_box_px']
        region = actual[y0:y1,x0:x1]
        assert set(np.unique(region)) == {0,255}
        assert np.array_equal(region[:,:,0], region[:,:,1])
        assert np.array_equal(region[0], region[-1])
        pattern = np.floor((np.arange(field_w)+.5)*row['lpi']/ppi*2).astype(np.int64)%2*255
        assert np.array_equal(region[0,:,0],pattern)
    with tifffile.TiffFile(main_tif) as f:
        page = f.pages[0]
        assert len(f.pages)==1 and page.tags['ResolutionUnit'].value==2
        assert page.tags['XResolution'].value == (ppi,1) and page.tags['YResolution'].value == (ppi,1)
        assert page.tags[34675].value == icc
    white = out / 'ISTEGE-BAGLI-AYNI-BOY-BEYAZ-MASKE.tif'
    with tifffile.TiffWriter(white) as f:
        f.write(data=(np.full((min(128,height-y),width),255,np.uint8) for y in range(0,height,128)),
                shape=(height,width),dtype=np.uint8,photometric='minisblack', rowsperstrip=128,
                resolution=(ppi,ppi),resolutionunit='INCH',metadata=None)
    assert np.all(tifffile.memmap(white)==255)
    preview = canvas.copy()
    preview.thumbnail((1900,1000), Image.Resampling.LANCZOS)
    preview.save(out/'YERLESIM-ONIZLEME-BUNU-BASMA.jpg', quality=95)
    guide = '''KOLAY PITCH TESTİ — MEVCUT MAKİNE AYARLARINI DEĞİŞTİRMEDEN

BASILACAK: BAS-50LPI-1200PPI-KOLAY-PITCH-TESTI.tif
JPG sadece yerleşim önizlemesi; JPG'yi basma.
Tek sayfa RGB TIFF, 1200 PPI. Tüm dosya yaklaşık 47,40 × 21,51 cm.
Her şeritli test alanı yaklaşık 13 cm genişliğinde; soldaki etiketler buna dahil değil.
Tüm dosyayı 13 cm yapma. %100 ölçek. Medyaya sığdır / Fit to media KAPALI.
Önceki portreyle aynı RIP döndürmesini, baskı yönünü, makine çözünürlüğünü,
profilini, hızını, UV/beyaz katmanını ve baskı malzemesini koru.
Bu test için kafa yüksekliği, pass, dither, ICC veya UV ayarını değiştirme.
Şeritli dosyaya keskinleştirme, yumuşatma veya yeniden örnekleme uygulama.
100 mm kontrol çizgisini cetvelle ölç. Belirgin fark varsa sonucu seçme;
önce gerçek baskı ölçüsünü bildir. Bu farkı pitch ayarıyla gizlemeyelim.
Beyaz maske yalnız mevcut baskı yöntemin zaten bu tür beyaz alt katman
kullanıyorsa yardımcı dosyadır; yeni katman tarifi değildir.

ALANLAR
A: 49,50–50,50 LPI, 0,05 adım. Önce geniş aralıkta en düzgün bölgeyi bul.
B: 49,80–50,10 LPI, 0,01 adım. A'nın seçimi bu aralıktaysa burada incelt.
C: 50,10–50,40 LPI, 0,01 adım. A'nın seçimi bu aralıktaysa burada incelt.
B31 ve C01 aynı 50,10 değeridir; ikinci konumda karşılaştırma da sağlar.
Tüm sayılar statik etiketlerdir: 00/kanal rakamı arama. Örneğin B21 = 50,00 LPI.
Test iki siyah/beyaz görüntü kullanır; bu, portreyi iki görüntü yapacağız demek değildir.

LENSİ NASIL KOYACAĞIM?
Bir tek 13 cm lensi sırayla A, B ve C'nin ETİKET SAĞINDAKİ şeritli alanlarına koy.
Etiketler lensin dışında kalsın. Oluklar kağıdın bu dosyadaki üst–alt yönüne paralel.
Lensin oluklu/kavisli yüzü izleyiciye, düz yüzü baskıya bakar; mevcut montajını koru.
Aynı baskı teması ve malzeme katmanlarını kullan. Lensi kuvvetle bükme/bastırma.
27 mm hizasındaki yatay siyah çizgi mercek altında düz ve kesintisiz görünmeli.
Bu çizgi sadece eğikliği hizalamaya yardım eder; hassas pitch'i tek başına ölçmez.

NEYE BAKACAĞIM?
Tek gözünü kapat. Önce gözünü alanın ortasına getir ve yaklaşık 50 cm'den bak.
50 cm başlangıç mesafesidir: gerçek portreyi başka mesafeden izleyeceksen
o mesafede de kontrol et ve sonucu verirken mesafeyi mutlaka yaz.
Başını biraz sağa–sola hareket ettir (başlangıçta büyük açıyla eğme).
En iyi şerit: SOL–ORTA–SAĞ birlikte aynı renkte görünür; bakış değişirken
tüm eni birlikte siyah/beyaz geçiş yapar. Tam siyah veya tam beyaz olduğu
bir an kadar, geçiş boyunca tüm enin birlikte davranması da önemlidir.
Yanlış eşleşme: içinde dalga, açık/koyu adalar veya bir ucu değişirken
diğer ucun geride kalması. Her şeride tek bir sabit anla karar verme.
Gri tek başına hata değildir; tüm en aynı gri ve birlikte değişiyorsa aday olabilir.
Komşu iki/üç şerit eşitse zorla tek değer seçme: kodların hepsini bildir.
A'daki kazanan B/C aralığının dışındaysa dar testi o noktaya göre yeniden hazırlarız.
A'nın ilk/son şeridi kazanırsa aralık kenarındayız; daha geniş test gerekir.
Hiçbir şerit birlikte değişmiyorsa bunu da bildir; rastgele değer seçme.
Telefon moiresi ve sıkıştırma yanıltabilir. Önce gözle değerlendir; foto/video destek olsun.

BANA ŞUNU YAZ
100 mm çizgi cetvelde: ____ mm.
Bakış mesafesi: ____ cm.
A'da en iyi: A___. B/C'de en iyi: B___ / C___.
En iyi şerit baştan sona birlikte siyah/beyaz değişiyor mu: evet / hayır.
Eşit görünen başka şeritler: ____.

SINIR
Bu dosya ölçüm adayları üretir. Dijital kontrol, fiziksel pitch seçimi değildir.
Bulunan değer sadece aynı lens, malzeme, RIP, baskı yönü ve izleme mesafesinde geçerlidir.
Pitch düzelince yüz detayının ve 3D derinliğinin mutlaka tamamen düzeleceği garanti edilmez.
Mevcut portre dosyaları ve uygulama ayarları değiştirilmedi.

YÖNTEM KAYNAKLARI
https://triaxes.com/docs/Pitch-test-en/Description.html
https://dplenticular.com/technology/pitch-test-files/
'''
    (out/'KISA-BASKI-VE-OKUMA-REHBERI.txt').write_text(guide, encoding='utf-8-sig')
    assert digest(previous) == previous_hash
    report = dict(status='digital_target_verified_physical_pitch_not_selected',
                  ppi=ppi, size_px=[width,height], size_mm=[width/ppi*25.4,height/ppi*25.4],
                  lens_field_mm=field_w/ppi*25.4, row_pitch_mm=row_h/ppi*25.4,
                  rows=rows, pattern='binary 50/50, center-sampled, 2 views, no filtering',
                  exact_saved_pixels_verified=True, exact_binary_stripes_verified=True,
                  previous_portrait_unchanged=True, physical_pitch_verified=False,
                  existing_printer_settings_changed=False,
                  tiff_sha256=digest(main_tif), reference_portrait_sha256=previous_hash,
                  notes=['Use same physical print path and viewing distance.',
                         '0.01 LPI candidate spacing does not guarantee 0.01 LPI measurement precision.'])
    (out/'DENETIM-VE-ETIKETLER.json').write_text(json.dumps(report, indent=2, ensure_ascii=False),encoding='utf-8')
    (HERE/'pitch-test-current.json').write_text(json.dumps({'delivery':str(out),'validation':report},indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'delivery':str(out),'size_px':[width,height],'size_mm':report['size_mm'],
                      'rows':len(rows),'saved_pixels_verified':True},ensure_ascii=False))

if __name__=='__main__':
    main()

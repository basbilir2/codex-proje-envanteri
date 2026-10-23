"""Three requested 50.20 LPI trials; reuse prepared geometry and verify exported pixels."""
from pathlib import Path
from fractions import Fraction
import copy
import json
import shutil
import subprocess
import sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import tifffile

APP = Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1')
sys.path.insert(0, str(APP))
from lenticular.printing import encode
from lenticular.runner import digest, find_blender, preview

WORK = Path(__file__).resolve().parent
SOURCE = APP/'outputs/contour-correction-20261010/coupled'
DELIVERY = Path(r'C:\Users\USER\Downloads\Lenticular-Portre-50-75-100LPI-20261009-35bdac\50.20-Uc-Derinlik-20261010')
PROFILES = [('A', 'HAFIF-DERINLIK', 'Hafif derinlik', .60, .60),
            ('B', 'DENGELI-GUCLU', 'Dengeli / güçlü', 1., 1.),
            ('C', 'ARKA-PLAN-AGIRLIKLI', 'Arka plan ağırlıklı', .70, 1.)]

def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')

def prepare():
    assert not DELIVERY.exists(), 'Use a fresh delivery folder.'
    DELIVERY.mkdir(parents=True)
    job = json.loads((SOURCE/'job.json').read_text(encoding='utf-8'))
    cfg = job['config']
    d = np.load(SOURCE/'depth_proximity.npy', allow_pickle=False)
    reference = (1/cfg['zero']-1/cfg['far'])/(1/cfg['near']-1/cfg['far'])
    assert abs(float(d[432, 958])-reference) < 1e-5
    old = APP/'outputs/surface-upgrade-20261009-220345/native-portrait-final/print/print-report.json'
    settings = json.loads(old.read_text(encoding='utf-8'))['settings']
    settings.update(nominal_lpi=50, effective_lpi=50.20, ppi=1200, printer_dpi=1200,
                    ne=10, stripe_sampling='area', white_underbase=False, phase=0,
                    pitch_verified=False, pitch_candidates=3, allow_unfilled=False)
    width = round(settings['width_mm']*1200/25.4)
    gap = round(5/25.4*1200)
    origins = [i*(width+gap) for i in range(3)]
    angle = np.arctan(cfg['positions'][-1]/cfg['zero'])
    positions = (cfg['zero']*np.tan(np.linspace(-angle, angle, 10))).tolist()
    variants = []
    for origin, (key, name, label, front, back) in zip(origins, PROFILES):
        folder = WORK/key
        (folder/'views').mkdir(parents=True)
        transformed = (reference+(d-reference)*np.where(d >= reference, front, back)).astype(np.float32)
        assert 0 <= transformed.min() <= transformed.max() <= 1
        assert abs(float(transformed[432, 958])-reference) < 1e-5
        np.save(folder/'depth_proximity.npy', transformed, allow_pickle=False)
        current = copy.deepcopy(job)
        current['stage'] = 'cached_corrected_scene_print_trial'
        current['config'].update(nr=10, ne=10, positions=positions, camera_span=positions[-1]-positions[0])
        current.pop('surfaces', None)
        current.pop('visual_acceptance', None)
        current.update(cached_scene=str(SOURCE/'scene.blend'),
                       surface_transform=dict(front_gain=front, back_gain=back, reference=reference),
                       trial_only=True, known_visual_limitation='Narrow shorts fold may retain side-view deformation.')
        current['limitations'] = ['Single-photo hidden surfaces are inferred.',
            'Comparison test; narrow shorts-fold deformation remains possible.',
            'Physical print sharpness and depth are not verified.']
        write(folder/'job.json', current)
        if front == back == 1:
            shutil.copy2(SOURCE/'views/view_0000.png', folder/'views/view_0000.png')
            shutil.copy2(SOURCE/'views/view_0001.png', folder/'views/view_0009.png')
        phase = float(Fraction(origin)*Fraction('50.20')/1200 % 1)
        variant_settings = settings | {'phase':phase}
        delta = job['mesh']['focal_px']*(positions[-1]-positions[0])*(
            1/cfg['zero'] - ((1-transformed)/cfg['far']+transformed/cfg['near']))
        front_percent = -float(delta.min())/job['size'][0]*100
        back_percent = float(delta.max())/job['size'][0]*100
        variant = dict(id=key, name=name, label=label, folder=str(folder),
                       front_gain=front, back_gain=back, settings=variant_settings,
                       panel_origin_px=origin, zero_reference=reference,
                       endpoint_parallax_percent=dict(front=front_percent, back=back_percent),
                       filename=f'{key}-{name}-50.20LPI-1200PPI.tif')
        variants.append(variant)
    protected = {str(SOURCE/f):digest(SOURCE/f) for f in ('source.png','depth_proximity.npy','job.json','scene.blend')}
    manifest = dict(scene_source=str(SOURCE), delivery=str(DELIVERY), variants=variants,
        protected_hashes=protected, common_settings=settings, panel_origins_px=origins,
        source_size=job['size'], test_only=True, software_visual_perfection_verified=False,
        phase_basis='Panel phase equals global sheet origin * 50.20 / 1200 modulo one; no stripe resampling.',
        status='prepared')
    write(WORK/'manifest.json', manifest)
    print(json.dumps(dict(stage='prepared', delivery=str(DELIVERY),
          profiles=[{'id':v['id'], **v['endpoint_parallax_percent']} for v in variants])), flush=True)
    return manifest

def render(manifest):
    if all((Path(v['folder'])/'geometry-checks.json').is_file() and all(
        (Path(v['folder'])/f'views/view_{i:04d}.png').is_file() for i in range(10)
    ) for v in manifest['variants']):
        print('ALL_TRIAL_VIEWS_REUSED', flush=True)
        return
    command = [str(find_blender()), '--background', '--python', str(WORK/'render_variants.py'), '--', str(WORK/'manifest.json')]
    with (WORK/'blender.log').open('a', encoding='utf-8') as log:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
        for line in process.stdout:
            log.write(line)
            if 'TRIAL_PROGRESS' in line or 'ALL_TRIAL_VIEWS_READY' in line or 'TRIAL_REUSED' in line:
                log.flush()
                print(line.strip(), flush=True)
        if process.wait() != 0:
            raise RuntimeError('Blender failed; inspect blender.log before retrying.')

def export(manifest):
    results = []
    for variant in manifest['variants']:
        folder = Path(variant['folder'])
        job = json.loads((folder/'job.json').read_text(encoding='utf-8'))
        # Ray-preserving geometry transforms leave the zero-camera image fixed.
        # The proof stage explicitly requires this common rendered reference.
        if not (folder/'center.png').is_file():
            shutil.copy2(SOURCE/'center.png', folder/'center.png')
        if not (folder/'coverage.json').is_file():
            preview(folder, job)
        coverage = json.loads((folder/'coverage.json').read_text())
        assert coverage['max_nonopaque_fraction'] < .0005
        last = [-1]
        def progress(message):
            percent = int(message.split('%')[-1])
            bucket = percent//25
            if bucket > last[0]:
                last[0] = bucket
                print(f"PRINT_PROGRESS {variant['id']} {percent}%", flush=True)
        output = folder/'print'
        if output.is_dir() and not (output/'print-report.json').is_file():
            # Preserve the interrupted raster and use a fresh final export.
            output = folder/'print-complete'
        if (output/'print-report.json').is_file():
            report = json.loads((output/'print-report.json').read_text(encoding='utf-8'))
            assert digest(output/'interlaced.tif') == report['interlaced_sha256']
        else:
            report = encode(folder, output, variant['settings'], progress=progress)
        assert report['raster_integrity']['sampled_pixels_verified']
        assert report['distinct_source_images'] == report['nr'] == report['ne'] == 10
        assert report['source_indices'] == list(range(9, -1, -1))
        assert report['nonopaque_source_fraction'] < .0005
        target = DELIVERY/variant['filename']
        shutil.copy2(output/'interlaced.tif', target)
        assert digest(target) == report['interlaced_sha256']
        write(DELIVERY/f"{variant['id']}-BASKI-RAPORU.json", report | {'trial_profile':variant})
        results.append(report)
        print(f"PRINT_READY {variant['id']}", flush=True)
    return results

def combine(manifest, reports):
    paths = [DELIVERY/v['filename'] for v in manifest['variants']]
    rasters = [tifffile.memmap(p) for p in paths]
    height, width = rasters[0].shape[:2]
    origins = manifest['panel_origins_px']
    sheet_width = origins[-1]+width
    footer_height = 700
    footer = Image.new('RGB', (sheet_width, footer_height), 'white')
    draw = ImageDraw.Draw(footer)
    title = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 112)
    small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 82)
    for origin, variant in zip(origins, manifest['variants']):
        x = origin+95
        draw.text((x,55), f"{variant['id']} — {variant['label']}", fill='black', font=title)
        draw.text((x,225), f"Ön %{round(100*variant['front_gain'])} / Arka %{round(100*variant['back_gain'])} • 10 bakış", fill='black', font=small)
        draw.text((x,370), '50,20 LPI • 1200 PPI • Portre eni 13 cm', fill='black', font=small)
        draw.text((x,510), '%100 ölçekte baskı • Karşılaştırma denemesi', fill='black', font=small)
    footer = np.asarray(footer)
    with tifffile.TiffFile(paths[0]) as tif:
        icc = tif.pages[0].tags[34675].value
    combined = DELIVERY/'TEK-BASKI-A-HAFIF-B-DENGELI-C-ARKA-DERINLIK.tif'
    def strips():
        for y in range(0, height+footer_height, 128):
            count = min(128, height+footer_height-y)
            tile = np.full((count, sheet_width, 3), 255, np.uint8)
            n = max(0, min(count, height-y))
            for origin, raster in zip(origins, rasters):
                tile[:n, origin:origin+width] = raster[y:y+n]
            if n < count:
                fy = max(0, y-height)
                tile[n:] = footer[fy:fy+count-n]
            yield tile
    with tifffile.TiffWriter(combined) as tif:
        tif.write(data=strips(), shape=(height+footer_height,sheet_width,3), dtype=np.uint8,
            photometric='rgb', rowsperstrip=128, resolution=(1200,1200), resolutionunit='INCH',
            metadata=None, extratags=[(34675,'B',len(icc),icc,False)])
    saved = tifffile.memmap(combined)
    for y in range(0,height,128):
        for origin, raster in zip(origins,rasters):
            assert np.array_equal(saved[y:min(height,y+128),origin:origin+width], raster[y:y+128])
    assert np.array_equal(saved[height:],footer)
    # Check continuous lens phase across the full sheet at every panel pixel.
    columns = np.arange(width,dtype=np.float64)+.5
    for origin,variant in zip(origins,manifest['variants']):
        global_phase = (columns+origin)*50.2/1200
        local_phase = columns*50.2/1200+variant['settings']['phase']
        error = (global_phase-local_phase+.5)%1-.5
        assert np.max(np.abs(error)) < 1e-10
    white = DELIVERY/'ISTEGE-BAGLI-BEYAZ-MASKE.tif'
    with tifffile.TiffWriter(white) as tif:
        tif.write(data=(np.full((min(128,height+footer_height-y),sheet_width),255,np.uint8)
                       for y in range(0,height+footer_height,128)),
            shape=(height+footer_height,sheet_width), dtype=np.uint8, photometric='minisblack',
            rowsperstrip=128, resolution=(1200,1200), resolutionunit='INCH', metadata=None)
    checks = {}
    for path in paths+[combined,white]:
        with tifffile.TiffFile(path) as tif:
            page = tif.pages[0]
            assert len(tif.pages)==1 and page.dtype==np.uint8 and not page.is_tiled
            for tag in ('XResolution','YResolution'):
                num,den = page.tags[tag].value
                assert num/den == 1200
            assert page.tags['ResolutionUnit'].value == 2
            if path != white:
                assert 34675 in page.tags
            checks[path.name] = dict(sha256=digest(path), shape=list(page.shape), size_bytes=path.stat().st_size)
    return dict(files=checks, combined=str(combined),
        combined_size_mm=[sheet_width*25.4/1200,(height+footer_height)*25.4/1200],
        individual_size_mm=[width*25.4/1200,height*25.4/1200],
        panels_pixel_identical=True, global_lens_phase_continuous=True,
        all_tiff_metadata_verified=True)

def previews(manifest):
    width,height,gap,header,footer = 360,596,16,80,75
    canvas_size = (3*width+4*gap,header+height+footer)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',21)
    heading = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',23)
    frames=[]
    for index in range(10):
        image = Image.new('RGB',canvas_size,'#f4f3ef')
        draw = ImageDraw.Draw(image)
        for col,variant in enumerate(manifest['variants']):
            x=gap+col*(width+gap)
            with Image.open(Path(variant['folder'])/f'views/view_{index:04d}.png') as original:
                panel=original.convert('RGB').resize((width,height),Image.Resampling.LANCZOS)
            image.paste(panel,(x,header))
            draw.text((x,14),f"{variant['id']} · {variant['label']}",font=heading,fill='#182637')
            draw.text((x,48),f"Ön %{round(100*variant['front_gain'])} / Arka %{round(100*variant['back_gain'])}",font=font,fill='#435260')
        draw.text((gap,header+height+10),'50,20 LPI · 1200 PPI · 10 bakış · Burun referansı sabit',font=font,fill='#182637')
        draw.text((gap,header+height+40),'Ekran önizlemesi; baskı için TIFF dosyasını kullan.',font=font,fill='#435260')
        frames.append(image)
    sequence=frames+frames[-2:0:-1]
    sequence[0].save(DELIVERY/'UC-DERINLIK-HAREKETLI-ONIZLEME.png',save_all=True,append_images=sequence[1:],
                     duration=160,loop=0,disposal=0,blend=0)
    frames[-1].save(DELIVERY/'YERLESIM-ONIZLEME-BASILMAZ.jpg',quality=94)
    regions=[('El / başparmak',(340,850,680,1190)),('Şort kıvrımı',(220,1510,560,1850))]
    contact=Image.new('RGB',(6*300,2*330),'#202833')
    draw=ImageDraw.Draw(contact)
    for row,(label,box) in enumerate(regions):
        for col,variant in enumerate(manifest['variants']):
            for side,index in enumerate((0,9)):
                x=(col*2+side)*300;y=row*330
                with Image.open(Path(variant['folder'])/f'views/view_{index:04d}.png') as im:
                    contact.paste(im.convert('RGB').crop(box).resize((300,300)),(x,y+30))
                draw.text((x+5,y+3),f"{variant['id']} {'Sol' if side==0 else 'Sağ'} · {label}",font=font,fill='white')
    contact.save(WORK/'detail-review.jpg',quality=96)

def finish(manifest,validation):
    for filename,expected in manifest['protected_hashes'].items():
        assert digest(Path(filename)) == expected
    validation.update(source_files_unchanged=True, status='comparison_trials_generated_and_raster_verified',
        physical_depth_verified=False, physical_sharpness_verified=False,
        software_visual_perfection_verified=False,
        known_limitation='Narrow shorts fold can retain side-view deformation; these are comparison trials.')
    manifest['status']='complete'
    manifest['validation']=validation
    write(WORK/'manifest.json',manifest)
    write(DELIVERY/'AYARLAR-VE-DOGRULAMA.json',manifest)
    size=validation['combined_size_mm']
    guide=f'''50,20 LPI — ÜÇ DERİNLİK KARŞILAŞTIRMASI

Ana baskı: TEK-BASKI-A-HAFIF-B-DENGELI-C-ARKA-DERINLIK.tif
Solda A: Hafif. Ön ve arka derinlik temel sahnenin %60'ı.
Ortada B: Dengeli / güçlü. Ön ve arka derinlik %100.
Sağda C: Arka plan ağırlıklı. Ön %70, arka %100.
Yüzdeler derinlik tasarımına aittir; baskı ölçeği değildir.

Hepsi aynı fotoğraf, kadraj, burun referansı ve 10 farklı kamera bakışı.
Lens nominali 50 LPI; etkin pitch 50,20 LPI.
Dosya 1200 × 1200 PPI; yazıcı planı 1200 DPI.
Her portre 13,0006 × 21,5138 cm.
Birleşik baskı {size[0]/10:.4f} × {size[1]/10:.4f} cm; altında ayar etiketleri var.
%100 gerçek ölçekte bas. Sayfaya sığdırma ve otomatik ölçek kapalı olmalı.
Oluklar portrelerin üst-alt yönüne paralel. Üç panelin şerit fazı tek lens
hizalamasına göre devam eder. Tekil TIFF'ler de kullanılabilir.
Şeritli TIFF'i tekrar boyutlandırma; önizleme PNG/JPEG dosyalarını basma.
Önceki pitch testindeki malzeme, RIP, baskı yönü ve renk düzenini koru.
ISTEGE-BAGLI-BEYAZ-MASKE.tif yalnız mevcut baskı yöntemin beyaz alt katman istiyorsa kullanılır.

Karşılaştır: yüz netliği, öndeki el/diz etkisi, arka duvar/bitki ayrımı,
bakış değişiminde çift kenar ve şort kıvrımı.
Şorttaki dar kıvrımda kalan yan bakış deformasyonu nedeniyle bunlar kusursuzluk
onayı verilmiş son üretim dosyaları değil, istenen karşılaştırma denemeleridir.
Gerçek lens altındaki netlik ve 3D baskı sonrasında değerlendirilecek.
'''
    (DELIVERY/'BASKI-NOTU.txt').write_text(guide,encoding='utf-8-sig')
    print(json.dumps(dict(stage='complete',delivery=str(DELIVERY),
                         combined_size_mm=size,checks='pixel, phase, TIFF metadata, source integrity passed')),flush=True)

if __name__=='__main__':
    cv2.setNumThreads(2)
    if '--resume' in sys.argv:
        manifest=json.loads((WORK/'manifest.json').read_text(encoding='utf-8'))
        assert manifest['status'] != 'complete'
        for filename, expected in manifest['protected_hashes'].items():
            assert digest(Path(filename)) == expected
        for variant in manifest['variants']:
            for path in (Path(variant['folder'])/'views').glob('view_*.png'):
                with Image.open(path) as im:
                    im.verify()
    else:
        manifest=prepare()
    render(manifest)
    reports=export(manifest)
    validation=combine(manifest,reports)
    previews(manifest)
    finish(manifest,validation)

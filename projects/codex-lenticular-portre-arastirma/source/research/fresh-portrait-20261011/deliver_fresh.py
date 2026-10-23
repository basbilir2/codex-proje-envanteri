from pathlib import Path
from fractions import Fraction
import copy,importlib.util,json,math,shutil,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
APP=Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1')
sys.path.insert(0,str(APP))
from lenticular.printing import DEFAULTS
from lenticular.runner import digest
from run_render import run
WORK=Path(__file__).resolve().parent;SOURCE=WORK/'scene';TRIALS=WORK/'trials'
DELIVERY=Path(r'C:\Users\USER\Downloads\Lenticular-Portre-50-75-100LPI-20261009-35bdac\YENI-HARITA-50.20-1200-20261011')
spec=importlib.util.spec_from_file_location('delivery',WORK.parent/'pitch5020-depth-20261010/make_trials.py')
delivery=importlib.util.module_from_spec(spec);spec.loader.exec_module(delivery)
delivery.WORK=TRIALS;delivery.SOURCE=SOURCE;delivery.DELIVERY=DELIVERY

def write(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')

def inspect():
    rgb=np.asarray(Image.open(SOURCE/'source.png').convert('RGB'))
    center=np.asarray(Image.open(SOURCE/'center.png').convert('RGB'))
    delta=np.abs(center.astype(np.int16)-rgb.astype(np.int16))
    results=dict(mean_rgb_error=float(delta.mean()),fraction_error_over_32=float(np.mean(delta.max(axis=2)>32)))
    assert results['fraction_error_over_32']<.01,results
    regions=[('Göğüs / kol birleşimi',(960,900,1680,1870)),('Cep / şort kıvrımı',(200,1480,590,1910))]
    pictures=[('Kaynak',SOURCE/'source.png'),('Sol bakış',SOURCE/'views/view_0000.png'),('Sağ bakış',SOURCE/'views/view_0001.png')]
    canvas=Image.new('RGB',(1260,1000),'#202833');draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',23)
    for row,(label,box) in enumerate(regions):
        for col,(view,path) in enumerate(pictures):
            with Image.open(path) as im:crop=im.convert('RGB').crop(box)
            crop.thumbnail((410,456))
            canvas.paste(crop,(col*420+(420-crop.width)//2,row*500+40))
            draw.text((col*420+8,row*500+7),f'{label} · {view}',font=font,fill='white')
    canvas.save(WORK/'new-critical-regions.jpg',quality=97)
    write(SOURCE/'center-check.json',results)
    print(json.dumps(results),flush=True)

def prepare():
    TRIALS.mkdir(exist_ok=False);DELIVERY.mkdir(exist_ok=False)
    base=json.loads((SOURCE/'job.json').read_text(encoding='utf-8'));cfg=base['config']
    d=np.load(SOURCE/'depth_proximity.npy',allow_pickle=False)
    settings=DEFAULTS|dict(width_mm=130,height_mm=215.139,bleed_mm=0,ppi=1200,printer_dpi=1200,
        nominal_lpi=50,effective_lpi=50.20,ne=10,axis='vertical',phase=0,tilt_deg=0,
        reverse_views=False,mirror=False,fit='contain',stripe_sampling='area',
        crosstalk=0,compensation=0,crosstalk_matrix=None,icc_path=None,color_mode='RGB',
        white_underbase=False,pitch_verified=False,viewing_distance_mm=500,lens_view_angle_deg=30,
        allow_unfilled=False,pitch_candidates=3,lens_angle_verified=False,raster_ppi_verified=False)
    width=round(130*1200/25.4);origins=[i*(width+round(5*1200/25.4)) for i in range(3)]
    a=math.atan(cfg['positions'][-1]/cfg['zero'])
    positions=(cfg['zero']*np.tan(np.linspace(-a,a,10))).tolist()
    variants=[]
    for origin,(key,name,label,front,back) in zip(origins,delivery.PROFILES):
        folder=TRIALS/key;(folder/'views').mkdir(parents=True)
        current=copy.deepcopy(base);current['config'].update(nr=10,ne=10,positions=positions)
        current.pop('surfaces',None)
        current['cached_scene']=str(SOURCE/'scene.blend')
        current['surface_transform']=dict(reference=.5,front_gain=front,back_gain=back)
        current['source_is_fresh']=True
        write(folder/'job.json',current)
        transformed=(.5+(d-.5)*np.where(d>=.5,front,back)).astype(np.float32)
        assert transformed[432,958]==.5
        np.save(folder/'depth_proximity.npy',transformed,allow_pickle=False)
        shutil.copy2(SOURCE/'center.png',folder/'center.png')
        if front==back==1:
            shutil.copy2(SOURCE/'views/view_0000.png',folder/'views/view_0000.png')
            shutil.copy2(SOURCE/'views/view_0001.png',folder/'views/view_0009.png')
        phase=float(Fraction(origin)*Fraction('50.20')/1200%1)
        variants.append(dict(id=key,name=name,label=label,front_gain=front,back_gain=back,
            folder=str(folder),settings=settings|{'phase':phase},panel_origin_px=origin,
            filename=f'{key}-YENI-{name}-50.20LPI-1200PPI.tif',
            endpoint_parallax_percent=dict(front=2.4*front,back=2.4*back)))
    protected={str(SOURCE/f):digest(SOURCE/f) for f in ('source.png','depth_proximity.npy','job.json','scene.blend')}
    original=Path(r'C:\Users\USER\Downloads\vd-gigapixel-recover v2-2x-faceai v2.jpg')
    protected[str(original)]=digest(original)
    manifest=dict(scene_source=str(SOURCE),delivery=str(DELIVERY),variants=variants,
        common_settings=settings,panel_origins_px=origins,protected_hashes=protected,
        source_size=base['size'],status='prepared',fresh_depth=True,
        old_depth_used=False,old_textures_used=False,old_meshes_used=False,
        depth_partitioning=False,source_segmentation=json.loads((SOURCE/'segmentation.json').read_text()),
        depth_model=json.loads((WORK/'inference/metadata.json').read_text()),
        center_check=json.loads((SOURCE/'center-check.json').read_text()),
        physical_validation_pending=True)
    write(TRIALS/'manifest.json',manifest)
    return manifest

def finish(manifest):
    reports=delivery.export(manifest)
    validation=delivery.combine(manifest,reports)
    delivery.previews(manifest)
    assert len({r['interlaced_sha256'] for r in reports})==3
    for p,checksum in manifest['protected_hashes'].items():assert digest(Path(p))==checksum
    for name,source in [('YENI-DERINLIK-16BIT.png',SOURCE/'depth-16bit.png'),
                        ('GERCEK-NESNE-SINIRLARI.jpg',WORK/'semantic-boundaries-final.jpg'),
                        ('GOGUS-KOL-VE-CEP-KONTROLU.jpg',WORK/'new-critical-regions.jpg')]:
        shutil.copy2(source,DELIVERY/name)
    validation.update(source_files_unchanged=True,distinct_variants=True,physical_3d_verified=False)
    manifest.update(status='complete',validation=validation)
    write(TRIALS/'manifest.json',manifest);write(DELIVERY/'YENI-URETIM-VE-DOGRULAMA.json',manifest)
    note='''YENİ FOTOĞRAF TABANLI ÜRETİM — 50,20 LPI / 1200 PPI

Önceki derinlik haritası, katmanlar ve kamera görüntüleri kullanılmadı.
Kaynak JPEG'den DA3MONO-LARGE ile 1008 işlem çözünürlüğünde yeniden hesaplandı.
Yakın elin derinlik değerleri yüzdelik kırpmayla düzleştirilmedi.
Kişi ve kollar SAM 2.1 ile fotoğraftan ayrıldı. Gövde ve şort tek sürekli yüzey.
Kumaşın ortasından geçen genel derinlik dilimleri kullanılmadı.
Burun merkezi sabit: kaynak fotoğrafta (958, 432).

A: ön/arka %60. B: ön/arka %100. C: ön %70, arka %100.
Yüzdeler temel derinlik tasarımına göre güç oranıdır; baskı ölçeği değildir.
Her örnekte 10 bakış, etkin pitch 50,20 LPI, dosya 1200 PPI, yazıcı planı 1200 DPI.
Her portre yaklaşık 13 × 21,514 cm. Birleşik sayfa yaklaşık 40 × 23 cm.
TEK-BASKI-A-HAFIF-B-DENGELI-C-ARKA-DERINLIK.tif dosyasını %100 ölçekte bas.
Sayfaya sığdırmayı kapat. Lens olukları üst-alt yönünde olsun.
Üç panelin şerit fazı aynı lens hizasına göre kesintisiz hesaplandı.
PNG/JPEG dosyaları inceleme içindir; baskıda TIFF kullan.
Beyaz maske yalnız mevcut RIP düzenin beyaz alt baskı gerektiriyorsa kullanılır.

Derinlik ve gizli yüzeyler tek fotoğraftan tahmindir; fiziksel netlik ve 3D baskıda değerlendirilir.
Kaynaklar: https://github.com/ByteDance-Seed/Depth-Anything-3
https://huggingface.co/docs/transformers/model_doc/sam2
'''
    (DELIVERY/'BASKI-NOTU.txt').write_text(note,encoding='utf-8-sig')
    print(json.dumps(dict(status='complete',delivery=str(DELIVERY),checks=validation)),flush=True)

if __name__=='__main__':
    if sys.argv[-1]=='inspect':inspect()
    else:
        manifest=prepare();run('variants');finish(manifest)

"""Lens-specific portrait variants plus a pitch-only 50.20 LPI control."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import json
import shutil
import uuid

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import tifffile

import fullscene_portrait as base
from lenticular.geometry import validate
from lenticular.printing import encode, to_linear, from_linear
from lenticular.runner import preview, digest
from lenticular.repair import plan_parallax

HERE=Path(__file__).resolve().parent
RECORD=HERE/'portrait-75-100-current.json'
PROFILES={75:dict(ne=8,angle_deg=3.0),100:dict(ne=6,angle_deg=2.4)}

def write(path,data):
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')

def rec():return json.loads(RECORD.read_text(encoding='utf-8'))

def prepare():
    cv2.setNumThreads(2)
    old=base.record();original_work=Path(old['work']);protected=base.protected()
    token='20261009-'+uuid.uuid4().hex[:6]
    work=HERE/('portrait-75-100-'+token)
    delivery=Path(r'C:\Users\USER\Downloads')/('Lenticular-Portre-50-75-100LPI-'+token)
    work.mkdir(exist_ok=False);delivery.mkdir(exist_ok=False)
    shared=work/'shared';shared.mkdir()
    shutil.copy2(Path(old['shared'])/'photo.png',shared/'photo.png')
    with Image.open(shared/'photo.png') as im:photo=im.copy()
    with Image.open(original_work/'person-mask.png') as im:person=np.asarray(im)>0
    depth=np.load(Path(old['shared'])/'depth.npy',allow_pickle=False)
    reference=old['render']['zero_reference'];w,h=photo.size
    _,_,old_disparity=plan_parallax(depth,(w,h),old['render']|{'nr':12,'angle_deg':3.8})
    old_cfg=old['configs']['A']
    coefficient=(w*old_cfg['focal_mm']/old_cfg['sensor_width_mm']*old_cfg['camera_span']
                 *(1/old_cfg['near']-1/old_cfg['far']))
    yy=np.arange(h,dtype=np.float32)[:,None]
    head=np.clip((1050-yy)/350,0,1);head=head*head*(3-2*head)
    positive=old_disparity>0
    # Keep foreground hands/limbs unchanged in the depth map. Bring the human
    # positive surface closer to zero, most strongly around facial detail.
    gain=np.where(person,.65-.35*head,1.06)
    revised=np.where(positive,old_disparity*gain,old_disparity)
    adjusted=(reference-revised/coefficient).astype(np.float32)
    adjusted[~positive]=depth[~positive]
    adjusted[432,958]=reference
    assert np.isfinite(adjusted).all() and adjusted.min()>=-1e-6 and adjusted.max()<=1+1e-6
    adjusted=np.clip(adjusted,0,1)
    assert np.array_equal(adjusted[~positive],depth[~positive])
    np.save(shared/'depth.npy',adjusted,allow_pickle=False)
    Image.fromarray(np.rint(adjusted*255).astype(np.uint8)).save(work/'depth-design.png')
    head_pixels=(person & (yy<740)).astype(np.uint8)
    head_pixels=cv2.dilate(head_pixels,np.ones((31,31),np.uint8))
    head_mask=cv2.GaussianBlur(head_pixels.astype(np.float32),(0,0),14)
    np.save(shared/'head-filter-mask.npy',head_mask,allow_pickle=False)
    profiles={};angles=[]
    for lpi,profile in PROFILES.items():
        render_settings=old['render']|dict(nr=profile['ne'],angle_deg=profile['angle_deg'])
        geometry,stats,disparity=plan_parallax(adjusted,(w,h),render_settings)
        assert not stats['angle_limited'] and abs(float(disparity[432,958]))<.001
        a=np.round(np.linspace(-profile['angle_deg']/2,profile['angle_deg']/2,profile['ne']),12)
        angles.extend(a.tolist())
        cfg=validate(old_cfg|geometry|{'nr':len(a),'ne':profile['ne'],
            'positions':(geometry['zero']*np.tan(np.deg2rad(a))).tolist()})
        endpoints={name:float(disparity[y,x]) if name=='burun' else float(np.median(disparity[y-10:y+11,x-10:x+11]))
                   for name,(x,y) in base.POINTS.items()}
        assert min(endpoints['duvar_sol'],endpoints['duvar_sag'])>20
        assert endpoints['basparmak']<-30 and endpoints['diger_el']<-15
        assert abs(endpoints['burun'])<.001
        profiles[str(lpi)]=dict(**profile,config=cfg,angles_deg=a.tolist(),parallax=stats,
            expected_endpoint_source_px=endpoints,filter_sigma_source_px=w/(130/25.4*lpi)/8,
            facial_filtered_fraction=.35,nominal_lpi=lpi,effective_lpi=lpi,pitch_verified=False)
    union=np.unique(angles)
    master=validate(old_cfg|{'nr':len(union),'ne':6,
        'camera_span':profiles['75']['config']['camera_span'],
        'positions':(old_cfg['zero']*np.tan(np.deg2rad(union))).tolist()})
    current=dict(work=str(work),delivery=str(delivery),shared=str(shared),profiles=profiles,
        configs={'A':master},render=old['render']|{'nr':len(union),'angle_deg':3.0},
        printing=old['printing'],protected_hashes=protected,source_50_work=str(original_work),
        source_50_report=old['validation'],source_50_sha256=digest(Path(old['delivery'])/'TEK-BASKI-SOL-6-ORTA-10-SAG-12-GORSEL.tif'),
        source_50_tiff=str(Path(old['delivery'])/'TEK-BASKI-SOL-6-ORTA-10-SAG-12-GORSEL.tif'),
        unique_angles_deg=union.tolist(),lens_width_confirmed_mm=130,
        observed_50_pitch=dict(effective_lpi=50.20,uniform_black_white_transition_single_eye=True,
                             viewing_distance_confirmed=False),status='prepared',
        design=dict(human_positive_depth_gain=.65,head_positive_depth_gain=.30,
                    background_positive_depth_gain=1.06,foreground_depth_unchanged=True,
                    nose_fixed=True,source_RGB_unchanged=True),
        limitations=['75/100 lens view angles and effective pitches are unmeasured.',
            '3D geometry and invisible surfaces are estimated from one photograph.',
            '75 and 100 are individually optimized profiles, not a pure LPI-only comparison.',
            'Small foreground silhouette reconstruction traces may remain.'])
    assert base.protected()==protected
    write(RECORD,current);write(delivery/'AYARLAR-VE-DERINLIK-PLANI.json',current)
    print(json.dumps(dict(delivery=str(delivery),views=len(union),profiles=profiles),ensure_ascii=False),flush=True)

def export_control():
    r=rec();work=Path(r['work']);delivery=Path(r['delivery'])
    settings=r['printing']|dict(nominal_lpi=50,effective_lpi=50.20,ne=10,pitch_verified=True)
    report=encode(Path(r['source_50_work'])/'conditioned',work/'control-50',settings)
    assert report['source_indices']==r['source_50_report']['source_selections']['10']
    assert report['distinct_source_images']==10 and report['raster_integrity']['sampled_pixels_verified']
    target=delivery/'50LPI-LENS-50.20-PITCH-10-GORSEL-KONTROL.tif'
    shutil.copy2(work/'control-50/interlaced.tif',target)
    assert digest(target)==report['interlaced_sha256']
    report['comparison']='Only effective pitch changed from 50.00 to 50.20; old 3.8-degree geometry, RGB filtering and 10 views retained.'
    report['pitch_observation']=r['observed_50_pitch']
    write(delivery/'50.20-PITCH-KONTROL-RAPORU.json',report)
    r['control_report']=report;r['control_tiff']=str(target);write(RECORD,r)
    print('50.20_PITCH_ONLY_CONTROL_READY',flush=True)

def render():
    base.RECORD=RECORD
    base.render()

def deliver():
    cv2.setNumThreads(2);r=rec();work=Path(r['work']);delivery=Path(r['delivery'])
    shared=Path(r['shared']);master=work/'A/render'
    with Image.open(shared/'photo.png') as im:source=np.array(im.convert('RGB'))
    head_mask=np.load(shared/'head-filter-mask.npy',allow_pickle=False)
    master_job=json.loads((master/'job.json').read_text(encoding='utf-8'))
    # Metadata must describe the explicit camera positions actually rendered.
    master_config=master_job['config']
    master_config['camera_span']=float(np.ptp(master_config['positions']))
    r['configs']['A']=master_config
    write(master/'job.json',master_job)
    write(RECORD,r)
    write(delivery/'AYARLAR-VE-DERINLIK-PLANI.json',r)
    master_angles=np.array(r['unique_angles_deg']);results={}
    for lpi in (75,100):
        profile=r['profiles'][str(lpi)];folder=work/f'views-{lpi}'
        target=delivery/f'{lpi}LPI-{profile["ne"]}-GORSEL-1200PPI-TAM-PORTRE.tif'
        report_path=delivery/f'{lpi}LPI-BASKI-RAPORU.json'
        if report_path.exists():
            report=json.loads(report_path.read_text(encoding='utf-8'))
            assert digest(target)==report['interlaced_sha256']
            assert report['distinct_source_images']==profile['ne']
            assert report['source_indices']==list(range(profile['ne']-1,-1,-1))
            assert report['pixels_per_channel']==2 and report['raster_integrity']['sampled_pixels_verified']
            assert json.loads((folder/'job.json').read_text(encoding='utf-8'))['config']==profile['config']
            assert report['settings']['effective_lpi']==lpi
            assert digest(work/f'conditioned-{lpi}/job.json')==report['source_job_sha256']
            motions=base.inspect_motion(folder,source)
            for name,data in motions.items():
                assert abs(data['endpoint_px']-profile['expected_endpoint_source_px'][name])<8
            indices=[int(np.argmin(abs(master_angles-angle))) for angle in profile['angles_deg']]
            results[str(lpi)]=dict(tiff=str(target),report=report,rendered_motion=motions,
                master_camera_indices=indices,settings=profile)
            print(f'{lpi}_LPI_VERIFIED_EXISTING_PORTRAIT',flush=True)
            continue
        (folder/'views').mkdir(parents=True,exist_ok=False)
        job=master_job|{'config':profile['config']};write(folder/'job.json',job)
        indices=[]
        for i,angle in enumerate(profile['angles_deg']):
            index=int(np.argmin(abs(master_angles-angle)));assert abs(master_angles[index]-angle)<1e-10
            indices.append(index);shutil.copy2(master/f'views/view_{index:04d}.png',folder/f'views/view_{i:04d}.png')
        shutil.copy2(master/'center.png',folder/'center.png');preview(folder,job)
        coverage=json.loads((folder/'coverage.json').read_text(encoding='utf-8'))
        assert coverage['max_nonopaque_fraction']<.0005
        motions=base.inspect_motion(folder,source)
        for name,data in motions.items():
            assert abs(data['endpoint_px']-profile['expected_endpoint_source_px'][name])<8
        conditioned=work/f'conditioned-{lpi}';(conditioned/'views').mkdir(parents=True,exist_ok=False)
        write(conditioned/'job.json',job);shutil.copy2(folder/'center.png',conditioned/'center.png')
        sigma=profile['filter_sigma_source_px']
        for i in range(profile['ne']):
            with Image.open(folder/f'views/view_{i:04d}.png') as im:rgba=np.array(im.convert('RGBA'))
            linear=to_linear(rgba[:,:,:3]);filtered=cv2.GaussianBlur(linear,(0,1),sigma,borderType=cv2.BORDER_REFLECT_101)
            # Lens-specific texture filtering, much weaker over facial detail;
            # never blur or sharpen a finished interlaced raster.
            amount=1-.65*head_mask
            rgba[:,:,:3]=from_linear(linear+(filtered-linear)*amount[:,:,None])
            Image.fromarray(rgba).save(conditioned/f'views/view_{i:04d}.png')
        settings=r['printing']|dict(nominal_lpi=lpi,effective_lpi=lpi,ne=profile['ne'],pitch_verified=False)
        report=encode(conditioned,work/f'print-{lpi}',settings)
        assert report['distinct_source_images']==profile['ne'] and report['raster_integrity']['sampled_pixels_verified']
        assert report['source_indices']==list(range(profile['ne']-1,-1,-1))
        assert report['pixels_per_channel']==2
        target=delivery/f'{lpi}LPI-{profile["ne"]}-GORSEL-1200PPI-TAM-PORTRE.tif'
        shutil.copy2(work/f'print-{lpi}/interlaced.tif',target)
        assert digest(target)==report['interlaced_sha256']
        write(delivery/f'{lpi}LPI-BASKI-RAPORU.json',report)
        results[str(lpi)]=dict(tiff=str(target),report=report,rendered_motion=motions,
            master_camera_indices=indices,settings=profile)
        print(f'{lpi}_LPI_PORTRAIT_READY',flush=True)
    paths=[Path(r['control_tiff']),Path(results['75']['tiff']),Path(results['100']['tiff'])]
    rasters=[tifffile.memmap(p) for p in paths];h,w=rasters[0].shape[:2]
    assert all(a.shape==(h,w,3) for a in rasters)
    gap=240+(-w)%48;origins=[i*(w+gap) for i in range(3)]
    assert all(x%48==0 for x in origins)
    sw=origins[-1]+w;fh=700
    footer=Image.new('RGB',(sw,fh),'white');draw=ImageDraw.Draw(footer)
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',115)
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',78)
    labels=[('50 LPI LENS / PITCH 50,20 / 10 GÖRSEL','Yalnız pitch düzeltildi / Eski 3,8° tasarım'),
            ('75 LPI / 8 GÖRSEL / 3,0°','Yeni tam hacim / Burun sabit / En 13 cm'),
            ('100 LPI / 6 GÖRSEL / 2,4°','Yeni tam hacim / Burun sabit / En 13 cm')]
    for origin,(label,note) in zip(origins,labels):
        assert draw.textbbox((origin+80,65),label,font=font)[2]<origin+w
        draw.text((origin+80,65),label,font=font,fill='black')
        draw.text((origin+80,245),note,font=small,fill='black')
        draw.text((origin+80,420),'1200 PPI / %100 baskı / Uygun lensle kontrol',font=small,fill='black')
    footer=np.array(footer)
    with tifffile.TiffFile(paths[0]) as f:icc=f.pages[0].tags[34675].value
    combined=delivery/'TEK-BASKI-SOL-50.20-ORTA-75-SAG-100-LPI.tif'
    def strips():
        for y in range(0,h+fh,128):
            n=min(128,h+fh-y);tile=np.full((n,sw,3),255,np.uint8);image_n=max(0,min(n,h-y))
            for origin,raster in zip(origins,rasters):tile[:image_n,origin:origin+w]=raster[y:y+image_n]
            if image_n<n:
                fy=max(0,y-h);tile[image_n:]=footer[fy:fy+n-image_n]
            yield tile
    with tifffile.TiffWriter(combined) as f:
        f.write(data=strips(),shape=(h+fh,sw,3),dtype=np.uint8,photometric='rgb',rowsperstrip=128,
            resolution=(1200,1200),resolutionunit='INCH',metadata=None,extratags=[(34675,'B',len(icc),icc,False)])
    saved=tifffile.memmap(combined)
    for y in range(0,h,128):
        for origin,raster in zip(origins,rasters):assert np.array_equal(saved[y:min(h,y+128),origin:origin+w],raster[y:y+128])
    assert np.array_equal(saved[h:],footer)
    white=delivery/'ISTEGE-BAGLI-UC-PORTRE-BEYAZ-MASKESI.tif'
    with tifffile.TiffWriter(white) as f:
        f.write(data=(np.full((min(128,h+fh-y),sw),255,np.uint8) for y in range(0,h+fh,128)),
            shape=(h+fh,sw),dtype=np.uint8,photometric='minisblack',rowsperstrip=128,
            resolution=(1200,1200),resolutionunit='INCH',metadata=None)
    assert base.protected()==r['protected_hashes'] and digest(Path(r['source_50_tiff']))==r['source_50_sha256']
    validation=dict(status='digital_checks_passed_physical_print_pending',results=results,
        combined_size_mm=[sw/1200*25.4,(h+fh)/1200*25.4],individual_size_mm=[w/1200*25.4,h/1200*25.4],
        all_panels_pixel_identical_to_individual_files=True,source_unchanged=True,
        physical_sharpness_verified=False,physical_3d_verified=False,
        sha256={p.name:digest(p) for p in (*paths,combined,white)},limitations=r['limitations'])
    write(delivery/'SON-DENETIM.json',validation)
    guide='''BASILACAK GÖRSEL DOSYALARI — PITCH TESTİ DEĞİLDİR

TEK BASKI: TEK-BASKI-SOL-50.20-ORTA-75-SAG-100-LPI.tif
Solda: 50 LPI lens için 50,20 pitch / eski 10 görüntülü 3,8° tasarım.
Ortada: 75 LPI / 8 görüntü / yeni 3,0° tam-resim tasarım.
Sağda: 100 LPI / 6 görüntü / yeni 2,4° tam-resim tasarım.
Tekil portre TIFF'leri de ayrı kullanılabilir. Hepsi 13 cm genişliğinde.
%100 ölçek; medyaya sığdır / otomatik ölçek kapalı. Tüm birleşik dosyayı 13 cm yapma.
Önceki portreyle aynı RIP döndürmesini, baskı yönünü, cihaz profili/çözünürlüğünü,
hızını, pass, UV, malzeme ve beyaz katmanını koru. JPEG önizlemeyi basma.
Beyaz maskesi yalnız mevcut yöntem zaten beyaz alt katman kullanıyorsa yardımcıdır.

NEDEN BU AYARLAR?
1200 PPI / 75 LPI = 16 piksel/lens. 8 görüntüyle bakış başına 2 piksel.
1200 PPI / 100 LPI = 12 piksel/lens. 6 görüntüyle bakış başına 2 piksel.
100 LPI'de 12 görüntü bir piksellik dar kanallar gerektirir; bu denemede kullanılmadı.
3,0° ve 2,4° toplam hesaplanmış kamera aralığıdır; lensin ölçülmüş bakış açısı değildir.
75/100 sürümlerinde yüzün pozitif derinlik kayması azaltıldı, burun sabit tutuldu;
gövde baskı düzlemine yaklaştırıldı ve arka planla ayrımı büyütüldü.
Öndeki eller/bacakların derinlik haritası korunurken toplam kamera aralığı,
daha sık lenslerde netlik denemesi için 75'te 3,0°, 100'de 2,4° seçildi.
Kaynak fotoğraf değişmedi; yatay filtre yeni LPI'ye göre daha hafif ve yüzde daha zayıf.
Filtre kamera görüntülerinde uygulandı; bitmiş şeritli TIFF'e uygulanmadı.
Görüntüler farklı gerçek fotoğraflar değil, tek fotoğraftan hesaplanmış bakışlardır.
Tek fotoğrafta görünmeyen kenarlarda küçük yeniden kurma izleri kalabilir.

50,20 KONTROLÜ
Bu bölümde yalnız pitch 50,00'dan 50,20'ye değişti. Yüz/derinlik/filtre aynı kaldı.
Kullanıcının tek gözle tüm şeridin birlikte siyah/beyaz değiştiği gözlemine dayanır.
Gerçek izleme mesafesi henüz sayısal olarak doğrulanmadı; aynı test mesafesini kullan.
50 LPI lens için bulunan 50,20, 75/100 lenslere otomatik aktarılmadı.
75/100 dosyaları NOMİNAL pitch'tedir; gerçek lens açıları ve pitch'leri ölçülmedi.

KARŞILAŞTIRMA
Her portrede SADECE ETİKETTEKİ LPI'ye uygun lensi kullan. Oluklar portrenin üst-alt yönüne paralel.
Lensi düz baskı yüzeyiyle doğru temas halinde, aynı ışık ve mesafede yerleştir.
Başını küçük hareketlerle gezdir. Burun/gözler, diğer el, dizler ve duvarı ayrı değerlendir.
50,20 kontrolünü eski 50,00 baskıyla karşılaştırırsan yalnız pitch değişimini ayırabilirsin.
75/100 sürümleri ayrı optimize edildi: farkların tamamını yalnız LPI'ye bağlayamayız.
Yüksek LPI, UV yazıcıda otomatik netlik garantisi değildir. Dar şeritler mürekkep
yayılması, baskı ölçeği ve hizalamaya daha hassas olabilir.
Sonucu her lens için: yüz netliği / kırçıl / çift kenar / arka plan ayrımı / genel 3D diye yaz.

Kaynak: https://dplenticular.com/technology/lenticular-depth-calculator/
'''
    (delivery/'BASKI-VE-KARSILASTIRMA.txt').write_text(guide,encoding='utf-8-sig')
    with Image.open(master/'center.png') as im:im=im.convert('RGB');im.thumbnail((450,750));panel=im.copy()
    image=Image.new('RGB',(1410,865),'white');draw=ImageDraw.Draw(image)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',23)
    for i,label in enumerate(('50,20 / 10 GÖRSEL / KONTROL','75 LPI / 8 GÖRSEL / YENİ','100 LPI / 6 GÖRSEL / YENİ')):
        image.paste(panel,(10+i*470,55));draw.text((10+i*470,10),label,font=font,fill='black')
    draw.text((10,815),'Yalnız yerleşim önizlemesi; lens altındaki netliği ve gerçek 3D sonucunu göstermez.',font=font,fill='black')
    image.save(delivery/'YERLESIM-ONIZLEME-BUNU-BASMA.jpg',quality=95)
    r['validation']=validation;r['status']='complete';write(RECORD,r)
    print(json.dumps(dict(status='complete',delivery=str(delivery),size_mm=validation['combined_size_mm']),ensure_ascii=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('prepare','control','render','deliver'))
    {'prepare':prepare,'control':export_control,'render':render,'deliver':deliver}[parser.parse_args().stage]()

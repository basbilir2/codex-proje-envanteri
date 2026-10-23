"""Reproducible, source-preserving portrait correction and optical test delivery."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil
import sys
import urllib.request
from urllib.parse import urlparse,parse_qs

import numpy as np
from PIL import Image,ImageDraw,ImageFont

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lenticular.pipeline import render_settings
from lenticular.printing import DEFAULTS,encode
from lenticular.repair import editable_depth,plan_parallax
from lenticular.runner import digest

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'outputs/studio/20261008-223746-051b86f3'
ASSET='cc3613687e1b438f'
POINT={'x':958/1871,'y':432/3097}


def write(path,data):
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')


def api(path,data=None,filename=None):
    info=json.loads((ROOT/'.studio/server.json').read_text(encoding='utf-8'))
    address=urlparse(info['url'])
    headers={'X-Studio-Token':parse_qs(address.query)['t'][0]}
    if filename:
        headers['X-Filename']=filename
    elif data is not None:
        headers['Content-Type']='application/json'
        data=json.dumps(data).encode()
    request=urllib.request.Request(f'{address.scheme}://{address.netloc}{path}',data=data,headers=headers)
    with urllib.request.urlopen(request,timeout=60) as response:return json.load(response)


def prepare():
    state=api('/api/state')
    asset=state['assets'][ASSET]
    original_hash=digest(Path(asset['original']))
    if original_hash.lower()!='d7d3c1c669483c99540c1f82ad71e34d3aa9b027facf6ce1c5785e400f694ec5':
        raise ValueError('Kaynak fotoğraf beklenen fotoğrafla uyuşmuyor.')
    output=Path.home()/'Downloads'/('Lenticular-50LPI-Duzeltme-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
    output.mkdir(exist_ok=False)
    write(output/'Onceki-Kaynak-Kaydi.json',asset)
    base=np.load(OLD/'prepared/depth.npy',allow_pickle=False)
    height,width=base.shape
    yy,xx=np.ogrid[:height,:width]
    def mask(cx,cy,rx,ry):
        q=((xx-cx)/rx)**2+((yy-cy)/ry)**2
        t=np.clip((1-q)/.55,0,1)
        return (t*t*(3-2*t)).astype(np.float32),np.clip(1-q,0,1).astype(np.float32)
    corrected=base.copy()
    body,roundness=mask(950,1310,570,680)
    body*=np.clip((base-.15)/.1,0,1)*np.clip((.7-base)/.1,0,1)
    corrected+=body*((base-.32)*.6+.055*roundness**2)
    face,_=mask(958,425,190,285)
    nose=float(base[432,958])
    face_target=np.maximum(nose+4*(base-nose),.18)
    corrected+=face*(face_target-base)
    corrected=np.clip(corrected,0,1).astype(np.float32)
    previous=json.loads((OLD/'project.json').read_text(encoding='utf-8'))
    rendering=render_settings(previous['render']|dict(nr=12,angle_deg=3.8,
        effect_strength=1,front_strength=1,back_strength=1,depth_curve='linear',
        reference_point=POINT,zero_reference=nose,depth_smoothing=.1,
        edge_refinement=.35,detail_enabled=False,surface_strength=0,
        depth_strokes=[],render_long_edge=0,max_parallax_percent=5.0))
    printing=DEFAULTS|previous['print']|dict(ne=12,ppi=1200,printer_dpi=1200,
        reverse_views=False,nominal_lpi=50,effective_lpi=50,pitch_verified=False,
        lens_angle_verified=False,raster_ppi_verified=False,lens_view_angle_deg=30,
        white_underbase=True,pitch_step=.01,pitch_candidates=21)
    with Image.open(OLD/'prepared/photo.png') as photo:
        actual,edits=editable_depth(corrected,rendering,photo)
    rendering['zero_reference']=edits['zero_reference']
    _,parallax,disparity=plan_parallax(actual,(width,height),rendering)
    locations={'burun':(958,432),'sol_yanak':(848,444),'sag_yanak':(1046,444),
        'alin':(952,241),'cene':(954,625),'ondeki_el':(550,1450),'duvar':(250,450)}
    measurements={}
    for label,(x,y) in locations.items():
        value=float(np.median(disparity[y-10:y+11,x-10:x+11]))
        measurements[label]=dict(endpoint_source_px=value,endpoint_print_mm=value*130/width)
    if abs(float(disparity[432,958]))>.001 or min(measurements[k]['endpoint_source_px'] for k in ('sol_yanak','sag_yanak'))<12:
        raise ValueError('Burun/yüz hacmi sayısal kontrolü geçmedi.')
    np.save(output/'Duzeltilmis-Derinlik.npy',corrected,allow_pickle=False)
    Image.fromarray(np.rint(actual*255).astype(np.uint8)).save(output/'Derinlik-Onizleme.png')
    write(output/'Hazirlik-Denetimi.json',dict(original_sha256=original_hash,reference_point=POINT,
        render=rendering,print=printing,measurements=measurements,parallax=parallax,
        method='Existing inferred depth; smooth local face residual gain 4, face floor .18; restrained torso volume. RGB photo unchanged.',
        limitations=['Single-photo inferred/artistic depth, not measured anatomy.',
            'Lens viewing angle and horizontal RIP resolution unverified; physical test required.']))
    api('/api/upload?kind=depth&asset='+ASSET,(output/'Duzeltilmis-Derinlik.npy').read_bytes(),'corrected-depth.npy')
    job=api('/api/jobs',dict(asset_id=ASSET,stage='full',render=rendering,print=printing))['id']
    api('/api/profile',dict(name='50 LPI · düzeltilmiş 12 görünüş · fiziksel test gerekli',render=rendering,print=printing))
    write(output/'Is-Kaydi.json',dict(job_id=job,output=str(output),original_sha256=original_hash))
    print(json.dumps(dict(job_id=job,output=str(output),face_measurements=measurements),ensure_ascii=False),flush=True)


def calibration(output):
    source=output/'Kontrol-Karti-Kameralari'
    (source/'views').mkdir(parents=True,exist_ok=False)
    width,height=1600,500
    focal=width*50/36
    span=.1993846153846154
    positions=np.linspace(-span/2,span/2,12)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',42)
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',29)
    palette=[(235,45,45),(235,100,25),(235,170,25),(195,210,35),(75,190,50),(25,175,130),
        (20,165,205),(35,100,225),(85,65,220),(150,55,210),(205,50,160),(225,50,100)]
    for i,p in enumerate(positions):
        image=Image.new('RGB',(width,height),'white')
        draw=ImageDraw.Draw(image)
        draw.rectangle((0,0,width,105),fill=palette[i])
        draw.text((35,20),f'BAKIS {i+1:02d} / 12 - egince sayi ve renk degismeli',font=font,fill='black')
        for cx,z,color,label in ((450,1.5,'#d63232','ONDE'),(800,2,'#168146','SABIT'),(1150,3,'#2861c0','ARKADA')):
            x=cx+focal*p*(1/2-1/z)
            draw.ellipse((x-62,190,x+62,314),fill=color)
            draw.text((x-70,335),label,font=font,fill='black')
        draw.line((800,175,800,320),fill='black',width=4)
        draw.line((730,252,870,252),fill='black',width=4)
        draw.text((35,440),'EN 130 mm - lens cizgileri DIKEY - %100 olcek',font=small,fill='black')
        image.save(source/f'views/view_{i:04d}.png')
        if i==6:image.save(source/'center.png')
    write(source/'job.json',dict(config=dict(nr=12,zero=2,near=1.5,far=3,
        positions=positions.tolist(),camera_axis='x'),mesh=dict(focal_px=focal)))
    for ppi,ne in ((1200,12),(600,6)):
        folder=output/f'Kontrol-{ppi}PPI-{ne}Kanal'
        settings=DEFAULTS|dict(width_mm=130,height_mm=130*height/width,
            ppi=ppi,nominal_lpi=50,effective_lpi=50,ne=ne,white_underbase=True,
            fit='contain',pitch_candidates=3)
        encode(source,folder,settings)
        shutil.copy2(folder/'interlaced.tif',output/f'ONCE-TEST-{ppi}PPI-{ne}Kanal.tif')
        shutil.copy2(folder/'white-underbase.tif',output/f'ONCE-TEST-{ppi}PPI-{ne}Kanal-Beyaz.tif')
    print('Kucuk optik kontrol kartlari hazir.',flush=True)


def deliver(output):
    record=json.loads((output/'Is-Kaydi.json').read_text(encoding='utf-8'))
    state=api('/api/state');job=state['jobs'][record['job_id']]
    if job['status']!='complete':
        print(json.dumps(dict(status=job['status'],progress=job.get('progress'),message=job.get('message')),ensure_ascii=False));return
    audit(output)
    folder=Path(job['output'])
    targets={'print/interlaced.tif':'Portre-13cm-50LPI-1200PPI-12Gorsel-DUZELTILMIS.tif',
        'print/white-underbase.tif':'Portre-Beyaz-Alt-Baski.tif',
        'print/print-report.json':'Baski-Raporu.json','print/baski-notlari.txt':'Baski-Notlari.txt',
        'print/pitch-test.tif':'Pitch-Testi-49.90-50.10-LPI.tif','print/pitch-test.json':'Pitch-Testi-Ayarlar.json',
        'print/registration.svg':'Hizalama.svg','project.json':'Ayarlar.json',
        'quality.json':'Gorunus-Kalite-Raporu.json','render/look-around.png':'Hareket-Onizlemesi-Fiziksel-Onay-Degil.png'}
    hashes={}
    for src,name in targets.items():
        target=output/name
        if target.exists():raise ValueError('Teslim dosyasi zaten var; üzerine yazılmaz.')
        shutil.copy2(folder/src,target)
        hashes[name]=digest(target)
        if hashes[name]!=digest(folder/src):raise ValueError('Teslim kopyasi hash ile uyuşmuyor.')
    if digest(Path(state['assets'][ASSET]['original']))!=record['original_sha256']:
        raise ValueError('Orijinal fotoğraf değişmiş.')
    write(output/'Teslim-Hashleri.json',hashes)
    print(json.dumps(dict(status='delivered',folder=str(output),job_id=record['job_id'],original_preserved=True),ensure_ascii=False),flush=True)


def audit(output):
    import cv2
    cv2.setNumThreads(2)
    record=json.loads((output/'Is-Kaydi.json').read_text(encoding='utf-8'))
    job=api('/api/state')['jobs'][record['job_id']]
    if job['status']!='complete':raise ValueError('Son denetim tamamlanmış iş gerektirir.')
    folder=Path(job['output']);render=folder/'render'
    report=json.loads((folder/'print/print-report.json').read_text(encoding='utf-8'))
    quality=json.loads((folder/'quality.json').read_text(encoding='utf-8'))
    cfg=json.loads((render/'job.json').read_text(encoding='utf-8'))
    photo=cv2.imread(str(folder/'prepared/photo.png'))
    ends=[cv2.imread(str(render/f'views/view_{i:04d}.png')) for i in (0,11)]
    points={'burun':(958,432),'sol_yanak':(848,444),'sag_yanak':(1046,444),
        'alin':(952,241),'cene':(954,625),'ondeki_el':(550,1450),'duvar':(250,450)}
    measured={}
    for name,(x,y) in points.items():
        # A broad nose patch includes cheeks with intentional nonzero relief.
        # Track the pinned tip itself, checked independently at 19 and 31 px.
        radius=9 if name=='burun' else 25
        template=photo[y-radius:y+radius+1,x-radius:x+radius+1]
        shifts=[];scores=[]
        for frame in ends:
            region=frame[y-45:y+46,x-115:x+116]
            result=cv2.matchTemplate(region,template,cv2.TM_CCOEFF_NORMED)
            _,score,_,position=cv2.minMaxLoc(result)
            shifts.append(position[0]-(115-radius));scores.append(float(score))
        measured[name]=dict(dx_first=shifts[0],dx_last=shifts[1],
            endpoint_shift_px=shifts[1]-shifts[0],correlation=scores,
            template_size_px=2*radius+1)
    nose_check=[]
    for frame in ends:
        match=cv2.matchTemplate(frame[387:478,843:1074],photo[417:448,943:974],cv2.TM_CCOEFF_NORMED)
        _,score,_,position=cv2.minMaxLoc(match)
        nose_check.append(dict(dx=position[0]-100,correlation=float(score)))
    assert report['source_indices']==list(range(11,-1,-1)),'Kamera şerit sırası yanlış.'
    assert report['distinct_source_images']==12,'Farklı kamera görüntüleri eksik.'
    assert report['raster_integrity']['sampled_pixels_verified'],'TIFF piksel denetimi geçmedi.'
    assert abs(quality['parallax']['reference_endpoint_disparity_px'])<.001,'Burun geometrik olarak kayıyor.'
    assert abs(measured['burun']['endpoint_shift_px'])<=2,'Burun görüntüde kayıyor.'
    assert abs(nose_check[1]['dx']-nose_check[0]['dx'])<=2,'Burun ikinci ölçümde kayıyor.'
    assert min(min(v['correlation']) for v in measured.values())>=.8,'Görüntü eşleşmesi güvenilir değil.'
    assert min(measured[k]['endpoint_shift_px'] for k in ('sol_yanak','sag_yanak'))>=12,'Yanakların hacim farkı zayıf.'
    assert measured['ondeki_el']['endpoint_shift_px']<0<measured['duvar']['endpoint_shift_px'],'Ön/arka ayrımı yanlış.'
    assert quality['max_nonopaque_fraction']<=.0005,'Görüntüde boş alan var.'
    result=dict(status='digital_checks_passed_physical_print_pending',job_id=record['job_id'],
        rendered_endpoint_measurements=measured,nose_geometry_shift_px=quality['parallax']['reference_endpoint_disparity_px'],
        independent_31px_nose_check=nose_check,
        distinct_rendered_images=report['distinct_source_images'],raster_integrity=report['raster_integrity'],
        channel_order=report['source_indices'],physical_3d_verified=False,
        limitations=['End-frame motion and TIFF integrity do not verify physical binocular channel separation.',
            'Hidden background remains estimated; inspect foreground edges on the physical control print.'])
    write(output/'Son-Denetim.json',result)
    print(json.dumps(result,ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('prepare','calibration','deliver','audit'));parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.stage=='prepare':prepare()
    elif args.stage=='calibration':calibration(args.output)
    elif args.stage=='audit':audit(args.output)
    else:deliver(args.output)

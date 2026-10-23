"""Portrait-specific inferred depth correction; never alters the RGB original."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.recover_50lpi import ROOT, ASSET, POINT, api, write
from lenticular.repair import plan_parallax
from lenticular.runner import digest
from lenticular.printing import encode

PREVIOUS=ROOT/'outputs/studio/20261009-104232-e4bb9119'
POINTS={'burun':(958,432),'basparmak':(525,1240),'sol_yanak':(848,444),
    'sag_yanak':(1046,444),'alin':(952,241),'cene':(954,625),
    'diger_el':(1390,1950),'govde':(1040,1330),'sol_diz':(530,2370),
    'sag_diz':(1370,2320),'duvar_sol':(250,450),'duvar_sag':(1570,620)}


def check_regions(values, old_thumb):
    """Reject a thumb-only success and preserve the user's accepted foreground."""
    if abs(values['burun'])>.001:raise ValueError('Burun referansı kayıyor.')
    if abs(values['basparmak']-old_thumb)>2:raise ValueError('Beğenilen başparmak değişti.')
    if values['sol_yanak']<36 or values['sag_yanak']<27:raise ValueError('Yüz iç hacmi yetersiz.')
    if values['diger_el']>-18:raise ValueError('Diğer el hâlâ sabit düzleme yakın.')
    if max(values['sol_diz'],values['sag_diz'])>-12:raise ValueError('Dizlerin yönü/hacmi yanlış.')
    if values['govde']<14:raise ValueError('Gövdenin ayrımı yetersiz.')
    if min(values['duvar_sol'],values['duvar_sag'])<30:raise ValueError('Arka plan yeterince ayrılmıyor.')


def consistent_motion(observations, pinned=False):
    """Require agreement at two patch scales; texture-poor skin is not a failure waiver."""
    accepted=[v for v in observations if min(v['correlations'])>=.80]
    if len(accepted)<2 or np.ptp([v['endpoint_px'] for v in accepted])>3:
        raise ValueError('Bölgesel görüntü ölçümü iki ölçekte doğrulanmadı.')
    return accepted[0]['endpoint_px'] if pinned else float(np.median([v['endpoint_px'] for v in accepted]))


def prepare():
    cv2.setNumThreads(2)
    state=api('/api/state');asset=state['assets'][ASSET]
    source_hash=digest(Path(asset['original']))
    if source_hash.lower()!='d7d3c1c669483c99540c1f82ad71e34d3aa9b027facf6ce1c5785e400f694ec5':
        raise ValueError('Kaynak fotoğraf uyuşmuyor.')
    output=Path.home()/'Downloads'/('Lenticular-50LPI-Bolgesel-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
    output.mkdir(exist_ok=False)
    write(output/'Onceki-Kaynak-Kaydi.json',asset)
    old=np.load(PREVIOUS/'prepared/depth.npy',allow_pickle=False)
    if old.shape!=(3098,1872):raise ValueError('Bu düzenleme yalnız incelenen portre içindir.')
    with Image.open(PREVIOUS/'prepared/photo.png') as im:rgb=np.asarray(im.convert('RGB'))
    h,w=old.shape;yy,xx=np.ogrid[:h,:w]
    def ellipse(cx,cy,rx,ry,feather=.25):
        q=((xx-cx)/rx)**2+((yy-cy)/ry)**2
        t=np.clip((1-q)/feather,0,1)
        return (t*t*(3-2*t)).astype(np.float32),np.clip(1-q,0,1).astype(np.float32)
    # Visible-person silhouette, constrained to the known source image.
    # No luminance-to-depth conversion: shadows/textile pattern are not geometry.
    from lenticular.layers import align_mask
    person=align_mask(rgb,old>.15).astype(np.float32)
    lowpass=cv2.GaussianBlur(old,(0,0),18)
    fine=np.clip(old-lowpass,-.025,.025)
    out=old.copy()
    def blend(mask,target):
        nonlocal out
        out=out*(1-mask)+np.asarray(target,dtype=np.float32)*mask
    # Back wall is a shallow, deliberately modeled surface; hidden color remains estimated.
    wall=.025+.09*(xx/(w-1))**2+.025*(yy/(h-1))
    _,stone1=ellipse(390,450,250,230)
    _,stone2=ellipse(1500,490,220,260)
    wall=wall+.08*stone1**2+.10*stone2**2
    ground=.075+.30*np.clip((yy-1750)/(h-1-1750),0,1)
    blend(1-person,np.where(yy>1750,ground,wall))
    body,roundness=ellipse(990,1390,610,720)
    blend(body*person,.16+.14*np.sqrt(roundness)+fine)
    # Knees/shins are in front of the pinned nose, not behind it.
    for cx,cy,rx,ry in ((510,2320,450,430),(1370,2300,350,450)):
        mask,roundness=ellipse(cx,cy,rx,ry)
        blend(mask*person,.52+.12*np.sqrt(roundness)+fine)
    for cx,cy,rx,ry in ((455,2670,240,330),(1260,2600,270,330)):
        mask,roundness=ellipse(cx,cy,rx,ry)
        blend(mask*person,.49+.10*roundness+fine)
    # Resting forearm / hand must have their own near-side volume.
    mask,roundness=ellipse(1435,1690,190,410)
    blend(mask*person,.52+.10*np.sqrt(roundness)+fine)
    mask,roundness=ellipse(1330,1920,260,205)
    blend(mask*person,.60+.10*np.sqrt(roundness)+fine)
    face,_=ellipse(958,420,205,330,.35)
    nose=float(old[432,958])
    blend(face*person,np.maximum(nose+1.75*(old-nose),.075))
    # Freeze the entire accepted raised-hand core, not just one pixel.
    hand_area,_=ellipse(525,1400,310,470)
    protected=(hand_area>0)&(old>.70)
    protected=cv2.dilate(protected.astype(np.uint8),np.ones((11,11),np.uint8))>0
    out[protected]=old[protected]
    out[432,958]=old[432,958]
    out=np.clip(out,0,1).astype(np.float32)
    rendering=json.loads((PREVIOUS/'project.json').read_text(encoding='utf-8'))['render']
    rendering.update(zero_reference=nose,reference_point=POINT,depth_smoothing=0,edge_refinement=0)
    printing=state['jobs']['20261009-104232-e4bb9119']['print'].copy()
    printing.update(ne=12,pitch_verified=False,lens_angle_verified=False,raster_ppi_verified=False)
    _,parallax,disparity=plan_parallax(out,(w,h),rendering)
    _,_,old_disparity=plan_parallax(old,(w,h),rendering)
    values={name:float(disparity[y,x]) if name=='burun' else
        float(np.median(disparity[y-10:y+11,x-10:x+11])) for name,(x,y) in POINTS.items()}
    old_thumb=float(np.median(old_disparity[1230:1251,515:536]))
    check_regions(values,old_thumb)
    if np.max(np.abs(out[protected]-old[protected]))!=0:raise ValueError('Korunan el değişti.')
    np.save(output/'Bolgesel-Derinlik.npy',out,allow_pickle=False)
    Image.fromarray(np.rint(out*255).astype(np.uint8)).save(output/'Derinlik-Onizleme.png')
    write(output/'Hazirlik-Denetimi.json',dict(original_sha256=source_hash,render=rendering,
        print=printing,planned_endpoint_px=values,thumb_unchanged_depth_pixels=int(protected.sum()),
        thumb_max_depth_change=0,parallax=parallax,
        method='Portrait-specific inferred/synthetic regional depth; raised-hand depth frozen; RGB unchanged.',
        limitations=['Not measured anatomy or recovered stone geometry.','Physical 3D remains unverified.']))
    api('/api/upload?kind=depth&asset='+ASSET,(output/'Bolgesel-Derinlik.npy').read_bytes(),'regional-depth.npy')
    identifier=api('/api/jobs',dict(asset_id=ASSET,stage='full',render=rendering,print=printing))['id']
    api('/api/profile',dict(name='50 LPI · bölgesel hacim · başparmak korundu · test gerekli',render=rendering,print=printing))
    write(output/'Is-Kaydi.json',dict(job_id=identifier,output=str(output),original_sha256=source_hash))
    print(json.dumps(dict(job_id=identifier,output=str(output),planned_endpoint_px=values),ensure_ascii=False),flush=True)


def finish(output):
    cv2.setNumThreads(2)
    record=json.loads((output/'Is-Kaydi.json').read_text(encoding='utf-8'))
    state=api('/api/state');job=state['jobs'][record['job_id']]
    if job['status']!='complete':raise ValueError(f"Çalışma henüz tamamlanmadı: {job['status']}")
    folder=Path(job['output']);views=Path(job['render_folder'])
    photo=cv2.imread(str(PREVIOUS/'prepared/photo.png'))
    frames=[cv2.imread(str(views/f'views/view_{i:04d}.png')) for i in (0,11)]
    values={};scores={}
    for name,(x,y) in POINTS.items():
        observations=[]
        for radius in ((9,15) if name=='burun' else (9,15,25)):
            template=photo[y-radius:y+radius+1,x-radius:x+radius+1]
            positions=[];correlations=[]
            for frame in frames:
                match=cv2.matchTemplate(frame[y-40:y+41,x-100:x+101],template,cv2.TM_CCOEFF_NORMED)
                _,score,_,location=cv2.minMaxLoc(match)
                positions.append(location[0]-(100-radius));correlations.append(float(score))
            observations.append(dict(template_size_px=2*radius+1,dx_first=positions[0],
                dx_last=positions[1],endpoint_px=positions[1]-positions[0],correlations=correlations))
        values[name]=consistent_motion(observations,pinned=name=='burun');scores[name]=observations
    check_regions(values,-62)
    report=json.loads((folder/'print/print-report.json').read_text(encoding='utf-8'))
    if not report['raster_integrity']['sampled_pixels_verified']:raise ValueError('TIFF denetimi geçmedi.')
    if report['distinct_source_images']!=12:raise ValueError('12 farklı görüntü yok.')
    quality=json.loads((folder/'quality.json').read_text(encoding='utf-8'))
    if quality['max_nonopaque_fraction']>.0005:raise ValueError('Görünüşte boş alan var.')
    if digest(Path(state['assets'][ASSET]['original']))!=record['original_sha256']:raise ValueError('Orijinal değişti.')
    six=output/'6-Kanal-Raporlari'
    if six.exists():raise ValueError('6 kanal çıktısı zaten var; üzerine yazılmaz.')
    six_report=encode(views,six,job['print']|{'ne':6})
    files={'print/interlaced.tif':'Portre-50LPI-1200PPI-12Kanal-BOLGESEL.tif',
        'print/white-underbase.tif':'Portre-Beyaz-Maskesi.tif',
        'print/print-report.json':'12-Kanal-Baski-Raporu.json',
        'project.json':'Ayarlar.json','quality.json':'Kalite-Raporu.json',
        'render/look-around.png':'Hareket-Onizleme-Fiziksel-Onay-Degil.png'}
    hashes={}
    for src,name in files.items():
        dst=output/name
        if dst.exists():raise ValueError('Teslim dosyası zaten var.')
        shutil.copy2(folder/src,dst)
        hashes[name]=digest(dst)
        if hashes[name]!=digest(folder/src):raise ValueError('Kopya uyuşmuyor.')
    shutil.copy2(six/'interlaced.tif',output/'Portre-50LPI-1200PPI-6Kanal-BOLGESEL.tif')
    hashes['Portre-50LPI-1200PPI-6Kanal-BOLGESEL.tif']=digest(output/'Portre-50LPI-1200PPI-6Kanal-BOLGESEL.tif')
    if hashes['Portre-50LPI-1200PPI-6Kanal-BOLGESEL.tif']!=digest(six/'interlaced.tif'):
        raise ValueError('6 kanal teslim kopyası uyuşmuyor.')
    # Face-only A/B samples retain original coordinates/scale: never re-fit the crop.
    for ne,src in ((12,folder/'print/interlaced.tif'),(6,six/'interlaced.tif')):
        import tifffile
        raster=tifffile.memmap(src)
        start,stop=round(100*1200*130/25.4/1872),round(750*1200*130/25.4/1872)
        target=output/f'ONCE-YUZ-TESTI-{ne}Kanal.tif'
        with tifffile.TiffFile(src) as source:
            icc=source.pages[0].tags[34675].value
        tifffile.imwrite(target,np.array(raster[start:stop]),photometric='rgb',resolution=(1200,1200),
            resolutionunit='INCH',metadata=None,extratags=[(34675,'B',len(icc),icc,False)])
        saved=tifffile.memmap(target)
        for row in (0,(stop-start)//2,stop-start-1):
            if not np.array_equal(saved[row],raster[start+row]):
                raise ValueError('Küçük yüz testi kaynak TIFF ile uyuşmuyor.')
        with tifffile.TiffFile(target) as cropped:
            page=cropped.pages[0]
            if page.imagewidth!=raster.shape[1] or page.tags['XResolution'].value!=(1200,1):
                raise ValueError('Küçük test ölçeği/çözünürlüğü yanlış.')
        hashes[target.name]=digest(target)
    white=tifffile.memmap(folder/'print/white-underbase.tif')
    white_test=output/'Yuz-Testi-Beyaz-Maskesi.tif'
    tifffile.imwrite(white_test,np.array(white[start:stop]),photometric='minisblack',
        resolution=(1200,1200),resolutionunit='INCH',metadata=None)
    hashes[white_test.name]=digest(white_test)
    write(output/'Son-Denetim.json',dict(status='digital_regional_checks_passed_physical_pending',
        job_id=record['job_id'],endpoint_source_px=values,match_scores=scores,
        raster_12=report['raster_integrity'],raster_6=six_report['raster_integrity'],
        physical_3d_verified=False,original_preserved=True,thumb_endpoint_px=values['basparmak']))
    write(output/'Teslim-Hashleri.json',hashes)
    print(json.dumps(dict(status='delivered',output=str(output),measured_endpoint_px=values),ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('prepare','finish'))
    parser.add_argument('--output',type=Path);args=parser.parse_args()
    if args.stage=='prepare':prepare()
    else:finish(args.output)

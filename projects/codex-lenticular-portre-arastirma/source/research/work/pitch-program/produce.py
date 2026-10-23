"""Use the installed Studio pitch generator; only impose its unchanged pixels."""
from pathlib import Path
from decimal import Decimal
import sys, json, hashlib, gc
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import tifffile

ROOT=Path(__file__).resolve().parents[2]
APP=Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1')
sys.path.insert(0,str(APP))
import lenticular.printing as engine
assert Path(engine.__file__).resolve()==APP/'lenticular'/'printing.py'
WIDE='--22cm' in sys.argv
FIELD=220 if WIDE else 130
PAGE_W,PAGE_H=(260,195) if WIDE else (170,215.139)
BAND_H,ROW_PITCH=(2.7,3.2) if WIDE else (3.2,3.8)
OUT=ROOT/'output'/('PROGRAM-PITCH-22CM' if WIDE else 'pdf/PROGRAM-PITCH-50-60-75-85-100')
OUT.mkdir(parents=True,exist_ok=True)
RAW=Path(__file__).parent/('native-22cm' if WIDE else 'native')
RAW.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protected=[APP/'lenticular'/'printing.py',APP/'.studio'/'state.json',ROOT/'fullscene-current.json',Path(r'C:\Users\USER\Downloads\vd-gigapixel-recover v2-2x-faceai v2.jpg')]
before={str(p):sha(p) for p in protected}
original=json.loads((ROOT/'fullscene-current.json').read_text(encoding='utf-8'))['printing']
assert original['width_mm']==130 and original['height_mm']==215.139 and original['ppi']==1200
assert original['axis']=='vertical' and not original['mirror']
PPI=original['ppi']; px=lambda v:round(v*PPI/25.4)
Image.MAX_IMAGE_PIXELS=160_000_000
page_size=(px(PAGE_W),px(PAGE_H))
font=lambda v,b=False:ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf' if b else 'C:/Windows/Fonts/arial.ttf',px(v))
manifest={'engine':str(Path(engine.__file__).resolve()),'engine_sha256':before[str(APP/'lenticular'/'printing.py')],'runtime':sys.executable,'method':'Studio printing.pitch_test called with validated 21-candidate settings for each half; 41 unique native bands copied without resizing or resampling into each single-sheet target.','ppi':PPI,'page_pixels':page_size,'page_mm':[v/PPI*25.4 for v in page_size],'pattern_width_mm':px(FIELD)/PPI*25.4,'step':'0.05','count_per_lens':41,'tests':[]}
for nominal in (50,60,75,85,100):
    print(f'PROGRAM_GENERATING {nominal} LPI',flush=True)
    values=[Decimal(nominal)-1+Decimal('.05')*i for i in range(41)]
    bands={}; native=[]; profile=None
    for part,offset in [('ALT',-.5),('UST',.5)]:
        folder=RAW/f'{nominal}LPI-{part}'
        folder.mkdir(exist_ok=True)
        settings=engine.validate(original|{'width_mm':FIELD,'nominal_lpi':nominal,'effective_lpi':nominal+offset,'pitch_step':.05,'pitch_candidates':21,'ne':2})
        target=folder/'pitch-test.tif'
        meta_file=folder/'pitch-test.json'
        expected_values=(settings['effective_lpi']+(np.arange(21)-10)*.05).tolist()
        # Reuse this run's native output only when its full candidate list matches;
        # every copied pixel is independently checked below.
        if not (target.is_file() and meta_file.is_file() and json.loads(meta_file.read_text(encoding='utf-8'))['candidate_lpi']==expected_values):
            engine.pitch_test(folder,settings,include_response=False)
        native.append({'file':str(target),'sha256':sha(target),'settings':settings})
        metadata=json.loads((folder/'pitch-test.json').read_text(encoding='utf-8'))
        with Image.open(target) as im:
            assert im.n_frames==1 and im.mode=='RGB'
            assert all(abs(v-PPI)<.001 for v in im.info['dpi'])
            profile=im.info['icc_profile']
            assert im.size==(px(FIELD)+px(22),px(13)+21*px(10))
            for i,value in enumerate(metadata['candidate_lpi']):
                key=f'{value:.2f}'
                y=px(13)+i*px(10)
                band=im.crop((px(22),y,px(22)+px(FIELD),y+px(BAND_H)))
                a=np.asarray(band)
                assert np.array_equal(a,np.broadcast_to(a[:1],a.shape))
                expected=(np.floor((np.arange(px(FIELD))+.5)*float(value)/PPI*2).astype(np.int64)%2*255).astype(np.uint8)
                assert np.array_equal(a[0,:,0],expected)
                assert np.array_equal(a[:,:,0],a[:,:,1]) and np.array_equal(a[:,:,0],a[:,:,2])
                if key in bands: assert band.tobytes()==bands[key].tobytes()
                bands[key]=band
        gc.collect()
    assert sorted(bands,key=Decimal)==[f'{v:.2f}' for v in values]
    page=Image.new('RGB',page_size,'white'); d=ImageDraw.Draw(page)
    def text(x,y,s,size=2.4,b=False,center=False):
        f=font(size,b); anchor='mt' if center else 'lt'
        box=d.textbbox((px(x),px(y)),s,font=f,anchor=anchor)
        assert box[0]>=px(3) and box[2]<=page.width-px(3) and box[3]<page.height-px(2),(s,box)
        d.text((px(x),px(y)),s,font=f,fill='black',anchor=anchor)
    def line(x,y,xx,yy,w=.15):d.line((px(x),px(y),px(xx),px(yy)),fill='black',width=max(1,px(w)))
    text(6,5,f'{nominal} LPI - PITCH TESTİ',3.8,True)
    text(6,11,f'{values[0]:.2f}-{values[-1]:.2f} LPI | 0.05 adım | 41 şerit',2.8,True)
    text(6,16,'Lenticular Studio üretimi | 1200 PPI | Tek sayfa',2.4)
    text(6,21,'%100 / Gerçek boyut - Sayfaya sığdırma KAPALI',2.5,True)
    text(6,26,f'Dosya: {PAGE_W/10:g} × {PAGE_H/10:.2f} cm | Çizgili test alanı: {FIELD/10:g} cm',2.3)
    text(10,31,'LPI',2.1,True,True)
    text(PAGE_W/2,31,'LENS ÇİZGİLERİ DİKEY OLMALI',2.1,True,True)
    text(PAGE_W-10,31,'LPI',2.1,True,True)
    line(20,34,20+FIELD,34,.2)
    checks=[]
    for i,value in enumerate(values):
        label=f'{value:.2f}'; top=36+i*ROW_PITCH
        band=bands[label]
        dest=(px(20),px(top))
        page.paste(band,dest)
        assert page.crop((dest[0],dest[1],dest[0]+band.width,dest[1]+band.height)).tobytes()==band.tobytes()
        text(10,top+.3,label,2.6,True,True)
        text(PAGE_W-10,top+.3,label,2.6,True,True)
        a=np.asarray(band)[0,:,0]
        edges=np.flatnonzero(a[1:]!=a[:-1])+1
        slope=np.polyfit(np.arange(len(edges)),edges,1)[0]
        measured=PPI/(2*slope)
        # At most one raster pixel of edge quantization, with no cumulative drift.
        residual=edges-(np.arange(1,len(edges)+1)*PPI/(2*float(value))-.5)
        assert np.all(residual>=-1e-6) and np.all(residual<=1+1e-6)
        # Regression is diagnostic only. Exact pixel equality and the bounded
        # edge error above verify the raster without a biased frequency fit.
        checks.append({'lpi':label,'native_band_sha256':hashlib.sha256(band.tobytes()).hexdigest(),'box_px':[dest[0],dest[1],dest[0]+band.width,dest[1]+band.height],'measured_lpi':round(measured,6)})
    foot=172 if WIDE else 193
    text(6,foot,'Lensi baskıya temas ettir; oluklu yüz gözlemciye baksın.',2.1)
    text(6,foot+4,'Aynı üretim / RIP ayarlarını ve izleme mesafesini kullan.',2.1)
    # A ruler in the view-selection axis. Vertical ruler is placed in the right margin.
    rule=183 if WIDE else 204
    line(20,rule,120,rule,.18)
    for n in range(11):
        line(20+10*n,rule-1,20+10*n,rule+1,.15)
    text(20,rule+3,'Uç çizgiler arası tam 100 mm olmalı.',2.2,True)
    xx=PAGE_W-3
    line(xx,65,xx,165,.15);line(xx-1,65,xx+1,65,.15);line(xx-1,165,xx+1,165,.15)
    text(123,rule,'Dikey: 100 mm',2.0)
    stem=f'PITCH-{nominal}LPI-{values[0]:.2f}-{values[-1]:.2f}'+('-22CM' if WIDE else '')+'-1200PPI'
    tif=OUT/(stem+'.tif')
    reuse=False
    if tif.is_file():
        with Image.open(tif) as old:
            reuse=old.size==page.size and hashlib.sha256(old.tobytes()).digest()==hashlib.sha256(page.tobytes()).digest()
    if not reuse:
        page.save(tif,dpi=(PPI,PPI),icc_profile=profile,compression='tiff_lzw')
    with Image.open(tif) as reread:
        assert reread.n_frames==1 and reread.size==page_size
        assert all(abs(v-PPI)<.001 for v in reread.info['dpi'])
        assert reread.info['icc_profile']==profile
        for row in checks:
            assert hashlib.sha256(reread.crop(row['box_px']).tobytes()).hexdigest()==row['native_band_sha256']
    thumb=page.copy();thumb.thumbnail((900,1200),Image.Resampling.LANCZOS)
    thumb.save(Path(__file__).parent/(f'preview-{nominal}'+('-22cm.png' if WIDE else '.png')))
    manifest['tests'].append({'nominal_lpi':nominal,'range':[str(values[0]),str(values[-1])],'tiff':str(tif),'native':native,'rows':checks,'tiff_sha256':sha(tif)})
    del page,bands,thumb
    gc.collect()
    print(f'VERIFIED {nominal} LPI - 41 native bands unchanged',flush=True)
assert before=={str(p):sha(p) for p in protected}
manifest['protected_files_unchanged']=True
manifest['physical_pitch_selected']=False
(Path(__file__).parent/('verification-22cm.json' if WIDE else 'verification.json')).write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
print('ALL_FIVE_PROGRAM_TARGETS_VERIFIED',flush=True)

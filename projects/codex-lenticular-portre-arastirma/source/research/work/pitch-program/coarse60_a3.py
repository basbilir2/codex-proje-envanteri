"""Studio-generated 59-63 coarse pitch test, with tall bands and lens guides."""
from pathlib import Path
from decimal import Decimal
import sys,json,hashlib,gc,zlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import tifffile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
APP=Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1')
sys.path.insert(0,str(APP))
import lenticular.printing as engine
assert Path(engine.__file__).resolve()==APP/'lenticular'/'printing.py'
OUT=ROOT/'output'/'60LPI-GENIS-TEST-59-63'
OUT.mkdir(parents=True,exist_ok=True)
RAW=HERE/'native-60-coarse-59-63'
RAW.mkdir(exist_ok=True)
PPI=1200;px=lambda v:round(v*PPI/25.4)
W,H=px(297),px(420)
FIELD=px(220);BAND=px(8)
Image.MAX_IMAGE_PIXELS=350_000_000
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protected=[APP/'lenticular'/'printing.py',APP/'.studio'/'state.json',ROOT/'fullscene-current.json']
before={str(p):sha(p) for p in protected}
original=json.loads((ROOT/'fullscene-current.json').read_text(encoding='utf-8'))['printing']
assert original['ppi']==1200 and original['axis']=='vertical' and not original['mirror']
values=[Decimal('59.00')+Decimal('.10')*i for i in range(41)]
bands={};native=[];profile=None
for center in (60,62):
    folder=RAW/f'center-{center}'
    folder.mkdir(exist_ok=True)
    settings=engine.validate(original|{'width_mm':220,'nominal_lpi':60,'effective_lpi':center,'pitch_step':.1,'pitch_candidates':21,'ne':2})
    engine.pitch_test(folder,settings,include_response=False)
    target=folder/'pitch-test.tif'
    metadata=json.loads((folder/'pitch-test.json').read_text(encoding='utf-8'))
    native.append({'path':str(target),'sha256':sha(target),'settings':settings})
    with Image.open(target) as im:
        assert im.n_frames==1 and im.mode=='RGB'
        assert all(abs(v-PPI)<.001 for v in im.info['dpi'])
        profile=im.info['icc_profile']
        assert im.size==(FIELD+px(22),px(13)+21*px(10))
        for i,value in enumerate(metadata['candidate_lpi']):
            label=f'{value:.2f}'
            y=px(13)+i*px(10)
            band=im.crop((px(22),y,px(22)+FIELD,y+BAND))
            data=np.asarray(band)
            # Full native band is constant vertically; copy without resampling.
            assert np.array_equal(data,np.broadcast_to(data[:1],data.shape))
            expected=(np.floor((np.arange(FIELD)+.5)*float(value)/PPI*2).astype(np.int64)%2*255).astype(np.uint8)
            assert np.array_equal(data[0,:,0],expected)
            assert np.array_equal(data[:,:,0],data[:,:,1]) and np.array_equal(data[:,:,0],data[:,:,2])
            if label in bands:assert band.tobytes()==bands[label].tobytes()
            bands[label]=band
    print(f'STUDIO_NATIVE_VERIFIED {center-1:.2f}-{center+1:.2f}',flush=True)
    gc.collect()
assert sorted(bands,key=Decimal)==[f'{v:.2f}' for v in values]

# Small independent label/guide layer; calibration stripes are copied later.
layout=Image.new('RGB',(W,H),'white')
d=ImageDraw.Draw(layout)
font=lambda mm,b=False:ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf' if b else 'C:/Windows/Fonts/arial.ttf',px(mm))
def text(x,y,s,size=2.7,b=False,center=False):
    f=font(size,b);anchor='mt' if center else 'lt'
    box=d.textbbox((px(x),px(y)),s,font=f,anchor=anchor)
    assert box[0]>=px(5) and box[2]<=W-px(5) and box[3]<=H-px(3),(s,box)
    d.text((px(x),px(y)),s,font=f,fill='black',anchor=anchor)
def line(x,y,xx,yy,width=.25):
    d.line((px(x),px(y),px(xx),px(yy)),fill='black',width=max(1,px(width)))
text(12,7,'60 LPI - GENİŞ ARALIK PITCH TESTİ',4.1,True)
text(12,14,'59.00-63.00 LPI | 0.10 adım | 41 etiketli bant',3.0,True)
text(12,20,'A3 dikey | 1200 PPI | Çizgili en: 22 cm | Bant yüksekliği: 8 mm',2.7)
text(12,26,'%100 / GERÇEK BOYUT - Sayfaya sığdırma ve yeniden örnekleme KAPALI',2.65,True)
text(17,34,'LPI',2.5,True,True)
text(150,34,'LENS OLUKLARI DİKEY - ÜST VE SOL ÇİZGİYE HİZALA',2.5,True,True)
text(275,34,'LPI',2.5,True,True)
# Clear, continuous L-shaped top/left reference, with an unobstructed white gap.
line(37,40,263,40,.4)
line(37,40,37,388,.4)
# Short perpendicular corner extensions make the reference edges easy to find.
line(34,40,37,40,.4)
line(37,37,37,40,.4)
rows=[]
for i,value in enumerate(values):
    top=43+i*8.4
    x,y=px(40),px(top)
    label=f'{value:.2f}'
    band=bands[label]
    layout.paste(band,(x,y))
    text(17,top+2,label,3.2,True,True)
    text(275,top+2,label,3.2,True,True)
    rows.append({'lpi':label,'box_px':[x,y,x+FIELD,y+BAND],'native_sha256':hashlib.sha256(band.tobytes()).hexdigest()})
text(12,392,'Önce en eşit değişen bandı bul. Detay testi, seçtiğin değerin çevresinde hazırlanacak.',2.65)
line(40,402,140,402,.2)
for i in range(11):line(40+i*10,401,40+i*10,403,.2)
text(40,405,'Bu çizginin iki ucu arası 100 mm olmalı.',2.5,True)
text(165,401,'Sonuç: __________ LPI',3.1,True)
text(12,412,'Lensi baskıya temas ettir. Aynı üretim ayarlarıyla ve gerçek izleme mesafesinden bak.',2.5)
target=OUT/'A3-60LPI-59.00-63.00-ADIM0.10-22CM-UZUN-BANT-1200PPI.tif'
array=np.asarray(layout)
def strips():
    for y in range(0,H,128):yield zlib.compress(array[y:min(y+128,H)].tobytes(),6)
with tifffile.TiffWriter(target) as writer:
    writer.write(data=strips(),shape=(H,W,3),dtype=np.uint8,photometric='rgb',compression='deflate',rowsperstrip=128,
        resolution=(PPI,PPI),resolutionunit='INCH',metadata=None,extratags=[(34675,'B',len(profile),profile,False)])
del array
with tifffile.TiffFile(target) as tif:
    assert len(tif.pages)==1
    page=tif.pages[0]
    assert page.shape==(H,W,3)
    assert page.tags['XResolution'].value==(PPI,1) and page.tags['YResolution'].value==(PPI,1)
    assert page.tags['ResolutionUnit'].value==2 and page.tags[34675].value==profile
    decoded=page.asarray(out='memmap')
    for row in rows:
        x0,y0,x1,y1=row['box_px']
        assert abs((x1-x0)/PPI*25.4-220)<.02
        assert abs((y1-y0)/PPI*25.4-8)<.02
        assert hashlib.sha256(decoded[y0:y1,x0:x1].tobytes()).hexdigest()==row['native_sha256']
    # Verify continuous reference edges and the 100 mm ruler in the saved file.
    assert np.all(decoded[px(40):px(388),px(37)]==0)
    assert np.all(decoded[px(40),px(37):px(263)]==0)
    assert np.all(decoded[px(402),px(40):px(140)]==0)
    del decoded
# Antialiased preview for layout review; never used to generate the TIFF.
preview=layout.resize((1052,1488),Image.Resampling.LANCZOS)
preview.save(HERE/'coarse60-A3-preview.png')
assert before=={str(p):sha(p) for p in protected}
report={'file':str(target),'size_mm':[W/PPI*25.4,H/PPI*25.4],'ppi':PPI,'range':['59.00','63.00'],
    'step':'0.10','count':41,'pattern_width_mm':FIELD/PPI*25.4,'band_height_mm':BAND/PPI*25.4,
    'engine':str(Path(engine.__file__).resolve()),'engine_sha256':before[str(APP/'lenticular'/'printing.py')],
    'native':native,'all_41_bands_pixel_equal':True,'top_and_side_guides_verified':True,'protected_files_unchanged':True,
    'physical_pitch_selected':False,'sha256':sha(target),'rows':rows}
(HERE/'coarse60-A3-verification.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['file','count','pattern_width_mm','band_height_mm','all_41_bands_pixel_equal','top_and_side_guides_verified']},ensure_ascii=False),flush=True)

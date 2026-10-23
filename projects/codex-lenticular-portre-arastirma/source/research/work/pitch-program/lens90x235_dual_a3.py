"""Two Studio-generated pitch tests with an explicit physical lens width."""
from pathlib import Path
import sys,json,hashlib,zlib,gc
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import tifffile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
APP=Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1')
sys.path.insert(0,str(APP))
import lenticular.printing as engine
assert Path(engine.__file__).resolve()==APP/'lenticular'/'printing.py'
PPI=1200;px=lambda mm:round(mm*PPI/25.4)
W,H=px(420),px(297)
LENS_W=190 if '--19cm' in sys.argv else 90
FW,FH=px(LENS_W),px(235)
ROW_H,HEADER_H=px(10),px(13)
NATIVE_BH=ROW_H-px(1)
BH=px(10.5)
BAND_PITCH=px(11)
Image.MAX_IMAGE_PIXELS=350_000_000
original=json.loads((ROOT/'fullscene-current.json').read_text(encoding='utf-8'))['printing']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protected=[Path(engine.__file__),APP/'.studio'/'state.json',ROOT/'fullscene-current.json']
before={str(p):sha(p) for p in protected}
RAW=HERE/f'native-lens{LENS_W}x235'
RAW.mkdir(exist_ok=True)
OUT=ROOT/'output'/f'A3-60-50LPI-LENS-{LENS_W//10}x23.5'
OUT.mkdir(parents=True,exist_ok=True)
target=OUT/f'A3-60LPI-59-61-50LPI-49-51-LENS{LENS_W//10}x23.5-1200PPI.tif'
layout=Image.new('L',(W,H),255)
d=ImageDraw.Draw(layout)
font=lambda mm,b=False:ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf' if b else 'C:/Windows/Fonts/arial.ttf',px(mm))
def text(x,y,s,size=2.8,b=False,center=False):
    f=font(size,b);anchor='mt' if center else 'lt'
    bounds=d.textbbox((px(x),px(y)),s,font=f,anchor=anchor)
    assert bounds[0]>=px(5) and bounds[2]<=W-px(5) and bounds[3]<H-px(3),(s,bounds)
    d.text((px(x),px(y)),s,font=f,anchor=anchor,fill=0)
def line(x,y,xx,yy,width=.25):d.line((px(x),px(y),px(xx),px(yy)),fill=0,width=max(1,px(width)))
text(210,5,f'LENS ENİ {LENS_W//10} cm × DİKEY BOYU 23,5 cm - İKİ PITCH TESTİ',4,True,True)
text(210,13,'Tek A3 yatay | 1200 PPI | %100 / GERÇEK BOYUT | Her test: 0.10 adım, 21 bant',2.8,True,True)
rows=[];panels=[];profile=None
positions=((60,18),(50,224)) if LENS_W==190 else ((60,90),(50,240))
for nominal,frame_x in positions:
    text(frame_x+LENS_W/2,23,f'{nominal} LPI | {nominal-1:.2f}-{nominal+1:.2f}',3.4,True,True)
    settings=engine.validate(original|{'width_mm':LENS_W,'height_mm':235,'nominal_lpi':nominal,'effective_lpi':nominal,
        'ppi':PPI,'axis':'vertical','phase':0,'tilt_deg':0,'mirror':False,'pitch_step':.1,'pitch_candidates':21,'ne':2})
    folder=RAW/f'{nominal}LPI'
    folder.mkdir(exist_ok=True)
    source=folder/'pitch-test.tif'
    meta_file=folder/'pitch-test.json'
    expected_values=(nominal+(np.arange(21)-10)*.1).tolist()
    if not (source.is_file() and meta_file.is_file() and json.loads(meta_file.read_text(encoding='utf-8'))['candidate_lpi']==expected_values):
        engine.pitch_test(folder,settings,include_response=False)
    meta=json.loads((folder/'pitch-test.json').read_text(encoding='utf-8'))
    values=meta['candidate_lpi']
    assert len(values)==21 and values[0]==nominal-1 and values[-1]==nominal+1
    assert all(abs(b-a-.1)<1e-8 for a,b in zip(values,values[1:]))
    x0,y0=px(frame_x),px(34)
    x1,y1=x0+FW,y0+FH
    # The clear inside of the border is exactly the physical lens size.
    # Draw the border outside that area so no calibration pixels are covered.
    stroke=px(.35)
    d.rectangle((x0-stroke,y0-stroke,x0-1,y1+stroke-1),fill=0)
    d.rectangle((x1,y0-stroke,x1+stroke-1,y1+stroke-1),fill=0)
    d.rectangle((x0,y0-stroke,x1-1,y0-1),fill=0)
    d.rectangle((x0,y1,x1-1,y1+stroke-1),fill=0)
    text(frame_x+LENS_W/2,29.5,f'{LENS_W//10} cm en - lens çizgileri dikey',2.3,True,True)
    with Image.open(source) as im:
        assert im.n_frames==1 and im.mode=='RGB'
        assert im.size==(FW+px(22),HEADER_H+21*ROW_H)
        assert all(abs(v-PPI)<.001 for v in im.info['dpi'])
        icc=im.info['icc_profile']
        if profile is not None:assert icc[:24]+icc[36:]==profile[:24]+profile[36:]
        profile=icc
        for i,value in enumerate(values):
            sy=HEADER_H+i*ROW_H
            native_band=im.crop((px(22),sy,px(22)+FW,sy+NATIVE_BH))
            band=native_band
            a=np.asarray(band)
            expected=(np.floor((np.arange(FW)+.5)*value/PPI*2).astype(np.int64)%2*255).astype(np.uint8)
            assert np.array_equal(a,np.broadcast_to(a[:1],a.shape))
            assert np.array_equal(a[0,:,0],expected)
            assert np.array_equal(a[:,:,0],a[:,:,1]) and np.array_equal(a[:,:,0],a[:,:,2])
            native_hash=hashlib.sha256(native_band.tobytes()).hexdigest()
            # Extend only the constant vertical run; preserve the exact native
            # horizontal samples. No horizontal scale, interpolation or blur.
            band=Image.fromarray(np.broadcast_to(a[:1],(BH,FW,3)).copy())
            block_height=20*BAND_PITCH+BH
            y=y0+(FH-block_height)//2+i*BAND_PITCH
            assert y>y0 and y+BH<y1
            layout.paste(band.convert('L'),(x0,y))
            # The 19 cm layout labels each band on its left, outside the lens.
            # Two full-width lens frames plus labels fit within the A3 width.
            if LENS_W==190:
                text(frame_x-8,y/PPI*25.4+2.4,f'{value:.2f}',2.6,True,True)
            else:
                text(frame_x-16,y/PPI*25.4+2.4,f'{value:.2f}',3.2,True,True)
                text(frame_x+106,y/PPI*25.4+2.4,f'{value:.2f}',3.2,True,True)
            rows.append({'nominal_lpi':nominal,'lpi':f'{value:.2f}','box_px':[x0,y,x1,y+BH],
                'native_rgb_sha256':native_hash,'printed_rgb_sha256':hashlib.sha256(band.tobytes()).hexdigest()})
    panels.append({'nominal_lpi':nominal,'lens_box_px':[x0,y0,x1,y1],
        'range':[nominal-1,nominal+1],'native_file':str(source),'native_sha256':sha(source)})
    print(f'STUDIO_VERIFIED {nominal} LPI: {nominal-1}-{nominal+1}, lens width {LENS_W} mm / height 235 mm',flush=True)
    gc.collect()
text(210,275,f'Lensi çerçevenin içine hizala: {LENS_W//10} cm YATAY, 23,5 cm DİKEY. Sayfaya sığdırma KAPALI.',2.8,True,True)
line(160,285,260,285,.2);line(160,283.5,160,286.5,.2);line(260,283.5,260,286.5,.2)
text(210,289,'Kontrol çizgisinin iki ucu arası baskıda tam 100 mm olmalı.',2.5,False,True)
text(15,281,'60 LPI sonucu: __________',2.8,True)
text(310,281,'50 LPI sonucu: __________',2.8,True)
def strips():
    for top in range(0,H,128):
        tile=layout.crop((0,top,W,min(top+128,H))).convert('RGB')
        yield zlib.compress(tile.tobytes(),6)
with tifffile.TiffWriter(target) as writer:
    writer.write(data=strips(),shape=(H,W,3),dtype=np.uint8,photometric='rgb',compression='deflate',rowsperstrip=128,
        resolution=(PPI,PPI),resolutionunit='INCH',metadata=None,extratags=[(34675,'B',len(profile),profile,False)])
with tifffile.TiffFile(target) as tif:
    assert len(tif.pages)==1
    page=tif.pages[0]
    assert page.shape==(H,W,3) and page.tags['ResolutionUnit'].value==2
    assert page.tags['XResolution'].value==(PPI,1) and page.tags['YResolution'].value==(PPI,1)
    assert page.tags[34675].value==profile
    saved=page.asarray(out='memmap')
    for row in rows:
        x0,y0,x1,y1=row['box_px']
        assert abs((x1-x0)/PPI*25.4-LENS_W)<.02
        assert abs((y1-y0)/PPI*25.4-10.5)<.02
        assert hashlib.sha256(saved[y0:y0+NATIVE_BH,x0:x1].tobytes()).hexdigest()==row['native_rgb_sha256']
        assert hashlib.sha256(saved[y0:y1,x0:x1].tobytes()).hexdigest()==row['printed_rgb_sha256']
        region=saved[y0:y1,x0:x1]
        assert np.array_equal(region,np.broadcast_to(region[:1],region.shape))
    for panel in panels:
        x0,y0,x1,y1=panel['lens_box_px']
        assert abs((x1-x0)/PPI*25.4-LENS_W)<.02 and abs((y1-y0)/PPI*25.4-235)<.02
        assert np.all(saved[y0:y1,x0-1]==0) and np.all(saved[y0-1,x0:x1]==0)
    assert np.all(saved[px(285),px(160):px(260)]==0)
    del saved
assert len(rows)==42
assert before=={str(p):sha(p) for p in protected}
layout.resize((1488,1052),Image.Resampling.LANCZOS).save(HERE/f'lens{LENS_W}x235-dual-A3-preview.png')
report={'file':str(target),'page_mm':[W/PPI*25.4,H/PPI*25.4],'ppi':PPI,
    'lens_width_mm':LENS_W,'lens_vertical_height_mm':235,'pattern_width_mm':FW/PPI*25.4,
    'band_height_mm':BH/PPI*25.4,'step':'0.10','candidates_per_test':21,
    'all_42_native_horizontal_patterns_identical':True,'vertical_extension_only':True,'lens_frames_verified':True,'protected_files_unchanged':True,
    'engine':str(Path(engine.__file__).resolve()),'engine_sha256':before[str(Path(engine.__file__))],
    'panels':panels,'rows':rows,'sha256':sha(target)}
(HERE/f'lens{LENS_W}x235-dual-A3-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['file','lens_width_mm','lens_vertical_height_mm','band_height_mm','all_42_native_horizontal_patterns_identical','lens_frames_verified']},ensure_ascii=False),flush=True)

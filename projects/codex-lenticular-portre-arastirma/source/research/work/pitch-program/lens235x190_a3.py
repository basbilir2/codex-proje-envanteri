"""Fit the unchanged Studio calibration bands to the supplied physical lens."""
from pathlib import Path
import json,hashlib,zlib,gc,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import tifffile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
nominal=50 if '--50lpi' in sys.argv else 60
bounds=(49,50,51) if nominal==50 else (59,61,63)
step='0.05' if nominal==50 else '0.10'
if nominal==50:
    bundle=json.loads((HERE/'verification-22cm.json').read_text(encoding='utf-8'))
    test=next(t for t in bundle['tests'] if t['nominal_lpi']==50)
    old={'engine':bundle['engine'],'engine_sha256':bundle['engine_sha256'],
        'native':[{'path':n['file'],'sha256':n['sha256']} for n in test['native']]}
else:
    old=json.loads((HERE/'coarse60-A3-verification.json').read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(old['engine'])==old['engine_sha256']
PPI=1200;px=lambda mm:round(mm*PPI/25.4)
W,H=px(297),px(420)
Image.MAX_IMAGE_PIXELS=350_000_000
layout=Image.new('L',(W,H),255)
d=ImageDraw.Draw(layout)
font=lambda mm,b=False:ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf' if b else 'C:/Windows/Fonts/arial.ttf',px(mm))
def text(x,y,s,size=2.5,b=False,center=False):
    f=font(size,b);anchor='mt' if center else 'lt'
    bounds=d.textbbox((px(x),px(y)),s,font=f,anchor=anchor)
    assert bounds[0]>=px(5) and bounds[2]<=W-px(5) and bounds[3]<H-px(3),(s,bounds)
    d.text((px(x),px(y)),s,font=f,anchor=anchor,fill=0)
def line(x,y,xx,yy,width=.25):
    d.line((px(x),px(y),px(xx),px(yy)),fill=0,width=max(1,px(width)))
text(11,5,f'{nominal} LPI - LENSE UYGUN PITCH TESTİ',3.5,True)
text(11,12,f'Lens: 23,5 × 19 cm | {bounds[0]:.2f}-{bounds[-1]:.2f} | {step} adım',2.5,True)
text(177,12,'Uç çizgiler arası 100 mm',2.3)
line(177,18,277,18,.2);line(177,17,177,19,.2);line(277,17,277,19,.2)
rows=[];frames=[];profile=None
for panel,(native,fy) in enumerate(zip(old['native'],(22,220)),1):
    assert sha(native['path'])==native['sha256']
    source=Path(native['path'])
    meta=json.loads((source.parent/'pitch-test.json').read_text(encoding='utf-8'))
    values=meta['candidate_lpi']
    assert len(values)==21 and abs(values[0]-bounds[panel-1])<1e-8 and abs(values[-1]-bounds[panel])<1e-8
    assert all(abs((b-a)-float(step))<1e-8 for a,b in zip(values,values[1:]))
    # Each rectangle is exactly the lens footprint; labels remain outside it.
    fx=31;fw=235;fh=190;field_x=fx+(fw-220)/2
    frame=[px(fx),px(fy),px(fx+fw),px(fy+fh)]
    assert abs((frame[2]-frame[0])/PPI*25.4-fw)<.02
    assert abs((frame[3]-frame[1])/PPI*25.4-fh)<.02
    line(fx,fy,fx+fw,fy,.35);line(fx,fy,fx,fy+fh,.35)
    line(fx+fw,fy,fx+fw,fy+fh,.2);line(fx,fy+fh,fx+fw,fy+fh,.2)
    text(148.5,fy+2,f'{panel} / {values[0]:.2f}-{values[-1]:.2f} LPI | Lensi bu çerçeveye hizala; oluklar dikey',2.3,True,True)
    frames.append(frame)
    with Image.open(source) as im:
        assert im.mode=='RGB' and im.n_frames==1
        assert all(abs(v-PPI)<.001 for v in im.info['dpi'])
        this_profile=im.info['icc_profile']
        if profile is not None:assert profile[:24]+profile[36:]==this_profile[:24]+this_profile[36:]
        profile=this_profile
        for i,value in enumerate(values):
            sy=px(13)+i*px(10)
            band=im.crop((px(22),sy,px(22)+px(220),sy+px(8)))
            a=np.asarray(band)
            assert np.array_equal(a,np.broadcast_to(a[:1],a.shape))
            assert np.array_equal(a[:,:,0],a[:,:,1]) and np.array_equal(a[:,:,0],a[:,:,2])
            expected=(np.floor((np.arange(px(220))+.5)*value/PPI*2).astype(np.int64)%2*255).astype(np.uint8)
            assert np.array_equal(a[0,:,0],expected)
            top=fy+10+i*8.4
            x,y=px(field_x),px(top)
            assert x>frame[0] and y>frame[1] and x+band.width<frame[2] and y+band.height<frame[3]
            layout.paste(band.convert('L'),(x,y))
            text(17,top+2,f'{value:.2f}',3.2,True,True)
            text(279,top+2,f'{value:.2f}',3.2,True,True)
            rows.append({'panel':panel,'lpi':f'{value:.2f}','box_px':[x,y,x+band.width,y+band.height],
                'native_rgb_sha256':hashlib.sha256(band.tobytes()).hexdigest()})
    print(f'PANEL_VERIFIED {panel}: {values[0]:.2f}-{values[-1]:.2f}, lens footprint 235x190 mm',flush=True)
    gc.collect()
text(148.5,214,f'{bounds[1]:.2f} iki bölümde ortak referanstır. Lensi üst bölümden alt bölüme aynı yönde taşı.',2.4,True,True)
text(11,413,'%100 / Gerçek boyut. Çizgili en 22 cm; bantlar 8 mm. Sonuç: __________ LPI',2.65,True)
OUT=ROOT/'output'/f'{nominal}LPI-LENS-23.5x19-A3'
OUT.mkdir(parents=True,exist_ok=True)
target=OUT/f'A3-{nominal}LPI-{bounds[0]}-{bounds[-1]}-LENS23.5x19-22CM-1200PPI.tif'
def strips():
    for y in range(0,H,128):
        strip=layout.crop((0,y,W,min(y+128,H))).convert('RGB')
        yield zlib.compress(strip.tobytes(),6)
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
        assert hashlib.sha256(saved[y0:y1,x0:x1].tobytes()).hexdigest()==row['native_rgb_sha256']
        assert abs((x1-x0)/PPI*25.4-220)<.02
        assert abs((y1-y0)/PPI*25.4-8)<.02
    for x0,y0,x1,y1 in frames:
        assert np.all(saved[y0,x0:x1]==0) and np.all(saved[y0:y1,x0]==0)
    del saved
assert len(rows)==42 and len({r['lpi'] for r in rows})==41
layout.resize((1052,1488),Image.Resampling.LANCZOS).save(HERE/f'lens235x190-A3-{nominal}LPI-preview.png')
report={'file':str(target),'ppi':PPI,'page_mm':[W/PPI*25.4,H/PPI*25.4],
    'lens_width_mm':235,'lens_height_mm':190,'orientation_assumed':'235 mm horizontal, 190 mm vertical, vertical grooves',
    'pattern_width_mm':px(220)/PPI*25.4,'band_height_mm':px(8)/PPI*25.4,
    'panels':[[f'{bounds[0]:.2f}',f'{bounds[1]:.2f}'],[f'{bounds[1]:.2f}',f'{bounds[2]:.2f}']],'step':step,'unique_lpi_count':41,'band_count':42,
    'all_native_pixels_equal':True,'both_lens_reference_frames_verified':True,'sha256':sha(target),'rows':rows}
(HERE/f'lens235x190-A3-{nominal}LPI-verification.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['file','unique_lpi_count','all_native_pixels_equal','both_lens_reference_frames_verified']},ensure_ascii=False),flush=True)

"""Lossless A3 imposition of the verified Studio-generated TIFF targets."""
from pathlib import Path
import hashlib,json,gc,sys,zlib
import numpy as np
import tifffile
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
WIDE='--22cm' in sys.argv
FIELD=220 if WIDE else 130
manifest=json.loads((HERE/('verification-22cm.json' if WIDE else 'verification.json')).read_text(encoding='utf-8'))
OUT=ROOT/'output'/('A3-PITCH-22CM' if WIDE else 'A3-PITCH-13CM')
OUT.mkdir(parents=True,exist_ok=True)
PPI=1200
px=lambda mm:round(mm*PPI/25.4)
W,H=(px(297),px(420)) if WIDE else (px(420),px(297))
CARD_W,CARD_H=manifest['page_pixels']
GAP=px(10)
Y=(H-CARD_H)//2
Image.MAX_IMAGE_PIXELS=350_000_000
tests={t['nominal_lpi']:t for t in manifest['tests']}
checks=[]
for page_number,group in enumerate([(50,60),(75,85),(100,)],1):
    width=CARD_W if WIDE else len(group)*CARD_W+(len(group)-1)*GAP
    left=(W-width)//2
    row_y=(H-(len(group)*CARD_H+(len(group)-1)*GAP))//2 if WIDE else Y
    placements=[]
    profiles=[]
    for i,nominal in enumerate(group):
        test=tests[nominal]
        source=Path(test['tiff'])
        assert hashlib.sha256(source.read_bytes()).hexdigest()==test['tiff_sha256']
        with Image.open(source) as im:
            assert im.size==(CARD_W,CARD_H) and im.mode=='RGB'
            assert all(abs(v-PPI)<.001 for v in im.info['dpi'])
            arr=np.asarray(im).copy()
            profiles.append(im.info['icc_profile'])
        placements.append({'nominal':nominal,'x':left if WIDE else left+i*(CARD_W+GAP),'y':row_y+i*(CARD_H+GAP) if WIDE else Y,'pixels':arr,'test':test})
    assert all(p[:24]+p[36:]==profiles[0][:24]+profiles[0][36:] for p in profiles)
    header=Image.new('RGB',(W,px(7) if WIDE else px(25)),'white')
    draw=ImageDraw.Draw(header)
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',px(3.6))
    caption=f'A3 / {page_number}-3  |  '+ ' + '.join(f'{n} LPI' for n in group)+'  |  %100 / GERÇEK BOYUT'
    draw.text((W//2,px(2) if WIDE else px(9)),caption,font=font,anchor='mt',fill='black')
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',px(2.7))
    if not WIDE:
        draw.text((W//2,px(16)),f'Her şeridin çizgili alanı {FIELD/10:g} cm. Ölçekleme / yeniden örnekleme kapalı.',font=small,anchor='mt',fill='black')
    header_arr=np.asarray(header)
    target=OUT/(f'A3-{page_number}-'+'-'.join(str(n) for n in group)+f'LPI-{FIELD//10}CM-1200PPI.tif')
    def strips():
        for top in range(0,H,128):
            bottom=min(H,top+128)
            tile=np.full((bottom-top,W,3),255,np.uint8)
            if top<header.height:
                end=min(bottom,header.height)
                tile[:end-top]=header_arr[top:end]
            for place in placements:
                a=max(top,place['y']);b=min(bottom,place['y']+CARD_H)
                if a<b:
                    tile[a-top:b-top,place['x']:place['x']+CARD_W]=place['pixels'][a-place['y']:b-place['y']]
            yield zlib.compress(tile.tobytes(),6)
    with tifffile.TiffWriter(target) as writer:
        writer.write(data=strips(),shape=(H,W,3),dtype=np.uint8,photometric='rgb',
            compression='deflate',rowsperstrip=128,resolution=(PPI,PPI),resolutionunit='INCH',
            metadata=None,extratags=[(34675,'B',len(profiles[0]),profiles[0],False)])
    # Decode the saved artifact to disk rather than holding a second full A3 in RAM.
    with tifffile.TiffFile(target) as tif:
        assert len(tif.pages)==1
        page=tif.pages[0]
        assert page.shape==(H,W,3)
        assert page.tags['ResolutionUnit'].value==2
        assert page.tags['XResolution'].value==(PPI,1)
        assert page.tags['YResolution'].value==(PPI,1)
        assert page.tags[34675].value==profiles[0]
        decoded=page.asarray(out='memmap')
        for place in placements:
            x,y=place['x'],place['y']
            saved=decoded[y:y+CARD_H,x:x+CARD_W]
            # Compare every pixel of the full original target, labels included.
            assert np.array_equal(saved,place['pixels'])
            for row in place['test']['rows']:
                x0,y0,x1,y1=row['box_px']
                assert hashlib.sha256(saved[y0:y1,x0:x1].tobytes()).hexdigest()==row['native_band_sha256']
                assert abs((x1-x0)/PPI*25.4-FIELD)<.02
        preview=Image.fromarray(decoded[::12,::12].copy())
        preview.save(HERE/(f'A3-preview-{page_number}'+('-22cm.png' if WIDE else '.png')))
        del decoded
    checks.append({'file':str(target),'lens_lpi':group,'pixels':[W,H],
        'size_mm':[W/PPI*25.4,H/PPI*25.4],'ppi':PPI,
        'pattern_width_mm':manifest['pattern_width_mm'],'all_source_pixels_equal':True,
        'all_native_band_hashes_equal':True,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    print(f'VERIFIED A3 {page_number}: {group}, {FIELD/10:g} cm fields unchanged',flush=True)
    del placements,arr,preview,header,header_arr
    gc.collect()
(HERE/('A3-verification-22cm.json' if WIDE else 'A3-verification.json')).write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('ALL_THREE_A3_TIFFS_VERIFIED',flush=True)

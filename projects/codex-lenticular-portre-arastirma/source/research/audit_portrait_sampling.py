"""Read-only comparison of source detail and lenticular sampling; no print edits."""
import json
from pathlib import Path
import cv2
import numpy as np
import tifffile
from PIL import Image

ROOT=Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1')
JOB=ROOT/'outputs/studio/20261009-113404-b9f6d34d'
DL=Path(r'C:\Users\USER\Downloads')
OUT=Path(__file__).resolve().parent/'portrait-sampling-audit'
OUT.mkdir(exist_ok=True)
cv2.setNumThreads(2)
def rgb(p):
    with Image.open(p) as im:return np.array(im.convert('RGB'))
def describe_tif(p):
    with tifffile.TiffFile(p) as t:
        pg=t.pages[0]; xr=pg.tags['XResolution'].value; yr=pg.tags['YResolution'].value
        xppi=xr[0]/xr[1]; yppi=yr[0]/yr[1]
        return dict(size_px=[pg.imagewidth,pg.imagelength],ppi=[xppi,yppi],size_mm=[pg.imagewidth/xppi*25.4,pg.imagelength/yppi*25.4],dtype=str(pg.dtype))
source=rgb(JOB/'prepared/photo.png'); center=rgb(JOB/'render/center.png')
regions={'face':(755,145,1165,750),'cloth':(650,930,1200,1660),'thumb':(335,1050,745,1660)}
report={'portrait':describe_tif(DL/'Lenticular-50LPI-Bolgesel-20261009-113340/Portre-50LPI-1200PPI-6Kanal-BOLGESEL.tif'),
        'ataturk':describe_tif(DL/'Ataturk_3D_50LPI_12kanal_1200PPI_200mm.tif'),'regions':{}}
pitch_src=source.shape[1]/(130/25.4*50)
for name,(x0,y0,x1,y1) in regions.items():
    s=source[y0:y1,x0:x1]; c=center[y0:y1,x0:x1]
    gray=cv2.cvtColor(s,cv2.COLOR_RGB2GRAY).astype(np.float32)
    smooth=cv2.GaussianBlur(gray,(0,1),pitch_src/3)
    residual=gray-smooth
    report['regions'][name]=dict(center_source_mae=float(np.mean(np.abs(c.astype(float)-s))),
        fine_horizontal_residual_rms=float(np.sqrt(np.mean(residual**2))),
        width_lenticules=(x1-x0)/pitch_src)
    Image.fromarray(np.concatenate([s,c],axis=1)).save(OUT/f'{name}-source-vs-center.png')
report['source_pixels_per_lenticule']=pitch_src
report['lenticular_sampling']=dict(portrait_lenticules_across_width=130/25.4*50,
    ataturk_lenticules_across_width=report['ataturk']['size_mm'][0]/25.4*50,
    output_pixels_per_lenticule=1200/50,output_pixels_per_channel=1200/50/6)
print(json.dumps(report,ensure_ascii=False,indent=2))
(OUT/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

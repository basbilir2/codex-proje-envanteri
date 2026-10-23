from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
import cv2
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from lenticular.layers import reliable_depth_core
from lenticular.restoration import complete_depth
OUT=Path(__file__).resolve().parent
SRC=ROOT/'outputs/surface-upgrade-20261009-220345/native-portrait-final'
depth=np.load(SRC/'depth_proximity.npy');box=(410,1040,710,1520);x0,y0,x1,y1=box
report=json.loads((SRC/'repair.json').read_text())
tiles=[]
def add(title,image):
    p=Image.new('RGB',(300,510),'#333333');p.paste(image.crop(box).convert('RGB'),(0,30));ImageDraw.Draw(p).text((4,6),title,fill='white');tiles.append(p)
add('Source',Image.open(SRC/'source.png'))
add('Center render',Image.open(SRC/'center.png'))
add('Original depth',Image.fromarray(cv2.applyColorMap(np.rint(depth*255).astype('uint8'),cv2.COLORMAP_TURBO)[:,:,::-1]))
for i,item in enumerate(report['layers']):
    mask=np.asarray(Image.open(SRC/f'layer_{i:02d}_mask.png'))>0
    hidden=np.asarray(Image.open(SRC/f'layer_{i+1:02d}_mask.png'))>0 if i<2 else np.zeros_like(mask)
    low,high=item['depth_interval'];valid=reliable_depth_core(mask&~hidden,depth,low,high,fine=True)
    geometry=complete_depth(depth,valid,low,high,surface_mask=mask&~hidden)
    np.save(OUT/f'geometry_{i}.npy',geometry)
    rgba=Image.open(SRC/f'layer_{i:02d}.png').convert('RGBA');bg=Image.new('RGBA',rgba.size,'#669988');bg.alpha_composite(rgba)
    add(f'Layer {i} texture',bg)
    add(f'Layer {i} geometry',Image.fromarray(cv2.applyColorMap(np.rint(geometry*255).astype('uint8'),cv2.COLORMAP_TURBO)[:,:,::-1]))
    core=np.repeat((valid*255).astype('uint8')[:,:,None],3,axis=2);core[mask&~valid]=[190,40,40];add(f'Layer {i} core',Image.fromarray(core))
canvas=Image.new('RGB',(1200,1530),'#333333')
for n,p in enumerate(tiles):canvas.paste(p,((n%4)*300,(n//4)*510))
canvas.save(OUT/'diagnostic.png')
print('Diagnostic and layer geometry saved.')

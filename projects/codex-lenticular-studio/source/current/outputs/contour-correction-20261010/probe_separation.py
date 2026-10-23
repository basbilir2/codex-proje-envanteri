from pathlib import Path
import sys,json,shutil,subprocess
import cv2,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from lenticular.layers import align_mask,reliable_depth_core
from lenticular.restoration import matte,complete_color,complete_depth
from lenticular.geometry import build_mesh
from lenticular.runner import find_blender
OUT=Path(__file__).resolve().parent;SRC=ROOT/'outputs/surface-upgrade-20261009-220345/native-portrait-final'
T=OUT/'probe';T.mkdir(exist_ok=True)
job=json.loads((SRC/'job.json').read_text());config=job['config'];d=np.load(SRC/'depth_proximity.npy')
rgb=np.asarray(Image.open(SRC/'source.png').convert('RGB'));cut=.6930732679150853
mask=np.asarray(Image.open(SRC/'layer_02_mask.png'))>0
near=align_mask(rgb,d>cut,fine=True)&mask
Image.fromarray(near.astype('uint8')*255).save(T/'near_mask.png')
for i,surface,hidden,low,high in [(2,mask,near,.4554727077484131,cut),(3,near,np.zeros_like(mask),cut,1)]:
    if i==2:
        color=np.asarray(Image.open(SRC/'layer_02.png').convert('RGB')).copy();alpha=np.asarray(Image.open(SRC/'layer_02.png'))[:,:,3]/255
        removal=cv2.dilate(near.astype('uint8'),np.ones((15,15),np.uint8))>0
        filled,info=complete_color(rgb,removal);color[removal]=filled[removal]
    else:alpha,color,info=matte(rgb,surface)
    texture=Image.fromarray(color).convert('RGBA');texture.putalpha(Image.fromarray(np.rint(alpha*255).astype('uint8')));texture.save(T/f'layer_{i:02d}.png')
    valid=reliable_depth_core(surface&~hidden,d,low,high,fine=True)
    geometry=complete_depth(d,valid,low,high,surface_mask=surface&~hidden)
    mesh,stats=build_mesh(geometry,config|{'edge_threshold':1.},sample_mode='linear')
    np.savez_compressed(T/f'layer_{i:02d}.npz',**mesh)
    print('Layer',i,'ready',flush=True)
(T/'probe.json').write_text(json.dumps(dict(source=str(SRC),out=str(T),config=config,size=job['size'])))
command=[str(find_blender()),'--background','--factory-startup','--python-exit-code','1','--python',str(OUT/'render_probe.py'),'--',str(T/'probe.json')]
with (T/'blender.log').open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
print('Probe complete',flush=True)

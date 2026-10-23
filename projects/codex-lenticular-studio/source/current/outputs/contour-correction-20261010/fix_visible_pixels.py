from pathlib import Path
import sys,json,subprocess,shutil
import numpy as np,cv2
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from lenticular.restoration import matte
from lenticular.runner import find_blender,preview
OUT=Path(__file__).resolve().parent;SRC=OUT/'scene';T=OUT/'ownership';T.mkdir()
job=json.loads((SRC/'job.json').read_text());job['config']['nr']=2;job['config']['positions']=[job['config']['positions'][0],job['config']['positions'][-1]]
report=json.loads((SRC/'repair.json').read_text());rgb=np.asarray(Image.open(SRC/'source.png').convert('RGB'))
masks=[np.asarray(Image.open(SRC/f'layer_{i:02d}_mask.png'))>0 for i in range(len(job['surfaces']))]
for name in ('source.png','depth_proximity.npy','mesh.npz'):shutil.copy2(SRC/name,T/name)
for i,layer in enumerate(job['surfaces']):
    with Image.open(SRC/layer['texture']) as image:old=np.asarray(image).copy()
    pad=report['layers'][i]['texture_padding_px']
    if i:alpha,color,info=matte(rgb,masks[i])
    else:alpha=masks[i].astype(np.float32);color=rgb.copy()
    if i+1<len(masks):
        with Image.open(SRC/job['surfaces'][i+1]['texture']) as image:near=np.asarray(image)[:,:,3]>0
    else:near=np.zeros(masks[i].shape,bool)
    if pad:
        color=np.pad(color,((pad,pad),(pad,pad),(0,0)),mode='edge');alpha=np.pad(alpha,((pad,pad),(pad,pad)),mode='edge')
        replace=np.pad(near,((pad,pad),(pad,pad)),constant_values=True)
    else:replace=near
    # Reuse the identical LaMa prediction computed for the same source and
    # removal mask. Only its application mask changes; geometry is identical.
    color[replace]=old[:,:,:3][replace]
    texture=Image.fromarray(color).convert('RGBA');texture.putalpha(Image.fromarray(np.rint(alpha*255).astype('uint8')));texture.save(T/layer['texture'])
    shutil.copy2(SRC/layer['mesh'],T/layer['mesh']);shutil.copy2(SRC/f'layer_{i:02d}_mask.png',T/f'layer_{i:02d}_mask.png')
    print('Visible pixels protected in layer',i,flush=True)
(T/'job.json').write_text(json.dumps(job,indent=2));(T/'repair.json').write_text(json.dumps(report|dict(completion_application='Only rendered nearer alpha or outside-frame padding; visible context retained'),indent=2))
cmd=[str(find_blender()),'--background','--factory-startup','--python-exit-code','1','--python',str(ROOT/'lenticular/blender_scene.py'),'--',str(T/'job.json')]
with (T/'blender.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
preview(T,job);print('Ownership endpoints ready',flush=True)

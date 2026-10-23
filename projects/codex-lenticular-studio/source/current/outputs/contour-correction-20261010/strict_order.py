from pathlib import Path
import sys,json,shutil,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from lenticular.runner import find_blender,preview
OUT=Path(__file__).resolve().parent;SRC=OUT/'rejected-coincident-surfaces';T=OUT/'coupled';T.mkdir()
job=json.loads((SRC/'job.json').read_text());report=json.loads((SRC/'repair.json').read_text());config=job['config']
for name in ('source.png','depth_proximity.npy','mesh.npz'):shutil.copy2(SRC/name,T/name)
ranges=[]
for i,layer in enumerate(job['surfaces']):
    with np.load(SRC/layer['mesh']) as data:mesh={k:data[k] for k in data.files}
    z=-mesh['vertices'][:,2];d=(1/z-1/config['far'])/(1/config['near']-1/config['far'])
    low,high=report['layers'][i]['depth_interval'];eps=min(1e-4,(high-low)*.01)
    lo=low+eps if i else low;hi=high-eps if i+1<len(job['surfaces']) else high
    bounded=np.clip(d,lo,hi);newz=1/((1-bounded)/config['far']+bounded/config['near'])
    mesh['vertices']*=newz[:,None]/z[:,None];np.savez_compressed(T/layer['mesh'],**mesh)
    ranges.append([float(bounded.min()),float(bounded.max())]);report['layers'][i]['geometry_interval']=[lo,hi]
    shutil.copy2(SRC/layer['texture'],T/layer['texture']);shutil.copy2(SRC/f'layer_{i:02d}_mask.png',T/f'layer_{i:02d}_mask.png')
assert all(ranges[i+1][0]-ranges[i][1]>1e-5 for i in range(len(ranges)-1))
(T/'job.json').write_text(json.dumps(job,indent=2));(T/'repair.json').write_text(json.dumps(report,indent=2))
(OUT/'strict-order-verification.json').write_text(json.dumps(dict(ranges=ranges,strictly_ordered=True,texture_reused_without_changes=True),indent=2))
cmd=[str(find_blender()),'--background','--factory-startup','--python-exit-code','1','--python',str(OUT/'render_strict.py'),'--',str(T/'job.json')]
with (T/'blender.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
preview(T,job);print('Strict layer order endpoint validation ready',flush=True)

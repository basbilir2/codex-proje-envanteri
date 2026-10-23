import sys,json,shutil,subprocess,time
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from lenticular.layers import reliable_depth_core
from lenticular.restoration import complete_depth
from lenticular.geometry import build_mesh
from lenticular.runner import find_blender,preview
from lenticular.printing import encode
OUT=Path(__file__).resolve().parent;source=OUT/'native-portrait/render';target=OUT/'native-portrait-corrected';target.mkdir()
job=json.loads((source/'job.json').read_text());config=job['config'];report=json.loads((source/'repair.json').read_text())
depth=np.load(source/'depth_proximity.npy',allow_pickle=False)
start=time.perf_counter()
for name in ('source.png','depth_proximity.npy','mesh.npz'):shutil.copy2(source/name,target/name)
for i,layer in enumerate(job['surfaces']):
 mask=np.asarray(Image.open(source/f'layer_{i:02d}_mask.png'))>0
 hidden=np.asarray(Image.open(source/f'layer_{i+1:02d}_mask.png'))>0 if i+1<len(job['surfaces']) else np.zeros_like(mask)
 low,high=report['layers'][i]['depth_interval'];valid=reliable_depth_core(mask&~hidden,depth,low,high,fine=True)
 geometry=complete_depth(depth,valid,low,high)
 mesh,stats=build_mesh(geometry,config|{'edge_threshold':1.0},padding=report['padding_px'] if i==0 else 0)
 np.savez_compressed(target/layer['mesh'],**mesh)
 shutil.copy2(source/layer['texture'],target/layer['texture']);shutil.copy2(source/f'layer_{i:02d}_mask.png',target/f'layer_{i:02d}_mask.png')
 report['layers'][i]['mesh']=stats
print('Corrected native geometry ready; existing verified textures reused.',flush=True)
(target/'repair.json').write_text(json.dumps(report,indent=2));(target/'job.json').write_text(json.dumps(job,indent=2))
command=[str(find_blender()),'--background','--factory-startup','--python-exit-code','1','--python',str(ROOT/'lenticular/blender_scene.py'),'--',str(target/'job.json')]
with (target/'blender.log').open('w',encoding='utf-8') as log:
 process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
 for line in process.stdout:
  log.write(line)
  if line.startswith('LENTICULAR_VIEW'):print(line.strip(),flush=True)
 if process.wait():raise RuntimeError('Blender failed')
preview(target,job)
printing=json.loads((OUT/'native-portrait/print/print-report.json').read_text())['settings']
result=encode(target,target/'print',printing)
assert result['raster_integrity']['sampled_pixels_verified']
(target/'validation.json').write_text(json.dumps(dict(render_size=job['size'],raster_size=result['raster_size'],views=len(config['positions']),raster_integrity=result['raster_integrity'],seconds=time.perf_counter()-start,texture_reuse='Shared textures from native-portrait; depth geometry recomputed with reliable_depth_core',physical_print_verified=False),indent=2))
print('Corrected native print verified',result['raster_size'],flush=True)

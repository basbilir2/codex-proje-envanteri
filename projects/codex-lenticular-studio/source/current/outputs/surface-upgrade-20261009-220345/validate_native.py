import sys,json,time
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from lenticular.geometry import validate
from lenticular.pipeline import render_settings
from lenticular.repair import editable_depth,plan_parallax
from lenticular.runner import render,digest
from lenticular.printing import encode
from lenticular.frames import FrameSet
OUT=Path(__file__).resolve().parent/'native-portrait'
PROJECT=Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac173361d8c8191a1449be5154f589f')
r=json.loads((PROJECT/'fullscene-current.json').read_text());source=Path(r['shared'])
old=FrameSet(Path(r['work'])/'conditioned')
hashes={n:digest(source/n) for n in ('photo.png','depth.npy')}
photo=Image.open(source/'photo.png').convert('RGBA');depth=np.load(source/'depth.npy',allow_pickle=False)
reference=(1/old.data['config']['zero']-1/3)/(1/1.5-1/3)
s=render_settings(dict(depth_curve='balanced',zero_reference=reference,angle_deg=4.5,front_parallax_percent=3,back_parallax_percent=3,depth_smoothing=0,edge_refinement=0,nr=12,grid_size=512,render_long_edge=0,repair_quality='advanced'))
balanced,edits=editable_depth(depth,s,photo);geometry,parallax,_=plan_parallax(balanced,photo.size,s)
config=validate(dict(nr=12,ne=12,grid_size=512,edge_mode='split',**geometry))
OUT.mkdir();photo.save(OUT/'photo.png');np.save(OUT/'depth.npy',balanced)
start=time.perf_counter();print('Native render starting:',photo.size,flush=True)
folder=render(OUT/'photo.png',OUT/'depth.npy',OUT/'render',config,repair=dict(enabled=True,layers=3,radius=5,quality='advanced'),progress=lambda s:print(s,flush=True))
render_seconds=time.perf_counter()-start
print('Native render complete; production-size QA raster starting.',flush=True)
printing=r['printing']|dict(ne=12,effective_lpi=50.2,ppi=1200,stripe_sampling='area',pitch_verified=False,raster_ppi_verified=False,lens_angle_verified=False,white_underbase=False,pitch_candidates=3)
report=encode(folder,OUT/'print',printing)
assert report['raster_integrity']['sampled_pixels_verified'];assert report['distinct_source_images']==12
assert all(digest(source/name)==value for name,value in hashes.items())
result=dict(render_size=photo.size,raster_size=report['raster_size'],render_seconds=render_seconds,total_seconds=time.perf_counter()-start,source_hashes=hashes,source_unchanged=True,render_settings=s,parallax=parallax,coverage=json.loads((folder/'coverage.json').read_text()),restoration=json.loads((folder/'repair.json').read_text()),raster_integrity=report['raster_integrity'],physical_print_verified=False)
(OUT/'validation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:result[k] for k in ('render_size','raster_size','render_seconds','total_seconds','source_unchanged','physical_print_verified')}),flush=True)

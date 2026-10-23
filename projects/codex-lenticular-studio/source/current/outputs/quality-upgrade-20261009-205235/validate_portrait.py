"""Read-only source audit plus a bounded actual Blender regression render."""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from lenticular.frames import FrameSet
from lenticular.geometry import validate
from lenticular.optics import depth_sampling, sampling_budget
from lenticular.pipeline import render_settings
from lenticular.printing import encode
from lenticular.repair import editable_depth, plan_parallax
from lenticular.runner import digest, render

OUT=Path(__file__).resolve().parent/'portrait-check-v2'
PROJECT=Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac173361d8c8191a1449be5154f589f')
r=json.loads((PROJECT/'fullscene-current.json').read_text())
source=Path(r['shared']);old=FrameSet(Path(r['work'])/'conditioned')
hashes={name:digest(source/name) for name in ('photo.png','depth.npy')}
printing=r['printing']|dict(ne=12,effective_lpi=50.2)
depth=np.load(source/'depth.npy',allow_pickle=False)
before,_=depth_sampling(depth,old.data['config'],old.size,printing,old.plan(printing)['source_indices'])
all_counts={}
for count in (6,10,12):
    s=printing|{'ne':count}
    a,_=depth_sampling(depth,old.data['config'],old.size,s,old.plan(s)['source_indices'])
    all_counts[str(count)]=a
photo=Image.open(source/'photo.png').convert('RGBA');photo.thumbnail((768,768),Image.Resampling.LANCZOS)
small=cv2.resize(depth,photo.size,interpolation=cv2.INTER_LINEAR)
reference=(1/old.data['config']['zero']-1/3)/(1/1.5-1/3)
settings=render_settings(dict(depth_curve='balanced',zero_reference=reference,angle_deg=4.5,
    front_parallax_percent=3,back_parallax_percent=3,depth_smoothing=0,edge_refinement=0,
    nr=12,grid_size=256,edge_guard=True,parallax_guard=True,max_parallax_percent=3))
balanced,edits=editable_depth(small,settings)
geometry,parallax,_=plan_parallax(balanced,photo.size,settings)
config=validate(dict(nr=12,ne=12,grid_size=256,edge_mode='split',**geometry))
OUT.mkdir(exist_ok=False)
photo.save(OUT/'photo.png');np.save(OUT/'depth.npy',balanced)
result=render(OUT/'photo.png',OUT/'depth.npy',OUT/'render',config,repair=dict(enabled=True,layers=4,radius=5))
frames=FrameSet(result)
after,_=depth_sampling(balanced,config,photo.size,printing,frames.plan(printing)['source_indices'])
# Small QA raster: verifies the full encoder, not a production print of this portrait.
qa=printing|dict(width_mm=25.4,height_mm=25.4*photo.height/photo.width,ppi=1200,white_underbase=False,
    stripe_sampling='area',pitch_candidates=3,pitch_verified=False)
report=encode(result,OUT/'print-qa',qa)
assert report['raster_integrity']['sampled_pixels_verified']
assert report['distinct_source_images']==12
assert all(digest(source/name)==value for name,value in hashes.items())
summary=dict(before=before,before_ne_comparison=all_counts,after_balanced=after,
    balanced_settings=settings,edits=edits,parallax=parallax,sampling=sampling_budget(printing),
    render_folder=str(result),qa_raster=report['raster_size'],source_hashes=hashes,source_unchanged=True,
    limitation='768px render and small QA TIFF verify software only; not a high-resolution production proof or measured physical improvement.')
(OUT/'comparison.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))

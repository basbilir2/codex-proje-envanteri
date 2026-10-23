from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
OLD=ROOT/'outputs/surface-upgrade-20261009-220345/native-portrait-final';NEW=OUT/'coupled'
def rgb(path):
    with Image.open(path) as image:return np.asarray(image.convert('RGB')).astype(np.float32)
source=rgb(OLD/'source.png');old=rgb(OLD/'center.png');new=rgb(NEW/'center.png')
regions={'whole_source':(0,0,1872,3098),'hand':(370,1020,770,1540),'cloth_edge':(180,1550,500,1930)}
errors={}
for name,(x0,y0,x1,y1) in regions.items():
    entry={}
    for label,value in [('before',old),('after',new)]:
        difference=np.abs(value[y0:y1,x0:x1]-source[y0:y1,x0:x1])
        entry[label]=dict(mean_absolute_rgb_error=float(difference.mean()),pixels_over_32_fraction=float((difference.max(axis=2)>32).mean()))
    errors[name]=entry
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
files=['lenticular/layers.py','lenticular/restoration.py','lenticular/pipeline.py','lenticular/web/index.html','tests/test_surface_quality.py']
record=dict(source_reprojection_errors=errors,source_photo_sha256=sha(OLD/'source.png'),
    source_depth_sha256=sha(OLD/'depth_proximity.npy'),modified_files={name:sha(ROOT/name) for name in files},
    note='Source-camera color fidelity is not a side-view shape or physical-print score.')
(OUT/'final-checks.json').write_text(json.dumps(record,indent=2))
print(json.dumps(errors,indent=2))

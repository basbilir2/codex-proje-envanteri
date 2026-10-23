from pathlib import Path
import sys,json,subprocess,shutil,time,hashlib
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from lenticular.runner import find_blender,preview,digest
from lenticular.printing import encode
OUT=Path(__file__).resolve().parent;T=OUT/'coupled';OLD=ROOT/'outputs/surface-upgrade-20261009-220345/native-portrait-final'
acceptance=json.loads((OUT/'visual-acceptance.json').read_text())
assert acceptance.get('accepted_for_print') is True,'Digital visual acceptance is still pending; do not create another print candidate'
job=json.loads((T/'job.json').read_text());original=json.loads((OLD/'job.json').read_text());records=json.loads((T/'render_result.json').read_text())
shutil.copy2(T/'job.json',T/'endpoint-job.json');shutil.copy2(T/'render_result.json',T/'endpoint-records.json')
shutil.copy2(T/'views/view_0001.png',T/'views/view_0011.png')
job['config']=original['config'];(T/'job.json').write_text(json.dumps(job,indent=2))
cmd=[str(find_blender()),'--background','--factory-startup','--python-exit-code','1','--python',str(OUT/'render_remaining.py'),'--',str(T/'job.json')]
start=time.perf_counter()
with (T/'remaining.log').open('w',encoding='utf-8') as log:
    p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
    for line in p.stdout:
        log.write(line)
        if line.startswith('LENTICULAR_VIEW'):print(line.strip(),flush=True)
    if p.wait():raise RuntimeError('Remaining views failed')
preview(T,job)
settings=json.loads((OLD/'print/print-report.json').read_text())['settings']
result=encode(T,T/'print',settings)
assert result['raster_integrity']['sampled_pixels_verified']
verification=dict(source_photo_unchanged=digest(Path(job['source_inputs']['photo']))==job['source_inputs']['photo_sha256'],
    source_depth_unchanged=digest(Path(job['source_inputs']['depth']))==job['source_inputs']['depth_sha256'],
    camera_configuration_unchanged=job['config']==original['config'],views=12,render_size=job['size'],
    raster_size=result['raster_size'],raster_integrity=result['raster_integrity'],seconds=time.perf_counter()-start,
    physical_print_verified=False,visual_acceptance='See contour-correction report; no universal quality guarantee')
(OUT/'validation.json').write_text(json.dumps(verification,indent=2))
print('New 12-view TIFF verified',result['raster_size'],flush=True)

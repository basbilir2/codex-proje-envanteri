import json,time,urllib.request,shutil,hashlib
from pathlib import Path
import tifffile,numpy as np
from PIL import Image
from lenticular.printing import channel_pattern,fitted_tile
root=Path.cwd();plan=json.loads((root/'.studio/numune-50-60-plan.json').read_text(encoding='utf-8'))
def api(path,payload=None):
    info=json.loads((root/'.studio/server.json').read_text(encoding='utf-8'))
    url=info['url'].replace('/?',path+'?')
    req=urllib.request.Request(url,None if payload is None else json.dumps(payload).encode(),{} if payload is None else {'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(req,timeout=60))
def wait_for(identifier):
    last=None
    while True:
        job=api('/api/state')['jobs'][identifier]
        msg=(job['status'],job.get('message'))
        if msg!=last:print(json.dumps({'id':identifier,'status':msg[0],'message':msg[1]},ensure_ascii=True),flush=True);last=msg
        if job['status']=='complete':return job
        if job['status'] in ('failed','cancelled','interrupted'):raise RuntimeError(job.get('error') or job.get('message'))
        time.sleep(8)
render=wait_for(plan['render_job'])
out=root/'outputs/NUMUNELER_50_60_LPI_20261005';out.mkdir(exist_ok=True)
results=[]
for lpi,ppi,ne,angle in [(50,1200,12,41),(60,1200,10,39)]:
    settings=plan['print']|dict(nominal_lpi=lpi,effective_lpi=lpi,ppi=ppi,ne=ne,lens_view_angle_deg=angle,reverse_views=True,mirror=False,white_underbase=False)
    identifier=api('/api/jobs',dict(asset_id=plan['asset_id'],stage='print',render_job=plan['render_job'],render=plan['render'],print=settings))['id']
    job=wait_for(identifier);folder=Path(job['output'])/'print';report=json.loads((folder/'print-report.json').read_text(encoding='utf-8'))
    assert len(set(report['source_indices']))==ne and report['source_indices'][0]==11 and report['source_indices'][-1]==0
    assert report['nonopaque_source_fraction']<=.0005
    assert all(abs(v-1/ne)<.001 for v in report['raster_channel_coverage_fraction'])
    path=folder/'interlaced.tif';pixels=tifffile.memmap(path);h,w=pixels.shape[:2]
    cols=np.arange(13,w-13,37);row=h//2;pattern=channel_pattern(w,row,1,settings)[0];maxdiff=0
    for channel in range(ne):
        selected=cols[pattern[cols]==channel]
        if not len(selected):continue
        source=np.asarray(Image.open(Path(render['render_folder'])/f"views/view_{report['source_indices'][channel]:04d}.png").convert('RGB'))
        expected=fitted_tile(source,w,h,row,1,settings,columns=selected)
        maxdiff=max(maxdiff,int(np.max(np.abs(expected.astype(np.int16)-pixels[row:row+1,selected].astype(np.int16)))))
    assert maxdiff==0, maxdiff
    del pixels
    target=out/f'Ataturk_3D_{lpi}LPI_{ne}kanal_{ppi}PPI_200mm.tif'
    if target.exists():raise FileExistsError(target)
    shutil.copyfile(path,target)
    hashval=hashlib.file_digest(target.open('rb'),'sha256').hexdigest()
    assert hashval==report['interlaced_sha256']
    api('/api/profile',dict(name=f'Grando 1200 - {lpi} LPI - {ne} kanal - numune',render=plan['render'],print=settings))
    results.append(dict(lpi=lpi,ppi=ppi,job=identifier,file=str(target),sha256=hashval,size=report['raster_size'],physical_size_mm=report['physical_size_mm'],max_sample_rgb_error=maxdiff,ne=ne,channel_width_pixels=ppi/lpi/ne))
    (root/'.studio/numune-50-60-result.json').write_text(json.dumps(dict(render_job=plan['render_job'],results=results),indent=2),encoding='utf-8')
    print(json.dumps(results[-1]),flush=True)
print('TWO_SAMPLES_READY',flush=True)

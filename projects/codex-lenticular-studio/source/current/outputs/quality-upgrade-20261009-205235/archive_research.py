"""Archive public primary references with hashes; never install downloaded code."""
import concurrent.futures
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/research/2026-10-09'
OUT.mkdir(parents=True,exist_ok=True)
SOURCES=[
 ('triaxes-depth','https://triaxes.com/docs/3dmk11-en/26Backgroundandforegroundparalla.html','html'),
 ('triaxes-layers','https://triaxes.com/docs/3dmk10/3DMasterKit-en/432Dto3Dconversion.html','html'),
 ('triaxes-legend','https://triaxes.com/legend/','html'),
 ('triaxes-pitch-guide','https://triaxes.com/downloads/Pitch-test-en.pdf','pdf'),
 ('imagiam-features','https://www.imagiam.com/lenticular-software/features','html'),
 ('3dz-suite','https://www.lenticularsoftware.de/onlinetools/index.htm','html'),
 ('3dz-pitch','https://www.lenticularsoftware.de/onlinetools/Pitchtest/anleitung.htm','html'),
 ('content-adaptive-lenticular','https://studios.disneyresearch.com/wp-content/uploads/2019/03/Content-adaptive-Lenticular-Prints-2.pdf','pdf'),
 ('display-calibration','https://arxiv.org/pdf/1606.07166','pdf'),
 ('layered-depth-inpainting','https://openaccess.thecvf.com/content_CVPR_2020/papers/Shih_3D_Photography_Using_Context-Aware_Layered_Depth_Inpainting_CVPR_2020_paper.pdf','pdf'),
 ('depth-anything-3','https://github.com/ByteDance-Seed/Depth-Anything-3','html'),
 ('moge','https://github.com/microsoft/MoGe','html'),
 ('sam2','https://github.com/facebookresearch/sam2','html'),
 ('lama','https://github.com/advimman/lama','html'),
 ('humaneyes-vendor-overview','https://dplenticular.com/lenticular-software/software-applications/human-eyes/','html'),
]
def fetch(item):
    name,url,extension=item
    record=dict(id=name,url=url,accessed='2026-10-09',status='unavailable')
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(request,timeout=40) as response:
            data=response.read(40*1024*1024+1)
            if len(data)>40*1024*1024:raise ValueError('Reference exceeds archive size limit')
            if extension=='pdf' and not data.startswith(b'%PDF'):raise ValueError('Response is not a PDF')
            target=OUT/(name+'.'+extension);target.write_bytes(data)
            record.update(status='archived',file=target.name,size_bytes=len(data),
                sha256=hashlib.sha256(data).hexdigest(),resolved_url=response.url)
    except Exception as error:record['error']=str(error)
    return record
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results=list(pool.map(fetch,SOURCES))
(OUT/'sources.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps([dict(id=r['id'],status=r['status'],bytes=r.get('size_bytes'),error=r.get('error')) for r in results]))

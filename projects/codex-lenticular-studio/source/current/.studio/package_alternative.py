import json,time,urllib.request,shutil,hashlib
from pathlib import Path
import tifffile
root=Path(__file__).resolve().parents[1]
item=json.loads((root/'.studio/production-alternative.json').read_text('utf-8'))
server=json.loads((root/'.studio/server.json').read_text('utf-8'));token=server['url'].split('?t=')[1]
last=''
while True:
    req=urllib.request.Request('http://127.0.0.1:8765/api/state',headers={'X-Studio-Token':token})
    state=json.load(urllib.request.urlopen(req,timeout=20));job=state['jobs'][item['job_id']]
    if job.get('message')!=last:print(job.get('message'),flush=True);last=job.get('message')
    if job['status']=='complete':break
    if job['status'] in ['failed','cancelled','interrupted']:raise RuntimeError(job.get('message'))
    time.sleep(30)
dest=Path(item['folder']);output=Path(job['output']);target=dest/(item['name']+'.tif')
report=json.loads((output/'print/print-report.json').read_text('utf-8'))
assert report['nr']==report['ne']==12 and len(set(report['source_indices']))==12
assert job['quality']['max_nonopaque_fraction']<=.0005
shutil.copy2(output/'print/interlaced.tif',target)
with tifffile.TiffFile(target) as tif:
    page=tif.pages[0];assert page.shape==(11028,9449,3)
    a,b=page.tags['XResolution'].value;assert a/b==1200
with target.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
assert sha==report['interlaced_sha256']
(dest/'Ayarlar'/(item['name']+'.json')).write_text(json.dumps(dict(schema_version=1,render=item['render'],print=item['print']),indent=2,ensure_ascii=False),'utf-8')
shutil.copy2(output/'print/print-report.json',dest/'Raporlar'/(item['name']+'_baski.json'))
shutil.copy2(output/'quality.json',dest/'Raporlar'/(item['name']+'_3d.json'))
shutil.copy2(Path(job['render_folder'])/'look-around.png',dest/'Onizlemeler'/(item['name']+'_HAREKETLI.png'))
manifest=dest/'teslim-manifestosu.json';records=json.loads(manifest.read_text('utf-8'))
records=[r for r in records if r['file']!=target.name]
records.append(dict(file=target.name,sha256=sha,bytes=target.stat().st_size,raster_size=report['raster_size'],physical_size_mm=report['physical_size_mm'],
    lpi=100,dpi=1200,views=12,actual_angle_deg=job['quality']['parallax']['effective_angle_deg'],
    max_parallax_percent=job['quality']['parallax']['max_parallax_percent'],empty_fraction=job['quality']['max_nonopaque_fraction'],
    warnings=job['warnings'],job_id=job['id'],alternative=True))
manifest.write_text(json.dumps(records,indent=2,ensure_ascii=False),'utf-8')
notes=dest/'ONCE_OKU_BASKI_NOTLARI.txt'
with notes.open('a',encoding='utf-8') as stream:
    stream.write('\n\nEK ALTERNATIF - 5 Ekim 2026\n100 lpi alternatif 1200 dpi.tif: 12 gorunus, 20x23.34 cm.\n')
    stream.write(f"Gercek kamera acisi {job['quality']['parallax']['effective_angle_deg']:.4f} derece; kayma %{job['quality']['parallax']['max_parallax_percent']:.3f}. Standart 100 LPI surumunden daha guclu, fiziksel test gerektirir.\nToplam 10 renkli TIFF: ilk 9 karsilastirma + bu alternatif.\n")
print('ALTERNATIVE_READY',target,flush=True)
print(json.dumps(job['quality']['parallax']),flush=True)

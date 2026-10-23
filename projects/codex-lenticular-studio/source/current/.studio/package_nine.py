"""Package this requested nine-output run; inspect metadata, no extra renders."""
import json, shutil, time, urllib.request, hashlib
from pathlib import Path
import tifffile

root=Path(__file__).resolve().parents[1]
plan=json.loads((root/'.studio/production-nine.json').read_text('utf-8'))
dest=Path(plan['folder']); manifest=dest/'teslim-manifestosu.json'
completed={v['job_id']:v for v in json.loads(manifest.read_text('utf-8'))} if manifest.exists() else {}
last=''
for name in ['Ayarlar','Onizlemeler','Kalibrasyon','Raporlar']:(dest/name).mkdir(exist_ok=True)
while len(completed)<len(plan['items']):
    server=json.loads((root/'.studio/server.json').read_text('utf-8'))
    req=urllib.request.Request('http://127.0.0.1:8765/api/state',headers={'X-Studio-Token':server['url'].split('?t=')[1]})
    state=json.load(urllib.request.urlopen(req,timeout=20))
    for item in plan['items']:
        key=item['job_id']; job=state['jobs'][key]
        if job['status'] in ['failed','cancelled','interrupted']:raise RuntimeError(f"{item['name']}: {job['status']} {job.get('message')}")
        if job['status']!='complete' or key in completed:continue
        output=Path(job['output']); report=json.loads((output/'print/print-report.json').read_text('utf-8'))
        assert report['nr']==report['ne']==item['views']
        assert len(set(report['source_indices']))==item['views']
        assert job['quality']['max_nonopaque_fraction']<=.0005
        filename=item['name']+'.tif';target=dest/filename
        shutil.copy2(output/'print/interlaced.tif',target)
        with tifffile.TiffFile(target) as tif:
            page=tif.pages[0];w,h=report['raster_size']
            assert page.shape==(h,w,3)
            resolution=page.tags['XResolution'].value
            assert abs(resolution[0]/resolution[1]-item['dpi'])<.01
            assert len(page.tags[34675].value)>0
        with target.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
        with (output/'print/interlaced.tif').open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==sha
        white=dest/f'BEYAZ_ALT_BASKI_{item["dpi"]}DPI_20x23.34cm.tif'
        if not white.exists():shutil.copy2(output/'print/white-underbase.tif',white)
        profile=dict(schema_version=1,render=item['render'],print=item['print'])
        (dest/'Ayarlar'/(item['name']+'.json')).write_text(json.dumps(profile,indent=2,ensure_ascii=False),'utf-8')
        shutil.copy2(output/'print/print-report.json',dest/'Raporlar'/(item['name']+'_baski.json'))
        (dest/'Raporlar'/(item['name']+'_3d.json')).write_text(json.dumps(job['quality'],indent=2,ensure_ascii=False),'utf-8')
        shutil.copy2(Path(job['render_folder'])/'look-around.png',dest/'Onizlemeler'/(item['name']+'_HAREKETLI.png'))
        cal=dest/'Kalibrasyon'/f'{item["lpi"]}LPI_{item["dpi"]}DPI';cal.mkdir(exist_ok=True)
        for name in ['pitch-test.tif','pitch-test.json','registration.svg']:
            if not (cal/name).exists():shutil.copy2(output/'print'/name,cal/name)
        completed[key]=dict(file=filename,sha256=sha,bytes=target.stat().st_size,raster_size=report['raster_size'],
            physical_size_mm=report['physical_size_mm'],lpi=item['lpi'],dpi=item['dpi'],views=item['views'],
            actual_angle_deg=job['quality']['parallax']['effective_angle_deg'],
            max_parallax_percent=job['quality']['parallax']['max_parallax_percent'],
            empty_fraction=job['quality']['max_nonopaque_fraction'],warnings=job['warnings'],job_id=key)
        (dest/'teslim-manifestosu.json').write_text(json.dumps(list(completed.values()),indent=2,ensure_ascii=False),'utf-8')
        print('PACKAGED',filename,flush=True)
    active=[f"{i['lpi']}LPI/{i['dpi']}DPI/{i['views']} views: {state['jobs'][i['job_id']].get('message')}" for i in plan['items'] if state['jobs'][i['job_id']]['status']=='running']
    status=f'{len(completed)}/9 ready; '+ '; '.join(active)
    if status!=last:print(status,flush=True);last=status
    if len(completed)<len(plan['items']):time.sleep(30)
notes=['UV BASKI PAKETI - 9 DOSYA','Boyut: 200 x 233.419 mm (20 x 23.34 cm). Piksel yuvarlamasi nedeniyle cok kucuk farklar raporda bulunur.',
    'TIFF: ICC etiketli sRGB, aynasiz, dikey lens, tasmasiz. Dosya adindaki DPI hedef baski modu ve TIFF PPI degeridir.',
    'Lens pitch degerleri nominaldir, fiziksel kalibrasyon YAPILMADI. Kalibrasyon klasorundeki pitch seritlerini ayni cihaz/lens/malzeme/mod ile kullanin.',
    'RIP: %100 olcek; sayfaya sigdirma ve yeniden ornekleme kapali. Aynalama/baski yuzu ve beyaz katman sirasi uretim duzenine gore dogrulanmali.',
    '2400 PPI dosya icin gercek adreslenebilir baski modu ve RIP uyumu gerekir. Yazici DPI etiketi renkli kanal ayirma gucunu tek basina kanitlamaz.',
    'Kaynak: 2322x2710 piksel (~295 PPI / 20 cm). 2400 PPI yeni fotograf detayi uretmez; ince interlace dilimlerini adresler.',
    'Yerel AI gucu 1.0, tahmini yuzey kabartisi 0.35. Yuzey kabartisi isik/golgeden sanatsal tahmindir, olculmus geometri degildir.',
    'Tam gorunusler Blender ile kaynak fotograf boyutunda uretildi. Her dosyada Nr=Ne; ayni gorunusu kopyalayarak kanal sayisi artirilmadi.',
    'Beyaz alt baski maskeleri DPI basina ortaktir. Renkli resim olarak degil RIP beyaz kanali olarak tanimlayin.',
    'Hareketli PNG onizlemeleri Onizlemeler klasorunde, tekrar yuklenebilir ayarlar Ayarlar klasorunde.',
    'Dosya basina:']
for item in completed.values():notes.append(f"{item['file']} | {item['raster_size']} px | gercek kamera acisi {item['actual_angle_deg']:.4f} derece | en fazla kayma %{item['max_parallax_percent']:.3f}")
(dest/'ONCE_OKU_BASKI_NOTLARI.txt').write_text('\n'.join(notes),'utf-8')
print('ALL_NINE_COMPLETE',dest,flush=True)

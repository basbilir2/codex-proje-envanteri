import urllib.request,hashlib,json,concurrent.futures,zipfile,sys
from pathlib import Path
if len(sys.argv)!=2:raise SystemExit('Usage: python install-redraw-models.py <dedicated-model-folder>')
root=Path(sys.argv[1]).resolve();root.mkdir(parents=True,exist_ok=True)
manifest=json.loads((Path(__file__).resolve().parent/'redraw-models.json').read_text(encoding='utf-8'))
def download(item):
 target=root/item['name'];partial=target.with_suffix(target.suffix+'.partial')
 if target.exists() and hashlib.file_digest(target.open('rb'),'sha256').hexdigest()==item['sha256']:
  print(item['name']+' verified existing',flush=True);return
 req=urllib.request.Request(item['url'],headers={'User-Agent':'DTF-Studio-local-redraw'})
 with urllib.request.urlopen(req,timeout=90) as response,partial.open('wb') as f:
  total=0;mark=0
  while chunk:=response.read(4*1024*1024):
   f.write(chunk);total+=len(chunk)
   if total-mark>256*1024*1024:print(item['name']+' '+str(round(total/1e9,2))+'GB',flush=True);mark=total
 digest=hashlib.file_digest(partial.open('rb'),'sha256').hexdigest()
 if digest!=item['sha256']:raise RuntimeError('Checksum mismatch: '+item['name'])
 partial.replace(target);print(item['name']+' VERIFIED',flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for result in pool.map(download,manifest):pass
runtime=(root/'runtime-cpu').resolve();runtime.mkdir(exist_ok=True)
with zipfile.ZipFile(root/'sd-win-cpu.zip') as z:
 for member in z.infolist():
  if not (runtime/member.filename).resolve().is_relative_to(runtime):raise RuntimeError('Unsafe archive path')
 z.extractall(runtime)
print('All models downloaded and hash verified.',flush=True)

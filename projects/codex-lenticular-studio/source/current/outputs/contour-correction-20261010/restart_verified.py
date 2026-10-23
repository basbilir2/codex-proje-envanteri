from pathlib import Path
import json,hashlib,urllib.request,subprocess,sys,time,shutil
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
info_path=ROOT/'.studio/server.json';state_path=ROOT/'.studio/state.json'
def sha():
    with state_path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def snapshot(info):return json.load(urllib.request.urlopen(info['url'].replace('/?','/api/state?'),timeout=5))
before=json.loads(info_path.read_text());assert Path(before['root']).resolve()==ROOT.resolve()
state=snapshot(before)
inactive={'complete','cancelled','failed','interrupted'}
assert not any(j.get('status') not in inactive for j in state['jobs'].values()),'An active Studio job prevents restart'
baseline=sha();counts={key:len(state[key]) for key in ('assets','jobs','profiles')}
shutil.copy2(state_path,OUT/'backup/state-before-restart.json')
request=urllib.request.Request(before['url'].replace('/?','/api/shutdown?'),data=b'{}',headers={'Content-Type':'application/json'},method='POST')
json.load(urllib.request.urlopen(request,timeout=5));time.sleep(1)
with (OUT/'studio.log').open('w') as log:
    subprocess.Popen([sys.executable,'-m','lenticular.studio','--no-browser'],cwd=ROOT,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
after=None
for _ in range(20):
    time.sleep(.5)
    try:
        info=json.loads(info_path.read_text())
        if info['pid']==before['pid']:continue
        after=snapshot(info);break
    except (OSError,ValueError):pass
assert after is not None,'Studio did not return ready'
newcounts={key:len(after[key]) for key in counts}
record=dict(before_pid=before['pid'],after_pid=info['pid'],before_counts=counts,after_counts=newcounts,
    before_sha256=baseline,after_sha256=sha(),ready=True,advanced_default=after['defaults']['render']['repair_quality']=='advanced')
assert counts==newcounts and baseline==record['after_sha256'],'Studio state changed during restart'
(OUT/'restart-verification.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))

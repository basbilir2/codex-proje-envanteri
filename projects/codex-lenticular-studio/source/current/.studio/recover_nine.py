import json,time,urllib.request,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
plan_path=root/'.studio/production-nine.json';plan=json.loads(plan_path.read_text('utf-8'))
token=json.loads((root/'.studio/server.json').read_text('utf-8'))['url'].split('?t=')[1]
def call(path,body=None):
    req=urllib.request.Request('http://127.0.0.1:8765'+path,headers={'X-Studio-Token':token,'Content-Type':'application/json'},data=None if body is None else json.dumps(body).encode())
    return json.load(urllib.request.urlopen(req,timeout=20))
last=''
while True:
    state=call('/api/state')
    busy=[j for j in state['jobs'].values() if j['status'] in ['running','queued','cancel_requested']]
    if not busy:break
    status='; '.join(j.get('message','') for j in busy if j['status']=='running')
    if status!=last:print(status,flush=True);last=status
    time.sleep(30)
print('Reloading print fix; completed renders retained',flush=True)
call('/api/shutdown',{'ok':True});time.sleep(2)
with (root/'.studio/app.log').open('w') as out,(root/'.studio/app-errors.log').open('w') as err:
    subprocess.Popen([sys.executable,'-m','lenticular.studio','--no-browser'],cwd=root,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
for attempt in range(20):
    try:state=call('/api/state');break
    except (OSError,ValueError):time.sleep(.5)
else:raise RuntimeError('Server could not restart')
for item in plan['items'][5:]:
    old=item['job_id'];previous=state['jobs'][old]
    if previous['status']=='complete':continue
    stage='print' if previous.get('render_folder') and 'render_warnings' in previous else 'full'
    request=dict(asset_id=plan['asset_id'],stage=stage,render=item['render'],print=item['print'])
    if stage=='print':request['render_job']=old
    result=call('/api/jobs',request)
    item['original_job_id']=old;item['job_id']=result['id']
    print('QUEUED',item['name'],stage,result['id'],flush=True)
plan_path.write_text(json.dumps(plan,indent=2),'utf-8')
(Path(plan['folder'])/'uretim-plani.json').write_text(json.dumps(plan,indent=2),'utf-8')
subprocess.run([sys.executable,str(root/'.studio/package_nine.py')],cwd=root,check=True)
for path in (Path(plan['folder'])/'Ayarlar').glob('*.json'):
    values=json.loads(path.read_text('utf-8'));values['schema_version']=1;path.write_text(json.dumps(values,indent=2,ensure_ascii=False),'utf-8')
print('DELIVERY_READY',flush=True)

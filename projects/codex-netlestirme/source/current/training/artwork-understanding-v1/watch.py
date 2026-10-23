"""Download the actual understanding adapter/evidence, then stop the exact Pod."""
import pathlib,json,base64,time,sys,subprocess,argparse
ROOT=pathlib.Path(__file__).resolve().parent;PROJECT=ROOT.parents[1]
sys.path.insert(0,str(PROJECT/'app/dev-deps'));import requests
p=argparse.ArgumentParser();p.add_argument('--pod',required=True);p.add_argument('--deadline',type=int,required=True);args=p.parse_args()
assert args.pod.isalnum()
private=json.loads((PROJECT/'on-kontrol/.private/connection.json').read_text());base=private['base']+'/api/contents/workspace/artwork-understanding-v1/';headers={'Authorization':'token '+private['token']}
def fetch(name):
    r=requests.get(base+name,headers=headers,params={'format':'base64'},timeout=45)
    if r.status_code==404:return None
    r.raise_for_status();return base64.b64decode(r.json()['content'])
def save(name):
    b=fetch(name)
    if b:
        path=ROOT/name;path.parent.mkdir(exist_ok=True,parents=True);path.write_bytes(b)
    return b
saved=False;last=0
try:
    print('UNDERSTANDING_WATCHER_READY',flush=True)
    while time.time()<args.deadline-45:
        try:
            progress=fetch('progress.json')
            if progress:
                d=json.loads(progress)
                if d['steps']!=last:
                    last=d['steps'];(ROOT/'progress.json').write_bytes(progress);print('TRAIN_STEP='+str(last),flush=True)
            result=fetch('training-result.json')
            if result and not saved:
                (ROOT/'training-result.json').write_bytes(result)
                for name in ['adapter/adapter_config.json','adapter/adapter_model.safetensors']:assert save(name)
                saved=True;print('REAL_UNDERSTANDING_ADAPTER_SAVED',flush=True)
            job=fetch('job-status.json')
            if job:
                (ROOT/'job-status.json').write_bytes(job);break
        except (requests.RequestException,json.JSONDecodeError):pass
        time.sleep(8)
    for name in ['train.log','install.log','export.log','environment.txt','progress.json','training-result.json','adapter/adapter_config.json','adapter/adapter_model.safetensors','adapter/artwork-understanding-f16.gguf']:
        try:save(name)
        except requests.RequestException:pass
    for row in json.loads((ROOT/'heldout.json').read_text()):
        for ext in ['.json','.raw.txt','.review.raw.txt','.focus.png']:
            try:save('validation/'+row['id']+ext)
            except requests.RequestException:pass
finally:
    stop=subprocess.run([sys.executable,'-X','utf8',str(PROJECT/'on-kontrol/cloud.py'),'exec','runpodctl stop pod '+args.pod,'--wait','2'],capture_output=True,text=True,encoding='utf-8',timeout=30)
    (ROOT/'stop-command.log').write_text(stop.stdout+stop.stderr,encoding='utf-8')
    (ROOT/'watcher-result.json').write_text(json.dumps(dict(pod_id=args.pod,adapter_downloaded=saved,last_observed_step=last,stop_requested=True),indent=2))
    print('UNDERSTANDING_STOP_REQUESTED',flush=True)

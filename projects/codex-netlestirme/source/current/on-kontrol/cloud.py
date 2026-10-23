"""Development-only authenticated Jupyter transport. Never included in product."""
import argparse, base64, json, pathlib, sys, time
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'app'/'dev-deps'))
import requests
import websocket
cfg=json.loads((ROOT/'.private'/'connection.json').read_text())
BASE=cfg['base']; HEADERS={'Authorization':'token '+cfg['token']}
def api(method,path,**kwargs):
    r=requests.request(method,BASE+'/api/'+path,headers=HEADERS,timeout=45,**kwargs)
    r.raise_for_status()
    return r.json() if r.content else None

p=argparse.ArgumentParser()
p.add_argument('action',choices=['exec','tail','upload','download'])
p.add_argument('path')
p.add_argument('local',nargs='?')
p.add_argument('--wait',type=int,default=15)
a=p.parse_args()
if a.action=='tail':
    print(api('GET','contents/'+a.path,params={'format':'text'})['content'][-1000:])
elif a.action=='upload':
    api('PUT','contents/'+a.path,json={'type':'file','format':'base64','content':base64.b64encode(pathlib.Path(a.local).read_bytes()).decode()})
    print('AKTARILDI',a.path)
elif a.action=='download':
    data=api('GET','contents/'+a.path,params={'format':'base64'})
    dest=pathlib.Path(a.local);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(base64.b64decode(data['content']))
    print('KAYDEDILDI',dest)
else:
    terms=api('GET','terminals')
    name=terms[0]['name'] if terms else api('POST','terminals')['name']
    ws=websocket.create_connection(BASE.replace('https:','wss:')+'/terminals/websocket/'+name,header=HEADERS,origin=BASE,timeout=5)
    # Drain terminal replay before sending; do not print old logs or echoed credentials.
    ws.settimeout(0.4)
    try:
        while True: ws.recv()
    except websocket.WebSocketTimeoutException: pass
    ws.send(json.dumps(['stdin',a.path+'\n']))
    until=time.monotonic()+a.wait
    while time.monotonic()<until:
        try:
            value=json.loads(ws.recv())
            if value[0]=='stdout': print(value[1],end='',flush=True)
        except websocket.WebSocketTimeoutException: continue
    ws.close()

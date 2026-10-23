"""One bounded real request: region -> quick result -> persisted PNG. No large model."""
import hashlib,json,pathlib,re,struct,time,requests
ROOT=pathlib.Path(__file__).resolve().parent.parent
BASE='http://127.0.0.1:17861'
html=requests.get(BASE,timeout=10).text
token=re.search(r'APP_TOKEN="([a-f0-9]+)"',html).group(1)
headers={'Origin':BASE,'X-App-Token':token}
source=ROOT/'app/inputs/portrait-original.png'
original_hash=hashlib.sha256(source.read_bytes()).hexdigest()
# Invalid selection must fail without leaving the single-job lock occupied.
bad=requests.post(BASE+'/api/enhance',headers={**headers,'X-Region':json.dumps({'left':500,'top':500,'width':160,'height':180})},data=source.read_bytes(),timeout=20)
assert bad.status_code==400,bad.text
start=time.monotonic()
r=requests.post(BASE+'/api/enhance?mode=quick',headers={**headers,'X-Region':json.dumps({'left':128,'top':100,'width':160,'height':180})},data=source.read_bytes(),timeout=20)
r.raise_for_status();job=r.json()
while job['status']=='running' and time.monotonic()-start<15:
    time.sleep(.1);job=requests.get(BASE+'/api/jobs/'+job['id'],timeout=10).json()
assert job['status']=='completed',job
png=requests.get(BASE+job['output'],timeout=10);png.raise_for_status()
assert png.content[:8]==b'\x89PNG\r\n\x1a\n'
assert struct.unpack('>II',png.content[16:24])==(160,180)
saved=requests.post(BASE+'/api/edited/'+job['id'],headers=headers,data=png.content,timeout=10)
saved.raise_for_status()
assert requests.get(BASE+saved.json()['output'],timeout=10).content[:8]==png.content[:8]
assert hashlib.sha256(source.read_bytes()).hexdigest()==original_hash
assert requests.get(BASE+'/api/status',timeout=10).json()['active'] is None
report={'region':job['region'],'output':[160,180],'seconds':round(time.monotonic()-start,3),'png_received':True,'edited_saved':True,'invalid_region_rejected':True,'source_unchanged':True,'job_id':job['id']}
(ROOT/'on-kontrol/workflow-check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))

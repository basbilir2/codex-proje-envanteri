from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent;root=p.parents[1];state=root/'.studio/state.json'
data=json.loads(state.read_text());counts={k:len(data[k]) for k in ('assets','jobs','profiles')}
checksum=hashlib.sha256(state.read_bytes()).hexdigest()
record=dict(counts=counts,state_sha256=checksum,state_unchanged=checksum=='91bc310be45003e96902b2031f399bf7e9f680af238df0095215d00ee7b87219',studio_was_not_running=True,studio_relaunched=False)
(p/'state-verification.json').write_text(json.dumps(record,indent=2))
v=json.loads((p/'validation.json').read_text());v.update(candidate='scene',superseded=True,visual_acceptance=False)
(p/'validation.json').write_text(json.dumps(v,indent=2))
job=json.loads((p/'coupled/job.json').read_text());job['visual_acceptance']=dict(accepted_for_print=False,record='../visual-acceptance.json')
(p/'coupled/job.json').write_text(json.dumps(job,indent=2))
preview=p/'coupled/preview.html';html=preview.read_text(encoding='utf-8')
html=html.replace('</h1>','</h1><p style="color:#ffbf69">Görsel kabul geçmedi: şort kıvrımında kalan bozulma var. Baskı için onaylı değildir.</p>',1)
preview.write_text(html,encoding='utf-8')
print(json.dumps(record))

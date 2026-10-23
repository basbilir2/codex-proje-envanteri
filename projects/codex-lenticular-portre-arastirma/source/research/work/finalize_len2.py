"""Validate the package once, then finish one local baseline after the verified download.
No cloud/model APIs; no application/source writes; status remains in output files.
"""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path

p=Path(r'C:\Users\USER\Documents\Codex\2026-10-10\referenced-chatgpt-conversation-this-is-an\outputs\len 2')
def readl(path):return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]
def save(name,data):(p/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def status(state,**extra):
    save('checks/local_progress.json',dict(state=state,updated_at=time.strftime('%Y-%m-%d %H:%M:%S'),weights_trained=False,**extra))
def inventory():
    rows=[]
    for f in sorted(p.rglob('*')):
        if not f.is_file() or '__pycache__' in f.parts or f.name=='package_manifest.json' or f.suffix in ('.part','.gguf'):continue
        rows.append(dict(path=f.relative_to(p).as_posix(),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
    save('checks/package_manifest.json',rows)

sources=readl(p/'sources/manifest.jsonl');ids={r['source_id'] for r in sources}
modules=json.loads((p/'uzmanlik_programi/konu_haritasi.json').read_text(encoding='utf-8'))
chunks=readl(p/'rag/chunks.jsonl');exams=readl(p/'eval/uzmanlik_sinavi.jsonl')
errors=[]
for m in modules:
    for s in m['source_ids']:
        if s not in ids:errors.append('Missing curriculum source '+s)
if len({c['chunk_id'] for c in chunks})!=len(chunks):errors.append('Duplicate chunks')
if any(t['prompt'] in c['text'] for t in exams for c in chunks):errors.append('Exam prompt leaked into RAG')
if any(t['model_run'] or t['score'] is not None for t in exams):errors.append('Unrun exam marked scored')
cards=readl(p/'egitim_icerigi/yerel_bilgi_kartlari.jsonl')
record=json.loads((p/'egitim_icerigi/kaynak_kayitlari.json').read_text(encoding='utf-8'))
source_folder=Path(record['source_folder']);hashes={k:v for c in cards for k,v in c['source_sha256'].items()}
for rel,sha in hashes.items():
    if hashlib.sha256((source_folder/rel).read_bytes()).hexdigest()!=sha:errors.append('Source report changed: '+rel)
save('checks/expertise_validation.json',dict(status='FAIL' if errors else 'PASS',errors=errors,
 modules=len(modules),new_primary_notes=18,products=7,new_pilot_cases=len(exams),rag_chunks=len(chunks),
 source_report_hashes_checked=len(hashes),exam_prompts_not_in_rag=True,
 model_expertise_tested=False,weights_trained=False,physical_print_test_run=False))
if errors:
    status('PACKAGE_CHECK_FAILED',errors=errors);inventory();raise SystemExit(1)
status('WAITING_FOR_VERIFIED_MODEL',package_checks='PASS',download_can_continue_without_paid_model=True)
inventory()
deadline=time.monotonic()+7200
while not (p/'model/model_manifest.json').exists():
    if time.monotonic()>deadline:
        status('MODEL_DOWNLOAD_NOT_FINISHED',next_action='Inspect download log before retry.');raise SystemExit(2)
    time.sleep(15)
status('RUNNING_ONE_LOCAL_BASELINE',package_checks='PASS')
env=os.environ.copy();env['PYTHONIOENCODING']='utf-8'
cmd=[sys.executable,str(p/'tools/local_worker.py'),str(p/'runtime/requests/pilot_knowledge.json')]
try:
    result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',env=env,timeout=660)
    (p/'checks/baseline_driver_stderr.txt').write_text(result.stderr,encoding='utf-8')
    packet=json.loads(result.stdout) if result.returncode==0 else None
except (subprocess.TimeoutExpired,json.JSONDecodeError) as exc:
    packet=None
    (p/'checks/baseline_driver_stderr.txt').write_text(str(exc),encoding='utf-8')
usable=bool(packet and packet['metadata']['inference_run'] and packet['metadata'].get('exit_code')==0 and packet['summary'] and packet['route']=='ASTRA_REVIEW')
save('checks/local_baseline.json',dict(status='RESPONSE_READY_FOR_ASTRA_REVIEW' if usable else 'NEEDS_ASTRA',
  baseline_response=packet,quality_approved=False,domain_mastery_tested=False,model_finetuned=False,
  note='Tek API kullanmayan yerel yanıt kontrolü. Anlamsal doğruluk ve ileri uzmanlık onayı değildir.'))
cfg=json.loads((p/'runtime/config.json').read_text(encoding='utf-8'))
cfg['status']='baseline_response_pending_astra_review' if usable else 'baseline_needs_astra'
save('runtime/config.json',cfg)
job=json.loads((p/'training/job_spec.json').read_text(encoding='utf-8'))
job['baseline_inference_run']=bool(packet and packet['metadata']['inference_run'])
job['status']='LOCAL_BASELINE_PENDING_REVIEW' if usable else 'LOCAL_BASELINE_NEEDS_ASTRA'
job['training_started']=False;job['weights_trained']=False
save('training/job_spec.json',job)
status('LOCAL_BASELINE_PENDING_REVIEW' if usable else 'LOCAL_BASELINE_NEEDS_ASTRA',result='checks/local_baseline.json')
(p/'DURUM.md').write_text('# len 2 — Güncel durum\n\n'+
 ('Ücretsiz model indirildi ve kaynak özetiyle bir yerel yanıt üretildi. Yanıt Astra incelemesini bekliyor.' if usable else 'Model indirme sonrası yerel yanıt kontrolü Astra incelemesi gerektiriyor.')+
 '\n\nAPI çıkarımı yapılmadı. Özel ağırlık eğitimi ve Lenticular Studio işlem bağdaştırıcısı henüz tamamlanmadı. İleri uzmanlık veya token tasarrufu oranı doğrulanmadı.\n',encoding='utf-8')
inventory()
print(json.dumps(dict(status='LOCAL_BASELINE_PENDING_REVIEW' if usable else 'LOCAL_BASELINE_NEEDS_ASTRA',weights_trained=False)),flush=True)

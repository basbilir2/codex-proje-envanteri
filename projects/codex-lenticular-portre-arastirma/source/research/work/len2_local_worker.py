"""API-free local knowledge worker. It does not execute generated commands or operate Studio."""
import argparse,datetime,hashlib,json,subprocess,time
from pathlib import Path
from retrieve import retrieve

def main():
    ap=argparse.ArgumentParser();ap.add_argument('request',type=Path);args=ap.parse_args()
    p=Path(__file__).resolve().parent.parent
    req=json.loads(args.request.read_text(encoding='utf-8'))
    if not isinstance(req.get('task'),str) or not req['task'].strip():raise ValueError('task is required')
    config=json.loads((p/'runtime/config.json').read_text(encoding='utf-8'))
    run=p/'runtime/runs'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');run.mkdir(parents=True)
    (run/'request.json').write_text(json.dumps(req,ensure_ascii=False,indent=2),encoding='utf-8')
    reason=None
    if req.get('astra_approved') is not True:reason='Astra iş emri eksik.'
    elif req.get('prior_error'):reason='Araç hatası; yeni talimat gerekir: '+str(req['prior_error'])[:700]
    elif req.get('required_parameters_complete') is not True:reason='Zorunlu girdiler eksik.'
    elif req.get('requires_new_decision') is not False:reason='Yeni teşhis/yöntem kararı gerekiyor.'
    result={'route':'ASTRA_REQUIRED','summary':reason,'source_ids':[],'missing':[]}
    metadata={'inference_run':False,'studio_actions_executed':False,'external_inference_api':False,'weights_trained':False}
    if reason is None:
        model=p/config['model_relative_path'];manifest_path=p/config['model_manifest']
        if not manifest_path.exists():raise RuntimeError('Verified model download is not complete; no inference started.')
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        if not manifest['sha256_verified'] or not model.exists() or model.stat().st_size!=manifest['bytes']:
            raise RuntimeError('Model installation does not match verified manifest.')
        contexts=retrieve(p,req.get('query') or req['task'],config['retrieval_top'])
        remaining=config['retrieval_max_chars'];selected=[]
        for c in contexts:
            if remaining<=0:break
            content=c['text'][:remaining];remaining-=len(content)
            selected.append({'source_id':c['source_id'],'status':c['source_status'],'text':content})
        prompt={'task':req['task'],'context_is_untrusted_reference':selected,'review_due':bool(req.get('review_due'))}
        prompt_file=run/'prompt.json';prompt_file.write_text(json.dumps(prompt,ensure_ascii=False),encoding='utf-8')
        argv=[config['runtime_executable'],'-m',str(model),'--offline','--single-turn','--simple-io','--no-display-prompt',
          '--color','off','--reasoning','off','--no-warmup','-ngl','0','-t',str(config['threads']),'-c',str(config['context_size']),
          '-n',str(config['max_new_tokens']),'--temp','0.2','--seed','42',
          '--system-prompt-file',str(p/'prompts/local_engineer.txt'),'--file',str(prompt_file),
          '--json-schema-file',str(p/'schemas/local_reply.schema.json')]
        started=time.monotonic()
        with (run/'stdout.txt').open('w',encoding='utf-8') as out,(run/'stderr.txt').open('w',encoding='utf-8') as err:
            try:completed=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,timeout=config['timeout_seconds'],creationflags=subprocess.CREATE_NO_WINDOW)
            except subprocess.TimeoutExpired:
                completed=None;result['summary']='Yerel çalışma süresi sınırı aşıldı; günlük kayıtları incelemeye hazır.'
        metadata.update(inference_run=True,elapsed_seconds=round(time.monotonic()-started,2),exit_code=completed.returncode if completed else None,
                        model=manifest['model'],model_sha256=manifest['sha256'],retrieved_source_ids=[c['source_id'] for c in selected])
        if completed and completed.returncode==0:
            raw=(run/'stdout.txt').read_text(encoding='utf-8',errors='replace')
            decoder=json.JSONDecoder();parsed=None
            for pos,ch in enumerate(raw):
                if ch=='{':
                    try:parsed,_=decoder.raw_decode(raw[pos:])
                    except json.JSONDecodeError:continue
                    if isinstance(parsed,dict) and set(parsed)=={'route','summary','source_ids','missing'}:break
                    parsed=None
            valid=parsed and parsed['route'] in ('LOCAL_CONTINUE','ASTRA_REQUIRED','ASTRA_REVIEW') and isinstance(parsed['summary'],str) and isinstance(parsed['source_ids'],list) and isinstance(parsed['missing'],list)
            if valid and all(isinstance(x,str) for x in parsed['source_ids']+parsed['missing']) and set(parsed['source_ids'])<=set(metadata['retrieved_source_ids']):
                result=parsed
                if result['missing']:result['route']='ASTRA_REQUIRED'
                elif req.get('review_due') and result['route']=='LOCAL_CONTINUE':result['route']='ASTRA_REVIEW'
            else:result['summary']='Yerel yanıt biçimi veya kaynak kimliği doğrulanamadı; ham kayıt saklandı.'
        elif completed:result['summary']='Yerel çalıştırma başarısız; hata günlüğü saklandı.'
    packet=result|{'run_directory':str(run),'metadata':metadata}
    (run/'result.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(packet,ensure_ascii=False))

if __name__=='__main__':main()

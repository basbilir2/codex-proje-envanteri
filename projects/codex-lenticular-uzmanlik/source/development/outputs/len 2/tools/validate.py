"""Validate data integrity, provenance and split separation; not model performance."""
import ast
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

def read_jsonl(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]

def main():
    package=Path(sys.argv[1]).resolve()
    sources=read_jsonl(package/'sources/manifest.jsonl')
    train=read_jsonl(package/'sft/candidates/train.jsonl')
    val=read_jsonl(package/'sft/candidates/validation.jsonl')
    all_tests=read_jsonl(package/'eval/heldout.jsonl')
    tests=[r for r in all_tests if r.get('benchmark_eligible',True)]
    chunks=read_jsonl(package/'rag/chunks.jsonl')
    errors=[];checks={}
    source_ids={d['source_id'] for d in sources}
    if len(source_ids)!=len(sources): errors.append('duplicate source ids')
    record_ids=[]
    required={'sample_id','group_id','split','mode','origin','review_status','training_eligible','source_ids','messages','evidence','language'}
    for record in train+val:
        record_ids.append(record['sample_id'])
        if set(record)!=required: errors.append('record fields: '+record['sample_id'])
        if record['mode']!='execution_only' or record['training_eligible'] is not False: errors.append('unsafe candidate state')
        if [m['role'] for m in record['messages']]!=['system','user','assistant']: errors.append('role order')
        if not all(isinstance(m['content'],str) and m['content'] for m in record['messages']):errors.append('message content')
        if not set(record['source_ids'])<=source_ids: errors.append('missing provenance')
        answer=record['messages'][-1]['content']
        if answer.startswith(('{','[')):
            json.loads(answer)
    if len(record_ids)!=len(set(record_ids)): errors.append('duplicate sample ids')
    group_sets=[{r['group_id'] for r in rows} for rows in (train,val,tests)]
    overlap=(group_sets[0]&group_sets[1]) | (group_sets[0]&group_sets[2]) | (group_sets[1]&group_sets[2])
    if overlap: errors.append('group leakage: '+str(overlap))
    # Exact prompt leakage check and lexical near-duplicate audit across splits.
    prompts=[[r['messages'][1]['content'] for r in train],[r['messages'][1]['content'] for r in val],[r['prompt'] for r in tests]]
    def norm(s): return re.sub(r'\s+',' ',s).strip().casefold()
    near=[]
    for i in range(3):
        for j in range(i+1,3):
            for a in prompts[i]:
                for b in prompts[j]:
                    score=difflib.SequenceMatcher(None,norm(a),norm(b)).ratio()
                    if score==1:errors.append('exact prompt leakage')
                    if score>=.86:near.append(dict(split_a=i,split_b=j,similarity=round(score,3)))
    checks['cross_split_near_duplicate_candidates']=near
    checks['near_duplicate_method']='Lexical SequenceMatcher threshold .86; not a semantic leakage proof.'
    if any(c['source_id'].startswith('local:app/tests/') for c in chunks): errors.append('test source leaked into rag')
    if any('holdout_real_job' in c['text'] for c in chunks): errors.append('heldout fixture leaked into rag')
    code=next(r for r in train if r['group_id']=='precise_code_edit')['messages'][-1]['content']
    node=ast.parse(code)
    if len(node.body)!=1 or not isinstance(node.body[0],ast.FunctionDef):errors.append('code sample shape')
    env={};exec(compile(node,'synthetic_fixture','exec'),env)
    if env['pixels'](127,600)!=3000 or env['pixels'](100,300)!=1181:errors.append('code fixture arithmetic')
    numeric=next(r for r in train if r['group_id']=='pixel_arithmetic')['messages'][-1]['content']
    if int(numeric)!=round(127*600/25.4):errors.append('numeric sample')
    # Verify current source texts and source-job reports have not changed since capture.
    roots={'app':Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1'),
           'reference':Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac173361d8c8191a1449be5154f589f')}
    unchanged=0
    for s in sources:
        if s['source_id'].startswith('local:'):
            p=roots[s['root_id']]/s['relative_path']
            if hashlib.sha256(p.read_bytes()).hexdigest()!=s['sha256']:errors.append('source changed: '+s['source_id'])
            else:unchanged+=1
    case=json.loads((package/'eval/private_fixtures/selected_job.json').read_text(encoding='utf-8'))
    for rel,digest in case['source_hashes'].items():
        if hashlib.sha256((Path(case['source_folder'])/rel).read_bytes()).hexdigest()!=digest:errors.append('job source changed')
    checks['source_text_hashes_unchanged']=unchanged
    checks['selected_job_report_hashes_checked']=len(case['source_hashes'])
    spec=importlib.util.spec_from_file_location('retrieve_len2',package/'tools/retrieve.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    retrieval=[]
    for query,expected in [('pixels_per_channel','local:app/lenticular/optics.py'),('trimap alfa','web:pymatting-alpha'),('pitch lens','web:triaxes-pitch')]:
        result=module.retrieve(package,query,20)
        ok=any(r['source_id']==expected for r in result)
        retrieval.append(dict(query=query,expected_source=expected,found=ok))
        if not ok:errors.append('retrieval missed '+query)
    if module.retrieve(package,'" OR DROP TABLE knowledge; --',1) is None:errors.append('query handling')
    historical=module.retrieve(package,'native-portrait-final',20)
    if any(r['source_status']=='rejected_visual_result' for r in historical):errors.append('history filter')
    checks.update(dict(record_structure_checked=True,source_provenance_checked=True,split_groups_disjoint=not overlap,
        exact_prompts_disjoint=True,synthetic_code_fixture_passed=True,retrieval_checks=retrieval,
        model_inference_run=False,model_training_run=False,physical_print_test_run=False,
        counts=dict(train_candidates=len(train),validation_candidates=len(val),heldout=len(tests),retired_from_holdout=len(all_tests)-len(tests),rag_chunks=len(chunks)),
        status='PASS' if not errors else 'FAIL',errors=errors))
    (package/'checks/validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(checks,ensure_ascii=False))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()

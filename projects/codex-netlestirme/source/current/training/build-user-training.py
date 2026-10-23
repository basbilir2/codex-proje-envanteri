"""Prepare a diverse, grouped dataset from reviewed user references.
Copies/converts original document assets; never invents artwork or text.
"""
import collections,hashlib,json,pathlib,shutil,zipfile
root=pathlib.Path(__file__).resolve().parent
user=root/'user-assets-20261022';old=root/'pilot-20261022';out=root/'user-recovery-v2'
(out/'images').mkdir(parents=True,exist_ok=True)
inventory=json.loads((user/'inventory.json').read_text(encoding='utf-8'))
assets={r['id']:r for r in inventory['records']}
pairs=json.loads((user/'candidate-pairs.json').read_text(encoding='utf-8'))
instruction='Understand the existing design as a whole and reconstruct it as clean, flat, reusable artwork on a light neutral gray display background. Recover the complete composition, characteristic figures, logos, motifs, patterns, geometry, color relationships, solid fills and intended artistic detail. Preserve visible lettering when present. Separate the design from the photographed object, fabric texture, wrinkles, lighting, shadows, glare, perspective, blur and compression damage. Retain intentional artwork textures and dark design interiors. Center the complete recovered design with clear margins; do not add new content or redesign its identity.'
identity='Preserve this already-flat artwork exactly as a clean design. Keep its full composition, figures, pattern, lettering, colors, fills and intended artistic textures. Do not reinterpret, simplify, remove elements, or add content.'
component='Recover only the existing palm-tree illustration from this photographed garment as clean flat artwork on a light neutral gray display background. Preserve its full shape, silhouette, proportions, placement of both trees and original ink color. Remove the garment, photographic lighting, background, interface and surrounding lettering. Do not redesign or invent parts.'
train=[];validation=[];provenance=[]
def copy(path,name):
    dest=out/'images'/name;shutil.copyfile(path,dest)
    return 'images/'+name,hashlib.file_digest(dest.open('rb'),'sha256').hexdigest()
for split,collection in [('train',train),('validation',validation)]:
    for i,row in enumerate(json.loads((old/(split+'.json')).read_text(encoding='utf-8')),1):
        target,th=copy(old/row['image'],f'synthetic-{split}-{i}-target.png')
        source,sh=copy(old/row['edit_image'][0],f'synthetic-{split}-{i}-source.png')
        collection.append({'image':target,'edit_image':[source],'prompt':instruction})
        provenance.append({'id':f'synthetic-{split}-{i}','split':split,'task':'recover-complete-artwork','target_sha256':th,'source_sha256':sh,'image':target,'edit_image':[source]})
for pair in pairs:
    name=pair['id'];split=pair['split']
    target,th=copy(user/pair['image'],f'real-{name}-target.png')
    source,sh=copy(user/pair['source'],f'real-{name}-source.jpeg')
    task='recover-component' if name=='palms' else 'recover-complete-artwork'
    prompt=component if name=='palms' else instruction
    (validation if split=='validation' else train).append({'image':target,'edit_image':[source],'prompt':prompt})
    provenance.append({**pair,'split':split,'status':'visually_reviewed_corresponding_reference_not_pixel_aligned_master','task':task,'image':target,'edit_image':[source],'target_sha256':th,'source_sha256':sh})
for id in [1,33,58,76]:
    a=assets[id];name,h=copy(user/'raw'/a['file'],f'flat-preservation-{id:03d}'+pathlib.Path(a['file']).suffix)
    train.append({'image':name,'edit_image':[name],'prompt':identity})
    provenance.append({'id':f'flat-preservation-{id:03d}','split':'train','task':'preserve-already-flat-artwork','image':name,'edit_image':[name],'source_sha256':h,'target_sha256':h,'note':'Identity preservation example; not a photograph/reconstruction pair.'})
assert len(train)==19 and len(validation)==4
train_hashes={p[k] for p in provenance if p['split']=='train' for k in ['target_sha256','source_sha256']}
validation_hashes={p[k] for p in provenance if p['split']=='validation' for k in ['target_sha256','source_sha256']}
assert not train_hashes & validation_hashes
for name,rows in [('train',train),('validation',validation)]:
    (out/(name+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest={'schema':2,'kind':'general artwork recovery, real corresponding references plus replay and identity preservation','instruction':instruction,'training_count':len(train),'validation_count':len(validation),'training_tasks':dict(collections.Counter(p['task'] for p in provenance if p['split']=='train')),'heldout_real_designs':['mavi','wolf'],'unpaired_source_challenges':[assets[i] for i in [103,104,105]],'unpaired_clean_pool':[a for a in inventory['records'] if a['kind']=='image' and a['id']<=86],'excluded_duplicate_groups':inventory['exact_duplicate_groups'],'near_duplicate_candidates':inventory['near_duplicate_candidates'],'records':provenance,'source_archive_sha256':inventory['archive_sha256'],'source_text_hints_provided_to_model':False,'pdf_print_repetitions_are_independent_examples':False,'training_started':False}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
cfg=json.loads((old/'pilot.json').read_text(encoding='utf-8'))
for k in list(cfg):
    if k.startswith(('observed_','training_','checkpoint_','pod_','session_started','new_session','provider_','latest_','optimizer_steps','final_eval','quality_accepted','heldout_')):cfg.pop(k)
cfg.update(status='prepared_not_trained',training_cases=19,validation_cases=4,dataset_repeat=3,planned_optimizer_steps=57,checkpoint_file='step-57.safetensors',save_every=19,preserve_aspect_ratio=True,max_pixels=768*512,training_timeout_seconds=1050,evaluation_timeout_seconds=1500,initial_lora='initial-lora.safetensors',initial_lora_sha256='3727642c84e169791cea093623e82c3fd1ac5415d2b5875761bd5349e4e85f37',initial_optimizer_steps=48,planned_cumulative_optimizer_steps=105,require_stop_guard=True,session_spend_limit_usd=1.0,session_wall_limit_seconds=3300,evaluation_cases=[{'name':'mavi','image':'images/real-mavi-source.jpeg','width':1024,'height':640},{'name':'wolf','image':'images/real-wolf-source.jpeg','width':768,'height':1024},{'name':'heldout07','image':'images/synthetic-validation-1-source.png','width':768,'height':512}])
cfg.update(evaluate_updated_first=True,previous_evaluation_cases=[],evaluation_cases=[{'name':'wolf','image':'images/real-wolf-source.jpeg','width':768,'height':1024}],comparison_note='Whole-design training is the user priority. One heldout output checks usable new weights; no broad quality or before/after claim.')
(out/'pilot.json').write_text(json.dumps(cfg,indent=2)+'\n')
shutil.copyfile(old/'weights.json',out/'weights.json')
initial=old/'validation-20261022/checkpoints/step-48.safetensors'
assert hashlib.file_digest(initial.open('rb'),'sha256').hexdigest()==cfg['initial_lora_sha256']
shutil.copyfile(initial,out/'initial-lora.safetensors')
print(json.dumps({'train':len(train),'validation':len(validation),'new_real_train':9,'real_holdout':2,'flat_preservation':4,'synthetic_replay':6,'planned_steps':57,'model_training_started':False,'hash_overlap':False}))

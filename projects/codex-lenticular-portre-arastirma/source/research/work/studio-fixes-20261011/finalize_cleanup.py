import json,hashlib,zipfile
from pathlib import Path
base=Path(__file__).parent
manifest=base/'cleanup-manifest.json'
data=json.loads(manifest.read_text(encoding='utf-8'))
added=0
with zipfile.ZipFile(data['archive'],'a',compression=zipfile.ZIP_DEFLATED) as z:
    for row in data['records']:
        target=row.get('duplicate_of')
        if not target: continue
        p=Path(target)
        # Only mutable application source and live metadata changed after the original full comparison.
        if '.venv' in p.parts or not (p.suffix in ('.py','.js','.html','.json') and row['bytes']<2000000): continue
        if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']: continue
        source=Path(row['path'])
        if not source.exists(): continue
        payload=source.read_bytes()
        assert hashlib.sha256(payload).hexdigest()==row['sha256'], source
        entry='late-preserved/'+str(source.relative_to(Path(r'C:\Users\USER\Documents'))).replace('\\','/')
        z.writestr(entry,payload)
        assert hashlib.sha256(z.read(entry)).hexdigest()==row['sha256']
        row['duplicate_of']=None;row['archive_entry']=entry;added+=1
manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
roots=[Path(r'C:\Users\USER\Documents\lenticular'),Path(r'C:\Users\USER\Documents\lenticular2\lenticular2'),Path(r'C:\Users\USER\Documents\lenticular2\g-p-6ac08f7c2fe88191a25ea989c11950e1'),Path(r'C:\Users\USER\Documents\lenticular2\g-p-6ac173361d8c8191a1449be5154f589f')]
missing_roots=[str(p) for p in roots if not p.exists()]
roots=[p for p in roots if p.exists()]
expected={r['path']:r['bytes'] for r in data['records'] if any(Path(r['path']).is_relative_to(p) for p in roots)}
found={}
for root in roots:
    assert root.resolve()==root
    for p in root.rglob('*'):
        assert not p.is_symlink() and not p.is_junction(),p
        if p.is_file():
            assert 'sources' not in p.relative_to(root).parts, f'Protected reference: {p}'
            found[str(p)]=p.stat().st_size
assert found==expected, 'Candidate contents changed since backup'
result={'already_absent':missing_roots,'verified':True,'roots':[str(p) for p in roots],'files':len(found),'bytes':sum(found.values()),'unique_files':sum(bool(r.get('archive_entry')) for r in data['records']),'late_preserved':added,'archive':data['archive']}
(base/'cleanup-ready.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))


import os, json, time, pathlib, collections

BASE = pathlib.Path(r'C:\Users\USER\Documents\Codex\2026-10-22\pc')
ROOTS = [r'C:\siparis-takip', r'C:\workspace', r'C:\Users\USER\btakip', r'C:\Users\USER\btakip2', r'C:\Users\USER\btakip22', r'C:\Users\USER\source', r'C:\Users\USER\Documents', r'C:\Users\USER\Desktop', r'C:\Users\USER\Downloads', r'C:\Users\USER\OneDrive', r'C:\Users\USER\.codex\.chatgpt-projects']
SKIP = {'.git','node_modules','.venv','venv','env','__pycache__','.next','.nuxt','.cache','site-packages','dist-packages','bin','obj','.vs','.vscode','packages','bower_components','.pytest_cache','.mypy_cache','coverage','htmlcov','.tox','runtime','runtimes','python_embeded','python_embedded','python','node_modules_backup','Lib','libs','vendor'}
MARKERS = {'package.json','pyproject.toml','requirements.txt','Cargo.toml','go.mod','pom.xml','build.gradle','build.gradle.kts','CMakeLists.txt','composer.json','pubspec.yaml','setup.py','setup.cfg','deno.json','project.godot','mix.exs','Gemfile'}
projects=[]; repos=[]; errors=[]; filemeta=[]; skipped=collections.Counter(); visited=0; start=time.time()
for root in ROOTS:
    if not os.path.isdir(root): continue
    stack=[(root,0)]
    while stack:
        folder,depth=stack.pop(); visited+=1
        try:
            with os.scandir(folder) as it: entries=list(it)
        except OSError as e:
            errors.append({'path':folder,'error':type(e).__name__}); continue
        names={e.name for e in entries}
        markers=sorted(n for n in names if n in MARKERS or n.endswith(('.csproj','.sln','.slnx','.vcxproj','.fsproj')))
        if '.git' in names: repos.append(folder)
        if markers:
            item={'path':folder,'markers':markers,'git':'.git' in names,'gitignore':'.gitignore' in names}
            if 'package.json' in markers:
                try:
                    p=json.loads(pathlib.Path(folder,'package.json').read_text(encoding='utf-8-sig'))
                    item.update(name=p.get('name'),version=p.get('version'),private=p.get('private'))
                except (OSError,ValueError): pass
            projects.append(item)
        for e in entries:
            try:
                if e.is_symlink() or (e.stat(follow_symlinks=False).st_file_attributes & 0x400):
                    skipped['link_or_reparse']+=1; continue
                if e.is_dir(follow_symlinks=False):
                    if e.name in SKIP or e.name.lower() in {x.lower() for x in SKIP}: skipped[e.name]+=1
                    elif depth>=22: errors.append({'path':e.path,'error':'depth_limit'})
                    else: stack.append((e.path,depth+1))
                elif e.is_file(follow_symlinks=False):
                    st=e.stat(follow_symlinks=False)
                    filemeta.append([e.path,st.st_size,st.st_mtime])
            except OSError as ex: errors.append({'path':e.path,'error':type(ex).__name__})
result={'roots':ROOTS,'projects':projects,'repos':repos,'errors':errors,'skipped':dict(skipped),'visited_dirs':visited,'files':len(filemeta),'elapsed':round(time.time()-start,1),'scope':'User project locations only; dependency/runtime folders and reparse points skipped; archive contents not inspected.'}
(BASE/'work').mkdir(exist_ok=True)
(BASE/'work'/'inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(BASE/'work'/'filemeta.json').write_text(json.dumps(filemeta,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in {'projects','repos','roots'}},ensure_ascii=False))
print(json.dumps({'projects':projects,'repos':repos},ensure_ascii=False,indent=2))

"""Read-only drive inventory; identify Lenticular scopes without following links."""
import ctypes
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'knowledge/cleanup-20261012'
KNOWN=[r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1',r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac173361d8c8191a1449be5154f589f']
TOPIC=re.compile(r'lenticul|lentik[üu]ler|lentikuler|^len[ _-]?2$',re.I)
PROTECTED_PARTS={'.venv','venv','.git','sources','site-packages','node_modules'}
started=datetime.now(timezone.utc)
cutoff=started-timedelta(hours=24)
cutoff_ts=cutoff.timestamp()
OUT.mkdir(exist_ok=True)
roots={}; branches={}; named=[]; errors=[]; junctions=[]
dirs=files=0
last_progress=time.monotonic()
def initial():return dict(files=0,bytes=0,old_files=0,old_bytes=0,recent_files=0,recent_bytes=0,newest_timestamp=0)
def add(group,st):
    group['files']+=1;group['bytes']+=st.st_size
    stamp=max(st.st_ctime,st.st_mtime)
    group['newest_timestamp']=max(group['newest_timestamp'],stamp)
    label='recent' if stamp>=cutoff_ts else 'old'
    group[label+'_files']+=1;group[label+'_bytes']+=st.st_size
drives=[f'{chr(65+i)}:\\' for i in range(26) if ctypes.windll.kernel32.GetLogicalDrives()&(1<<i)]
stack=[(d,None) for d in drives]
known={os.path.normcase(p) for p in KNOWN}
with (OUT/'files.jsonl').open('w',encoding='utf-8') as detail:
    while stack:
        path,scope=stack.pop()
        dirs+=1
        try:
            with os.scandir(path) as entries:
                for e in entries:
                    try:
                        is_dir=e.is_dir(follow_symlinks=False)
                        if is_dir:
                            st=e.stat(follow_symlinks=False)
                            if st.st_file_attributes&0x400:
                                junctions.append(e.path);continue
                            next_scope=scope
                            if next_scope is None and (TOPIC.search(e.name) or os.path.normcase(e.path) in known):
                                next_scope=e.path
                                roots[next_scope]=initial()
                            stack.append((e.path,next_scope))
                        else:
                            files+=1
                            if not scope and not TOPIC.search(e.name):continue
                            st=e.stat(follow_symlinks=False)
                            if st.st_file_attributes&0x400:continue
                            record=dict(path=e.path,bytes=st.st_size,created_utc=datetime.fromtimestamp(st.st_ctime,timezone.utc).isoformat(),modified_utc=datetime.fromtimestamp(st.st_mtime,timezone.utc).isoformat(),recent=max(st.st_ctime,st.st_mtime)>=cutoff_ts,scope=scope)
                            if scope:
                                add(roots[scope],st)
                                rel=os.path.relpath(e.path,scope)
                                first=rel.split(os.sep)[0] if os.sep in rel else '[root files]'
                                branch=os.path.join(scope,first)
                                add(branches.setdefault(branch,initial()),st)
                                # Retain individual metadata outside package/runtime
                                # trees for a later exact deletion allowlist.
                                if not any(p.casefold() in PROTECTED_PARTS for p in Path(rel).parts):
                                    detail.write(json.dumps(record,ensure_ascii=False)+'\n')
                            else:named.append(record)
                    except OSError as exc:errors.append(dict(path=e.path,error=str(exc)))
        except OSError as exc:errors.append(dict(path=path,error=str(exc)))
        if time.monotonic()-last_progress>25:
            print(f'Inventory: {dirs} directories, {files} filenames; {len(roots)} Lenticular scopes.',flush=True)
            last_progress=time.monotonic()
report=dict(started_utc=started.isoformat(),cutoff_utc=cutoff.isoformat(),drives=drives,scanned_directories=dirs,scanned_filenames=files,roots=roots,branches=branches,named_files=named,access_errors=errors,skipped_reparse_points=junctions,policy='Read only. Recent means created OR modified within the previous 24 hours. No link traversal. No deletion.')
(OUT/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
summary=dict(cutoff_utc=report['cutoff_utc'],scanned_directories=dirs,scanned_filenames=files,access_errors=len(errors),scopes=[dict(path=p,**v) for p,v in sorted(roots.items(),key=lambda i:i[1]['bytes'],reverse=True)],standalone_lenticular_files=len(named))
print(json.dumps(summary,ensure_ascii=True,indent=2),flush=True)

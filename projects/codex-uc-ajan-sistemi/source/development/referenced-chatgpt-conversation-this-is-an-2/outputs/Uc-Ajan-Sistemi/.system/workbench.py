"""Source checkpoints, bounded project checks, browser evidence and distributable builds."""
import ast
from contextlib import closing
import difflib
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import mimetypes
import os
from pathlib import Path
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import threading
import time
from urllib.parse import unquote, urlparse
from urllib.request import urlopen
import uuid
import zipfile

SYSTEM=Path(__file__).resolve().parent
SKIP={'.git','.system','node_modules','.venv','venv','__pycache__','.next','dist','build','bin','obj','Library','Temp','Logs','data','user-data','storage','uploads','backups'}
SOURCE={'.html','.css','.scss','.js','.mjs','.cjs','.jsx','.ts','.tsx','.vue','.svelte','.py','.cs','.csproj','.sln','.props','.targets','.xaml','.resx','.fs','.vb','.c','.h','.cpp','.hpp','.rs','.toml','.lock','.go','.mod','.sum','.java','.kt','.kts','.gradle','.xml','.yaml','.yml','.md','.txt','.svg','.png','.jpg','.jpeg','.webp','.gif','.ico','.gd','.tscn','.tres','.godot','.unity','.prefab','.shader','.glsl','.wgsl','.dart','.sh','.ps1','.cmd','.bat'}
JSON_SOURCE={'package.json','package-lock.json','composer.json','app.json','manifest.json','studio-checks.json','jsconfig.json','launchsettings.json','appsettings.example.json'}
SOURCE.update({'.blend','.glb','.gltf','.obj','.mtl','.fbx','.bin','.wav','.ogg','.mp3','.cfg'})
JSON_SOURCE.add('model-report.json')

def digest(raw):return hashlib.sha256(raw).hexdigest()
def clean_environment():
    allowed={'PATH','PATHEXT','SYSTEMROOT','WINDIR','COMSPEC','TEMP','TMP','APPDATA','LOCALAPPDATA','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMW6432','USERPROFILE','JAVA_HOME','ANDROID_HOME','ANDROID_SDK_ROOT','DOTNET_ROOT'}
    env={k:v for k,v in os.environ.items() if k.upper() in allowed}
    env.update(PYTHONUTF8='1',PYTHONIOENCODING='utf-8',CI='1',HOST='127.0.0.1',
               DOTNET_NOLOGO='1',DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1')
    return env
def public(path):
    sensitive=re.search(r'(^|[-_.])(secret|credential|password|token|data|veri|database|customers|orders|sessions|users)([-_.]|$)',path.name,re.I)
    return not any(p in SKIP or p.startswith('.') for p in path.parts) and not sensitive and not path.name.lower().startswith('appsettings.') and path.suffix.lower() not in {'.key','.pem','.pfx','.db','.sqlite','.sqlite3','.csv','.xlsx','.xls'}
def source(path):
    if path.name in {'.gitignore','.editorconfig','.env.example'}:return True
    return public(path) and (path.suffix.lower() in SOURCE or path.name.lower() in JSON_SOURCE or (path.suffix=='.json' and path.name.startswith('tsconfig')))

class Workbench:
    def __init__(self,data):
        self.data=Path(data).resolve();self.db=self.data/'studio.sqlite';self.store=self.data/'workbench'
        self.store.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock();self.processes={};self.servers={};self.sdk_cache=None

    def project(self,workspace):
        root=Path(workspace).resolve(strict=True)
        with closing(sqlite3.connect(self.db)) as db:
            rows=db.execute("SELECT id,workspace FROM conversations WHERE mode='work'").fetchall()
        match=next((cid for cid,folder in rows if Path(folder).resolve()==root),None)
        if not match or root==Path(root.anchor) or root==SYSTEM or root.is_relative_to(SYSTEM):
            raise ValueError('Yalnız bu uygulamada açılmış çalışma klasöründe işlem yapılabilir.')
        return root,match

    def safe(self,root,relative,must_exist=False):
        rel=Path(relative)
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('Proje dışına erişilemez.')
        path=(root/rel).resolve(strict=must_exist)
        if not path.is_relative_to(root) or any(p.startswith('.') and p not in {'.gitignore','.editorconfig','.env.example'} for p in rel.parts):
            raise ValueError('Bu yola erişilemez.')
        return path

    def inventory(self,root):
        result={};total=0
        for folder,dirs,names in os.walk(root,followlinks=False):
            dirs[:]=sorted(n for n in dirs if n not in SKIP and not n.startswith('.') and not (Path(folder)/n).is_symlink())
            for name in sorted(names):
                p=Path(folder)/name;rel=p.relative_to(root)
                if not source(rel) or p.is_symlink():continue
                resolved=p.resolve()
                if not resolved.is_relative_to(root):continue
                total+=p.stat().st_size
                if total>256*1024*1024 or len(result)>=5000:raise ValueError('Kaynak sürüm kaydı sınırı aşıldı (256 MB / 5000 dosya). Değişiklik yapılmadan duruldu.')
                result[rel.as_posix()]={'sha256':digest(p.read_bytes()),'size':p.stat().st_size}
        return result

    def fingerprint(self,inventory):return digest(json.dumps(inventory,sort_keys=True).encode())

    def versions(self,workspace):
        root,cid=self.project(workspace);folder=self.store/cid/'versions';result=[]
        for file in folder.glob('*.json') if folder.exists() else []:
            m=json.loads(file.read_text(encoding='utf-8'))
            result.append({k:m[k] for k in ('id','label','created','fingerprint','file_count')})
        return sorted(result,key=lambda x:x['created'],reverse=True)

    def checkpoint(self,workspace,label='Kaynak kaydı'):
        with self.lock:
            root,cid=self.project(workspace);items=self.inventory(root);fp=self.fingerprint(items)
            existing=self.versions(workspace)
            if existing and existing[0]['fingerprint']==fp:return dict(existing[0],reused=True)
            folder=self.store/cid/'versions';folder.mkdir(parents=True,exist_ok=True)
            vid=uuid.uuid4().hex
            manifest={'id':vid,'label':str(label)[:100],'created':time.time(),'fingerprint':fp,'file_count':len(items),'files':items}
            with zipfile.ZipFile(folder/(vid+'.zip'),'w',zipfile.ZIP_DEFLATED) as archive:
                for name,meta in items.items():
                    path=self.safe(root,name,True);raw=path.read_bytes()
                    if digest(raw)!=meta['sha256']:raise ValueError('Kayıt sırasında dosya değişti; yeniden kayıt gerekiyor.')
                    archive.writestr(name,raw)
            (folder/(vid+'.json')).write_text(json.dumps(manifest,ensure_ascii=False),encoding='utf-8')
            return {k:manifest[k] for k in ('id','label','created','fingerprint','file_count')}

    def manifest(self,cid,vid):
        if not re.fullmatch('[a-f0-9]{32}',vid):raise ValueError('Geçersiz sürüm.')
        return json.loads((self.store/cid/'versions'/(vid+'.json')).read_text(encoding='utf-8'))

    def diff(self,workspace,vid):
        root,cid=self.project(workspace);target=self.manifest(cid,vid);current=self.inventory(root)
        changes=[];snippets=[]
        with zipfile.ZipFile(self.store/cid/'versions'/(vid+'.zip')) as archive:
            for name in sorted(set(current)|set(target['files'])):
                a=current.get(name,{}).get('sha256');b=target['files'].get(name,{}).get('sha256')
                if a==b:continue
                changes.append({'path':name,'action':'geri getir' if a is None else 'yeni dosyayı güvenlik kaydına taşı' if b is None else 'önceki içeriği geri getir'})
                if len(snippets)<8 and Path(name).suffix in {'.html','.css','.js','.ts','.py','.cs','.md','.json'}:
                    old=archive.read(name).decode('utf-8','replace').splitlines() if b else []
                    new=self.safe(root,name,True).read_text(encoding='utf-8',errors='replace').splitlines() if a else []
                    snippets.append('\n'.join(list(difflib.unified_diff(new,old,fromfile='Şimdi/'+name,tofile='Seçilen/'+name))[:120]))
        return {'version':vid,'expected':self.fingerprint(current),'changes':changes,'diff':'\n\n'.join(snippets)[:24000]}

    def restore(self,workspace,vid,expected):
        with self.lock:
            root,cid=self.project(workspace);current=self.inventory(root)
            if self.fingerprint(current)!=expected:raise ValueError('Önizlemeden sonra dosyalar değişti. Geri alma listesini tekrar aç.')
            target=self.manifest(cid,vid);backup=self.checkpoint(workspace,'Geri alma öncesi güvenlik kaydı')
            recovery=self.store/cid/'recovered'/uuid.uuid4().hex
            with zipfile.ZipFile(self.store/cid/'versions'/(vid+'.zip')) as archive:
                # Validate all targets before any mutation; live data and secret files are outside this inventory.
                for name,meta in target['files'].items():
                    if not source(Path(name)):raise ValueError('Kaynak dışı dosya kaydı reddedildi.')
                    self.safe(root,name)
                    if digest(archive.read(name))!=meta['sha256']:raise ValueError('Sürüm arşivi doğrulanamadı.')
                for name in set(current)-set(target['files']):
                    p=self.safe(root,name,True);dest=(recovery/name).resolve()
                    if not dest.is_relative_to(recovery.resolve()):raise ValueError('Geçersiz güvenlik yolu.')
                    dest.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(p),str(dest))
                for name in target['files']:
                    p=self.safe(root,name);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(archive.read(name))
            actual=self.inventory(root)
            if self.fingerprint(actual)!=target['fingerprint']:raise ValueError('Geri alma doğrulanamadı; güvenlik kaydı korundu.')
            self.checkpoint(workspace,'Geri alındı: '+target['label'])
            return {'restored':True,'safety_version':backup['id'],'fingerprint':target['fingerprint']}

    def sdk(self):
        if self.sdk_cache:return self.sdk_cache
        edge=Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Microsoft/Edge/Application/msedge.exe'
        chrome=Path(os.environ.get('ProgramFiles','C:/Program Files'))/'Google/Chrome/Application/chrome.exe'
        unity=Path(os.environ.get('ProgramFiles','C:/Program Files'))/'Unity/Hub/Editor'
        unity_exes=list(unity.glob('*/Editor/Unity.exe')) if unity.exists() else []
        blender_exes=list((Path(os.environ.get('ProgramFiles','C:/Program Files'))/'Blender Foundation').glob('Blender */blender.exe'))
        android=Path(os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT') or Path(os.environ.get('LOCALAPPDATA',''))/'Android/Sdk')
        self.sdk_cache={'node':shutil.which('node'),'npm':shutil.which('npm.cmd' if os.name=='nt' else 'npm'),
            'python':sys.executable,'git':shutil.which('git'),'dotnet':shutil.which('dotnet'),
            'browser':str(edge if edge.is_file() else chrome) if edge.is_file() or chrome.is_file() else None,
            'browser_automation':(SYSTEM/'automation/node_modules/playwright-core/package.json').is_file(),
            'desktop_automation':os.name=='nt' and (SYSTEM/'automation/desktop.ps1').is_file(),
            'pyinstaller':(SYSTEM/'automation/python-packages/PyInstaller/__main__.py').is_file() or importlib.util.find_spec('PyInstaller') is not None,
            'godot':shutil.which('godot') or shutil.which('godot4'),'unity':str(unity_exes[-1]) if unity_exes else None,
            'blender':shutil.which('blender') or (str(sorted(blender_exes)[-1]) if blender_exes else None),
            'android_sdk':str(android) if android.is_dir() else None,'java':shutil.which('java')}
        return self.sdk_cache

    def inspect(self,workspace):
        root,cid=self.project(workspace);package={}
        if (root/'package.json').is_file():package=json.loads((root/'package.json').read_text(encoding='utf-8'))
        csproj=[p.name for p in root.glob('*.csproj')]
        stack='node' if package else 'dotnet' if csproj else 'godot' if (root/'project.godot').exists() else 'unity' if (root/'ProjectSettings/ProjectVersion.txt').exists() else 'web' if (root/'index.html').exists() else 'python' if (root/'main.py').exists() or (root/'app.py').exists() else 'source'
        if stack=='source' and any((root/'assets3d').glob('*/model.glb')):stack='blender'
        tools=dict(self.sdk())
        project_python=next((root/p for p in ('.venv/Scripts/python.exe','venv/Scripts/python.exe') if (root/p).is_file()),None)
        if project_python:tools['python']=str(project_python)
        return {'workspace':str(root),'stack':stack,'scripts':package.get('scripts',{}),'dependencies':sorted(set(package.get('dependencies',{}))|set(package.get('devDependencies',{}))),
                'dotnet_projects':csproj,'tools':tools,'check_steps':(root/'studio-checks.json').is_file(),
                'note':'Yalnız yerel araçlar kullanılır; eksik SDK kurulmuş gibi gösterilmez.'}

    def command(self,args,root,timeout=180):
        env=clean_environment()
        if 'PyInstaller' in args and (SYSTEM/'automation/python-packages/PyInstaller/__main__.py').is_file():
            env['PYTHONPATH']=str(SYSTEM/'automation/python-packages')
        if os.name=='nt' and str(args[0]).lower().endswith(('.cmd','.bat')):args=[env.get('COMSPEC','cmd.exe'),'/d','/c',*args]
        process=subprocess.Popen([str(a) for a in args],cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                                 creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:raw,_=process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill();raw,_=process.communicate();return {'passed':False,'exit_code':None,'error':'İşlem süresi doldu.','output':raw.decode('utf-8','replace')[-12000:]}
        return {'passed':process.returncode==0,'exit_code':process.returncode,'output':raw.decode('utf-8','replace')[-12000:]}

    def preview_start(self,workspace):
        with self.lock:
            root,cid=self.project(workspace)
            if cid in self.servers:return self.servers[cid]['url']
            if cid in self.processes and self.processes[cid]['process'].poll() is None:return self.processes[cid]['url']
            info=self.inspect(workspace)
            # Built web output can be served without running any project backend.
            entry=next((root/p for p in (('dist/index.html','build/index.html') if info['stack']=='node' else ('index.html',)) if (root/p).is_file()),None)
            if entry:
                base=entry.parent
                class Handler(BaseHTTPRequestHandler):
                    def log_message(self,*_):pass
                    def do_GET(self):
                        relative=unquote(urlparse(self.path).path).lstrip('/') or 'index.html'
                        if relative=='favicon.ico' and not (base/relative).exists():self.send_response(204);self.end_headers();return
                        path=(base/relative).resolve()
                        if not path.is_relative_to(base) or not public(path.relative_to(base)) or not path.is_file():
                            self.send_response(404);self.end_headers();return
                        raw=path.read_bytes();self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(path.name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(raw)));self.end_headers()
                        try:self.wfile.write(raw)
                        except OSError:pass
                server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
                threading.Thread(target=server.serve_forever,daemon=True).start()
                url=f'http://127.0.0.1:{server.server_port}'
                self.servers[cid]={'server':server,'url':url};return url
            if info['stack']!='node' or 'dev' not in info['scripts']:raise ValueError('Otomatik web önizlemesi için index.html, web derlemesi veya desteklenen dev komutu gerekiyor.')
            if not (root/'node_modules').exists():raise ValueError('Proje bağımlılıkları kurulu değil. Önce çalışma motorunda gerekli paket kurulumunu yap.')
            if not ({'vite','next'}&set(info['dependencies'])):raise ValueError('Bu sunucu için otomatik başlatma tarifi yok; ajan uygun çalıştırma adımını belirlemeli.')
            with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
            args=[info['tools']['npm'],'run','dev','--','--hostname' if 'next' in info['dependencies'] else '--host','127.0.0.1','--port',str(port)]
            if os.name=='nt':args=[os.environ.get('COMSPEC','cmd.exe'),'/d','/c',*args]
            logdir=self.store/cid;logdir.mkdir(parents=True,exist_ok=True)
            log=(logdir/'preview.log').open('ab')
            proc=subprocess.Popen(args,cwd=root,env=clean_environment(),stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            url=f'http://127.0.0.1:{port}';self.processes[cid]={'process':proc,'log':log,'url':url}
            for _ in range(80):
                if proc.poll() is not None:raise ValueError('Önizleme sunucusu kapandı: '+(logdir/'preview.log').read_text(errors='replace')[-3000:])
                try:
                    with urlopen(url,timeout=.5):return url
                except OSError:time.sleep(.25)
            raise ValueError('Önizleme sunucusu hazır olmadı.')

    def browser(self,workspace,steps=None,width=1280,height=800,include_image=False):
        root,cid=self.project(workspace);sdk=self.sdk()
        if not sdk['node'] or not sdk['browser'] or not sdk['browser_automation']:raise ValueError('Tarayıcı kontrol aracı kurulu değil.')
        if steps is None:
            recipe=root/'studio-checks.json'
            steps=json.loads(recipe.read_text(encoding='utf-8')).get('steps',[]) if recipe.is_file() else []
        if not isinstance(steps,list) or len(steps)>20:raise ValueError('En fazla 20 tarayıcı adımı kullanılabilir.')
        run=uuid.uuid4().hex;folder=self.store/cid/'checks';folder.mkdir(parents=True,exist_ok=True)
        screenshot=folder/(run+'.png')
        payload={'url':self.preview_start(workspace),'browser':sdk['browser'],'screenshot':str(screenshot),'steps':steps,'width':width,'height':height}
        result=subprocess.run([sdk['node'],str(SYSTEM/'automation/browser.cjs')],input=json.dumps(payload).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=clean_environment(),timeout=180,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:record=json.loads(result.stdout)
        except ValueError:raise ValueError('Tarayıcı kontrolü çalışmadı: '+result.stderr.decode('utf-8','replace')[-2000:])
        record.update(id=run,kind='browser',created=time.time(),fingerprint=self.fingerprint(self.inventory(root)),
                      acceptance=digest(json.dumps(steps,sort_keys=True).encode()))
        (folder/(run+'.json')).write_text(json.dumps(record,ensure_ascii=False),encoding='utf-8')
        return record

    def history(self,workspace):
        _,cid=self.project(workspace);folder=self.store/cid/'checks'
        records=[json.loads(p.read_text(encoding='utf-8')) for p in folder.glob('*.json')] if folder.exists() else []
        return sorted(records,key=lambda x:x['created'],reverse=True)[:30]

    def verify(self,workspace,steps_override=None,desktop_override=None):
        info=self.inspect(workspace);root,_=self.project(workspace);fp=self.fingerprint(self.inventory(root))
        if info['stack']=='blender':
            last=next((r for r in self.history(workspace) if r.get('kind')=='blender'),None)
            if last:return self.blender(workspace,**last['recipe'])
            return {'passed':False,'unsupported':True,'errors':['Önce blender_asset ile gerçek model üretilmeli.']}
        recipe=root/'studio-checks.json'
        recipe_data=json.loads(recipe.read_text(encoding='utf-8')) if recipe.is_file() else {}
        steps=steps_override if steps_override is not None else recipe_data.get('steps',[])
        desktop_config=desktop_override if desktop_override is not None else recipe_data.get('desktop')
        expected='desktop' if desktop_config and info['stack'] in ('dotnet','python') else 'browser' if info['stack'] in ('web','node') else 'python-syntax' if info['stack']=='python' else 'build'
        acceptance=digest(json.dumps(desktop_config.get('steps',[]) if expected=='desktop' else steps,sort_keys=True).encode())
        for old in self.history(workspace):
            if old.get('fingerprint')==fp and old.get('kind')==expected and (expected not in ('browser','desktop') or old.get('acceptance')==acceptance):
                return dict(old,reused=True)
        if expected=='desktop':
            package=self.action(workspace,'package')
            if not package.get('passed'):return package
            executables=package.get('executables',[])
            if desktop_config.get('executable'):executables=[p for p in executables if Path(p).name==desktop_config['executable']]
            if len(executables)!=1:raise ValueError('Masaüstü kontrolü için tek bir paket EXE seçilmeli (desktop.executable).')
            return self.desktop(workspace,executables[0],desktop_config.get('steps',[]),desktop_config.get('window_title',''))
        if info['stack'] in ('web','node'):
            if info['stack']=='node' and 'build' in info['scripts']:
                built=self.action(workspace,'build')
                if not built['passed']:return built
            return self.browser(workspace,steps=steps)
        if info['stack']=='python':
            errors=[]
            for name in self.inventory(root):
                if name.endswith('.py'):
                    try:ast.parse(self.safe(root,name,True).read_text(encoding='utf-8-sig'),filename=name)
                    except (SyntaxError,UnicodeError) as e:errors.append(str(e))
            return self.save_check(workspace,{'kind':'python-syntax','passed':not errors,'errors':errors,'limitation':'Sözdizimi kontrolü; masaüstü arayüzünün çalıştığını kanıtlamaz.'})
        if info['stack']=='dotnet':
            result=self.action(workspace,'build')
            result['limitation']='Derleme kontrolü; GUI için studio-checks.json içinde desktop adımları tanımlanmalı.'
            return result
        return {'passed':False,'unsupported':True,'kind':'unverified','errors':['Bu proje türünde otomatik canlı kontrol tarifi yok. Ajan ilgili SDK ve çalıştırma tarifini tamamlamalı.'],'stack':info['stack']}

    def save_check(self,workspace,record):
        root,cid=self.project(workspace);folder=self.store/cid/'checks';folder.mkdir(parents=True,exist_ok=True)
        record.update(id=uuid.uuid4().hex,created=time.time(),fingerprint=self.fingerprint(self.inventory(root)))
        (folder/(record['id']+'.json')).write_text(json.dumps(record,ensure_ascii=False),encoding='utf-8');return record

    def action(self,workspace,action='build',entry=''):
        if action not in ('build','test','package'):raise ValueError('Geçersiz proje işlemi.')
        root,cid=self.project(workspace);info=self.inspect(workspace);sdk=info['tools'];stack=info['stack']
        if action=='test' and stack=='node' and re.search(r'(--watch|vitest\s*$|jest\s*$)',info['scripts'].get('test','')):
            raise ValueError('Test komutu izleme modunda. Tek seferlik test komutu tanımlanmalı.')
        fingerprint=self.fingerprint(self.inventory(root))
        for old in self.history(workspace):
            if old.get('fingerprint')==fingerprint and old.get('kind')==action and (not old.get('artifact') or Path(old['artifact']).is_file()):return dict(old,reused=True)
        folder=self.store/cid/'artifacts';folder.mkdir(parents=True,exist_ok=True);builddir=folder/uuid.uuid4().hex
        output_root=root;note='Kaynak kod paketi';checks=[]
        if stack=='node':
            script='build' if action=='package' else action
            if script not in info['scripts']:raise ValueError(f'package.json içinde {script} komutu yok.')
            if re.search(r'\b(deploy|upload)\b|--publish|npm\s+publish',info['scripts'][script],re.I):raise ValueError('Yayınlama içeren komut otomatik çalıştırılmaz.')
            result=self.command([sdk['npm'],'run',script],root,240);checks.append(result)
            if action=='package':
                output_root=next((root/p for p in ('dist','build','out') if (root/p).is_dir()),None)
                if output_root is None:result=dict(result,passed=False,error='Derleme çıktı klasörü bulunamadı (dist/build/out).')
            note='Web derlemesi' if action=='package' else script
        elif stack=='dotnet':
            if not sdk['dotnet']:raise ValueError('.NET SDK kurulu değil.')
            projects=info['dotnet_projects']
            if not entry and len(projects)!=1:raise ValueError('Derlenecek .csproj dosyasını belirt.')
            project=self.safe(root,entry or projects[0],True)
            if project.suffix!='.csproj':raise ValueError('.csproj seçmelisin.')
            cmd=[sdk['dotnet'],'publish' if action=='package' else action,str(project),'-c','Release']
            if action=='package':cmd+=['-o',str(builddir)];output_root=builddir
            result=self.command(cmd,root,300);checks.append(result);note='Windows/.NET yayın çıktısı; uygun .NET çalışma zamanı gerekir.'
        elif stack=='python':
            if action=='build':return self.verify(workspace)
            if action=='test':result=self.command([sdk['python'],'-m','pytest','-q'],root,180);checks.append(result)
            else:
                if not sdk['pyinstaller']:raise ValueError('EXE paketi için PyInstaller kurulu değil. Gerekli kurulum çalışma motorunda onaylanarak yapılmalı.')
                file=self.safe(root,entry or ('main.py' if (root/'main.py').exists() else 'app.py'),True)
                if file.suffix!='.py':raise ValueError('Python giriş dosyası seç.')
                result=self.command([sdk['python'],'-m','PyInstaller','--noconfirm','--onefile','--distpath',str(builddir),'--workpath',str(builddir/'work'),'--specpath',str(builddir/'spec'),str(file)],root,300)
                checks.append(result);output_root=builddir;note='Windows Python EXE'
        elif stack in ('web','blender'):
            result={'passed':True,'output':'Statik web uygulaması; derleyici gerekmiyor.'}
            if stack=='blender':
                result=self.verify(workspace);note='Blender kaynak modeli, GLB oyun varlığı ve önizlemeler'
                if action!='package':return result
            elif action=='test':return self.browser(workspace)
        elif stack=='godot':
            if not sdk['godot']:raise ValueError('Godot kurulu değil.')
            if action=='package':raise ValueError('Godot dışa aktarım hedefi export_presets.cfg ile tanımlanmalı; hedef platform belirtilmeden paket üretilemez.')
            result=self.command([sdk['godot'],'--headless','--path',str(root),'--editor','--quit'],root,180);checks.append(result)
        else:raise ValueError('Bu proje türünde hazır derleme tarifi yok. İlgili SDK ve proje komutu eklenmeli.')
        record={'kind':action,'passed':result['passed'],'output':result.get('output',''),'errors':[result['error']] if result.get('error') else [],'steps':checks,'note':note}
        if action=='package' and record['passed']:
            if output_root is None:raise ValueError('Paket kaynağı bulunamadı.')
            artifact=folder/(time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]+'.zip');total=0
            with zipfile.ZipFile(artifact,'w',zipfile.ZIP_DEFLATED) as archive:
                for base,dirs,names in os.walk(output_root,followlinks=False):
                    dirs[:]=[n for n in dirs if n not in SKIP and not n.startswith('.') and not (Path(base)/n).is_symlink() and n not in ('work','spec')]
                    for name in names:
                        file=Path(base)/name;rel=file.relative_to(output_root)
                        if file.is_symlink() or not public(rel):continue
                        total+=file.stat().st_size
                        if total>256*1024*1024:raise ValueError('Paket sınırı 256 MB aşıldı.')
                        archive.write(file,rel.as_posix())
                archive.writestr('STUDYO-PAKET-BILGISI.txt',note+'\nOluşturulma: '+time.strftime('%Y-%m-%d %H:%M:%S'))
            record.update(artifact=str(artifact),artifact_name=artifact.name,bytes=artifact.stat().st_size,sha256=digest(artifact.read_bytes()),
                          executables=[str(p) for p in output_root.glob('*.exe')])
        return self.save_check(workspace,record)

    def blender(self,workspace,script,name='oyun-nesnesi',reference='',max_triangles=30000,include_image=False):
        root,cid=self.project(workspace);sdk=self.sdk()
        if not sdk['blender']:raise ValueError('Blender kurulu değil.')
        script_path=self.safe(root,script,True)
        if script_path.suffix!='.py':raise ValueError('Proje içindeki Blender Python betiğini seç.')
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,60}',name):raise ValueError('Model adı yalnız harf, sayı, - ve _ içerebilir.')
        if not isinstance(max_triangles,int) or not 12<=max_triangles<=200000:raise ValueError('Üçgen bütçesi 12–200000 olmalı.')
        if reference:
            image=self.safe(root,reference,True)
            if image.suffix.lower() not in {'.png','.jpg','.jpeg','.webp'}:raise ValueError('Referans PNG/JPG/WebP olmalı.')
        recipe={'script':script,'name':name,'reference':reference,'max_triangles':max_triangles}
        inputs={k:v for k,v in self.inventory(root).items() if not k.startswith('assets3d/')}
        input_hash=digest(json.dumps({'files':inputs,'recipe':recipe},sort_keys=True).encode())
        for old in self.history(workspace):
            if old.get('kind')=='blender' and old.get('passed') and old.get('input_hash')==input_hash and Path(old.get('artifact','')).is_file():
                if all(self.safe(root,p).is_file() and digest(self.safe(root,p).read_bytes())==h for p,h in old.get('asset_hashes',{}).items()):return dict(old,reused=True)
        self.checkpoint(workspace,'3D model üretimi öncesi')
        run=uuid.uuid4().hex;private=self.store/cid/'artifacts'/run;output=private/'model';private.mkdir(parents=True)
        cfg=private/'blender-job.json';cfg.write_text(json.dumps({'script':str(script_path),'output':str(output),'max_triangles':max_triangles}),encoding='utf-8')
        result=self.command([sdk['blender'],'--background','--factory-startup','--disable-autoexec','--threads','4','--python-exit-code','1','--python',str(SYSTEM/'automation/blender_asset.py'),'--',str(cfg)],root,300)
        report_file=output/'model-report.json'
        record={'kind':'blender','passed':result['passed'] and report_file.is_file(),'errors':[],
                'output':result['output'][-4500:],'recipe':recipe,'input_hash':input_hash,
                'note':'Görsel rehberli yaklaşık modelleme; yerel Blender CPU, ücretli 3D servisi yok.'}
        if not record['passed']:
            record['errors']=[result.get('error','Blender modeli üretilemedi; işlem çıktısını düzelt.')]
            return self.save_check(workspace,record)
        record['mesh']=json.loads(report_file.read_text(encoding='utf-8'))
        destination=self.safe(root,'assets3d/'+name+'-'+run[:6]);destination.mkdir(parents=True)
        hashes={}
        for file in output.iterdir():
            if file.name not in {'model.blend','model.glb','preview.png','back.png','model-report.json'}:continue
            target=destination/file.name;shutil.copy2(file,target);hashes[target.relative_to(root).as_posix()]=digest(target.read_bytes())
        artifact=private/(name+'.zip')
        with zipfile.ZipFile(artifact,'w',zipfile.ZIP_DEFLATED) as archive:
            for file in destination.iterdir():archive.write(file,file.name)
            archive.write(script_path,'source/'+script_path.name)
            if reference:archive.write(image,'reference/'+image.name)
            archive.writestr('MODEL-BILGISI.txt','Görsel rehberli yaklaşık Blender modeli. Görünmeyen yüzler varsayımdır.\nmodel.glb: oyun motoruna aktarılabilir mesh/malzeme/UV. model.blend: düzenlenebilir kaynak.\nModelin oyuna entegrasyonu, çarpışma ve istenen animasyonlar ayrıca tamamlanmalıdır.')
        record.update(asset_folder=str(destination),asset_hashes=hashes,screenshot=str(output/'preview.png'),artifact=str(artifact),artifact_name=artifact.name,sha256=digest(artifact.read_bytes()))
        saved=self.save_check(workspace,record);self.checkpoint(workspace,'3D model ve GLB üretildi');return saved

    def desktop(self,workspace,executable,steps=None,window_title='',include_image=False):
        if os.name!='nt':raise ValueError('Bu masaüstü kontrolü Windows içindir.')
        root,cid=self.project(workspace);exe=Path(executable).resolve(strict=True)
        authorized={str(Path(p).resolve()) for r in self.history(workspace) if r.get('kind')=='package' and r.get('passed') for p in r.get('executables',[])}
        if str(exe) not in authorized or not exe.is_relative_to((self.store/cid/'artifacts').resolve()):
            raise ValueError('Yalnız bu projenin yeni oluşturulmuş paket EXE dosyası kontrol edilebilir; kurulu kullanıcı uygulamaları açılmaz.')
        if not isinstance(steps or [],list) or len(steps or [])>20:raise ValueError('En fazla 20 masaüstü adımı kullanılabilir.')
        folder=self.store/cid/'checks';folder.mkdir(parents=True,exist_ok=True);run=uuid.uuid4().hex
        profile=self.store/cid/'test-profiles'/run;profile.mkdir(parents=True)
        env=clean_environment();env.update(UC_AI_TEST_MODE='1',UC_AI_TEST_PROFILE=str(profile),APPDATA=str(profile/'Roaming'),LOCALAPPDATA=str(profile/'Local'),TEMP=str(profile),TMP=str(profile))
        for p in ('Roaming','Local'):(profile/p).mkdir()
        process=subprocess.Popen([str(exe)],cwd=exe.parent,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        powershell=Path(os.environ.get('SYSTEMROOT','C:/Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe'
        try:
            payload={'pid':process.pid,'steps':steps or [],'window_title':window_title,'screenshot':str(folder/(run+'.png'))}
            result=subprocess.run([str(powershell),'-NoProfile','-STA','-ExecutionPolicy','Bypass','-File',str(SYSTEM/'automation/desktop.ps1')],input=json.dumps(payload,ensure_ascii=False).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=clean_environment(),timeout=130,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:record=json.loads(result.stdout.decode('utf-8-sig'))
            except ValueError:raise ValueError('Masaüstü kontrolü başlatılamadı: '+result.stderr.decode('utf-8','replace')[-2500:])
            record.update(id=run,kind='desktop',created=time.time(),fingerprint=self.fingerprint(self.inventory(root)),
                          acceptance=digest(json.dumps(steps or [],sort_keys=True).encode()),test_profile=str(profile))
            (folder/(run+'.json')).write_text(json.dumps(record,ensure_ascii=False),encoding='utf-8');return record
        finally:
            if process.poll() is None:subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

    def close(self):
        for item in self.servers.values():item['server'].shutdown();item['server'].server_close()
        for item in self.processes.values():
            p=item['process']
            if p.poll() is None:
                if os.name=='nt':subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                else:p.terminate()
            item['log'].close()

    def evidence_file(self,workspace,check_id,kind):
        _,cid=self.project(workspace)
        if not re.fullmatch('[a-f0-9]{32}',check_id):raise ValueError('Geçersiz kontrol.')
        record=json.loads((self.store/cid/'checks'/(check_id+'.json')).read_text(encoding='utf-8'))
        p=Path(record['screenshot'] if kind=='image' else record['artifact']).resolve()
        if not p.is_relative_to((self.store/cid).resolve()):raise ValueError('Geçersiz çıktı yolu.')
        return p

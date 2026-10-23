"""Local desktop chat/work UI backed by the real OpenCode server and NVIDIA NIM."""
import base64
from contextlib import ExitStack, contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import io
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import sqlite3
import subprocess
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse, parse_qs, unquote
from urllib.request import Request, urlopen
import uuid
import webbrowser
import zipfile
import sys

from nim_adapter import nim_connection
from workbench import Workbench

SYSTEM = Path(__file__).resolve().parent
ROOT = SYSTEM.parent
DATA = SYSTEM / 'studio-data'
ASSETS = SYSTEM / 'ui'
MODELS = {'deepseek': 'deepseek-ai/deepseek-v4.1-flash', 'glm': 'z-ai/glm-5.3',
          'nemotron': 'nvidia/nemotron-3.5-super-vl-120b-a12b', 'glmflash': 'z-ai/glm-5.3-flash'}
TEAM = ('deepseek', 'glm', 'nemotron')
SKIP = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.system', '.next'}


def uid(): return uuid.uuid4().hex


def public_file(path):
    return not re.search(r'(^|[-_.])(secret|credential|password|token|data|veri|database|customers|orders|sessions|users)([-_.]|$)',path.name,re.I) and not path.name.lower().startswith('appsettings.') and not any(p in SKIP or p.startswith('.') for p in path.parts) and path.name.lower() not in {
        'auth.json', 'credentials.json', 'nvidia-key.dpapi'} and path.suffix.lower() not in {'.pem', '.key', '.pfx', '.db', '.sqlite', '.sqlite3', '.mdb', '.csv', '.xls', '.xlsx'}


class Studio:
    def __init__(self, data=DATA):
        self.data = Path(data)
        self.data.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data / 'studio.sqlite'
        self.lock = threading.RLock()
        self.jobs = {}
        self.session_jobs = {}
        self.active_lock = threading.Lock()
        self.token = secrets.token_urlsafe(32)
        self.native_password = secrets.token_urlsafe(32)
        self.health = {name: {'state': 'unknown', 'detail': 'Henüz kontrol edilmedi'} for name in MODELS}
        health_file = self.data / 'model-health.json'
        if health_file.is_file():
            try: self.health.update(json.loads(health_file.read_text(encoding='utf-8')))
            except (ValueError, OSError): pass
        self.engine_url = ''
        self.engine_process = None
        self.stop = threading.Event()
        self.previews = {}
        with self.db() as db:
            db.executescript('''
              CREATE TABLE IF NOT EXISTS conversations(
                id TEXT PRIMARY KEY,title TEXT NOT NULL,mode TEXT NOT NULL,workspace TEXT,
                session_id TEXT,created REAL,updated REAL,archived INTEGER DEFAULT 0);
              CREATE TABLE IF NOT EXISTS messages(
                id TEXT PRIMARY KEY,conversation_id TEXT,role TEXT,content TEXT,
                attachments TEXT DEFAULT '[]',created REAL,state TEXT DEFAULT 'done');
              CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
            ''')
            db.execute("UPDATE messages SET state='interrupted' WHERE state='running'")
            if 'selected_model' not in {row[1] for row in db.execute('PRAGMA table_info(conversations)')}:
                db.execute("ALTER TABLE conversations ADD COLUMN selected_model TEXT DEFAULT 'deepseek'")
        self.workbench = Workbench(self.data)

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.db_path, timeout=20)
        db.row_factory = sqlite3.Row
        try:
            with db: yield db
        finally: db.close()

    def rows(self, sql, args=()):
        with self.db() as db: return [dict(row) for row in db.execute(sql, args)]

    def conversation(self, cid):
        rows = self.rows('SELECT * FROM conversations WHERE id=?', (cid,))
        if not rows: raise ValueError('Sohbet bulunamadı.')
        return rows[0]

    def conversations(self, archived=False):
        return self.rows('SELECT * FROM conversations WHERE archived=? ORDER BY updated DESC', (int(archived),))

    def create(self, mode='chat', title='', folder=''):
        if mode not in ('chat', 'work'): raise ValueError('Geçersiz sohbet türü.')
        cid = uid()
        title = title.strip()[:120] or ('Yeni sohbet' if mode == 'chat' else 'Yeni çalışma')
        if mode == 'work':
            if folder:
                workspace = Path(folder).expanduser().resolve(strict=True)
                if not workspace.is_dir(): raise ValueError('Bir klasör seçmelisin.')
            else:
                safe = re.sub(r'[^\w -]', '', title).strip(' .')[:50] or 'Calisma'
                workspace = ROOT / 'Projeler' / (safe + '-' + cid[:6])
                workspace.mkdir(parents=True)
        else:
            workspace = self.data / 'chats' / cid
            workspace.mkdir(parents=True)
        now = time.time()
        with self.db() as db:
            db.execute('INSERT INTO conversations(id,title,mode,workspace,created,updated) VALUES(?,?,?,?,?,?)',
                       (cid, title, mode, str(workspace), now, now))
            db.execute('UPDATE conversations SET selected_model=? WHERE id=?', ('team' if mode == 'work' else 'nemotron', cid))
        return self.conversation(cid)

    def message(self, cid, role, content='', attachments=None, state='done'):
        mid = uid()
        with self.db() as db:
            db.execute('INSERT INTO messages VALUES(?,?,?,?,?,?,?)',
                       (mid, cid, role, content, json.dumps(attachments or [], ensure_ascii=False), time.time(), state))
            db.execute('UPDATE conversations SET updated=? WHERE id=?', (time.time(), cid))
        return mid

    def native(self, method, path, body=None, folder=None, timeout=30):
        if folder: path += ('&' if '?' in path else '?') + urlencode({'directory': str(folder)})
        headers = {'Authorization': 'Basic ' + base64.b64encode(('opencode:' + self.native_password).encode()).decode()}
        payload = None
        if body is not None:
            headers['Content-Type'] = 'application/json'
            payload = json.dumps(body, ensure_ascii=False).encode('utf-8')
        request = Request(self.engine_url + path, data=payload, headers=headers, method=method)
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
            return json.loads(raw) if raw.strip() else None

    def native_request(self, path):
        return Request(self.engine_url + path, headers={'Authorization': 'Basic ' +
                       base64.b64encode(('opencode:' + self.native_password).encode()).decode()})

    def runtime_config(self):
        cfg = json.loads((SYSTEM / 'opencode.json').read_text(encoding='utf-8'))
        for name, agent in cfg['agent'].items():
            agent['prompt'] = (SYSTEM / 'prompts' / (name + '.md')).read_text(encoding='utf-8')
        for name, model in cfg['provider']['nvidia-nim']['models'].items():
            if name.startswith(('deepseek', 'nvidia/')): model['modalities']['input'] = ['text', 'image']
        cfg['agent']['sohbet'] = {
            'mode': 'primary', 'model': cfg['model'], 'description': 'Dosyalara dokunmadan normal sohbet',
            'prompt': ('You are the conversational assistant in Uc AI Studyo. Answer naturally and concisely '
                       'in Turkish. This is ordinary chat, not a coding project. Do not inspect or change files, '
                       'run terminal commands, or create a project. Images attached to the user message are '
                       'available for visual understanding. If the user explicitly asks for the three-agent '
                       'team, call chat_glm and chat_nemotron tasks concurrently with short read-only questions and '
                       'collect their answers. Otherwise answer directly. Never invent tool results.'),
            'permission': {'read': 'deny', 'glob': 'deny', 'grep': 'deny', 'edit': 'deny', 'development_*': 'deny',
                           'bash': 'deny', 'external_directory': 'deny',
                           'task': {'*': 'deny', 'chat_glm': 'allow', 'chat_nemotron': 'allow'}}}
        for name in ('glm', 'nemotron'):
            cfg['agent']['chat_' + name] = {'mode': 'subagent', 'model': 'nvidia-nim/' + MODELS[name],
                'description': 'Read-only conversational answer; no file, browser or command access.',
                'prompt': 'Answer the assigned conversational question concisely in Turkish. Do not use tools or change files.',
                'permission': {'*': 'deny'}, 'steps': 2}
        cfg['mcp'] = {'development': {'type': 'local', 'command': [sys.executable, str(SYSTEM / 'workbench_mcp.py'), '--data-dir', str(self.data)], 'enabled': True, 'timeout': 360000}}
        cfg['permission']['development_*'] = 'allow'
        guidance = (
            '\nYou have real development MCP tools, named development_inspect_project, development_checkpoint_project, '
            'development_browser_check and development_project_action. Use inspect_project for stack/SDK identity. '
            'For web apps use browser_check to actually open the app, exercise the changed user flow and inspect '
            'JS/HTTP errors and screenshot. Use include_image=true if your model supports images; GLM 5.3 must '
            'use include_image=false. For substantive interactive changes write a short studio-checks.json with '
            'meaningful browser steps (click/fill/press/expect_text/expect_visible) for the changed user flow. '
            'Fix real failures before completion, at most two targeted repairs; do not repeat passing checks on '
            'unchanged source. project_action builds/tests/packages locally; no deploy. Report missing SDKs '
            'truthfully; Python syntax alone is not a GUI test. Checkpoints and packages are real stored artifacts. '
            'For a single-model request work directly; do not call task. A three-model request uses actual glm '
            'and nemotron tasks concurrently. Do not modify this system, its tools, secrets or launchers.')
        guidance += (' For Windows GUI projects use development_project_action package and development_desktop_check '
                     'with the returned executables path; it controls only the new packaged app window. Save '
                     'native UI steps under studio-checks.json desktop.steps. New GUI code should use '
                     'UC_AI_TEST_MODE / UC_AI_TEST_PROFILE for disposable test data, never production data. '
                     'Name/automation_id selectors are available; read the returned controls and screenshot. '
                     'For canvas motion browser checks support expect_stable and expect_motion.')
        guidance += (' For an image-based 3D/game asset request, inspect the attached image using vision (delegate its '
                     'description to Nemotron if your model cannot see images), then write a project-local bpy Python '
                     'construction script and call development_blender_asset. Front is -Y, Z up, meters. This creates '
                     'real editable .blend and game-importable .glb, UV, packed materials, two preview renders and mesh '
                     'checks on local CPU. Use the reference path under references/ and a suitable triangle budget. '
                     'No neural image-to-mesh model is installed: explicitly describe this as approximate procedural '
                     'reconstruction and unseen sides as assumptions. Inspect actual renders for reference fidelity. '
                     'Rigging, animation, collision and game integration must be implemented when requested, not '
                     'claimed from mesh export alone. Do not download large AI weights or use paid 3D APIs silently.')
        for name in ('deepseek', 'glm', 'nemotron'): cfg['agent'][name]['prompt'] += guidance
        return cfg

    def start_engine(self, stack):
        key = os.environ.get('NVIDIA_API_KEY')
        if not key: raise ValueError('Kayıtlı NVIDIA anahtarı yüklenemedi.')
        upstream, local_key = stack.enter_context(nim_connection(key, self.data / 'requests.jsonl', self.connection_event))
        cfg = self.runtime_config()
        cfg['provider']['nvidia-nim']['options'].update(baseURL=upstream, apiKey='{env:NVIDIA_API_KEY}')
        config_path = self.data / 'runtime-config.json'
        config_path.write_text(json.dumps(cfg, ensure_ascii=False), encoding='utf-8')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        env = os.environ.copy()
        env.update(NVIDIA_API_KEY=local_key, OPENCODE_SERVER_PASSWORD=self.native_password,
                   OPENCODE_CONFIG=str(config_path), OPENCODE_DISABLE_AUTOUPDATE='true',
                   OPENCODE_CONFIG_CONTENT=json.dumps(cfg, ensure_ascii=False))
        env.pop('OPENCODE_CONFIG_DIR', None)
        runtime = self.data / 'engine'
        for key, folder in [('XDG_CONFIG_HOME', 'config'), ('XDG_DATA_HOME', 'data'),
                            ('XDG_CACHE_HOME', 'cache'), ('XDG_STATE_HOME', 'state')]:
            env[key] = str(runtime / folder)
        logfile = stack.enter_context((self.data / 'engine.log').open('a', encoding='utf-8'))
        process = subprocess.Popen([str(SYSTEM / 'opencode.exe'), 'serve', '--pure', '--hostname',
                                    '127.0.0.1', '--port', str(port)], env=env, cwd=ROOT,
                                   stdout=logfile, stderr=logfile,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.engine_process = process
        stack.callback(self.close_engine)
        self.engine_url = f'http://127.0.0.1:{port}'
        for _ in range(100):
            if process.poll() is not None: raise ValueError('Çalışma motoru açılamadı. engine.log dosyasına bak.')
            try:
                if self.native('GET', '/global/health', timeout=1).get('healthy'): break
            except (OSError, ValueError): time.sleep(0.15)
        else: raise ValueError('Çalışma motoru zamanında açılamadı.')
        effective = self.native('GET', '/config')
        if effective.get('provider', {}).get('nvidia-nim', {}).get('options', {}).get('baseURL') != upstream:
            raise ValueError('Güvenli NVIDIA bağlantısı çalışma motoruna uygulanamadı.')
        try: self.development_status = self.native('GET', '/mcp', timeout=20)
        except (OSError, ValueError): self.development_status = {'development': {'status': 'failed'}}
        threading.Thread(target=self.events, daemon=True).start()

    def close_engine(self):
        self.stop.set()
        self.workbench.close()
        if self.engine_process and self.engine_process.poll() is None:
            self.engine_process.terminate()
            try: self.engine_process.wait(timeout=5)
            except subprocess.TimeoutExpired: self.engine_process.kill()

    def connection_event(self, record):
        name = next((name for name, model in MODELS.items() if model == record.get('model')), None)
        if not name: return
        state = 'waiting' if record.get('phase') == 'start' else 'error' if record.get('error') else 'connected'
        detail = 'NVIDIA yanıtı bekleniyor' if state == 'waiting' else (
            'NVIDIA yanıt verdi' if state == 'connected' else
            'NVIDIA yanıt süresi doldu' if record.get('error') == 'TimeoutError' else
            f'NVIDIA bağlantı hatası ({record.get("status", "ağ")})')
        with self.lock:
            self.health[name] = {'state': state, 'detail': detail, 'time': time.time()}
            (self.data / 'model-health.json').write_text(json.dumps(self.health, ensure_ascii=False), encoding='utf-8')

    def error_text(self, error):
        if isinstance(error, dict):
            data = error.get('data', {})
            value = data.get('message') or error.get('message') or error.get('name') or 'Model yanıt vermedi.'
        elif isinstance(error, HTTPError):
            try: value = f'Motor HTTP {error.code}: ' + error.read().decode('utf-8', 'replace')
            except OSError: value = str(error)
        else: value = str(error)
        for secret in (os.environ.get('NVIDIA_API_KEY'), self.native_password, self.token):
            if secret: value = value.replace(secret, '[gizli]')
        return value[:2400]

    def events(self):
        while not self.stop.is_set():
            try:
                with urlopen(self.native_request('/global/event'), timeout=75) as response:
                    for raw in response:
                        if self.stop.is_set(): return
                        line = raw.decode('utf-8', 'replace').strip()
                        if line.startswith('data:'):
                            try: self.on_event(json.loads(line[5:]))
                            except (ValueError, KeyError, TypeError): pass
            except (OSError, ValueError): self.stop.wait(2)

    def on_event(self, wrapper):
        event = wrapper.get('payload', wrapper)
        kind, props = event.get('type', ''), event.get('properties', {})
        info = props.get('info', {})
        with self.lock:
            if kind == 'session.created' and info.get('parentID') in self.session_jobs:
                self.session_jobs[info['id']] = self.session_jobs[info['parentID']]
            sid = props.get('sessionID') or info.get('sessionID') or props.get('part', {}).get('sessionID')
            cid = self.session_jobs.get(sid)
            job = self.jobs.get(cid)
            if not job or not job['running']: return
            if kind == 'message.updated' and info.get('role') == 'assistant':
                if sid == job['session_id']:
                    job['assistant_ids'].add(info['id'])
                    if info.get('error'): job['native_error'] = self.error_text(info['error'])
            if kind == 'session.error': job['native_error'] = self.error_text(props.get('error', {}))
            part = props.get('part', {})
            if kind == 'message.part.updated':
                if part.get('type') == 'text' and part.get('messageID') in job['assistant_ids']:
                    job['parts'][part['id']] = part.get('text', '')
                if part.get('type') == 'tool':
                    state = part.get('state', {})
                    if part.get('tool') == 'task':
                        name = state.get('input', {}).get('subagent_type', '').removeprefix('chat_')
                        if name in MODELS:
                            job['agents'][name] = {'state': state.get('status', 'running'),
                                                   'result': self.error_text(state.get('output', ''))[-5000:],
                                                   'time': state.get('time', {})}
                    title = state.get('title') or state.get('input', {}).get('command') or part.get('tool')
                    job['activity'] = self.error_text(title)[:180]
                    job['logs'][part['id']] = {'state': state.get('status', 'running'),
                        'title': self.error_text(title)[:250],
                        'output': self.error_text(state.get('output') or state.get('error') or ''),
                        'time': state.get('time', {})}
            elif kind == 'message.part.delta' and props.get('field') == 'text':
                if props.get('messageID') in job['assistant_ids']:
                    part_id = props['partID']
                    job['parts'][part_id] = job['parts'].get(part_id, '') + props.get('delta', '')

    def send(self, cid, text, attachments, model='team'):
        conv = self.conversation(cid)
        text = text.strip()
        if not text and not attachments: raise ValueError('Bir mesaj yaz veya görsel ekle.')
        if len(text) > 80000: raise ValueError('Mesaj çok uzun; ilgili bölümü gönder.')
        if model not in ('team', *MODELS): raise ValueError('Geçersiz model.')
        if model == 'glm' and attachments: raise ValueError('Görsel için DeepSeek, Nemotron veya üçlü ekibi seç.')
        if not self.active_lock.acquire(blocking=False):
            raise ValueError('Bir işlem sürüyor. Bitmesini bekleyebilir veya Durdur düğmesine basabilirsin.')
        try:
            before = self.workbench.checkpoint(conv['workspace'], 'Çalışma öncesi: ' + text[:60]) if conv['mode'] == 'work' else None
            validated = []
            if len(attachments) > 4 or len(set(attachments)) != len(attachments):
                raise ValueError('En fazla dört farklı görsel ekleyebilirsin.')
            total = 0
            for aid in attachments:
                meta = self.attachment(cid, aid)
                total += Path(meta['path']).stat().st_size
                validated.append({key: meta[key] for key in ('id', 'name', 'mime')})
            if total > 8 * 1024 * 1024: raise ValueError('Görseller toplamda en fazla 8 MB olabilir.')
            with self.db() as db: db.execute('UPDATE conversations SET selected_model=? WHERE id=?', (model, cid))
            if text and conv['title'] == 'Yeni sohbet':
                with self.db() as db: db.execute('UPDATE conversations SET title=? WHERE id=?', (text[:55], cid))
            self.message(cid, 'user', text, validated)
            mid = self.message(cid, 'assistant', state='running')
            chosen = 'deepseek' if model == 'team' else model
            job = {'running': True, 'message_id': mid, 'parts': {}, 'assistant_ids': set(),
                   'agents': {name: {'state': 'running' if name == chosen else
                              'queued' if model == 'team' else 'idle'} for name in (TEAM if model == 'team' else (chosen,))},
                   'activity': 'İstek hazırlanıyor', 'started': time.time(), 'session_id': conv['session_id'],
                   'native_error': '', 'cancelled': False, 'pending': [], 'questions': [], 'pending_at': 0, 'logs': {}}
            job.update(before_version=before, validation=None, artifacts=[], repairs=0)
            with self.lock: self.jobs[cid] = job
            threading.Thread(target=self.run_message, args=(conv, job, text, validated, model), daemon=True).start()
            return {'accepted': True}
        except Exception:
            self.active_lock.release()
            raise

    def run_message(self, conv, job, text, attachments, model):
        cid, folder = conv['id'], conv['workspace']
        final, state = '', 'done'
        try:
            if job['cancelled']: raise ValueError('İşlem durduruldu.')
            sid = conv['session_id']
            if not sid:
                payload = {'title': conv['title']}
                if conv['mode'] == 'chat':
                    payload['permission'] = [{'permission': action, 'pattern': '*', 'action': 'deny'}
                                             for action in ('read', 'glob', 'grep', 'edit', 'bash', 'external_directory')]
                session = self.native('POST', '/session', payload, folder)
                sid = session['id']
                with self.db() as db: db.execute('UPDATE conversations SET session_id=? WHERE id=?', (sid, cid))
            with self.lock:
                job['session_id'] = sid
                self.session_jobs[sid] = cid
            if job['cancelled']: raise ValueError('İşlem durduruldu.')
            selected = 'deepseek' if model == 'team' else model
            parts = [{'type': 'text', 'text': text or 'Bu görseli incele.'}]
            for attachment in attachments:
                meta = self.attachment(cid, attachment['id'])
                encoded = base64.b64encode(Path(meta['path']).read_bytes()).decode()
                parts.append({'type': 'file', 'mime': meta['mime'], 'filename': meta['name'],
                              'url': 'data:' + meta['mime'] + ';base64,' + encoded})
                if conv['mode'] == 'work':
                    reference = Path(folder) / 'references' / (meta['id'] + mimetypes.guess_extension(meta['mime']))
                    reference.parent.mkdir(exist_ok=True)
                    shutil.copyfile(meta['path'], reference)
                    parts.append({'type': 'text', 'text': 'Attached reference image is also saved at: ' + str(reference)})
            instruction = ('This is a work session in the explicitly selected application folder. ' +
                           ('Use actual glm and nemotron task calls concurrently for substantive development. '
                            if model == 'team' else 'The user selected a single model. Implement directly without delegation. ') +
                           'Images are visual requirements: inspect them, provide GLM a textual specification, '
                           'and give Nemotron relevant image paths for independent visual review. '
                           'Own disjoint files. Implement working software, do not return only a plan. '
                           'Use the existing architecture and run only necessary validation. '
                           'For a small browser game/app prefer a working index.html with local assets that '
                           'can be previewed. Do not deploy, publish, send messages, or modify live data '
                           'without user authorization. Never claim a test passed unless it ran.') if conv['mode'] == 'work' else (
                           'This is normal chat. Do not create a project or use file/terminal tools. ' +
                           ('The user selected the three-model team. Ask chat_glm and chat_nemotron short independent '
                            'read-only questions concurrently; collect both and synthesize a concise answer.'
                            if model == 'team' else 'The user selected one model. Answer directly, without delegating.'))
            if conv['mode'] == 'work':
                instruction += (' Use the development MCP tools for actual browser/SDK/build checks. '
                                'Do not merely describe a test. Save a short studio-checks.json with steps that '
                                'exercise the changed interaction when relevant. Automatic validation and up to '
                                'two bounded repairs will run before delivery. Prefer reusing a passing check '
                                'on unchanged source. Current workspace is: ' + folder)
            message = {'agent': 'deepseek' if conv['mode'] == 'work' else 'sohbet',
                       'model': {'providerID': 'nvidia-nim', 'modelID': MODELS[selected]},
                       'parts': parts, 'system': instruction}
            if model != 'team': message['tools'] = {'task': False}
            job['activity'] = 'Model yanıtı bekleniyor'
            # Long development tasks may involve several bounded model/tool calls.
            self.native('POST', f'/session/{sid}/message', message, folder, timeout=1800)
            messages = self.native('GET', f'/session/{sid}/message', folder=folder)
            latest_user = max((index for index, item in enumerate(messages)
                               if item['info']['role'] == 'user'), default=-1)
            texts, errors = [], []
            for item in messages[latest_user + 1:]:
                if item['info']['role'] != 'assistant': continue
                if item['info'].get('error'): errors.append(self.error_text(item['info']['error']))
                for part in item.get('parts', []):
                    if part.get('type') == 'text' and part.get('text'): texts.append(part['text'])
                    if part.get('tool') == 'task':
                        task = part.get('state', {})
                        name = task.get('input', {}).get('subagent_type', '').removeprefix('chat_')
                        if name in MODELS:
                            job['agents'][name] = {'state': task.get('status'),
                                'result': self.error_text(task.get('output', ''))[-5000:], 'time': task.get('time', {})}
            final = '\n\n'.join(texts)
            if errors or job['native_error']:
                state = 'error'
                final += ('\n\n' if final else '') + 'Bağlantı / işlem hatası: ' + (errors[-1] if errors else job['native_error'])
            if not final.strip():
                state, final = 'error', 'Model tamamlanmış bir yanıt döndürmedi. Modeller bölümünden bağlantı durumunu görebilirsin.'
            if state == 'done' and conv['mode'] == 'work' and not job['cancelled']:
                final, state = self.validate_development(conv, job, message, final)
            if state == 'done' and model == 'team':
                missing = [name for name in ('glm', 'nemotron') if job['agents'][name]['state'] != 'completed']
                if missing:
                    state = 'error'
                    final += '\n\nÜçlü ekip tamamlanamadı: ' + ', '.join(missing) + ' görevi tamamlanmış değil.'
                else:
                    intervals = [job['agents'][name].get('time', {}) for name in ('glm', 'nemotron')]
                    job['parallel_verified'] = all('start' in item and 'end' in item for item in intervals) and (
                        max(item['start'] for item in intervals) < min(item['end'] for item in intervals))
                    if not job['parallel_verified']:
                        final += '\n\nİki yardımcı görev tamamlandı; eşzamanlı çalışma doğrulanamadı.'
            if job['cancelled']: state = 'cancelled'
            job['agents'][selected] = {'state': 'completed' if state == 'done' else state}
        except Exception as error:
            state = 'cancelled' if job['cancelled'] else 'error'
            final = '\n'.join(job['parts'].values())
            final += ('\n\n' if final else '') + ('İşlem durduruldu.' if job['cancelled'] else self.error_text(error))
        finally:
            if conv['mode'] == 'work':
                try: job['after_version'] = self.workbench.checkpoint(folder, 'Çalışma sonrası: ' + text[:60])
                except Exception as error:
                    state = 'error'; final += '\n\nSürüm kaydı tamamlanamadı: ' + self.error_text(error)
            with self.db() as db:
                db.execute('UPDATE messages SET content=?,state=? WHERE id=?', (final, state, job['message_id']))
                db.execute('UPDATE conversations SET updated=? WHERE id=?', (time.time(), cid))
            with self.lock:
                job.update(running=False, finished=time.time(), pending=[], questions=[],
                           activity='Tamamlandı' if state == 'done' else 'Durduruldu' if state == 'cancelled' else 'İşlem tamamlanamadı')
                for agent in job['agents'].values():
                    if agent['state'] in ('running', 'queued', 'pending'): agent['state'] = 'cancelled' if job['cancelled'] else 'error' if state == 'error' else 'idle'
                saved = {key: value for key, value in job.items() if key not in ('parts', 'assistant_ids', 'session_id')}
                runs = self.data / 'runs'
                runs.mkdir(exist_ok=True)
                (runs / (cid + '.json')).write_text(json.dumps(saved, ensure_ascii=False), encoding='utf-8')
            self.active_lock.release()

    def validate_development(self, conv, job, template, final):
        folder, sid = conv['workspace'], job['session_id']
        recipe = Path(folder) / 'studio-checks.json'
        frozen_recipe = json.loads(recipe.read_text(encoding='utf-8')) if recipe.is_file() else {}
        acceptance = frozen_recipe.get('steps', [])
        for attempt in range(3):
            if job['cancelled']: return final, 'cancelled'
            job['activity'] = 'Uygulama ve ilgili kontroller çalıştırılıyor'
            try: validation = self.workbench.verify(folder, steps_override=acceptance, desktop_override=frozen_recipe.get('desktop'))
            except Exception as error:
                validation = {'passed': False, 'setup_required': True, 'errors': [self.error_text(error)]}
            job['validation'] = validation
            job['logs']['automatic-validation'] = {'state': 'completed' if validation.get('passed') else 'error',
                'title': 'Gerçek uygulama kontrolü', 'output': json.dumps(validation, ensure_ascii=False)[:12000]}
            if validation.get('passed'):
                final += '\n\nKontrol geçti: ' + validation.get('kind', 'uygulama')
                if validation.get('limitation'): final += '. ' + validation['limitation']
                job['activity'] = 'Dağıtım paketi hazırlanıyor'
                try:
                    package = self.workbench.action(folder, 'package')
                    if package.get('passed') and package.get('artifact'):
                        job['artifacts'] = [package]; final += '\nDağıtım paketi hazır; Çalışma alanı → Kontroller bölümünden indirebilirsin.'
                    else:
                        job['package_error'] = package; final += '\nPaket tamamlanamadı: ' + (package.get('error') or package.get('output', '')[-1500:])
                except Exception as error:
                    job['package_error'] = self.error_text(error)
                    final += '\nPaket hazırlama için eksik adım: ' + self.error_text(error)
                return final, 'done'
            if validation.get('unsupported') or validation.get('setup_required') or attempt == 2:
                return final + '\n\nUygulama kontrolü tamamlanamadı: ' + json.dumps(validation.get('errors') or validation.get('output'), ensure_ascii=False)[-5000:], 'error'
            job['repairs'] = attempt + 1
            job['activity'] = f'Gerçek kontroldeki hata düzeltiliyor ({attempt + 1}/2)'
            repair = dict(template)
            repair['parts'] = [{'type': 'text', 'text':
                'Automatic local application validation failed. Fix only the concrete failure, then use the '
                'development tools to check the changed flow. Do not change the acceptance steps to hide a '
                'failure. Do not run unrelated tests. This is bounded repair '+str(attempt+1)+'/2. Evidence:\n'+
                json.dumps(validation, ensure_ascii=False)[-14000:]}]
            image_path = validation.get('screenshot')
            if image_path and template['model']['modelID'] != MODELS['glm'] and Path(image_path).is_file():
                repair['parts'].append({'type': 'file', 'mime': 'image/png', 'filename': 'application-check.png',
                    'url': 'data:image/png;base64,' + base64.b64encode(Path(image_path).read_bytes()).decode()})
            job['native_error'] = ''
            self.native('POST', f'/session/{sid}/message', repair, folder, timeout=1800)
            messages = self.native('GET', f'/session/{sid}/message', folder=folder)
            user_index = max((i for i, m in enumerate(messages) if m['info']['role'] == 'user'), default=-1)
            texts, errors = [], []
            for item in messages[user_index + 1:]:
                if item['info']['role'] != 'assistant': continue
                if item['info'].get('error'): errors.append(self.error_text(item['info']['error']))
                texts += [part['text'] for part in item.get('parts', []) if part.get('type') == 'text' and part.get('text')]
            if texts: final = '\n\n'.join(texts)
            if errors or job['native_error']:
                return final + '\n\nDüzeltme tamamlanamadı: ' + (errors[-1] if errors else job['native_error']), 'error'

    def cancel(self, cid):
        conv = self.conversation(cid)
        job = self.jobs.get(cid)
        if job and job['running']:
            job['cancelled'] = True
            if job.get('session_id'): self.native('POST', f'/session/{job["session_id"]}/abort', {}, conv['workspace'])
        return {'cancelled': True}

    def detail(self, cid):
        conv = self.conversation(cid)
        messages = self.rows('SELECT * FROM messages WHERE conversation_id=? ORDER BY created', (cid,))
        for message in messages: message['attachments'] = json.loads(message['attachments'])
        job = self.jobs.get(cid)
        if job and job['running'] and time.time() - job['pending_at'] > 1.5 and job.get('session_id'):
            job['pending_at'] = time.time()
            try:
                job['pending'] = self.native('GET', '/permission', folder=conv['workspace']) or []
                job['questions'] = self.native('GET', '/question', folder=conv['workspace']) or []
            except (OSError, ValueError): pass
        if job:
            visible = {key: value for key, value in job.items() if key not in ('parts', 'assistant_ids', 'session_id')}
            if job['running']:
                for message in messages:
                    if message['id'] == job['message_id']: message['content'] = '\n\n'.join(job['parts'].values())
        else:
            run_file = self.data / 'runs' / (cid + '.json')
            visible = json.loads(run_file.read_text(encoding='utf-8')) if run_file.is_file() else None
        return {'conversation': conv, 'messages': messages, 'job': visible, 'health': self.health}

    def respond(self, cid, kind, request_id, value):
        conv = self.conversation(cid)
        if kind not in ('permission', 'question'): raise ValueError('Geçersiz istek.')
        pending = self.native('GET', '/' + kind, folder=conv['workspace']) or []
        if not any(item['id'] == request_id for item in pending): raise ValueError('Bu istek artık beklemiyor.')
        if kind == 'permission':
            if value not in ('once', 'reject'): raise ValueError('Geçersiz izin yanıtı.')
            body, suffix = {'reply': value}, 'reply'
        else:
            body, suffix = ({'answers': value}, 'reply') if value is not None else ({}, 'reject')
        self.native('POST', f'/{kind}/{request_id}/{suffix}', body, conv['workspace'])
        return {'ok': True}

    def upload(self, cid, files):
        self.conversation(cid)
        if len(files) > 4: raise ValueError('Bir defada en fazla dört görsel ekleyebilirsin.')
        directory = self.data / 'uploads' / cid
        directory.mkdir(parents=True, exist_ok=True)
        uploaded, total = [], 0
        for file in files:
            mime = file.get('mime', '')
            if mime not in ('image/png', 'image/jpeg', 'image/webp'):
                raise ValueError('PNG, JPG veya WebP görseli kullan.')
            raw = base64.b64decode(file.get('data', ''), validate=True)
            total += len(raw)
            if not raw or len(raw) > 4 * 1024 * 1024 or total > 8 * 1024 * 1024:
                raise ValueError('Görsel en fazla 4 MB, toplam görseller en fazla 8 MB olabilir.')
            valid = (mime == 'image/png' and raw.startswith(b'\x89PNG\r\n\x1a\n')) or (
                mime == 'image/jpeg' and raw.startswith(b'\xff\xd8\xff')) or (
                mime == 'image/webp' and raw[:4] == b'RIFF' and raw[8:12] == b'WEBP')
            if not valid: raise ValueError('Görsel dosyası türüyle uyuşmuyor.')
            aid = uid()
            path = directory / aid
            path.write_bytes(raw)
            meta = {'id': aid, 'name': Path(file.get('name', 'Görsel')).name[:150],
                    'mime': mime, 'path': str(path)}
            path.with_suffix('.json').write_text(json.dumps(meta, ensure_ascii=False), encoding='utf-8')
            uploaded.append({key: meta[key] for key in ('id', 'name', 'mime')})
        return uploaded

    def attachment(self, cid, aid):
        if not re.fullmatch(r'[a-f0-9]{32}', aid): raise ValueError('Geçersiz görsel.')
        path = self.data / 'uploads' / cid / (aid + '.json')
        if not path.is_file(): raise ValueError('Görsel bulunamadı.')
        return json.loads(path.read_text(encoding='utf-8'))

    def workspace_file(self, cid, relative):
        conv = self.conversation(cid)
        if conv['mode'] != 'work': raise ValueError('Bu sohbet bir çalışma projesi değil.')
        root = Path(conv['workspace']).resolve(strict=True)
        path = (root / relative).resolve(strict=True)
        if not path.is_relative_to(root) or not public_file(path.relative_to(root)):
            raise ValueError('Bu dosyaya erişilemez.')
        if not path.is_file(): raise ValueError('Dosya bulunamadı.')
        return path

    def files(self, cid):
        conv = self.conversation(cid)
        if conv['mode'] != 'work': return []
        root = Path(conv['workspace'])
        result = []
        for folder, dirs, names in os.walk(root, followlinks=False):
            dirs[:] = sorted(name for name in dirs if name not in SKIP and not name.startswith('.') and
                              not (Path(folder) / name).is_symlink())
            if len(Path(folder).relative_to(root).parts) > 8:
                dirs[:] = []
                continue
            for name in sorted(names):
                file = Path(folder) / name
                relative = file.relative_to(root)
                if public_file(relative) and not file.is_symlink():
                    result.append({'path': relative.as_posix(), 'size': file.stat().st_size})
                    if len(result) >= 800: return result
        return result

    def import_existing(self):
        with self.db() as db:
            if db.execute("SELECT value FROM settings WHERE key='legacy-import'").fetchone(): return
        # Only known application folders are imported; smoke-test conversations stay out of the UI.
        registry = SYSTEM / 'projects.json'
        if registry.exists():
            for project in json.loads(registry.read_text(encoding='utf-8')):
                folder = Path(project['path'])
                if not folder.is_absolute(): folder = ROOT / folder
                if folder.is_dir() and not self.rows('SELECT id FROM conversations WHERE workspace=?', (str(folder),)):
                    self.create('work', project['name'], str(folder))
        # Preserve real conversations made from the earlier terminal UI, when present.
        old_db = SYSTEM / 'user/data/opencode/opencode.db'
        if old_db.exists():
            try:
                db = sqlite3.connect(old_db.as_uri() + '?mode=ro', uri=True)
                db.row_factory = sqlite3.Row
                for session in db.execute('SELECT id,title,directory,parent_id FROM session ORDER BY time_updated DESC LIMIT 100'):
                    if session['parent_id']: continue
                    matches = self.rows('SELECT id FROM conversations WHERE workspace=?', (session['directory'],))
                    if not matches: continue
                    # The old engine owns this session. Import text history only, never reuse its id in the new engine.
                    for row in db.execute('SELECT id,data FROM message WHERE session_id=? ORDER BY time_created', (session['id'],)):
                        info = json.loads(row['data'])
                        text = '\n\n'.join(json.loads(part['data']).get('text', '') for part in
                               db.execute('SELECT data FROM part WHERE message_id=? ORDER BY time_created', (row['id'],))
                               if json.loads(part['data']).get('type') == 'text')
                        if text.strip(): self.message(matches[0]['id'], info['role'], text)
                db.close()
            except (sqlite3.Error, ValueError, KeyError): pass
        with self.db() as db: db.execute("INSERT OR REPLACE INTO settings VALUES('legacy-import','done')")

    def preview(self, cid):
        for candidate in ('index.html', 'dist/index.html', 'build/index.html', 'public/index.html'):
            try: self.workspace_file(cid, candidate)
            except (ValueError, OSError): continue
            nonce = self.previews.setdefault(cid, secrets.token_urlsafe(24))
            return f'/preview/{nonce}/{cid}/{candidate}'
        return None

    def folder_picker(self):
        code = ("Add-Type -AssemblyName System.Windows.Forms; "
                "$d=New-Object System.Windows.Forms.FolderBrowserDialog; "
                "$d.Description='Uygulamanın kaynak kod klasörünü seç'; "
                "if($d.ShowDialog() -eq 'OK'){[Console]::Write($d.SelectedPath)}")
        result = subprocess.run(['powershell.exe', '-NoProfile', '-STA', '-Command', code],
                                capture_output=True, text=True, encoding='utf-8', errors='replace',
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        return result.stdout.strip()

    def check_models(self):
        with self.lock:
            if getattr(self, 'checking', False): return {'checking': True}
            if self.active_lock.locked(): raise ValueError('Süren işlem bittikten sonra bağlantı kontrolü yapabilirsin.')
            self.checking = True
        def check(name):
            from nim_adapter import normalize
            body = normalize({'model': MODELS[name], 'messages': [{'role': 'user', 'content': 'Reply exactly TAMAM.'}],
                              'max_tokens': 4096, 'stream': True})
            record = {'model': MODELS[name], 'phase': 'start'}
            self.connection_event(record)
            answer = ''
            try:
                request = Request('https://integrate.api.nvidia.com/v1/chat/completions', data=json.dumps(body).encode(),
                                  headers={'Content-Type': 'application/json',
                                           'Authorization': 'Bearer ' + os.environ['NVIDIA_API_KEY']})
                with urlopen(request, timeout=120) as response:
                    for raw in response:
                        line = raw.decode('utf-8', 'replace').strip()
                        if not line.startswith('data:'): continue
                        if line[5:].strip() == '[DONE]': break
                        for choice in json.loads(line[5:]).get('choices', []):
                            answer += choice.get('delta', {}).get('content') or ''
                        if answer.strip(): break
                if answer.strip():
                    self.connection_event({'model': MODELS[name], 'phase': 'end', 'status': 200})
                else:
                    with self.lock: self.health[name] = {'state': 'error', 'detail': 'Tamamlanmış yanıt alınamadı', 'time': time.time()}
            except Exception as error:
                self.connection_event({'model': MODELS[name], 'phase': 'end', 'error': type(error).__name__,
                                       'status': getattr(error, 'code', None)})
        def all_models():
            from concurrent.futures import ThreadPoolExecutor
            try:
                with ThreadPoolExecutor(max_workers=3) as pool: list(pool.map(check, MODELS))
            finally: self.checking = False
        threading.Thread(target=all_models, daemon=True).start()
        return {'checking': True}


def make_handler(studio):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_): pass

        def authenticated(self):
            return hmac.compare_digest(self.headers.get('X-Studio-Token', ''), studio.token)

        def send(self, status, data, mime='application/json; charset=utf-8', extra=None):
            if isinstance(data, (dict, list)): data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            elif isinstance(data, str): data = data.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            for name, value in (extra or {}).items(): self.send_header(name, value)
            self.end_headers()
            try: self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError): pass

        def do_GET(self):
            url = urlparse(self.path)
            path = unquote(url.path)
            query = parse_qs(url.query)
            try:
                if path in ('/', '/app.js', '/style.css', '/logo.svg'):
                    asset = ASSETS / ('index.html' if path == '/' else path[1:])
                    self.send(200, asset.read_bytes(), mimetypes.guess_type(asset.name)[0] or 'text/plain', {
                        'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; frame-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'"})
                    return
                if path.startswith('/preview/'):
                    _, _, nonce, cid, relative = path.split('/', 4)
                    if not hmac.compare_digest(studio.previews.get(cid, ''), nonce): raise ValueError('Önizleme geçersiz.')
                    file = studio.workspace_file(cid, relative)
                    if file.suffix.lower() not in {'.html', '.css', '.js', '.mjs', '.json', '.txt', '.png', '.jpg',
                                                   '.jpeg', '.webp', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf'}:
                        raise ValueError('Bu dosya önizlenemez.')
                    raw = file.read_bytes()
                    if len(raw) > 25 * 1024 * 1024: raise ValueError('Önizleme dosyası çok büyük.')
                    if file.suffix == '.html':
                        prefix = '/preview/' + nonce + '/' + cid + '/' + str(Path(relative).parent).replace('\\', '/').strip('.')
                        html = raw.decode('utf-8', 'replace')
                        html = re.sub(r'((?:src|href)=[\"\'])/(?!/)', lambda m: m[1] + prefix.rstrip('/') + '/', html)
                        raw = html.encode('utf-8')
                    self.send(200, raw, mimetypes.guess_type(file.name)[0] or 'application/octet-stream', {
                        'Content-Security-Policy': "sandbox allow-scripts allow-forms; object-src 'none'"})
                    return
                if not self.authenticated(): self.send(401, {'error': 'Uygulamayı masaüstü kısayolundan aç.'}); return
                if path == '/api/state':
                    self.send(200, {'app': 'Uc AI Studyo', 'version': '1.2.0',
                                   'conversations': studio.conversations(query.get('archived') == ['1']),
                                   'health': studio.health, 'checking': getattr(studio, 'checking', False),
                                   'development_tools': getattr(studio, 'development_status', {}),
                                   'engine': studio.engine_process is not None and studio.engine_process.poll() is None})
                elif path.startswith('/api/conversation/'):
                    self.send(200, studio.detail(path.rsplit('/', 1)[1]))
                elif path.startswith('/api/files/'):
                    cid = path.rsplit('/', 1)[1]
                    self.send(200, {'files': studio.files(cid), 'preview': studio.preview(cid)})
                elif path.startswith('/api/development/'):
                    conv = studio.conversation(path.rsplit('/', 1)[1])
                    folder = conv['workspace']
                    self.send(200, {'project': studio.workbench.inspect(folder),
                        'agent_tools': getattr(studio, 'development_status', {}),
                        'versions': studio.workbench.versions(folder), 'checks': studio.workbench.history(folder)})
                elif path.startswith('/api/evidence/'):
                    _, _, _, cid, check_id = path.split('/')
                    kind = query.get('type', ['image'])[0]
                    if kind not in ('image', 'artifact'): raise ValueError('Geçersiz çıktı türü.')
                    file = studio.workbench.evidence_file(studio.conversation(cid)['workspace'], check_id, kind)
                    self.send(200, file.read_bytes(), 'image/png' if kind == 'image' else 'application/zip')
                elif path.startswith('/api/file/'):
                    file = studio.workspace_file(path.rsplit('/', 1)[1], query.get('path', [''])[0])
                    self.send(200, {'path': file.name, 'text': file.read_bytes()[:1024 * 1024].decode('utf-8', 'replace'),
                                   'truncated': file.stat().st_size > 1024 * 1024})
                elif path.startswith('/api/image/'):
                    _, _, _, cid, aid = path.split('/')
                    studio.conversation(cid)
                    meta = studio.attachment(cid, aid)
                    self.send(200, Path(meta['path']).read_bytes(), meta['mime'])
                elif path.startswith('/api/export/'):
                    cid = path.rsplit('/', 1)[1]
                    detail = studio.detail(cid)
                    detail.pop('health', None)
                    detail.pop('job', None)
                    self.send(200, detail)
                elif path.startswith('/api/project-zip/'):
                    cid = path.rsplit('/', 1)[1]
                    items = studio.files(cid)
                    buffer, total = io.BytesIO(), 0
                    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
                        for item in items:
                            total += item['size']
                            if total > 200 * 1024 * 1024: raise ValueError('Proje indirme sınırı 200 MB.')
                            file = studio.workspace_file(cid, item['path'])
                            archive.write(file, item['path'])
                    self.send(200, buffer.getvalue(), 'application/zip')
                else: self.send(404, {'error': 'Bulunamadı.'})
            except (ValueError, OSError, KeyError) as error: self.send(400, {'error': studio.error_text(error)})

        def do_POST(self):
            if not self.authenticated(): self.send(401, {'error': 'Yetkisiz istek.'}); return
            origin = self.headers.get('Origin')
            if origin and origin != 'http://' + self.headers.get('Host', ''):
                self.send(403, {'error': 'Geçersiz kaynak.'}); return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 13 * 1024 * 1024: raise ValueError('İstek boyutu geçersiz.')
                data = json.loads(self.rfile.read(length))
                path = urlparse(self.path).path
                if path == '/api/create':
                    result = studio.create(data.get('mode', 'chat'), data.get('title', ''), data.get('folder', ''))
                elif path == '/api/send':
                    result = studio.send(data['id'], data.get('text', ''), data.get('attachments', []), data.get('model', 'deepseek'))
                elif path == '/api/cancel': result = studio.cancel(data['id'])
                elif path == '/api/development-action':
                    conv = studio.conversation(data['id']); action = data.get('action')
                    if not studio.active_lock.acquire(blocking=False): raise ValueError('Önce süren geliştirme işlemini tamamla veya durdur.')
                    try:
                        if action == 'checkpoint': result = studio.workbench.checkpoint(conv['workspace'], data.get('label', 'Elle kaydedilen sürüm'))
                        elif action == 'verify': result = studio.workbench.verify(conv['workspace'])
                        elif action in ('build', 'test', 'package'): result = studio.workbench.action(conv['workspace'], action, data.get('entry', ''))
                        else: raise ValueError('Geçersiz geliştirme işlemi.')
                    finally: studio.active_lock.release()
                elif path == '/api/version-diff':
                    result = studio.workbench.diff(studio.conversation(data['id'])['workspace'], data['version'])
                elif path == '/api/version-restore':
                    if not studio.active_lock.acquire(blocking=False): raise ValueError('Süren işlem varken geri alınamaz.')
                    try: result = studio.workbench.restore(studio.conversation(data['id'])['workspace'], data['version'], data['expected'])
                    finally: studio.active_lock.release()
                elif path == '/api/upload': result = studio.upload(data['id'], data.get('files', []))
                elif path == '/api/respond':
                    result = studio.respond(data['id'], data['kind'], data['request_id'], data.get('value'))
                elif path == '/api/rename':
                    title = data.get('title', '').strip()[:120]
                    if not title: raise ValueError('Bir ad yaz.')
                    studio.conversation(data['id'])
                    with studio.db() as db: db.execute('UPDATE conversations SET title=? WHERE id=?', (title, data['id']))
                    result = {'ok': True}
                elif path == '/api/archive':
                    studio.conversation(data['id'])
                    if studio.jobs.get(data['id'], {}).get('running'): raise ValueError('Önce süren işlemi durdur.')
                    with studio.db() as db: db.execute('UPDATE conversations SET archived=? WHERE id=?',
                                                      (int(bool(data.get('archived', True))), data['id']))
                    result = {'ok': True}
                elif path == '/api/pick-folder': result = {'folder': studio.folder_picker()}
                elif path == '/api/open-folder':
                    conv = studio.conversation(data['id'])
                    if conv['mode'] != 'work': raise ValueError('Çalışma seçmelisin.')
                    os.startfile(conv['workspace'])
                    result = {'ok': True}
                elif path == '/api/check-models': result = studio.check_models()
                else: self.send(404, {'error': 'Bulunamadı.'}); return
                self.send(200, result)
            except (ValueError, OSError, KeyError, TypeError) as error:
                self.send(400, {'error': studio.error_text(error)})
    return Handler


def open_window(url):
    candidates = [Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / 'Microsoft/Edge/Application/msedge.exe',
                  Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Google/Chrome/Application/chrome.exe',
                  Path(os.environ.get('LOCALAPPDATA', '')) / 'Google/Chrome/Application/chrome.exe']
    browser = next((path for path in candidates if path.is_file()), None)
    if browser:
        subprocess.Popen([str(browser), '--app=' + url, '--window-size=1440,960'],
                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    else: webbrowser.open(url)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-open', action='store_true')
    parser.add_argument('--data-dir', type=Path, default=DATA)
    args = parser.parse_args()
    args.data_dir.mkdir(parents=True, exist_ok=True)
    instance_path = args.data_dir / 'instance.json'
    if instance_path.is_file():
        try:
            old = json.loads(instance_path.read_text(encoding='utf-8'))
            parsed = urlparse(old['url'])
            if parsed.hostname != '127.0.0.1': raise ValueError('Geçersiz yerel adres.')
            request = Request(old['url'] + '/api/state', headers={'X-Studio-Token': old['token']})
            with urlopen(request, timeout=2) as response: valid = json.load(response).get('app') == 'Uc AI Studyo'
            if valid:
                if not args.no_open: open_window(old['url'] + '/#' + old['token'])
                return
        except (OSError, ValueError, KeyError): pass
    studio = Studio(args.data_dir)
    with ExitStack() as stack:
        studio.start_engine(stack)
        studio.import_existing()
        server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(studio))
        stack.callback(server.server_close)
        url = f'http://127.0.0.1:{server.server_port}'
        instance_path.write_text(json.dumps({'url': url, 'token': studio.token, 'pid': os.getpid()}), encoding='utf-8')
        if not args.no_open: open_window(url + '/#' + studio.token)
        try: server.serve_forever()
        except KeyboardInterrupt: pass


if __name__ == '__main__': main()

import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parent.parent
SYSTEM = ROOT / 'outputs/Uc-Ajan-Sistemi/.system'
WORK = ROOT / 'work/independent-live'
WORK.mkdir(exist_ok=True)
sys.path.insert(0, str(SYSTEM))
from nim_adapter import nim_connection, normalize

# Check exact adapter behavior locally before the one live workflow.
for model in ('deepseek-ai/deepseek-v4.1-flash', 'z-ai/glm-5.3',
              'nvidia/nemotron-3.5-super-vl-120b-a12b'):
    body = normalize({'model': model, 'max_tokens': 4096, 'reasoning_effort': 'low'})
    if model.startswith('deepseek'): assert body['reasoning_effort'] == 1
    if model.startswith('z-ai'): assert body['chat_template_kwargs']['clear_thinking'] is True
    if model.startswith('nvidia'): assert body['chat_template_kwargs']['enable_thinking'] is False

config = json.loads((SYSTEM / 'opencode.json').read_text(encoding='utf-8'))
config['permission'] = {'read': 'deny', 'edit': 'deny', 'bash': 'deny', 'webfetch': 'deny',
                        'task': {'*': 'deny', 'glm': 'allow', 'nemotron': 'allow'}}
for name, agent in config['agent'].items():
    agent['prompt'] = ('Read-only calculator review. Do not access files or shell. '
                       'Only deepseek may call task for glm and nemotron. Reply concisely in Turkish.')
    agent['steps'] = 4 if name == 'deepseek' else 2
    agent['permission'] = {'read': 'deny', 'edit': 'deny', 'bash': 'deny', 'webfetch': 'deny'}
    if name != 'deepseek': agent['permission']['task'] = 'deny'
path = WORK / 'opencode.json'
path.write_text(json.dumps(config), encoding='utf-8')
code = (ROOT / 'outputs/Hesap-Makinesi/calculator.js').read_text(encoding='utf-8')
prompt = ('Review this calculator implementation with all three agents. Immediately issue TWO task '
          'calls in ONE response: glm reviews arithmetic/input state, nemotron reviews division by zero '
          'and recovery. Supply this code in both child prompts. Each child returns at most 60 words, '
          'concrete findings or OK. No tools other than these two task calls. Collect both and give '
          'one brief Turkish conclusion. No follow-up reviews or tests.\nCODE:\n' + code)
env = os.environ.copy()
env['OPENCODE_CONFIG'] = str(path)
for key, folder in [('XDG_CONFIG_HOME', 'config'), ('XDG_DATA_HOME', 'data'),
                    ('XDG_CACHE_HOME', 'cache'), ('XDG_STATE_HOME', 'state')]:
    env[key] = str(SYSTEM / 'user' / folder)
env['OPENCODE_DISABLE_AUTOUPDATE'] = 'true'
report = {'actual_opencode': True, 'actual_nvidia': True, 'models_substituted': False,
          'attempts': 1, 'status': 'failed'}
start = time.time()
request_log = WORK / 'requests.jsonl'
lines = []

with nim_connection(env['NVIDIA_API_KEY'], request_log) as (url, token):
    env['NVIDIA_API_KEY'] = token
    env['OPENCODE_CONFIG_CONTENT'] = json.dumps({'provider': {'nvidia-nim': {
        'options': {'baseURL': url, 'apiKey': '{env:NVIDIA_API_KEY}'}}}})
    process = subprocess.Popen([str(SYSTEM / 'opencode.exe'), 'run', '--pure', '--format', 'json',
                                '--agent', 'deepseek', '--title', 'Uc Ajan Hesap Makinesi', prompt],
                               env=env, cwd=WORK, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding='utf-8', errors='replace')

    def read_output():
        for line in process.stdout:
            lines.append(line)
            try:
                event = json.loads(line)
                part = event.get('part', {})
                if part.get('tool') == 'task':
                    state = part.get('state', {})
                    print(json.dumps({'agent': state.get('input', {}).get('subagent_type'),
                                      'status': state.get('status')}, ensure_ascii=True), flush=True)
            except ValueError: pass

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    while process.poll() is None:
        if time.time() - start > 480:
            report['reason'] = 'overall_timeout'
            process.kill()
            break
        if request_log.exists():
            requests = [json.loads(line) for line in request_log.read_text(encoding='utf-8').splitlines() if line]
            failures = [request for request in requests if 'error' in request]
            if failures:
                report.update(reason='nvidia_request_failed', request_failure=failures[-1])
                process.kill()
                break
        time.sleep(0.5)
    process.wait()
    reader.join(timeout=3)
    report['exit_code'] = process.returncode
    errors = process.stderr.read()
    if errors: (WORK / 'stderr.txt').write_text(errors, encoding='utf-8')

output = ''.join(lines)
(WORK / 'events.jsonl').write_text(output, encoding='utf-8')
children = {}
final = []
for line in output.splitlines():
    try: event = json.loads(line)
    except ValueError: continue
    part = event.get('part', {})
    state = part.get('state', {})
    name = state.get('input', {}).get('subagent_type')
    if part.get('tool') == 'task' and name in ('glm', 'nemotron'):
        children[name] = {'status': state.get('status'), 'time': state.get('time'),
                          'result': state.get('output', '')[:2000]}
    if event.get('type') == 'text': final.append(part.get('text', ''))
report.update(children=children, final='\n'.join(final)[-2500:], seconds=round(time.time()-start, 2))
if len(children) == 2 and all(child['status'] == 'completed' for child in children.values()):
    a, b = [children[name]['time'] for name in ('glm', 'nemotron')]
    report['parallel'] = max(a['start'], b['start']) < min(a['end'], b['end'])
    if report['parallel'] and process.returncode == 0 and final: report['status'] = 'passed'
(SYSTEM.parent / 'OpenCode-canli-sonuc.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=True, indent=2), flush=True)

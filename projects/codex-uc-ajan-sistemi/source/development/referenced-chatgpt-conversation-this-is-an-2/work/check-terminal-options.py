"""Local verification of actual OpenCode request options; no external API calls."""
import json
import os
from pathlib import Path
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent.parent
SYSTEM = ROOT / 'outputs/Uc-Ajan-Sistemi/.system'
WORK = ROOT / 'work/terminal-check'
WORK.mkdir(exist_ok=True)
received = []

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        received.append({key: body.get(key) for key in
                         ('model', 'reasoning_effort', 'chat_template_kwargs', 'max_tokens')})
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.end_headers()
        for delta, finish in (({'role': 'assistant', 'content': 'LOCAL_OPTIONS_OK'}, None), ({}, 'stop')):
            event = {'id': 'local', 'object': 'chat.completion.chunk', 'created': 1,
                     'model': body['model'],
                     'choices': [{'index': 0, 'delta': delta, 'finish_reason': finish}]}
            self.wfile.write(('data: '+json.dumps(event)+'\n\n').encode())
        self.wfile.write(b'data: [DONE]\n\n')
        self.wfile.flush()

server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
config = json.loads((SYSTEM / 'opencode.json').read_text(encoding='utf-8'))
config['provider']['nvidia-nim']['options'].update(baseURL=f'http://127.0.0.1:{server.server_port}/v1',
                                                apiKey='local-verification-only')
for name, agent in config['agent'].items():
    agent['prompt'] = 'Reply LOCAL_OPTIONS_OK. Do not use tools.'
    agent['steps'] = 1
path = WORK / 'opencode.json'
path.write_text(json.dumps(config), encoding='utf-8')
env = os.environ.copy()
env['OPENCODE_CONFIG'] = str(path)
env['NVIDIA_API_KEY'] = 'local-verification-only'
for envname, folder in [('XDG_CONFIG_HOME', 'config'), ('XDG_DATA_HOME', 'data'),
                        ('XDG_CACHE_HOME', 'cache'), ('XDG_STATE_HOME', 'state')]:
    env[envname] = str(SYSTEM / 'user' / folder)
try:
    for name in ('deepseek', 'glm', 'nemotron'):
        process = subprocess.run([str(SYSTEM / 'opencode.exe'), 'run', '--pure', '--format', 'json',
                                  '--agent', name, 'Reply LOCAL_OPTIONS_OK.'], cwd=WORK, env=env,
                                 capture_output=True, encoding='utf-8', errors='replace', timeout=35)
        if process.returncode or 'LOCAL_OPTIONS_OK' not in process.stdout:
            raise RuntimeError(process.stderr[-800:] + process.stdout[-800:])
    print(json.dumps({'local_request_options': received}, indent=2))
    (WORK / 'request-options.json').write_text(json.dumps(received, indent=2), encoding='utf-8')
finally:
    server.shutdown()
    server.server_close()

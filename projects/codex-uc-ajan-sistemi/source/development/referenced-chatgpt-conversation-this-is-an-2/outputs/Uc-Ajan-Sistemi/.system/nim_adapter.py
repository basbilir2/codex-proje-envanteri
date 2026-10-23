"""Loopback-only OpenCode/NIM compatibility adapter. Never logs keys or prompts."""
from contextlib import contextmanager
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

MODELS = {'deepseek-ai/deepseek-v4.1-flash': 8192,
          'z-ai/glm-5.3': 8192,
          'z-ai/glm-5.3-flash': 8192,
          'nvidia/nemotron-3.5-super-vl-120b-a12b': 4096}


def normalize(body):
    model = body.get('model')
    if model not in MODELS: raise ValueError('Yalnız yapılandırılmış NVIDIA modelleri kullanılabilir.')
    body['max_tokens'] = min(int(body.pop('max_completion_tokens', body.get('max_tokens', MODELS[model]))),
                             MODELS[model])
    template = body.setdefault('chat_template_kwargs', {})
    if model.startswith('deepseek'):
        # OpenCode's generic "low" string is not DeepSeek V4.1's numeric effort.
        body['reasoning_effort'] = 1
    elif model.startswith('z-ai'):
        body['reasoning_effort'] = 'low'
        template['clear_thinking'] = True
    else:
        body.pop('reasoning_effort', None)
        template['enable_thinking'] = False
    return body


@contextmanager
def nim_connection(key, log_path, on_event=None):
    local_token = secrets.token_urlsafe(32)
    lock = threading.Lock()

    def notify(record):
        if on_event:
            try: on_event(dict(record))
            except Exception: pass

    def log(record):
        with lock:
            with Path(log_path).open('a', encoding='utf-8') as file:
                file.write(json.dumps(record, ensure_ascii=False) + '\n')

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_): pass

        def json_error(self, status, message):
            body = json.dumps({'error': {'message': message, 'type': 'nim_gateway'}}).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            auth = self.headers.get('Authorization', '')
            if not hmac.compare_digest(auth, 'Bearer ' + local_token):
                self.json_error(401, 'Yerel bağlantı anahtarı geçersiz.')
                return
            if self.path != '/v1/chat/completions':
                self.json_error(404, 'Desteklenmeyen API yolu.')
                return
            record = {'start': time.time()}
            sent = False
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 16 * 1024 * 1024: raise ValueError('İstek boyutu geçersiz.')
                body = normalize(json.loads(self.rfile.read(length)))
                record.update(model=body['model'], reasoning_effort=body.get('reasoning_effort'),
                              chat_template_kwargs=body.get('chat_template_kwargs'))
                notify(dict(record, phase='start'))
                request = Request('https://integrate.api.nvidia.com/v1/chat/completions',
                                  data=json.dumps(body).encode(), headers={
                                      'Content-Type': 'application/json',
                                      'Accept-Encoding': 'identity',
                                      'Authorization': 'Bearer ' + key})
                with urlopen(request, timeout=230) as response:
                    record.update(status=response.status, first_response=time.time())
                    notify(dict(record, phase='response'))
                    self.send_response(response.status)
                    self.send_header('Content-Type', response.headers.get('Content-Type', 'application/json'))
                    self.send_header('Cache-Control', 'no-store')
                    self.end_headers()
                    sent = True
                    while True:
                        data = response.read1(65536)
                        if not data: break
                        self.wfile.write(data)
                        self.wfile.flush()
                        if time.time() - record['start'] > 270:
                            raise TimeoutError('Toplam yanıt süresi sınırı')
            except HTTPError as error:
                record.update(status=error.code, error='nvidia_http_error')
                if not sent:
                    # Failed dependency is non-retryable in the client. Preserve the
                    # real upstream status in the message and journal, avoiding
                    # automatic quota/server-error retry loops.
                    client_status = 424 if error.code == 429 or error.code >= 500 else error.code
                    self.json_error(client_status, f'NVIDIA HTTP {error.code}: model erişimi veya kota kontrol edilmeli.')
            except (TimeoutError, OSError) as error:
                record.update(error=type(error).__name__)
                if not sent:
                    try: self.json_error(424, 'NVIDIA yanıt süresi doldu. Model değişmedi; otomatik tekrar ve ücretli geçiş yok.')
                    except (BrokenPipeError, OSError): pass
            except (ValueError, json.JSONDecodeError) as error:
                record.update(error='invalid_request')
                if not sent: self.json_error(400, str(error))
            finally:
                record['end'] = time.time()
                log(record)
                notify(dict(record, phase='end'))

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/v1', local_token
    finally:
        server.shutdown()
        server.server_close()

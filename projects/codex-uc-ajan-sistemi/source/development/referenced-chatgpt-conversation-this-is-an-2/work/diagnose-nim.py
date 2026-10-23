import concurrent.futures
import json
import os
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

MODELS = {'deepseek': 'deepseek-ai/deepseek-v4.1-flash', 'glm': 'z-ai/glm-5.3'}

def probe(agent):
    start = time.monotonic()
    body = {'model': MODELS[agent], 'messages': [{'role': 'user', 'content': 'Reply only OK.'}],
            'max_tokens': 256, 'stream': True, 'temperature': 1}
    if agent == 'glm':
        body.update(reasoning_effort='low', chat_template_kwargs={'clear_thinking': True})
    else:
        body['reasoning_effort'] = 1
    req = Request('https://integrate.api.nvidia.com/v1/chat/completions',
                  data=json.dumps(body).encode(), headers={
                      'Authorization': 'Bearer ' + os.environ['NVIDIA_API_KEY'],
                      'Content-Type': 'application/json', 'Accept': 'text/event-stream'})
    result = {'agent': agent, 'model': MODELS[agent]}
    try:
        with urlopen(req, timeout=50) as response:
            result['http_status'] = response.status
            content, reasoning = '', 0
            for raw in response:
                line = raw.decode('utf-8', 'replace').strip()
                if not line.startswith('data:'): continue
                if line[5:].strip() == '[DONE]': break
                event = json.loads(line[5:])
                for choice in event.get('choices', []):
                    delta = choice.get('delta', {})
                    content += delta.get('content') or ''
                    reasoning += len(delta.get('reasoning_content') or '')
                if content.strip(): break
                if time.monotonic() - start > 65: raise TimeoutError('overall_deadline')
            result.update(status='passed' if content.strip() else 'no_answer',
                          answer=content[:120], reasoning_characters=reasoning)
    except HTTPError as exc:
        result.update(status='failed', http_status=exc.code,
                      detail=exc.read(1000).decode('utf-8', 'replace'))
    except Exception as exc:
        result.update(status='failed', error_type=type(exc).__name__, detail=str(exc)[:150])
    result['seconds'] = round(time.monotonic() - start, 2)
    print(json.dumps(result), flush=True)
    return result

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(probe, MODELS))
with open(os.path.join(os.path.dirname(__file__), 'nim-diagnosis.json'), 'w', encoding='utf-8') as file:
    json.dump(results, file, indent=2)

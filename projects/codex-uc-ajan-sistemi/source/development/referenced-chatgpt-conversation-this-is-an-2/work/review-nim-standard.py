"""One actual parallel calculator review, using documented standard request fields."""
import concurrent.futures
import json
import os
from pathlib import Path
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parent.parent
MODELS = {'deepseek': 'deepseek-ai/deepseek-v4.1-flash', 'glm': 'z-ai/glm-5.3',
          'nemotron': 'nvidia/nemotron-3.5-super-vl-120b-a12b'}
CODE = (ROOT / 'outputs/Hesap-Makinesi/calculator.js').read_text(encoding='utf-8')
SCOPES = {'deepseek': 'Review the arithmetic implementation and summarize whether it is correct.',
          'glm': 'Review state transitions and decimal input for bugs.',
          'nemotron': 'Review division by zero and error recovery for bugs.'}

def review(agent):
    start = time.time()
    body = {'model': MODELS[agent], 'messages': [{'role': 'user', 'content':
            SCOPES[agent] + ' Reply in at most 60 words with concrete bugs or OK.\n' + CODE}],
            'max_tokens': 512, 'stream': True, 'temperature': 1, 'top_p': 0.95}
    request = Request('https://integrate.api.nvidia.com/v1/chat/completions',
                      data=json.dumps(body).encode(), headers={
                          'Authorization': 'Bearer ' + os.environ['NVIDIA_API_KEY'],
                          'Content-Type': 'application/json'})
    result = {'agent': agent, 'model': MODELS[agent], 'started_at': start}
    try:
        with urlopen(request, timeout=155) as response:
            result.update(http_status=response.status, headers_after=round(time.time()-start, 2))
            answer, reasoning = '', 0
            for raw in response:
                line = raw.decode('utf-8', 'replace').strip()
                if not line.startswith('data:'): continue
                if line[5:].strip() == '[DONE]': break
                event = json.loads(line[5:])
                for choice in event.get('choices', []):
                    delta = choice.get('delta', {})
                    answer += delta.get('content') or ''
                    reasoning += len(delta.get('reasoning_content') or '')
                if time.time()-start > 180: raise TimeoutError('Overall deadline')
            result.update(status='passed' if answer.strip() else 'no_final_answer',
                          answer=answer[:2000], reasoning_characters=reasoning)
    except HTTPError as error:
        result.update(status='failed', http_status=error.code,
                      detail=error.read(700).decode('utf-8', 'replace'))
    except Exception as error:
        result.update(status='failed', error_type=type(error).__name__, detail=str(error)[:120])
    result['ended_at'] = time.time()
    result['seconds'] = round(result['ended_at']-start, 2)
    print(json.dumps(result, ensure_ascii=True), flush=True)
    return result

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    results = list(pool.map(review, MODELS))
report = {'real_nvidia_requests': True, 'models_substituted': False, 'results': results,
          'all_passed': all(r['status']=='passed' for r in results),
          'requests_overlap': max(r['started_at'] for r in results) < min(r['ended_at'] for r in results)}
(ROOT / 'outputs/Uc-Ajan-Sistemi/canli-durum.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

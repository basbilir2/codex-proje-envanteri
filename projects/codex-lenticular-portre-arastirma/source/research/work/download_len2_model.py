from pathlib import Path
import hashlib,json,subprocess,urllib.request
p=Path(r'C:\Users\USER\Documents\Codex\2026-10-10\referenced-chatgpt-conversation-this-is-an\outputs\len 2\model')
p.mkdir(exist_ok=True)
revision='530227a7d994db8eca5ab5ced2fb692b614357fd'
name='Qwen3-14B-Q4_K_M.gguf'
sha='500a8806e85ee9c83f3ae08420295592451379b4f8cf2d0f41c15dffeb6b81f0'
url=f'https://huggingface.co/Qwen/Qwen3-14B-GGUF/resolve/{revision}/{name}'
target=p/name
part=p/(name+'.part')
if not target.exists():
    result=subprocess.run(['curl.exe','--location','--fail','--retry','2','--connect-timeout','30','--continue-at','-','--silent','--show-error','--output',str(part),url])
    if result.returncode:raise SystemExit(result.returncode)
    with part.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    if actual!=sha:raise RuntimeError('Downloaded model checksum mismatch; partial file retained, not activated.')
    part.rename(target)
else:
    with target.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    if actual!=sha:raise RuntimeError('Existing model checksum mismatch; not activated.')
for filename in ['LICENSE','README.md']:
    with urllib.request.urlopen(f'https://huggingface.co/Qwen/Qwen3-14B-GGUF/resolve/{revision}/{filename}',timeout=30) as response:
        (p/filename).write_bytes(response.read())
record=dict(model='Qwen/Qwen3-14B-GGUF',revision=revision,filename=name,bytes=target.stat().st_size,sha256=actual,
            sha256_verified=True,source_url=url,license='Apache-2.0',local_training_performed=False,role='pretrained_baseline_candidate')
(p/'model_manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record),flush=True)

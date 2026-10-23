"""Read and pin official training weight metadata; never download weights."""
import json
import pathlib
import requests

root = pathlib.Path(__file__).resolve().parent / 'pilot-20261022'
root.mkdir(parents=True, exist_ok=True)
specs = [
    ('Qwen/Qwen-Image-Edit-2511', 'transformer/diffusion_pytorch_model.safetensors.index.json'),
    ('Qwen/Qwen-Image', 'text_encoder/model.safetensors.index.json'),
]
records = []
for repo, index in specs:
    info = requests.get('https://huggingface.co/api/models/' + repo, timeout=25)
    info.raise_for_status()
    revision = info.json()['sha']
    response = requests.get(f'https://huggingface.co/{repo}/resolve/{revision}/{index}', timeout=25)
    response.raise_for_status()
    records.append({'repo': repo, 'revision': revision, 'index': index,
                    'bytes': response.json()['metadata']['total_size'],
                    'files': sorted(set(response.json()['weight_map'].values()))})
total = sum(r['bytes'] for r in records)
(root / 'weights.json').write_text(json.dumps({'models': records,
    'transformer_plus_text_encoder_bytes': total, 'vae_tokenizer_processor_additional': True}, indent=2), encoding='utf-8')
print('Transformer + text encoder GiB:', round(total / 2**30, 2))
print('Only metadata fetched; no weight downloads or GPU use.')

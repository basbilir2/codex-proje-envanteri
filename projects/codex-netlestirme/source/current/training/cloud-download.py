"""Download only the revision-pinned training dependencies on the cloud machine."""
import json
import os
from pathlib import Path
from huggingface_hub import snapshot_download

root = Path(__file__).resolve().parent / 'pilot-20261022'
manifest = json.loads((root / 'weights.json').read_text())
base = root / 'models'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
for i, item in enumerate(manifest['models']):
    folder = 'transformer/' if i == 0 else 'text_encoder/'
    patterns = [folder + name for name in item['files']] + [item['index']]
    if i == 1:
        patterns += ['tokenizer/*', 'vae/diffusion_pytorch_model.safetensors']
    snapshot_download(item['repo'], revision=item['revision'], local_dir=str(base / item['repo']),
                      allow_patterns=patterns, max_workers=2)
support = manifest['processor_model']
snapshot_download(support['repo'], revision=support['revision'], local_dir=str(base / support['repo']),
                  allow_patterns=support['patterns'], max_workers=2)
print('PINNED_TRAINING_WEIGHTS_READY', flush=True)

"""One capped cloud pilot. No retries, model substitutions or parameter sweeps."""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
import torch

root = Path(__file__).resolve().parent
data = root / 'pilot-20261022'
cfg = json.loads((data / 'pilot.json').read_text())
record = {'kind': 'LoRA adaptation pilot', 'status': 'running', 'configuration': cfg, 'phases': []}
started = time.monotonic()
os.environ['DIFFSYNTH_MODEL_BASE_PATH'] = str(data / 'models')
os.environ['DIFFSYNTH_SKIP_DOWNLOAD'] = 'True'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['WANDB_DISABLED'] = 'true'
os.environ['PYTHONUNBUFFERED'] = '1'

def report():
    record['seconds'] = round(time.monotonic() - started, 2)
    (data / 'pilot-result.json').write_text(json.dumps(record, indent=2), encoding='utf-8')

def phase(name, command, limit):
    print('STAGE=' + name, flush=True)
    start = time.monotonic()
    with (data / (name.lower() + '.log')).open('w', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=str(root), stdout=log, stderr=subprocess.STDOUT, timeout=limit, check=False)
    record['phases'].append({'phase': name, 'seconds': round(time.monotonic() - start, 2), 'exit_code': result.returncode})
    report()
    if result.returncode:
        raise RuntimeError(name + ' failed; no automatic retry')

try:
    if not torch.cuda.is_available() or torch.cuda.get_device_properties(0).total_memory / 2**30 < cfg['minimum_gpu_gib']:
        raise RuntimeError('GPU prerequisite not met')
    train = json.loads((data / 'train.json').read_text())
    validation = json.loads((data / 'validation.json').read_text())
    if len(train) != 6 or len(validation) != 2:
        raise RuntimeError('Unexpected dataset size')
    if any(not isinstance(row['edit_image'], list) or len(row['edit_image']) != 1 for row in train + validation):
        raise RuntimeError('Qwen 2511 requires one-element image lists for the multi-image conditioning path')
    record['conditioning_contract'] = 'Qwen-Image-Edit-2511 multi-image path with one-element lists'
    if {r['image'] for r in train} & {r['image'] for r in validation}:
        raise RuntimeError('Training/evaluation leakage')
    dit = 'Qwen/Qwen-Image-Edit-2511:transformer/diffusion_pytorch_model*.safetensors'
    text = 'Qwen/Qwen-Image:text_encoder/model*.safetensors'
    vae = 'Qwen/Qwen-Image:vae/diffusion_pytorch_model.safetensors'
    common = [sys.executable, str(root / 'seeded-train.py'), '--model_id_with_origin_paths', ','.join([dit, text, vae]),
              '--height', str(cfg['height']), '--width', str(cfg['width']), '--max_pixels', str(cfg['height'] * cfg['width']),
              '--learning_rate', str(cfg['learning_rate']), '--num_epochs', '1', '--lora_base_model', 'dit',
              '--lora_rank', str(cfg['lora_rank']), '--lora_target_modules',
              'to_q,to_k,to_v,add_q_proj,add_k_proj,add_v_proj,to_out.0,to_add_out,img_mlp.net.2,img_mod.1,txt_mlp.net.2,txt_mod.1',
              '--remove_prefix_in_ckpt', 'pipe.dit.', '--dataset_num_workers', '0', '--zero_cond_t',
              '--use_gradient_checkpointing', '--use_gradient_checkpointing_offload']
    if '--reuse-cache' in sys.argv:
        cached = sorted((data / 'cache').rglob('*.pth'))
        if len(cached) != len(train) or any(p.stat().st_size < 1024 for p in cached):
            raise RuntimeError('Incomplete preprocessing cache')
        # Upstream stores runtime flags in inputs_shared during preprocessing.
        # Training arguments do not override cached flags. Reject older caches.
        for path in cached:
            inputs_shared = torch.load(path, map_location='cpu', weights_only=False)[0]
            if not inputs_shared.get('use_gradient_checkpointing') or not inputs_shared.get('use_gradient_checkpointing_offload'):
                raise RuntimeError('Cache lacks checkpoint/offload flags; regenerate preprocessing')
        record['reused_cache_examples'] = len(cached)
    else:
        phase('CACHE', common + ['--dataset_base_path', str(data), '--dataset_metadata_path', str(data / 'train.json'),
              '--data_file_keys', 'image,edit_image', '--extra_inputs', 'edit_image', '--dataset_repeat', '1',
              '--output_path', str(data / 'cache'), '--offload_models', dit, '--fp8_models', text,
              '--task', 'sft:data_process'], cfg['cache_timeout_seconds'])
    phase('TRAIN', common + ['--dataset_base_path', str(data / 'cache'), '--dataset_repeat', str(cfg['dataset_repeat']),
          '--output_path', str(data / 'checkpoints'), '--offload_models', text + ',' + vae, '--fp8_models', dit,
          '--save_steps', '24', '--enable_csv_log', '--task', 'sft:train'], cfg['training_timeout_seconds'])
    checkpoint = data / 'checkpoints' / cfg['checkpoint_file']
    if not checkpoint.is_file() or checkpoint.stat().st_size < 1024:
        raise RuntimeError('No trained checkpoint')
    phase('EVALUATE', [sys.executable, str(root / 'cloud-evaluate.py')], cfg['evaluation_timeout_seconds'])
    record.update(status='completed', checkpoint=str(checkpoint), quality_accepted=False)
    print('PILOT_FILES_READY', flush=True)
except Exception as error:
    record.update(status='failed', error=str(error))
    print('PILOT_FAILED=' + str(error), flush=True)
    raise
finally:
    report()

"""Capped heldout inference, optionally with matched previous-weight comparisons."""
import json
import os
import time
from pathlib import Path
import torch
from PIL import Image
from diffsynth.pipelines.qwen_image import QwenImagePipeline, ModelConfig

root = Path(__file__).resolve().parent
data = root / 'pilot-20261022'
cfg = json.loads((data / 'pilot.json').read_text())
manifest = json.loads((data / 'manifest.json').read_text())
out = data / 'evaluation'
out.mkdir(exist_ok=True)
memory = dict(offload_dtype=torch.float8_e4m3fn, offload_device='cpu',
              onload_dtype=torch.float8_e4m3fn, onload_device='cuda',
              preparing_dtype=torch.float8_e4m3fn, preparing_device='cuda',
              computation_dtype=torch.bfloat16, computation_device='cuda')
pipe = QwenImagePipeline.from_pretrained(torch_dtype=torch.bfloat16, device='cuda', model_configs=[
    ModelConfig(model_id='Qwen/Qwen-Image-Edit-2511', origin_file_pattern='transformer/diffusion_pytorch_model*.safetensors', **memory),
    ModelConfig(model_id='Qwen/Qwen-Image', origin_file_pattern='text_encoder/model*.safetensors', **memory),
    ModelConfig(model_id='Qwen/Qwen-Image', origin_file_pattern='vae/diffusion_pytorch_model.safetensors'),
], tokenizer_config=ModelConfig(path=str(data / 'models/Qwen/Qwen-Image/tokenizer')),
   processor_config=ModelConfig(path=str(data / 'models/Qwen/Qwen-Image-Edit/processor')))
cases = [(r['name'],data/r['image'],r['width'],r['height']) for r in cfg['evaluation_cases']] if cfg.get('evaluation_cases') else [
    ('mavi', data / 'holdout-mavi.jpeg', 1024, 640),('heldout07', data / 'images/07-surface.png', 768, 512)]
results = []
conditions=[True,False] if cfg.get('evaluate_updated_first') else [False,True]
if cfg.get('previous_evaluation_cases')==[]:
    conditions=[True]
for adapted in conditions:
    pipe.clear_lora()
    if adapted:
        pipe.load_lora(pipe.dit, str(data / 'checkpoints' / cfg['checkpoint_file']))
    elif cfg.get('initial_lora'):
        pipe.load_lora(pipe.dit,str(data/cfg['initial_lora']))
    for name, path, width, height in cases:
        if not adapted and cfg.get('previous_evaluation_cases') is not None and name not in cfg['previous_evaluation_cases']:
            continue
        start = time.monotonic()
        image = pipe(manifest['instruction'], edit_image=[Image.open(path).convert('RGB')], seed=cfg['seed'],
                     num_inference_steps=cfg['evaluation_steps'], height=height, width=width, zero_cond_t=True)
        output = name + ('-lora.png' if adapted else '-base.png')
        image.save(out / output)
        results.append({'case': name, 'adapted': adapted, 'file': output, 'seconds': round(time.monotonic()-start,2),
                        'seed': cfg['seed'], 'steps': cfg['evaluation_steps'], 'width': width, 'height': height,
                        'condition': 'updated_lora' if adapted else ('previous_lora' if cfg.get('initial_lora') else 'unadapted_base')})
        (out / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
        print('EVAL_READY=' + output, flush=True)

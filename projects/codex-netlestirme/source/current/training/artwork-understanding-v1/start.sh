#!/usr/bin/env bash
set -euo pipefail
export PYTHONUNBUFFERED=1 HF_HUB_DISABLE_TELEMETRY=1
cd /workspace/artwork-understanding-v1
trap 'printf "{\"exit_code\":%s}\n" "$?" > job-status.json' EXIT
python - <<'PY'
import json,os,time
g=json.load(open('/tmp/recovery-stop-guard.json'));assert g['armed'] and g['pod_id']==os.environ['RUNPOD_POD_ID'] and g['deadline_unix']>time.time()+1600
os.kill(g['pid'],0)
PY
echo STAGE=INSTALL_UNDERSTANDING_TRAINING
python -m pip install --disable-pip-version-check transformers==4.57.1 peft==0.17.1 huggingface_hub pillow > install.log 2>&1
python -m pip freeze > environment.txt
echo STAGE=DOWNLOAD_EXISTING_ENCODER_ONLY
if [ ! -e models ] && [ -d /workspace/recovery-training/pilot-20261022/models ]; then
  ln -s /workspace/recovery-training/pilot-20261022/models models
fi
python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download('Qwen/Qwen-Image',revision='75e0b4be04f60ec59a75f475837eced720f823b6',allow_patterns=['text_encoder/*'],local_dir='models/Qwen/Qwen-Image')
snapshot_download('Qwen/Qwen-Image-Edit',revision='ac7f9318f633fc4b5778c59367c8128225f1e3de',allow_patterns=['processor/*'],local_dir='models/Qwen/Qwen-Image-Edit')
PY
echo STAGE=TRAIN_UNDERSTANDING_NOT_DIFFUSION
timeout 1800 python -u train.py
echo STAGE=EXPORT_UNDERSTANDING_ADAPTER
git clone --depth 1 --branch b11829 https://github.com/ggml-org/llama.cpp.git llama.cpp > export.log 2>&1
python -m pip install --disable-pip-version-check -r llama.cpp/requirements/requirements-convert_lora_to_gguf.txt >> export.log 2>&1
python llama.cpp/convert_lora_to_gguf.py --base models/Qwen/Qwen-Image/text_encoder --outfile adapter/artwork-understanding-f16.gguf --outtype f16 adapter >> export.log 2>&1
echo UNDERSTANDING_JOB_COMPLETED

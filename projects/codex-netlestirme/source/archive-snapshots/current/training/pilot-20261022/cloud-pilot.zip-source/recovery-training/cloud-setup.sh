#!/usr/bin/env bash
set -euo pipefail
cd /workspace/recovery-training
export PYTHONUNBUFFERED=1 HF_HUB_DISABLE_TELEMETRY=1
echo STAGE=INSTALL
if [ ! -d DiffSynth-Studio/.git ]; then
  git init DiffSynth-Studio
  git -C DiffSynth-Studio remote add origin https://github.com/modelscope/DiffSynth-Studio.git
  git -C DiffSynth-Studio fetch --depth 1 origin d188f01d09013688dea27cc28f2e8dc0953c2543
  git -C DiffSynth-Studio checkout --detach FETCH_HEAD
fi
test "$(git -C DiffSynth-Studio rev-parse HEAD)" = d188f01d09013688dea27cc28f2e8dc0953c2543
python -m pip install --disable-pip-version-check -e ./DiffSynth-Studio huggingface_hub transformers==4.57.1 peft==0.17.1 >pilot-20261022/install.log 2>&1
python -m pip freeze >pilot-20261022/environment.txt
python -c 'import shutil; assert shutil.disk_usage(".").free > 65*2**30, "Training disk too small"'
echo STAGE=DOWNLOAD_TRAINING_WEIGHTS
timeout 1200 python -u cloud-download.py >pilot-20261022/download.log 2>&1
echo STAGE=TRAINING_PILOT
python -u cloud-pilot.py

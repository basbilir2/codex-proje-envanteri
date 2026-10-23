#!/usr/bin/env bash
set -euo pipefail
cd /workspace/netlestirme
trap 'code=$?; printf "CLOUD_JOB_EXIT=%s\n" "$code"' EXIT
echo STAGE=PREPARE_MODEL
timeout 900 python -u prepare.py >download.log 2>&1
mkdir -p runtime-cuda jobs/design-recovery
tar -xzf /workspace/cuda-runtime.tar.gz -C runtime-cuda
chmod +x runtime-cuda/sd-cli
export LD_LIBRARY_PATH="$(python -c 'import torch,pathlib; print(pathlib.Path(torch.__file__).parent / "lib")'):/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}"
echo STAGE=RECONSTRUCT_DESIGN
python -u qwen_worker.py --exe runtime-cuda/sd-cli --input inputs/mavi.jpeg --output jobs/design-recovery/result.png --width 1024 --height 640 --steps 40 --task extract-design --timeout 600
echo STAGE=OUTPUT_READY

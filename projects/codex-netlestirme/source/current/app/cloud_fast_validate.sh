#!/usr/bin/env bash
set -euo pipefail
cd /workspace/netlestirme
while pgrep -f '^bash cloud_validate.sh$' >/dev/null; do sleep 5; done
test -f jobs/portrait/result.png
python -u qwen_worker.py --exe sd/build/bin/sd-cli --input inputs/portrait-degraded.jpeg --output jobs/portrait-fast/result.png --width 512 --height 512 --timeout 300 --lightning
printf '\nHIZLANDIRILMIS_CIKTI_HAZIR\n'

#!/usr/bin/env bash
set -euo pipefail
cd /workspace/netlestirme
python -u qwen_worker.py --exe sd/build/bin/sd-cli --input inputs/mavi.jpeg --output jobs/mavi/result.png --width 512 --height 1104 --timeout 600
python -u qwen_worker.py --exe sd/build/bin/sd-cli --input inputs/portrait-degraded.jpeg --output jobs/portrait/result.png --width 512 --height 512 --timeout 600
printf '\nGERCEK_CIKTILAR_HAZIR\n'

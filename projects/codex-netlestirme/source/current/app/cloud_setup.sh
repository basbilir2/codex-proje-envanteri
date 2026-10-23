#!/usr/bin/env bash
set -euo pipefail
cd /workspace/netlestirme
python -u prepare.py >download.log 2>&1 &
DOWNLOAD_PID=$!
trap 'kill "$DOWNLOAD_PID" 2>/dev/null || true' EXIT
if ! command -v cmake >/dev/null; then python -m pip install cmake==3.31.6; fi
if [ ! -d sd/.git ]; then
  git init sd
  git -C sd remote add origin https://github.com/leejet/stable-diffusion.cpp.git
  git -C sd fetch --depth 1 origin 845646b034a12ed844966c84bd7585c8fcb37b7f
  git -C sd checkout --detach FETCH_HEAD
  git -C sd submodule update --init --depth 1
fi
cmake -S sd -B sd/build -DSD_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=86 -DCMAKE_BUILD_TYPE=Release -DSD_BUILD_EXAMPLES=ON
cmake --build sd/build --target sd-cli -j 4
wait "$DOWNLOAD_PID"
sd/build/bin/sd-cli --list-devices
printf '\nKURULUM_TAMAM\n'

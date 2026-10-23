$ErrorActionPreference = 'Stop'
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Önce .\setup.ps1 çalıştırın (Python 3.10–3.13).' }
& $taskPython -m pip install 'torch==2.14.1+cpu' 'torchvision==0.29.1+cpu' --index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE -ne 0) { throw 'CPU PyTorch kurulamadı.' }
& $taskPython -m pip install -r (Join-Path $PSScriptRoot 'requirements-depth.txt')
if ($LASTEXITCODE -ne 0) { throw 'Depth bağımlılıkları kurulamadı.' }
& $taskPython -m pip install --no-deps 'depth-anything-3 @ git+https://github.com/ByteDance-Seed/Depth-Anything-3.git@3d835ec1a5802d64a8b8b15f817a1ab54809bfe4'
if ($LASTEXITCODE -ne 0) { throw 'DA3 kaynak paketi kurulamadı. Git bağlantısını kontrol edin.' }
Write-Host 'Yerel depth hazır. İlk çalıştırmada resmi model ağırlıkları indirilir.'

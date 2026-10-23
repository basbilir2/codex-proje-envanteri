$ErrorActionPreference = 'Stop'
$qualityPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $qualityPython -c 'import torch, numpy, scipy'
if ($LASTEXITCODE -ne 0) { throw 'Önce setup-depth.ps1 ile yerel derinlik ortamını kurun.' }
& $qualityPython -m pip install -r (Join-Path $PSScriptRoot 'requirements-quality.txt')
if ($LASTEXITCODE -ne 0) { throw 'İnce kenar bileşenleri kurulamadı.' }
$qualityModelFolder = Join-Path $PSScriptRoot '.models\lama'
New-Item -ItemType Directory -Path $qualityModelFolder -Force | Out-Null
$qualityModelPath = Join-Path $qualityModelFolder 'big-lama.pt'
$qualityModelUrl = 'https://github.com/enesmsahin/simple-lama-inpainting/releases/download/v0.1.0/big-lama.pt'
$qualityExpectedHash = '7ba7aa7ac37a4d41fdbbeba3a2af7ead18058552997e3a3cd1a3b2210c9e6b4c'
if (-not (Test-Path -LiteralPath $qualityModelPath)) {
    $qualityPartPath = $qualityModelPath + '.part'
    Invoke-WebRequest -Uri $qualityModelUrl -OutFile $qualityPartPath
    if ((Get-FileHash -LiteralPath $qualityPartPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $qualityExpectedHash) { throw 'Model indirmesi doğrulanamadı.' }
    Move-Item -LiteralPath $qualityPartPath -Destination $qualityModelPath
}
if ((Get-FileHash -LiteralPath $qualityModelPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $qualityExpectedHash) { throw 'Mevcut model dosyası beklenen sürümle uyuşmuyor; dosya korundu.' }
@{url=$qualityModelUrl; release='v0.1.0'; sha256=$qualityExpectedHash; device='cpu'; format='TorchScript'; upstream='https://github.com/advimman/lama'; conversion='https://github.com/enesmsahin/simple-lama-inpainting'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $qualityModelFolder 'provenance.json') -Encoding utf8
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/advimman/lama/main/LICENSE' -OutFile (Join-Path $qualityModelFolder 'LAMA_LICENSE.txt')
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/enesmsahin/simple-lama-inpainting/main/LICENSE' -OutFile (Join-Path $qualityModelFolder 'CONVERSION_LICENSE.txt')
Write-Host 'Yerel ince kenar ve arka plan bileşenleri hazır. İlk kenar işlemi derleme nedeniyle daha uzun sürebilir.'

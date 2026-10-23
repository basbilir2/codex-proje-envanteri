param([switch]$DownloadModels)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$recoveryNode = Get-Command node -ErrorAction Stop
$recoveryPython = Get-Command python -ErrorAction Stop
& $recoveryNode.Source --version
& $recoveryPython.Source --version
& npm.cmd ci --ignore-scripts
if ($LASTEXITCODE -ne 0) { throw 'Node bağımlılıkları kurulamadı.' }
& $recoveryNode.Source --input-type=module -e "import sharp from 'sharp'; console.log('Görsel modülü hazır:', sharp.versions.sharp)"
if ($LASTEXITCODE -ne 0) { throw 'Görsel modülü yüklenemedi.' }
$recoveryConfigPath = Join-Path $PSScriptRoot 'runtime-config.json'
$recoveryConfig = Get-Content -LiteralPath $recoveryConfigPath -Raw | ConvertFrom-Json
$recoveryConfig.python = $recoveryPython.Source
if ($DownloadModels) {
    & $recoveryPython.Source prepare.py
    if ($LASTEXITCODE -ne 0) { throw 'Model doğrulaması tamamlanamadı.' }
    & $recoveryPython.Source prepare_lightning.py
    if ($LASTEXITCODE -ne 0) { throw 'Hızlandırıcı doğrulanamadı.' }
    & $recoveryPython.Source prepare_background.py
    if ($LASTEXITCODE -ne 0) { throw 'Arka plan modeli doğrulanamadı.' }
}
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $recoveryConfig.runtime))) {
    if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'runtime/sd-cli.exe')) {
        $recoveryConfig.runtime = 'runtime/sd-cli.exe'
        $recoveryConfig.backend = 'cpu'
    } else { throw 'Yerel model çalıştırıcısı eksik. Model kurulum aşaması gerekli.' }
}
$recoveryConfig | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $recoveryConfigPath -Encoding utf8NoBOM
& npm.cmd test
if ($LASTEXITCODE -ne 0) { throw 'Kontroller geçmedi.' }
Write-Output 'Kurulum kontrolleri geçti. Bu sonuç modelin tasarım kurtarma kalite/hız kabulü değildir.'

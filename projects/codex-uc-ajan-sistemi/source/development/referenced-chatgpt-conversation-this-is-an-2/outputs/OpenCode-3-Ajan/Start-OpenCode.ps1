param(
    [string]$ProjectPath,
    [switch]$Validate,
    [switch]$Test,
    [switch]$Offline
)
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (-not $ProjectPath) { $ProjectPath = $workspace }
$ProjectPath = (Resolve-Path -LiteralPath $ProjectPath).Path
if (-not (Test-Path -LiteralPath $ProjectPath -PathType Container)) { throw 'Proje klasörü bulunamadı.' }
. (Join-Path $PSScriptRoot 'Import-NvidiaEnvironment.ps1')
$runtime = Join-Path $workspace 'work\runtime'
$cli = Join-Path $runtime 'node_modules\.bin\opencode.cmd'
if (-not (Test-Path -LiteralPath $cli)) {
    New-Item -ItemType Directory -Force -Path $runtime | Out-Null
    & npm.cmd install --prefix $runtime --no-audit --no-fund opencode-ai@1.19.3
    if ($LASTEXITCODE -ne 0) { throw 'OpenCode kurulamadı.' }
}
if ($Validate -or $Test -or $Offline) {
    $testArgs = @((Join-Path $PSScriptRoot 'verify.py'), '--cli', $cli)
    if ($Test) { $testArgs += '--live' }
    & python @testArgs
    exit $LASTEXITCODE
}
if (-not $env:NVIDIA_API_KEY) { throw 'NVIDIA anahtarı eksik. NVIDIA-Anahtarini-Kaydet.cmd dosyasını açın.' }
Push-Location -LiteralPath $ProjectPath
try {
    & $cli --agent deepseek --model 'nvidia-nim/deepseek-ai/deepseek-v4.1-flash'
    exit $LASTEXITCODE
} finally { Pop-Location }

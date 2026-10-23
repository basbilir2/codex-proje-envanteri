param([string]$PythonPath)
$ErrorActionPreference = 'Stop'
if (-not $PythonPath) {
    $taskBundled = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    $PythonPath = if (Test-Path -LiteralPath $taskBundled) { $taskBundled } else { 'python' }
}
& $PythonPath -m venv (Join-Path $PSScriptRoot '.venv')
if ($LASTEXITCODE -ne 0) { throw 'Python ortamı oluşturulamadı.' }
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $taskPython -m pip install -e $PSScriptRoot
if ($LASTEXITCODE -ne 0) { throw 'Proje kurulamadı.' }
Write-Host 'Kurulum tamamlandı. .\run.ps1 doctor veya .\run.ps1 demo kullanın.'

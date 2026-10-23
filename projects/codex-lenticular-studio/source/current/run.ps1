param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
$ErrorActionPreference = 'Stop'
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    throw 'Önce setup.ps1 çalıştırın.'
}
Push-Location $PSScriptRoot
try {
    & $taskPython -m lenticular @Arguments
    $taskExit = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $taskExit

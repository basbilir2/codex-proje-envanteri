$ErrorActionPreference = 'Stop'
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Önce setup.ps1 ve setup-depth.ps1 çalıştırın.' }
$taskState = Join-Path $PSScriptRoot '.studio\server.json'
function Open-ReadyStudio {
    if (Test-Path -LiteralPath $taskState) {
        try {
            $taskInfo = Get-Content -LiteralPath $taskState -Raw | ConvertFrom-Json
            $taskUrl = [uri]$taskInfo.url
            if ($taskUrl.Host -ne '127.0.0.1' -or $taskInfo.root -ne $PSScriptRoot) { return $false }
            $taskProbe = Invoke-RestMethod -Uri ($taskInfo.url.Replace('/?','/api/state?')) -TimeoutSec 2
            if ($taskProbe.schema_version -eq 1) { Start-Process $taskInfo.url; return $true }
        } catch { }
    }
    return $false
}
if (Open-ReadyStudio) { exit 0 }
$taskLocal = Join-Path $PSScriptRoot '.studio'
New-Item -ItemType Directory -Path $taskLocal -Force | Out-Null
Start-Process -FilePath $taskPython -ArgumentList '-m','lenticular.studio','--no-browser' -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskLocal 'app.log') -RedirectStandardError (Join-Path $taskLocal 'app-errors.log')
for ($taskAttempt=0; $taskAttempt -lt 20; $taskAttempt++) {
    Start-Sleep -Milliseconds 500
    if (Open-ReadyStudio) { exit 0 }
}
throw 'Uygulama açılamadı. .studio\app-errors.log dosyasını kontrol edin.'

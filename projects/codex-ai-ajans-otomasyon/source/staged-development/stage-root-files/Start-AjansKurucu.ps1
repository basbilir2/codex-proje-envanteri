[CmdletBinding()]
param([switch]$NoBrowser)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Find-Docker {
  $command = Get-Command docker -ErrorAction SilentlyContinue
  if ($command) { return $command.Source }
  $candidates = @(
    (Join-Path $env:ProgramFiles 'Docker\Docker\resources\bin\docker.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Docker\Docker\resources\bin\docker.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe')
  )
  return $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}

function Unprotect-LocalValue([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { throw 'Kurulum bilgisi eksik. Ajans Kurucu kurulumunu yeniden çalıştır.' }
  $cipher = [IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8).Trim()
  $secure = ConvertTo-SecureString -String $cipher
  return [Net.NetworkCredential]::new('', $secure).Password
}

$docker = Find-Docker
if (-not $docker) { throw 'Docker Desktop bulunamadı. Önce Docker Desktop kurulmalı; sonra bu simge yeniden açılmalı.' }

$secretRoot = Join-Path $root 'secrets\creator'
$env:AJANS_CREATOR_PASSWORD_HASH = Unprotect-LocalValue (Join-Path $secretRoot 'password-hash.dpapi')
$env:AJANS_CREATOR_ENCRYPTION_KEY = Unprotect-LocalValue (Join-Path $secretRoot 'encryption-key.dpapi')

try {
  & $docker compose --project-directory $root -f (Join-Path $root 'docker-compose.creator.yml') up -d
  if ($LASTEXITCODE -ne 0) { throw 'Ajans Kurucu başlatılamadı.' }
} finally {
  Remove-Item Env:AJANS_CREATOR_PASSWORD_HASH,Env:AJANS_CREATOR_ENCRYPTION_KEY -ErrorAction SilentlyContinue
}

$ready = $false
$deadline = (Get-Date).AddSeconds(45)
do {
  try { $ready = (Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5684/api/health' -TimeoutSec 3).StatusCode -eq 200 } catch { $ready = $false }
  if (-not $ready) { Start-Sleep -Milliseconds 500 }
} while (-not $ready -and (Get-Date) -lt $deadline)

if (-not $ready) { throw 'Ajans Kurucu zamanında açılmadı. Docker Desktop durumunu kontrol et.' }
if (-not $NoBrowser) { Start-Process 'http://localhost:5684/' }
Write-Output 'Ajans Kurucu hazır: http://localhost:5684/'

[CmdletBinding()]
param([string]$InstallRoot = (Join-Path $env:LOCALAPPDATA 'AjansKurucu'))

$ErrorActionPreference = 'Stop'
$sourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$installRoot = [IO.Path]::GetFullPath($InstallRoot)
$localBase = [IO.Path]::GetFullPath($env:LOCALAPPDATA)
if (-not $installRoot.StartsWith($localBase, [StringComparison]::OrdinalIgnoreCase)) { throw 'Kurulum konumu kullanıcı klasörü içinde olmalı.' }

$required = @('ui\ajans-yonetim\server.mjs','projects\agents','data\memory','workflows','docker-compose.creator.yml','Start-AjansKurucu.ps1')
foreach ($item in $required) { if (-not (Test-Path -LiteralPath (Join-Path $sourceRoot $item))) { throw "Kurulum paketi eksik: $item" } }

if (Test-Path -LiteralPath $installRoot) {
  $backupRoot = Join-Path $installRoot ('backups\installer-' + (Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'))
  New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
  foreach ($item in @('ui','projects','workflows','docker-compose.creator.yml','Start-AjansKurucu.ps1')) {
    $current = Join-Path $installRoot $item
    if (Test-Path -LiteralPath $current) { Copy-Item -LiteralPath $current -Destination $backupRoot -Recurse -Force }
  }
}

New-Item -ItemType Directory -Force -Path $installRoot,(Join-Path $installRoot 'data\admin'),(Join-Path $installRoot 'secrets\creator') | Out-Null
foreach ($folder in @('ui','projects','workflows')) {
  $destination = Join-Path $installRoot $folder
  New-Item -ItemType Directory -Force -Path $destination | Out-Null
  Copy-Item -Path (Join-Path $sourceRoot "$folder\*") -Destination $destination -Recurse -Force
}
New-Item -ItemType Directory -Force -Path (Join-Path $installRoot 'data\memory') | Out-Null
Copy-Item -Path (Join-Path $sourceRoot 'data\memory\*') -Destination (Join-Path $installRoot 'data\memory') -Force
foreach ($file in @('docker-compose.creator.yml','Start-AjansKurucu.ps1','KULLANIM_KILAVUZU.md')) {
  $source = Join-Path $sourceRoot $file
  if (Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination $installRoot -Force }
}

$secretRoot = Join-Path $installRoot 'secrets\creator'
$passwordPath = Join-Path $secretRoot 'password-hash.dpapi'
$encryptionPath = Join-Path $secretRoot 'encryption-key.dpapi'
if (-not (Test-Path -LiteralPath $passwordPath)) {
  do {
    $first = Read-Host 'Ajans Kurucu giriş parolanı belirle' -AsSecureString
    $second = Read-Host 'Parolayı tekrar yaz' -AsSecureString
    $plainFirst = [Net.NetworkCredential]::new('', $first).Password
    $plainSecond = [Net.NetworkCredential]::new('', $second).Password
    $valid = $plainFirst.Length -ge 10 -and $plainFirst -ceq $plainSecond
    if (-not $valid) { Write-Host 'Parolalar eşleşmeli ve en az 10 karakter olmalı.' -ForegroundColor Yellow }
  } until ($valid)
  $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
  $salt = New-Object byte[] 16
  try { $rng.GetBytes($salt) } finally { $rng.Dispose() }
  $derive = [Security.Cryptography.Rfc2898DeriveBytes]::new($plainFirst, $salt, 210000, [Security.Cryptography.HashAlgorithmName]::SHA256)
  try { $hash = $derive.GetBytes(32) } finally { $derive.Dispose() }
  $passwordHash = 'pbkdf2_sha256$210000$' + [Convert]::ToBase64String($salt) + '$' + [Convert]::ToBase64String($hash)
  $protectedPassword = ConvertTo-SecureString -String $passwordHash -AsPlainText -Force | ConvertFrom-SecureString
  [IO.File]::WriteAllText($passwordPath, $protectedPassword, [Text.Encoding]::UTF8)
  $plainFirst = $null; $plainSecond = $null; $passwordHash = $null
}
if (-not (Test-Path -LiteralPath $encryptionPath)) {
  $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
  $keyBytes = New-Object byte[] 48
  try { $rng.GetBytes($keyBytes) } finally { $rng.Dispose() }
  $key = [Convert]::ToBase64String($keyBytes)
  $protectedKey = ConvertTo-SecureString -String $key -AsPlainText -Force | ConvertFrom-SecureString
  [IO.File]::WriteAllText($encryptionPath, $protectedKey, [Text.Encoding]::UTF8)
  $key = $null
}

$shortcutPath = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Ajans Kurucu.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = 'powershell.exe'
$shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + (Join-Path $installRoot 'Start-AjansKurucu.ps1') + '"'
$shortcut.WorkingDirectory = $installRoot
$shortcut.Description = 'Çevrimdışı yaşayan ajans uygulaması kurucusu'
$shortcut.Save()

Write-Host 'Ajans Kurucu kuruldu. Masaüstü simgesi oluşturuldu.' -ForegroundColor Green
& (Join-Path $installRoot 'Start-AjansKurucu.ps1')

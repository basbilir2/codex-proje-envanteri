[CmdletBinding()]
param([string]$OutputDirectory = '')

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) { $OutputDirectory = Join-Path $root 'dist' }
$stamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$stage = Join-Path $env:TEMP "AjansKurucu-$stamp"
$packageRoot = Join-Path $stage 'Ajans-Kurucu'
New-Item -ItemType Directory -Force -Path $packageRoot,(Join-Path $packageRoot 'data\memory') | Out-Null

foreach ($folder in @('ui','projects','workflows')) { Copy-Item -LiteralPath (Join-Path $root $folder) -Destination $packageRoot -Recurse -Force }
$memoryFiles = @('model-yonlendirme.json','yetki-matrisi.json','tartisma-politikasi.json','durum-makinesi.json','hafiza-politikasi.json','guvenlik-politikasi.json','kalite-politikasi.json','gizlilik-ve-veri-saklama.json','degisiklik-yonetimi.json','musteri-baslangic-motoru.json','zaman-yonetimi.json','test-kabul-kriterleri.json','baglam-derleme-politikasi.json')
foreach ($file in $memoryFiles) {
  $source = Join-Path $root "data\memory\$file"
  if (Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination (Join-Path $packageRoot 'data\memory') -Force }
}
foreach ($file in @('docker-compose.creator.yml','Start-AjansKurucu.ps1','Install-AjansKurucu.ps1','AJANS-KURUCU-KUR.cmd')) { Copy-Item -LiteralPath (Join-Path $root $file) -Destination $packageRoot -Force }
Copy-Item -LiteralPath (Join-Path $root 'ui\ajans-yonetim\KULLANIM_KILAVUZU.md') -Destination (Join-Path $packageRoot 'KULLANIM_KILAVUZU.md') -Force

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$zip = Join-Path $OutputDirectory "Ajans-Kurucu-$stamp.zip"
Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -CompressionLevel Optimal
$hash = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash
Write-Output "Kurulum paketi: $zip"
Write-Output "SHA-256: $hash"

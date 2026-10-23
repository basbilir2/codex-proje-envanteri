[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
function Convert-BytesToHex([byte[]]$Bytes) { return ([BitConverter]::ToString($Bytes) -replace '-', '') }
function Get-Sha256Hex([string]$Text) { $sha = [Security.Cryptography.SHA256]::Create(); try { return Convert-BytesToHex ($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Text))) } finally { $sha.Dispose() } }
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$inventoryPath = Join-Path $root 'data\security\supply-chain-inventory.json'
$secretPath = Join-Path $root 'secrets\approval-hmac-key.dpapi'
if (-not (Test-Path -LiteralPath $inventoryPath) -or -not (Test-Path -LiteralPath $secretPath)) { throw 'Envanter veya yerel imza anahtarı bulunamadı.' }
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $inventoryPath | ConvertFrom-Json
$paths = @($inventory.critical_file_hashes.PSObject.Properties.Name)
$agentPromptPaths = Get-ChildItem -LiteralPath (Join-Path $root 'projects\agents') -File -Filter '*.txt' | ForEach-Object { $_.FullName.Substring($root.Length + 1) }
$requiredPaths = @(
  'Enable-AiAjansModelWorker.ps1','Update-SupplyChainInventory.ps1','Protect-BrandAccountRegistry.ps1','Set-BrandAccountVerification.ps1',
  'tests/orchestration-pipeline.test.mjs','tests/scoped-service-auth.test.mjs','tests/account-binding.test.mjs','tests/local-delivery.test.mjs',
  'data/memory/rol-kartlari.json','data/memory/marka-ozeti.json','data/memory/model-yonlendirme.json','data/memory/yetki-matrisi.json',
  'data/memory/tartisma-politikasi.json','data/memory/durum-makinesi.json','data/memory/hafiza-politikasi.json','data/memory/guvenlik-politikasi.json',
  'data/memory/kalite-politikasi.json','data/memory/gozlemlenebilirlik-politikasi.json','data/memory/gizlilik-ve-veri-saklama.json',
  'data/memory/yayin-adaptoru-sozlesmesi.json','data/memory/hesap-kayitlari.json','data/memory/sistem-hafizasi.json',
  'ui/ajans-merkezi/public/index.html','ui/ajans-merkezi/public/app.js','ui/ajans-merkezi/public/styles.css',
  'ui/ajans-yonetim/server.mjs','ui/ajans-yonetim/public/index.html','ui/ajans-yonetim/public/app.js',
  'ui/ajans-yonetim/public/styles.css','ui/ajans-yonetim/public/client.html','ui/ajans-yonetim/public/client.js',
  'ui/ajans-yonetim/KULLANIM_KILAVUZU.md'
) + @($agentPromptPaths)
foreach ($required in $requiredPaths) { if ($paths -notcontains $required) { $paths += $required } }
$hashes = [ordered]@{}
foreach ($relative in ($paths | Sort-Object -Unique)) {
  $full = Join-Path $root $relative
  if (-not (Test-Path -LiteralPath $full)) { throw "Kritik dosya bulunamadı: $relative" }
  $hashes[$relative] = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash
}
$payloadJson = $hashes | ConvertTo-Json -Compress
$payloadSha = Get-Sha256Hex $payloadJson
$cipher = [IO.File]::ReadAllText($secretPath, [Text.Encoding]::UTF8).Trim(); $secure = ConvertTo-SecureString -String $cipher; $key = [Net.NetworkCredential]::new('', $secure).Password
$hmac = [Security.Cryptography.HMACSHA256]::new([Text.Encoding]::UTF8.GetBytes($key))
try { $signature = Convert-BytesToHex ($hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($payloadJson))) }
finally { $hmac.Dispose(); $key = $null }
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$inventory.status = 'signed_local_baseline'
$inventory.critical_file_hashes = [pscustomobject]$hashes
$inventory | Add-Member -Force NoteProperty signature ([pscustomobject]@{ algorithm = 'HMAC-SHA256-DPAPI-local-user'; payload_sha256 = $payloadSha; value = $signature })
$temp = "$inventoryPath.$PID.tmp"; $inventory | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $temp -Encoding UTF8; Move-Item -LiteralPath $temp -Destination $inventoryPath -Force
Write-Output "İmzalı tedarik zinciri envanteri güncellendi: $($hashes.Count) kritik dosya."

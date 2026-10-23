[CmdletBinding()]
param([switch]$Build)

$ErrorActionPreference = 'Stop'
function Convert-BytesToHex([byte[]]$Bytes) { return ([BitConverter]::ToString($Bytes) -replace '-', '') }
function Get-Sha256Hex([string]$Text) { $sha = [Security.Cryptography.SHA256]::Create(); try { return Convert-BytesToHex ($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Text))) } finally { $sha.Dispose() } }
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$docker = 'C:\Users\USER\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe'
if (-not (Test-Path -LiteralPath $docker)) { throw 'Docker komutu bulunamadı.' }

$inventoryPath = Join-Path $root 'data\security\supply-chain-inventory.json'
if (-not (Test-Path -LiteralPath $inventoryPath)) { throw 'Tedarik zinciri envanteri bulunamadı; servisler başlatılmadı.' }
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $inventoryPath | ConvertFrom-Json
$drift = @()
foreach ($entry in $inventory.critical_file_hashes.PSObject.Properties) {
  $file = Join-Path $root $entry.Name
  if (-not (Test-Path -LiteralPath $file) -or (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $entry.Value) {
    $drift += $entry.Name
  }
}
if ($drift.Count -gt 0) { throw "Kritik dosya özeti uyuşmuyor; servisler güvenli biçimde durdu: $($drift -join ', ')" }

function Unprotect-LocalSecret {
  param([Parameter(Mandatory)][string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) { throw "Korunan sır bulunamadı: $Path" }
  $cipher = [IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8).Trim()
  $secure = ConvertTo-SecureString -String $cipher
  return [Net.NetworkCredential]::new('', $secure).Password
}

function Get-DerivedServiceKey {
  param([Parameter(Mandatory)][string]$RootKey, [Parameter(Mandatory)][string]$Service)
  $hmac = [Security.Cryptography.HMACSHA256]::new([Text.Encoding]::UTF8.GetBytes($RootKey))
  try { return [Convert]::ToBase64String($hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes("ai-ajans-service:${Service}:v1"))) }
  finally { $hmac.Dispose() }
}

$secretDir = Join-Path $root 'secrets'
if (-not (Test-Path -LiteralPath (Join-Path $secretDir 'runtime-api-key.dpapi'))) {
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'projects\runtime\bootstrap-local-secrets.ps1') -ProjectRoot $root | Out-Null
}
& (Join-Path $root 'projects\runtime\protect-secrets-acl.ps1') -ProjectRoot $root | Out-Null

$env:N8N_ENCRYPTION_KEY = Unprotect-LocalSecret (Join-Path $secretDir 'n8n-encryption-key.dpapi')
$env:AJANS_RUNTIME_API_KEY = Unprotect-LocalSecret (Join-Path $secretDir 'runtime-api-key.dpapi')
$env:AJANS_CENTER_API_KEY = Get-DerivedServiceKey -RootKey $env:AJANS_RUNTIME_API_KEY -Service 'center'
$env:AJANS_SCHEDULER_API_KEY = Get-DerivedServiceKey -RootKey $env:AJANS_RUNTIME_API_KEY -Service 'scheduler'
$env:AJANS_WORKER_API_KEY = Get-DerivedServiceKey -RootKey $env:AJANS_RUNTIME_API_KEY -Service 'worker'
$env:AJANS_N8N_SERVICE_API_KEY = Get-DerivedServiceKey -RootKey $env:AJANS_RUNTIME_API_KEY -Service 'n8n'
$env:AJANS_ADMIN_ENCRYPTION_KEY = Get-DerivedServiceKey -RootKey $env:AJANS_RUNTIME_API_KEY -Service 'admin-credential-vault'
$env:AJANS_APPROVAL_HMAC_KEY = Unprotect-LocalSecret (Join-Path $secretDir 'approval-hmac-key.dpapi')
$signedHashes = [ordered]@{}
foreach ($entry in ($inventory.critical_file_hashes.PSObject.Properties | Sort-Object Name)) { $signedHashes[$entry.Name] = [string]$entry.Value }
$inventoryPayload = $signedHashes | ConvertTo-Json -Compress
$inventoryPayloadSha = Get-Sha256Hex $inventoryPayload
$inventoryHmac = [Security.Cryptography.HMACSHA256]::new([Text.Encoding]::UTF8.GetBytes($env:AJANS_APPROVAL_HMAC_KEY))
try { $inventorySignature = Convert-BytesToHex ($inventoryHmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($inventoryPayload))) }
finally { $inventoryHmac.Dispose() }
if ($inventory.signature.algorithm -ne 'HMAC-SHA256-DPAPI-local-user' -or $inventory.signature.payload_sha256 -ne $inventoryPayloadSha -or $inventory.signature.value -ne $inventorySignature) { throw 'Tedarik zinciri envanter imzası geçersiz; servisler başlatılmadı.' }
$env:AJANS_ADAPTER_API_KEY = Unprotect-LocalSecret (Join-Path $secretDir 'adapter-api-key.dpapi')
$operatorPath = Join-Path $secretDir 'operator-password-hash.dpapi'
$env:AJANS_OPERATOR_PASSWORD_HASH = if (Test-Path -LiteralPath $operatorPath) { Unprotect-LocalSecret $operatorPath } else { '' }
$env:AJANS_MODEL_WORKER_ENABLED = 'false'
$env:AJANS_AUTONOMOUS_TASKS_ENABLED = 'false'
$env:AJANS_MODEL_ACCEPTANCE_PROOF = 'unverified'
$env:AJANS_MODEL_PROVIDER = 'google'
$env:AJANS_MODEL_NAME = 'models/gemini-3.1-flash-lite'
$env:AJANS_MODEL_BILLING_MODE = ''
$env:AJANS_MODEL_INPUT_USD_PER_MILLION = ''
$env:AJANS_MODEL_OUTPUT_USD_PER_MILLION = ''
$env:AJANS_MODEL_PRICING_VERIFIED = 'false'
$env:AJANS_MODEL_ADAPTER_URL = ''

$activationPath = Join-Path $root 'data\security\model-worker-activation.json'
$modelActivationValid = $false
if (Test-Path -LiteralPath $activationPath) {
  $wrapper = Get-Content -Raw -Encoding UTF8 -LiteralPath $activationPath | ConvertFrom-Json
  if (-not $wrapper.payload_json -or -not $wrapper.signature_hmac_sha256) { throw 'Model worker etkinleştirme kaydı bozuk.' }
  $hmac = [Security.Cryptography.HMACSHA256]::new([Text.Encoding]::UTF8.GetBytes($env:AJANS_APPROVAL_HMAC_KEY))
  try { $expectedSignature = Convert-BytesToHex ($hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes([string]$wrapper.payload_json))) }
  finally { $hmac.Dispose() }
  if ($expectedSignature -ne [string]$wrapper.signature_hmac_sha256) { throw 'Model worker etkinleştirme imzası geçersiz.' }
  $activation = [string]$wrapper.payload_json | ConvertFrom-Json
  $reportPath = Join-Path $root 'tests\results\model-quality-acceptance-report.json'
  $workflowPath = Join-Path $root 'workflows\18-runtime-model-adapter-template.json'
  $report = Get-Content -Raw -Encoding UTF8 -LiteralPath $reportPath | ConvertFrom-Json
  $hashesMatch = (Get-FileHash -LiteralPath $reportPath -Algorithm SHA256).Hash -eq $activation.quality_report_sha256 -and (Get-FileHash -LiteralPath $workflowPath -Algorithm SHA256).Hash -eq $activation.workflow_template_sha256
  $acceptancePass = $report.status -eq 'PASS' -and $report.actual_quality_acceptance_passed -eq $true -and $report.Operator_shadow_acceptance -eq $true
  $pricing = $activation.pricing
  $pricingValid = $pricing -and $pricing.verified_from_official_source -eq $true -and $pricing.billing_mode -in @('free_tier','paid') -and [double]$pricing.input_usd_per_million -ge 0 -and [double]$pricing.output_usd_per_million -ge 0 -and ($pricing.billing_mode -ne 'free_tier' -or ([double]$pricing.input_usd_per_million -eq 0 -and [double]$pricing.output_usd_per_million -eq 0))
  if ($activation.enabled -ne $true -or -not $hashesMatch -or -not $acceptancePass -or -not $pricingValid) { throw 'Model kalite kabul ve fiyat kaydı güncel kaynaklarla eşleşmiyor; model worker kapalı tutuldu.' }
  $env:AJANS_MODEL_WORKER_ENABLED = 'true'
  $env:AJANS_AUTONOMOUS_TASKS_ENABLED = 'true'
  $env:AJANS_MODEL_ACCEPTANCE_PROOF = 'verified'
  $env:AJANS_MODEL_PROVIDER = [string]$activation.provider
  $env:AJANS_MODEL_NAME = [string]$activation.model
  $env:AJANS_MODEL_BILLING_MODE = [string]$pricing.billing_mode
  $env:AJANS_MODEL_INPUT_USD_PER_MILLION = [string]$pricing.input_usd_per_million
  $env:AJANS_MODEL_OUTPUT_USD_PER_MILLION = [string]$pricing.output_usd_per_million
  $env:AJANS_MODEL_PRICING_VERIFIED = 'true'
  $env:AJANS_MODEL_ADAPTER_URL = [string]$activation.adapter_url
  $modelActivationValid = $true
}

$arguments = @('compose', '--project-directory', $root, '-f', (Join-Path $root 'docker-compose.yml'), 'up', '-d')
if ($Build) { $arguments += '--build' }
& $docker @arguments
if ($LASTEXITCODE -ne 0) { throw "Docker Compose başlatılamadı: $LASTEXITCODE" }

Remove-Item Env:N8N_ENCRYPTION_KEY,Env:AJANS_RUNTIME_API_KEY,Env:AJANS_CENTER_API_KEY,Env:AJANS_SCHEDULER_API_KEY,Env:AJANS_WORKER_API_KEY,Env:AJANS_N8N_SERVICE_API_KEY,Env:AJANS_ADMIN_ENCRYPTION_KEY,Env:AJANS_APPROVAL_HMAC_KEY,Env:AJANS_ADAPTER_API_KEY,Env:AJANS_OPERATOR_PASSWORD_HASH,Env:AJANS_MODEL_WORKER_ENABLED,Env:AJANS_AUTONOMOUS_TASKS_ENABLED,Env:AJANS_MODEL_ACCEPTANCE_PROOF,Env:AJANS_MODEL_PROVIDER,Env:AJANS_MODEL_NAME,Env:AJANS_MODEL_BILLING_MODE,Env:AJANS_MODEL_INPUT_USD_PER_MILLION,Env:AJANS_MODEL_OUTPUT_USD_PER_MILLION,Env:AJANS_MODEL_PRICING_VERIFIED,Env:AJANS_MODEL_ADAPTER_URL -ErrorAction SilentlyContinue
$deadline = (Get-Date).AddSeconds(45)
do {
  try { $centerReady = (Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5680/api/health' -TimeoutSec 3).StatusCode -eq 200 } catch { $centerReady = $false }
  try { $adminReady = (Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5684/api/health' -TimeoutSec 3).StatusCode -eq 200 } catch { $adminReady = $false }
  try { $n8nReady = (Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5678/healthz' -TimeoutSec 3).StatusCode -eq 200 } catch { $n8nReady = $false }
  if ($centerReady -and $adminReady -and $n8nReady) { break }
  Start-Sleep -Milliseconds 500
} while ((Get-Date) -lt $deadline)
if (-not ($centerReady -and $adminReady -and $n8nReady)) { throw 'Yerel servisler zamaninda canli duruma gelemedi.' }
$requiredContainers = @('ai-ajans-n8n','ai-ajans-merkezi','ai-ajans-yonetim','ai-ajans-runtime','ai-ajans-scheduler','ai-ajans-worker','ai-ajans-guardian')
foreach ($container in $requiredContainers) {
  $running = (& $docker inspect -f '{{.State.Running}}' $container 2>$null).Trim()
  if ($running -ne 'true') { throw "Gerekli servis çalışmıyor: $container" }
}
if ($modelActivationValid) {
  $workerStatus = Join-Path $root 'data\health\worker.json'; $schedulerStatus = Join-Path $root 'data\health\scheduler.json'
  $serviceDeadline = (Get-Date).AddSeconds(30)
  do {
    try { $workerReady = (Get-Content -Raw -Encoding UTF8 $workerStatus | ConvertFrom-Json).readiness -eq 'ready' } catch { $workerReady = $false }
    try { $schedulerReady = (Get-Content -Raw -Encoding UTF8 $schedulerStatus | ConvertFrom-Json).readiness -eq 'ready' } catch { $schedulerReady = $false }
    if ($workerReady -and $schedulerReady) { break }
    Start-Sleep -Milliseconds 500
  } while ((Get-Date) -lt $serviceDeadline)
  if (-not ($workerReady -and $schedulerReady)) { throw 'Model kabulü etkin olmasına rağmen worker veya scheduler hazır duruma gelemedi.' }
}
if (Test-Path -LiteralPath $operatorPath) {
  Write-Output 'AI Ajans servisleri canli. Operator onayi yapilandirildi; hazirlik durumu Ajans Merkezi ve guardian kaydindan dogrulanmalidir.'
} else {
  Write-Output 'AI Ajans servisleri canli; durum SETUP_REQUIRED. Son hazirlik icin Operator onay parolasi ve model/hesap credentiallari gerekir.'
}

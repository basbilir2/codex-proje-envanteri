[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = 'C:\ai-ajans'
$resultFile = Join-Path $projectRoot 'data\logs\ucretsiz-yerel-test-sonucu.json'
$performanceFile = Join-Path $projectRoot 'data\logs\model-performans-kaydi.json'
$activeContextFile = Join-Path $projectRoot 'data\memory\aktif-baglam.json'
$imageLogFile = Join-Path $projectRoot 'data\logs\cloudflare-gorsel-test-sonucu.json'
$docker = 'C:\Users\USER\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe'

function Write-JsonAtomic {
  param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)]$Value)
  $directory = Split-Path -Parent $Path
  if (-not (Test-Path -LiteralPath $directory)) { New-Item -ItemType Directory -Path $directory -Force | Out-Null }
  $temporary = $Path + '.tmp.' + [Guid]::NewGuid().ToString('N')
  $json = $Value | ConvertTo-Json -Depth 50
  [IO.File]::WriteAllText($temporary, $json, [Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporary -Destination $Path -Force
}

function Unprotect-LocalSecret {
  param([Parameter(Mandatory)][string]$Path)
  $cipher = [IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8).Trim()
  $secure = ConvertTo-SecureString -String $cipher
  return [Net.NetworkCredential]::new('', $secure).Password
}

function Get-DerivedServiceKey {
  param([Parameter(Mandatory)][string]$RootKey, [Parameter(Mandatory)][string]$Service)
  $hmac = [Security.Cryptography.HMACSHA256]::new([Text.Encoding]::UTF8.GetBytes($RootKey))
  try { return [Convert]::ToBase64String($hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes('ai-ajans-service:' + $Service + ':v1'))) }
  finally { $hmac.Dispose() }
}

if (-not (Test-Path -LiteralPath $resultFile)) { throw 'Guvenli metin test sonucu bulunamadi.' }
$result = Get-Content -Raw -Encoding UTF8 -LiteralPath $resultFile | ConvertFrom-Json
if ($result.test_label -ne 'TEST - YAYIN YAPMAZ' -or $result.publish_authorized -ne $false -or $result.external_publish_executed -ne $false) { throw 'Yayin kilidi dogrulanamadi.' }
if ($result.status -ne 'Operator_onayi_bekliyor') { throw 'Sonuc Operator onay asamasinda degil.' }

$imageFile = Get-ChildItem -LiteralPath (Join-Path $projectRoot 'data\outputs\images') -File |
  Where-Object { $_.Name -like ($result.task_id + '-cloudflare-flux.*') } |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1
if (-not $imageFile) { throw 'Bu goreve ait Cloudflare gorseli bulunamadi.' }
$imageBytes = [IO.File]::ReadAllBytes($imageFile.FullName)
if ($imageBytes.Length -lt 10000) { throw 'Cloudflare gorsel dosyasi beklenenden kucuk.' }
$isJpeg = $imageBytes[0] -eq 0xFF -and $imageBytes[1] -eq 0xD8 -and $imageBytes[2] -eq 0xFF
$isPng = $imageBytes[0] -eq 0x89 -and $imageBytes[1] -eq 0x50 -and $imageBytes[2] -eq 0x4E -and $imageBytes[3] -eq 0x47
if (-not ($isJpeg -or $isPng)) { throw 'Cloudflare gorsel dosyasi JPEG veya PNG degil.' }

$stamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$backupRoot = Join-Path $projectRoot ('backups\' + $stamp + '\cloudflare-image-approval')
foreach ($path in @($resultFile,$performanceFile,$activeContextFile,$imageLogFile)) {
  if (Test-Path -LiteralPath $path) {
    $relative = $path.Substring($projectRoot.Length).TrimStart('\')
    $destination = Join-Path $backupRoot $relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath $path -Destination $destination -Force
  }
}

$result.content_version = 'v4-cloudflare-image-test-publish-plan'
$result.idempotency_key = $result.task_id + '-' + $result.content_version
$finalCaption = if ($result.agent_trace.ordinaryus.final_caption) { [string]$result.agent_trace.ordinaryus.final_caption } else { [string]$result.content_payload.caption }
$selectedIdea = @($result.agent_trace.content.ideas) | Where-Object id -eq $result.agent_trace.content.recommended_candidate | Select-Object -First 1
$nextSlot = (Get-Date).Date.AddDays(1).AddHours(20).AddMinutes(30)
$result.content_payload | Add-Member -NotePropertyName caption -NotePropertyValue $finalCaption -Force
$result.content_payload | Add-Member -NotePropertyName platform -NotePropertyValue 'Instagram' -Force
$result.content_payload | Add-Member -NotePropertyName language -NotePropertyValue 'tr-TR' -Force
$result.content_payload | Add-Member -NotePropertyName cta -NotePropertyValue ([string]$selectedIdea.cta) -Force
$result.content_payload | Add-Member -NotePropertyName hashtags -NotePropertyValue @('#TrendyBrander','#DTFBaskı','#KendiTasarımın','#TişörtTasarımı','#EvdeÜretim') -Force
$result.content_payload | Add-Member -NotePropertyName agent_summary -NotePropertyValue ([string]$result.agent_trace.ordinaryus.Operator_summary) -Force
$result.content_payload | Add-Member -NotePropertyName risks -NotePropertyValue @($result.agent_trace.ordinaryus.remaining_risks) -Force
$result.content_payload | Add-Member -NotePropertyName publish_plan -NotePropertyValue ([pscustomobject]@{
  status='suggested_not_scheduled'
  suggested_at=$nextSlot.ToString('o')
  timezone='Europe/Istanbul'
  rationale='Yerel test için önerilen akşam penceresi. Gerçek hesap performans verisi henüz bağlı değildir.'
}) -Force
$result.content_payload | Add-Member -NotePropertyName approval_scope -NotePropertyValue ([pscustomobject]@{
  delivery_mode='local_file_only'
  publish_authorized=$false
  external_publish_executed=$false
}) -Force
$result.content_payload.visual_source = 'cloudflare_workers_ai_generated_test'
$result.preview_source = 'Cloudflare Workers AI - FLUX.1 Schnell test'
$result.preview_ref = '/media/generated/' + $imageFile.Name
$result.model_test.model_calls = 7
$result.model_test.billing_mode = 'cloudflare_free_allocation_test'
$result.model_test.cost_note = 'Cloudflare ucretsiz tahsisli test. Kesin fatura veya sifir maliyet iddiasi kaydedilmez.'
$result.model_test | Add-Member -NotePropertyName image_model -NotePropertyValue '@cf/black-forest-labs/flux-1-schnell' -Force
$result.model_test | Add-Member -NotePropertyName image_provider -NotePropertyValue 'cloudflare' -Force
$result.token_guards.image_generation = $true
$result.token_guards.local_reference_only = $false
$result.completed_at = (Get-Date).ToUniversalTime().ToString('o')
Write-JsonAtomic -Path $resultFile -Value $result

Write-JsonAtomic -Path $imageLogFile -Value ([ordered]@{
  schema_version='1.0'
  task_id=$result.task_id
  status='generated_waiting_Operator_approval'
  provider='cloudflare'
  model='@cf/black-forest-labs/flux-1-schnell'
  image_file=('data/outputs/images/' + $imageFile.Name)
  byte_length=$imageBytes.Length
  publish_authorized=$false
  external_publish_executed=$false
  generated_at=(Get-Date).ToUniversalTime().ToString('o')
})

$performance = if (Test-Path -LiteralPath $performanceFile) { Get-Content -Raw -Encoding UTF8 -LiteralPath $performanceFile | ConvertFrom-Json } else { [pscustomobject]@{ schema_version='1.0'; records=@() } }
$records = @($performance.records)
$callId = $result.task_id + '-7-cloudflare-image'
if (-not ($records | Where-Object call_id -eq $callId)) {
  $records += [ordered]@{
    call_id=$callId
    timestamp=(Get-Date).ToUniversalTime().ToString('o')
    task_type='TEST GERCEK - image_generation'
    provider='cloudflare'
    model='@cf/black-forest-labs/flux-1-schnell'
    input_tokens=$null
    output_tokens=0
    image_outputs=1
    actual_usage_available=$false
    estimated_cost_usd=$null
    billing_mode='free_allocation_test'
    publish_executed=$false
  }
}
Write-JsonAtomic -Path $performanceFile -Value ([ordered]@{ schema_version='1.0'; records=@($records | Select-Object -Last 500) })

$activeContext = Get-Content -Raw -Encoding UTF8 -LiteralPath $activeContextFile | ConvertFrom-Json
$activeContext.updated_at = (Get-Date).ToUniversalTime().ToString('o')
$activeContext.state = 'Operator_onayi_bekliyor'
$activeContext.current_task = [pscustomobject]@{
  task_id=$result.task_id
  task_type='free_local_e2e_test'
  goal='Gemini metin ajanlari ve Cloudflare ucretsiz gorsel testi sonucunu yerel onay ekraninda kontrol etmek.'
  agent_id='yayin_arayuz_ajani'
  source_ref='data/logs/ucretsiz-yerel-test-sonucu.json'
  source_fingerprint=$null
  request_fingerprint=$result.idempotency_key
}
$activeContext.selected_model = [pscustomobject]@{
  provider='google_text_plus_cloudflare_image'
  model='models/gemini-3.1-flash-lite + @cf/black-forest-labs/flux-1-schnell'
  billing_mode='free_test'
}
$activeContext.approval = [pscustomobject]@{
  publish_authorized=$false
  status='Operator_onayi_bekliyor'
  note='Bu test yalniz yerel dosyaya kaydedilebilir; sosyal medyada yayinlanamaz.'
}
Write-JsonAtomic -Path $activeContextFile -Value $activeContext

$rootKey = Unprotect-LocalSecret (Join-Path $projectRoot 'secrets\runtime-api-key.dpapi')
$n8nKey = Get-DerivedServiceKey -RootKey $rootKey -Service 'n8n'
$approvalPayload = [ordered]@{
  brand_id=$result.brand_id
  content_id=$result.content_id
  content_version=$result.content_version
  content_payload=$result.content_payload
  idempotency_key=$result.idempotency_key
  summary=('TEST - YAYIN YAPMAZ | ' + $result.summary)
  preview_refs=@($result.preview_ref)
}
$requestJson = [ordered]@{ key=$n8nKey; payload=$approvalPayload } | ConvertTo-Json -Depth 20 -Compress
$requestBase64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($requestJson))
$nodeScript = "const x=JSON.parse(Buffer.from(process.argv[1],'base64').toString('utf8'));fetch('http://ajans-runtime:5681/v1/local-approvals',{method:'POST',headers:{Authorization:'Bearer '+x.key,'Content-Type':'application/json; charset=utf-8'},body:JSON.stringify(x.payload)}).then(async r=>{const t=await r.text();if(!r.ok){console.error(t);process.exit(1)}process.stdout.write(t)}).catch(e=>{console.error(e.message);process.exit(1)});"
$approvalRaw = & $docker exec ai-ajans-n8n node -e $nodeScript $requestBase64
if ($LASTEXITCODE -ne 0) { throw 'Yerel onay paketi runtime tarafindan kabul edilmedi.' }
$approval = ($approvalRaw | Out-String).Trim() | ConvertFrom-Json
if ($approval.publish_authorized -ne $false -or $approval.delivery_mode -ne 'local_file_only') { throw 'Yerel onay yayin kilidi dogrulanamadi.' }

[pscustomobject]@{
  status='PASS'
  task_id=$result.task_id
  image_file=$imageFile.FullName
  image_bytes=$imageBytes.Length
  approval_id=$approval.approval_id
  approval_reused=[bool]$approval.reused
  center_url='http://localhost:5680'
  backup=$backupRoot
  publish_executed=$false
} | ConvertTo-Json -Depth 5

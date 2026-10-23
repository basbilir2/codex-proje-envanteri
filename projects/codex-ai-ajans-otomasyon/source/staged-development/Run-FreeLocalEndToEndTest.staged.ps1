[CmdletBinding()]
param([switch]$UseExistingResult)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$docker = 'C:\Users\USER\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe'
$workflowId = 'FreeLocalE2E19A'
$workflowFile = Join-Path $projectRoot 'workflows\19-ucretsiz-yerel-uctan-uca-test.json'
$imageWorkflowId = 'GeminiImageTest20A'
$imageWorkflowFile = Join-Path $projectRoot 'workflows\20-gemini-gorsel-uretimi-test.json'
$resultFile = Join-Path $projectRoot 'data\logs\ucretsiz-yerel-test-sonucu.json'

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

function Estimate-Tokens {
  param($Value)
  $text = if ($Value -is [string]) { $Value } else { $Value | ConvertTo-Json -Depth 30 -Compress }
  return [Math]::Max(1, [Math]::Ceiling($text.Length / 4.0))
}

if (-not (Test-Path -LiteralPath $docker)) { throw 'Docker bulunamadi.' }
if (-not (Test-Path -LiteralPath $workflowFile)) { throw 'Ucretsiz test workflow dosyasi bulunamadi.' }
if (-not (Test-Path -LiteralPath $imageWorkflowFile)) { throw 'Gemini gorsel test workflow dosyasi bulunamadi.' }

$stamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$backupRoot = Join-Path $projectRoot ('backups\' + $stamp + '\free-local-e2e-test')
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
$mutableFiles = @(
  'data\logs\ucretsiz-yerel-test-sonucu.json',
  'data\logs\analizci-son-cikti.txt',
  'data\logs\icerik-stratejisti-son-cikti.json',
  'data\logs\ajan-konusmalari.json',
  'data\logs\ajans-oturum-log.json',
  'data\logs\model-performans-kaydi.json',
  'data\memory\aktif-baglam.json',
  'data\logs\gemini-gorsel-test-sonucu.json'
)
foreach ($relative in $mutableFiles) {
  $source = Join-Path $projectRoot $relative
  if (Test-Path -LiteralPath $source) {
    $destination = Join-Path $backupRoot $relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination -Force
  }
}

try {
  $health = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5678/healthz' -TimeoutSec 5
  if ($health.StatusCode -ne 200) { throw 'n8n sagliksiz.' }
} catch {
  & (Join-Path $projectRoot 'Start-AiAjans.ps1') | Out-Null
  Start-Sleep -Seconds 5
}

if (-not $UseExistingResult) {
  $importOutput = & $docker exec ai-ajans-n8n n8n import:workflow --input='/workflows/19-ucretsiz-yerel-uctan-uca-test.json' 2>&1
  if ($LASTEXITCODE -ne 0) { throw ('Workflow ice aktarilamadi: ' + (($importOutput | Out-String).Trim())) }
  if (Test-Path -LiteralPath $resultFile) { Move-Item -LiteralPath $resultFile -Destination (Join-Path $backupRoot 'previous-run-result.json') -Force }
  $executionOutput = & $docker exec -e N8N_RUNNERS_BROKER_PORT=5689 ai-ajans-n8n n8n execute --id=$workflowId --rawOutput 2>&1
  if ($LASTEXITCODE -ne 0) {
    $shortError = (($executionOutput | Out-String).Trim())
    if ($shortError.Length -gt 2000) { $shortError = $shortError.Substring(0, 2000) }
    throw ('Ucretsiz Gemini test akisi tamamlanamadi: ' + $shortError)
  }
}
if (-not (Test-Path -LiteralPath $resultFile)) { throw 'Workflow tamamlandi fakat yerel sonuc dosyasi olusmadi.' }

$result = Get-Content -Raw -Encoding UTF8 -LiteralPath $resultFile | ConvertFrom-Json
if ($result.test_label -ne 'TEST - YAYIN YAPMAZ' -or $result.publish_authorized -ne $false -or $result.external_publish_executed -ne $false) { throw 'Test yayin korumasi dogrulanamadi.' }
if ($result.status -ne 'Operator_onayi_bekliyor') { throw ('Beklenmeyen test durumu: ' + $result.status) }

$testImageName = $result.task_id + '-gemini.png'
$testImageFile = Join-Path $projectRoot ('data\outputs\images\' + $testImageName)
New-Item -ItemType Directory -Path (Split-Path -Parent $testImageFile) -Force | Out-Null
if (Test-Path -LiteralPath $testImageFile) {
  $oldImageBackup = Join-Path $backupRoot ('data\outputs\images\' + $testImageName)
  New-Item -ItemType Directory -Path (Split-Path -Parent $oldImageBackup) -Force | Out-Null
  Move-Item -LiteralPath $testImageFile -Destination $oldImageBackup -Force
}

$imageImportOutput = & $docker exec ai-ajans-n8n n8n import:workflow --input='/workflows/20-gemini-gorsel-uretimi-test.json' 2>&1
if ($LASTEXITCODE -ne 0) { throw ('Gemini gorsel workflow ice aktarilamadi: ' + (($imageImportOutput | Out-String).Trim())) }
$imageExecutionOutput = & $docker exec -e N8N_RUNNERS_BROKER_PORT=5689 ai-ajans-n8n n8n execute --id=$imageWorkflowId --rawOutput 2>&1
if ($LASTEXITCODE -ne 0) {
  $shortError = (($imageExecutionOutput | Out-String).Trim())
  if ($shortError.Length -gt 2200) { $shortError = $shortError.Substring(0, 2200) }
  throw ('Gemini gercek gorsel uretimi tamamlanamadi. Google hesabinda gorsel API faturalandirmasi gerekebilir. Ayrinti: ' + $shortError)
}
if (-not (Test-Path -LiteralPath $testImageFile)) { throw 'Gemini cagrisi tamamlandi fakat gorsel yerel dosyada bulunamadi.' }
$imageBytes = [IO.File]::ReadAllBytes($testImageFile)
if ($imageBytes.Length -lt 10000) { throw 'Gemini gorsel dosyasi beklenenden kucuk veya bos.' }
$isPng = $imageBytes.Length -ge 8 -and $imageBytes[0] -eq 0x89 -and $imageBytes[1] -eq 0x50 -and $imageBytes[2] -eq 0x4E -and $imageBytes[3] -eq 0x47
$isJpeg = $imageBytes.Length -ge 3 -and $imageBytes[0] -eq 0xFF -and $imageBytes[1] -eq 0xD8 -and $imageBytes[2] -eq 0xFF
if (-not ($isPng -or $isJpeg)) { throw 'Gemini gorsel ciktisi PNG veya JPEG degil.' }

$result.content_version = 'v2-gemini-image'
$result.idempotency_key = $result.task_id + '-' + $result.content_version
$result.content_payload.visual_source = 'gemini_api_generated'
$result.preview_source = 'Gemini API - gemini-3.1-flash-lite-image'
$result.preview_ref = '/media/generated/' + $testImageName
$result.model_test.model_calls = 7
$result.model_test.billing_mode = 'mixed_free_text_paid_image'
$result.model_test.cost_note = 'Metin testleri ucretsiz kotayi kullanabilir; Gemini gercek gorsel modeli ucretli olabilir. Kesin fatura uydurulmaz.'
$result.model_test | Add-Member -NotePropertyName image_model -NotePropertyValue 'models/gemini-3.1-flash-lite-image' -Force
$result.model_test | Add-Member -NotePropertyName estimated_image_unit_cost_usd -NotePropertyValue 0.0336 -Force
$result.token_guards.image_generation = $true
$result.token_guards.local_reference_only = $false
$result.completed_at = (Get-Date).ToUniversalTime().ToString('o')
Write-JsonAtomic -Path $resultFile -Value $result
Write-JsonAtomic -Path (Join-Path $projectRoot 'data\logs\gemini-gorsel-test-sonucu.json') -Value ([ordered]@{
  schema_version='1.0'; task_id=$result.task_id; status='generated_waiting_Operator_approval'; provider='google';
  model='models/gemini-3.1-flash-lite-image'; image_file=('data/outputs/images/' + $testImageName);
  byte_length=$imageBytes.Length; publish_authorized=$false; external_publish_executed=$false;
  generated_at=(Get-Date).ToUniversalTime().ToString('o')
})

$analysisText = @(
  'TEST - YAYIN YAPMAZ',
  '',
  'Veri durumu: ' + $result.agent_trace.analysis.data_status,
  'Ana bulgu: ' + $result.agent_trace.analysis.main_finding,
  'Hedef segment: ' + $result.agent_trace.analysis.target_segment,
  'Stratejik yon: ' + $result.agent_trace.analysis.strategic_direction,
  'Oncelikli aksiyonlar: ' + (($result.agent_trace.analysis.priority_actions) -join ' | '),
  'Eksik veriler: ' + (($result.agent_trace.analysis.missing_data) -join ' | '),
  'Risk: ' + $result.agent_trace.analysis.risk,
  'Guven: ' + $result.agent_trace.analysis.confidence
) -join [Environment]::NewLine
[IO.File]::WriteAllText((Join-Path $projectRoot 'data\logs\analizci-son-cikti.txt'), $analysisText, [Text.UTF8Encoding]::new($false))

$contentForDashboard = [ordered]@{
  schema_version = '1.0'
  status = 'TEST - Operator onayi bekliyor'
  data_disclaimer = $result.agent_trace.content.data_disclaimer
  segment = $result.agent_trace.content.segment
  recommended_candidate = $result.agent_trace.content.recommended_candidate
  selection_reason = $result.agent_trace.content.selection_reason
  ideas = @($result.agent_trace.content.ideas | ForEach-Object {
    [ordered]@{ id=$_.id; format=$_.format; hook=$_.hook; message=$_.message; cta=$_.cta; visual_brief=$_.visual_direction }
  })
  test_only = $true
  publish_authorized = $false
}
Write-JsonAtomic -Path (Join-Path $projectRoot 'data\logs\icerik-stratejisti-son-cikti.json') -Value $contentForDashboard

$messages = @(
  [ordered]@{ agent_name='Analizci'; type='stratejik analiz'; text=($result.agent_trace.analysis.main_finding + ' ' + $result.agent_trace.analysis.strategic_direction) },
  [ordered]@{ agent_name='Icerik Stratejisti'; type='icerik adaylari'; text=('3 aday uretti. Onerilen: ' + $result.agent_trace.content.recommended_candidate + '. ' + $result.agent_trace.content.selection_reason) },
  [ordered]@{ agent_name='Gorsel Stratejist'; type='gorsel brief ve uretim'; text=($result.agent_trace.visual.composition + ' ' + $result.agent_trace.visual.scene + ' Gemini ile gercek test gorseli olusturuldu ve yerel onaya eklendi.') },
  [ordered]@{ agent_name='Cesur Muhalif'; type='itiraz'; text=($result.agent_trace.debate.bold_view.problem + ' Cozum: ' + $result.agent_trace.debate.bold_view.solution) },
  [ordered]@{ agent_name='Temkinli Muhalif'; type='risk kontrolu'; text=($result.agent_trace.debate.cautious_view.problem + ' Cozum: ' + $result.agent_trace.debate.cautious_view.solution) },
  [ordered]@{ agent_name='Ana Ordinaryus'; type='karar'; text=($result.agent_trace.ordinaryus.decision + ': ' + $result.agent_trace.ordinaryus.reason) },
  [ordered]@{ agent_name='Yayin Arayuz Ajani'; type='onay paketi'; text=$result.agent_trace.interface.summary }
)
$conversationDoc = [ordered]@{
  schema_version='1.0'
  updated_at=(Get-Date).ToUniversalTime().ToString('o')
  conversations=@([ordered]@{ id=$result.task_id; title='Ucretsiz yerel uctan uca test'; status='Operator onayi bekliyor'; messages=$messages })
  debates=@([ordered]@{ id=($result.task_id + '-debate'); status='Tek tur tamamlandi'; current_round=1; max_rounds=3; note=(($result.agent_trace.debate.common_points) -join ' | '); participants=@('Cesur Muhalif','Temkinli Muhalif') })
}
Write-JsonAtomic -Path (Join-Path $projectRoot 'data\logs\ajan-konusmalari.json') -Value $conversationDoc

$sessionFile = Join-Path $projectRoot 'data\logs\ajans-oturum-log.json'
$sessions = if (Test-Path -LiteralPath $sessionFile) { Get-Content -Raw -Encoding UTF8 $sessionFile | ConvertFrom-Json } else { [pscustomobject]@{ schema_version='1.0'; records=@() } }
$sessionRecords = @($sessions.records)
$sessionRecords += [ordered]@{ session_id=$result.task_id; started_at=$result.created_at; completed_at=$result.completed_at; mode='free_local_e2e_test'; agents=@('analizci','sosyal_medya_icerik_stratejisti','gorsel_stratejist','cesur_muhalif','temkinli_muhalif','ana_ordinaryus','yayin_arayuz_ajani'); model='models/gemini-3.1-flash-lite'; result='Operator_onayi_bekliyor'; publish_executed=$false }
Write-JsonAtomic -Path $sessionFile -Value ([ordered]@{ schema_version='1.0'; records=@($sessionRecords | Select-Object -Last 100) })

$brandText = Get-Content -Raw -Encoding UTF8 (Join-Path $projectRoot 'projects\marka-kimligi.txt')
$productText = Get-Content -Raw -Encoding UTF8 (Join-Path $projectRoot 'projects\urunler.txt')
$audienceText = Get-Content -Raw -Encoding UTF8 (Join-Path $projectRoot 'projects\hedef-kitle.txt')
$guardText = Get-Content -Raw -Encoding UTF8 (Join-Path $projectRoot 'projects\yasakli-ifadeler.txt')
$patternsText = Get-Content -Raw -Encoding UTF8 (Join-Path $projectRoot 'projects\icerik-ornekleri.txt')
$roles = Get-Content -Raw -Encoding UTF8 (Join-Path $projectRoot 'data\memory\rol-kartlari.json') | ConvertFrom-Json
function Role-Text([string]$Id) { return (($roles.cards | Where-Object agent_id -eq $Id | Select-Object -First 1) | ConvertTo-Json -Depth 10 -Compress) }
$estimateSpecs = @(
  @{ task='TEST TAHMINI - analysis'; input=(Role-Text 'analizci')+$brandText+$productText+$audienceText; output=$result.agent_trace.analysis },
  @{ task='TEST TAHMINI - content_ideas'; input=(Role-Text 'sosyal_medya_icerik_stratejisti')+($result.agent_trace.analysis|ConvertTo-Json -Compress)+$brandText+$audienceText+$patternsText; output=$result.agent_trace.content },
  @{ task='TEST TAHMINI - visual_brief'; input=(Role-Text 'gorsel_stratejist')+($result.agent_trace.content|ConvertTo-Json -Compress)+$brandText; output=$result.agent_trace.visual },
  @{ task='TEST TAHMINI - debate_turn'; input=(Role-Text 'kontrol_muhalefet_kurulu')+($result.agent_trace.content|ConvertTo-Json -Compress)+($result.agent_trace.visual|ConvertTo-Json -Compress)+$guardText; output=$result.agent_trace.debate },
  @{ task='TEST TAHMINI - ordinaryus_decision'; input=(Role-Text 'ana_ordinaryus')+($result.agent_trace|ConvertTo-Json -Depth 20 -Compress); output=$result.agent_trace.ordinaryus },
  @{ task='TEST TAHMINI - interface_summary'; input=(Role-Text 'yayin_arayuz_ajani')+($result.agent_trace.ordinaryus|ConvertTo-Json -Compress); output=$result.agent_trace.interface }
)
$performanceFile = Join-Path $projectRoot 'data\logs\model-performans-kaydi.json'
$performance = if (Test-Path -LiteralPath $performanceFile) { Get-Content -Raw -Encoding UTF8 $performanceFile | ConvertFrom-Json } else { [pscustomobject]@{ schema_version='1.0'; records=@() } }
$performanceRecords = @($performance.records)
$callIndex = 0
foreach ($spec in $estimateSpecs) {
  $callIndex += 1
  $performanceRecords += [ordered]@{
    call_id=($result.task_id + '-' + $callIndex)
    timestamp=(Get-Date).ToUniversalTime().ToString('o')
    task_type=$spec.task
    provider='google'
    model='models/gemini-3.1-flash-lite'
    input_tokens=(Estimate-Tokens $spec.input)
    output_tokens=(Estimate-Tokens $spec.output)
    token_measurement='estimated_chars_div_4_not_provider_usage'
    actual_usage_available=$false
    estimated_cost_usd=$null
    billing_mode='free_tier_test'
    publish_executed=$false
  }
}
$performanceRecords += [ordered]@{
  call_id=($result.task_id + '-7-image')
  timestamp=(Get-Date).ToUniversalTime().ToString('o')
  task_type='TEST GERCEK - image_generation'
  provider='google'
  model='models/gemini-3.1-flash-lite-image'
  input_tokens=(Estimate-Tokens $result.agent_trace.visual.generation_prompt)
  output_tokens=0
  image_outputs=1
  token_measurement='input_estimated_chars_div_4_image_output_not_tokenized_here'
  actual_usage_available=$false
  estimated_cost_usd=0.0336
  cost_measurement='official_unit_price_estimate_not_invoice'
  billing_mode='paid_image_api_if_billing_enabled'
  publish_executed=$false
}
Write-JsonAtomic -Path $performanceFile -Value ([ordered]@{ schema_version='1.0'; records=@($performanceRecords | Select-Object -Last 500) })

$activeContextPath = Join-Path $projectRoot 'data\memory\aktif-baglam.json'
$activeContext = Get-Content -Raw -Encoding UTF8 $activeContextPath | ConvertFrom-Json
$activeContext.updated_at = (Get-Date).ToUniversalTime().ToString('o')
$activeContext.state = 'Operator_onayi_bekliyor'
$activeContext.current_task = [pscustomobject]@{ task_id=$result.task_id; task_type='free_local_e2e_test'; goal='Ucretsiz Gemini ajan zinciri sonucunu yerel onay ekraninda kontrol etmek.'; agent_id='yayin_arayuz_ajani'; source_ref='data/logs/ucretsiz-yerel-test-sonucu.json'; source_fingerprint=$null; request_fingerprint=$result.idempotency_key }
$activeContext.selected_model = [pscustomobject]@{ provider='google'; model='models/gemini-3.1-flash-lite + models/gemini-3.1-flash-lite-image'; billing_mode='mixed_test' }
$activeContext.approval = [pscustomobject]@{ publish_authorized=$false; status='Operator_onayi_bekliyor'; note='Bu test yalniz yerel dosyaya kaydedilebilir; sosyal medyada yayinlanamaz.' }
$activeContext.guards = [pscustomobject]@{ full_prompt_sent=$false; full_brand_source_sent=$false; raw_history_sent=$false; duplicate_brand_block=$false }
Write-JsonAtomic -Path $activeContextPath -Value $activeContext

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
$stdinPayload = [ordered]@{ key=$n8nKey; payload=$approvalPayload } | ConvertTo-Json -Depth 20 -Compress
$nodeScript = "let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',async()=>{const x=JSON.parse(s);const r=await fetch('http://ajans-runtime:5681/v1/local-approvals',{method:'POST',headers:{Authorization:'Bearer '+x.key,'Content-Type':'application/json'},body:JSON.stringify(x.payload)});const t=await r.text();if(!r.ok){console.error(t);process.exit(1)}process.stdout.write(t)});"
$approvalRaw = $stdinPayload | & $docker exec -i ai-ajans-n8n node -e $nodeScript
if ($LASTEXITCODE -ne 0) { throw 'Yerel onay paketi runtime tarafindan kabul edilmedi.' }
$approval = ($approvalRaw | Out-String).Trim() | ConvertFrom-Json
if ($approval.publish_authorized -ne $false -or $approval.delivery_mode -ne 'local_file_only') { throw 'Yerel onay yayin kilidi dogrulanamadi.' }

[pscustomobject]@{
  status='PASS'
  workflow=$workflowId
  image_workflow=$imageWorkflowId
  task_id=$result.task_id
  model_calls=7
  model='models/gemini-3.1-flash-lite + models/gemini-3.1-flash-lite-image'
  image_file=$testImageFile
  approval_id=$approval.approval_id
  approval_reused=[bool]$approval.reused
  center_url='http://localhost:5680'
  backup=$backupRoot
  publish_executed=$false
} | ConvertTo-Json -Depth 5

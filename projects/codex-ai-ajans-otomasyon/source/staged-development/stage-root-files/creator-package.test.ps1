[CmdletBinding()]
param(
  [string]$CreatorRoot = '',
  [string]$WorkspaceRoot = 'C:\ai-ajans',
  [int]$Port = 5696
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($CreatorRoot)) {
  $projectCandidate = Join-Path $PSScriptRoot '..\ui\ajans-yonetim'
  $CreatorRoot = if (Test-Path -LiteralPath $projectCandidate) { $projectCandidate } else { Join-Path $PSScriptRoot '..\stage-admin-full' }
}
$testRoot = Join-Path $PSScriptRoot 'runtime-test-data'
New-Item -ItemType Directory -Force -Path $testRoot | Out-Null
$password = 'LocalCreatorTest1234'
$salt = New-Object byte[] 16
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
try { $rng.GetBytes($salt) } finally { $rng.Dispose() }
$derive = [Security.Cryptography.Rfc2898DeriveBytes]::new($password, $salt, 210000, [Security.Cryptography.HashAlgorithmName]::SHA256)
try { $hash = $derive.GetBytes(32) } finally { $derive.Dispose() }

$env:OPERATOR_PASSWORD_HASH = 'pbkdf2_sha256$210000$' + [Convert]::ToBase64String($salt) + '$' + [Convert]::ToBase64String($hash)
$env:ADMIN_ENCRYPTION_KEY = 'local-test-encryption-key-123456789012345678901234567890'
$env:APP_ROOT = [IO.Path]::GetFullPath($CreatorRoot)
$env:WORKSPACE_ROOT = [IO.Path]::GetFullPath($WorkspaceRoot)
$env:ADMIN_DATA_ROOT = $testRoot
$env:HOST = '127.0.0.1'
$env:PORT = [string]$Port
$stdout = Join-Path $testRoot 'server.out.log'
$stderr = Join-Path $testRoot 'server.err.log'
$process = Start-Process -FilePath node -ArgumentList 'server.mjs' -WorkingDirectory $env:APP_ROOT -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru

try {
  $ready = $false
  for ($attempt = 0; $attempt -lt 40; $attempt++) {
    try { $ready = (Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$Port/api/health" -TimeoutSec 2).StatusCode -eq 200 } catch { $ready = $false }
    if ($ready) { break }
    Start-Sleep -Milliseconds 250
  }
  if (-not $ready) { throw 'Test sunucusu açılamadı.' }

  $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
  $login = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$Port/api/login" -WebSession $session -ContentType 'application/json' -Body (@{ password = $password } | ConvertTo-Json)
  $headers = @{ 'X-CSRF-Token' = $login.csrf_token }
  $payload = @{
    name = 'Gizli Motor Testi'; slug = 'gizli-motor-testi'; brand_name = 'Test Marka'; description = 'Yerel doğrulama'; accent = '#8b5cf6'
    features = @('brand','content','visuals','workflow','approvals','connections','models'); plan_id = 'basic'; max_enabled_agents = 11; monthly_token_limit = 300000; debate_rounds = 1; agent_names = @{}
    api_control_mode = 'locked'; allowed_providers = 'google_gemini,openai'; text_provider = 'google_gemini'; text_model = 'auto'; visual_provider = 'openai'; visual_model = 'auto'; credential_reentry_allowed = $false; meta_reconnect_allowed = $false
    chat_enabled = $true; chat_model_mode = 'inherit'; chat_provider = ''; chat_model = ''; chat_token_limit = 900; chat_content_revision = $true; chat_visual_revision = $true
  } | ConvertTo-Json -Depth 8
  $created = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$Port/api/apps" -WebSession $session -Headers $headers -ContentType 'application/json' -Body $payload
  $packageResponse = Invoke-WebRequest -UseBasicParsing -Uri ("http://127.0.0.1:$Port/api/apps/{0}/package" -f $created.app.app_id) -WebSession $session
  $package = $packageResponse.Content | ConvertFrom-Json
  $checks = [ordered]@{
    core_roles = $package.app.agents.Count -eq 11
    hidden_n8n = $package.app.runtime_engine.type -eq 'embedded_managed_n8n' -and $package.app.runtime_engine.user_account_required -eq $false -and $package.app.runtime_engine.user_interface_exposed -eq $false
    workflow_count = $package.runtime_blueprint.workflows.Count -eq 22
    all_workflows_passive = @($package.runtime_blueprint.workflows | Where-Object { $_.active -ne $false }).Count -eq 0
    no_workflow_credentials = $packageResponse.Content -notmatch '"credentials"\s*:'
    api_locked = $package.app.connection_policy.api_control_mode -eq 'locked' -and $package.app.connection_policy.provider_selection_editable -eq $false -and $package.app.connection_policy.can_add_providers -eq $false
    chat_guarded = $package.app.assistant_chat.enabled -eq $true -and $package.app.assistant_chat.permissions.publish -eq $false -and $package.app.assistant_chat.permissions.change_hidden_workflows -eq $false -and $package.app.assistant_chat.maximum_tokens_per_message -eq 900
    mode_gating = @($package.app.operating_modes.catalog | Where-Object { $_.id -eq 'autonomous' -and $_.access_state -eq 'upgrade_required' -and $_.minimum_plan -eq 'pro' }).Count -eq 1
    autonomous_acceptance = $package.app.operating_modes.autonomous.requires_explicit_risk_acceptance -eq $true -and $package.app.operating_modes.autonomous.can_bypass_final_publish_approval -eq $true -and $package.app.operating_modes.autonomous.acceptance_text_sha256.Length -eq 64
    controlled_auto_approval = $package.app.operating_modes.guided_auto.can_bypass_final_publish_approval -eq $false -and $package.integrity.controlled_auto_requires_final_approval -eq $true
    credentials_absent = $package.credentials_included -eq $false
  }
  $failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value } | ForEach-Object { $_.Key })
  if ($failed.Count) { throw "Doğrulama başarısız: $($failed -join ', ')" }
  $checks | ConvertTo-Json
}
finally {
  if ($process -and -not $process.HasExited) { Stop-Process -Id $process.Id -Force }
  Remove-Item Env:OPERATOR_PASSWORD_HASH,Env:ADMIN_ENCRYPTION_KEY,Env:APP_ROOT,Env:WORKSPACE_ROOT,Env:ADMIN_DATA_ROOT,Env:HOST,Env:PORT -ErrorAction SilentlyContinue
}

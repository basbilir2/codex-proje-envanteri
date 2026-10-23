param([switch]$Check, [string]$ProjectPath)
$ErrorActionPreference = 'Stop'
$Host.UI.RawUI.WindowTitle = 'Uc AI Terminal - DeepSeek + GLM + Nemotron'
[Console]::InputEncoding = New-Object System.Text.UTF8Encoding
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$env:OPENCODE_CONFIG = Join-Path $PSScriptRoot 'opencode.json'
$env:OPENCODE_DISABLE_AUTOUPDATE = 'true'
$env:XDG_CONFIG_HOME = Join-Path $PSScriptRoot 'user\config'
$env:XDG_DATA_HOME = Join-Path $PSScriptRoot 'user\data'
$env:XDG_CACHE_HOME = Join-Path $PSScriptRoot 'user\cache'
$env:XDG_STATE_HOME = Join-Path $PSScriptRoot 'user\state'
Remove-Item Env:OPENCODE_CONFIG_CONTENT -ErrorAction SilentlyContinue
Remove-Item Env:OPENCODE_CONFIG_DIR -ErrorAction SilentlyContinue
$secretFile = Join-Path $PSScriptRoot 'nvidia-key.dpapi'
$secureKey = ConvertTo-SecureString ([IO.File]::ReadAllText($secretFile))
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
try { $env:NVIDIA_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
$pythonArgs = @((Join-Path $PSScriptRoot 'terminal.py'))
if ($Check) { $pythonArgs += '--check' }
if ($ProjectPath) { $pythonArgs += @('--project', $ProjectPath) }
try {
    & python @pythonArgs
    exit $LASTEXITCODE
} finally { Remove-Item Env:NVIDIA_API_KEY -ErrorAction SilentlyContinue }

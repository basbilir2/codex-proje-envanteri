param([switch]$NoOpen)
$env:PSModulePath = $PSHOME + '\Modules'
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
try {
    $secretFile = Join-Path $PSScriptRoot 'nvidia-key.dpapi'
    $secureKey = ConvertTo-SecureString ([IO.File]::ReadAllText($secretFile))
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
    try { $env:NVIDIA_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
    $pythonArgs = @((Join-Path $PSScriptRoot 'studio.py'))
    if ($NoOpen) { $pythonArgs += '--no-open' }
    & python @pythonArgs 2>> (Join-Path $PSScriptRoot 'studio-startup.log')
    if ($LASTEXITCODE -ne 0) { throw 'Uygulama baslatilamadi. .system/studio-startup.log dosyasina bak.' }
} catch {
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot 'studio-startup-error.txt'), $_.Exception.Message)
    Add-Type -AssemblyName System.Windows.Forms
    [Windows.Forms.MessageBox]::Show($_.Exception.Message, 'Uc AI Studyo') | Out-Null
} finally { Remove-Item Env:NVIDIA_API_KEY -ErrorAction SilentlyContinue }

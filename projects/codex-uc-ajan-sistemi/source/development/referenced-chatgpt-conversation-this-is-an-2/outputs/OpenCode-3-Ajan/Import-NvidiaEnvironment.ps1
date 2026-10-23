$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (-not $env:NVIDIA_API_KEY) {
    foreach ($name in @('NVIDIA_API_KEY','NIM_API_KEY','NVIDIA_NIM_API_KEY')) {
        foreach ($scope in @('Process','User','Machine')) {
            $candidate = [Environment]::GetEnvironmentVariable($name,$scope)
            if ($candidate) { $env:NVIDIA_API_KEY = $candidate; break }
        }
        if ($env:NVIDIA_API_KEY) { break }
    }
}
if (-not $env:NVIDIA_API_KEY) {
    $secretFile = Join-Path $workspace 'work\secrets\nvidia-key.dpapi'
    if (Test-Path -LiteralPath $secretFile) {
        $secureKey = ConvertTo-SecureString ([IO.File]::ReadAllText($secretFile))
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
        try { $env:NVIDIA_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
        finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
    }
}
# These variables apply only to the current process and its OpenCode child.
$env:OPENCODE_CONFIG = Join-Path $PSScriptRoot 'opencode.json'
$env:OPENCODE_DISABLE_AUTOUPDATE = 'true'

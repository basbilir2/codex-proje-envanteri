$ErrorActionPreference = 'Stop'

$target = 'C:\Users\USER\AppData\Local\Docker\wsl\disk\docker_data.vhdx'
$expected = [System.IO.Path]::GetFullPath('C:\Users\USER\AppData\Local\Docker\wsl\disk\docker_data.vhdx')
$resolved = [System.IO.Path]::GetFullPath($target)
$allowedParent = [System.IO.Path]::GetFullPath('C:\Users\USER\AppData\Local\Docker\wsl\disk').TrimEnd('\') + '\'

if ($resolved -ne $expected -or -not $resolved.StartsWith($allowedParent, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Docker disk target validation failed: $resolved"
}

$dockerProcesses = Get-Process -ErrorAction SilentlyContinue |
    Where-Object { $_.ProcessName -match '^(Docker Desktop|com\.docker\..*|dockerd)$' }
if ($dockerProcesses) {
    throw 'Docker is running; data disk removal stopped.'
}

$distros = (wsl.exe --list --quiet 2>$null) -replace "`0", ''
if ($distros -contains 'docker-desktop') {
    throw 'docker-desktop is still registered; data disk removal stopped.'
}

if (-not (Test-Path -LiteralPath $resolved)) {
    [pscustomobject]@{ Path = $resolved; BeforeGB = 0; Removed = $true } | Format-List
    exit 0
}

$item = Get-Item -LiteralPath $resolved -Force
if ($item.PSIsContainer -or ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'Refusing unexpected Docker data target type.'
}

$before = [int64]$item.Length
Remove-Item -LiteralPath $resolved -Force

[pscustomobject]@{
    Path = $resolved
    BeforeGB = [math]::Round($before / 1GB, 3)
    Removed = -not (Test-Path -LiteralPath $resolved)
} | Format-List

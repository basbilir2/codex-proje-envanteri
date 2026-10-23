$ErrorActionPreference = 'Stop'

$removeRoots = @(
    'C:\Users\USER\AppData\Roaming\Adobe',
    'C:\Users\USER\AppData\Roaming\com.adobe.dunamis',
    'C:\Users\USER\AppData\Roaming\Zoom',
    'C:\Users\USER\AppData\Roaming\Opera Software',
    'C:\Users\USER\AppData\Local\CapCut'
)
$tempRoot = 'C:\Users\USER\AppData\Local\Temp'

function Get-Bytes([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return [int64]0 }
    return [int64]((Get-ChildItem -LiteralPath $Path -Force -Recurse -File -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum).Sum)
}

function Assert-OrdinaryDirectory([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    if (-not $item.PSIsContainer) { throw "Not a directory: $Path" }
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse point refused: $Path" }
    $link = Get-ChildItem -LiteralPath $Path -Force -Recurse -Attributes ReparsePoint -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($link) { throw "Nested reparse point refused: $($link.FullName)" }
}

$results = @()
foreach ($path in $removeRoots) {
    if (-not (Test-Path -LiteralPath $path)) { continue }
    Assert-OrdinaryDirectory $path
    $before = Get-Bytes $path
    try {
        Remove-Item -LiteralPath $path -Force -Recurse -ErrorAction Stop
        $results += [pscustomobject]@{ Path = $path; BeforeBytes = $before; Removed = $true; RemainingBytes = 0; Error = $null }
    } catch {
        $results += [pscustomobject]@{ Path = $path; BeforeBytes = $before; Removed = $false; RemainingBytes = Get-Bytes $path; Error = $_.Exception.Message }
    }
}

Assert-OrdinaryDirectory $tempRoot
Get-ChildItem -LiteralPath $tempRoot -Force | ForEach-Object {
    if ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse point refused: $($_.FullName)" }
}
$tempBefore = Get-Bytes $tempRoot
$tempErrors = @()
Get-ChildItem -LiteralPath $tempRoot -Force | ForEach-Object {
    try { Remove-Item -LiteralPath $_.FullName -Force -Recurse -ErrorAction Stop } catch { $tempErrors += $_.Exception.Message }
}
$results += [pscustomobject]@{ Path = "$tempRoot (contents only)"; BeforeBytes = $tempBefore; Removed = ($tempErrors.Count -eq 0); RemainingBytes = Get-Bytes $tempRoot; Error = ($tempErrors -join ' | ') }

$results | ConvertTo-Json -Depth 3

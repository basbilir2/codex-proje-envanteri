param(
    [switch]$Chrome,
    [switch]$CapCut
)

$ErrorActionPreference = 'Stop'

function Get-TreeBytes([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return [int64]0 }
    $sum = [int64]0
    Get-ChildItem -LiteralPath $Path -File -Force -Recurse -ErrorAction SilentlyContinue |
        ForEach-Object { $sum += [int64]$_.Length }
    return $sum
}

function Remove-VerifiedTree([string]$Path, [string]$AllowedRoot) {
    $full = [System.IO.Path]::GetFullPath($Path).TrimEnd('\')
    $root = [System.IO.Path]::GetFullPath($AllowedRoot).TrimEnd('\') + '\'
    if (-not $full.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsafe target outside allowed root: $full"
    }
    if (-not (Test-Path -LiteralPath $full)) {
        return [pscustomobject]@{ Path = $full; BeforeBytes = 0; RemainingBytes = 0; Status = 'NotFound' }
    }
    $item = Get-Item -LiteralPath $full -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Refusing reparse-point target: $full"
    }
    $before = Get-TreeBytes $full
    Remove-Item -LiteralPath $full -Recurse -Force -ErrorAction SilentlyContinue
    $remaining = Get-TreeBytes $full
    [pscustomobject]@{
        Path = $full
        BeforeBytes = $before
        RemainingBytes = $remaining
        Status = if ($remaining -eq 0) { 'Removed' } else { 'PartiallyRemoved' }
    }
}

$results = [System.Collections.Generic.List[object]]::new()

if ($Chrome) {
    if (Get-Process chrome -ErrorAction SilentlyContinue) {
        throw 'Chrome is running; close Chrome before cache cleanup.'
    }
    $chromeRoot = 'C:\Users\USER\AppData\Local\Google\Chrome\User Data'
    $profilePattern = '^(Default|Profile \d+|Guest Profile|System Profile)$'
    $directCaches = @('Cache', 'Code Cache', 'GPUCache', 'DawnWebGPUCache', 'DawnGraphiteCache', 'GrShaderCache', 'ShaderCache', 'Media Cache')
    Get-ChildItem -LiteralPath $chromeRoot -Directory -Force -ErrorAction Stop |
        Where-Object { $_.Name -match $profilePattern } |
        ForEach-Object {
            $profile = $_.FullName
            foreach ($name in $directCaches) {
                $results.Add((Remove-VerifiedTree (Join-Path $profile $name) $chromeRoot))
            }
            $results.Add((Remove-VerifiedTree (Join-Path $profile 'Service Worker\CacheStorage') $chromeRoot))
            $results.Add((Remove-VerifiedTree (Join-Path $profile 'Service Worker\ScriptCache') $chromeRoot))
        }
}

if ($CapCut) {
    if (Get-Process CapCut -ErrorAction SilentlyContinue) {
        throw 'CapCut is running; close CapCut before cache cleanup.'
    }
    $capCutRoot = 'C:\Users\USER\AppData\Local\CapCut'
    $capCutTargets = @(
        'C:\Users\USER\AppData\Local\CapCut\User Data\Cache',
        'C:\Users\USER\AppData\Local\CapCut\User Data\Download',
        'C:\Users\USER\AppData\Local\CapCut\User Data\CEF\Cache'
    )
    foreach ($target in $capCutTargets) {
        $results.Add((Remove-VerifiedTree $target $capCutRoot))
    }
}

$beforeTotal = [int64](($results | Measure-Object BeforeBytes -Sum).Sum)
$remainingTotal = [int64](($results | Measure-Object RemainingBytes -Sum).Sum)
$results | Where-Object { $_.BeforeBytes -gt 0 } | Sort-Object BeforeBytes -Descending | Select-Object -First 20 Status,
    @{n='BeforeGB';e={[math]::Round($_.BeforeBytes / 1GB, 3)}},
    @{n='RemainingGB';e={[math]::Round($_.RemainingBytes / 1GB, 3)}},Path | Format-Table -AutoSize
[pscustomobject]@{
    TargetedGB = [math]::Round($beforeTotal / 1GB, 3)
    RemovedGB = [math]::Round(($beforeTotal - $remainingTotal) / 1GB, 3)
    RemainingGB = [math]::Round($remainingTotal / 1GB, 3)
} | Format-List

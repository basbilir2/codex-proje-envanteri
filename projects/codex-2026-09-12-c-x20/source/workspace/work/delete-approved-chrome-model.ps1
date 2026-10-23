$ErrorActionPreference = 'Stop'

$target = 'C:\Users\USER\AppData\Local\Google\Chrome\User Data\OptGuideOnDeviceModel'
$allowedRoot = [System.IO.Path]::GetFullPath('C:\Users\USER\AppData\Local\Google\Chrome\User Data').TrimEnd('\') + '\'
$resolved = [System.IO.Path]::GetFullPath($target).TrimEnd('\')

if (-not $resolved.StartsWith($allowedRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
    [System.IO.Path]::GetFileName($resolved) -ne 'OptGuideOnDeviceModel') {
    throw "Chrome model target validation failed: $resolved"
}
if (Get-Process chrome -ErrorAction SilentlyContinue) {
    throw 'Chrome is running; model removal stopped.'
}
if (-not (Test-Path -LiteralPath $resolved)) {
    [pscustomobject]@{ Removed = $true; RemovedGB = 0; Path = $resolved } | Format-List
    exit 0
}

$item = Get-Item -LiteralPath $resolved -Force
if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'Refusing reparse-point target.'
}
$before = (Get-ChildItem -LiteralPath $resolved -File -Recurse -Force -ErrorAction SilentlyContinue |
    Measure-Object Length -Sum).Sum
Remove-Item -LiteralPath $resolved -Recurse -Force

[pscustomobject]@{
    Removed = -not (Test-Path -LiteralPath $resolved)
    RemovedGB = [math]::Round($before / 1GB, 3)
    Path = $resolved
} | Format-List

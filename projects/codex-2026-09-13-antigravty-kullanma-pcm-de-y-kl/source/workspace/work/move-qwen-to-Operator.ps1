$ErrorActionPreference = 'Stop'
$source = 'C:\Users\USER\AppData\Local\LocalAIOS\models\Qwen3-14B-Q4_K_M.gguf'
$target = 'D:\Qwen3-14B-Q4_K_M.gguf'

if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Source model not found: $source" }
if (Test-Path -LiteralPath $target) { throw "Target already exists: $target" }
$sourceItem = Get-Item -LiteralPath $source -Force
if ($sourceItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Source reparse point refused.' }

Copy-Item -LiteralPath $source -Destination $target -Force -ErrorAction Stop
$targetItem = Get-Item -LiteralPath $target -Force
if ($targetItem.Length -ne $sourceItem.Length) { throw "Copy size mismatch: source=$($sourceItem.Length), target=$($targetItem.Length)" }
$sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
$targetHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
if ($sourceHash -ne $targetHash) { throw 'Copy hash mismatch; source is retained.' }

Remove-Item -LiteralPath $source -Force -ErrorAction Stop
[pscustomobject]@{
    Source = $source
    Target = $target
    SizeGB = [math]::Round($sourceItem.Length / 1GB, 2)
    SHA256 = $sourceHash
    SourceRemoved = -not (Test-Path -LiteralPath $source)
    TargetVerified = (Test-Path -LiteralPath $target)
} | Format-List

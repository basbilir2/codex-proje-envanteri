param([Parameter(Mandatory=$true)][string]$PlanPath)
$ErrorActionPreference = 'Stop'
$plan = Get-Content -LiteralPath $PlanPath -Raw -Encoding UTF8 | ConvertFrom-Json
$cutoff = [DateTimeOffset]::Parse($plan.cutoff_utc).UtcDateTime
$roots = @($plan.approved_roots | ForEach-Object { (Resolve-Path -LiteralPath $_).ProviderPath.TrimEnd('\') })
$approvedFiles = @($plan.approved_files | ForEach-Object { [IO.Path]::GetFullPath($_) })
if ($roots.Count -eq 0 -or @($roots | Where-Object { $_.Length -lt 12 }).Count) { throw 'Invalid cleanup roots.' }
$protectedRoots = @($plan.protected_roots | ForEach-Object { [IO.Path]::GetFullPath($_).TrimEnd('\') })
$protectedFiles = @($plan.protected_files | ForEach-Object { [IO.Path]::GetFullPath($_) })
$reportDir = [IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($PlanPath))
$logPath = Join-Path $reportDir 'deletion-log.jsonl'
$writer = [IO.StreamWriter]::new($logPath, $true, [Text.UTF8Encoding]::new($false))
$beforeFree = ([IO.DriveInfo]::new('C')).AvailableFreeSpace
[long]$removedBytes=0; [int]$removed=0; [int]$skipped=0; [int]$failed=0
try {
    foreach ($target in $plan.targets) {
        $status='skipped'; $reason=''; $path=[IO.Path]::GetFullPath($target.path)
        try {
            if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'Not an existing ordinary file.' }
            $resolved=(Resolve-Path -LiteralPath $path).ProviderPath
            $matchingRoot=@($roots | Where-Object { $resolved.StartsWith($_+'\', [StringComparison]::OrdinalIgnoreCase) })
            if ($matchingRoot.Count -eq 0 -and $approvedFiles -notcontains $resolved) { throw 'Outside exact approved Lenticular artifact roots/files.' }
            if ($resolved -match '\\(sources|\.git)\\') { throw 'Protected synced source/repository path.' }
            foreach ($p in $protectedRoots) {
                if ($resolved.Equals($p,[StringComparison]::OrdinalIgnoreCase) -or $resolved.StartsWith($p+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Protected active resource.' }
            }
            if ($protectedFiles -contains $resolved) { throw 'Protected dependency file.' }
            $cursor=$resolved
            while ($cursor -and $cursor.Length -gt 3) {
                if ([IO.File]::GetAttributes($cursor) -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse point in target ancestry.' }
                $cursor=[IO.Path]::GetDirectoryName($cursor)
            }
            $file=Get-Item -LiteralPath $resolved -Force
            if ($file.PSIsContainer) { throw 'Directory removal is not allowed.' }
            if ($file.CreationTimeUtc -ge $cutoff -or $file.LastWriteTimeUtc -ge $cutoff) { throw 'Created or modified within protected 24 hours.' }
            if ($file.Length -ne $target.bytes) { throw 'File changed after inventory.' }
            $length=$file.Length
            Remove-Item -LiteralPath $resolved -Force
            if (Test-Path -LiteralPath $resolved) { throw 'File still present after removal.' }
            $removedBytes+=$length; $removed++; $status='deleted'
        } catch {
            $reason=$_.Exception.Message
            if ($reason -like '*after removal*') { $status='failed'; $failed++ } else { $skipped++ }
        }
        $writer.WriteLine((@{path=$path;status=$status;bytes=$target.bytes;reason=$reason;utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Compress))
        if (($removed+$skipped+$failed)%200 -eq 0) { $writer.Flush() }
        if (($removed+$skipped+$failed)%2000 -eq 0) { Write-Output ('Deleted {0} files / {1:N2} GB.' -f $removed, ($removedBytes/1e9)) }
    }
} finally { $writer.Dispose() }
$summary=@{cutoff_utc=$plan.cutoff_utc;removed_files=$removed;removed_bytes=$removedBytes;removed_gb=$removedBytes/1e9;removed_gib=$removedBytes/1GB;skipped_files=$skipped;failed_files=$failed;free_before_bytes=$beforeFree;free_after_bytes=([IO.DriveInfo]::new('C')).AvailableFreeSpace;deletion_log=$logPath}
$summary | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $reportDir 'deletion-result.json') -Encoding UTF8
$summary | ConvertTo-Json -Depth 4

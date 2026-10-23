param(
    [string]$Root = 'C:\',
    [string]$UserRoot = 'C:\Users\USER',
    [string]$OutputPath = 'C:\Users\USER\Documents\Codex\2026-09-12\c-x20\work\disk-audit.json'
)

$ErrorActionPreference = 'Stop'

Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;

public sealed class DiskAuditResult
{
    public Dictionary<string,long> DirectoryBytes { get; set; } = new Dictionary<string,long>(StringComparer.OrdinalIgnoreCase);
    public List<LargeFileItem> LargeFiles { get; set; } = new List<LargeFileItem>();
    public long TotalBytes { get; set; }
    public long FileCount { get; set; }
    public long DirectoryCount { get; set; }
    public long ErrorCount { get; set; }
}

public sealed class LargeFileItem
{
    public string Path { get; set; }
    public long Bytes { get; set; }
    public DateTime LastWriteTime { get; set; }
}

public static class DiskAuditor
{
    private static void Add(Dictionary<string,long> map, string key, long value)
    {
        long old;
        map.TryGetValue(key, out old);
        map[key] = old + value;
    }

    private static int RelativeDepth(string root, string path)
    {
        string rel = path.Substring(root.TrimEnd('\\').Length).Trim('\\');
        if (rel.Length == 0) return 0;
        return rel.Split(new[]{'\\'}, StringSplitOptions.RemoveEmptyEntries).Length;
    }

    private static void AddAncestors(DiskAuditResult result, string root, string userRoot, string directory, long bytes)
    {
        string current = directory;
        while (!String.IsNullOrEmpty(current))
        {
            bool underRoot = current.StartsWith(root, StringComparison.OrdinalIgnoreCase) ||
                             String.Equals(current.TrimEnd('\\'), root.TrimEnd('\\'), StringComparison.OrdinalIgnoreCase);
            if (!underRoot) break;

            int driveDepth = RelativeDepth(root, current);
            bool underUser = current.StartsWith(userRoot.TrimEnd('\\') + "\\", StringComparison.OrdinalIgnoreCase) ||
                             String.Equals(current.TrimEnd('\\'), userRoot.TrimEnd('\\'), StringComparison.OrdinalIgnoreCase);
            int userDepth = underUser ? RelativeDepth(userRoot, current) : Int32.MaxValue;

            if (driveDepth <= 3 || (underUser && userDepth <= 5)) Add(result.DirectoryBytes, current.TrimEnd('\\'), bytes);

            DirectoryInfo parent;
            try { parent = Directory.GetParent(current); }
            catch { break; }
            if (parent == null) break;
            current = parent.FullName;
        }
    }

    public static DiskAuditResult Run(string root, string userRoot)
    {
        var result = new DiskAuditResult();
        var pending = new Stack<string>();
        pending.Push(root);

        while (pending.Count > 0)
        {
            string dir = pending.Pop();
            result.DirectoryCount++;

            try
            {
                foreach (string file in Directory.EnumerateFiles(dir))
                {
                    try
                    {
                        var info = new FileInfo(file);
                        long size = info.Length;
                        result.TotalBytes += size;
                        result.FileCount++;
                        AddAncestors(result, root, userRoot, dir, size);
                        if (size >= 100L * 1024L * 1024L)
                        {
                            result.LargeFiles.Add(new LargeFileItem { Path = file, Bytes = size, LastWriteTime = info.LastWriteTime });
                        }
                    }
                    catch { result.ErrorCount++; }
                }
            }
            catch { result.ErrorCount++; }

            try
            {
                foreach (string child in Directory.EnumerateDirectories(dir))
                {
                    try
                    {
                        var attrs = File.GetAttributes(child);
                        if ((attrs & FileAttributes.ReparsePoint) == 0) pending.Push(child);
                    }
                    catch { result.ErrorCount++; }
                }
            }
            catch { result.ErrorCount++; }
        }

        result.LargeFiles = result.LargeFiles.OrderByDescending(x => x.Bytes).Take(300).ToList();
        return result;
    }
}
'@

$result = [DiskAuditor]::Run($Root, $UserRoot)
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
$summary = [pscustomobject]@{
    ScannedGB = [math]::Round($result.TotalBytes / 1GB, 2)
    Files = $result.FileCount
    Directories = $result.DirectoryCount
    Errors = $result.ErrorCount
    LargeFiles = $result.LargeFiles.Count
    OutputPath = $OutputPath
}
$summary | Format-List

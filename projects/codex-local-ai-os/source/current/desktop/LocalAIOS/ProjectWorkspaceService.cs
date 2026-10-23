using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace LocalAIOS;

internal sealed record ProjectCloneResult(string SourcePath, string ProjectPath, int CopiedFiles);

internal static class ProjectWorkspaceService
{
    private static readonly HashSet<string> ExcludedDirectories = new(StringComparer.OrdinalIgnoreCase)
    {
        ".git", ".vs", ".idea", ".vscode", "node_modules", "bin", "obj", "dist", "build",
        "coverage", ".next", ".nuxt", ".cache", "packages"
    };

    private static readonly HashSet<string> TextExtensions = new(StringComparer.OrdinalIgnoreCase)
    {
        ".cs", ".fs", ".vb", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".java",
        ".go", ".rs", ".php", ".rb", ".cpp", ".c", ".h", ".html", ".css", ".scss", ".sql",
        ".json", ".xml", ".yml", ".yaml", ".toml", ".ini", ".config", ".md", ".txt", ".sln",
        ".csproj", ".fsproj", ".vbproj", ".props", ".targets", ".ps1", ".cmd", ".bat", ".sh"
    };

    public static async Task<ProjectCloneResult> CreateNextVersionAsync(string sourcePath, CancellationToken cancellationToken)
    {
        var source = Path.GetFullPath(sourcePath.Trim());
        if (!Directory.Exists(source)) throw new DirectoryNotFoundException("Seçilen eski proje klasörü bulunamadı.");

        var destination = NextAvailablePath(source);
        Directory.CreateDirectory(destination);
        var copied = 0;
        try
        {
            foreach (var file in EnumerateProjectFiles(source))
            {
                cancellationToken.ThrowIfCancellationRequested();
                var relative = Path.GetRelativePath(source, file);
                var target = SafePath(destination, relative);
                Directory.CreateDirectory(Path.GetDirectoryName(target)!);
                await using var input = new FileStream(file, FileMode.Open, FileAccess.Read, FileShare.ReadWrite, 81920, true);
                await using var output = new FileStream(target, FileMode.CreateNew, FileAccess.Write, FileShare.None, 81920, true);
                await input.CopyToAsync(output, cancellationToken);
                copied++;
            }

            var localAi = Path.Combine(destination, ".localaios");
            Directory.CreateDirectory(localAi);
            await File.WriteAllTextAsync(Path.Combine(localAi, "project.json"), JsonSerializer.Serialize(new
            {
                schemaVersion = 1,
                sourceReadOnly = source,
                activeWritableProject = destination,
                createdAt = DateTimeOffset.Now,
                rule = "The source project is reference-only. All changes must stay inside activeWritableProject."
            }, AppSettings.JsonOptions), cancellationToken);
            await File.WriteAllTextAsync(Path.Combine(localAi, "PROJECT_CONTEXT.md"), $"""
                # Local AI OS Project Context

                - Original reference project: `{source}`
                - Active writable project: `{destination}`
                - Created: {DateTimeOffset.Now:O}
                - Copied source files: {copied}

                The original project is read-only reference material for this continuation. Never edit, move,
                rename or delete anything under the original path. Continue all work only in this new project.
                Build outputs and dependency caches were intentionally not copied; they can be recreated.
                """, cancellationToken);
            return new(source, destination, copied);
        }
        catch
        {
            try { if (Directory.Exists(destination)) Directory.Delete(destination, true); } catch { }
            throw;
        }
    }

    public static async Task<string> BuildContextAsync(string projectPath, string request, CancellationToken cancellationToken)
    {
        var root = Path.GetFullPath(projectPath);
        if (!Directory.Exists(root)) return "";
        var files = EnumerateProjectFiles(root).Take(1200).ToArray();
        var relativePaths = files.Select(file => Path.GetRelativePath(root, file)).ToArray();
        var terms = Regex.Matches(request.ToLowerInvariant(), @"[\p{L}\p{N}_-]{3,}")
            .Select(match => match.Value).Distinct().Take(20).ToArray();
        var selected = files
            .Where(IsSafeTextFile)
            .OrderByDescending(file => Relevance(Path.GetRelativePath(root, file), terms))
            .ThenBy(file => Path.GetRelativePath(root, file).Length)
            .Take(28)
            .ToArray();

        var builder = new StringBuilder();
        builder.AppendLine($"Aktif ve yazılabilir proje: {root}");
        builder.AppendLine("Bu klasörün dışına yazma. Eski kaynak proje yalnızca referanstır.");
        builder.AppendLine("\nProje dosya haritası:");
        foreach (var path in relativePaths.Take(400)) builder.AppendLine("- " + path);
        builder.AppendLine("\nİlgili dosya içerikleri:");
        foreach (var file in selected)
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (builder.Length >= 60000) break;
            try
            {
                var content = await File.ReadAllTextAsync(file, cancellationToken);
                if (content.IndexOf('\0') >= 0) continue;
                if (content.Length > 12000) content = content[..12000] + "\n[dosyanın devamı kısaltıldı]";
                builder.AppendLine($"\n--- {Path.GetRelativePath(root, file)} ---\n{content}");
            }
            catch { }
        }
        return builder.ToString()[..Math.Min(builder.Length, 65000)];
    }

    public static string SafePath(string root, string relativePath)
    {
        if (string.IsNullOrWhiteSpace(relativePath) || Path.IsPathRooted(relativePath))
            throw new InvalidOperationException("Geçersiz proje dosyası yolu.");
        var fullRoot = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        var full = Path.GetFullPath(Path.Combine(fullRoot, relativePath));
        if (!full.StartsWith(fullRoot, StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Proje klasörü dışına yazma engellendi.");
        var firstPart = Path.GetRelativePath(fullRoot, full).Split(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)[0];
        if (firstPart.Equals(".git", StringComparison.OrdinalIgnoreCase) ||
            firstPart.Equals(".localaios", StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Korunan proje alanına yazma engellendi.");
        return full;
    }

    private static string NextAvailablePath(string source)
    {
        var parent = Directory.GetParent(source)?.FullName ?? throw new InvalidOperationException("Proje üst klasörü bulunamadı.");
        var name = Path.GetFileName(source.TrimEnd(Path.DirectorySeparatorChar));
        var match = Regex.Match(name, @"^(.*?)(?:\s+v(\d+))$", RegexOptions.IgnoreCase);
        var baseName = match.Success ? match.Groups[1].Value.Trim() : name;
        var version = match.Success && int.TryParse(match.Groups[2].Value, out var current) ? current + 1 : 2;
        string candidate;
        do { candidate = Path.Combine(parent, $"{baseName} v{version++}"); } while (Directory.Exists(candidate));
        return candidate;
    }

    private static IEnumerable<string> EnumerateProjectFiles(string root)
    {
        var pending = new Stack<string>();
        pending.Push(root);
        while (pending.Count > 0)
        {
            var directory = pending.Pop();
            IEnumerable<string> directories;
            IEnumerable<string> files;
            try
            {
                directories = Directory.EnumerateDirectories(directory).ToArray();
                files = Directory.EnumerateFiles(directory).ToArray();
            }
            catch { continue; }
            foreach (var file in files) yield return file;
            foreach (var child in directories)
            {
                try
                {
                    if (ExcludedDirectories.Contains(Path.GetFileName(child))) continue;
                    if ((File.GetAttributes(child) & FileAttributes.ReparsePoint) != 0) continue;
                    pending.Push(child);
                }
                catch { }
            }
        }
    }

    private static bool IsSafeTextFile(string file)
    {
        var name = Path.GetFileName(file);
        if (name.Equals(".env", StringComparison.OrdinalIgnoreCase) || name.Contains("secret", StringComparison.OrdinalIgnoreCase)) return false;
        try { return TextExtensions.Contains(Path.GetExtension(file)) && new FileInfo(file).Length <= 1_000_000; }
        catch { return false; }
    }

    private static int Relevance(string path, string[] terms)
    {
        var lower = path.ToLowerInvariant();
        var score = terms.Count(lower.Contains) * 10;
        if (lower.EndsWith("readme.md") || lower.EndsWith("project_context.md") || lower.EndsWith("agents.md")) score += 50;
        if (lower.EndsWith("package.json") || lower.EndsWith(".sln") || lower.EndsWith(".csproj")) score += 35;
        return score;
    }
}

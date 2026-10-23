using System.Text.Json;

namespace LocalAIOS;

internal sealed record ProjectChangeResult(string Summary, string[] Files, string ProjectPath);
internal sealed record ProjectChangePlan(string Summary, ProjectFileChange[] Files);
internal sealed record ProjectFileChange(string Path, string Content);

internal sealed class ProjectAgentService(LocalModelClient model)
{
    public async Task<ProjectChangeResult> ApplyAsync(string projectPath, string request, CancellationToken cancellationToken)
    {
        var root = Path.GetFullPath(projectPath);
        var marker = Path.Combine(root, ".localaios", "project.json");
        if (!File.Exists(marker)) throw new InvalidOperationException("Bu klasör güvenli bir Local AI OS çalışma kopyası değil.");
        var context = await ProjectWorkspaceService.BuildContextAsync(root, request, cancellationToken);
        var raw = await model.GenerateAsync("""
            You are a careful software engineer editing a protected project copy. Return one JSON object only:
            {"summary":"short user-language summary","files":[{"path":"relative/path","content":"complete file content"}]}
            Analyze the supplied project context and implement the user's request with the smallest coherent change.
            Every path must be relative to the active project. Never use .., absolute paths, .git or .localaios.
            Return complete final content for each changed or new file. Do not delete files and do not use markdown fences.
            Do not claim tests were run. If no file change is needed, return an empty files array and explain in summary.
            """, $"Kullanıcı isteği:\n{request}\n\n{context}", cancellationToken, 6000, true);
        var plan = ParsePlan(raw);
        return await ApplyPlanAsync(root, request, plan, cancellationToken);
    }

    internal static async Task<ProjectChangeResult> ApplyPlanAsync(
        string root, string request, ProjectChangePlan plan, CancellationToken cancellationToken)
    {
        if (plan.Files.Length > 12) throw new InvalidOperationException("Tek işlemde en fazla 12 dosya güvenle değiştirilebilir.");
        var changed = new List<string>();
        var backupRoot = Path.Combine(root, ".localaios", "backups", DateTime.Now.ToString("yyyyMMdd-HHmmss"));
        foreach (var change in plan.Files)
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (change.Content.Length > 1_000_000) throw new InvalidOperationException("Üretilen dosya güvenli boyut sınırını aştı.");
            var destination = ProjectWorkspaceService.SafePath(root, change.Path);
            var relative = Path.GetRelativePath(root, destination);
            if (File.Exists(destination))
            {
                var backup = Path.Combine(backupRoot, relative);
                Directory.CreateDirectory(Path.GetDirectoryName(backup)!);
                File.Copy(destination, backup, false);
            }
            Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
            await File.WriteAllTextAsync(destination, change.Content, cancellationToken);
            changed.Add(relative);
        }
        var log = Path.Combine(root, ".localaios", "CHANGES.md");
        await File.AppendAllTextAsync(log,
            $"\n## {DateTimeOffset.Now:O}\n\nİstek: {request}\n\nSonuç: {plan.Summary}\n\nDosyalar:\n{string.Join("\n", changed.Select(path => "- " + path))}\n",
            cancellationToken);
        return new(plan.Summary, changed.ToArray(), root);
    }

    internal static ProjectChangePlan ParsePlan(string raw)
    {
        var start = raw.IndexOf('{');
        var end = raw.LastIndexOf('}');
        if (start < 0 || end <= start) throw new InvalidOperationException("Proje değişikliği güvenli biçimde üretilemedi.");
        try
        {
            var plan = JsonSerializer.Deserialize<ProjectChangePlan>(raw[start..(end + 1)], AppSettings.JsonOptions);
            return plan is null ? throw new InvalidOperationException() : plan with
            {
                Summary = plan.Summary ?? "Değişiklik hazırlandı.",
                Files = plan.Files ?? []
            };
        }
        catch
        {
            throw new InvalidOperationException("Modelin proje değişikliği doğrulanamadı; hiçbir dosyaya dokunulmadı.");
        }
    }
}

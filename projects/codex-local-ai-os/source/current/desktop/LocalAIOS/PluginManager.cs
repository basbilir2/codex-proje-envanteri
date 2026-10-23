using System.IO.Compression;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace LocalAIOS;

internal sealed class PluginSource
{
    public string Topic { get; set; } = "";
    public string Url { get; set; } = "";
    public string LearningMethod { get; set; } = "";
}

internal sealed class PluginWorkflowStep
{
    public string Action { get; set; } = "";
    public string Instruction { get; set; } = "";
}

internal sealed class PluginQuality
{
    public int MinimumSources { get; set; }
    public int MinimumAnswerLength { get; set; }
    public bool RequireSourceUrls { get; set; }
    public string[] Checks { get; set; } = [];
}

internal sealed class PluginTool
{
    public string Id { get; set; } = "";
    public string Capability { get; set; } = "";
    public string EntryPoint { get; set; } = "";
    public bool AutoRun { get; set; }
    public int TimeoutSeconds { get; set; } = 60;
}

internal sealed class PluginManifest
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Version { get; set; } = "1.0.0";
    public string Description { get; set; } = "";
    public string[] Triggers { get; set; } = [];
    public string[] Capabilities { get; set; } = [];
    public string Instructions { get; set; } = "";
    public PluginSource[] Sources { get; set; } = [];
    public PluginWorkflowStep[] Workflow { get; set; } = [];
    public PluginQuality Quality { get; set; } = new();
    public PluginTool[] Tools { get; set; } = [];
    public string[] Permissions { get; set; } = [];
    public string CreatedFrom { get; set; } = "manual";
    public string LastValidatedAt { get; set; } = "";
    [JsonIgnore] public string InstallDirectory { get; set; } = "";
}

internal sealed class PluginManager
{
    public PluginManifest[] List()
    {
        AppPaths.EnsureDirectories();
        var files = Directory.EnumerateFiles(AppPaths.Plugins, "manifest.json", SearchOption.AllDirectories)
            .Concat(Directory.EnumerateFiles(AppPaths.Plugins, "*.json", SearchOption.TopDirectoryOnly));
        return files.Distinct(StringComparer.OrdinalIgnoreCase)
            .Select(Read).Where(plugin => plugin is not null).Cast<PluginManifest>().ToArray();
    }

    public PluginManifest[] Match(string request) => List().Select(plugin => new
        {
            Plugin = plugin,
            Score = (plugin.Triggers ?? []).Count(trigger => !string.IsNullOrWhiteSpace(trigger) &&
                request.Contains(trigger, StringComparison.OrdinalIgnoreCase))
        }).Where(item => item.Score > 0).OrderByDescending(item => item.Score).Take(3)
        .Select(item => item.Plugin).ToArray();

    public string ContextFor(string request) => BuildContext(Match(request));

    public static string BuildContext(IEnumerable<PluginManifest> plugins) => string.Join("\n\n", plugins.Select(plugin =>
        $"Yetenek: {plugin.Name} v{plugin.Version}\n" +
        $"Kurallar: {plugin.Instructions}\n" +
        $"İş akışı:\n{string.Join("\n", plugin.Workflow.Select((step, index) => $"{index + 1}. {step.Action}: {step.Instruction}"))}\n" +
        $"Bilgiye erişim yolları:\n{string.Join("\n", plugin.Sources.Select(source => $"- {source.Topic}: {source.Url} | {source.LearningMethod}"))}\n" +
        $"Kalite kontrolleri: {string.Join(", ", plugin.Quality.Checks)}"));

    public PluginManifest Install(string sourceFile)
    {
        AppPaths.EnsureDirectories();
        if (Path.GetExtension(sourceFile).Equals(".lai-plugin", StringComparison.OrdinalIgnoreCase))
            return InstallPackage(sourceFile);
        var plugin = Read(sourceFile) ?? throw new InvalidOperationException("Eklenti dosyası geçerli değil.");
        Normalize(plugin);
        if (plugin.Tools.Length > 0)
            throw new InvalidOperationException("Program içeren eklenti güvenli .lai-plugin paketi olarak yüklenmelidir.");
        return InstallManifest(plugin);
    }

    public PluginManifest InstallManifest(PluginManifest plugin)
    {
        Normalize(plugin);
        Validate(plugin);
        var safeId = SafeName(plugin.Id);
        var directory = Path.Combine(AppPaths.Plugins, safeId);
        Directory.CreateDirectory(directory);
        var manifestPath = Path.Combine(directory, "manifest.json");
        if (File.Exists(manifestPath))
        {
            var versions = Path.Combine(directory, "versions");
            Directory.CreateDirectory(versions);
            File.Copy(manifestPath, Path.Combine(versions, DateTime.UtcNow.ToString("yyyyMMdd-HHmmss") + ".json"), true);
        }
        plugin.LastValidatedAt = DateTimeOffset.UtcNow.ToString("O");
        File.WriteAllText(manifestPath, JsonSerializer.Serialize(plugin, AppSettings.JsonOptions));
        plugin.InstallDirectory = directory;
        return plugin;
    }

    public string[] ValidateAnswer(string answer, string[] sources, IEnumerable<PluginManifest> plugins)
    {
        var failures = new List<string>();
        foreach (var plugin in plugins)
        {
            if (plugin.Quality.MinimumAnswerLength > 0 && answer.Length < plugin.Quality.MinimumAnswerLength)
                failures.Add($"{plugin.Name}: cevap yeterince kapsamlı değil");
            if (plugin.Quality.MinimumSources > 0 && sources.Length < plugin.Quality.MinimumSources)
                failures.Add($"{plugin.Name}: en az {plugin.Quality.MinimumSources} kaynak gerekli");
            if (plugin.Quality.RequireSourceUrls && !answer.Contains("http", StringComparison.OrdinalIgnoreCase))
                failures.Add($"{plugin.Name}: kaynak bağlantıları cevapta yok");
        }
        return failures.ToArray();
    }

    private PluginManifest InstallPackage(string sourceFile)
    {
        var staging = Path.Combine(AppPaths.Root, "plugin-staging", Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(staging);
        try
        {
            using var archive = ZipFile.OpenRead(sourceFile);
            foreach (var entry in archive.Entries)
            {
                var destination = Path.GetFullPath(Path.Combine(staging, entry.FullName));
                if (!destination.StartsWith(staging + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidOperationException("Eklenti paketi güvenli değil.");
                if (string.IsNullOrEmpty(entry.Name)) { Directory.CreateDirectory(destination); continue; }
                Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
                entry.ExtractToFile(destination, true);
            }
            var manifestPath = Directory.EnumerateFiles(staging, "manifest.json", SearchOption.AllDirectories).FirstOrDefault()
                ?? throw new InvalidOperationException("Eklenti manifesti bulunamadı.");
            var plugin = Read(manifestPath) ?? throw new InvalidOperationException("Eklenti manifesti geçersiz.");
            var installed = InstallManifest(plugin);
            foreach (var file in Directory.EnumerateFiles(Path.GetDirectoryName(manifestPath)!, "*", SearchOption.AllDirectories))
            {
                if (Path.GetFileName(file).Equals("manifest.json", StringComparison.OrdinalIgnoreCase)) continue;
                var relative = Path.GetRelativePath(Path.GetDirectoryName(manifestPath)!, file);
                var destination = Path.Combine(installed.InstallDirectory, relative);
                Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
                File.Copy(file, destination, true);
            }
            return installed;
        }
        finally
        {
            if (Directory.Exists(staging)) Directory.Delete(staging, true);
        }
    }

    private static void Validate(PluginManifest plugin)
    {
        if (string.IsNullOrWhiteSpace(plugin.Id) || string.IsNullOrWhiteSpace(plugin.Name))
            throw new InvalidOperationException("Eklenti kimliği veya adı eksik.");
        if (plugin.Triggers.Length == 0 || string.IsNullOrWhiteSpace(plugin.Instructions))
            throw new InvalidOperationException("Eklentinin tetikleyicileri veya çalışma kuralları eksik.");
        foreach (var source in plugin.Sources)
            if (!Uri.TryCreate(source.Url, UriKind.Absolute, out var uri) || uri.Scheme is not ("http" or "https"))
                throw new InvalidOperationException($"Geçersiz bilgi kaynağı: {source.Url}");
        foreach (var tool in plugin.Tools)
            if (Path.IsPathRooted(tool.EntryPoint) || tool.EntryPoint.Contains("..") ||
                !Path.GetExtension(tool.EntryPoint).Equals(".exe", StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("Eklenti program yolu güvenli değil.");
    }

    private static void Normalize(PluginManifest plugin)
    {
        plugin.Triggers ??= [];
        plugin.Capabilities ??= [];
        plugin.Sources ??= [];
        plugin.Workflow ??= [];
        plugin.Quality ??= new();
        plugin.Quality.Checks ??= [];
        plugin.Tools ??= [];
        plugin.Permissions ??= [];
    }

    private static PluginManifest? Read(string file)
    {
        try
        {
            var plugin = JsonSerializer.Deserialize<PluginManifest>(File.ReadAllText(file), AppSettings.JsonOptions);
            if (plugin is not null) plugin.InstallDirectory = Path.GetDirectoryName(file)!;
            return plugin;
        }
        catch { return null; }
    }

    private static string SafeName(string value) =>
        string.Concat(value.Select(character => char.IsLetterOrDigit(character) || character is '-' or '_' ? character : '_'));
}

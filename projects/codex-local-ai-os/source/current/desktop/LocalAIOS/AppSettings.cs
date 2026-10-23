using System.Text.Json;

namespace LocalAIOS;

internal sealed class AppSettings
{
    public string UpdateFeedUrl { get; set; } = "";
    public Dictionary<string, string> InstalledPacks { get; set; } = [];
    public int ServerPort { get; set; } = 11435;
    public bool CloudEnabled { get; set; }
    public bool AllowProjectCloud { get; set; }
    public string SyncFolder { get; set; } = "";
    public string LastSyncUtc { get; set; } = "";
    public string ReasoningMode { get; set; } = "balanced";
    public string ActiveProjectPath { get; set; } = "";
    public string ActiveProjectSourcePath { get; set; } = "";

    public static AppSettings Load()
    {
        AppPaths.EnsureDirectories();
        try
        {
            return JsonSerializer.Deserialize<AppSettings>(File.ReadAllText(AppPaths.Settings)) ?? new();
        }
        catch
        {
            return new();
        }
    }

    public void Save()
    {
        AppPaths.EnsureDirectories();
        File.WriteAllText(AppPaths.Settings, JsonSerializer.Serialize(this, JsonOptions));
    }

    public static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        WriteIndented = true
    };
}

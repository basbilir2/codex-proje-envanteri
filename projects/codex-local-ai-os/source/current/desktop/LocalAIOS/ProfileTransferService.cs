using System.IO.Compression;
using System.Text.Json;

namespace LocalAIOS;

internal sealed class ProfileTransferService(AppSettings settings)
{
    private const string SyncFileName = "LocalAIOS-profile.laios";

    public async Task ExportAsync(string destination, CancellationToken cancellationToken)
    {
        AppPaths.EnsureDirectories();
        if (File.Exists(destination)) File.Delete(destination);
        await using var stream = File.Create(destination);
        using var archive = new ZipArchive(stream, ZipArchiveMode.Create);
        AddDirectory(archive, AppPaths.Knowledge, "knowledge");
        AddDirectory(archive, AppPaths.Plugins, "plugins");
        AddDirectory(archive, Path.Combine(AppPaths.Root, "memory"), "memory");
        var manifest = archive.CreateEntry("profile.json", CompressionLevel.Fastest);
        await using var output = manifest.Open();
        await JsonSerializer.SerializeAsync(output, new
        {
            schemaVersion = 1,
            createdAt = DateTimeOffset.UtcNow,
            settings.UpdateFeedUrl,
            settings.CloudEnabled,
            settings.AllowProjectCloud
        }, AppSettings.JsonOptions, cancellationToken);
    }

    public async Task ImportAsync(string source, CancellationToken cancellationToken)
    {
        AppPaths.EnsureDirectories();
        using var archive = ZipFile.OpenRead(source);
        foreach (var entry in archive.Entries)
        {
            if (string.IsNullOrEmpty(entry.Name) || entry.FullName.Equals("profile.json", StringComparison.OrdinalIgnoreCase)) continue;
            var normalized = entry.FullName.Replace('\\', '/');
            if (!normalized.StartsWith("knowledge/") && !normalized.StartsWith("plugins/") && !normalized.StartsWith("memory/")) continue;
            var destination = Path.GetFullPath(Path.Combine(AppPaths.Root, normalized.Replace('/', Path.DirectorySeparatorChar)));
            if (!destination.StartsWith(AppPaths.Root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase)) continue;
            Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
            await using var input = entry.Open();
            await using var output = File.Create(destination);
            await input.CopyToAsync(output, cancellationToken);
        }

        var profile = archive.GetEntry("profile.json");
        if (profile is not null)
        {
            await using var stream = profile.Open();
            using var document = await JsonDocument.ParseAsync(stream, cancellationToken: cancellationToken);
            if (document.RootElement.TryGetProperty("UpdateFeedUrl", out var feed)) settings.UpdateFeedUrl = feed.GetString() ?? settings.UpdateFeedUrl;
            if (document.RootElement.TryGetProperty("CloudEnabled", out var cloud)) settings.CloudEnabled = cloud.GetBoolean();
            if (document.RootElement.TryGetProperty("AllowProjectCloud", out var permission)) settings.AllowProjectCloud = permission.GetBoolean();
            settings.Save();
        }
    }

    public async Task PullAsync(CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(settings.SyncFolder)) return;
        var file = Path.Combine(settings.SyncFolder, SyncFileName);
        if (!File.Exists(file)) return;
        var remoteTime = File.GetLastWriteTimeUtc(file);
        if (DateTimeOffset.TryParse(settings.LastSyncUtc, out var last) && remoteTime <= last.UtcDateTime) return;
        await ImportAsync(file, cancellationToken);
        settings.LastSyncUtc = remoteTime.ToString("O");
        settings.Save();
    }

    public async Task PushAsync(CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(settings.SyncFolder)) return;
        Directory.CreateDirectory(settings.SyncFolder);
        var file = Path.Combine(settings.SyncFolder, SyncFileName);
        await ExportAsync(file, cancellationToken);
        settings.LastSyncUtc = File.GetLastWriteTimeUtc(file).ToString("O");
        settings.Save();
    }

    private static void AddDirectory(ZipArchive archive, string source, string prefix)
    {
        if (!Directory.Exists(source)) return;
        foreach (var file in Directory.EnumerateFiles(source, "*", SearchOption.AllDirectories))
        {
            var relative = Path.GetRelativePath(source, file).Replace('\\', '/');
            archive.CreateEntryFromFile(file, $"{prefix}/{relative}", CompressionLevel.Fastest);
        }
    }
}

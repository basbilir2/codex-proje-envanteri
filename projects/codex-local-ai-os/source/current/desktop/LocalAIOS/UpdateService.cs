using System.Security.Cryptography;
using System.Text.Json;

namespace LocalAIOS;

internal sealed record PackUpdate(string Id, string Version, string Title, string Summary, string Url, string? Sha256, string? Kind);
internal sealed record UpdateFeed(int SchemaVersion, string? AppVersion, string? Title, string? Notes, string? AppDownloadUrl, string? AppSha256, PackUpdate[] KnowledgePacks);

internal sealed class UpdateService(AppSettings settings)
{
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromMinutes(5) };

    public async Task<(UpdateFeed Feed, PackUpdate[] NewPacks)?> CheckAsync(CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(settings.UpdateFeedUrl)) return null;
        var json = await _http.GetStringAsync(settings.UpdateFeedUrl, cancellationToken);
        var feed = JsonSerializer.Deserialize<UpdateFeed>(json, AppSettings.JsonOptions)
            ?? throw new InvalidOperationException("Güncelleme bilgisi okunamadı.");
        var newPacks = (feed.KnowledgePacks ?? [])
            .Where(pack => !settings.InstalledPacks.TryGetValue(pack.Id, out var version) || version != pack.Version)
            .ToArray();
        return (feed, newPacks);
    }

    public async Task InstallPacksAsync(IEnumerable<PackUpdate> packs, CancellationToken cancellationToken)
    {
        AppPaths.EnsureDirectories();
        foreach (var pack in packs)
        {
            var bytes = await _http.GetByteArrayAsync(pack.Url, cancellationToken);
            if (pack.Kind?.Equals("capability", StringComparison.OrdinalIgnoreCase) == true && string.IsNullOrWhiteSpace(pack.Sha256))
                throw new InvalidOperationException($"{pack.Title} yetenek paketinin güvenlik özeti eksik.");
            if (!string.IsNullOrWhiteSpace(pack.Sha256))
            {
                var actual = Convert.ToHexString(SHA256.HashData(bytes));
                if (!actual.Equals(pack.Sha256, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidOperationException($"{pack.Title} paketinin güvenlik doğrulaması başarısız.");
            }
            if (pack.Kind?.Equals("capability", StringComparison.OrdinalIgnoreCase) == true)
            {
                var updateDirectory = Path.Combine(AppPaths.Root, "updates");
                Directory.CreateDirectory(updateDirectory);
                var extension = pack.Url.Contains(".lai-plugin", StringComparison.OrdinalIgnoreCase) ? ".lai-plugin" : ".json";
                var temporary = Path.Combine(updateDirectory, $"capability-{SafeName(pack.Id)}{extension}");
                await File.WriteAllBytesAsync(temporary, bytes, cancellationToken);
                try { new PluginManager().Install(temporary); }
                finally { if (File.Exists(temporary)) File.Delete(temporary); }
            }
            else
            {
                var destination = Path.Combine(AppPaths.Knowledge, $"pack-{SafeName(pack.Id)}.json");
                await File.WriteAllBytesAsync(destination, bytes, cancellationToken);
            }
            settings.InstalledPacks[pack.Id] = pack.Version;
        }
        settings.Save();
    }

    public static bool HasAppUpdate(UpdateFeed feed)
    {
        var current = typeof(UpdateService).Assembly.GetName().Version ?? new Version(0, 0);
        return Version.TryParse(feed.AppVersion, out var offered) && offered > current &&
            !string.IsNullOrWhiteSpace(feed.AppDownloadUrl);
    }

    public async Task<string> DownloadAppUpdateAsync(UpdateFeed feed, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(feed.AppDownloadUrl) || string.IsNullOrWhiteSpace(feed.AppSha256))
            throw new InvalidOperationException("Uygulama güncellemesinin güvenlik doğrulaması eksik.");
        var directory = Path.Combine(AppPaths.Root, "updates");
        Directory.CreateDirectory(directory);
        var destination = Path.Combine(directory, "LocalAIOS-update.exe");
        var bytes = await _http.GetByteArrayAsync(feed.AppDownloadUrl, cancellationToken);
        var actual = Convert.ToHexString(SHA256.HashData(bytes));
        if (!actual.Equals(feed.AppSha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Uygulama güncellemesinin güvenlik doğrulaması başarısız.");
        await File.WriteAllBytesAsync(destination, bytes, cancellationToken);
        return destination;
    }

    private static string SafeName(string value) =>
        string.Concat(value.Select(character => char.IsLetterOrDigit(character) || character is '-' or '_' ? character : '_'));
}

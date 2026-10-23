using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace LocalAIOS;

internal sealed record KnowledgeDocument(
    string Id,
    string Title,
    string SourceUrl,
    string AddedAt,
    string LastCheckedAt,
    string SourceHash,
    string Summary,
    string[] Keywords,
    string[] CachedChunks,
    string? CacheQuery,
    string? CacheExpiresAt);

internal sealed record KnowledgeContext(string Content, string[] Sources);

internal sealed class KnowledgeStore
{
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromMinutes(3) };
    private static readonly Regex Tags = new("<[^>]+>", RegexOptions.Compiled);
    private static readonly Regex Scripts = new("<(script|style)[^>]*>.*?</\\1>", RegexOptions.Compiled | RegexOptions.IgnoreCase | RegexOptions.Singleline);
    private static readonly Regex Spaces = new("\\s+", RegexOptions.Compiled);
    private static readonly Regex Words = new("[\\p{L}\\p{N}]{3,}", RegexOptions.Compiled);
    private static readonly HashSet<string> StopWords = new(StringComparer.OrdinalIgnoreCase)
        { "bir", "ile", "için", "olan", "olarak", "the", "and", "this", "that", "from", "are", "was", "www", "http", "https" };

    public async Task<KnowledgeDocument> AddUrlAsync(string url, CancellationToken cancellationToken)
    {
        var (uri, title, text) = await FetchAsync(url, cancellationToken);
        var now = DateTimeOffset.UtcNow;
        var document = new KnowledgeDocument(
            Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(url)))[..16],
            title,
            uri.ToString(),
            now.ToString("O"),
            now.ToString("O"),
            Hash(text),
            text[..Math.Min(1200, text.Length)],
            Keywords(text),
            [],
            null,
            null);
        await SaveAsync(document, cancellationToken);
        return document;
    }

    public async Task PruneAsync(CancellationToken cancellationToken)
    {
        AppPaths.EnsureDirectories();
        foreach (var file in Directory.EnumerateFiles(AppPaths.Knowledge, "*.json"))
        {
            try
            {
                var document = JsonSerializer.Deserialize<KnowledgeDocument>(
                    await File.ReadAllTextAsync(file, cancellationToken), AppSettings.JsonOptions);
                if (document is null || document.CachedChunks.Length == 0 ||
                    !DateTimeOffset.TryParse(document.CacheExpiresAt, out var expiry) || expiry > DateTimeOffset.UtcNow) continue;
                document = document with { CachedChunks = [], CacheQuery = null, CacheExpiresAt = null };
                await File.WriteAllTextAsync(file, JsonSerializer.Serialize(document, AppSettings.JsonOptions), cancellationToken);
            }
            catch { }
        }
    }

    public async Task<KnowledgeContext> SearchAsync(string query, CancellationToken cancellationToken)
    {
        AppPaths.EnsureDirectories();
        var terms = Tokenize(query).Distinct(StringComparer.OrdinalIgnoreCase).ToArray();
        if (terms.Length == 0) return new("", []);
        var candidates = new List<(int Score, string File, KnowledgeDocument Document)>();
        foreach (var file in Directory.EnumerateFiles(AppPaths.Knowledge, "*.json"))
        {
            try
            {
                var json = await File.ReadAllTextAsync(file, cancellationToken);
                if (JsonSerializer.Deserialize<KnowledgeDocument>(json, AppSettings.JsonOptions) is not { } document) continue;
                var index = $"{document.Title} {document.Summary} {string.Join(' ', document.Keywords)}".ToLowerInvariant();
                var score = terms.Count(term => index.Contains(term, StringComparison.OrdinalIgnoreCase));
                if (score > 0) candidates.Add((score, file, document));
            }
            catch { }
        }

        var selected = new List<string>();
        var sources = new List<string>();
        foreach (var candidate in candidates.OrderByDescending(item => item.Score).Take(3))
        {
            var document = candidate.Document;
            var queryKey = string.Join('|', terms.Order(StringComparer.OrdinalIgnoreCase));
            var cacheValid = document.CacheQuery == queryKey &&
                DateTimeOffset.TryParse(document.CacheExpiresAt, out var expiry) && expiry > DateTimeOffset.UtcNow;
            if (!cacheValid)
            {
                try
                {
                    var (_, title, text) = await FetchAsync(document.SourceUrl, cancellationToken);
                    var chunks = Chunk(text, 1800, 150)
                        .Select(chunk => (Score: terms.Count(term => chunk.Contains(term, StringComparison.OrdinalIgnoreCase)), Text: chunk))
                        .OrderByDescending(item => item.Score)
                        .Where(item => item.Score > 0)
                        .Take(3)
                        .Select(item => item.Text)
                        .ToArray();
                    document = document with
                    {
                        Title = title,
                        LastCheckedAt = DateTimeOffset.UtcNow.ToString("O"),
                        SourceHash = Hash(text),
                        Summary = text[..Math.Min(1200, text.Length)],
                        Keywords = Keywords(text),
                        CachedChunks = chunks,
                        CacheQuery = queryKey,
                        CacheExpiresAt = DateTimeOffset.UtcNow.AddHours(24).ToString("O")
                    };
                    await File.WriteAllTextAsync(candidate.File, JsonSerializer.Serialize(document, AppSettings.JsonOptions), cancellationToken);
                }
                catch
                {
                    // Kaynak geçici olarak erişilemezse kısa yerel özet kullanılmaya devam eder.
                }
            }
            var content = document.CachedChunks.Length > 0 ? string.Join("\n", document.CachedChunks) : document.Summary;
            selected.Add($"Kaynak: {document.Title} ({document.SourceUrl})\n{content}");
            sources.Add(document.SourceUrl);
        }
        return new(string.Join("\n\n", selected), sources.Distinct().ToArray());
    }

    private async Task<(Uri Uri, string Title, string Text)> FetchAsync(string url, CancellationToken cancellationToken)
    {
        if (!Uri.TryCreate(url, UriKind.Absolute, out var uri) || (uri.Scheme != "https" && uri.Scheme != "http"))
            throw new ArgumentException("Geçerli bir web bağlantısı girin.");
        var html = await _http.GetStringAsync(uri, cancellationToken);
        var titleMatch = Regex.Match(html, "<title[^>]*>(.*?)</title>", RegexOptions.IgnoreCase | RegexOptions.Singleline);
        var title = titleMatch.Success ? Clean(titleMatch.Groups[1].Value) : uri.Host;
        var text = Clean(Scripts.Replace(html, " "));
        if (text.Length < 100) throw new InvalidOperationException("Bağlantıdan yeterli metin alınamadı.");
        if (text.Length > 2_000_000) text = text[..2_000_000];
        return (uri, title, text);
    }

    private static async Task SaveAsync(KnowledgeDocument document, CancellationToken cancellationToken)
    {
        AppPaths.EnsureDirectories();
        var file = Path.Combine(AppPaths.Knowledge, $"personal-{document.Id}.json");
        await File.WriteAllTextAsync(file, JsonSerializer.Serialize(document, AppSettings.JsonOptions), cancellationToken);
    }

    private static string[] Keywords(string text) => Tokenize(text)
        .GroupBy(word => word, StringComparer.OrdinalIgnoreCase)
        .OrderByDescending(group => group.Count())
        .Take(50)
        .Select(group => group.Key)
        .ToArray();
    private static IEnumerable<string> Tokenize(string text) => Words.Matches(text.ToLowerInvariant())
        .Select(match => match.Value).Where(word => !StopWords.Contains(word));
    private static string Clean(string html) => Spaces.Replace(WebUtility.HtmlDecode(Tags.Replace(html, " ")), " ").Trim();
    private static string Hash(string text) => Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(text)));
    private static IEnumerable<string> Chunk(string text, int size, int overlap)
    {
        for (var start = 0; start < text.Length; start += size - overlap)
            yield return text.Substring(start, Math.Min(size, text.Length - start));
    }
}

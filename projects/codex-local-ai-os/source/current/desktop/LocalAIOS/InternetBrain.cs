using System.Net;
using System.Text.RegularExpressions;
using System.Xml.Linq;

namespace LocalAIOS;

internal sealed record InternetResearch(string Context, string[] Sources);

internal sealed class InternetBrain
{
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromSeconds(25) };
    private static readonly Regex Tags = new("<[^>]+>", RegexOptions.Compiled);
    private static readonly Regex Scripts = new("<(script|style|nav|footer)[^>]*>.*?</\\1>", RegexOptions.Compiled | RegexOptions.IgnoreCase | RegexOptions.Singleline);
    private static readonly Regex Spaces = new("\\s+", RegexOptions.Compiled);
    private static readonly Regex Words = new("[\\p{L}\\p{N}]{3,}", RegexOptions.Compiled);

    public InternetBrain() => _http.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0 LocalAIOS/0.3");

    public static bool ShouldResearch(string request, bool hasLocalContext)
    {
        var text = request.ToLowerInvariant();
        var casual = new[] { "merhaba", "nasılsın", "teşekkür", "sohbet", "hikaye yaz", "şiir yaz" };
        if (casual.Any(text.Contains)) return false;
        var fresh = new[] { "güncel", "bugün", "son durum", "haber", "fiyat", "sürüm", "yeni çıkan", "mevcut" };
        var knowledge = new[] { "nedir", "nasıl", "neden", "nerede", "kimdir", "araştır", "karşılaştır", "öğren" };
        return fresh.Any(text.Contains) || (!hasLocalContext && knowledge.Any(text.Contains));
    }

    public async Task<InternetResearch> ResearchAsync(string request, CancellationToken cancellationToken)
    {
        var results = await SearchAsync(request, cancellationToken);
        if (results.Count == 0) return new("", []);
        var terms = Words.Matches(request.ToLowerInvariant()).Select(match => match.Value).Distinct().ToArray();
        var collected = (await Task.WhenAll(results.Take(4)
            .Select(result => CollectResultAsync(result, terms, cancellationToken))))
            .Where(item => item is not null).Select(item => item!.Value).ToArray();
        return new(string.Join("\n\n", collected.Select(item => item.Context)),
            collected.Select(item => item.Url).Distinct().ToArray());
    }

    public async Task<InternetResearch> ResearchAsync(
        string request, IEnumerable<string> preferredSources, CancellationToken cancellationToken)
    {
        var regularTask = SafeResearchAsync(request, cancellationToken);
        var terms = Words.Matches(request.ToLowerInvariant()).Select(match => match.Value).Distinct().ToArray();
        var preferred = (await Task.WhenAll(preferredSources.Where(value => !string.IsNullOrWhiteSpace(value))
                .Distinct(StringComparer.OrdinalIgnoreCase).Take(4)
                .Select(url => CollectPreferredAsync(url, terms, cancellationToken))))
            .Where(item => item is not null).Select(item => item!.Value).ToArray();
        var regular = await regularTask;
        var contexts = preferred.Select(item => item.Context).ToList();
        var sources = preferred.Select(item => item.Url).ToList();
        if (!string.IsNullOrWhiteSpace(regular.Context)) contexts.Add(regular.Context);
        sources.AddRange(regular.Sources);
        return new(string.Join("\n\n", contexts), sources.Distinct(StringComparer.OrdinalIgnoreCase).ToArray());
    }

    private async Task<InternetResearch> SafeResearchAsync(string request, CancellationToken cancellationToken)
    {
        try { return await ResearchAsync(request, cancellationToken); }
        catch { return new("", []); }
    }

    private async Task<(string Context, string Url)?> CollectResultAsync(
        SearchResult result, string[] terms, CancellationToken cancellationToken)
    {
        try
        {
            var text = await FetchTextAsync(result.Url, cancellationToken);
            var chunks = Chunk(text, 1800, 150)
                .Select(chunk => (Score: terms.Count(term => chunk.Contains(term, StringComparison.OrdinalIgnoreCase)), Text: chunk))
                .OrderByDescending(item => item.Score).Take(2).Select(item => item.Text).ToArray();
            var useful = chunks.Length > 0 ? string.Join("\n", chunks) : result.Description;
            return ($"Kaynak: {result.Title}\nURL: {result.Url}\n{useful}", result.Url);
        }
        catch
        {
            return string.IsNullOrWhiteSpace(result.Description)
                ? null : ($"Kaynak: {result.Title}\nURL: {result.Url}\n{result.Description}", result.Url);
        }
    }

    private async Task<(string Context, string Url)?> CollectPreferredAsync(
        string url, string[] terms, CancellationToken cancellationToken)
    {
        try
        {
            var content = await FetchTextAsync(url, cancellationToken);
            var best = Chunk(content, 1800, 150)
                .Select(chunk => (Score: terms.Count(term => chunk.Contains(term, StringComparison.OrdinalIgnoreCase)), Text: chunk))
                .OrderByDescending(item => item.Score).Take(2).Select(item => item.Text);
            return ($"Kayıtlı öğrenme kaynağı\nURL: {url}\n{string.Join("\n", best)}", url);
        }
        catch { return null; }
    }

    private async Task<List<SearchResult>> SearchAsync(string query, CancellationToken cancellationToken)
    {
        var url = "https://www.bing.com/search?format=rss&q=" + Uri.EscapeDataString(query);
        var xml = await _http.GetStringAsync(url, cancellationToken);
        var document = XDocument.Parse(xml);
        return document.Descendants("item").Select(item => new SearchResult(
                WebUtility.HtmlDecode(item.Element("title")?.Value ?? "Kaynak"),
                item.Element("link")?.Value ?? "",
                Clean(item.Element("description")?.Value ?? "")))
            .Where(item => Uri.TryCreate(item.Url, UriKind.Absolute, out var uri) && uri.Scheme is "http" or "https")
            .Take(8).ToList();
    }

    private async Task<string> FetchTextAsync(string url, CancellationToken cancellationToken)
    {
        using var response = await _http.GetAsync(url, HttpCompletionOption.ResponseHeadersRead, cancellationToken);
        response.EnsureSuccessStatusCode();
        var mediaType = response.Content.Headers.ContentType?.MediaType ?? "";
        if (!mediaType.Contains("html", StringComparison.OrdinalIgnoreCase) && !mediaType.Contains("text", StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Metin olmayan kaynak.");
        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        using var reader = new StreamReader(stream);
        var buffer = new char[1_000_000];
        var read = await reader.ReadBlockAsync(buffer.AsMemory(), cancellationToken);
        return Clean(Scripts.Replace(new string(buffer, 0, read), " "));
    }

    private static string Clean(string value) => Spaces.Replace(WebUtility.HtmlDecode(Tags.Replace(value, " ")), " ").Trim();
    private static IEnumerable<string> Chunk(string text, int size, int overlap)
    {
        for (var start = 0; start < text.Length; start += size - overlap)
            yield return text.Substring(start, Math.Min(size, text.Length - start));
    }

    private sealed record SearchResult(string Title, string Url, string Description);
}

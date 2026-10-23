using System.Text.Json;
using System.Text.RegularExpressions;

namespace LocalAIOS;

internal sealed class CapabilityDevelopmentEngine(PluginManager plugins, InternetBrain internet)
{
    public async Task<PluginManifest> AcquireAsync(
        string need, LocalModelClient model, CancellationToken cancellationToken, IEnumerable<string>? preferredSources = null)
    {
        var cleanNeed = Regex.Replace(need, @"https?://\S+", " ").Trim();
        var research = await internet.ResearchAsync(cleanNeed + " official documentation best practices",
            preferredSources ?? [], cancellationToken);
        if (research.Sources.Length < 2)
            throw new InvalidOperationException("Bu yetenek için iki güvenilir kaynak yolu bulunamadı; eksik tarif kaydedilmedi.");
        var prompt = $$"""
            User capability need:
            {{need}}

            Current trustworthy source candidates:
            {{research.Context[..Math.Min(research.Context.Length, 4000)]}}

            Design a reusable capability recipe. The value is not memorizing content; it is knowing how to reacquire, apply, and verify it.
            Return only one JSON object matching this shape:
            {
              "id":"lower_snake_case",
              "name":"short Turkish name",
              "version":"1.0.0",
              "description":"purpose",
              "triggers":["at least three phrases"],
              "capabilities":["domain.action"],
              "instructions":"clear operating rules",
              "sources":[{"topic":"...","url":"https://...","learningMethod":"how and when to retrieve/verify"}],
              "workflow":[{"action":"detect_need","instruction":"..."},{"action":"retrieve","instruction":"..."},{"action":"verify","instruction":"..."},{"action":"apply","instruction":"..."}],
              "quality":{"minimumSources":2,"minimumAnswerLength":200,"requireSourceUrls":true,"checks":["freshness","authority","contradictions","application result"]},
              "tools":[],
              "permissions":["internet_read"],
              "createdFrom":"chat_acquisition"
            }
            """;
        var output = await model.GenerateAsync(
            "You design safe, portable AI capability recipes. Output strict valid JSON only.",
            prompt, cancellationToken, 900, true);
        var plugin = Parse(output) ?? CreateFallback(need, research.Sources);
        Normalize(plugin, need, research.Sources);
        return plugins.InstallManifest(plugin);
    }

    private static PluginManifest? Parse(string output)
    {
        var first = output.IndexOf('{');
        var last = output.LastIndexOf('}');
        if (first < 0 || last <= first) return null;
        try { return JsonSerializer.Deserialize<PluginManifest>(output[first..(last + 1)], AppSettings.JsonOptions); }
        catch { return null; }
    }

    private static void Normalize(PluginManifest plugin, string need, string[] sources)
    {
        plugin.Triggers ??= [];
        plugin.Capabilities ??= [];
        plugin.Sources ??= [];
        plugin.Workflow ??= [];
        plugin.Quality ??= new();
        plugin.Quality.Checks ??= [];
        plugin.Tools ??= [];
        plugin.Permissions ??= [];
        plugin.Id = Slug(string.IsNullOrWhiteSpace(plugin.Id) ? need : plugin.Id);
        if (string.IsNullOrWhiteSpace(plugin.Name)) plugin.Name = need.Length > 50 ? need[..50] : need;
        if (string.IsNullOrWhiteSpace(plugin.Version)) plugin.Version = "1.0.0";
        if (plugin.Triggers.Length < 3)
            plugin.Triggers = Regex.Matches(need.ToLowerInvariant(), "[\\p{L}\\p{N}]{4,}").Select(match => match.Value).Distinct().Take(6).ToArray();
        if (plugin.Triggers.Length == 0) plugin.Triggers = [plugin.Name];
        if (string.IsNullOrWhiteSpace(plugin.Instructions))
            plugin.Instructions = "İhtiyacı belirle, güncel güvenilir kaynakları bul, karşılaştır, uygula ve sonucu doğrula.";
        var observedSources = sources.ToHashSet(StringComparer.OrdinalIgnoreCase);
        plugin.Sources = plugin.Sources.Where(source => observedSources.Contains(source.Url)).ToArray();
        var existingSources = plugin.Sources.Select(source => source.Url).ToHashSet(StringComparer.OrdinalIgnoreCase);
        plugin.Sources = plugin.Sources.Concat(sources.Where(url => !existingSources.Contains(url)).Take(6 - plugin.Sources.Length)
            .Select(url => new PluginSource
            {
                Topic = need,
                Url = url,
                LearningMethod = "Gerektiğinde güncel içeriği al, ilgili kısmı çıkar ve başka kaynakla doğrula."
            })).Take(6).ToArray();
        if (plugin.Workflow.Length == 0)
            plugin.Workflow =
            [
                new() { Action = "detect_need", Instruction = "Eksik bilgi/yeteneği kesin tanımla." },
                new() { Action = "retrieve", Instruction = "Kayıtlı kaynak yollarından güncel bilgiyi edin." },
                new() { Action = "verify", Instruction = "En az iki güvenilir kaynağı karşılaştır." },
                new() { Action = "apply", Instruction = "Bilgiyi göreve uygula ve sonucu kontrol et." }
            ];
        plugin.CreatedFrom = "chat_acquisition";
        plugin.Tools = [];
        plugin.Permissions = ["internet_read"];
    }

    private static PluginManifest CreateFallback(string need, string[] sources) => new()
    {
        Id = Slug(need),
        Name = need.Length > 50 ? need[..50] : need,
        Description = "Sohbet sırasında edinilen yetenek",
        Triggers = Regex.Matches(need.ToLowerInvariant(), "[\\p{L}\\p{N}]{4,}").Select(match => match.Value).Distinct().Take(6).ToArray(),
        Capabilities = ["dynamic.research_apply"],
        Instructions = "İhtiyacı belirle, güncel güvenilir kaynakları bul, karşılaştır, uygula ve sonucu doğrula.",
        Sources = sources.Take(6).Select(url => new PluginSource { Topic = need, Url = url, LearningMethod = "Güncel içeriği al, ilgili kısmı çıkar ve çapraz doğrula." }).ToArray(),
        Quality = new() { MinimumSources = 2, MinimumAnswerLength = 200, RequireSourceUrls = true, Checks = ["freshness", "authority", "contradictions", "result"] }
    };

    private static string Slug(string value)
    {
        var slug = Regex.Replace(value.ToLowerInvariant(), "[^a-z0-9çğıöşü]+", "_").Trim('_');
        return string.IsNullOrWhiteSpace(slug) ? "dynamic_capability" : slug[..Math.Min(slug.Length, 60)];
    }
}

using System.Text.Json;

namespace LocalAIOS;

internal sealed record CapabilityGap(bool Missing, string Need, string Reason, string[] SelectedIds);

internal static class CapabilityGapDetector
{
    private static readonly string[] ExplicitSignals =
    [
        "yetenek edin", "yetenek ekle", "bu yeteneği öğren", "kendini geliştir",
        "eklenti oluştur", "bu konuda geliş", "bu konuda uzmanlaş"
    ];

    private static readonly string[] SpecialistSignals =
    [
        "uzman", "profesyonel", "strateji", "denetle", "optimize", "analiz et",
        "seo", "muhasebe", "mevzuat", "kampanya", "pazar araştır", "teşhis",
        "hazırla", "oluştur", "yap", "planla", "incele", "araştır", "geliştir"
    ];

    public static async Task<CapabilityGap> AnalyzeAsync(
        string request, PluginManager plugins, LocalModelClient model, CancellationToken cancellationToken)
    {
        var literal = plugins.Match(request);
        if (literal.Length > 0) return new(false, "", "Kayıtlı yetenek bulundu.", literal.Select(plugin => plugin.Id).ToArray());
        if (ExplicitSignals.Any(signal => request.Contains(signal, StringComparison.OrdinalIgnoreCase)))
            return new(true, request, "Kullanıcı yeni yetenek istedi.", []);
        if (!SpecialistSignals.Any(signal => request.Contains(signal, StringComparison.OrdinalIgnoreCase)))
            return new(false, "", "Genel yeteneklerle yapılabilir.", []);

        var catalogue = string.Join("\n", plugins.List().Take(20).Select(plugin =>
            $"- id={plugin.Id}; name={plugin.Name}; purpose={plugin.Description}; abilities={string.Join(',', plugin.Capabilities)}; triggers={string.Join(',', plugin.Triggers)}"));

        var output = await model.GenerateAsync("""
            You detect reusable capability gaps for a personal AI. Built-in abilities are general chat,
            current web research, sourced memory, image generation and single-file mini applications.
            Select semantically relevant installed capability IDs even when wording differs. A new capability
            is justified only when the request needs repeatable specialist methods, domain sources, tools or
            validation beyond the built-ins and no installed capability covers it. Return strict JSON only:
            {"missing":true|false,"need":"precise reusable capability","reason":"short","selectedIds":["id"]}
            """, $"Request:\n{request}\n\nInstalled capability catalogue:\n{catalogue}", cancellationToken, 300, true);
        try
        {
            var first = output.IndexOf('{');
            var last = output.LastIndexOf('}');
            if (first >= 0 && last > first)
                return JsonSerializer.Deserialize<CapabilityGap>(output[first..(last + 1)], AppSettings.JsonOptions)
                    ?? new(false, "", "Karar üretilemedi.", []);
        }
        catch { }
        return new(false, "", "Karar güvenle doğrulanamadı.", []);
    }
}

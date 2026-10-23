namespace LocalAIOS;

internal static class ReasoningRouter
{
    public static bool ShouldThinkDeeply(string request, string mode)
    {
        if (mode.Equals("fast", StringComparison.OrdinalIgnoreCase)) return false;
        if (mode.Equals("powerful", StringComparison.OrdinalIgnoreCase)) return true;
        var signals = new[]
        {
            "derin düşün", "çok dikkatli", "adım adım", "karmaşık", "mimari",
            "strateji", "kanıtla", "hata ayıkla", "risk analizi", "karşılaştır"
        };
        return request.Length > 600 || signals.Count(signal =>
            request.Contains(signal, StringComparison.OrdinalIgnoreCase)) >= 2;
    }

    public static string Label(string mode) => mode.ToLowerInvariant() switch
    {
        "fast" => "Hızlı",
        "powerful" => "En güçlü",
        _ => "Dengeli"
    };
}

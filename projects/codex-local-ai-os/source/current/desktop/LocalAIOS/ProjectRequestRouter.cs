namespace LocalAIOS;

internal static class ProjectRequestRouter
{
    private static readonly string[] ContinuationSignals =
    [
        "kaldığımız yerden", "kaldigimiz yerden", "eski klasöre dokunmadan", "eski klasore dokunmadan",
        "yeni sürüm klasörü", "yeni surum klasoru", "v2 klasörü", "v2 klasoru", "projeyi kopyala"
    ];

    private static readonly string[] ProjectSignals =
    [
        "proje", "uygulama", "kod", "dosya", "özellik", "ozellik", "hata", "buton", "sayfa", "ekran",
        "general", "api", "veritaban", "arayüz", "arayuz"
    ];

    private static readonly string[] ChangeSignals =
    [
        "ekle", "düzelt", "duzelt", "değiştir", "degistir", "geliştir", "gelistir", "oluştur", "olustur",
        "uygula", "yenile", "kaldığımız yerden devam", "kaldigimiz yerden devam", "kodla", "tamamla"
    ];

    public static bool IsContinuationRequest(string text) => ContinuationSignals.Any(text.ContainsIgnoreCase);

    public static bool IsProjectRelated(string text) => ProjectSignals.Any(text.ContainsIgnoreCase);

    public static bool IsChangeRequest(string text) => IsProjectRelated(text) && ChangeSignals.Any(text.ContainsIgnoreCase);

    private static bool ContainsIgnoreCase(this string value, string signal) =>
        value.Contains(signal, StringComparison.OrdinalIgnoreCase);
}

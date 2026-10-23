namespace BTakip;

internal static class CloudConfiguration
{
    // BTakip'in kendi Google/Firebase projesine ait genel istemci ayarlarıdır.
    // Kullanıcı kurulum sırasında bu değerleri görmez veya girmek zorunda kalmaz.
    public const string FirebaseProjectId = "btakip-trendybrander";
    public const string FirebaseApiKey = "PRIVATE_VALUE_001";
    public const string GoogleClientId = "756472361241-37ueh657dseh80821a54co36o7ag6kv8.apps.googleusercontent.com";
    public const string GoogleClientSecret = "PRIVATE_VALUE_002";

    public static bool IsConfigured =>
        !FirebaseProjectId.StartsWith("BTAKIP_", StringComparison.Ordinal) &&
        !FirebaseApiKey.StartsWith("BTAKIP_", StringComparison.Ordinal) &&
        GoogleClientId.EndsWith(".apps.googleusercontent.com", StringComparison.OrdinalIgnoreCase) &&
        !GoogleClientSecret.StartsWith("BTAKIP_", StringComparison.Ordinal);
}

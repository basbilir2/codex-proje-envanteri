using System.Reflection;
using System.Text.Json;

namespace THesap;

public static class SeedData
{
    // Kurulum anındaki canlı BTakip katalog kopyası; çalışırken BTakip'e erişmez.
    public static (List<PriceGroup> Groups, List<PriceItem> Items) Create()
    {
        using var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("THesap.CatalogSnapshot.json")
            ?? throw new InvalidOperationException("THesap katalog kopyası bulunamadı.");
        var catalog = JsonSerializer.Deserialize<CatalogSnapshot>(stream, new JsonSerializerOptions { PropertyNameCaseInsensitive = true })
            ?? throw new InvalidOperationException("THesap katalog kopyası okunamadı.");
        return (catalog.PriceGroups, catalog.PriceItems);
    }
    private sealed class CatalogSnapshot { public List<PriceGroup> PriceGroups { get; set; } = []; public List<PriceItem> PriceItems { get; set; } = []; }
}

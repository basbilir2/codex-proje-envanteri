using System.Text.Json;

namespace THesap;

public static class CatalogStore
{
    private static readonly JsonSerializerOptions Options = new() { WriteIndented = true, PropertyNameCaseInsensitive = true };
    public static string DataPath => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "THesap", "thesap-katalog.json");

    public static (List<PriceGroup> Groups, List<PriceItem> Items) Load()
    {
        try
        {
            if (File.Exists(DataPath))
            {
                var data = JsonSerializer.Deserialize<CatalogData>(File.ReadAllText(DataPath), Options);
                if (data is { Groups.Count: > 0, Items.Count: > 0 }) return (data.Groups, data.Items);
            }
        }
        catch { }
        var seed = SeedData.Create();
        Save(seed.Groups, seed.Items);
        return seed;
    }

    public static void Save(List<PriceGroup> groups, List<PriceItem> items)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(DataPath)!);
        var temporary = DataPath + ".new";
        File.WriteAllText(temporary, JsonSerializer.Serialize(new CatalogData { Groups = groups, Items = items }, Options));
        File.Move(temporary, DataPath, true);
    }

    public sealed class CatalogData
    {
        public List<PriceGroup> Groups { get; set; } = [];
        public List<PriceItem> Items { get; set; } = [];
    }
}

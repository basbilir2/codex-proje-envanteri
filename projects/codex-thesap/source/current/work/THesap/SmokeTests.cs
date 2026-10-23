namespace THesap;

public static class SmokeTests
{
    public static int Run()
    {
        try
        {
            var (groups, items) = SeedData.Create(); Assert(items.Count == 34, "BTakip canlı başlangıç kataloğu");
            using var managementScreen = new PriceManagementForm(groups, items, () => { });
            Assert(managementScreen.Controls.Count > 0, "fiyat tanımları ekranı açılışı");
            var uv = items.Single(x => x.Name == "UV Baskı"); Assert(PricingEngine.Calculate([uv], new(60, 90, 0, 0, 1, 40), 2).CostTl == 450m, "UV 60×90 maliyeti");
            var foil = items.Single(x => x.Name == "Folyo" && x.Variant == "Eko"); var plotter = items.Single(x => x.Name == "Plotter Kesim"); Assert(PricingEngine.Calculate([foil, plotter], new(100, 100, 0, 0, 1, 40), 2).CostTl == 75m, "Folyo + Plotter");
            var dtf = items.Single(x => x.Name == "DTF Baskı"); Assert(PricingEngine.Calculate([dtf], new(0, 0, 12, 0, 1, 40), 2).CostTl == 1200m, "DTF 10 m üstü");
            Console.WriteLine("THESAP_SMOKE_OK"); return 0;
        }
        catch (Exception ex) { Console.Error.WriteLine(ex); return 1; }
    }
    private static void Assert(bool value, string name) { if (!value) throw new InvalidOperationException(name); }
}

namespace BTakip;

public static class SmokeTests
{
    public static int Run(string[] args)
    {
        var root = GetArgument(args, "--data-dir") ?? Path.Combine(Path.GetTempPath(), "BTakipSmoke-" + Guid.NewGuid().ToString("N"));
        try
        {
            Console.WriteLine("BTakip kritik smoke testi başlıyor...");
            var store = new DataStore(root);
            Assert(store.State.PriceItems.Count >= 18, "varsayılan fiyat listesi");

            var uv = store.State.PriceItems.Single(x => x.Name == "UV Baskı");
            var uvResult = PricingEngine.Calculate([uv], new CalculationInput(60, 90, 0, 0, 1, 40), 2);
            Assert(uvResult.CostTl == 450m, "UV 60×90 maliyeti");

            uv.GroupProfitPercentOverrides["dealer"] = 80m;
            var uvSpecial = PricingEngine.Calculate([uv], new CalculationInput(60, 90, 0, 0, 1, 40), 2, null, "dealer", store.State.PriceGroups);
            Assert(uvSpecial.CostTl == 450m && uvSpecial.SaleTl == 810m, "malzemeye özel müşteri kâr oranı");
            uv.GroupProfitPercentOverrides.Clear();

            var foil = store.State.PriceItems.Single(x => x.Name == "Folyo" && x.Variant == "Eko");
            var plotter = store.State.PriceItems.Single(x => x.Name == "Plotter Kesim");
            var plotterResult = PricingEngine.Calculate([foil, plotter], new CalculationInput(100, 100, 0, 0, 1, 40), 2);
            Assert(plotterResult.CostTl == 75m, "folyo + %50 plotter");

            var dtf = store.State.PriceItems.Single(x => x.Name == "DTF Baskı");
            var dtfResult = PricingEngine.Calculate([dtf], new CalculationInput(0, 0, 12, 0, 1, 40), 2);
            Assert(dtfResult.CostTl == 1200m, "DTF 10 metre üstü kademesi");

            var customer = new Customer { Name = "Smoke Müşteri", PriceGroupId = "dealer", DeviceId = store.State.DeviceId };
            store.State.Customers.Add(customer);
            store.State.Orders.Add(new Order { CustomerId = customer.Id, Description = "Smoke UV — Ölçü: 60 × 90 cm", Material = uv.DisplayName, WidthCm = 60, HeightCm = 90, CostTotalTl = 450, SaleTotalTl = 900, ExchangeRate = 40, PriceGroupId = "dealer", DeviceId = store.State.DeviceId });
            store.State.Payments.Add(new Payment { CustomerId = customer.Id, AmountTl = 250, Description = "Smoke Tahsilat", DeviceId = store.State.DeviceId });
            store.SaveAsync("Smoke kayıt").GetAwaiter().GetResult();
            Assert(File.Exists(store.DataFile), "yerel veri dosyası");
            Assert(File.Exists(store.LatestWorkbook), "her kayıt sonrası Excel yedeği");
            Assert(File.Exists(store.DataFile + ".sha256") && DataStore.VerifyFileIntegrity(store.DataFile), "yerel veri SHA-256 bütünlüğü");
            Assert(File.Exists(store.LatestWorkbook + ".sha256") && DataStore.VerifyFileIntegrity(store.LatestWorkbook), "Excel yedeği SHA-256 bütünlüğü");
            Assert(store.GetBalance(customer.Id) == 650m, "cari bakiye");
            Assert(store.GetLedger(customer.Id).First(x => x.Type == "Satış").Measure == "60 × 90 cm", "cari ölçü sütunu");
            Assert(store.GetLedger(customer.Id).First(x => x.Type == "Satış").Material == uv.DisplayName, "cari malzeme sütunu");

            store.CaptureUndo("Smoke geçici sipariş");
            var temporaryOrder = new Order { CustomerId = customer.Id, Description = "Geri alınacak", SaleTotalTl = 100, DeviceId = store.State.DeviceId };
            store.State.Orders.Add(temporaryOrder);
            store.SaveAsync("Smoke geri alma hazırlığı").GetAwaiter().GetResult();
            Assert(store.GetBalance(customer.Id) == 750m, "geri alma öncesi hareket");
            store.UndoLastAsync().GetAwaiter().GetResult();
            Assert(store.GetBalance(customer.Id) == 650m && !store.State.Orders.Any(x => x.Id == temporaryOrder.Id && !x.Deleted), "son veri işlemini geri alma");
            Assert(!store.CanUndo, "kullanılmış geri alma kopyasının arşivlenmesi");

            var importRoot = Path.Combine(root, "import-test");
            var imported = new DataStore(importRoot);
            var report = SimpleXlsx.Import(store.LatestWorkbook, imported);
            imported.SaveAsync("Smoke Excel içe aktarma").GetAwaiter().GetResult();
            Assert(report.Customers > 0 && report.Prices > 0 && report.Orders > 0 && report.Payments > 0, "Excel içe/dışa aktarma");
            Assert(imported.State.Orders.Any(x => x.Material == uv.DisplayName), "Excel sipariş malzemesi");
            var beforeAppend = (imported.State.Customers.Count, imported.State.PriceItems.Count, imported.State.Orders.Count, imported.State.Payments.Count);
            SimpleXlsx.Import(store.LatestWorkbook, imported, true);
            var afterAppend = (imported.State.Customers.Count, imported.State.PriceItems.Count, imported.State.Orders.Count, imported.State.Payments.Count);
            Assert(beforeAppend == afterAppend, "Excel cariye ekle tekrarları çoğaltmaz");

            var fullBackup = Path.Combine(root, "BTakip-Smoke-Tam-Yedek.btakip");
            store.ExportFullBackup(fullBackup);
            var restoreRoot = Path.Combine(root, "full-restore-test");
            var restored = new DataStore(restoreRoot);
            restored.ImportFullBackupAsync(fullBackup).GetAwaiter().GetResult();
            var restoredCustomer = restored.State.Customers.Single(x => x.Name == customer.Name);
            Assert(restored.GetBalance(restoredCustomer.Id) == 650m, "tek dosyalık tam yedekten cari bakiye");
            Assert(restored.State.PriceItems.Count == store.State.PriceItems.Count && restored.State.Settings.UsdTryRate == store.State.Settings.UsdTryRate, "tam yedekten fiyatlar ve ayarlar");

            Console.WriteLine("SMOKE TEST BAŞARILI");
            Console.WriteLine("Veri klasörü: " + root);
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("SMOKE TEST BAŞARISIZ: " + ex);
            return 1;
        }
    }

    private static void Assert(bool condition, string name)
    {
        if (!condition) throw new InvalidOperationException("Test başarısız: " + name);
        Console.WriteLine("OK  " + name);
    }

    private static string? GetArgument(string[] args, string key)
    {
        var index = Array.FindIndex(args, x => x.Equals(key, StringComparison.OrdinalIgnoreCase));
        return index >= 0 && index + 1 < args.Length ? args[index + 1] : null;
    }
}

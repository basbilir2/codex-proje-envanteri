using System.Globalization;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace BTakip;

public sealed class ImportedPricingReport
{
    public string Customer { get; set; } = "";
    public decimal ExchangeRate { get; set; }
    public decimal Multiplier { get; set; }
    public int TotalOrders { get; set; }
    public int CompleteOrders { get; set; }
    public int PartialOrders { get; set; }
    public int UnpricedOrders { get; set; }
    public decimal SalesTotalTl { get; set; }
    public decimal PaymentsTotalTl { get; set; }
    public decimal BalanceTl { get; set; }
    public List<ImportedPricingDetail> Details { get; set; } = [];
}

public sealed class ImportedPricingDetail
{
    public string OrderId { get; set; } = "";
    public DateTime Date { get; set; }
    public string Description { get; set; } = "";
    public decimal CostTl { get; set; }
    public decimal SaleTl { get; set; }
    public string Status { get; set; } = "";
    public string Missing { get; set; } = "";
    public string Calculation { get; set; } = "";
}

public static class ImportedOrderPricing
{
    private static readonly CultureInfo Tr = new("tr-TR");
    private static readonly Regex Dimension = new(@"(?<w>\d+(?:[.,]\d+)?)\s*[×xX]\s*(?<h>\d+(?:[.,]\d+)?)\s*cm", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex SingleCentimeter = new(@"Ölçü:\s*(?<cm>\d+(?:[.,]\d+)?)\s*cm\b", RegexOptions.IgnoreCase | RegexOptions.Compiled);

    public static ImportedPricingReport RepriceBetul(DataStore store)
    {
        var state = store.State;
        var customer = state.Customers.FirstOrDefault(x => Fold(x.Name) == "AnonPerson_0005")
            ?? throw new InvalidOperationException("AnonPerson_0005 müşteri kaydı bulunamadı.");
        var group = state.PriceGroups.First(x => x.Id == "dealer");
        customer.PriceGroupId = group.Id;
        store.Touch(customer);

        var rate = state.Settings.UsdTryRate > 0 ? state.Settings.UsdTryRate : 40m;
        var orders = state.Orders.Where(x => !x.Deleted && x.CustomerId == customer.Id && x.Id.StartsWith("AnonPerson_0002_siparis_", StringComparison.OrdinalIgnoreCase)).ToList();
        var detailGroups = orders.GroupBy(GroupKey).ToDictionary(g => g.Key, g => g.ToList());
        var report = new ImportedPricingReport
        {
            Customer = customer.Name,
            ExchangeRate = rate,
            Multiplier = group.CostMultiplier,
            TotalOrders = orders.Count
        };

        foreach (var order in orders)
        {
            var original = StripAudit(order.Description);
            var singleLength = SingleCentimeter.Match(original);
            if (singleLength.Success && !Dimension.IsMatch(original))
                order.LengthMeter = Number(singleLength.Groups["cm"].Value) / 100m;
            var text = Fold(original);
            var missing = new List<string>();
            var calculations = new List<string>();
            var lines = new List<OrderLine>();
            var area = EffectiveArea(original, order);
            var hasKnownPrice = false;

            var agreed = AgreedSale(original, order.Quantity);
            if (agreed > 0)
            {
                order.CostTotalTl = 0;
                order.SaleTotalTl = agreed;
                order.Lines = [new OrderLine { Name = "Kaynakta yazılı anlaşılmış satış fiyatı", QuantityUsed = 1, UnitCost = agreed, Currency = "TL", CostTl = 0 }];
                calculations.Add($"Kaynakta yazılı satış fiyatı: {agreed:N2} TL");
                hasKnownPrice = true;
            }
            else
            {
                if (Word(text, "dtf"))
                {
                    var length = EffectiveDtfLength(original, order);
                    if (length > 0)
                    {
                        var item = Item(state, "DTF Baskı");
                        var unitUsd = length > 10 && item.SecondaryCost > 0 ? item.SecondaryCost : item.UnitCost;
                        Add(lines, item, length, unitUsd, "USD", length * unitUsd * rate);
                        calculations.Add($"DTF {length:N2} m × {unitUsd:N2} USD × {rate:N4}");
                        hasKnownPrice = true;
                    }
                    else missing.Add("DTF uzunluğu/ölçüsü");
                }

                if (text.Contains("dekota"))
                {
                    if (area > 0)
                    {
                        var isFive = Regex.IsMatch(text, @"5\s*mm");
                        var item = Item(state, "Dekota", isFive ? "5 mm" : "3 mm");
                        var sheetArea = item.SheetWidthCm * item.SheetHeightCm / 10_000m;
                        var ratio = area / sheetArea;
                        Add(lines, item, ratio, item.UnitCost, "USD", ratio * item.UnitCost * rate);
                        calculations.Add($"Dekota {(isFive ? "5" : "3")} mm {area:N4} m² / {sheetArea:N4} m² × {item.UnitCost:N2} USD × {rate:N4}");
                        hasKnownPrice = true;
                    }
                    else missing.Add("Dekota ölçüsü");
                }

                if (text.Contains("pleksi"))
                {
                    if (Regex.IsMatch(text, @"5\s*mm")) missing.Add("5 mm pleksi fiyatı");
                    else if (area <= 0) missing.Add("Pleksi ölçüsü");
                    else
                    {
                        var color = text.Contains("bordo") ? "Bordo" : text.Contains("siyah") ? "Siyah" : text.Contains("seffaf") ? "Şeffaf" : text.Contains("yesil") ? "Yeşil" : "";
                        if (color.Length == 0) missing.Add("Pleksi rengi/fiyatı");
                        else
                        {
                            var item = Item(state, "Pleksi", color);
                            var sheetArea = item.SheetWidthCm * item.SheetHeightCm / 10_000m;
                            var ratio = area / sheetArea;
                            Add(lines, item, ratio, item.UnitCost, "USD", ratio * item.UnitCost * rate);
                            calculations.Add($"{color} pleksi {area:N4} m² / {sheetArea:N4} m² × {item.UnitCost:N2} USD × {rate:N4}");
                            hasKnownPrice = true;
                        }
                    }
                }

                var hasFolyo = text.Contains("folyo");
                var goldFolyo = text.Contains("gold") || text.Contains("altin");
                var hasCompanionFolyo = detailGroups[GroupKey(order)].Any(x => x.Id != order.Id && Fold(DetailPart(StripAudit(x.Description))).Contains("folyo") && !Fold(DetailPart(StripAudit(x.Description))).Contains("plotter"));
                if (hasFolyo && !goldFolyo)
                {
                    if (area > 0)
                    {
                        var item = Item(state, "Folyo", "Eko");
                        Add(lines, item, area, item.UnitCost, "TL", area * item.UnitCost);
                        calculations.Add($"Eko folyo {area:N4} m² × {item.UnitCost:N2} TL");
                        hasKnownPrice = true;
                    }
                    else missing.Add("Folyo ölçüsü");
                }
                else if (hasFolyo && goldFolyo) missing.Add("Gold folyo fiyatı");

                if (text.Contains("plotter"))
                {
                    if (goldFolyo) missing.Add("Gold folyo için plotter maliyeti");
                    else if (area > 0)
                    {
                        var item = Item(state, "Plotter Kesim");
                        var foil = Item(state, "Folyo", "Eko");
                        if (!hasFolyo && !hasCompanionFolyo)
                        {
                            Add(lines, foil, area, foil.UnitCost, "TL", area * foil.UnitCost);
                            calculations.Add($"Plotter ürünü folyosu {area:N4} m² × {foil.UnitCost:N2} TL");
                        }
                        var plotterCost = area * foil.UnitCost * item.UnitCost / 100m;
                        Add(lines, item, item.UnitCost, item.UnitCost, "%", plotterCost);
                        calculations.Add($"Plotter {area:N4} m² folyo maliyetinin %{item.UnitCost:N0}'si");
                        hasKnownPrice = true;
                    }
                    else missing.Add("Plotter ölçüsü");
                }

                if (Word(text, "uv"))
                {
                    if (area > 0)
                    {
                        var item = Item(state, "UV Baskı");
                        var tables = area / 0.54m;
                        Add(lines, item, tables, item.UnitCost, "TL", tables * item.UnitCost);
                        calculations.Add($"UV {area:N4} m² / 0,54 × {item.UnitCost:N2} TL");
                        hasKnownPrice = true;
                    }
                    else missing.Add("UV baskı ölçüsü");
                }

                if (text.Contains("sivama"))
                {
                    if (area > 0)
                    {
                        var item = Item(state, "Sıvama");
                        Add(lines, item, area, item.UnitCost, "TL", area * item.UnitCost);
                        calculations.Add($"Sıvama {area:N4} m² × {item.UnitCost:N2} TL");
                        hasKnownPrice = true;
                    }
                    else missing.Add("Sıvama ölçüsü");
                }

                if (text.Contains("lazer")) missing.Add("Lazer kesim süresi");
                if (text.Contains("kazima")) missing.Add("Kazıma fiyatı");
                if (text.Contains("tasiyici") || text.Contains("baskes transfer")) missing.Add("Taşıyıcı fiyatı");
                if (text.Contains("karton ayak") || text.Contains("destek")) missing.Add("Karton ayak/destek fiyatı");
                if (text.Contains("kece")) missing.Add("Keçe kesim fiyatı");
                if (!hasKnownPrice && missing.Count == 0) missing.Add("Ürün/hizmet fiyat eşleştirmesi");

                order.Lines = lines;
                order.CostTotalTl = decimal.Round(lines.Sum(x => x.CostTl), 2);
                order.SaleTotalTl = PricingEngine.CalculateSale(lines, state.PriceItems, group.Id, group.CostMultiplier, state.PriceGroups);
            }

            order.PriceGroupId = group.Id;
            order.ExchangeRate = rate;
            order.Description = missing.Count == 0 ? original : $"{original} | HESAP KONTROL: {string.Join(", ", missing.Distinct())}";
            store.Touch(order);

            var status = missing.Count == 0 ? "Tam hesaplandı" : order.SaleTotalTl > 0 ? "Kısmi hesaplandı" : "Fiyat bekliyor";
            if (status == "Tam hesaplandı") report.CompleteOrders++;
            else if (status == "Kısmi hesaplandı") report.PartialOrders++;
            else report.UnpricedOrders++;
            report.Details.Add(new ImportedPricingDetail
            {
                OrderId = order.Id,
                Date = order.Date,
                Description = original,
                CostTl = order.CostTotalTl,
                SaleTl = order.SaleTotalTl,
                Status = status,
                Missing = string.Join("; ", missing.Distinct()),
                Calculation = string.Join(" + ", calculations)
            });
        }

        report.SalesTotalTl = decimal.Round(orders.Sum(x => x.SaleTotalTl), 2);
        report.PaymentsTotalTl = decimal.Round(state.Payments.Where(x => !x.Deleted && x.CustomerId == customer.Id).Sum(x => x.AmountTl), 2);
        report.BalanceTl = report.SalesTotalTl - report.PaymentsTotalTl;
        return report;
    }

    public static void SaveReport(ImportedPricingReport report, string path)
    {
        File.WriteAllText(path, JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));
    }

    private static PriceItem Item(AppState state, string name, string? variant = null) =>
        state.PriceItems.First(x => !x.Deleted && Fold(x.Name) == Fold(name) && (variant is null || Fold(x.Variant).Contains(Fold(variant))));

    private static void Add(List<OrderLine> lines, PriceItem item, decimal used, decimal unitCost, string currency, decimal costTl) =>
        lines.Add(new OrderLine { PriceItemId = item.Id, Name = item.DisplayName, QuantityUsed = decimal.Round(used, 4), UnitCost = unitCost, Currency = currency, CostTl = decimal.Round(costTl, 2) });

    private static decimal EffectiveArea(string description, Order order)
    {
        var dimensions = Dimension.Matches(description).Select(m => (W: Number(m.Groups["w"].Value), H: Number(m.Groups["h"].Value))).ToList();
        var qty = order.Quantity <= 0 ? 1 : order.Quantity;
        if (dimensions.Count == 0) return Math.Max(0, order.WidthCm) * Math.Max(0, order.HeightCm) / 10_000m * qty;
        if (dimensions.Count == 1) return dimensions[0].W * dimensions[0].H / 10_000m * qty;
        if (qty > 1) return dimensions[0].W * dimensions[0].H / 10_000m + dimensions[^1].W * dimensions[^1].H / 10_000m * qty;
        return dimensions.Sum(x => x.W * x.H / 10_000m);
    }

    private static decimal EffectiveDtfLength(string description, Order order)
    {
        var qty = order.Quantity <= 0 ? 1 : order.Quantity;
        var single = SingleCentimeter.Match(description);
        if (single.Success) return Number(single.Groups["cm"].Value) / 100m * qty;
        if (order.LengthMeter > 0) return order.LengthMeter * qty;
        var match = Dimension.Match(description);
        if (!match.Success) return 0;
        var w = Number(match.Groups["w"].Value);
        var h = Number(match.Groups["h"].Value);
        var shorter = Math.Min(w, h);
        var longer = Math.Max(w, h);
        decimal length = longer <= 58 ? shorter / 100m : shorter <= 58 ? longer / 100m : (w * h / 10_000m) / 0.58m;
        return length * qty;
    }

    private static decimal AgreedSale(string text, decimal orderQuantity)
    {
        var whatsapp = Regex.Match(text, @"(?<p>\d+(?:[.,]\d+)?)\s*[-–]?\s*Whatsapp\s*fiyat", RegexOptions.IgnoreCase);
        if (whatsapp.Success) return Number(whatsapp.Groups["p"].Value);
        var each = Regex.Match(text, @"(?<q>\d+)\s*adet.*?Tanesi\s*(?<p>\d+(?:[.,]\d+)?)\s*TL", RegexOptions.IgnoreCase);
        if (each.Success) return Number(each.Groups["q"].Value) * Number(each.Groups["p"].Value);
        return 0;
    }

    private static string GroupKey(Order order) => $"{order.Date:yyyyMMdd}|{Fold(StripAudit(order.Description).Split('—')[0])}";
    private static string DetailPart(string text) { var parts = text.Split('—'); return parts.Length > 1 ? parts[1] : text; }
    private static string StripAudit(string text) { var i = text.IndexOf(" | HESAP KONTROL:", StringComparison.OrdinalIgnoreCase); return (i >= 0 ? text[..i] : text).Trim(); }
    private static bool Word(string text, string value) => Regex.IsMatch(text, $@"(^|[^a-z0-9]){Regex.Escape(value)}([^a-z0-9]|$)", RegexOptions.IgnoreCase);
    private static decimal Number(string value)
    {
        var normalized = value.Trim();
        if (normalized.Contains(','))
            return decimal.Parse(normalized.Replace(".", "").Replace(',', '.'), CultureInfo.InvariantCulture);
        return decimal.Parse(normalized, CultureInfo.InvariantCulture);
    }
    private static string Fold(string value) => value.Trim().ToLower(Tr).Replace("ı", "i").Replace("ş", "s").Replace("ğ", "g").Replace("ü", "u").Replace("ö", "o").Replace("ç", "c");
}

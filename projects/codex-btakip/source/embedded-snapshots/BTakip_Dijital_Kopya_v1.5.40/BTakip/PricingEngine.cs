namespace BTakip;

public static class PricingEngine
{
    public static CalculationResult Calculate(
        IEnumerable<PriceItem> selected,
        CalculationInput input,
        decimal groupMultiplier,
        decimal? alternativeMarkupPercent = null,
        string? priceGroupId = null,
        IEnumerable<PriceGroup>? priceGroups = null,
        IEnumerable<PriceItem>? catalog = null,
        bool? dtfDiscounted = null)
    {
        var result = new CalculationResult();
        var area = Math.Max(0, input.WidthCm) * Math.Max(0, input.HeightCm) / 10_000m;
        var qty = input.Quantity <= 0 ? 1 : input.Quantity;
        decimal materialSubtotal = 0;
        var percentItems = new List<PriceItem>();
        var activeItems = selected.Where(x => x.Active && !x.Deleted).ToList();
        var allItems = (catalog ?? activeItems).Where(x => x.Active && !x.Deleted).ToList();
        var selectedIds = activeItems.Select(x => x.Id).ToHashSet();

        foreach (var item in activeItems)
        {
            if (item.Formula == PricingFormula.PercentMaterial)
            {
                percentItems.Add(item);
                continue;
            }

            if (item.IsPrintProduct && item.Formula != PricingFormula.DtfTier &&
                !item.Name.Contains("DTF", StringComparison.OrdinalIgnoreCase) &&
                !string.IsNullOrWhiteSpace(item.BaseMaterialPriceItemId) && !selectedIds.Contains(item.BaseMaterialPriceItemId))
            {
                var material = allItems.FirstOrDefault(x => x.Id == item.BaseMaterialPriceItemId);
                if (material is not null)
                {
                    var materialUsed = material.Formula == PricingFormula.SheetArea ? CalculateSheetRatio(material, area, qty) : area * qty;
                    var materialNativeCost = materialUsed * material.UnitCost;
                    var materialTlCost = material.Currency.Equals("USD", StringComparison.OrdinalIgnoreCase) ? materialNativeCost * input.ExchangeRate : materialNativeCost;
                    var materialLine = new OrderLine
                    {
                        PriceItemId = item.Id, Name = material.DisplayName, QuantityUsed = decimal.Round(materialUsed, 4),
                        UnitCost = material.UnitCost, Currency = material.Currency, CostTl = decimal.Round(materialTlCost, 2)
                    };
                    result.Lines.Add(materialLine);
                    result.CostTl += materialLine.CostTl;
                    materialSubtotal += materialLine.CostTl;
                }
            }

            decimal used = item.Formula switch
            {
                PricingFormula.SquareMeter => area * qty,
                PricingFormula.Meter => Math.Max(0, input.LengthMeter) * qty,
                PricingFormula.Piece => qty,
                PricingFormula.Minute => Math.Max(0, input.DurationMinutes) * qty,
                PricingFormula.Hour => Math.Max(0, input.DurationMinutes) / 60m * qty,
                PricingFormula.Fixed => 1,
                PricingFormula.SheetArea => CalculateSheetRatio(item, area, qty),
                PricingFormula.UvTable => area / GetTableArea(item) * qty,
                PricingFormula.DtfTier => Math.Max(0, input.LengthMeter) * qty,
                _ => 0
            };

            var useDtfDiscount = item.Formula == PricingFormula.DtfTier && item.SecondaryCost > 0 &&
                (string.Equals(priceGroupId, "dealer", StringComparison.OrdinalIgnoreCase) ||
                 (dtfDiscounted ?? input.LengthMeter > 10));
            var unitCost = useDtfDiscount ? item.SecondaryCost : item.UnitCost;
            var nativeCost = used * unitCost;
            var tlCost = item.Currency.Equals("USD", StringComparison.OrdinalIgnoreCase)
                ? nativeCost * input.ExchangeRate
                : nativeCost;

            var line = new OrderLine
            {
                PriceItemId = item.Id,
                Name = item.DisplayName,
                QuantityUsed = decimal.Round(used, 4),
                UnitCost = unitCost,
                Currency = item.Currency,
                CostTl = decimal.Round(tlCost, 2)
            };
            result.Lines.Add(line);
            result.CostTl += line.CostTl;
            if (item.Category.Equals("Malzeme", StringComparison.OrdinalIgnoreCase) || item.Category.Equals("Baskı", StringComparison.OrdinalIgnoreCase) ||
                item.Category.Equals("Ürün", StringComparison.OrdinalIgnoreCase))
                materialSubtotal += line.CostTl;

            if (item.ServiceEnabled && item.ServiceUnitCost > 0)
            {
                var serviceUsed = item.ServiceFormula == PricingFormula.Minute
                    ? Math.Max(0, input.DurationMinutes) * qty
                    : area * qty;
                var serviceNativeCost = serviceUsed * item.ServiceUnitCost;
                var serviceTlCost = item.Currency.Equals("USD", StringComparison.OrdinalIgnoreCase)
                    ? serviceNativeCost * input.ExchangeRate
                    : serviceNativeCost;
                var serviceLine = new OrderLine
                {
                    PriceItemId = item.Id,
                    Name = string.IsNullOrWhiteSpace(item.ServiceName) ? item.DisplayName + " / Hizmet" : item.DisplayName + " / " + item.ServiceName,
                    QuantityUsed = decimal.Round(serviceUsed, 4), UnitCost = item.ServiceUnitCost,
                    Currency = item.Currency, CostTl = decimal.Round(serviceTlCost, 2)
                };
                result.Lines.Add(serviceLine);
                result.CostTl += serviceLine.CostTl;
            }
        }

        foreach (var item in percentItems)
        {
            var tlCost = materialSubtotal * item.UnitCost / 100m;
            result.Lines.Add(new OrderLine
            {
                PriceItemId = item.Id,
                Name = item.DisplayName,
                QuantityUsed = item.UnitCost,
                UnitCost = item.UnitCost,
                Currency = "%",
                CostTl = decimal.Round(tlCost, 2)
            });
            result.CostTl += tlCost;
        }

        result.CostTl = decimal.Round(result.CostTl, 2);
        result.SaleTl = alternativeMarkupPercent.HasValue
            ? decimal.Round(result.CostTl * (1 + alternativeMarkupPercent.Value / 100m), 2)
            : CalculateSale(result.Lines, activeItems.Concat(allItems), priceGroupId, groupMultiplier, priceGroups);
        return result;
    }

    public static decimal CalculateSale(IEnumerable<OrderLine> lines, IEnumerable<PriceItem> items, string? priceGroupId, decimal groupMultiplier, IEnumerable<PriceGroup>? priceGroups = null)
    {
        var byId = items.Where(x => !x.Deleted).GroupBy(x => x.Id).ToDictionary(x => x.Key, x => x.First());
        var total = lines.Sum(line => line.CostTl * ResolveMultiplier(byId.GetValueOrDefault(line.PriceItemId), priceGroupId, groupMultiplier));
        return decimal.Round(total, 2);
    }

    public static decimal ResolveMultiplier(PriceItem? item, string? priceGroupId, decimal groupMultiplier, IReadOnlyDictionary<string, decimal>? groupMultipliers = null)
    {
        if (GetSpecialProfitPercent(item, priceGroupId) is decimal specialPercent) return 1m + specialPercent / 100m;
        return groupMultiplier;
    }

    public static decimal? GetSpecialProfitPercent(PriceItem? item, string? priceGroupId)
    {
        if (item is null || string.IsNullOrWhiteSpace(priceGroupId)) return null;
        if (item.GroupProfitPercentOverrides?.TryGetValue(priceGroupId, out var specialPercent) == true) return specialPercent;
        return item.SpecialProfitPercent.HasValue && string.Equals(item.PriceGroupId, priceGroupId, StringComparison.OrdinalIgnoreCase)
            ? item.SpecialProfitPercent
            : null;
    }

    private static decimal CalculateSheetRatio(PriceItem item, decimal area, decimal qty)
    {
        var sheetArea = item.SheetWidthCm * item.SheetHeightCm / 10_000m;
        return sheetArea <= 0 ? 0 : area / sheetArea * qty;
    }

    private static decimal GetTableArea(PriceItem item)
    {
        var configured = item.SheetWidthCm * item.SheetHeightCm / 10_000m;
        return configured > 0 ? configured : 0.54m;
    }
}

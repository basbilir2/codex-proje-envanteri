namespace THesap;

public sealed class PriceGroup
{
    public string Id { get; set; } = "";
    public string Code { get; set; } = "";
    public string Name { get; set; } = "";
    public decimal CostMultiplier { get; set; }
    public string CalculatorLabel => $"{Name} — %{(CostMultiplier - 1m) * 100m:0.##} kâr";
    public override string ToString() => CalculatorLabel;
}

public sealed class PriceItem
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Category { get; set; } = "Malzeme";
    public string Name { get; set; } = "";
    public string Variant { get; set; } = "";
    public string Unit { get; set; } = "m²";
    public string Currency { get; set; } = "TL";
    public decimal UnitCost { get; set; }
    public decimal SecondaryCost { get; set; }
    public decimal SheetWidthCm { get; set; }
    public decimal SheetHeightCm { get; set; }
    public string BaseMaterialPriceItemId { get; set; } = "";
    public bool IsPrintProduct { get; set; }
    public bool ServiceEnabled { get; set; }
    public string ServiceName { get; set; } = "";
    public string ServiceFormula { get; set; } = PricingFormula.SquareMeter;
    public decimal ServiceUnitCost { get; set; }
    public string Formula { get; set; } = PricingFormula.SquareMeter;
    public bool Active { get; set; } = true;
    public bool Deleted { get; set; }
    public string PriceGroupId { get; set; } = "retail";
    public Dictionary<string, decimal> GroupProfitPercentOverrides { get; set; } = [];
    public decimal? SpecialProfitPercent { get; set; }
    public string DisplayName => string.IsNullOrWhiteSpace(Variant) ? Name : $"{Name} — {Variant}";
    // Hesaplama listesindeki adlar BTakip'teki gibi yalındır; tür bilgisi
    // yalnız Fiyat Tanımları tablosunda ayrı sütunda gösterilir.
    public override string ToString() => DisplayName;
}

public static class PricingFormula
{
    public const string SquareMeter = "M2";
    public const string Meter = "METRE";
    public const string Piece = "ADET";
    public const string Minute = "DAKIKA";
    public const string Hour = "SAAT";
    public const string Fixed = "SABIT";
    public const string SheetArea = "LEVHA_ALAN";
    public const string UvTable = "UV_60X90";
    public const string DtfTier = "DTF_KADEME";
    public const string PercentMaterial = "MALZEME_YUZDE";
}

public sealed record CalculationInput(decimal WidthCm, decimal HeightCm, decimal LengthMeter, decimal DurationMinutes, decimal Quantity, decimal ExchangeRate);
public sealed class OrderLine { public string PriceItemId { get; set; } = ""; public string Name { get; set; } = ""; public decimal QuantityUsed { get; set; } public decimal UnitCost { get; set; } public string Currency { get; set; } = "TL"; public decimal CostTl { get; set; } }
public sealed class CalculationResult { public decimal CostTl { get; set; } public decimal SaleTl { get; set; } public List<OrderLine> Lines { get; set; } = []; }

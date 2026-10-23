using System.Text.Json.Serialization;

namespace BTakip;

public abstract class SyncEntity
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public DateTime UpdatedAtUtc { get; set; } = DateTime.UtcNow;
    public long Revision { get; set; } = 1;
    public long SyncedRevision { get; set; }
    public string DeviceId { get; set; } = "";
    public bool Deleted { get; set; }
}

public sealed class Customer : SyncEntity
{
    public string Name { get; set; } = "";
    public string Company { get; set; } = "";
    public string Phone { get; set; } = "";
    public string Email { get; set; } = "";
    public string PriceGroupId { get; set; } = "retail";
    public string Notes { get; set; } = "";
    [JsonIgnore] public string PriceGroupName { get; set; } = "";
}

public sealed class PriceGroup : SyncEntity
{
    public string Code { get; set; } = "";
    public string Name { get; set; } = "";
    public decimal CostMultiplier { get; set; }
    [JsonIgnore] public string CalculatorLabel => $"{Name} — %{(CostMultiplier - 1m) * 100m:0.##} kâr";
}

public sealed class PriceItem : SyncEntity
{
    public string Category { get; set; } = "Malzeme";
    public string Name { get; set; } = "";
    public string Variant { get; set; } = "";
    public string Unit { get; set; } = "m²";
    public string Currency { get; set; } = "TL";
    public decimal UnitCost { get; set; }
    public decimal SecondaryCost { get; set; }
    public decimal SheetWidthCm { get; set; }
    public decimal SheetHeightCm { get; set; }
    public decimal ThicknessMm { get; set; }
    public string BaseMaterialPriceItemId { get; set; } = "";
    public bool IsPrintProduct { get; set; }
    public bool ServiceEnabled { get; set; }
    public string ServiceName { get; set; } = "";
    public string ServiceFormula { get; set; } = PricingFormula.SquareMeter;
    public decimal ServiceUnitCost { get; set; }
    public string Formula { get; set; } = PricingFormula.SquareMeter;
    public bool Active { get; set; } = true;
    public string PriceGroupId { get; set; } = "retail";
    public Dictionary<string, decimal> GroupProfitPercentOverrides { get; set; } = [];
    // Eski kayıtları yalnız bağlı oldukları müşteri grubunda okuyabilmek için korunur.
    public decimal? SpecialProfitPercent { get; set; }
    [JsonIgnore] public string DisplayName => string.IsNullOrWhiteSpace(Variant) ? Name : $"{Name} — {Variant}";
}

public sealed class Order : SyncEntity
{
    public DateTime Date { get; set; } = DateTime.Today;
    public string CustomerId { get; set; } = "";
    public string Description { get; set; } = "";
    public string Material { get; set; } = "";
    public decimal WidthCm { get; set; }
    public decimal HeightCm { get; set; }
    public decimal AreaM2 { get; set; }
    public decimal LengthMeter { get; set; }
    public decimal DurationMinutes { get; set; }
    public decimal Quantity { get; set; } = 1;
    public decimal ExchangeRate { get; set; }
    public decimal CostTotalTl { get; set; }
    public decimal SaleTotalTl { get; set; }
    public string PriceGroupId { get; set; } = "retail";
    public decimal? AlternativePercent { get; set; }
    public List<OrderLine> Lines { get; set; } = [];
}

public sealed class OrderLine
{
    public string PriceItemId { get; set; } = "";
    public string Name { get; set; } = "";
    public decimal QuantityUsed { get; set; }
    public decimal UnitCost { get; set; }
    public string Currency { get; set; } = "TL";
    public decimal CostTl { get; set; }
}

public sealed class Payment : SyncEntity
{
    public DateTime Date { get; set; } = DateTime.Today;
    public string CustomerId { get; set; } = "";
    public decimal AmountTl { get; set; }
    public string Description { get; set; } = "Tahsilat";
    public string PaymentType { get; set; } = "Nakit";
}

public sealed class ConflictRecord
{
    public string EntityType { get; set; } = "";
    public string EntityId { get; set; } = "";
    public string LocalJson { get; set; } = "";
    public string RemoteJson { get; set; } = "";
    public DateTime DetectedAtUtc { get; set; } = DateTime.UtcNow;
}

public enum ConflictDecision { UseGoogle, UsePc, KeepBoth, Skip }

public sealed class AppSettings
{
    public decimal UsdTryRate { get; set; } = 40m;
    public bool AutoExchangeRate { get; set; } = true;
    public string GoogleWebAppUrl { get; set; } = "";
    public string GoogleSyncToken { get; set; } = "";
    public int SyncIntervalSeconds { get; set; } = 30;
    public bool StartWithWindows { get; set; }
    public string LastGoogleChangeToken { get; set; } = "0";
    public DateTime? LastSyncUtc { get; set; }
    public string CloudAccountId { get; set; } = "";
    public string CloudAccountEmail { get; set; } = "";
    public DateTime? LastFirestorePullUtc { get; set; }
    public bool CloudBootstrapComplete { get; set; }
    public DateTime? LastCloudBackupUtc { get; set; }
    public DateTime? LastSheetMirrorUtc { get; set; }
}

public sealed class AppState
{
    public int SchemaVersion { get; set; } = 1;
    public string DeviceId { get; set; } = Environment.MachineName + "-" + Guid.NewGuid().ToString("N")[..8];
    public AppSettings Settings { get; set; } = new();
    public List<Customer> Customers { get; set; } = [];
    public List<PriceGroup> PriceGroups { get; set; } = [];
    public List<PriceItem> PriceItems { get; set; } = [];
    public List<Order> Orders { get; set; } = [];
    public List<Payment> Payments { get; set; } = [];
    public List<ConflictRecord> Conflicts { get; set; } = [];
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

    public static readonly Dictionary<string, string> Labels = new()
    {
        [SquareMeter] = "m² üzerinden",
        [Meter] = "metre üzerinden",
        [Piece] = "adet üzerinden",
        [Minute] = "dakika üzerinden",
        [Hour] = "saat üzerinden",
        [Fixed] = "sabit ücret",
        [SheetArea] = "levha alanı oranı",
        [UvTable] = "UV 60×90 oranı",
        [DtfTier] = "DTF 10 m kademesi",
        [PercentMaterial] = "baskı / malzeme toplamının yüzdesi"
    };
}

public sealed record CalculationInput(
    decimal WidthCm,
    decimal HeightCm,
    decimal LengthMeter,
    decimal DurationMinutes,
    decimal Quantity,
    decimal ExchangeRate);

public sealed class CalculationResult
{
    public decimal CostTl { get; set; }
    public decimal SaleTl { get; set; }
    public List<OrderLine> Lines { get; set; } = [];
}

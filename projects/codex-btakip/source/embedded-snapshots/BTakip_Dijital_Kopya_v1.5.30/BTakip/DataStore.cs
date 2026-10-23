using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
using System.IO.Compression;

namespace BTakip;

public sealed class DataStore
{
    private readonly JsonSerializerOptions _json = new()
    {
        WriteIndented = true,
        PropertyNameCaseInsensitive = true
    };
    private readonly SemaphoreSlim _gate = new(1, 1);
    private string? _recoveryMessage;

    public string RootPath { get; }
    public string DataFile => Path.Combine(RootPath, "btakip-veri.json");
    public string LatestWorkbook => Path.Combine(RootPath, "BTakip_Yedek_Son.xlsx");
    public string UndoFile => Path.Combine(RootPath, "GeriAl", "son-islem.json");
    public string UndoReasonFile => Path.Combine(RootPath, "GeriAl", "son-islem.txt");
    public AppState State { get; private set; }
    public bool ApplicationIntegrityOk { get; private set; } = true;
    public string SecurityStatus { get; private set; } = "Yedek ve yazılım bütünlük koruması etkin.";
    public bool CanUndo => File.Exists(UndoFile) && VerifyChecksum(UndoFile);
    public string UndoDescription => File.Exists(UndoReasonFile) ? File.ReadAllText(UndoReasonFile).Trim() : "Son işlem";
    public event EventHandler? Saved;

    public DataStore(string? overridePath = null)
    {
        RootPath = overridePath
            ?? Environment.GetEnvironmentVariable("BTAKIP_DATA_DIR")
            ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "btakip");
        Directory.CreateDirectory(RootPath);
        State = LoadOrCreate();
        CheckApplicationIntegrity();
        if (!File.Exists(DataFile + ".sha256")) WriteChecksum(DataFile);
        if (File.Exists(LatestWorkbook) && !File.Exists(LatestWorkbook + ".sha256")) WriteChecksum(LatestWorkbook);
        if (!string.IsNullOrWhiteSpace(_recoveryMessage))
            SecurityStatus = _recoveryMessage + " " + SecurityStatus;
    }

    private AppState LoadOrCreate()
    {
        if (File.Exists(DataFile))
        {
            try
            {
                if (!VerifyChecksum(DataFile)) throw new InvalidDataException("Ana veri dosyasının bütünlük değeri eşleşmiyor.");
                var loaded = JsonSerializer.Deserialize<AppState>(File.ReadAllText(DataFile), _json);
                if (loaded is not null)
                {
                    var catalogMigrated = Normalize(loaded);
                    if (catalogMigrated)
                    {
                        State = loaded;
                        SaveAsync("Fiyat kalemlerinin türleri düzenlendi").GetAwaiter().GetResult();
                    }
                    return loaded;
                }
            }
            catch
            {
                var corruptDir = Path.Combine(RootPath, "Kurtarma");
                Directory.CreateDirectory(corruptDir);
                var corruptCopy = Path.Combine(corruptDir, $"btakip-bozuk-{DateTime.Now:yyyyMMdd-HHmmss}.json");
                File.Copy(DataFile, corruptCopy, true);
                if (File.Exists(DataFile + ".sha256")) File.Copy(DataFile + ".sha256", corruptCopy + ".sha256", true);
                var recovered = LoadLatestValidBackup();
                if (recovered is not null)
                {
                    Normalize(recovered);
                    State = recovered;
                    _recoveryMessage = "Ana kayıt doğrulanamadığı için son sağlam yedek otomatik kurtarıldı.";
                    SaveAsync("Bütünlük kontrolü: son sağlam yedekten otomatik kurtarma").GetAwaiter().GetResult();
                    return recovered;
                }
            }
        }

        var state = SeedData.Create();
        Normalize(state);
        State = state;
        SaveAsync("İlk kurulum").GetAwaiter().GetResult();
        return state;
    }

    private static bool Normalize(AppState state)
    {
        var catalogMigrated = false;
        state.DeviceId = string.IsNullOrWhiteSpace(state.DeviceId)
            ? Environment.MachineName + "-" + Guid.NewGuid().ToString("N")[..8]
            : state.DeviceId;
        state.Settings ??= new AppSettings();
        state.Customers ??= [];
        state.PriceGroups ??= [];
        state.PriceItems ??= [];
        state.Orders ??= [];
        state.Payments ??= [];
        state.Conflicts ??= [];
        var ecoSolvent = state.PriceItems.FirstOrDefault(x => x.Name.Equals("Eco Solvent", StringComparison.OrdinalIgnoreCase));
        if (ecoSolvent is null)
        {
            state.PriceItems.Add(new PriceItem
            {
                Id = "eco-solvent", Category = "Baskı", Name = "Eco Solvent", Unit = "m²", Currency = "TL",
                Formula = PricingFormula.SquareMeter, Active = true, IsPrintProduct = true,
                DeviceId = state.DeviceId, Revision = 1, UpdatedAtUtc = DateTime.UtcNow
            });
            catalogMigrated = true;
        }
        else if (ecoSolvent.Deleted || !ecoSolvent.Active)
        {
            ecoSolvent.Deleted = false;
            ecoSolvent.Active = true;
            ecoSolvent.UpdatedAtUtc = DateTime.UtcNow;
            ecoSolvent.Revision = Math.Max(1, ecoSolvent.Revision + 1);
            ecoSolvent.DeviceId = state.DeviceId;
            catalogMigrated = true;
        }
        foreach (var item in state.PriceItems)
        {
            var name = item.Name.Trim();
            var targetCategory = name.Equals("Baskes", StringComparison.OrdinalIgnoreCase) ||
                                 name.Contains("Lazer Kesim", StringComparison.OrdinalIgnoreCase) ||
                                 name.Equals("Sıvama", StringComparison.OrdinalIgnoreCase)
                ? "Hizmet"
                : name.Contains("DTF", StringComparison.OrdinalIgnoreCase) ||
                                 name.Equals("UV", StringComparison.OrdinalIgnoreCase) ||
                                 name.StartsWith("UV ", StringComparison.OrdinalIgnoreCase) ||
                                 name.Contains("Solvent", StringComparison.OrdinalIgnoreCase)
                ? "Baskı"
                : "Malzeme";
            if (!item.Category.Equals(targetCategory, StringComparison.OrdinalIgnoreCase) || item.IsPrintProduct != (targetCategory == "Baskı"))
            {
                item.Category = targetCategory;
                item.IsPrintProduct = targetCategory == "Baskı";
                item.UpdatedAtUtc = DateTime.UtcNow;
                item.Revision = Math.Max(1, item.Revision + 1);
                item.DeviceId = state.DeviceId;
                catalogMigrated = true;
            }
            if (item.ThicknessMm <= 0)
            {
                var thickness = System.Text.RegularExpressions.Regex.Match(item.Variant, @"(?<mm>\d+(?:[.,]\d+)?)\s*mm", System.Text.RegularExpressions.RegexOptions.IgnoreCase);
                if (thickness.Success && decimal.TryParse(thickness.Groups["mm"].Value.Replace(',', '.'), System.Globalization.NumberStyles.Number, System.Globalization.CultureInfo.InvariantCulture, out var mm))
                    item.ThicknessMm = mm;
            }
            if (string.IsNullOrWhiteSpace(item.PriceGroupId)) item.PriceGroupId = "retail";
            item.BaseMaterialPriceItemId ??= "";
            item.ServiceName ??= "";
            item.ServiceFormula = item.ServiceFormula is PricingFormula.Minute or PricingFormula.SquareMeter ? item.ServiceFormula : PricingFormula.SquareMeter;
            item.GroupProfitPercentOverrides ??= [];
            if (item.SpecialProfitPercent is decimal legacyPercent)
            {
                item.GroupProfitPercentOverrides.TryAdd(item.PriceGroupId, legacyPercent);
                item.SpecialProfitPercent = null;
            }
        }
        foreach (var order in state.Orders.Where(x => string.IsNullOrWhiteSpace(x.Material)))
            order.Material = InferMaterial(order, state.PriceItems);
        foreach (var order in state.Orders)
        {
            var customer = state.Customers.FirstOrDefault(x => !x.Deleted && x.Id == order.CustomerId);
            if (customer is not null) order.PriceGroupId = customer.PriceGroupId;
        }
        return catalogMigrated;
    }

    public async Task<bool> NormalizeCatalogAsync()
    {
        if (!Normalize(State)) return false;
        await SaveAsync("Fiyat kalemlerinin türleri düzenlendi").ConfigureAwait(false);
        return true;
    }

    public void Touch(SyncEntity entity)
    {
        entity.UpdatedAtUtc = DateTime.UtcNow;
        entity.Revision = Math.Max(1, entity.Revision + 1);
        entity.DeviceId = State.DeviceId;
    }

    public async Task SaveAsync(string reason, bool createWorkbook = true)
    {
        await _gate.WaitAsync().ConfigureAwait(false);
        try
        {
            Directory.CreateDirectory(RootPath);
            var temp = DataFile + ".tmp";
            var json = JsonSerializer.Serialize(State, _json);
            await File.WriteAllTextAsync(temp, json).ConfigureAwait(false);
            File.Move(temp, DataFile, true);
            WriteChecksum(DataFile);

            var dailyDir = Path.Combine(RootPath, "Yedekler", DateTime.Now.ToString("yyyy-MM-dd"));
            Directory.CreateDirectory(dailyDir);
            var snapshot = Path.Combine(dailyDir, $"btakip-{DateTime.Now:HHmmssfff}.json");
            File.Copy(DataFile, snapshot, true);
            WriteChecksum(snapshot);

            if (createWorkbook)
            {
                try
                {
                    SimpleXlsx.Export(State, LatestWorkbook);
                    WriteChecksum(LatestWorkbook);
                }
                catch (Exception ex) { await AppendLogAsync($"Excel yedeği oluşturulamadı: {ex.Message}").ConfigureAwait(false); }
            }

            await AppendLogAsync($"KAYIT | {reason} | {Path.GetFileName(snapshot)}").ConfigureAwait(false);
        }
        finally
        {
            _gate.Release();
        }
        Saved?.Invoke(this, EventArgs.Empty);
    }

    public void CaptureUndo(string reason)
    {
        var undoDir = Path.GetDirectoryName(UndoFile)!;
        Directory.CreateDirectory(undoDir);
        if (File.Exists(UndoFile)) MoveCurrentUndoTo(Path.Combine(undoDir, "Gecmis"), UndoDescription);
        var description = string.IsNullOrWhiteSpace(reason) ? "Son işlem" : reason.Trim();
        WriteAtomic(UndoFile, JsonSerializer.Serialize(new UndoSnapshot(DateTime.UtcNow, description, State), _json));
        WriteChecksum(UndoFile);
        WriteAtomic(UndoReasonFile, description);
    }

    public async Task<string?> UndoLastAsync()
    {
        if (!File.Exists(UndoFile)) return null;
        if (!VerifyChecksum(UndoFile)) throw new InvalidDataException("Geri alma kopyasının bütünlüğü doğrulanamadı.");
        var undo = JsonSerializer.Deserialize<UndoSnapshot>(File.ReadAllText(UndoFile), _json)
            ?? throw new InvalidDataException("Geri alma kopyası okunamadı.");
        var restored = undo.State;
        Normalize(restored);
        var reason = UndoDescription;
        PreserveNewerRemoteChanges(restored, State, undo.CapturedAtUtc);
        restored.Settings.LastGoogleChangeToken = State.Settings.LastGoogleChangeToken;
        restored.Settings.LastSyncUtc = State.Settings.LastSyncUtc;
        restored.Conflicts = State.Conflicts;
        PrepareUndoState(restored, State);
        State = restored;
        await SaveAsync("Geri alındı: " + reason).ConfigureAwait(false);
        ArchiveUsedUndo(reason);
        PromotePreviousUndo();
        return reason;
    }

    public static bool VerifyFileIntegrity(string path) => File.Exists(path) && VerifyChecksum(path);

    public void ProtectFile(string path) => WriteChecksum(path);

    public void ExportFullBackup(string path)
    {
        var fullPath = Path.GetFullPath(path);
        Directory.CreateDirectory(Path.GetDirectoryName(fullPath)!);
        var temp = fullPath + ".tmp";
        if (File.Exists(temp)) File.Delete(temp);
        var data = JsonSerializer.SerializeToUtf8Bytes(State, _json);
        var manifest = new FullBackupManifest(1, DateTime.UtcNow, Environment.MachineName, Convert.ToHexString(SHA256.HashData(data)));
        using (var archive = ZipFile.Open(temp, ZipArchiveMode.Create))
        {
            var dataEntry = archive.CreateEntry("btakip-veri.json", CompressionLevel.Optimal);
            using (var stream = dataEntry.Open()) stream.Write(data);
            var manifestEntry = archive.CreateEntry("yedek-bilgisi.json", CompressionLevel.Optimal);
            using (var writer = new StreamWriter(manifestEntry.Open())) writer.Write(JsonSerializer.Serialize(manifest, _json));
            if (File.Exists(LatestWorkbook)) archive.CreateEntryFromFile(LatestWorkbook, "BTakip_Yedek_Son.xlsx", CompressionLevel.Optimal);
        }
        File.Move(temp, fullPath, true);
    }

    public async Task ImportFullBackupAsync(string path)
    {
        using var archive = ZipFile.OpenRead(path);
        var dataEntry = archive.GetEntry("btakip-veri.json") ?? throw new InvalidDataException("Yedek içinde BTakip veri dosyası bulunamadı.");
        var manifestEntry = archive.GetEntry("yedek-bilgisi.json") ?? throw new InvalidDataException("Yedek doğrulama bilgisi bulunamadı.");
        byte[] data;
        using (var input = dataEntry.Open())
        using (var memory = new MemoryStream()) { input.CopyTo(memory); data = memory.ToArray(); }
        FullBackupManifest manifest;
        using (var reader = new StreamReader(manifestEntry.Open()))
            manifest = JsonSerializer.Deserialize<FullBackupManifest>(reader.ReadToEnd(), _json) ?? throw new InvalidDataException("Yedek doğrulama bilgisi okunamadı.");
        var hash = Convert.ToHexString(SHA256.HashData(data));
        if (manifest.FormatVersion != 1 || !hash.Equals(manifest.DataSha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Yedek dosyasının bütünlüğü doğrulanamadı.");
        var restored = JsonSerializer.Deserialize<AppState>(data, _json) ?? throw new InvalidDataException("Yedek verileri okunamadı.");
        var newDeviceId = State.DeviceId;
        Normalize(restored);
        restored.DeviceId = newDeviceId;
        var now = DateTime.UtcNow;
        foreach (var entity in AllEntities(restored))
        {
            entity.DeviceId = newDeviceId;
            entity.Revision = Math.Max(1, entity.Revision + 1);
            entity.SyncedRevision = 0;
            entity.UpdatedAtUtc = now;
        }
        State = restored;
        await SaveAsync("Tek dosyalık tam yedek geri yüklendi").ConfigureAwait(false);
    }

    private static IEnumerable<SyncEntity> AllEntities(AppState state) =>
        state.Customers.Cast<SyncEntity>().Concat(state.PriceGroups).Concat(state.PriceItems).Concat(state.Orders).Concat(state.Payments);

    private AppState? LoadLatestValidBackup()
    {
        var root = Path.Combine(RootPath, "Yedekler");
        if (!Directory.Exists(root)) return null;
        foreach (var file in Directory.EnumerateFiles(root, "btakip-*.json", SearchOption.AllDirectories)
                     .OrderByDescending(File.GetLastWriteTimeUtc))
        {
            try
            {
                if (!VerifyChecksum(file)) continue;
                var state = JsonSerializer.Deserialize<AppState>(File.ReadAllText(file), _json);
                if (state is not null) return state;
            }
            catch { }
        }
        return null;
    }

    private void CheckApplicationIntegrity()
    {
        try
        {
            var executable = Environment.ProcessPath;
            if (string.IsNullOrWhiteSpace(executable) || !File.Exists(executable)) return;
            var hash = FileHash(executable);
            var version = Assembly.GetEntryAssembly()?.GetName().Version?.ToString() ?? "0.0.0.0";
            var sidecarOk = !File.Exists(executable + ".sha256") || VerifyChecksum(executable);
            var manifestPath = Path.Combine(RootPath, "yazilim-butunluk.json");
            SoftwareManifest? previous = null;
            if (File.Exists(manifestPath))
                previous = JsonSerializer.Deserialize<SoftwareManifest>(File.ReadAllText(manifestPath), _json);
            var recordedOk = previous is null || previous.Version != version || previous.Sha256.Equals(hash, StringComparison.OrdinalIgnoreCase);
            ApplicationIntegrityOk = sidecarOk && recordedOk;
            if (!ApplicationIntegrityOk)
            {
                SecurityStatus = "UYARI: Uygulama dosyasının bütünlüğü doğrulanamadı. Kurulum dosyasıyla onarım yapın.";
                File.AppendAllText(Path.Combine(RootPath, "btakip.log"), $"{DateTime.Now:yyyy-MM-dd HH:mm:ss} | GÜVENLİK | Uygulama bütünlük uyuşmazlığı{Environment.NewLine}");
                return;
            }
            if (previous is null || previous.Version != version)
                WriteAtomic(manifestPath, JsonSerializer.Serialize(new SoftwareManifest(version, hash, executable, DateTime.UtcNow), _json));
        }
        catch (Exception ex)
        {
            ApplicationIntegrityOk = false;
            SecurityStatus = "UYARI: Yazılım bütünlük kontrolü tamamlanamadı.";
            try { File.AppendAllText(Path.Combine(RootPath, "btakip.log"), $"{DateTime.Now:yyyy-MM-dd HH:mm:ss} | GÜVENLİK | {ex.Message}{Environment.NewLine}"); } catch { }
        }
    }

    private static void PrepareUndoState(AppState restored, AppState current)
    {
        restored.DeviceId = current.DeviceId;
        PrepareUndoEntities(restored.Customers, current.Customers, current.DeviceId);
        PrepareUndoEntities(restored.PriceGroups, current.PriceGroups, current.DeviceId);
        PrepareUndoEntities(restored.PriceItems, current.PriceItems, current.DeviceId);
        PrepareUndoEntities(restored.Orders, current.Orders, current.DeviceId);
        PrepareUndoEntities(restored.Payments, current.Payments, current.DeviceId);
    }

    private static void PrepareUndoEntities<T>(List<T> restored, List<T> current, string deviceId) where T : SyncEntity
    {
        var now = DateTime.UtcNow;
        var currentById = current.ToDictionary(x => x.Id, StringComparer.OrdinalIgnoreCase);
        var restoredIds = restored.Select(x => x.Id).ToHashSet(StringComparer.OrdinalIgnoreCase);
        for (var index = 0; index < restored.Count; index++)
        {
            var entity = restored[index];
            if (currentById.TryGetValue(entity.Id, out var unchanged) && EntityDataEqual(entity, unchanged))
            {
                restored[index] = unchanged;
                continue;
            }
            var currentRevision = currentById.TryGetValue(entity.Id, out var present) ? present.Revision : 0;
            entity.Revision = Math.Max(entity.Revision, currentRevision) + 1;
            entity.SyncedRevision = 0;
            entity.UpdatedAtUtc = now;
            entity.DeviceId = deviceId;
        }
        foreach (var entity in current.Where(x => !restoredIds.Contains(x.Id)))
        {
            entity.Deleted = true;
            entity.Revision = Math.Max(1, entity.Revision + 1);
            entity.SyncedRevision = 0;
            entity.UpdatedAtUtc = now;
            entity.DeviceId = deviceId;
            restored.Add(entity);
        }
    }

    private static void PreserveNewerRemoteChanges(AppState restored, AppState current, DateTime capturedAtUtc)
    {
        PreserveRemoteEntities(restored.Customers, current.Customers, current.DeviceId, capturedAtUtc);
        PreserveRemoteEntities(restored.PriceGroups, current.PriceGroups, current.DeviceId, capturedAtUtc);
        PreserveRemoteEntities(restored.PriceItems, current.PriceItems, current.DeviceId, capturedAtUtc);
        PreserveRemoteEntities(restored.Orders, current.Orders, current.DeviceId, capturedAtUtc);
        PreserveRemoteEntities(restored.Payments, current.Payments, current.DeviceId, capturedAtUtc);
    }

    private static void PreserveRemoteEntities<T>(List<T> restored, List<T> current, string localDeviceId, DateTime capturedAtUtc) where T : SyncEntity
    {
        foreach (var remote in current.Where(x => x.UpdatedAtUtc > capturedAtUtc && !x.DeviceId.Equals(localDeviceId, StringComparison.OrdinalIgnoreCase)))
        {
            var index = restored.FindIndex(x => x.Id.Equals(remote.Id, StringComparison.OrdinalIgnoreCase));
            if (index >= 0) restored[index] = remote;
            else restored.Add(remote);
        }
    }

    private static bool EntityDataEqual(SyncEntity left, SyncEntity right) => (left, right) switch
    {
        (Customer a, Customer b) => a.Deleted == b.Deleted && a.Name == b.Name && a.Company == b.Company && a.Phone == b.Phone && a.Email == b.Email && a.PriceGroupId == b.PriceGroupId && a.Notes == b.Notes,
        (PriceGroup a, PriceGroup b) => a.Deleted == b.Deleted && a.Code == b.Code && a.Name == b.Name && a.CostMultiplier == b.CostMultiplier,
        (PriceItem a, PriceItem b) => a.Deleted == b.Deleted && a.Category == b.Category && a.Name == b.Name && a.Variant == b.Variant && a.Unit == b.Unit && a.Currency == b.Currency && a.UnitCost == b.UnitCost && a.SecondaryCost == b.SecondaryCost && a.SheetWidthCm == b.SheetWidthCm && a.SheetHeightCm == b.SheetHeightCm && a.ThicknessMm == b.ThicknessMm && a.BaseMaterialPriceItemId == b.BaseMaterialPriceItemId && a.IsPrintProduct == b.IsPrintProduct && a.ServiceEnabled == b.ServiceEnabled && a.ServiceName == b.ServiceName && a.ServiceFormula == b.ServiceFormula && a.ServiceUnitCost == b.ServiceUnitCost && a.Formula == b.Formula && a.Active == b.Active && a.PriceGroupId == b.PriceGroupId && a.SpecialProfitPercent == b.SpecialProfitPercent && JsonSerializer.Serialize(a.GroupProfitPercentOverrides) == JsonSerializer.Serialize(b.GroupProfitPercentOverrides),
        (Order a, Order b) => a.Deleted == b.Deleted && a.Date == b.Date && a.CustomerId == b.CustomerId && a.Description == b.Description && a.Material == b.Material && a.WidthCm == b.WidthCm && a.HeightCm == b.HeightCm && a.AreaM2 == b.AreaM2 && a.LengthMeter == b.LengthMeter && a.DurationMinutes == b.DurationMinutes && a.Quantity == b.Quantity && a.ExchangeRate == b.ExchangeRate && a.CostTotalTl == b.CostTotalTl && a.SaleTotalTl == b.SaleTotalTl && a.PriceGroupId == b.PriceGroupId && a.AlternativePercent == b.AlternativePercent && JsonSerializer.Serialize(a.Lines) == JsonSerializer.Serialize(b.Lines),
        (Payment a, Payment b) => a.Deleted == b.Deleted && a.Date == b.Date && a.CustomerId == b.CustomerId && a.AmountTl == b.AmountTl && a.Description == b.Description && a.PaymentType == b.PaymentType,
        _ => false
    };

    private void ArchiveUsedUndo(string reason)
    {
        MoveCurrentUndoTo(Path.Combine(RootPath, "GeriAl", "Kullanildi"), reason);
    }

    private void MoveCurrentUndoTo(string directory, string reason)
    {
        if (!File.Exists(UndoFile)) return;
        Directory.CreateDirectory(directory);
        var stem = Path.Combine(directory, $"geri-al-{DateTime.Now:yyyyMMdd-HHmmssfff}-{Guid.NewGuid():N}");
        File.Move(UndoFile, stem + ".json", true);
        if (File.Exists(UndoFile + ".sha256")) File.Move(UndoFile + ".sha256", stem + ".json.sha256", true);
        if (File.Exists(UndoReasonFile)) File.Move(UndoReasonFile, stem + ".txt", true);
        else File.WriteAllText(stem + ".txt", reason);
    }

    private void PromotePreviousUndo()
    {
        var historyDir = Path.Combine(RootPath, "GeriAl", "Gecmis");
        if (!Directory.Exists(historyDir)) return;
        var previous = Directory.GetFiles(historyDir, "*.json")
            .Where(VerifyChecksum)
            .OrderByDescending(File.GetLastWriteTimeUtc)
            .FirstOrDefault();
        if (previous is null) return;
        File.Move(previous, UndoFile, true);
        if (File.Exists(previous + ".sha256")) File.Move(previous + ".sha256", UndoFile + ".sha256", true);
        var reasonFile = Path.ChangeExtension(previous, ".txt");
        if (File.Exists(reasonFile)) File.Move(reasonFile, UndoReasonFile, true);
    }

    private static void WriteChecksum(string path)
    {
        if (!File.Exists(path)) return;
        WriteAtomic(path + ".sha256", FileHash(path) + "  " + Path.GetFileName(path));
    }

    private static bool VerifyChecksum(string path)
    {
        var checksumPath = path + ".sha256";
        if (!File.Exists(checksumPath)) return true;
        var expected = File.ReadAllText(checksumPath).Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries).FirstOrDefault() ?? "";
        return expected.Length == 64 && expected.Equals(FileHash(path), StringComparison.OrdinalIgnoreCase);
    }

    private static string FileHash(string path) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path)));

    private static void WriteAtomic(string path, string text)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(path))!);
        var temp = path + ".tmp";
        File.WriteAllText(temp, text);
        File.Move(temp, path, true);
    }

    private sealed record SoftwareManifest(string Version, string Sha256, string Path, DateTime RecordedAtUtc);
    private sealed record UndoSnapshot(DateTime CapturedAtUtc, string Reason, AppState State);
    private sealed record FullBackupManifest(int FormatVersion, DateTime CreatedAtUtc, string SourceComputer, string DataSha256);

    public async Task AppendLogAsync(string text)
    {
        var line = $"{DateTime.Now:yyyy-MM-dd HH:mm:ss} | {text}{Environment.NewLine}";
        await File.AppendAllTextAsync(Path.Combine(RootPath, "btakip.log"), line).ConfigureAwait(false);
    }

    public IEnumerable<(string Id, DateTime Date, string Type, string Description, string Material, string Measure, decimal Debit, decimal Credit)> GetLedger(string customerId)
    {
        var orders = State.Orders.Where(x => !x.Deleted && x.CustomerId == customerId)
            .Select(x => (Id: x.Id, Date: x.Date, Type: "Satış", Description: x.Description, Material: GetOrderMaterial(x), Measure: GetOrderMeasure(x), Debit: x.SaleTotalTl, Credit: 0m));
        var payments = State.Payments.Where(x => !x.Deleted && x.CustomerId == customerId)
            .Select(x => (Id: x.Id, Date: x.Date, Type: "Tahsilat", Description: x.Description, Material: "", Measure: "", Debit: 0m, Credit: x.AmountTl));
        return orders.Concat(payments).OrderBy(x => x.Date).ThenBy(x => x.Type);
    }

    public decimal GetBalance(string customerId) => GetLedger(customerId).Sum(x => x.Debit - x.Credit);

    private static string GetOrderMeasure(Order order)
    {
        if (order.WidthCm > 0 && order.HeightCm > 0)
            return $"{order.WidthCm:0.##} × {order.HeightCm:0.##} cm";
        if (order.AreaM2 > 0)
            return $"{order.AreaM2:0.##} m²";
        if (order.LengthMeter > 0)
            return $"{order.LengthMeter:0.##} m";
        const string marker = "Ölçü:";
        var markerIndex = order.Description.IndexOf(marker, StringComparison.OrdinalIgnoreCase);
        if (markerIndex >= 0)
        {
            var value = order.Description[(markerIndex + marker.Length)..];
            var auditIndex = value.IndexOf(" | HESAP KONTROL:", StringComparison.OrdinalIgnoreCase);
            if (auditIndex >= 0) value = value[..auditIndex];
            value = value.Trim().Trim('—').Trim();
            if (value.Length > 0) return value;
        }

        return "";
    }

    private static string GetOrderMaterial(Order order) => string.IsNullOrWhiteSpace(order.Material) ? InferMaterial(order, []) : order.Material;

    private static string InferMaterial(Order order, List<PriceItem> prices)
    {
        if (order.Lines.Count > 0) return string.Join(" + ", order.Lines.Select(x => x.Name).Distinct());
        var matched = prices.Where(x => !x.Deleted && order.Description.Contains(x.Name, StringComparison.OrdinalIgnoreCase)).Select(x => x.Name).Distinct().ToList();
        if (matched.Count > 0) return string.Join(" + ", matched);
        var first = order.Description.Split([" — ", " | "], StringSplitOptions.RemoveEmptyEntries).FirstOrDefault() ?? "";
        return first.Trim();
    }
}

public static class SeedData
{
    public static AppState Create()
    {
        var state = new AppState();
        var device = state.DeviceId;
        state.PriceGroups =
        [
            Group("dealer", "Reklamcı / Fason", 2.00m, device),
            Group("regular", "Sürekli Müşteri", 2.80m, device),
            Group("trades", "Çevre Esnafı", 3.00m, device),
            Group("retail", "Perakende", 4.00m, device)
        ];

        state.PriceItems =
        [
            Item("Malzeme", "Folyo", "Eko", "m²", "TL", 50m, PricingFormula.SquareMeter, device),
            Item("Malzeme", "Folyo", "Orafol", "m²", "TL", 67.5m, PricingFormula.SquareMeter, device),
            Item("Malzeme", "Branda", "Eko", "m²", "TL", 50m, PricingFormula.SquareMeter, device),
            Item("Malzeme", "Branda", "Normal", "m²", "TL", 67.5m, PricingFormula.SquareMeter, device),
            Item("Malzeme", "Branda", "Arkası Siyah", "m²", "TL", 75m, PricingFormula.SquareMeter, device),
            Item("Malzeme", "OWV", "", "m²", "TL", 75m, PricingFormula.SquareMeter, device),
            Item("Malzeme", "Kumlama", "", "m²", "TL", 75m, PricingFormula.SquareMeter, device),
            Sheet("Malzeme", "Dekota", "3 mm 156×305", "USD", 19m, 156m, 305m, device),
            Sheet("Malzeme", "Dekota", "5 mm 156×305", "USD", 33m, 156m, 305m, device),
            Sheet("Malzeme", "Pleksi", "3 mm Yeşil 135×200", "USD", 80m, 135m, 200m, device),
            Sheet("Malzeme", "Pleksi", "3 mm Bordo 135×200", "USD", 82m, 135m, 200m, device),
            Sheet("Malzeme", "Pleksi", "3 mm Siyah 135×200", "USD", 58m, 135m, 200m, device),
            Sheet("Malzeme", "Pleksi", "3 mm Şeffaf 135×200", "USD", 52m, 135m, 200m, device),
            Item("Baskı", "UV Baskı", "Malzeme hariç 60×90", "tabla", "TL", 450m, PricingFormula.UvTable, device),
            Dtf(device),
            Item("Hizmet", "Sıvama", "", "m²", "TL", 100m, PricingFormula.SquareMeter, device),
            Item("Hizmet", "Lazer Kesim", "200 TL/saat", "dakika", "TL", 200m / 60m, PricingFormula.Minute, device),
            Item("Malzeme", "Plotter Kesim", "Folyo maliyetine %50", "%", "%", 50m, PricingFormula.PercentMaterial, device)
        ];
        return state;
    }

    private static PriceGroup Group(string code, string name, decimal multiplier, string device) => new()
    {
        Id = code, Code = code, Name = name, CostMultiplier = multiplier, DeviceId = device
    };

    private static PriceItem Item(string category, string name, string variant, string unit, string currency,
        decimal cost, string formula, string device) => new()
    {
        Category = category, Name = name, Variant = variant, Unit = unit, Currency = currency,
        UnitCost = cost, Formula = formula, DeviceId = device
    };

    private static PriceItem Sheet(string category, string name, string variant, string currency, decimal cost,
        decimal width, decimal height, string device)
    {
        var item = Item(category, name, variant, "levha", currency, cost, PricingFormula.SheetArea, device);
        item.SheetWidthCm = width;
        item.SheetHeightCm = height;
        return item;
    }

    private static PriceItem Dtf(string device)
    {
        var item = Item("Baskı", "DTF Baskı", "58 cm en — 10 m üstü indirimli", "metre", "USD", 5m, PricingFormula.DtfTier, device);
        item.SecondaryCost = 2.5m;
        return item;
    }
}

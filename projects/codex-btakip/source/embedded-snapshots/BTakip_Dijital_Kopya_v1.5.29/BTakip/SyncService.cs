using System.Net.Http.Json;
using System.Text.Json;

namespace BTakip;

public sealed class SyncStatus
{
    public bool Success { get; set; }
    public bool Changed { get; set; }
    public string Message { get; set; } = "";
    public int Sent { get; set; }
    public int Received { get; set; }
}

public sealed class SyncService : IDisposable
{
    private readonly DataStore _store;
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromSeconds(20) };
    private readonly SemaphoreSlim _gate = new(1, 1);
    public Func<ConflictRecord, Task<ConflictDecision>>? ConflictResolver { get; set; }

    public SyncService(DataStore store) => _store = store;

    public async Task<SyncStatus> SyncAsync(CancellationToken cancellationToken = default)
    {
        var cfg = _store.State.Settings;
        if (string.IsNullOrWhiteSpace(cfg.GoogleWebAppUrl) || string.IsNullOrWhiteSpace(cfg.GoogleSyncToken))
            return new SyncStatus { Message = "Google bağlantısı henüz yapılandırılmadı." };
        if (!await _gate.WaitAsync(0, cancellationToken))
            return new SyncStatus { Message = "Senkronizasyon zaten çalışıyor." };

        try
        {
            var result = new SyncStatus();
            var statusUrl = AddQuery(cfg.GoogleWebAppUrl,
                $"action=pull&token={Uri.EscapeDataString(cfg.GoogleSyncToken)}&since={Uri.EscapeDataString(cfg.LastGoogleChangeToken)}");
            using var pullResponse = await _http.GetAsync(statusUrl, cancellationToken);
            pullResponse.EnsureSuccessStatusCode();
            var pullText = await pullResponse.Content.ReadAsStringAsync(cancellationToken);
            var pull = JsonSerializer.Deserialize<ApiResponse>(pullText, JsonOptions())
                       ?? throw new InvalidOperationException("Google boş yanıt verdi.");
            if (!pull.Ok) throw new InvalidOperationException(pull.Error ?? "Google verisi okunamadı.");

            if (pull.Records is not null)
            {
                foreach (var record in pull.Records)
                {
                    if (await ApplyRemoteAsync(record)) result.Received++;
                }
            }

            cfg.LastGoogleChangeToken = pull.ChangeToken ?? cfg.LastGoogleChangeToken;

            var localChanges = AllEntities().Where(x => x.Entity.Revision > x.Entity.SyncedRevision).ToList();
            if (localChanges.Count > 0)
            {
                var pushPayload = new
                {
                    token = cfg.GoogleSyncToken,
                    action = "push",
                    deviceId = _store.State.DeviceId,
                    records = localChanges.Select(x => new { type = x.Type, data = x.Entity })
                };
                using var pushResponse = await _http.PostAsJsonAsync(cfg.GoogleWebAppUrl, pushPayload, cancellationToken);
                pushResponse.EnsureSuccessStatusCode();
                var push = await pushResponse.Content.ReadFromJsonAsync<ApiResponse>(cancellationToken: cancellationToken)
                           ?? throw new InvalidOperationException("Google boş yanıt verdi.");
                if (!push.Ok) throw new InvalidOperationException(push.Error ?? "Google kayıt kabul etmedi.");
                foreach (var x in localChanges) x.Entity.SyncedRevision = x.Entity.Revision;
                result.Sent = localChanges.Count;
                cfg.LastGoogleChangeToken = push.ChangeToken ?? cfg.LastGoogleChangeToken;
            }

            cfg.LastSyncUtc = DateTime.UtcNow;
            result.Success = true;
            result.Changed = result.Sent + result.Received > 0;
            result.Message = result.Changed
                ? $"Senkron tamamlandı: {result.Sent} gönderildi, {result.Received} alındı."
                : "Google ile güncel.";
            await _store.SaveAsync("Google senkronizasyonu");
            return result;
        }
        catch (Exception ex)
        {
            await _store.AppendLogAsync("SENKRON HATA | " + ex.Message);
            return new SyncStatus { Message = "Senkron yapılamadı: " + ex.Message };
        }
        finally
        {
            _gate.Release();
        }
    }

    private async Task<bool> ApplyRemoteAsync(RemoteRecord remote)
    {
        var incoming = DeserializeEntity(remote.Type, remote.Data);
        if (incoming is null || string.IsNullOrWhiteSpace(incoming.Id)) return false;
        var local = FindEntity(remote.Type, incoming.Id);
        if (local is null)
        {
            incoming.SyncedRevision = incoming.Revision;
            AddEntity(remote.Type, incoming);
            return true;
        }

        var remoteNew = incoming.Revision > local.SyncedRevision || incoming.UpdatedAtUtc > local.UpdatedAtUtc;
        var localDirty = local.Revision > local.SyncedRevision;
        if (!remoteNew)
        {
            local.SyncedRevision = Math.Max(local.SyncedRevision, incoming.Revision);
            return false;
        }

        if (localDirty && !Equivalent(local, incoming))
        {
            var conflict = new ConflictRecord
            {
                EntityType = remote.Type,
                EntityId = incoming.Id,
                LocalJson = JsonSerializer.Serialize(local, local.GetType(), JsonOptions()),
                RemoteJson = JsonSerializer.Serialize(incoming, incoming.GetType(), JsonOptions())
            };
            _store.State.Conflicts.Add(conflict);
            var decision = ConflictResolver is null ? ConflictDecision.Skip : await ConflictResolver(conflict);
            switch (decision)
            {
                case ConflictDecision.UseGoogle:
                    incoming.SyncedRevision = incoming.Revision;
                    ReplaceEntity(remote.Type, incoming);
                    return true;
                case ConflictDecision.UsePc:
                    local.Revision = Math.Max(local.Revision, incoming.Revision) + 1;
                    local.UpdatedAtUtc = DateTime.UtcNow;
                    return false;
                case ConflictDecision.KeepBoth:
                    incoming.Id = Guid.NewGuid().ToString("N");
                    incoming.Revision = 1;
                    incoming.SyncedRevision = 0;
                    incoming.DeviceId = _store.State.DeviceId;
                    incoming.UpdatedAtUtc = DateTime.UtcNow;
                    AddEntity(remote.Type, incoming);
                    return true;
                default:
                    return false;
            }
        }

        incoming.SyncedRevision = incoming.Revision;
        ReplaceEntity(remote.Type, incoming);
        return true;
    }

    public async Task<decimal?> FetchTcmbUsdRateAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            var xml = await _http.GetStringAsync("https://www.tcmb.gov.tr/kurlar/today.xml", cancellationToken);
            var doc = System.Xml.Linq.XDocument.Parse(xml);
            var usd = doc.Descendants("Currency").FirstOrDefault(x => (string?)x.Attribute("CurrencyCode") == "USD");
            var text = usd?.Element("ForexSelling")?.Value;
            if (decimal.TryParse(text, System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out var rate))
                return rate;
        }
        catch (Exception ex) { await _store.AppendLogAsync("KUR HATA | " + ex.Message); }
        return null;
    }

    private IEnumerable<(string Type, SyncEntity Entity)> AllEntities()
    {
        foreach (var x in _store.State.Customers) yield return ("customers", x);
        foreach (var x in _store.State.PriceGroups) yield return ("price_groups", x);
        foreach (var x in _store.State.PriceItems) yield return ("price_items", x);
        foreach (var x in _store.State.Orders) yield return ("orders", x);
        foreach (var x in _store.State.Payments) yield return ("payments", x);
    }

    private SyncEntity? FindEntity(string type, string id) => type switch
    {
        "customers" => _store.State.Customers.FirstOrDefault(x => x.Id == id),
        "price_groups" => _store.State.PriceGroups.FirstOrDefault(x => x.Id == id),
        "price_items" => _store.State.PriceItems.FirstOrDefault(x => x.Id == id),
        "orders" => _store.State.Orders.FirstOrDefault(x => x.Id == id),
        "payments" => _store.State.Payments.FirstOrDefault(x => x.Id == id),
        _ => null
    };

    private void AddEntity(string type, SyncEntity entity)
    {
        switch (type)
        {
            case "customers": _store.State.Customers.Add((Customer)entity); break;
            case "price_groups": _store.State.PriceGroups.Add((PriceGroup)entity); break;
            case "price_items": _store.State.PriceItems.Add((PriceItem)entity); break;
            case "orders": _store.State.Orders.Add((Order)entity); break;
            case "payments": _store.State.Payments.Add((Payment)entity); break;
        }
    }

    private void ReplaceEntity(string type, SyncEntity entity)
    {
        switch (type)
        {
            case "customers": Replace(_store.State.Customers, (Customer)entity); break;
            case "price_groups": Replace(_store.State.PriceGroups, (PriceGroup)entity); break;
            case "price_items": Replace(_store.State.PriceItems, (PriceItem)entity); break;
            case "orders": Replace(_store.State.Orders, (Order)entity); break;
            case "payments": Replace(_store.State.Payments, (Payment)entity); break;
        }
    }

    private static void Replace<T>(List<T> list, T entity) where T : SyncEntity
    {
        var index = list.FindIndex(x => x.Id == entity.Id);
        if (index >= 0) list[index] = entity; else list.Add(entity);
    }

    private static SyncEntity? DeserializeEntity(string type, JsonElement json) => type switch
    {
        "customers" => json.Deserialize<Customer>(JsonOptions()),
        "price_groups" => json.Deserialize<PriceGroup>(JsonOptions()),
        "price_items" => json.Deserialize<PriceItem>(JsonOptions()),
        "orders" => json.Deserialize<Order>(JsonOptions()),
        "payments" => json.Deserialize<Payment>(JsonOptions()),
        _ => null
    };

    private static bool Equivalent(SyncEntity a, SyncEntity b)
    {
        var x = JsonSerializer.Serialize(a, a.GetType(), JsonOptions()).Replace($"\"SyncedRevision\":{a.SyncedRevision}", "\"SyncedRevision\":0");
        var y = JsonSerializer.Serialize(b, b.GetType(), JsonOptions()).Replace($"\"SyncedRevision\":{b.SyncedRevision}", "\"SyncedRevision\":0");
        return x == y;
    }

    private static string AddQuery(string url, string query) => url + (url.Contains('?') ? "&" : "?") + query;
    private static JsonSerializerOptions JsonOptions() => new() { PropertyNameCaseInsensitive = true };
    public void Dispose() { _http.Dispose(); _gate.Dispose(); }

    private sealed class ApiResponse
    {
        public bool Ok { get; set; }
        public string? Error { get; set; }
        public string? ChangeToken { get; set; }
        public List<RemoteRecord>? Records { get; set; }
    }

    private sealed class RemoteRecord
    {
        public string Type { get; set; } = "";
        public JsonElement Data { get; set; }
    }
}

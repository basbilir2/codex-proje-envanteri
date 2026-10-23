using System.Diagnostics;
using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace BTakip;

public sealed class CloudSyncResult
{
    public bool Success { get; set; }
    public bool Changed { get; set; }
    public int Sent { get; set; }
    public int Received { get; set; }
    public string Message { get; set; } = "";
}

public sealed record CloudAccountInfo(string Id, string Email);

public sealed class GoogleCloudSyncService : IDisposable
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    private readonly DataStore _store;
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromSeconds(45) };
    private readonly SemaphoreSlim _gate = new(1, 1);
    private readonly string _sessionPath;
    private CloudSession? _session;

    public Func<ConflictRecord, Task<ConflictDecision>>? ConflictResolver { get; set; }
    public bool IsConfigured => CloudConfiguration.IsConfigured;
    public bool IsConnected => _session is not null;
    public string AccountEmail => _session?.Email ?? "";

    public GoogleCloudSyncService(DataStore store)
    {
        _store = store;
        _sessionPath = Path.Combine(store.RootPath, "bulut-oturumu.dat");
    }

    public async Task<CloudAccountInfo?> TryRestoreSessionAsync(CancellationToken cancellationToken = default)
    {
        if (!IsConfigured) return null;
        _session = LoadSession();
        if (_session is null) return null;
        try
        {
            await EnsureGoogleTokenAsync(cancellationToken).ConfigureAwait(false);
            await EnsureFirebaseTokenAsync(cancellationToken).ConfigureAwait(false);
            await _store.ActivateCloudAccountAsync(_session.Uid, _session.Email).ConfigureAwait(false);
            return new CloudAccountInfo(_session.Uid, _session.Email);
        }
        catch
        {
            _session = null;
            return null;
        }
    }

    public async Task<CloudAccountInfo> ConnectAsync(CancellationToken cancellationToken = default)
    {
        if (!IsConfigured) throw new InvalidOperationException("BTakip bulut bağlantısı henüz yapılandırılmadı.");
        var oauth = await AuthorizeGoogleAsync(cancellationToken).ConfigureAwait(false);
        var firebase = await SignInFirebaseAsync(oauth.IdToken, cancellationToken).ConfigureAwait(false);
        _session = new CloudSession
        {
            GoogleAccessToken = oauth.AccessToken,
            GoogleRefreshToken = oauth.RefreshToken,
            GoogleExpiresUtc = DateTime.UtcNow.AddSeconds(oauth.ExpiresIn),
            FirebaseIdToken = firebase.IdToken,
            FirebaseRefreshToken = firebase.RefreshToken,
            FirebaseExpiresUtc = DateTime.UtcNow.AddSeconds(ParseSeconds(firebase.ExpiresIn)),
            Uid = firebase.LocalId,
            Email = string.IsNullOrWhiteSpace(firebase.Email) ? ReadJwtClaim(oauth.IdToken, "email") : firebase.Email
        };
        SaveSession();
        await _store.ActivateCloudAccountAsync(_session.Uid, _session.Email).ConfigureAwait(false);
        return new CloudAccountInfo(_session.Uid, _session.Email);
    }

    public void Disconnect()
    {
        _session = null;
        try { if (File.Exists(_sessionPath)) File.Delete(_sessionPath); } catch { }
    }

    public async Task RestoreLatestDriveBackupAsync(CancellationToken cancellationToken = default)
    {
        if (_session is null) throw new InvalidOperationException("Önce Google hesabını bağlayın.");
        await EnsureGoogleTokenAsync(cancellationToken).ConfigureAwait(false);
        await EnsureFirebaseTokenAsync(cancellationToken).ConfigureAwait(false);
        var key = await EnsureBackupKeyAsync(cancellationToken).ConfigureAwait(false);
        var folderId = await EnsureDriveBackupFolderAsync(cancellationToken).ConfigureAwait(false);
        var fileId = await FindDriveFileAsync($"name='BTakip-Son.btakip.enc' and '{folderId}' in parents and trashed=false", cancellationToken).ConfigureAwait(false);
        if (string.IsNullOrWhiteSpace(fileId)) throw new FileNotFoundException("Google Drive'da BTakip yedeği bulunamadı.");
        using var response = await SendGoogleAsync(HttpMethod.Get, $"https://www.googleapis.com/drive/v3/files/{fileId}?alt=media", null, cancellationToken).ConfigureAwait(false);
        var encrypted = await response.Content.ReadAsByteArrayAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode) throw new InvalidOperationException("Drive yedeği indirilemedi.");
        var plain = DecryptBackup(encrypted, key, _session.Uid);
        var temp = Path.Combine(Path.GetTempPath(), "BTakip-Bulut-" + Guid.NewGuid().ToString("N") + ".btakip");
        try
        {
            await File.WriteAllBytesAsync(temp, plain, cancellationToken).ConfigureAwait(false);
            _store.CaptureUndo("Google Drive yedeği geri yüklendi");
            await _store.ImportFullBackupAsync(temp).ConfigureAwait(false);
            _store.State.Settings.CloudAccountId = _session.Uid;
            _store.State.Settings.CloudAccountEmail = _session.Email;
            _store.State.Settings.CloudBootstrapComplete = true;
            _store.State.Settings.LastFirestorePullUtc = DateTime.UtcNow;
            foreach (var item in AllEntities())
            {
                _store.Touch(item.Entity);
                item.Entity.SyncedRevision = 0;
            }
            await _store.SaveAsync("Google Drive şifreli yedeği geri yüklendi").ConfigureAwait(false);
        }
        finally { try { if (File.Exists(temp)) File.Delete(temp); } catch { } }
    }

    public async Task<CloudSyncResult> SyncAsync(CancellationToken cancellationToken = default)
    {
        if (_session is null) return new CloudSyncResult { Message = "Google hesabı bağlı değil." };
        if (!await _gate.WaitAsync(0, cancellationToken).ConfigureAwait(false))
            return new CloudSyncResult { Message = "Bulut eşitlemesi zaten çalışıyor." };

        try
        {
            await EnsureFirebaseTokenAsync(cancellationToken).ConfigureAwait(false);
            var result = new CloudSyncResult();
            var initialRestore = !_store.State.Settings.CloudBootstrapComplete;
            result.Received = await PullFirestoreAsync(initialRestore, cancellationToken).ConfigureAwait(false);
            result.Sent = await PushFirestoreAsync(cancellationToken).ConfigureAwait(false);
            _store.State.Settings.CloudBootstrapComplete = true;
            _store.State.Settings.LastSyncUtc = DateTime.UtcNow;
            result.Changed = result.Sent + result.Received > 0;
            var warnings = new List<string>();

            if (result.Changed || !_store.State.Settings.LastSheetMirrorUtc.HasValue ||
                DateTime.UtcNow - _store.State.Settings.LastSheetMirrorUtc.Value > TimeSpan.FromMinutes(5))
            {
                try
                {
                    await MirrorToSheetsAsync(cancellationToken).ConfigureAwait(false);
                    _store.State.Settings.LastSheetMirrorUtc = DateTime.UtcNow;
                }
                catch (Exception ex)
                {
                    warnings.Add("Sheets bekliyor: " + ex.Message);
                    await _store.AppendLogAsync("SHEETS YEDEK HATA | " + ex.Message).ConfigureAwait(false);
                }
            }

            if (!_store.State.Settings.LastCloudBackupUtc.HasValue ||
                _store.State.Settings.LastCloudBackupUtc.Value.ToLocalTime().Date != DateTime.Today)
            {
                try
                {
                    await UploadEncryptedDriveBackupAsync(cancellationToken).ConfigureAwait(false);
                    _store.State.Settings.LastCloudBackupUtc = DateTime.UtcNow;
                }
                catch (Exception ex)
                {
                    warnings.Add("Drive yedeği bekliyor: " + ex.Message);
                    await _store.AppendLogAsync("DRIVE YEDEK HATA | " + ex.Message).ConfigureAwait(false);
                }
            }

            await _store.SaveAsync("Firebase, Google Sheets ve Drive eşitlemesi").ConfigureAwait(false);
            result.Success = true;
            var mainMessage = result.Changed
                ? $"Bulut güncel: {result.Sent} gönderildi, {result.Received} alındı."
                : "Firebase, Google Sheets, Drive ve yerel kayıt güncel.";
            result.Message = warnings.Count == 0 ? mainMessage : mainMessage + Environment.NewLine + string.Join(Environment.NewLine, warnings);
            return result;
        }
        catch (Exception ex)
        {
            await _store.AppendLogAsync("BULUT SENKRON HATA | " + ex.Message).ConfigureAwait(false);
            return new CloudSyncResult { Message = "Bulut eşitlemesi yapılamadı: " + ex.Message };
        }
        finally { _gate.Release(); }
    }

    private async Task<OAuthTokenResponse> AuthorizeGoogleAsync(CancellationToken cancellationToken)
    {
        var verifier = Base64Url(RandomNumberGenerator.GetBytes(48));
        var challenge = Base64Url(SHA256.HashData(Encoding.ASCII.GetBytes(verifier)));
        var state = Base64Url(RandomNumberGenerator.GetBytes(24));
        var port = GetFreeTcpPort();
        var redirect = $"http://127.0.0.1:{port}/";
        using var listener = new HttpListener();
        listener.Prefixes.Add(redirect);
        listener.Start();

        var scope = "openid email profile https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/spreadsheets";
        var authUrl = "https://accounts.google.com/o/oauth2/v2/auth?" + Query(new Dictionary<string, string>
        {
            ["client_id"] = CloudConfiguration.GoogleClientId,
            ["redirect_uri"] = redirect,
            ["response_type"] = "code",
            ["scope"] = scope,
            ["access_type"] = "offline",
            ["prompt"] = "select_account consent",
            ["include_granted_scopes"] = "true",
            ["code_challenge"] = challenge,
            ["code_challenge_method"] = "S256",
            ["state"] = state
        });
        Process.Start(new ProcessStartInfo(authUrl) { UseShellExecute = true });

        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(TimeSpan.FromMinutes(5));
        var context = await listener.GetContextAsync().WaitAsync(timeout.Token).ConfigureAwait(false);
        var query = context.Request.QueryString;
        var html = "<html><body style='font-family:Segoe UI;padding:36px'><h2>BTakip bağlantısı tamamlandı.</h2><p>Bu pencereyi kapatabilirsiniz.</p></body></html>";
        var bytes = Encoding.UTF8.GetBytes(html);
        context.Response.ContentType = "text/html; charset=utf-8";
        context.Response.ContentLength64 = bytes.Length;
        await context.Response.OutputStream.WriteAsync(bytes, timeout.Token).ConfigureAwait(false);
        context.Response.Close();
        listener.Stop();

        if (!string.IsNullOrWhiteSpace(query["error"])) throw new InvalidOperationException("Google girişi iptal edildi: " + query["error"]);
        if (!state.Equals(query["state"], StringComparison.Ordinal)) throw new InvalidOperationException("Google giriş doğrulaması eşleşmedi.");
        var code = query["code"] ?? throw new InvalidOperationException("Google giriş kodu alınamadı.");

        using var response = await _http.PostAsync("https://oauth2.googleapis.com/token", new FormUrlEncodedContent(new Dictionary<string, string>
        {
            ["client_id"] = CloudConfiguration.GoogleClientId,
            ["client_secret"] = CloudConfiguration.GoogleClientSecret,
            ["code"] = code,
            ["code_verifier"] = verifier,
            ["grant_type"] = "authorization_code",
            ["redirect_uri"] = redirect
        }), cancellationToken).ConfigureAwait(false);
        var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode) throw new InvalidOperationException("Google oturumu açılamadı: " + ErrorMessage(text));
        var token = JsonSerializer.Deserialize<OAuthTokenResponse>(text, JsonOptions) ?? throw new InvalidOperationException("Google oturum yanıtı okunamadı.");
        if (string.IsNullOrWhiteSpace(token.IdToken) || string.IsNullOrWhiteSpace(token.RefreshToken))
            throw new InvalidOperationException("Google uzun süreli bağlantı izni alınamadı.");
        return token;
    }

    private async Task<FirebaseSignInResponse> SignInFirebaseAsync(string googleIdToken, CancellationToken cancellationToken)
    {
        var url = $"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={Uri.EscapeDataString(CloudConfiguration.FirebaseApiKey)}";
        var payload = new
        {
            postBody = "id_token=" + Uri.EscapeDataString(googleIdToken) + "&providerId=google.com",
            requestUri = "http://localhost",
            returnIdpCredential = true,
            returnSecureToken = true
        };
        using var response = await _http.PostAsJsonAsync(url, payload, cancellationToken).ConfigureAwait(false);
        var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode) throw new InvalidOperationException("Firebase hesabı açılamadı: " + ErrorMessage(text));
        return JsonSerializer.Deserialize<FirebaseSignInResponse>(text, JsonOptions) ?? throw new InvalidOperationException("Firebase oturum yanıtı okunamadı.");
    }

    private async Task EnsureGoogleTokenAsync(CancellationToken cancellationToken)
    {
        if (_session is null) throw new InvalidOperationException("Google hesabı bağlı değil.");
        if (_session.GoogleExpiresUtc > DateTime.UtcNow.AddMinutes(3)) return;
        using var response = await _http.PostAsync("https://oauth2.googleapis.com/token", new FormUrlEncodedContent(new Dictionary<string, string>
        {
            ["client_id"] = CloudConfiguration.GoogleClientId,
            ["client_secret"] = CloudConfiguration.GoogleClientSecret,
            ["refresh_token"] = _session.GoogleRefreshToken,
            ["grant_type"] = "refresh_token"
        }), cancellationToken).ConfigureAwait(false);
        var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode) throw new InvalidOperationException("Google oturumu yenilenemedi: " + ErrorMessage(text));
        var token = JsonSerializer.Deserialize<OAuthTokenResponse>(text, JsonOptions) ?? throw new InvalidOperationException("Google yenileme yanıtı okunamadı.");
        _session.GoogleAccessToken = token.AccessToken;
        _session.GoogleExpiresUtc = DateTime.UtcNow.AddSeconds(token.ExpiresIn);
        SaveSession();
    }

    private async Task EnsureFirebaseTokenAsync(CancellationToken cancellationToken)
    {
        if (_session is null) throw new InvalidOperationException("Google hesabı bağlı değil.");
        if (_session.FirebaseExpiresUtc > DateTime.UtcNow.AddMinutes(3)) return;
        var url = $"https://securetoken.googleapis.com/v1/token?key={Uri.EscapeDataString(CloudConfiguration.FirebaseApiKey)}";
        using var response = await _http.PostAsync(url, new FormUrlEncodedContent(new Dictionary<string, string>
        {
            ["grant_type"] = "refresh_token",
            ["refresh_token"] = _session.FirebaseRefreshToken
        }), cancellationToken).ConfigureAwait(false);
        var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode) throw new InvalidOperationException("Firebase oturumu yenilenemedi: " + ErrorMessage(text));
        var token = JsonSerializer.Deserialize<FirebaseRefreshResponse>(text, JsonOptions) ?? throw new InvalidOperationException("Firebase yenileme yanıtı okunamadı.");
        _session.FirebaseIdToken = token.IdToken;
        _session.FirebaseRefreshToken = token.RefreshToken;
        _session.FirebaseExpiresUtc = DateTime.UtcNow.AddSeconds(ParseSeconds(token.ExpiresIn));
        SaveSession();
    }

    private async Task<int> PullFirestoreAsync(bool initialRestore, CancellationToken cancellationToken)
    {
        if (_session is null) return 0;
        var documents = new List<JsonElement>();
        var parent = FirestoreBase + "/users/" + Uri.EscapeDataString(_session.Uid);
        if (!_store.State.Settings.LastFirestorePullUtc.HasValue)
        {
            string? pageToken = null;
            do
            {
                var url = parent + "/records?pageSize=300" + (string.IsNullOrWhiteSpace(pageToken) ? "" : "&pageToken=" + Uri.EscapeDataString(pageToken));
                using var response = await SendFirebaseAsync(HttpMethod.Get, url, null, cancellationToken).ConfigureAwait(false);
                if (response.StatusCode == HttpStatusCode.NotFound) break;
                var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
                if (!response.IsSuccessStatusCode) throw new InvalidOperationException("Firestore verisi okunamadı: " + ErrorMessage(text));
                using var json = JsonDocument.Parse(text);
                if (json.RootElement.TryGetProperty("documents", out var array)) documents.AddRange(array.EnumerateArray().Select(x => x.Clone()));
                pageToken = json.RootElement.TryGetProperty("nextPageToken", out var next) ? next.GetString() : null;
            } while (!string.IsNullOrWhiteSpace(pageToken));
        }
        else
        {
            var cutoff = _store.State.Settings.LastFirestorePullUtc.Value.AddMinutes(-2).ToString("O");
            var body = new
            {
                structuredQuery = new
                {
                    from = new[] { new { collectionId = "records" } },
                    where = new { fieldFilter = new { field = new { fieldPath = "updatedAtUtc" }, op = "GREATER_THAN_OR_EQUAL", value = new { timestampValue = cutoff } } },
                    orderBy = new[] { new { field = new { fieldPath = "updatedAtUtc" }, direction = "ASCENDING" } }
                }
            };
            using var content = JsonContent.Create(body);
            using var response = await SendFirebaseAsync(HttpMethod.Post, parent + ":runQuery", content, cancellationToken).ConfigureAwait(false);
            var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            if (!response.IsSuccessStatusCode) throw new InvalidOperationException("Firestore değişiklikleri okunamadı: " + ErrorMessage(text));
            using var json = JsonDocument.Parse(text);
            foreach (var row in json.RootElement.EnumerateArray())
                if (row.TryGetProperty("document", out var document)) documents.Add(document.Clone());
        }

        var pullStarted = DateTime.UtcNow;
        var received = 0;
        foreach (var document in documents)
        {
            if (!document.TryGetProperty("fields", out var fields)) continue;
            var type = FirestoreString(fields, "type");
            var entityJson = FirestoreString(fields, "json");
            if (string.IsNullOrWhiteSpace(type) || string.IsNullOrWhiteSpace(entityJson)) continue;
            var incoming = DeserializeEntity(type, entityJson);
            if (incoming is not null && await ApplyRemoteAsync(type, incoming, initialRestore).ConfigureAwait(false)) received++;
        }
        _store.State.Settings.LastFirestorePullUtc = pullStarted;
        return received;
    }

    private async Task<int> PushFirestoreAsync(CancellationToken cancellationToken)
    {
        if (_session is null) return 0;
        var changes = AllEntities().Where(x => x.Entity.Revision > x.Entity.SyncedRevision).ToList();
        foreach (var chunk in changes.Chunk(200))
        {
            var writes = chunk.Select(item =>
            {
                var fields = new Dictionary<string, object>
                {
                    ["type"] = new { stringValue = item.Type },
                    ["entityId"] = new { stringValue = item.Entity.Id },
                    ["json"] = new { stringValue = JsonSerializer.Serialize(item.Entity, item.Entity.GetType(), JsonOptions) },
                    ["revision"] = new { integerValue = item.Entity.Revision.ToString(System.Globalization.CultureInfo.InvariantCulture) },
                    ["updatedAtUtc"] = new { timestampValue = item.Entity.UpdatedAtUtc.ToUniversalTime().ToString("O") },
                    ["deviceId"] = new { stringValue = item.Entity.DeviceId }
                };
                return new { update = new { name = FirestoreDocumentName(_session.Uid, item.Type, item.Entity.Id), fields } };
            }).ToArray();
            using var content = JsonContent.Create(new { writes });
            using var response = await SendFirebaseAsync(HttpMethod.Post, FirestoreBase + ":commit", content, cancellationToken).ConfigureAwait(false);
            var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            if (!response.IsSuccessStatusCode) throw new InvalidOperationException("Firestore kayıtları gönderilemedi: " + ErrorMessage(text));
            foreach (var item in chunk) item.Entity.SyncedRevision = item.Entity.Revision;
        }
        return changes.Count;
    }

    private async Task<bool> ApplyRemoteAsync(string type, SyncEntity incoming, bool initialRestore)
    {
        var local = FindEntity(type, incoming.Id);
        if (local is null)
        {
            incoming.SyncedRevision = incoming.Revision;
            AddEntity(type, incoming);
            return true;
        }
        if (initialRestore)
        {
            incoming.SyncedRevision = incoming.Revision;
            ReplaceEntity(type, incoming);
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
                EntityType = type,
                EntityId = incoming.Id,
                LocalJson = JsonSerializer.Serialize(local, local.GetType(), JsonOptions),
                RemoteJson = JsonSerializer.Serialize(incoming, incoming.GetType(), JsonOptions)
            };
            _store.State.Conflicts.Add(conflict);
            var decision = ConflictResolver is null ? ConflictDecision.Skip : await ConflictResolver(conflict).ConfigureAwait(false);
            if (decision == ConflictDecision.UseGoogle)
            {
                incoming.SyncedRevision = incoming.Revision;
                ReplaceEntity(type, incoming);
                return true;
            }
            if (decision == ConflictDecision.UsePc)
            {
                local.Revision = Math.Max(local.Revision, incoming.Revision) + 1;
                local.UpdatedAtUtc = DateTime.UtcNow;
                return false;
            }
            if (decision == ConflictDecision.KeepBoth)
            {
                incoming.Id = Guid.NewGuid().ToString("N");
                incoming.Revision = 1;
                incoming.SyncedRevision = 0;
                incoming.DeviceId = _store.State.DeviceId;
                incoming.UpdatedAtUtc = DateTime.UtcNow;
                AddEntity(type, incoming);
                return true;
            }
            return false;
        }
        incoming.SyncedRevision = incoming.Revision;
        ReplaceEntity(type, incoming);
        return true;
    }

    private async Task MirrorToSheetsAsync(CancellationToken cancellationToken)
    {
        await EnsureGoogleTokenAsync(cancellationToken).ConfigureAwait(false);
        var spreadsheetId = await FindOrCreateSpreadsheetAsync(cancellationToken).ConfigureAwait(false);
        var titles = new[] { "Müşteriler", "Fiyat Grupları", "Fiyat Tanımları", "Siparişler", "Tahsilatlar" };
        using (var clear = JsonContent.Create(new { ranges = titles.Select(x => $"'{x}'!A:Z").ToArray() }))
        using (var response = await SendGoogleAsync(HttpMethod.Post, $"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheetId}/values:batchClear", clear, cancellationToken).ConfigureAwait(false))
        {
            var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            if (!response.IsSuccessStatusCode) throw new InvalidOperationException("Google Sheets temizlenemedi: " + ErrorMessage(text));
        }

        var data = BuildSheetRanges();
        using var content = JsonContent.Create(new { valueInputOption = "RAW", data });
        using var write = await SendGoogleAsync(HttpMethod.Post, $"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheetId}/values:batchUpdate", content, cancellationToken).ConfigureAwait(false);
        var writeText = await write.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!write.IsSuccessStatusCode) throw new InvalidOperationException("Google Sheets güncellenemedi: " + ErrorMessage(writeText));
    }

    private async Task<string> FindOrCreateSpreadsheetAsync(CancellationToken cancellationToken)
    {
        if (_session is null) throw new InvalidOperationException("Google hesabı bağlı değil.");
        var escapedUid = _session.Uid.Replace("'", "\\'");
        var query = $"mimeType='application/vnd.google-apps.spreadsheet' and trashed=false and appProperties has {{ key='btakipUid' and value='{escapedUid}' }}";
        var found = await FindDriveFileAsync(query, cancellationToken).ConfigureAwait(false);
        if (!string.IsNullOrWhiteSpace(found)) return found;

        var body = new
        {
            properties = new { title = "BTakip Veri" },
            sheets = new[] { "Müşteriler", "Fiyat Grupları", "Fiyat Tanımları", "Siparişler", "Tahsilatlar" }
                .Select(title => new { properties = new { title } }).ToArray()
        };
        using var content = JsonContent.Create(body);
        using var response = await SendGoogleAsync(HttpMethod.Post, "https://sheets.googleapis.com/v4/spreadsheets", content, cancellationToken).ConfigureAwait(false);
        var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode) throw new InvalidOperationException("BTakip Google tablosu oluşturulamadı: " + ErrorMessage(text));
        using var json = JsonDocument.Parse(text);
        var id = json.RootElement.GetProperty("spreadsheetId").GetString() ?? throw new InvalidOperationException("Google tablo kimliği alınamadı.");
        using var metadata = JsonContent.Create(new { appProperties = new Dictionary<string, string> { ["btakipUid"] = _session.Uid, ["btakipRole"] = "mirror" } });
        using var update = await SendGoogleAsync(new HttpMethod("PATCH"), $"https://www.googleapis.com/drive/v3/files/{id}?fields=id", metadata, cancellationToken).ConfigureAwait(false);
        update.EnsureSuccessStatusCode();
        return id;
    }

    private object[] BuildSheetRanges()
    {
        var state = _store.State;
        static object Range(string title, IEnumerable<object?[]> rows) => new { range = $"'{title}'!A1", majorDimension = "ROWS", values = rows };
        static string D(DateTime value) => value.ToLocalTime().ToString("dd.MM.yyyy HH:mm:ss");
        static string N(decimal value) => value.ToString("0.####", System.Globalization.CultureInfo.InvariantCulture);

        var customers = new List<object?[]> { new object?[] { "Kayıt Kimliği", "Ad", "Firma", "Telefon", "E-posta", "Fiyat Grubu", "Not", "Silindi", "Sürüm", "Güncelleme" } };
        customers.AddRange(state.Customers.Select(x => new object?[] { x.Id, x.Name, x.Company, x.Phone, x.Email, x.PriceGroupId, x.Notes, x.Deleted, x.Revision, D(x.UpdatedAtUtc) }));
        var groups = new List<object?[]> { new object?[] { "Kayıt Kimliği", "Kod", "Ad", "Maliyet Çarpanı", "Silindi", "Sürüm", "Güncelleme" } };
        groups.AddRange(state.PriceGroups.Select(x => new object?[] { x.Id, x.Code, x.Name, N(x.CostMultiplier), x.Deleted, x.Revision, D(x.UpdatedAtUtc) }));
        var prices = new List<object?[]> { new object?[] { "Kayıt Kimliği", "Tür", "Ad", "Varyant", "Birim", "Para", "Alış", "İkinci Maliyet", "Hesap", "Levha En", "Levha Boy", "Kalınlık", "Temel Malzeme", "Grup Kârları", "Aktif", "Silindi", "Sürüm", "Güncelleme" } };
        prices.AddRange(state.PriceItems.Select(x => new object?[] { x.Id, x.Category, x.Name, x.Variant, x.Unit, x.Currency, N(x.UnitCost), N(x.SecondaryCost), x.Formula, N(x.SheetWidthCm), N(x.SheetHeightCm), N(x.ThicknessMm), x.BaseMaterialPriceItemId, JsonSerializer.Serialize(x.GroupProfitPercentOverrides), x.Active, x.Deleted, x.Revision, D(x.UpdatedAtUtc) }));
        var orders = new List<object?[]> { new object?[] { "Kayıt Kimliği", "Tarih", "Müşteri Kimliği", "Açıklama", "Malzeme", "En cm", "Boy cm", "Alan m²", "Uzunluk m", "Süre dk", "Adet", "Alış TL", "Satış TL", "Fiyat Grubu", "Kalemler", "Silindi", "Sürüm", "Güncelleme" } };
        orders.AddRange(state.Orders.Select(x => new object?[] { x.Id, x.Date.ToString("dd.MM.yyyy"), x.CustomerId, x.Description, x.Material, N(x.WidthCm), N(x.HeightCm), N(x.AreaM2), N(x.LengthMeter), N(x.DurationMinutes), N(x.Quantity), N(x.CostTotalTl), N(x.SaleTotalTl), x.PriceGroupId, JsonSerializer.Serialize(x.Lines), x.Deleted, x.Revision, D(x.UpdatedAtUtc) }));
        var payments = new List<object?[]> { new object?[] { "Kayıt Kimliği", "Tarih", "Müşteri Kimliği", "Tutar TL", "Açıklama", "Ödeme Türü", "Silindi", "Sürüm", "Güncelleme" } };
        payments.AddRange(state.Payments.Select(x => new object?[] { x.Id, x.Date.ToString("dd.MM.yyyy"), x.CustomerId, N(x.AmountTl), x.Description, x.PaymentType, x.Deleted, x.Revision, D(x.UpdatedAtUtc) }));
        return new[] { Range("Müşteriler", customers), Range("Fiyat Grupları", groups), Range("Fiyat Tanımları", prices), Range("Siparişler", orders), Range("Tahsilatlar", payments) };
    }

    private async Task UploadEncryptedDriveBackupAsync(CancellationToken cancellationToken)
    {
        if (_session is null) return;
        await EnsureGoogleTokenAsync(cancellationToken).ConfigureAwait(false);
        var key = await EnsureBackupKeyAsync(cancellationToken).ConfigureAwait(false);
        var tempRoot = Path.Combine(Path.GetTempPath(), "BTakip-Bulut");
        Directory.CreateDirectory(tempRoot);
        var plain = Path.Combine(tempRoot, Guid.NewGuid().ToString("N") + ".btakip");
        try
        {
            _store.ExportFullBackup(plain);
            var encrypted = EncryptBackup(File.ReadAllBytes(plain), key, _session.Uid);
            var folderId = await EnsureDriveBackupFolderAsync(cancellationToken).ConfigureAwait(false);
            await UploadDriveFileAsync("BTakip-Son.btakip.enc", encrypted, folderId, cancellationToken).ConfigureAwait(false);
            await UploadDriveFileAsync($"BTakip-{DateTime.Today:yyyy-MM-dd}.btakip.enc", encrypted, folderId, cancellationToken).ConfigureAwait(false);
        }
        finally { try { if (File.Exists(plain)) File.Delete(plain); } catch { } }
    }

    private async Task<byte[]> EnsureBackupKeyAsync(CancellationToken cancellationToken)
    {
        if (_session is null) throw new InvalidOperationException("Google hesabı bağlı değil.");
        var url = FirestoreBase + "/users/" + Uri.EscapeDataString(_session.Uid) + "/private/backup-key";
        using var response = await SendFirebaseAsync(HttpMethod.Get, url, null, cancellationToken).ConfigureAwait(false);
        if (response.IsSuccessStatusCode)
        {
            var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            using var json = JsonDocument.Parse(text);
            var value = FirestoreString(json.RootElement.GetProperty("fields"), "value");
            return Convert.FromBase64String(value);
        }
        if (response.StatusCode != HttpStatusCode.NotFound)
            throw new InvalidOperationException("Bulut yedek anahtarı okunamadı: " + ErrorMessage(await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false)));

        var key = RandomNumberGenerator.GetBytes(32);
        var fields = new Dictionary<string, object> { ["value"] = new { stringValue = Convert.ToBase64String(key) }, ["createdAtUtc"] = new { timestampValue = DateTime.UtcNow.ToString("O") } };
        using var content = JsonContent.Create(new { fields });
        using var create = await SendFirebaseAsync(new HttpMethod("PATCH"), url, content, cancellationToken).ConfigureAwait(false);
        create.EnsureSuccessStatusCode();
        return key;
    }

    private async Task<string> EnsureDriveBackupFolderAsync(CancellationToken cancellationToken)
    {
        if (_session is null) throw new InvalidOperationException("Google hesabı bağlı değil.");
        var escapedUid = _session.Uid.Replace("'", "\\'");
        var query = $"mimeType='application/vnd.google-apps.folder' and trashed=false and appProperties has {{ key='btakipUid' and value='{escapedUid}' }} and appProperties has {{ key='btakipRole' and value='backupFolder' }}";
        var found = await FindDriveFileAsync(query, cancellationToken).ConfigureAwait(false);
        if (!string.IsNullOrWhiteSpace(found)) return found;
        using var content = JsonContent.Create(new { name = "BTakip Yedekleri", mimeType = "application/vnd.google-apps.folder", appProperties = new Dictionary<string, string> { ["btakipUid"] = _session.Uid, ["btakipRole"] = "backupFolder" } });
        using var response = await SendGoogleAsync(HttpMethod.Post, "https://www.googleapis.com/drive/v3/files?fields=id", content, cancellationToken).ConfigureAwait(false);
        var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode) throw new InvalidOperationException("Drive yedek klasörü oluşturulamadı: " + ErrorMessage(text));
        using var json = JsonDocument.Parse(text);
        return json.RootElement.GetProperty("id").GetString() ?? throw new InvalidOperationException("Drive klasör kimliği alınamadı.");
    }

    private async Task UploadDriveFileAsync(string name, byte[] bytes, string folderId, CancellationToken cancellationToken)
    {
        var query = $"name='{name.Replace("'", "\\'")}' and '{folderId}' in parents and trashed=false";
        var fileId = await FindDriveFileAsync(query, cancellationToken).ConfigureAwait(false);
        var metadata = string.IsNullOrWhiteSpace(fileId) ? new { name, parents = new[] { folderId } } : (object)new { name };
        using var multipart = new MultipartContent("related");
        multipart.Add(new StringContent(JsonSerializer.Serialize(metadata), Encoding.UTF8, "application/json"));
        var media = new ByteArrayContent(bytes);
        media.Headers.ContentType = new MediaTypeHeaderValue("application/octet-stream");
        multipart.Add(media);
        var method = string.IsNullOrWhiteSpace(fileId) ? HttpMethod.Post : new HttpMethod("PATCH");
        var url = string.IsNullOrWhiteSpace(fileId)
            ? "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id"
            : $"https://www.googleapis.com/upload/drive/v3/files/{fileId}?uploadType=multipart&fields=id";
        using var response = await SendGoogleAsync(method, url, multipart, cancellationToken).ConfigureAwait(false);
        var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode) throw new InvalidOperationException("Drive yedeği yüklenemedi: " + ErrorMessage(text));
    }

    private async Task<string?> FindDriveFileAsync(string query, CancellationToken cancellationToken)
    {
        var url = "https://www.googleapis.com/drive/v3/files?pageSize=20&fields=files(id,name)&q=" + Uri.EscapeDataString(query);
        using var response = await SendGoogleAsync(HttpMethod.Get, url, null, cancellationToken).ConfigureAwait(false);
        var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode) throw new InvalidOperationException("Google Drive okunamadı: " + ErrorMessage(text));
        using var json = JsonDocument.Parse(text);
        return json.RootElement.TryGetProperty("files", out var files) && files.GetArrayLength() > 0
            ? files[0].GetProperty("id").GetString()
            : null;
    }

    private static byte[] EncryptBackup(byte[] plain, byte[] key, string uid)
    {
        var nonce = RandomNumberGenerator.GetBytes(12);
        var tag = new byte[16];
        var cipher = new byte[plain.Length];
        using var aes = new AesGcm(key, tag.Length);
        aes.Encrypt(nonce, plain, cipher, tag, Encoding.UTF8.GetBytes(uid));
        var header = Encoding.ASCII.GetBytes("BTAKIPENC1");
        return header.Concat(nonce).Concat(tag).Concat(cipher).ToArray();
    }

    private static byte[] DecryptBackup(byte[] encrypted, byte[] key, string uid)
    {
        var header = Encoding.ASCII.GetBytes("BTAKIPENC1");
        if (encrypted.Length < header.Length + 28 || !encrypted.AsSpan(0, header.Length).SequenceEqual(header))
            throw new InvalidDataException("Drive yedeğinin biçimi geçersiz.");
        var nonce = encrypted.AsSpan(header.Length, 12).ToArray();
        var tag = encrypted.AsSpan(header.Length + 12, 16).ToArray();
        var cipher = encrypted.AsSpan(header.Length + 28).ToArray();
        var plain = new byte[cipher.Length];
        using var aes = new AesGcm(key, tag.Length);
        aes.Decrypt(nonce, cipher, tag, plain, Encoding.UTF8.GetBytes(uid));
        return plain;
    }

    private async Task<HttpResponseMessage> SendFirebaseAsync(HttpMethod method, string url, HttpContent? content, CancellationToken cancellationToken)
    {
        await EnsureFirebaseTokenAsync(cancellationToken).ConfigureAwait(false);
        using var request = new HttpRequestMessage(method, url) { Content = content };
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _session!.FirebaseIdToken);
        return await _http.SendAsync(request, cancellationToken).ConfigureAwait(false);
    }

    private async Task<HttpResponseMessage> SendGoogleAsync(HttpMethod method, string url, HttpContent? content, CancellationToken cancellationToken)
    {
        await EnsureGoogleTokenAsync(cancellationToken).ConfigureAwait(false);
        using var request = new HttpRequestMessage(method, url) { Content = content };
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _session!.GoogleAccessToken);
        return await _http.SendAsync(request, cancellationToken).ConfigureAwait(false);
    }

    private string FirestoreBase => $"https://firestore.googleapis.com/v1/projects/{CloudConfiguration.FirebaseProjectId}/databases/(default)/documents";
    private string FirestoreDocumentName(string uid, string type, string id) => $"projects/{CloudConfiguration.FirebaseProjectId}/databases/(default)/documents/users/{uid}/records/{type}_{id}";

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

    private static SyncEntity? DeserializeEntity(string type, string json) => type switch
    {
        "customers" => JsonSerializer.Deserialize<Customer>(json, JsonOptions),
        "price_groups" => JsonSerializer.Deserialize<PriceGroup>(json, JsonOptions),
        "price_items" => JsonSerializer.Deserialize<PriceItem>(json, JsonOptions),
        "orders" => JsonSerializer.Deserialize<Order>(json, JsonOptions),
        "payments" => JsonSerializer.Deserialize<Payment>(json, JsonOptions),
        _ => null
    };

    private static bool Equivalent(SyncEntity a, SyncEntity b)
    {
        var x = JsonSerializer.Serialize(a, a.GetType(), JsonOptions).Replace($"\"SyncedRevision\":{a.SyncedRevision}", "\"SyncedRevision\":0");
        var y = JsonSerializer.Serialize(b, b.GetType(), JsonOptions).Replace($"\"SyncedRevision\":{b.SyncedRevision}", "\"SyncedRevision\":0");
        return x == y;
    }

    private void SaveSession()
    {
        if (_session is null) return;
        Directory.CreateDirectory(Path.GetDirectoryName(_sessionPath)!);
        var plain = JsonSerializer.SerializeToUtf8Bytes(_session, JsonOptions);
        var entropy = SHA256.HashData(Encoding.UTF8.GetBytes("BTakip.GoogleCloud.Session.v1"));
        var protectedBytes = ProtectedData.Protect(plain, entropy, DataProtectionScope.CurrentUser);
        var temp = _sessionPath + ".tmp";
        File.WriteAllBytes(temp, protectedBytes);
        File.Move(temp, _sessionPath, true);
    }

    private CloudSession? LoadSession()
    {
        try
        {
            if (!File.Exists(_sessionPath)) return null;
            var entropy = SHA256.HashData(Encoding.UTF8.GetBytes("BTakip.GoogleCloud.Session.v1"));
            var plain = ProtectedData.Unprotect(File.ReadAllBytes(_sessionPath), entropy, DataProtectionScope.CurrentUser);
            return JsonSerializer.Deserialize<CloudSession>(plain, JsonOptions);
        }
        catch { return null; }
    }

    private static int GetFreeTcpPort()
    {
        var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();
        var port = ((IPEndPoint)listener.LocalEndpoint).Port;
        listener.Stop();
        return port;
    }

    private static string Query(IEnumerable<KeyValuePair<string, string>> values) => string.Join("&", values.Select(x => Uri.EscapeDataString(x.Key) + "=" + Uri.EscapeDataString(x.Value)));
    private static string Base64Url(byte[] value) => Convert.ToBase64String(value).TrimEnd('=').Replace('+', '-').Replace('/', '_');
    private static long ParseSeconds(string value) => long.TryParse(value, out var seconds) ? seconds : 3600;
    private static string FirestoreString(JsonElement fields, string name) => fields.TryGetProperty(name, out var field) && field.TryGetProperty("stringValue", out var value) ? value.GetString() ?? "" : "";
    private static string ReadJwtClaim(string token, string claim)
    {
        try
        {
            var part = token.Split('.')[1].Replace('-', '+').Replace('_', '/');
            part = part.PadRight(part.Length + (4 - part.Length % 4) % 4, '=');
            using var json = JsonDocument.Parse(Convert.FromBase64String(part));
            return json.RootElement.TryGetProperty(claim, out var value) ? value.GetString() ?? "" : "";
        }
        catch { return ""; }
    }

    private static string ErrorMessage(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            if (doc.RootElement.TryGetProperty("error", out var error))
            {
                if (error.ValueKind == JsonValueKind.String) return error.GetString() ?? "Bilinmeyen hata";
                if (error.TryGetProperty("message", out var message)) return message.GetString() ?? "Bilinmeyen hata";
            }
        }
        catch { }
        return json.Length > 300 ? json[..300] : json;
    }

    public void Dispose()
    {
        _http.Dispose();
        _gate.Dispose();
    }

    private sealed class CloudSession
    {
        public string GoogleAccessToken { get; set; } = "";
        public string GoogleRefreshToken { get; set; } = "";
        public DateTime GoogleExpiresUtc { get; set; }
        public string FirebaseIdToken { get; set; } = "";
        public string FirebaseRefreshToken { get; set; } = "";
        public DateTime FirebaseExpiresUtc { get; set; }
        public string Uid { get; set; } = "";
        public string Email { get; set; } = "";
    }

    private sealed class OAuthTokenResponse
    {
        [JsonPropertyName("access_token")] public string AccessToken { get; set; } = "";
        [JsonPropertyName("refresh_token")] public string RefreshToken { get; set; } = "";
        [JsonPropertyName("id_token")] public string IdToken { get; set; } = "";
        [JsonPropertyName("expires_in")] public long ExpiresIn { get; set; } = 3600;
    }

    private sealed class FirebaseSignInResponse
    {
        public string LocalId { get; set; } = "";
        public string Email { get; set; } = "";
        public string IdToken { get; set; } = "";
        public string RefreshToken { get; set; } = "";
        public string ExpiresIn { get; set; } = "3600";
    }

    private sealed class FirebaseRefreshResponse
    {
        [JsonPropertyName("id_token")] public string IdToken { get; set; } = "";
        [JsonPropertyName("refresh_token")] public string RefreshToken { get; set; } = "";
        [JsonPropertyName("expires_in")] public string ExpiresIn { get; set; } = "3600";
    }
}

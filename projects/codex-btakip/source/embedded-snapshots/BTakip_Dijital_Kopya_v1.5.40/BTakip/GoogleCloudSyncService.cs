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
            var warnings = new List<string>();
            try
            {
                // Google Sheets'te kullanıcı tarafından girilen yeni satırlar, Firestore'a
                // gönderilmeden önce aynı yerel fiyat motoruyla hesaplanır.
                result.Received += await ImportEditableSheetEntriesAsync(cancellationToken).ConfigureAwait(false);
            }
            catch (Exception ex)
            {
                warnings.Add("Sheets girişi bekliyor: " + ex.Message);
                await _store.AppendLogAsync("SHEETS GİRİŞ HATA | " + ex.Message).ConfigureAwait(false);
            }
            result.Sent = await PushFirestoreAsync(cancellationToken).ConfigureAwait(false);
            _store.State.Settings.CloudBootstrapComplete = true;
            _store.State.Settings.LastSyncUtc = DateTime.UtcNow;
            result.Changed = result.Sent + result.Received > 0;

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
        var workspace = await GetSheetWorkspaceAsync(cancellationToken).ConfigureAwait(false);
        using (var clear = JsonContent.Create(new { ranges = workspace.DisplayTitles.Select(x => $"'{x.Replace("'", "''")}'!A:Z").ToArray() }))
        using (var response = await SendGoogleAsync(HttpMethod.Post, $"https://sheets.googleapis.com/v4/spreadsheets/{workspace.SpreadsheetId}/values:batchClear", clear, cancellationToken).ConfigureAwait(false))
        {
            var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            if (!response.IsSuccessStatusCode) throw new InvalidOperationException("Google Sheets temizlenemedi: " + ErrorMessage(text));
        }

        var data = BuildReadableSheetRanges(workspace.Sheets, workspace.CustomerSheets);
        using var content = JsonContent.Create(new { valueInputOption = "USER_ENTERED", data });
        using var write = await SendGoogleAsync(HttpMethod.Post, $"https://sheets.googleapis.com/v4/spreadsheets/{workspace.SpreadsheetId}/values:batchUpdate", content, cancellationToken).ConfigureAwait(false);
        var writeText = await write.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!write.IsSuccessStatusCode) throw new InvalidOperationException("Google Sheets güncellenemedi: " + ErrorMessage(writeText));
        await WriteEditableSheetTemplatesAsync(workspace.SpreadsheetId, cancellationToken).ConfigureAwait(false);
        await FormatReadableSheetsAsync(workspace.SpreadsheetId, workspace.Sheets, cancellationToken).ConfigureAwait(false);
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
            properties = new { title = "BTakip Müşteri Takip", locale = "tr_TR", timeZone = "Europe/Istanbul" },
            sheets = new[] { new { properties = new { title = "Müşteriler" } } }
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

    private Dictionary<string, string> BuildCustomerSheetTitles()
    {
        var result = new Dictionary<string, string>(StringComparer.Ordinal);
        var used = new HashSet<string>(new[] { "Müşteriler", "Fiyat Tanımları", "Ürün Girişi", "Hareket Girişi" }, StringComparer.OrdinalIgnoreCase);
        foreach (var customer in _store.State.Customers.Where(x => !x.Deleted).OrderBy(x => x.Name, StringComparer.CurrentCultureIgnoreCase))
        {
            var clean = new string((string.IsNullOrWhiteSpace(customer.Name) ? "Müşteri" : customer.Name.Trim())
                .Select(ch => "[]:*?/\\".Contains(ch) ? ' ' : ch).ToArray()).Trim();
            if (clean.Length > 80) clean = clean[..80].Trim();
            if (string.IsNullOrWhiteSpace(clean)) clean = "Müşteri";
            var title = clean;
            var number = 2;
            while (!used.Add(title)) title = $"{clean} ({number++})";
            result[customer.Id] = title;
        }
        return result;
    }

    private async Task<Dictionary<string, int>> EnsureReadableSheetLayoutAsync(string spreadsheetId, IReadOnlyCollection<string> desiredTitles, CancellationToken cancellationToken)
    {
        async Task<Dictionary<string, int>> ReadAsync()
        {
            using var response = await SendGoogleAsync(HttpMethod.Get, $"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheetId}?fields=sheets.properties(sheetId,title)", null, cancellationToken).ConfigureAwait(false);
            var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            if (!response.IsSuccessStatusCode) throw new InvalidOperationException("Google Sheets sayfaları okunamadı: " + ErrorMessage(text));
            using var json = JsonDocument.Parse(text);
            return json.RootElement.GetProperty("sheets").EnumerateArray().ToDictionary(
                x => x.GetProperty("properties").GetProperty("title").GetString() ?? "",
                x => x.GetProperty("properties").GetProperty("sheetId").GetInt32(),
                StringComparer.OrdinalIgnoreCase);
        }

        var current = await ReadAsync().ConfigureAwait(false);
        var missing = desiredTitles.Where(x => !current.ContainsKey(x)).ToArray();
        if (missing.Length > 0)
        {
            var requests = missing.Select(title => (object)new { addSheet = new { properties = new { title } } }).ToArray();
            await SendSheetsBatchAsync(spreadsheetId, requests, cancellationToken).ConfigureAwait(false);
            current = await ReadAsync().ConfigureAwait(false);
        }

        var desired = new HashSet<string>(desiredTitles, StringComparer.OrdinalIgnoreCase);
        // Kullanıcının kendi eklediği sayfaları silme. Sadece önceki teknik görünümün
        // artık kullanılmayan üç sayfası temizlenir.
        var obsoleteNames = new HashSet<string>(new[] { "Fiyat Grupları", "Siparişler", "Tahsilatlar" }, StringComparer.OrdinalIgnoreCase);
        var obsolete = current.Where(x => obsoleteNames.Contains(x.Key) && !desired.Contains(x.Key)).Select(x => x.Value).ToArray();
        var layout = new List<object>
        {
            new { updateSpreadsheetProperties = new { properties = new { title = "BTakip Müşteri Takip", locale = "tr_TR", timeZone = "Europe/Istanbul" }, fields = "title,locale,timeZone" } }
        };
        layout.AddRange(obsolete.Select(sheetId => (object)new { deleteSheet = new { sheetId } }));
        await SendSheetsBatchAsync(spreadsheetId, layout.ToArray(), cancellationToken).ConfigureAwait(false);
        return current.Where(x => desired.Contains(x.Key)).ToDictionary(x => x.Key, x => x.Value, StringComparer.OrdinalIgnoreCase);
    }

    private async Task<SheetWorkspace> GetSheetWorkspaceAsync(CancellationToken cancellationToken)
    {
        await EnsureGoogleTokenAsync(cancellationToken).ConfigureAwait(false);
        var spreadsheetId = await FindOrCreateSpreadsheetAsync(cancellationToken).ConfigureAwait(false);
        var customerSheets = BuildCustomerSheetTitles();
        var displayTitles = new[] { "Müşteriler", "Fiyat Tanımları" }.Concat(customerSheets.Values).ToArray();
        var titles = displayTitles.Concat(new[] { "Ürün Girişi", "Hareket Girişi" }).ToArray();
        var sheets = await EnsureReadableSheetLayoutAsync(spreadsheetId, titles, cancellationToken).ConfigureAwait(false);
        return new SheetWorkspace(spreadsheetId, sheets, customerSheets, displayTitles);
    }

    private object[] BuildReadableSheetRanges(IReadOnlyDictionary<string, int> sheets, IReadOnlyDictionary<string, string> customerSheets)
    {
        var state = _store.State;
        static object Range(string title, IEnumerable<object?[]> rows) => new { range = $"'{title.Replace("'", "''")}'!A1", majorDimension = "ROWS", values = rows };
        static string FormulaText(string value) => value.Replace("\"", "\"\"");

        var activeGroups = state.PriceGroups.Where(x => !x.Deleted).ToList();
        var groups = activeGroups.ToDictionary(x => x.Id, x => x.Name);
        var fasonGroup = activeGroups.FirstOrDefault(x => x.Name.Contains("Fason", StringComparison.OrdinalIgnoreCase));
        var retailGroup = activeGroups.FirstOrDefault(x => x.Name.Contains("Perakende", StringComparison.OrdinalIgnoreCase));
        var customers = new List<object?[]> { new object?[] { "Müşteri", "Firma", "Fiyat Grubu", "Telefon", "Bakiye" } };
        foreach (var customer in state.Customers.Where(x => !x.Deleted).OrderBy(x => x.Name, StringComparer.CurrentCultureIgnoreCase))
        {
            var balance = state.Orders.Where(x => !x.Deleted && x.CustomerId == customer.Id).Sum(x => x.SaleTotalTl)
                          - state.Payments.Where(x => !x.Deleted && x.CustomerId == customer.Id).Sum(x => x.AmountTl);
            var title = customerSheets[customer.Id];
            var link = $"=HYPERLINK(\"#gid={sheets[title]}\";\"{FormulaText(customer.Name)}\")";
            customers.Add(new object?[] { link, customer.Company, groups.GetValueOrDefault(customer.PriceGroupId, customer.PriceGroupId), customer.Phone, balance });
        }

        var prices = new List<object?[]> { new object?[] { "Malzeme / Hizmet", "Tür", "Ürün", "Açıklama", "Birim", "Para", "Alış Fiyatı", "Maliyet TL", "Hesap", "Fason Kâr %", "Perakende Kâr %", "Durum" } };
        prices.AddRange(state.PriceItems.Where(x => !x.Deleted).OrderBy(x => x.Category).ThenBy(x => x.Name).ThenBy(x => x.Variant)
            .Select(x => new object?[]
            {
                x.DisplayName, x.Category, x.Name, x.Variant, x.Unit, x.Currency, x.UnitCost,
                x.Currency.Equals("USD", StringComparison.OrdinalIgnoreCase) ? x.UnitCost * state.Settings.UsdTryRate : x.UnitCost,
                SheetFormulaName(x.Formula),
                ProfitPercentForSheet(x, fasonGroup), ProfitPercentForSheet(x, retailGroup), x.Active ? "Aktif" : "Pasif"
            }));

        var ranges = new List<object> { Range("Müşteriler", customers), Range("Fiyat Tanımları", prices) };
        foreach (var customer in state.Customers.Where(x => !x.Deleted))
        {
            var rows = new List<object?[]> { new object?[] { "Tarih", "Hareket", "Açıklama", "Malzeme", "Ölçü", "Borç", "Tahsilat", "Bakiye" } };
            var movements = new List<(DateTime Date, DateTime Updated, string Type, string Description, string Material, string Measure, decimal Debt, decimal Payment)>();
            movements.AddRange(state.Orders.Where(x => !x.Deleted && x.CustomerId == customer.Id)
                .Select(x => (x.Date, x.UpdatedAtUtc, "Satış", x.Description, x.Material, FormatSheetMeasure(x), x.SaleTotalTl, 0m)));
            movements.AddRange(state.Payments.Where(x => !x.Deleted && x.CustomerId == customer.Id)
                .Select(x => (x.Date, x.UpdatedAtUtc, "Tahsilat", string.IsNullOrWhiteSpace(x.Description) ? x.PaymentType : x.Description, "", "", 0m, x.AmountTl)));
            decimal running = 0;
            foreach (var movement in movements.OrderBy(x => x.Date).ThenBy(x => x.Updated).ThenBy(x => x.Type == "Tahsilat" ? 1 : 0))
            {
                running += movement.Debt - movement.Payment;
                rows.Add(new object?[] { movement.Date.ToString("dd.MM.yyyy"), movement.Type, movement.Description, movement.Material, movement.Measure,
                    movement.Debt == 0 ? null : movement.Debt, movement.Payment == 0 ? null : movement.Payment, running });
            }
            ranges.Add(Range(customerSheets[customer.Id], rows));
        }
        return ranges.ToArray();
    }

    private async Task WriteEditableSheetTemplatesAsync(string spreadsheetId, CancellationToken cancellationToken)
    {
        using var content = JsonContent.Create(new { valueInputOption = "USER_ENTERED", data = BuildEditableSheetRanges() });
        using var response = await SendGoogleAsync(HttpMethod.Post, $"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheetId}/values:batchUpdate", content, cancellationToken).ConfigureAwait(false);
        var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode) throw new InvalidOperationException("Google Sheets giriş alanları hazırlanamadı: " + ErrorMessage(text));
    }

    private object[] BuildEditableSheetRanges()
    {
        const int rowCount = 300;
        static object Range(string title, string startCell, IEnumerable<object?[]> rows) => new { range = $"'{title.Replace("'", "''")}'!{startCell}", majorDimension = "ROWS", values = rows };

        var productHeaders = new object?[] { "Durum", "Tür", "Ürün", "Açıklama", "Birim", "Para", "Alış Fiyatı", "Hesap", "Fason Kâr %", "Perakende Kâr %", "Fason Satış Önizleme", "Perakende Satış Önizleme" };
        var productFason = new List<object?[]>();
        var productRetail = new List<object?[]>();
        var movementHeaders = new object?[] { "Durum", "Tarih", "Müşteri", "Hareket", "Açıklama", "Malzeme", "Baskı", "Hizmet", "En cm", "Boy cm", "Uzunluk m", "Süre dk", "Adet", "Tahsilat TL", "Maliyet Önizleme", "Borç Önizleme" };
        var movementCost = new List<object?[]>();
        var movementDebt = new List<object?[]>();
        for (var row = 2; row < rowCount + 2; row++)
        {
            productFason.Add(new object?[] { $"=IF($G{row}=\"\";\"\";$G{row}*(1+IF($I{row}=\"\";1;$I{row}/100)))" });
            productRetail.Add(new object?[] { $"=IF($G{row}=\"\";\"\";$G{row}*(1+IF($J{row}=\"\";3;$J{row}/100)))" });
            movementCost.Add(new object?[] { MovementCostFormula(row) });
            movementDebt.Add(new object?[] { MovementDebtFormula(row) });
        }

        return new object[]
        {
            Range("Ürün Girişi", "A1", new[] { productHeaders }),
            Range("Ürün Girişi", "K2", productFason),
            Range("Ürün Girişi", "L2", productRetail),
            Range("Hareket Girişi", "A1", new[] { movementHeaders }),
            Range("Hareket Girişi", "O2", movementCost),
            Range("Hareket Girişi", "P2", movementDebt)
        };
    }

    private static string MovementCostFormula(int row) =>
        $"=IF($D{row}<>\"Satış\";\"\";IF(AND($F{row}=\"\";$G{row}=\"\";$H{row}=\"\");\"\";{SheetItemCostFormula(row, "F")}+{SheetItemCostFormula(row, "G")}+{SheetItemCostFormula(row, "H")}))";

    private static string MovementDebtFormula(int row) =>
        $"=IF($O{row}=\"\";\"\";$O{row}*(1+SWITCH(VLOOKUP($C{row};'Müşteriler'!$A$2:$E;3;FALSE);\"Reklamcı / Fason\";1;\"Perakende\";3;\"Çevre Esnafı\";2;\"Sürekli Müşteri\";1;0)))";

    private static string SheetItemCostFormula(int row, string column)
    {
        var lookup = $"VLOOKUP(${column}{row};'Fiyat Tanımları'!$A$2:$L;";
        var cost = lookup + "8;FALSE)";
        var formula = lookup + "9;FALSE)";
        var quantity = $"IF($M{row}=\"\";1;$M{row})";
        var area = $"($I{row}*$J{row}/10000)";
        return $"IF(${column}{row}=\"\";0;SWITCH({formula};\"m² üzerinden\";{cost}*{area}*{quantity};\"metre üzerinden\";{cost}*$K{row}*{quantity};\"adet üzerinden\";{cost}*{quantity};\"dakika üzerinden\";{cost}*$L{row}*{quantity};\"saat üzerinden\";{cost}*$L{row}/60*{quantity};\"sabit ücret\";{cost};\"levha alanı oranı\";{cost}*{area}*{quantity};\"UV 60×90 oranı\";{cost}*{area}/0.54*{quantity};\"DTF 10 m kademesi\";{cost}*$K{row}*{quantity};0))";
    }

    private async Task<int> ImportEditableSheetEntriesAsync(CancellationToken cancellationToken)
    {
        var workspace = await GetSheetWorkspaceAsync(cancellationToken).ConfigureAwait(false);
        await WriteEditableSheetTemplatesAsync(workspace.SpreadsheetId, cancellationToken).ConfigureAwait(false);
        var productRows = await ReadSheetRowsAsync(workspace.SpreadsheetId, "'Ürün Girişi'!A2:L301", cancellationToken).ConfigureAwait(false);
        var movementRows = await ReadSheetRowsAsync(workspace.SpreadsheetId, "'Hareket Girişi'!A2:P301", cancellationToken).ConfigureAwait(false);
        var statuses = new List<(string Sheet, int Row, string Status)>();
        var imported = 0;
        var undoCaptured = false;

        void CaptureUndo()
        {
            if (undoCaptured) return;
            _store.CaptureUndo("Google Sheets girişleri aktarıldı");
            undoCaptured = true;
        }

        for (var index = 0; index < productRows.Count; index++)
        {
            var row = productRows[index];
            if (!ShouldImportSheetRow(Cell(row, 0)) || string.IsNullOrWhiteSpace(Cell(row, 2))) continue;
            var category = Cell(row, 1);
            if (category is not ("Malzeme" or "Baskı" or "Hizmet"))
            {
                statuses.Add(("Ürün Girişi", index + 2, "Hata: Tür Malzeme, Baskı veya Hizmet olmalı."));
                continue;
            }
            if (!TrySheetDecimal(Cell(row, 6), out var cost) || cost < 0)
            {
                statuses.Add(("Ürün Girişi", index + 2, "Hata: Alış Fiyatı gerekli."));
                continue;
            }

            var name = Cell(row, 2).Trim();
            var variant = Cell(row, 3).Trim();
            var displayName = string.IsNullOrWhiteSpace(variant) ? name : $"{name} — {variant}";
            var update = Cell(row, 0).Trim().StartsWith("Güncelle", StringComparison.OrdinalIgnoreCase);
            var existing = _store.State.PriceItems.FirstOrDefault(x => !x.Deleted && x.DisplayName.Equals(displayName, StringComparison.OrdinalIgnoreCase));
            if (update && existing is null)
            {
                statuses.Add(("Ürün Girişi", index + 2, "Hata: Güncellenecek tanım bulunamadı."));
                continue;
            }
            if (!update && existing is not null)
            {
                statuses.Add(("Ürün Girişi", index + 2, "Hata: Tanım zaten var. Güncelle seçin."));
                continue;
            }

            CaptureUndo();
            var item = existing ?? new PriceItem { DeviceId = _store.State.DeviceId };
            item.Category = category;
            item.Name = name;
            item.Variant = variant;
            item.Unit = string.IsNullOrWhiteSpace(Cell(row, 4)) ? "m²" : Cell(row, 4).Trim();
            item.Currency = string.IsNullOrWhiteSpace(Cell(row, 5)) ? "TL" : Cell(row, 5).Trim().ToUpperInvariant();
            item.UnitCost = cost;
            item.Formula = FormulaFromSheet(Cell(row, 7));
            item.IsPrintProduct = category == "Baskı";
            item.Active = true;
            SetSheetProfitOverride(item, _store.State.PriceGroups.FirstOrDefault(x => !x.Deleted && x.Name.Contains("Fason", StringComparison.OrdinalIgnoreCase)), Cell(row, 8));
            SetSheetProfitOverride(item, _store.State.PriceGroups.FirstOrDefault(x => !x.Deleted && x.Name.Contains("Perakende", StringComparison.OrdinalIgnoreCase)), Cell(row, 9));
            _store.Touch(item);
            if (existing is null) _store.State.PriceItems.Add(item);
            statuses.Add(("Ürün Girişi", index + 2, ImportedStatus()));
            imported++;
        }

        for (var index = 0; index < movementRows.Count; index++)
        {
            var row = movementRows[index];
            if (!ShouldImportSheetRow(Cell(row, 0)) || string.IsNullOrWhiteSpace(Cell(row, 2)) || string.IsNullOrWhiteSpace(Cell(row, 3))) continue;
            var customer = _store.State.Customers.FirstOrDefault(x => !x.Deleted && x.Name.Equals(Cell(row, 2).Trim(), StringComparison.OrdinalIgnoreCase));
            if (customer is null)
            {
                statuses.Add(("Hareket Girişi", index + 2, "Hata: Müşteri bulunamadı."));
                continue;
            }
            if (!TrySheetDate(Cell(row, 1), out var date)) date = DateTime.Today;
            var movement = Cell(row, 3).Trim();
            if (movement.Equals("Tahsilat", StringComparison.OrdinalIgnoreCase))
            {
                if (!TrySheetDecimal(Cell(row, 13), out var amount) || amount <= 0)
                {
                    statuses.Add(("Hareket Girişi", index + 2, "Hata: Tahsilat TL gerekli."));
                    continue;
                }
                CaptureUndo();
                _store.State.Payments.Add(new Payment
                {
                    DeviceId = _store.State.DeviceId, CustomerId = customer.Id, Date = date, AmountTl = amount,
                    Description = string.IsNullOrWhiteSpace(Cell(row, 4)) ? "Tahsilat" : Cell(row, 4).Trim(), PaymentType = "Tahsilat"
                });
                statuses.Add(("Hareket Girişi", index + 2, ImportedStatus()));
                imported++;
                continue;
            }
            if (!movement.Equals("Satış", StringComparison.OrdinalIgnoreCase))
            {
                statuses.Add(("Hareket Girişi", index + 2, "Hata: Hareket Satış veya Tahsilat olmalı."));
                continue;
            }

            var selected = new[] { Cell(row, 5), Cell(row, 6), Cell(row, 7) }
                .Where(x => !string.IsNullOrWhiteSpace(x))
                .Select(FindPriceItemBySheetName)
                .ToList();
            if (selected.Count == 0 || selected.Any(x => x is null))
            {
                statuses.Add(("Hareket Girişi", index + 2, "Hata: Malzeme, Baskı veya Hizmet seçin."));
                continue;
            }

            TrySheetDecimal(Cell(row, 8), out var width);
            TrySheetDecimal(Cell(row, 9), out var height);
            TrySheetDecimal(Cell(row, 10), out var length);
            TrySheetDecimal(Cell(row, 11), out var minutes);
            var quantity = TrySheetDecimal(Cell(row, 12), out var suppliedQuantity) && suppliedQuantity > 0 ? suppliedQuantity : 1m;
            var input = new CalculationInput(width, height, length, minutes, quantity, _store.State.Settings.UsdTryRate);
            var items = selected.Cast<PriceItem>().ToList();
            if (!HasRequiredSheetMeasure(items, input))
            {
                statuses.Add(("Hareket Girişi", index + 2, "Hata: Seçilen kalemin ölçü veya süresini girin."));
                continue;
            }
            var group = _store.State.PriceGroups.FirstOrDefault(x => !x.Deleted && x.Id == customer.PriceGroupId);
            if (group is null)
            {
                statuses.Add(("Hareket Girişi", index + 2, "Hata: Müşterinin fiyat grubu bulunamadı."));
                continue;
            }

            var calculation = PricingEngine.Calculate(items, input, group.CostMultiplier, null, group.Id, _store.State.PriceGroups, _store.State.PriceItems);
            var material = string.Join(" + ", items.Select(x => x.DisplayName));
            CaptureUndo();
            _store.State.Orders.Add(new Order
            {
                DeviceId = _store.State.DeviceId, CustomerId = customer.Id, Date = date,
                Description = string.IsNullOrWhiteSpace(Cell(row, 4)) ? material : Cell(row, 4).Trim(), Material = material,
                WidthCm = width, HeightCm = height, AreaM2 = width * height / 10_000m, LengthMeter = length, DurationMinutes = minutes,
                Quantity = quantity, ExchangeRate = _store.State.Settings.UsdTryRate, CostTotalTl = calculation.CostTl,
                SaleTotalTl = calculation.SaleTl, PriceGroupId = group.Id, Lines = calculation.Lines
            });
            statuses.Add(("Hareket Girişi", index + 2, ImportedStatus()));
            imported++;
        }

        if (statuses.Count > 0) await WriteSheetStatusesAsync(workspace.SpreadsheetId, statuses, cancellationToken).ConfigureAwait(false);
        return imported;
    }

    private async Task<List<string[]>> ReadSheetRowsAsync(string spreadsheetId, string range, CancellationToken cancellationToken)
    {
        var url = "https://sheets.googleapis.com/v4/spreadsheets/" + spreadsheetId + "/values/" + Uri.EscapeDataString(range) + "?majorDimension=ROWS";
        using var response = await SendGoogleAsync(HttpMethod.Get, url, null, cancellationToken).ConfigureAwait(false);
        var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode) throw new InvalidOperationException("Google Sheets girişleri okunamadı: " + ErrorMessage(text));
        using var json = JsonDocument.Parse(text);
        if (!json.RootElement.TryGetProperty("values", out var values)) return [];
        return values.EnumerateArray().Select(row => row.EnumerateArray().Select(x => x.ToString()).ToArray()).ToList();
    }

    private async Task WriteSheetStatusesAsync(string spreadsheetId, IEnumerable<(string Sheet, int Row, string Status)> statuses, CancellationToken cancellationToken)
    {
        var data = statuses.Select(x => (object)new { range = $"'{x.Sheet}'!A{x.Row}", majorDimension = "ROWS", values = new[] { new[] { x.Status } } }).ToArray();
        using var content = JsonContent.Create(new { valueInputOption = "USER_ENTERED", data });
        using var response = await SendGoogleAsync(HttpMethod.Post, $"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheetId}/values:batchUpdate", content, cancellationToken).ConfigureAwait(false);
        var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode) throw new InvalidOperationException("Google Sheets giriş durumu yazılamadı: " + ErrorMessage(text));
    }

    private static string Cell(IReadOnlyList<string> row, int index) => index < row.Count ? row[index].Trim() : "";
    private static string ImportedStatus() => "Aktarıldı " + DateTime.Now.ToString("dd.MM.yyyy HH:mm");
    private static bool ShouldImportSheetRow(string status) => !status.StartsWith("Aktarıldı", StringComparison.OrdinalIgnoreCase);

    private PriceItem? FindPriceItemBySheetName(string name) => _store.State.PriceItems.FirstOrDefault(x => !x.Deleted && x.Active && x.DisplayName.Equals(name.Trim(), StringComparison.OrdinalIgnoreCase));

    private static bool TrySheetDecimal(string value, out decimal result) =>
        decimal.TryParse(value, System.Globalization.NumberStyles.Number, System.Globalization.CultureInfo.GetCultureInfo("tr-TR"), out result) ||
        decimal.TryParse(value, System.Globalization.NumberStyles.Number, System.Globalization.CultureInfo.InvariantCulture, out result);

    private static bool TrySheetDate(string value, out DateTime result) =>
        DateTime.TryParse(value, System.Globalization.CultureInfo.GetCultureInfo("tr-TR"), System.Globalization.DateTimeStyles.AllowWhiteSpaces, out result) ||
        DateTime.TryParse(value, System.Globalization.CultureInfo.InvariantCulture, System.Globalization.DateTimeStyles.AllowWhiteSpaces, out result);

    private static string FormulaFromSheet(string formula)
    {
        if (PricingFormula.Labels.Any(x => x.Value.Equals(formula, StringComparison.OrdinalIgnoreCase)))
            return PricingFormula.Labels.First(x => x.Value.Equals(formula, StringComparison.OrdinalIgnoreCase)).Key;
        return PricingFormula.Labels.ContainsKey(formula) ? formula : PricingFormula.SquareMeter;
    }

    private static void SetSheetProfitOverride(PriceItem item, PriceGroup? group, string value)
    {
        if (group is null || string.IsNullOrWhiteSpace(value) || !TrySheetDecimal(value, out var percent)) return;
        item.GroupProfitPercentOverrides ??= [];
        item.GroupProfitPercentOverrides[group.Id] = percent;
    }

    private static bool HasRequiredSheetMeasure(IEnumerable<PriceItem> items, CalculationInput input) => items.All(item => item.Formula switch
    {
        PricingFormula.SquareMeter or PricingFormula.SheetArea or PricingFormula.UvTable => input.WidthCm > 0 && input.HeightCm > 0,
        PricingFormula.Meter or PricingFormula.DtfTier => input.LengthMeter > 0,
        PricingFormula.Minute or PricingFormula.Hour => input.DurationMinutes > 0,
        _ => true
    });

    private async Task FormatReadableSheetsAsync(string spreadsheetId, IReadOnlyDictionary<string, int> sheets, CancellationToken cancellationToken)
    {
        var requests = new List<object>();

        void Money(int sheetId, int start, int end) => requests.Add(new
        {
            repeatCell = new
            {
                range = new { sheetId, startRowIndex = 1, startColumnIndex = start, endColumnIndex = end },
                cell = new { userEnteredFormat = new { numberFormat = new { type = "NUMBER", pattern = "#,##0.00" } } },
                fields = "userEnteredFormat.numberFormat"
            }
        });

        void Validation(int sheetId, int column, IEnumerable<string> values)
        {
            var allowed = values.Where(x => !string.IsNullOrWhiteSpace(x)).Distinct(StringComparer.OrdinalIgnoreCase)
                .Select(x => new { userEnteredValue = x }).ToArray();
            if (allowed.Length == 0) return;
            requests.Add(new
            {
                setDataValidation = new
                {
                    range = new { sheetId, startRowIndex = 1, endRowIndex = 501, startColumnIndex = column, endColumnIndex = column + 1 },
                    rule = new { condition = new { type = "ONE_OF_LIST", values = allowed }, strict = true, showCustomUi = true }
                }
            });
        }

        var productNames = _store.State.PriceItems.Where(x => !x.Deleted && x.Active).Select(x => x.DisplayName).ToArray();
        var materials = _store.State.PriceItems.Where(x => !x.Deleted && x.Active && x.Category.Equals("Malzeme", StringComparison.OrdinalIgnoreCase)).Select(x => x.DisplayName).ToArray();
        var prints = _store.State.PriceItems.Where(x => !x.Deleted && x.Active && x.Category.Equals("Baskı", StringComparison.OrdinalIgnoreCase)).Select(x => x.DisplayName).ToArray();
        var services = _store.State.PriceItems.Where(x => !x.Deleted && x.Active && x.Category.Equals("Hizmet", StringComparison.OrdinalIgnoreCase)).Select(x => x.DisplayName).ToArray();
        var customers = _store.State.Customers.Where(x => !x.Deleted).Select(x => x.Name).ToArray();
        var units = _store.State.PriceItems.Where(x => !x.Deleted).Select(x => x.Unit)
            .Concat(new[] { "m²", "metre", "adet", "dakika", "saat", "levha", "tabla", "%" }).ToArray();

        foreach (var (title, sheetId) in sheets)
        {
            var columns = title switch
            {
                "Müşteriler" => 5,
                "Fiyat Tanımları" => 12,
                "Ürün Girişi" => 12,
                "Hareket Girişi" => 16,
                _ => 8
            };
            requests.Add(new { updateSheetProperties = new { properties = new { sheetId, gridProperties = new { frozenRowCount = 1 } }, fields = "gridProperties.frozenRowCount" } });
            requests.Add(new { repeatCell = new { range = new { sheetId, startRowIndex = 0, endRowIndex = 1, startColumnIndex = 0, endColumnIndex = columns }, cell = new { userEnteredFormat = new { backgroundColorStyle = new { rgbColor = new { red = 0.07, green = 0.20, blue = 0.28 } }, textFormat = new { foregroundColorStyle = new { rgbColor = new { red = 1.0, green = 1.0, blue = 1.0 } }, bold = true } } }, fields = "userEnteredFormat(backgroundColorStyle,textFormat)" } });
            requests.Add(new { repeatCell = new { range = new { sheetId, startRowIndex = 0, endRowIndex = 1, startColumnIndex = 0, endColumnIndex = 1 }, cell = new { userEnteredFormat = new { backgroundColorStyle = new { rgbColor = new { red = 0.0, green = 0.45, blue = 0.78 } } } }, fields = "userEnteredFormat.backgroundColorStyle" } });
            requests.Add(new { autoResizeDimensions = new { dimensions = new { sheetId, dimension = "COLUMNS", startIndex = 0, endIndex = columns } } });
            var wideColumn = title switch { "Fiyat Tanımları" => 3, "Ürün Girişi" => 3, "Hareket Girişi" => 4, _ => 2 };
            requests.Add(new { updateDimensionProperties = new { range = new { sheetId, dimension = "COLUMNS", startIndex = wideColumn, endIndex = wideColumn + 1 }, properties = new { pixelSize = 300 }, fields = "pixelSize" } });
            requests.Add(new { setBasicFilter = new { filter = new { range = new { sheetId, startRowIndex = 0, startColumnIndex = 0, endColumnIndex = columns } } } });

            if (title == "Müşteriler") Money(sheetId, 4, 5);
            else if (title == "Fiyat Tanımları") { Money(sheetId, 6, 8); }
            else if (title == "Ürün Girişi")
            {
                Money(sheetId, 6, 7); Money(sheetId, 10, 12);
                Validation(sheetId, 0, new[] { "Yeni", "Güncelle" });
                Validation(sheetId, 1, new[] { "Malzeme", "Baskı", "Hizmet" });
                Validation(sheetId, 4, units);
                Validation(sheetId, 5, new[] { "TL", "USD", "%" });
                Validation(sheetId, 7, PricingFormula.Labels.Values);
            }
            else if (title == "Hareket Girişi")
            {
                Money(sheetId, 13, 16);
                Validation(sheetId, 0, new[] { "Yeni" });
                Validation(sheetId, 2, customers);
                Validation(sheetId, 3, new[] { "Satış", "Tahsilat" });
                Validation(sheetId, 5, materials.Length == 0 ? productNames : materials);
                Validation(sheetId, 6, prints);
                Validation(sheetId, 7, services);
            }
            else Money(sheetId, 5, 8);
        }
        await SendSheetsBatchAsync(spreadsheetId, requests.ToArray(), cancellationToken).ConfigureAwait(false);
    }

    private async Task SendSheetsBatchAsync(string spreadsheetId, object[] requests, CancellationToken cancellationToken)
    {
        if (requests.Length == 0) return;
        using var content = JsonContent.Create(new { requests });
        using var response = await SendGoogleAsync(HttpMethod.Post, $"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheetId}:batchUpdate", content, cancellationToken).ConfigureAwait(false);
        var text = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode) throw new InvalidOperationException("Google Sheets düzeni güncellenemedi: " + ErrorMessage(text));
    }

    private static string FormatSheetMeasure(Order order)
    {
        static string N(decimal value) => value.ToString("0.##", System.Globalization.CultureInfo.GetCultureInfo("tr-TR"));
        if (order.WidthCm > 0 && order.HeightCm > 0) return $"{N(order.WidthCm)} × {N(order.HeightCm)} cm";
        if (order.AreaM2 > 0) return $"{N(order.AreaM2)} m²";
        if (order.LengthMeter > 0) return $"{N(order.LengthMeter)} m";
        if (order.DurationMinutes > 0) return $"{N(order.DurationMinutes)} dk";
        return "";
    }

    private static string SheetFormulaName(string formula) => PricingFormula.Labels.GetValueOrDefault(formula, formula);

    private static decimal ProfitPercentForSheet(PriceItem item, PriceGroup? group)
    {
        if (group is null) return 0;
        if (item.GroupProfitPercentOverrides?.TryGetValue(group.Id, out var specialPercent) == true) return specialPercent;
        return (group.CostMultiplier - 1m) * 100m;
    }

    private sealed record SheetWorkspace(
        string SpreadsheetId,
        IReadOnlyDictionary<string, int> Sheets,
        IReadOnlyDictionary<string, string> CustomerSheets,
        IReadOnlyCollection<string> DisplayTitles);

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

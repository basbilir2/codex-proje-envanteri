using System.Diagnostics;
using System.Collections.Concurrent;
using System.IO.Compression;
using System.Net.Http.Headers;
using System.Text.Json;

namespace LocalAIOS;

internal sealed record SetupProgress(string Message, int Percent);

internal sealed class RuntimeManager : IDisposable
{
    private const string ReleaseApi = "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest";
    private readonly HttpClient _http = new() { Timeout = Timeout.InfiniteTimeSpan };
    private readonly int _port;
    private readonly ModelProfile _model;
    private Process? _server;
    private readonly ConcurrentQueue<string> _serverErrors = new();

    public RuntimeManager(int port, ModelProfile model)
    {
        _port = port;
        _model = model;
        _http.DefaultRequestHeaders.UserAgent.Add(new ProductInfoHeaderValue("LocalAIOS", "0.1"));
    }

    public ModelProfile Model => _model;
    public bool IsInstalled => FindServer() is not null && File.Exists(AppPaths.Model(_model.FileName));

    public async Task EnsureInstalledAsync(IProgress<SetupProgress> progress, CancellationToken cancellationToken)
    {
        AppPaths.EnsureDirectories();
        if (FindServer() is null)
        {
            progress.Report(new("Yerel motor indiriliyor…", 1));
            await DownloadEngineAsync(progress, cancellationToken);
        }
        var modelPath = AppPaths.Model(_model.FileName);
        if (!File.Exists(modelPath))
        {
            progress.Report(new("Yapay zekâ modeli indiriliyor…", 1));
            await DownloadFileAsync(_model.DownloadUrl, modelPath + ".part", progress, 5, 95, cancellationToken);
            File.Move(modelPath + ".part", modelPath, true);
        }
        progress.Report(new("Hazır", 100));
    }

    public async Task StartAsync(IProgress<SetupProgress> progress, CancellationToken cancellationToken)
    {
        if (await IsHealthyAsync(cancellationToken)) return;
        var server = FindServer() ?? throw new InvalidOperationException("Yerel motor bulunamadı.");
        var arguments = $"-m \"{AppPaths.Model(_model.FileName)}\" --host 127.0.0.1 --port {_port} -c {_model.ContextSize} -np 1 -ngl 0 --jinja";
        _server = Process.Start(new ProcessStartInfo
        {
            FileName = server,
            Arguments = arguments,
            WorkingDirectory = Path.GetDirectoryName(server)!,
            UseShellExecute = false,
            CreateNoWindow = true,
            WindowStyle = ProcessWindowStyle.Hidden,
            RedirectStandardOutput = true,
            RedirectStandardError = true
        }) ?? throw new InvalidOperationException("Yerel motor başlatılamadı.");
        _server.OutputDataReceived += (_, _) => { };
        _server.ErrorDataReceived += (_, eventArgs) =>
        {
            if (string.IsNullOrWhiteSpace(eventArgs.Data)) return;
            _serverErrors.Enqueue(eventArgs.Data);
            while (_serverErrors.Count > 30) _serverErrors.TryDequeue(out var discarded);
        };
        _server.BeginOutputReadLine();
        _server.BeginErrorReadLine();

        progress.Report(new("Model belleğe yükleniyor…", 98));
        for (var attempt = 0; attempt < 120; attempt++)
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (_server.HasExited)
            {
                throw new InvalidOperationException($"Yerel motor durdu: {string.Join(" | ", _serverErrors)}");
            }
            if (await IsHealthyAsync(cancellationToken))
            {
                progress.Report(new("Hazır", 100));
                return;
            }
            await Task.Delay(1000, cancellationToken);
        }
        throw new TimeoutException("Model zamanında başlatılamadı.");
    }

    private async Task DownloadEngineAsync(IProgress<SetupProgress> progress, CancellationToken cancellationToken)
    {
        var json = await _http.GetStringAsync(ReleaseApi, cancellationToken);
        using var document = JsonDocument.Parse(json);
        var assets = document.RootElement.GetProperty("assets").EnumerateArray();
        string? downloadUrl = null;
        foreach (var asset in assets)
        {
            var name = asset.GetProperty("name").GetString() ?? "";
            if (name.EndsWith("bin-win-cpu-x64.zip", StringComparison.OrdinalIgnoreCase))
            {
                downloadUrl = asset.GetProperty("browser_download_url").GetString();
                break;
            }
        }
        if (downloadUrl is null) throw new InvalidOperationException("Windows yerel motor paketi bulunamadı.");

        var archive = Path.Combine(AppPaths.Root, "engine.zip");
        await DownloadFileAsync(downloadUrl, archive, progress, 1, 90, cancellationToken);
        if (Directory.Exists(AppPaths.Runtime)) Directory.Delete(AppPaths.Runtime, true);
        Directory.CreateDirectory(AppPaths.Runtime);
        ZipFile.ExtractToDirectory(archive, AppPaths.Runtime, true);
        File.Delete(archive);
    }

    private async Task DownloadFileAsync(
        string url,
        string destination,
        IProgress<SetupProgress> progress,
        int startPercent,
        int endPercent,
        CancellationToken cancellationToken)
    {
        using var response = await _http.GetAsync(url, HttpCompletionOption.ResponseHeadersRead, cancellationToken);
        response.EnsureSuccessStatusCode();
        var total = response.Content.Headers.ContentLength;
        await using var input = await response.Content.ReadAsStreamAsync(cancellationToken);
        await using var output = new FileStream(destination, FileMode.Create, FileAccess.Write, FileShare.None, 1024 * 1024, true);
        var buffer = new byte[1024 * 1024];
        long received = 0;
        int read;
        while ((read = await input.ReadAsync(buffer, cancellationToken)) > 0)
        {
            await output.WriteAsync(buffer.AsMemory(0, read), cancellationToken);
            received += read;
            if (total > 0)
            {
                var ratio = (double)received / total.Value;
                var percent = startPercent + (int)((endPercent - startPercent) * ratio);
                progress.Report(new($"İndiriliyor… %{percent}", percent));
            }
        }
    }

    private string? FindServer() => Directory.Exists(AppPaths.Runtime)
        ? Directory.EnumerateFiles(AppPaths.Runtime, "llama-server.exe", SearchOption.AllDirectories).FirstOrDefault()
        : null;

    private async Task<bool> IsHealthyAsync(CancellationToken cancellationToken)
    {
        try
        {
            using var check = new HttpClient { Timeout = TimeSpan.FromSeconds(2) };
            using var response = await check.GetAsync($"http://127.0.0.1:{_port}/health", cancellationToken);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    public void Dispose()
    {
        try
        {
            if (_server is { HasExited: false }) _server.Kill(true);
        }
        catch { }
        _server?.Dispose();
        _http.Dispose();
    }
}

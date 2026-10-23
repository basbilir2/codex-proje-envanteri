using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;

namespace LocalAIOS;

internal sealed record ModelEndpoint(string ChatUrl, string Model, string? ApiKey)
{
    public static ModelEndpoint Local(int port) => new($"http://127.0.0.1:{port}/v1/chat/completions", "local-model", null);
    public static ModelEndpoint OpenRouter(string key) => new("https://openrouter.ai/api/v1/chat/completions", "openrouter/free", key);
}

internal sealed class CloudComputeClient(string apiKey)
{
    private readonly HttpClient _http = CreateClient(apiKey);
    public ModelEndpoint Endpoint => ModelEndpoint.OpenRouter(apiKey);

    public async Task<string> ChatAsync(IReadOnlyList<ChatMessage> history, string knowledge, CancellationToken cancellationToken)
    {
        var system = """
            Sen Local AI OS için gerektiğinde kullanılan ücretsiz çevrimiçi düşünme katmanısın.
            Türkçe sorulara doğal Türkçe cevap ver. Doğruluğu önceliklendir ve bilmediğini uydurma.
            Sağlanan kaynak bilgisini yalnız ilgili olduğunda kullan. Son cevabı gereksiz uzatma.
            İnternet kaynağı kullanıldığında doğrulanabilir bağlantıları cevabın sonunda kısa bir Kaynaklar bölümünde belirt.
            """;
        if (!string.IsNullOrWhiteSpace(knowledge)) system += $"\n\nKaynak bağlamı:\n{knowledge}";
        var messages = new List<object> { new { role = "system", content = system } };
        messages.AddRange(history.Select(message => (object)new { role = message.Role, content = message.Content }));
        using var response = await _http.PostAsJsonAsync(Endpoint.ChatUrl, new
        {
            model = Endpoint.Model,
            messages,
            temperature = 0.3,
            max_tokens = 4096,
            stream = false
        }, cancellationToken);
        response.EnsureSuccessStatusCode();
        using var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync(cancellationToken));
        return document.RootElement.GetProperty("choices")[0].GetProperty("message")
            .GetProperty("content").GetString()?.Trim() ?? "Cevap üretilemedi.";
    }

    private static HttpClient CreateClient(string key)
    {
        var client = new HttpClient { Timeout = TimeSpan.FromMinutes(15) };
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", key);
        client.DefaultRequestHeaders.Add("HTTP-Referer", "https://local-ai-os.invalid");
        client.DefaultRequestHeaders.Add("X-Title", "Local AI OS");
        return client;
    }
}

internal static class ComputeRouter
{
    public static bool ShouldUseCloud(string request, bool projectTask, HardwareProfile hardware, AppSettings settings)
    {
        if (!settings.CloudEnabled || string.IsNullOrWhiteSpace(SecretStore.Read())) return false;
        if (projectTask && !settings.AllowProjectCloud) return false;
        var complexWords = new[] { "mimari", "baştan", "kapsamlı", "karmaşık", "analiz", "refactor", "debug", "hata", "uygulama" };
        var complexity = complexWords.Count(word => request.Contains(word, StringComparison.OrdinalIgnoreCase));
        return hardware.Model.Id == "compact" && (projectTask || request.Length > 180)
            || hardware.Model.Id == "standard" && projectTask && (complexity > 0 || request.Length > 400)
            || complexity >= 3;
    }
}

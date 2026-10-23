using System.Net.Http.Json;
using System.Text.Json;

namespace LocalAIOS;

internal sealed record ChatMessage(string Role, string Content);

internal sealed class LocalModelClient(int port)
{
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromMinutes(10) };

    public async Task<string> ChatAsync(
        IReadOnlyList<ChatMessage> history,
        string knowledge,
        bool deepThinking,
        CancellationToken cancellationToken)
    {
        var system = """
            Sen Local AI OS adlı, tamamen kullanıcının bilgisayarında çalışan kişisel yapay zekâsın.
            Türkçe sorulara doğal ve açık Türkçe cevap ver. Kullanıcının dilini takip et.
            Doğruluğu önceliklendir; bilmediğin şeyi uydurma. Cevapları gereksiz uzatma.
            Sağlanan yerel bilgi bağlamını yalnız ilgili olduğunda kullan.
            İnternet kaynağı kullanıldığında doğrulanabilir bağlantıları cevabın sonunda kısa bir Kaynaklar bölümünde belirt.
            """;
        if (!string.IsNullOrWhiteSpace(knowledge))
            system += $"\n\nYerel bilgi bağlamı:\n{knowledge[..Math.Min(knowledge.Length, 14000)]}";

        var messages = new List<object> { new { role = "system", content = system } };
        var recent = RecentHistory(history);
        messages.AddRange(recent.Select((message, index) => (object)new
        {
            role = message.Role,
            content = !deepThinking && index == recent.Count - 1 && message.Role == "user"
                ? "/no_think\n" + message.Content : message.Content
        }));
        var request = new Dictionary<string, object?>
        {
            ["model"] = "local-model",
            ["messages"] = messages,
            ["temperature"] = 0.35,
            ["max_tokens"] = deepThinking ? 3072 : 768,
            ["stream"] = false,
            ["reasoning_effort"] = deepThinking ? "medium" : "none",
            ["chat_template_kwargs"] = new { enable_thinking = deepThinking }
        };
        using var response = await _http.PostAsJsonAsync(
            $"http://127.0.0.1:{port}/v1/chat/completions", request, cancellationToken);
        response.EnsureSuccessStatusCode();
        using var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync(cancellationToken));
        return document.RootElement.GetProperty("choices")[0]
            .GetProperty("message").GetProperty("content").GetString()?.Trim()
            ?? "Cevap üretilemedi.";
    }

    private static List<ChatMessage> RecentHistory(IReadOnlyList<ChatMessage> history)
    {
        var selected = new List<ChatMessage>();
        var characters = 0;
        for (var index = history.Count - 1; index >= 0 && selected.Count < 16; index--)
        {
            var message = history[index];
            if (selected.Count > 0 && characters + message.Content.Length > 12000) break;
            selected.Add(message);
            characters += message.Content.Length;
        }
        selected.Reverse();
        return selected;
    }

    public async Task<string> GenerateAsync(
        string system, string request, CancellationToken cancellationToken, int maxTokens = 4096, bool json = false)
    {
        var messages = new object[]
        {
            new { role = "system", content = system },
            new { role = "user", content = "/no_think\n" + request }
        };
        var payload = new Dictionary<string, object?>
        {
            ["model"] = "local-model",
            ["messages"] = messages,
            ["temperature"] = 0.2,
            ["max_tokens"] = maxTokens,
            ["stream"] = false,
            ["reasoning_effort"] = "none",
            ["chat_template_kwargs"] = new { enable_thinking = false }
        };
        if (json) payload["response_format"] = new { type = "json_object" };
        using var response = await _http.PostAsJsonAsync(
            $"http://127.0.0.1:{port}/v1/chat/completions", payload, cancellationToken);
        response.EnsureSuccessStatusCode();
        using var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync(cancellationToken));
        return document.RootElement.GetProperty("choices")[0].GetProperty("message")
            .GetProperty("content").GetString()?.Trim() ?? "";
    }
}

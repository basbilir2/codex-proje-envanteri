namespace LocalAIOS;

internal sealed class ImageService
{
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromMinutes(5) };

    public async Task<string> GenerateAsync(string prompt, int size, CancellationToken cancellationToken)
    {
        AppPaths.EnsureDirectories();
        var encoded = Uri.EscapeDataString(prompt);
        var seed = Random.Shared.Next();
        var urls = new[]
        {
            $"https://gen.pollinations.ai/image/{encoded}?model=flux&width={size}&height={size}&nologo=true&seed={seed}",
            $"https://image.pollinations.ai/prompt/{encoded}?width={size}&height={size}&nologo=true&seed={seed}"
        };
        HttpResponseMessage? response = null;
        foreach (var url in urls)
        {
            response = await _http.GetAsync(url, HttpCompletionOption.ResponseHeadersRead, cancellationToken);
            if (response.IsSuccessStatusCode) break;
            response.Dispose();
            response = null;
        }
        using (response)
        {
            if (response is null) throw new InvalidOperationException("Ücretsiz görsel sağlayıcılarına ulaşılamadı.");
        var mediaType = response.Content.Headers.ContentType?.MediaType ?? "";
        if (!mediaType.StartsWith("image/", StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Görsel servisi geçerli bir resim döndürmedi.");
        var extension = mediaType.Contains("png", StringComparison.OrdinalIgnoreCase) ? ".png" : ".jpg";
        var file = Path.Combine(AppPaths.Artifacts, "Gorsel-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + extension);
        await using var input = await response.Content.ReadAsStreamAsync(cancellationToken);
        await using (var output = File.Create(file))
            await input.CopyToAsync(output, cancellationToken);
        if (new FileInfo(file).Length < 2000) throw new InvalidOperationException("Üretilen görsel dosyası geçersiz.");
        using var image = Image.FromFile(file);
        if (image.Width < size / 2 || image.Height < size / 2) throw new InvalidOperationException("Üretilen görsel boyutu geçersiz.");
        return file;
        }
    }
}

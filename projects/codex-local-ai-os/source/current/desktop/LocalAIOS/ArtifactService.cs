namespace LocalAIOS;

internal sealed class ArtifactService
{
    public async Task<string> CreateMiniAppAsync(string description, LocalModelClient model, CancellationToken cancellationToken)
    {
        var output = await model.GenerateAsync("""
            Create a complete, polished, working single-file HTML mini application.
            Include all CSS and JavaScript inside the HTML. Do not use external packages or network resources.
            Return only the HTML document, without markdown fences or explanations.
            The visible interface should follow the user's language.
            """, description, cancellationToken, 2600);
        var start = output.IndexOf("<!DOCTYPE", StringComparison.OrdinalIgnoreCase);
        if (start < 0) start = output.IndexOf("<html", StringComparison.OrdinalIgnoreCase);
        if (start > 0) output = output[start..];
        var fence = output.LastIndexOf("```", StringComparison.Ordinal);
        if (fence > 0) output = output[..fence];
        if (!output.Contains("<html", StringComparison.OrdinalIgnoreCase) || !output.Contains("</html>", StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Model geçerli bir mini uygulama üretemedi.");
        AppPaths.EnsureDirectories();
        var directory = Path.Combine(AppPaths.Artifacts, "MiniApp-" + DateTime.Now.ToString("yyyyMMdd-HHmmss"));
        Directory.CreateDirectory(directory);
        var file = Path.Combine(directory, "index.html");
        await File.WriteAllTextAsync(file, output, cancellationToken);
        return file;
    }
}

namespace LocalAIOS;

internal static class AppPaths
{
    private static readonly string DefaultRoot = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "LocalAIOS");
    public static readonly string Root = Environment.GetEnvironmentVariable("LOCALAIOS_DATA_ROOT") is { Length: > 0 } customRoot
        ? Path.GetFullPath(customRoot) : DefaultRoot;
    public static readonly string Runtime = Path.Combine(DefaultRoot, "runtime");
    public static readonly string Models = Path.Combine(DefaultRoot, "models");
    public static readonly string Knowledge = Path.Combine(Root, "knowledge");
    public static readonly string Plugins = Path.Combine(Root, "plugins");
    public static readonly string Artifacts = Path.Combine(Root, "artifacts");
    public static readonly string Settings = Path.Combine(Root, "settings.json");
    public static string Model(string fileName) => Path.Combine(Models, fileName);

    public static void EnsureDirectories()
    {
        Directory.CreateDirectory(Root);
        Directory.CreateDirectory(Runtime);
        Directory.CreateDirectory(Models);
        Directory.CreateDirectory(Knowledge);
        Directory.CreateDirectory(Plugins);
        Directory.CreateDirectory(Artifacts);
    }
}

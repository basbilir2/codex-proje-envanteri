using System.Globalization;

namespace THesap;

internal static class Program
{
    [STAThread]
    private static int Main(string[] args)
    {
        CultureInfo.DefaultThreadCurrentCulture = new CultureInfo("tr-TR");
        CultureInfo.DefaultThreadCurrentUICulture = new CultureInfo("tr-TR");
        if (args.Contains("--smoke-test", StringComparer.OrdinalIgnoreCase)) return SmokeTests.Run();
        ApplicationConfiguration.Initialize();
        Application.Run(new MainForm());
        return 0;
    }
}

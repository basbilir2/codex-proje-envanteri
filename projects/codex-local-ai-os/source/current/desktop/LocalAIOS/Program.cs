namespace LocalAIOS;

internal static class Program
{
    [STAThread]
    private static void Main(string[] args)
    {
        if (UpdateBootstrap.TryApply(args)) return;
        if (args.Length >= 1 && args[0] == "--self-test")
        {
            var report = args.Length >= 2 ? args[1] : Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "LocalAIOS", "self-test-report.json");
            Environment.SetEnvironmentVariable("LOCALAIOS_DATA_ROOT",
                Path.Combine(Path.GetDirectoryName(Path.GetFullPath(report))!, "self-test-data-" + DateTime.Now.ToString("yyyyMMdd-HHmmss")));
            Environment.ExitCode = SelfTestRunner.RunAsync(report).GetAwaiter().GetResult();
            return;
        }
        if (args.Length >= 1 && args[0] == "--image-test")
        {
            var report = args.Length >= 2 ? args[1] : Path.Combine(Path.GetTempPath(), "LocalAIOS-image-test.json");
            Environment.SetEnvironmentVariable("LOCALAIOS_DATA_ROOT",
                Path.Combine(Path.GetDirectoryName(Path.GetFullPath(report))!, "image-test-data-" + DateTime.Now.ToString("yyyyMMdd-HHmmss")));
            Environment.ExitCode = SelfTestRunner.RunImageAsync(report).GetAwaiter().GetResult();
            return;
        }
        if (args.Length >= 1 && args[0] == "--performance-test")
        {
            var report = args.Length >= 2 ? args[1] : Path.Combine(Path.GetTempPath(), "LocalAIOS-performance-test.json");
            Environment.ExitCode = SelfTestRunner.RunPerformanceAsync(report).GetAwaiter().GetResult();
            return;
        }
        if (args.Length >= 1 && args[0] == "--project-safety-test")
        {
            var report = args.Length >= 2 ? args[1] : Path.Combine(Path.GetTempPath(), "LocalAIOS-project-safety-test.json");
            Environment.ExitCode = SelfTestRunner.RunProjectSafetyAsync(report).GetAwaiter().GetResult();
            return;
        }
        ApplicationConfiguration.Initialize();
        Application.Run(new MainForm());
    }
}

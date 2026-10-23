using System.Diagnostics;
using System.Reflection;
using Microsoft.Win32;

namespace THesap.Setup;

internal static class Program
{
    [STAThread]
    private static int Main(string[] args)
    {
        var installDir = Argument(args, "--install-dir") ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "THesap");
        var uninstall = args.Contains("--uninstall", StringComparer.OrdinalIgnoreCase);
        if (uninstall) return Installer.Uninstall(installDir) ? 0 : 1;
        if (args.Contains("--smoke-test", StringComparer.OrdinalIgnoreCase)) return Installer.SmokeTest(installDir);
        if (args.Contains("--silent", StringComparer.OrdinalIgnoreCase)) return Installer.Install(installDir, !args.Contains("--no-launch", StringComparer.OrdinalIgnoreCase)) ? 0 : 1;
        ApplicationConfiguration.Initialize();
        var result = MessageBox.Show($"THesap şu klasöre kurulacak:\n{installDir}\n\nDevam edilsin mi?", "THesap Kurulum", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
        if (result != DialogResult.Yes) return 0;
        if (!Installer.Install(installDir, true)) { MessageBox.Show(Installer.LastError ?? "Kurulum tamamlanamadı.", "THesap Kurulum", MessageBoxButtons.OK, MessageBoxIcon.Error); return 1; }
        MessageBox.Show("THesap kuruldu ve açıldı.", "THesap Kurulum", MessageBoxButtons.OK, MessageBoxIcon.Information); return 0;
    }
    private static string? Argument(string[] args, string name) { var index = Array.FindIndex(args, x => x.Equals(name, StringComparison.OrdinalIgnoreCase)); return index >= 0 && index + 1 < args.Length ? args[index + 1] : null; }
}

internal static class Installer
{
    public static string? LastError { get; private set; }
    public static bool Install(string installDir, bool launch)
    {
        try
        {
            Directory.CreateDirectory(installDir); var target = Path.Combine(installDir, "THesap.exe");
            try { foreach (var process in Process.GetProcessesByName("THesap")) process.Kill(true); } catch { }
            using var source = Assembly.GetExecutingAssembly().GetManifestResourceStream("THesap.exe") ?? throw new InvalidOperationException("Kurulum paketi uygulamayı içermiyor.");
            using (var destination = File.Create(target + ".new")) source.CopyTo(destination); File.Move(target + ".new", target, true);
            var uninstaller = Path.Combine(installDir, "THesap_Kaldir.exe"); File.Copy(Environment.ProcessPath!, uninstaller, true);
            File.WriteAllText(Path.Combine(installDir, "setup-result.log"), "OK"); Register(installDir, target, uninstaller);
            if (launch) Process.Start(new ProcessStartInfo(target) { UseShellExecute = true }); return true;
        }
        catch (Exception ex) { LastError = ex.Message; return false; }
    }
    public static bool Uninstall(string installDir)
    {
        try { Registry.CurrentUser.DeleteSubKeyTree(@"Software\Microsoft\Windows\CurrentVersion\Uninstall\THesap", false); var exe = Path.Combine(installDir, "THesap.exe"); try { foreach (var process in Process.GetProcessesByName("THesap")) process.Kill(true); } catch { } if (File.Exists(exe)) File.Delete(exe); return true; } catch (Exception ex) { LastError = ex.Message; return false; }
    }
    public static int SmokeTest(string root)
    {
        var target = Path.Combine(root, "THesap-Setup-Smoke"); if (!Install(target, false) || !File.Exists(Path.Combine(target, "THesap.exe")) || !File.Exists(Path.Combine(target, "THesap_Kaldir.exe"))) return 1;
        using var process = Process.Start(new ProcessStartInfo(Path.Combine(target, "THesap.exe"), "--smoke-test") { UseShellExecute = false }); process?.WaitForExit(60000); return process is { HasExited: true, ExitCode: 0 } ? 0 : 1;
    }
    private static void Register(string dir, string exe, string uninstaller)
    {
        using var key = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Uninstall\THesap"); key?.SetValue("DisplayName", "THesap"); key?.SetValue("DisplayVersion", "1.0.0"); key?.SetValue("Publisher", "İzmirde Reklam"); key?.SetValue("InstallLocation", dir); key?.SetValue("DisplayIcon", exe); key?.SetValue("UninstallString", $"\"{uninstaller}\" --uninstall --install-dir \"{dir}\""); key?.SetValue("NoModify", 1, RegistryValueKind.DWord); key?.SetValue("NoRepair", 1, RegistryValueKind.DWord);
    }
}

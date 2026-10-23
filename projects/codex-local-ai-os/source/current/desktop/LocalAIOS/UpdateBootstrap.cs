using System.Diagnostics;

namespace LocalAIOS;

internal static class UpdateBootstrap
{
    public static bool TryApply(string[] args)
    {
        if (args.Length != 3 || args[0] != "--apply-update" || !int.TryParse(args[2], out var processId)) return false;
        try
        {
            Process.GetProcessById(processId).WaitForExit(30000);
        }
        catch { }
        var target = Path.GetFullPath(args[1]);
        var source = Environment.ProcessPath ?? throw new InvalidOperationException("Güncelleme dosyası bulunamadı.");
        File.Copy(source, target, true);
        Process.Start(new ProcessStartInfo(target) { UseShellExecute = true });
        return true;
    }
}

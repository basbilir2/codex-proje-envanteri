using System.Diagnostics;
using System.Text.Json;

namespace LocalAIOS;

internal static class PluginToolRunner
{
    public static async Task<string> RunAsync(
        IEnumerable<PluginManifest> plugins, string request, CancellationToken cancellationToken)
    {
        var outputs = new List<string>();
        foreach (var plugin in plugins)
        foreach (var tool in plugin.Tools.Where(item => item.AutoRun))
        {
            if (!plugin.Permissions.Contains("local_process", StringComparer.OrdinalIgnoreCase)) continue;
            var root = Path.GetFullPath(plugin.InstallDirectory) + Path.DirectorySeparatorChar;
            var executable = Path.GetFullPath(Path.Combine(plugin.InstallDirectory, tool.EntryPoint));
            if (!executable.StartsWith(root, StringComparison.OrdinalIgnoreCase) ||
                !Path.GetExtension(executable).Equals(".exe", StringComparison.OrdinalIgnoreCase) || !File.Exists(executable))
                throw new InvalidOperationException($"{plugin.Name} program aracı güvenle çalıştırılamadı.");

            using var process = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = executable,
                    WorkingDirectory = plugin.InstallDirectory,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardInput = true,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true
                }
            };
            process.Start();
            await process.StandardInput.WriteLineAsync(JsonSerializer.Serialize(new { request }, AppSettings.JsonOptions));
            process.StandardInput.Close();
            var stdoutTask = process.StandardOutput.ReadToEndAsync(cancellationToken);
            var stderrTask = process.StandardError.ReadToEndAsync(cancellationToken);
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            timeout.CancelAfter(TimeSpan.FromSeconds(Math.Clamp(tool.TimeoutSeconds, 1, 120)));
            try { await process.WaitForExitAsync(timeout.Token); }
            catch (OperationCanceledException)
            {
                try { process.Kill(true); } catch { }
                throw new TimeoutException($"{plugin.Name} program aracı zamanında tamamlanmadı.");
            }
            var stdout = await stdoutTask;
            var stderr = await stderrTask;
            if (process.ExitCode != 0)
                throw new InvalidOperationException($"{plugin.Name} program aracı hata verdi: {stderr[..Math.Min(stderr.Length, 500)]}");
            outputs.Add($"Program aracı ({plugin.Name}/{tool.Id}) çıktısı:\n{stdout[..Math.Min(stdout.Length, 100000)]}");
        }
        return string.Join("\n\n", outputs);
    }
}

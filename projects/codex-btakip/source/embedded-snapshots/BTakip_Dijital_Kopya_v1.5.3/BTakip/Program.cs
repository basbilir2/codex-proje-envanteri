using System.Globalization;

namespace BTakip;

internal static class Program
{
    private const string SingleInstanceMutexName = @"Local\BTakip_IzmirdeReklam_SingleInstance";
    private const string ActivationSignalName = @"Local\BTakip_IzmirdeReklam_Activate";

    [STAThread]
    private static int Main(string[] args)
    {
        CultureInfo.DefaultThreadCurrentCulture = new CultureInfo("tr-TR");
        CultureInfo.DefaultThreadCurrentUICulture = new CultureInfo("tr-TR");

        if (args.Contains("--smoke-test", StringComparer.OrdinalIgnoreCase))
            return SmokeTests.Run(args);

        var backupIndex = Array.FindIndex(args, x => x.Equals("--create-backup", StringComparison.OrdinalIgnoreCase));
        if (backupIndex >= 0)
        {
            if (backupIndex + 1 >= args.Length) return 6;
            try
            {
                var store = new DataStore();
                store.ExportFullBackup(args[backupIndex + 1]);
                return 0;
            }
            catch { return 7; }
        }

        var importIndex = Array.FindIndex(args, x => x.Equals("--import-excel", StringComparison.OrdinalIgnoreCase));
        if (importIndex >= 0)
        {
            if (importIndex + 1 >= args.Length || !File.Exists(args[importIndex + 1])) return 2;
            try
            {
                var store = new DataStore();
                var report = SimpleXlsx.Import(args[importIndex + 1], store);
                store.SaveAsync($"Komut satırı Excel içe aktarımı: {Path.GetFileName(args[importIndex + 1])}").GetAwaiter().GetResult();
                return report.Customers + report.Prices + report.Orders + report.Payments > 0 ? 0 : 3;
            }
            catch
            {
                return 1;
            }
        }

        if (args.Contains("--price-AnonPerson_0002-orders", StringComparer.OrdinalIgnoreCase))
        {
            try
            {
                var store = new DataStore();
                var report = ImportedOrderPricing.RepriceBetul(store);
                store.SaveAsync("AnonPerson_0005 ölçü ve hizmetlerden Reklamcı cari fiyatlandırması").GetAwaiter().GetResult();
                ImportedOrderPricing.SaveReport(report, Path.Combine(store.RootPath, "AnonPerson_0002_Hanim_Fiyatlama_Raporu.json"));
                return 0;
            }
            catch
            {
                return 1;
            }
        }

        string? restoreMessage = null;
        var restoreIndex = Array.FindIndex(args, x => x.Equals("--restore-backup", StringComparison.OrdinalIgnoreCase));
        if (restoreIndex >= 0)
        {
            if (restoreIndex + 1 >= args.Length || !File.Exists(args[restoreIndex + 1])) return 4;
            try
            {
                var store = new DataStore();
                store.CaptureUndo("Kurulum sırasında tam yedek yüklendi");
                store.ImportFullBackupAsync(args[restoreIndex + 1]).GetAwaiter().GetResult();
                restoreMessage = "Önceki BTakip tam yedeği başarıyla yüklendi.";
                if (args.Contains("--restore-only", StringComparer.OrdinalIgnoreCase)) return 0;
            }
            catch { return 5; }
        }

        using var activationSignal = new EventWaitHandle(false, EventResetMode.AutoReset, ActivationSignalName);
        using var instanceMutex = new Mutex(true, SingleInstanceMutexName, out var isFirstInstance);
        if (!isFirstInstance)
        {
            activationSignal.Set();
            return 0;
        }

        try
        {
            ApplicationConfiguration.Initialize();
            var form = new MainForm(args);
            _ = form.Handle;
            var activationThread = new Thread(() =>
            {
                while (!form.IsDisposed)
                {
                    try
                    {
                        activationSignal.WaitOne();
                        if (!form.IsDisposed) form.BeginInvoke((Action)form.RestoreFromExternalLaunch);
                    }
                    catch (InvalidOperationException) { return; }
                }
            }) { IsBackground = true, Name = "BTakip pencere etkinleştirme" };
            activationThread.Start();
            if (restoreMessage is not null) form.Shown += (_, _) => MessageBox.Show(restoreMessage, "Yedek Yüklendi", MessageBoxButtons.OK, MessageBoxIcon.Information);
            Application.Run(form);
            return 0;
        }
        finally
        {
            instanceMutex.ReleaseMutex();
        }
    }
}

using System.Diagnostics;
using System.IO.Compression;
using System.Reflection;
using System.Security.Cryptography;
using System.Runtime.InteropServices;
using System.Text.Json;
using Microsoft.Win32;

namespace BTakip.Setup;

internal static class Program
{
    [STAThread]
    private static int Main(string[] args)
    {
        var installer = new Installer();
        var dir = GetArgument(args, "--install-dir") ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "BTakip");
        var launchedAsUninstaller = Path.GetFileNameWithoutExtension(Environment.ProcessPath ?? "").Contains("Kaldir", StringComparison.OrdinalIgnoreCase);
        if (args.Contains("--uninstall", StringComparer.OrdinalIgnoreCase) || (launchedAsUninstaller && !args.Contains("--uninstall-ui", StringComparer.OrdinalIgnoreCase)))
        {
            var temp = Path.Combine(Path.GetTempPath(), "BTakip_Kaldir_" + Guid.NewGuid().ToString("N") + ".exe");
            File.Copy(Environment.ProcessPath!, temp, true);
            Process.Start(new ProcessStartInfo(temp, $"--uninstall-ui --install-dir \"{dir}\" --wait-for-pid {Environment.ProcessId}") { UseShellExecute = true });
            return 0;
        }
        if (args.Contains("--uninstall-ui", StringComparer.OrdinalIgnoreCase))
        {
            var waitText = GetArgument(args, "--wait-for-pid");
            if (int.TryParse(waitText, out var waitPid) && waitPid != Environment.ProcessId)
            {
                try { Process.GetProcessById(waitPid).WaitForExit(10000); } catch { }
            }
            ApplicationConfiguration.Initialize();
            Application.Run(new UninstallForm(installer, dir));
            return 0;
        }
        if (args.Contains("--smoke-test", StringComparer.OrdinalIgnoreCase))
            return installer.SmokeTest(dir);
        if (args.Contains("--silent", StringComparer.OrdinalIgnoreCase))
            return installer.Install(dir, !args.Contains("--no-launch", StringComparer.OrdinalIgnoreCase), true) ? 0 : 1;

        ApplicationConfiguration.Initialize();
        Application.Run(new SetupForm(installer, dir));
        return 0;
    }

    private static string? GetArgument(string[] args, string key)
    {
        var index = Array.FindIndex(args, x => x.Equals(key, StringComparison.OrdinalIgnoreCase));
        return index >= 0 && index + 1 < args.Length ? args[index + 1] : null;
    }
}

internal sealed class Installer
{
    public string? LastError { get; private set; }

    public bool Install(string installDir, bool launch, bool createShortcuts = true)
    {
        try
        {
            Directory.CreateDirectory(installDir);
            var target = Path.Combine(installDir, "BTakip.exe");
            if (createShortcuts) BackupUserData();
            StopInstalledApplication(target);
            BackupPreviousApplication(target, installDir);
            var temp = target + ".new";
            using (var input = Assembly.GetExecutingAssembly().GetManifestResourceStream("BTakip_Portable.exe")
                               ?? throw new InvalidOperationException("Kurulum paketindeki BTakip uygulaması bulunamadı."))
            using (var output = File.Create(temp)) input.CopyTo(output);
            File.Move(temp, target, true);
            WriteChecksum(target);
            var uninstall = Path.Combine(installDir, "BTakip_Kaldir.exe");
            var setupExecutable = Environment.ProcessPath ?? throw new InvalidOperationException("Kurulum uygulaması yolu bulunamadı.");
            if (!Path.GetFullPath(setupExecutable).Equals(Path.GetFullPath(uninstall), StringComparison.OrdinalIgnoreCase))
                File.Copy(setupExecutable, uninstall, true);

            if (createShortcuts)
            {
                try
                {
                    CreateShortcut(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), "BTakip.url"), target);
                    var startDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), "BTakip");
                    Directory.CreateDirectory(startDir);
                    CreateShortcut(Path.Combine(startDir, "BTakip.url"), target);
                    CreateShortcut(Path.Combine(startDir, "BTakip'i Kaldır.url"), uninstall);
                    RegisterInstall(installDir, target, uninstall);
                }
                // Kısıtlı bir kullanıcı profili kısayol kaydını engellese bile ana
                // uygulama ve mevcut veriler doğru kurulduysa güncellemeyi bozma.
                catch (UnauthorizedAccessException) { }
                catch (IOException) { }
            }
            Directory.CreateDirectory(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "btakip"));
            File.WriteAllText(Path.Combine(installDir, "setup-result.log"), $"OK{Environment.NewLine}Desktop={Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory)}{Environment.NewLine}Programs={Environment.GetFolderPath(Environment.SpecialFolder.Programs)}");
            if (launch) Process.Start(new ProcessStartInfo(target) { UseShellExecute = true });
            return true;
        }
        catch (Exception ex)
        {
            LastError = ex.ToString();
            try { Directory.CreateDirectory(installDir); File.WriteAllText(Path.Combine(installDir, "setup-result.log"), "ERROR" + Environment.NewLine + ex); } catch { }
            return false;
        }
    }

    public int SmokeTest(string root)
    {
        var targetDir = Path.Combine(root, "BTakip-Setup-Smoke");
        if (!Install(targetDir, false, false))
        {
            Console.Error.WriteLine("SETUP TEST BAŞARISIZ: " + LastError);
            return 1;
        }
        var exe = Path.Combine(targetDir, "BTakip.exe");
        var uninstaller = Path.Combine(targetDir, "BTakip_Kaldir.exe");
        if (!File.Exists(exe) || new FileInfo(exe).Length < 1_000_000 || !VerifyChecksum(exe) || !File.Exists(uninstaller))
        {
            Console.Error.WriteLine("SETUP TEST BAŞARISIZ: Kurulan uygulama veya kaldırıcı bulunamadı.");
            return 1;
        }
        var smokeData = Path.Combine(targetDir, "smoke-data");
        using var process = Process.Start(new ProcessStartInfo(exe, $"--smoke-test --data-dir \"{smokeData}\"") { UseShellExecute = false });
        process?.WaitForExit(60000);
        if (process is null || !process.HasExited || process.ExitCode != 0)
        {
            try { if (process is not null && !process.HasExited) process.Kill(true); } catch { }
            Console.Error.WriteLine("SETUP TEST BAŞARISIZ: Kurulan BTakip kritik testten geçmedi.");
            return 1;
        }
        if (!Uninstall(targetDir, true, false) || Directory.Exists(targetDir))
        {
            Console.Error.WriteLine("SETUP TEST BAŞARISIZ: Program Ekle/Kaldır çekirdek kaldırma işlemi tamamlanamadı. " + LastError);
            return 1;
        }
        Console.WriteLine("SETUP TEST BAŞARILI: " + exe);
        return 0;
    }

    public bool HasExistingData() => File.Exists(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "btakip", "btakip-veri.json"));

    public string? FindLatestBackup()
    {
        var directories = new[]
        {
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "btakip"),
            Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),
            Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Downloads")
        };
        return directories.Where(Directory.Exists)
            .SelectMany(path => Directory.EnumerateFiles(path, "*.btakip", SearchOption.TopDirectoryOnly))
            .OrderByDescending(File.GetLastWriteTimeUtc).FirstOrDefault();
    }

    public void LaunchInstalled(string installDir, string? backup = null)
    {
        var target = Path.Combine(installDir, "BTakip.exe");
        var args = backup is null ? "" : $"--restore-backup \"{backup}\"";
        Process.Start(new ProcessStartInfo(target, args) { UseShellExecute = true });
    }

    public bool CreateFullBackup(string path)
    {
        try
        {
            var root = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "btakip");
            var dataFile = Path.Combine(root, "btakip-veri.json");
            if (!File.Exists(dataFile)) throw new FileNotFoundException("Yedeklenecek BTakip veri dosyası bulunamadı.", dataFile);
            if (!VerifyChecksum(dataFile)) throw new InvalidDataException("BTakip veri dosyasının bütünlüğü doğrulanamadı; kaldırma durduruldu.");

            var fullPath = Path.ChangeExtension(Path.GetFullPath(path), ".btakip");
            Directory.CreateDirectory(Path.GetDirectoryName(fullPath)!);
            var temp = fullPath + ".tmp";
            if (File.Exists(temp)) File.Delete(temp);
            var data = File.ReadAllBytes(dataFile);
            var manifest = new FullBackupManifest(1, DateTime.UtcNow, Environment.MachineName, Convert.ToHexString(SHA256.HashData(data)));
            using (var archive = ZipFile.Open(temp, ZipArchiveMode.Create))
            {
                var dataEntry = archive.CreateEntry("btakip-veri.json", CompressionLevel.Optimal);
                using (var stream = dataEntry.Open()) stream.Write(data);
                var manifestEntry = archive.CreateEntry("yedek-bilgisi.json", CompressionLevel.Optimal);
                using (var writer = new StreamWriter(manifestEntry.Open())) writer.Write(JsonSerializer.Serialize(manifest, new JsonSerializerOptions { WriteIndented = true }));
                var workbook = Path.Combine(root, "BTakip_Yedek_Son.xlsx");
                if (File.Exists(workbook)) archive.CreateEntryFromFile(workbook, "BTakip_Yedek_Son.xlsx", CompressionLevel.Optimal);
            }
            File.Move(temp, fullPath, true);
            return true;
        }
        catch (Exception ex) { LastError = ex.ToString(); return false; }
    }

    public bool Uninstall(string installDir, bool keepData, bool removeRegistration = true)
    {
        try
        {
            var fullInstall = Path.GetFullPath(installDir).TrimEnd(Path.DirectorySeparatorChar);
            var marker = Path.Combine(fullInstall, "setup-result.log");
            if (!IsSafeInstallDirectory(fullInstall) || !File.Exists(marker) || !File.ReadAllText(marker).StartsWith("OK", StringComparison.Ordinal))
                throw new InvalidOperationException("Kaldırılacak BTakip kurulum klasörü doğrulanamadı.");
            var target = Path.Combine(fullInstall, "BTakip.exe");
            StopInstalledApplication(target);
            if (removeRegistration)
            {
                var desktopShortcut = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), "BTakip.url");
                if (File.Exists(desktopShortcut)) File.Delete(desktopShortcut);
                var startDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), "BTakip");
                if (Directory.Exists(startDir)) Directory.Delete(startDir, true);
                using var run = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Run", true);
                run?.DeleteValue("BTakip", false);
            }
            DeleteDirectoryWithRetry(fullInstall);
            if (removeRegistration) Registry.CurrentUser.DeleteSubKeyTree(@"Software\Microsoft\Windows\CurrentVersion\Uninstall\BTakip", false);
            if (!keepData)
            {
                var dataRoot = Path.GetFullPath(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "btakip")).TrimEnd(Path.DirectorySeparatorChar);
                if (Path.GetFileName(dataRoot).Equals("btakip", StringComparison.OrdinalIgnoreCase) && Directory.Exists(dataRoot)) Directory.Delete(dataRoot, true);
            }
            NativeMethods.MoveFileEx(Environment.ProcessPath!, null, 4);
            return true;
        }
        catch (Exception ex) { LastError = ex.ToString(); return false; }
    }

    private static void CreateShortcut(string shortcutPath, string target)
    {
        var url = new Uri(target).AbsoluteUri;
        File.WriteAllText(shortcutPath, $"[InternetShortcut]{Environment.NewLine}URL={url}{Environment.NewLine}IconFile={target}{Environment.NewLine}IconIndex=0{Environment.NewLine}");
    }

    private static void RegisterInstall(string installDir, string target, string uninstall)
    {
        using var key = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Uninstall\BTakip");
        var version = FileVersionInfo.GetVersionInfo(target).ProductVersion ?? Assembly.GetExecutingAssembly().GetName().Version?.ToString(3) ?? "1.0.0";
        key?.SetValue("DisplayName", "BTakip");
        key?.SetValue("DisplayVersion", version);
        key?.SetValue("Publisher", "İzmirde Reklam");
        key?.SetValue("InstallLocation", installDir);
        key?.SetValue("DisplayIcon", target);
        key?.SetValue("UninstallString", $"\"{uninstall}\" --uninstall --install-dir \"{installDir}\"");
        key?.SetValue("QuietUninstallString", $"\"{uninstall}\" --uninstall --install-dir \"{installDir}\"");
        key?.SetValue("InstallDate", DateTime.Now.ToString("yyyyMMdd"));
        key?.SetValue("EstimatedSize", (int)Math.Min(int.MaxValue, (new FileInfo(target).Length + new FileInfo(uninstall).Length) / 1024), RegistryValueKind.DWord);
        key?.SetValue("NoRemove", 0, RegistryValueKind.DWord);
        key?.SetValue("NoModify", 1, RegistryValueKind.DWord);
        key?.SetValue("NoRepair", 1, RegistryValueKind.DWord);
        key?.SetValue("SystemComponent", 0, RegistryValueKind.DWord);
        key?.SetValue("WindowsInstaller", 0, RegistryValueKind.DWord);
    }

    private static void StopInstalledApplication(string target)
    {
        var fullTarget = Path.GetFullPath(target);
        foreach (var process in Process.GetProcesses())
        {
            try
            {
                if (process.Id == Environment.ProcessId || !Path.GetFullPath(process.MainModule?.FileName ?? "").Equals(fullTarget, StringComparison.OrdinalIgnoreCase)) continue;
                process.CloseMainWindow();
                if (!process.WaitForExit(1500)) process.Kill(true);
                process.WaitForExit(3000);
            }
            catch { }
            finally { process.Dispose(); }
        }
    }

    private static bool IsSafeInstallDirectory(string path)
    {
        var blocked = new[]
        {
            Path.GetPathRoot(path),
            Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles),
            Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86)
        }.Where(value => !string.IsNullOrWhiteSpace(value)).Select(value => Path.GetFullPath(value!).TrimEnd(Path.DirectorySeparatorChar));
        return !blocked.Any(value => value.Equals(path, StringComparison.OrdinalIgnoreCase));
    }

    private static void DeleteDirectoryWithRetry(string path)
    {
        Exception? lastError = null;
        for (var attempt = 0; attempt < 5; attempt++)
        {
            try
            {
                if (Directory.Exists(path)) Directory.Delete(path, true);
                return;
            }
            catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
            {
                lastError = ex;
                Thread.Sleep(300);
            }
        }
        throw new IOException("BTakip kurulum klasörü kaldırılamadı.", lastError);
    }

    private static void BackupUserData()
    {
        try
        {
            var root = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "btakip");
            if (!Directory.Exists(root)) return;
            var backup = Path.Combine(root, "Yedekler", "Yazilim-Guncelleme-Oncesi-" + DateTime.Now.ToString("yyyyMMdd-HHmmssfff"));
            Directory.CreateDirectory(backup);
            foreach (var name in new[] { "btakip-veri.json", "btakip-veri.json.sha256", "BTakip_Yedek_Son.xlsx", "BTakip_Yedek_Son.xlsx.sha256", "btakip.log", "yazilim-butunluk.json" })
            {
                var source = Path.Combine(root, name);
                if (File.Exists(source)) File.Copy(source, Path.Combine(backup, name), true);
            }
        }
        // Ana veri yerinde kalır. Yalnızca ek güncelleme kopyası alınamadığında
        // kurulumun güvenli dosya değişimini gereksiz yere engelleme.
        catch (UnauthorizedAccessException) { }
        catch (IOException) { }
    }

    private static void BackupPreviousApplication(string target, string installDir)
    {
        if (!File.Exists(target)) return;
        var backup = Path.Combine(installDir, "OncekiSurum");
        Directory.CreateDirectory(backup);
        var saved = Path.Combine(backup, "BTakip-" + DateTime.Now.ToString("yyyyMMdd-HHmmssfff") + ".exe");
        File.Copy(target, saved, true);
        if (File.Exists(target + ".sha256")) File.Copy(target + ".sha256", saved + ".sha256", true);
    }

    private static void WriteChecksum(string path) => File.WriteAllText(path + ".sha256", Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))) + "  " + Path.GetFileName(path));

    private static bool VerifyChecksum(string path)
    {
        var sidecar = path + ".sha256";
        if (!File.Exists(path) || !File.Exists(sidecar)) return false;
        var expected = File.ReadAllText(sidecar).Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries).FirstOrDefault();
        return expected?.Equals(Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))), StringComparison.OrdinalIgnoreCase) == true;
    }

    private sealed record FullBackupManifest(int FormatVersion, DateTime CreatedAtUtc, string SourceComputer, string DataSha256);
}

internal sealed class SetupForm : Form
{
    private readonly Installer _installer;
    private readonly TextBox _path;
    private readonly Button _install;
    private readonly Label _status;

    public SetupForm(Installer installer, string defaultPath)
    {
        _installer = installer;
        Text = "İzmirde Reklam Kurulumu";
        Width = 620; Height = 410; FormBorderStyle = FormBorderStyle.FixedDialog; MaximizeBox = false;
        StartPosition = FormStartPosition.CenterScreen; BackColor = Color.White; Font = new Font("Segoe UI", 10f);
        var header = new Panel { Dock = DockStyle.Top, Height = 105, BackColor = Color.FromArgb(20, 48, 65) };
        header.Controls.Add(new Label { Text = "BTakip", ForeColor = Color.White, Font = new Font("Segoe UI Semibold", 25f), AutoSize = true, Location = new Point(28, 18) });
        header.Controls.Add(new Label { Text = "İzmirde Reklam Müşteri Takip kurulumu", ForeColor = Color.FromArgb(183, 213, 220), Font = new Font("Segoe UI", 10f), AutoSize = true, Location = new Point(31, 64) });
        var description = new Label { Text = "Uygulama bu bilgisayara kurulacak, masaüstü ve Başlat menüsü kısayolları oluşturulacaktır. Veriler kullanıcı klasöründeki btakip klasöründe saklanır.", AutoSize = true, MaximumSize = new Size(540, 0), Location = new Point(30, 130), ForeColor = Color.FromArgb(55, 67, 74) };
        var pathLabel = new Label { Text = "Kurulum klasörü", AutoSize = true, Location = new Point(30, 205), ForeColor = Color.FromArgb(20, 48, 65), Font = new Font("Segoe UI Semibold", 9.5f) };
        _path = new TextBox { Text = defaultPath, Location = new Point(30, 228), Width = 535, Height = 30 };
        _install = new Button { Text = "Kur", Location = new Point(445, 280), Width = 120, Height = 42, FlatStyle = FlatStyle.Flat, BackColor = Color.FromArgb(29, 122, 126), ForeColor = Color.White, Font = new Font("Segoe UI Semibold", 10f) };
        _install.FlatAppearance.BorderSize = 0;
        _install.Click += Install_Click;
        _status = new Label { Text = "Hazır", AutoSize = true, Location = new Point(30, 294), ForeColor = Color.FromArgb(102, 117, 126) };
        Controls.AddRange([header, description, pathLabel, _path, _install, _status]);
    }

    private async void Install_Click(object? sender, EventArgs e)
    {
        _install.Enabled = false; _status.Text = "Kuruluyor…";
        var installDir = _path.Text.Trim();
        var ok = await Task.Run(() => _installer.Install(installDir, false));
        if (ok)
        {
            _status.Text = "Kurulum tamamlandı.";
            string? backup = null;
            if (!_installer.HasExistingData())
            {
                backup = _installer.FindLatestBackup();
                if (backup is not null)
                {
                    var useBackup = MessageBox.Show(
                        $"Bu bilgisayarda önceki BTakip verisi yok. Bir tam yedek bulundu:\n\n{backup}\n\nMüşterileri, fiyatları, siparişleri, tahsilatları ve ayarları bu yedekten devralmak ister misiniz?",
                        "BTakip Yedeği Bulundu", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
                    if (useBackup != DialogResult.Yes) backup = null;
                }
            }
            _installer.LaunchInstalled(installDir, backup);
            MessageBox.Show(backup is null
                    ? "BTakip başarıyla kuruldu ve açılıyor. Mevcut verileriniz korunmuştur."
                    : "BTakip başarıyla kuruldu. Bulunan tam yedek açılışta içe alınacaktır.",
                "BTakip Kurulumu", MessageBoxButtons.OK, MessageBoxIcon.Information);
            Close();
        }
        else
        {
            _status.Text = "Kurulum tamamlanamadı."; _install.Enabled = true;
            MessageBox.Show(_installer.LastError, "BTakip Kurulumu", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}

internal sealed class UninstallForm : Form
{
    private readonly Installer _installer;
    private readonly string _installDir;
    private readonly CheckBox _keepData;
    private readonly Button _remove;
    private readonly Label _status;

    public UninstallForm(Installer installer, string installDir)
    {
        _installer = installer; _installDir = installDir;
        Text = "BTakip'i Kaldır";
        Width = 600; Height = 365; FormBorderStyle = FormBorderStyle.FixedDialog; MaximizeBox = false;
        StartPosition = FormStartPosition.CenterScreen; BackColor = Color.White; Font = new Font("Segoe UI", 10f);
        var header = new Panel { Dock = DockStyle.Top, Height = 95, BackColor = Color.FromArgb(20, 48, 65) };
        header.Controls.Add(new Label { Text = "BTakip'i Kaldır", ForeColor = Color.White, Font = new Font("Segoe UI Semibold", 22f), AutoSize = true, Location = new Point(28, 24) });
        var description = new Label
        {
            Text = "Yazılım bu bilgisayardan kaldırılır. Google tablolarındaki kayıtlar hiçbir zaman silinmez veya değiştirilmez.",
            AutoSize = true, MaximumSize = new Size(530, 0), Location = new Point(30, 120), ForeColor = Color.FromArgb(55, 67, 74)
        };
        _keepData = new CheckBox
        {
            Text = "BTakip verilerimi ve yerel yedeklerimi sakla",
            Checked = true, AutoSize = true, Location = new Point(30, 180),
            Font = new Font("Segoe UI Semibold", 10f), ForeColor = Color.FromArgb(20, 48, 65)
        };
        var hint = new Label
        {
            Text = "Önerilen: İşaretli bırakın. Yeniden kurduğunuzda kaldığınız yerden devam edebilirsiniz.",
            AutoSize = true, MaximumSize = new Size(520, 0), Location = new Point(50, 209), ForeColor = Color.FromArgb(102, 117, 126)
        };
        _remove = new Button { Text = "Kaldır", Location = new Point(430, 260), Width = 125, Height = 42, FlatStyle = FlatStyle.Flat, BackColor = Color.FromArgb(180, 67, 57), ForeColor = Color.White, Font = new Font("Segoe UI Semibold", 10f) };
        _remove.FlatAppearance.BorderSize = 0; _remove.Click += Remove_Click;
        var cancel = new Button { Text = "Vazgeç", Location = new Point(295, 260), Width = 125, Height = 42, FlatStyle = FlatStyle.Flat, BackColor = Color.White, ForeColor = Color.FromArgb(20, 48, 65) };
        cancel.FlatAppearance.BorderColor = Color.FromArgb(180, 190, 195); cancel.Click += (_, _) => Close();
        _status = new Label { Text = "Hazır", AutoSize = true, Location = new Point(30, 274), ForeColor = Color.FromArgb(102, 117, 126) };
        Controls.AddRange([header, description, _keepData, hint, cancel, _remove, _status]);
    }

    private async void Remove_Click(object? sender, EventArgs e)
    {
        string? backupPath = null;
        if (_installer.HasExistingData())
        {
            var backupChoice = MessageBox.Show(
                "BTakip'i kaldırmadan önce tüm müşterileri, fiyatları, malzemeleri, siparişleri, tahsilatları ve ayarları tek dosyada yedeklemek ister misiniz?\n\nBu dosya yeni BTakip kurulumunda tek seçimle geri yüklenebilir.",
                "Kaldırmadan Önce Yedekle", MessageBoxButtons.YesNoCancel, MessageBoxIcon.Question);
            if (backupChoice == DialogResult.Cancel) return;
            if (backupChoice == DialogResult.Yes)
            {
                using var dialog = new SaveFileDialog
                {
                    Title = "BTakip Tüm Verileri Yedekle",
                    Filter = "BTakip tam yedek (*.btakip)|*.btakip",
                    FileName = $"BTakip_Tum_Veriler_{DateTime.Now:yyyyMMdd_HHmm}.btakip",
                    InitialDirectory = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory)
                };
                if (dialog.ShowDialog(this) != DialogResult.OK) return;
                _remove.Enabled = false; _status.Text = "Tüm veriler yedekleniyor…";
                var backupOk = await Task.Run(() => _installer.CreateFullBackup(dialog.FileName));
                if (!backupOk)
                {
                    _remove.Enabled = true; _status.Text = "Yedek oluşturulamadı; kaldırma durduruldu.";
                    MessageBox.Show(_installer.LastError, "BTakip Yedekleme", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return;
                }
                backupPath = Path.ChangeExtension(dialog.FileName, ".btakip");
            }
        }
        if (!_keepData.Checked)
        {
            var confirm = MessageBox.Show(
                "Bu seçenek BTakip'in bu bilgisayardaki müşterilerini, siparişlerini, tahsilatlarını, ayarlarını ve yerel yedeklerini kalıcı olarak siler. Devam edilsin mi?",
                "Yerel Verileri de Sil", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
            if (confirm != DialogResult.Yes) return;
        }
        _remove.Enabled = false; _status.Text = "Kaldırılıyor…";
        var ok = await Task.Run(() => _installer.Uninstall(_installDir, _keepData.Checked));
        if (!ok)
        {
            _remove.Enabled = true; _status.Text = "Kaldırma tamamlanamadı.";
            MessageBox.Show(_installer.LastError, "BTakip'i Kaldır", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }
        var result = _keepData.Checked
                ? "BTakip kaldırıldı. Yerel verileriniz ve yedekleriniz saklandı."
                : "BTakip ve bu bilgisayardaki yerel veriler kaldırıldı. Google tablolarına dokunulmadı.";
        if (backupPath is not null) result += $"\n\nTüm veriler tek dosyada yedeklendi:\n{backupPath}\n\nYeni BTakip kurulumunda bu dosyayı seçerek tüm verileri tek adımda geri yükleyebilirsiniz.";
        MessageBox.Show(result,
            "BTakip'i Kaldır", MessageBoxButtons.OK, MessageBoxIcon.Information);
        Close();
    }
}

internal static class NativeMethods
{
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    internal static extern bool MoveFileEx(string lpExistingFileName, string? lpNewFileName, int dwFlags);
}

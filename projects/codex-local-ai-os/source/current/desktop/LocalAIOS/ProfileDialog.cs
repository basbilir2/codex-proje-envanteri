namespace LocalAIOS;

internal sealed class ProfileDialog : Form
{
    private readonly AppSettings _settings;
    private readonly ProfileTransferService _transfer;
    private readonly Label _status = new();

    public ProfileDialog(AppSettings settings)
    {
        _settings = settings;
        _transfer = new(settings);
        Text = "Hafıza ve bağlam";
        Size = new Size(610, 310);
        StartPosition = FormStartPosition.CenterParent;
        BackColor = Color.FromArgb(24, 27, 34);
        ForeColor = Color.White;
        Font = new Font("Segoe UI", 10);
        Controls.Add(new Label
        {
            Text = "Kaynak yollarını, öğrenilen dersleri ve eklentileri başka bilgisayara taşıyabilir\nveya ücretsiz bir eşitlenen klasör üzerinden otomatik devam edebilirsin.",
            Left = 22, Top = 20, Width = 550, Height = 52
        });
        var export = new Button { Text = "Profili dışa aktar", Left = 22, Top = 92, Width = 160, Height = 38 };
        var import = new Button { Text = "Profili içe aktar", Left = 194, Top = 92, Width = 160, Height = 38 };
        var sync = new Button { Text = "Eşitleme klasörü seç", Left = 366, Top = 92, Width = 195, Height = 38 };
        export.Click += async (_, _) => await ExportAsync();
        import.Click += async (_, _) => await ImportAsync();
        sync.Click += async (_, _) => await SelectSyncAsync();
        _status.SetBounds(22, 151, 540, 45);
        _status.ForeColor = Color.FromArgb(154, 163, 180);
        _status.Text = string.IsNullOrWhiteSpace(settings.SyncFolder) ? "Otomatik eşitleme kapalı." : $"Eşitleme: {settings.SyncFolder}";
        var close = new Button { Text = "Kapat", DialogResult = DialogResult.OK, Left = 471, Top = 215, Width = 90 };
        Controls.AddRange([export, import, sync, _status, close]);
        AcceptButton = close;
    }

    private async Task ExportAsync()
    {
        using var picker = new SaveFileDialog { Filter = "Local AI profili (*.laios)|*.laios", FileName = "LocalAIOS-profile.laios" };
        if (picker.ShowDialog(this) != DialogResult.OK) return;
        await _transfer.ExportAsync(picker.FileName, CancellationToken.None);
        _status.Text = "Profil dışa aktarıldı.";
    }

    private async Task ImportAsync()
    {
        using var picker = new OpenFileDialog { Filter = "Local AI profili (*.laios)|*.laios" };
        if (picker.ShowDialog(this) != DialogResult.OK) return;
        await _transfer.ImportAsync(picker.FileName, CancellationToken.None);
        _status.Text = "Profil alındı. Yapay zekâ kaldığı bağlamla devam edebilir.";
    }

    private async Task SelectSyncAsync()
    {
        using var picker = new FolderBrowserDialog { Description = "OneDrive, Google Drive veya başka bir eşitlenen klasör seçin", UseDescriptionForTitle = true };
        if (picker.ShowDialog(this) != DialogResult.OK) return;
        _settings.SyncFolder = picker.SelectedPath;
        _settings.Save();
        await _transfer.PushAsync(CancellationToken.None);
        _status.Text = $"Otomatik eşitleme açık: {_settings.SyncFolder}";
    }
}

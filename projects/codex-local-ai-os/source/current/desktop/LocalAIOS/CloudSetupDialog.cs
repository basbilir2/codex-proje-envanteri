using System.Diagnostics;

namespace LocalAIOS;

internal sealed class CloudSetupDialog : Form
{
    private readonly TextBox _key = new();
    private readonly CheckBox _enabled = new();
    private readonly CheckBox _projectPermission = new();
    private readonly AppSettings _settings;

    public CloudSetupDialog(AppSettings settings)
    {
        _settings = settings;
        Text = "Ücretsiz çevrimiçi güç";
        Width = 610;
        Height = 330;
        StartPosition = FormStartPosition.CenterParent;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = false;
        BackColor = Color.FromArgb(24, 27, 34);
        ForeColor = Color.White;
        Font = new Font("Segoe UI", 10);

        Controls.Add(new Label
        {
            Text = "Yerel donanım yetersiz kaldığında OpenRouter'ın ücretsiz modelleri kullanılabilir.\nÜcretsiz hesap anahtarı gerekir; kota ve erişim sağlayıcıya bağlıdır.",
            Left = 22, Top = 18, Width = 550, Height = 52
        });
        var account = new LinkLabel { Text = "Ücretsiz anahtar oluştur", Left = 22, Top = 76, Width = 190, LinkColor = Color.FromArgb(133, 148, 255) };
        account.LinkClicked += (_, _) => Process.Start(new ProcessStartInfo("https://openrouter.ai/settings/keys") { UseShellExecute = true });
        Controls.Add(account);
        Controls.Add(new Label { Text = "Anahtar:", Left = 22, Top = 111, Width = 80 });
        _key.SetBounds(100, 106, 465, 28);
        _key.UseSystemPasswordChar = true;
        _key.Text = SecretStore.Read() is null ? "" : "••••••••••••";
        Controls.Add(_key);
        _enabled.Text = "Gerektiğinde ücretsiz cloud kullan";
        _enabled.SetBounds(22, 151, 300, 28);
        _enabled.Checked = settings.CloudEnabled;
        _projectPermission.Text = "Proje görevlerinde ilgili kod parçalarının gönderilmesine izin ver";
        _projectPermission.SetBounds(22, 185, 520, 28);
        _projectPermission.Checked = settings.AllowProjectCloud;
        Controls.AddRange([_enabled, _projectPermission]);
        var cancel = new Button { Text = "İptal", DialogResult = DialogResult.Cancel, Left = 385, Top = 230, Width = 85 };
        var save = new Button { Text = "Kaydet", Left = 480, Top = 230, Width = 85 };
        save.Click += (_, _) => SaveAndClose();
        Controls.AddRange([cancel, save]);
        CancelButton = cancel;
    }

    private void SaveAndClose()
    {
        var value = _key.Text.Trim();
        if (value.Length > 0 && !value.StartsWith('•')) SecretStore.Save(value);
        if (_enabled.Checked && SecretStore.Read() is null)
        {
            MessageBox.Show("Önce ücretsiz hesap anahtarını girin.", "Anahtar gerekli");
            return;
        }
        _settings.CloudEnabled = _enabled.Checked;
        _settings.AllowProjectCloud = _projectPermission.Checked;
        _settings.Save();
        DialogResult = DialogResult.OK;
        Close();
    }
}

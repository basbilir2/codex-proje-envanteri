namespace LocalAIOS;

internal sealed class PluginDialog : Form
{
    private readonly PluginManager _manager;
    private readonly ListBox _list = new();

    public PluginDialog(PluginManager manager)
    {
        _manager = manager;
        Text = "Eklentiler";
        Size = new Size(620, 430);
        StartPosition = FormStartPosition.CenterParent;
        BackColor = Color.FromArgb(24, 27, 34);
        ForeColor = Color.White;
        Font = new Font("Segoe UI", 10);
        _list.SetBounds(20, 20, 565, 300);
        _list.BackColor = Color.FromArgb(34, 38, 47);
        _list.ForeColor = Color.White;
        var install = new Button { Text = "Eklenti yükle", Left = 375, Top = 335, Width = 110 };
        var close = new Button { Text = "Kapat", DialogResult = DialogResult.OK, Left = 495, Top = 335, Width = 90 };
        install.Click += (_, _) => Install();
        Controls.AddRange([_list, install, close]);
        AcceptButton = close;
        RefreshList();
    }

    private void Install()
    {
        using var picker = new OpenFileDialog { Filter = "Local AI eklentisi (*.lai-plugin;*.json)|*.lai-plugin;*.json", Title = "Eklenti seçin" };
        if (picker.ShowDialog(this) != DialogResult.OK) return;
        try
        {
            var plugin = _manager.Install(picker.FileName);
            MessageBox.Show($"{plugin.Name} eklentisi yüklendi.", "Eklentiler");
            RefreshList();
        }
        catch (Exception exception)
        {
            MessageBox.Show(exception.Message, "Eklenti yüklenemedi", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    private void RefreshList()
    {
        _list.Items.Clear();
        foreach (var plugin in _manager.List())
            _list.Items.Add($"{plugin.Name}  ·  v{plugin.Version}  ·  {plugin.Description}");
        if (_list.Items.Count == 0) _list.Items.Add("Henüz eklenti yüklenmedi.");
    }
}

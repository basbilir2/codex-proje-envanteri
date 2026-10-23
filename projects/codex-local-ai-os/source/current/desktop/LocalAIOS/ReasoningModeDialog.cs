namespace LocalAIOS;

internal sealed class ReasoningModeDialog : Form
{
    public string SelectedMode { get; private set; }

    public ReasoningModeDialog(string currentMode)
    {
        SelectedMode = currentMode;
        Text = "Zekâ modu";
        Size = new Size(540, 330);
        StartPosition = FormStartPosition.CenterParent;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = false;
        BackColor = Color.FromArgb(24, 27, 34);
        ForeColor = Color.White;
        Font = new Font("Segoe UI", 10);
        Controls.Add(new Label
        {
            Text = "İstediğin çalışma biçimini seç. Sonradan değiştirebilirsin.",
            Left = 24, Top = 18, Width = 480, Height = 28
        });
        AddMode("fast", "Hızlı", "Sohbet ve günlük işler için en kısa bekleme.", 58);
        AddMode("balanced", "Dengeli · Önerilen", "Basit işleri hızlı, zor işleri derin düşünür.", 125);
        AddMode("powerful", "En güçlü", "Her görevde derin düşünür; belirgin şekilde daha yavaştır.", 192);
        var cancel = new Button { Text = "Vazgeç", DialogResult = DialogResult.Cancel, Left = 414, Top = 252, Width = 90 };
        Controls.Add(cancel);
        CancelButton = cancel;
    }

    private void AddMode(string id, string title, string description, int top)
    {
        var selected = id.Equals(SelectedMode, StringComparison.OrdinalIgnoreCase) ? "  ✓" : "";
        var button = new Button
        {
            Text = title + selected + "\n" + description,
            Left = 24, Top = top, Width = 480, Height = 56,
            TextAlign = ContentAlignment.MiddleLeft
        };
        button.Click += (_, _) => { SelectedMode = id; DialogResult = DialogResult.OK; Close(); };
        Controls.Add(button);
    }
}

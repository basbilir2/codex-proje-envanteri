namespace LocalAIOS;

internal sealed class PromptDialog : Form
{
    private readonly TextBox _input = new();
    public string Value => _input.Text.Trim();

    public PromptDialog(string title, string message, string initialValue = "")
    {
        Text = title;
        Width = 570;
        Height = 190;
        StartPosition = FormStartPosition.CenterParent;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = false;
        BackColor = Color.FromArgb(24, 27, 34);
        ForeColor = Color.White;

        var label = new Label { Text = message, Left = 20, Top = 18, Width = 510, Height = 24 };
        _input.SetBounds(20, 50, 515, 28);
        _input.Text = initialValue;
        var cancel = new Button { Text = "İptal", DialogResult = DialogResult.Cancel, Left = 355, Top = 95, Width = 85 };
        var ok = new Button { Text = "Tamam", DialogResult = DialogResult.OK, Left = 450, Top = 95, Width = 85 };
        AcceptButton = ok;
        CancelButton = cancel;
        Controls.AddRange([label, _input, cancel, ok]);
    }
}

using System.Diagnostics;

namespace LocalAIOS;

internal sealed class ProjectDialog : Form
{
    public bool CreateCopyRequested { get; private set; }

    public ProjectDialog(string activeProject)
    {
        Text = "Projeler";
        Size = new Size(620, 250);
        StartPosition = FormStartPosition.CenterParent;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = false;
        BackColor = Color.FromArgb(24, 27, 34);
        ForeColor = Color.White;
        Font = new Font("Segoe UI", 10);
        var active = string.IsNullOrWhiteSpace(activeProject) ? "Henüz çalışma projesi seçilmedi." : $"Çalışılan kopya:\n{activeProject}";
        Controls.Add(new Label { Text = active, Left = 22, Top = 20, Width = 560, Height = 58 });
        var create = new Button { Text = "Eski projeden yeni sürüm oluştur", Left = 22, Top = 100, Width = 270, Height = 42 };
        create.Click += (_, _) => { CreateCopyRequested = true; DialogResult = DialogResult.OK; };
        var open = new Button { Text = "Çalışma klasörünü aç", Left = 306, Top = 100, Width = 190, Height = 42, Enabled = Directory.Exists(activeProject) };
        open.Click += (_, _) => Process.Start(new ProcessStartInfo(activeProject) { UseShellExecute = true });
        var close = new Button { Text = "Kapat", Left = 500, Top = 158, Width = 82, Height = 34, DialogResult = DialogResult.Cancel };
        Controls.AddRange([create, open, close]);
    }
}

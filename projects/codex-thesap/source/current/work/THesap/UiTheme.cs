namespace THesap;

public static class UiTheme
{
    public static readonly Color Navy = Color.FromArgb(20, 48, 65), Teal = Color.FromArgb(29, 122, 126), Mint = Color.FromArgb(228, 245, 241), Sand = Color.FromArgb(248, 244, 235), Ink = Color.FromArgb(38, 48, 56), Muted = Color.FromArgb(102, 117, 126), Line = Color.FromArgb(218, 226, 230);
    public static Button Button(string text, bool primary = true) { var b = new Button { Text = text, AutoSize = true, Height = 38, Padding = new Padding(14, 4, 14, 4), FlatStyle = FlatStyle.Flat, BackColor = primary ? Teal : Color.White, ForeColor = primary ? Color.White : Navy, Font = new Font("Segoe UI Semibold", 9.5f), Cursor = Cursors.Hand, Margin = new Padding(4) }; b.FlatAppearance.BorderColor = primary ? Teal : Line; return b; }
    public static Label Label(string text, bool title = false) => new() { Text = text, AutoSize = true, ForeColor = title ? Navy : Ink, Font = new Font(title ? "Segoe UI Semibold" : "Segoe UI", title ? 11f : 9.5f), Margin = new Padding(3, 8, 3, 3) };
    public static TextBox TextBox() => new() { BorderStyle = BorderStyle.FixedSingle, Font = new Font("Segoe UI", 10f), Height = 30, Dock = DockStyle.Top };
    public static NumericUpDown Number(decimal max = 1000000, int decimals = 2) => new() { Maximum = max, Minimum = 0, DecimalPlaces = decimals, ThousandsSeparator = true, Font = new Font("Segoe UI", 10f), Height = 30, Dock = DockStyle.Top };
    public static ComboBox Combo() => new() { DropDownStyle = ComboBoxStyle.DropDownList, Font = new Font("Segoe UI", 10f), Height = 30, Dock = DockStyle.Top };
    public static DataGridView Grid() { var g = new DataGridView { Dock = DockStyle.Fill, BackgroundColor = Color.White, BorderStyle = BorderStyle.None, ReadOnly = true, AllowUserToAddRows = false, AllowUserToDeleteRows = false, AllowUserToResizeRows = false, RowHeadersVisible = false, SelectionMode = DataGridViewSelectionMode.FullRowSelect, MultiSelect = false, AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill, EnableHeadersVisualStyles = false, ColumnHeadersHeight = 38, Font = new Font("Segoe UI", 9.5f), GridColor = Line }; g.ColumnHeadersDefaultCellStyle.BackColor = Navy; g.ColumnHeadersDefaultCellStyle.ForeColor = Color.White; g.DefaultCellStyle.SelectionBackColor = Mint; g.DefaultCellStyle.SelectionForeColor = Ink; return g; }
    public static Panel EditorPanel() => new() { Dock = DockStyle.Fill, BackColor = Sand, Padding = new Padding(18), AutoScroll = true };
}

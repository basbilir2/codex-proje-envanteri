namespace BTakip;

public static class UiTheme
{
    public static readonly Color Navy = Color.FromArgb(20, 48, 65);
    public static readonly Color Teal = Color.FromArgb(29, 122, 126);
    public static readonly Color Mint = Color.FromArgb(228, 245, 241);
    public static readonly Color Sand = Color.FromArgb(248, 244, 235);
    public static readonly Color Orange = Color.FromArgb(231, 137, 55);
    public static readonly Color Ink = Color.FromArgb(38, 48, 56);
    public static readonly Color Muted = Color.FromArgb(102, 117, 126);
    public static readonly Color Line = Color.FromArgb(218, 226, 230);

    public static Button Button(string text, bool primary = true)
    {
        var button = new Button
        {
            Text = text,
            AutoSize = true,
            Height = 38,
            Padding = new Padding(14, 4, 14, 4),
            FlatStyle = FlatStyle.Flat,
            BackColor = primary ? Teal : Color.White,
            ForeColor = primary ? Color.White : Navy,
            Font = new Font("Segoe UI Semibold", 9.5f),
            Cursor = Cursors.Hand,
            Margin = new Padding(4)
        };
        button.FlatAppearance.BorderColor = primary ? Teal : Line;
        button.FlatAppearance.BorderSize = 1;
        return button;
    }

    public static Label Label(string text, bool title = false) => new()
    {
        Text = text,
        AutoSize = true,
        ForeColor = title ? Navy : Ink,
        Font = new Font(title ? "Segoe UI Semibold" : "Segoe UI", title ? 11f : 9.5f),
        Margin = new Padding(3, 8, 3, 3)
    };

    public static TextBox TextBox(bool multi = false) => new()
    {
        BorderStyle = BorderStyle.FixedSingle,
        Font = new Font("Segoe UI", 10f),
        Multiline = multi,
        Height = multi ? 72 : 30,
        Dock = DockStyle.Top
    };

    public static NumericUpDown Number(decimal maximum = 1000000, int decimals = 2) => new()
    {
        Maximum = maximum,
        Minimum = 0,
        DecimalPlaces = decimals,
        ThousandsSeparator = true,
        Font = new Font("Segoe UI", 10f),
        Height = 30,
        Dock = DockStyle.Top
    };

    public static ComboBox Combo() => new()
    {
        DropDownStyle = ComboBoxStyle.DropDownList,
        Font = new Font("Segoe UI", 10f),
        Height = 30,
        Dock = DockStyle.Top
    };

    public static DataGridView Grid()
    {
        var grid = new DataGridView
        {
            Dock = DockStyle.Fill,
            BackgroundColor = Color.White,
            BorderStyle = BorderStyle.None,
            ReadOnly = true,
            AllowUserToAddRows = false,
            AllowUserToDeleteRows = false,
            AllowUserToResizeRows = false,
            RowHeadersVisible = false,
            SelectionMode = DataGridViewSelectionMode.FullRowSelect,
            MultiSelect = false,
            AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
            AutoGenerateColumns = false,
            EnableHeadersVisualStyles = false,
            ColumnHeadersHeight = 38,
            RowTemplate = { Height = 34 },
            Font = new Font("Segoe UI", 9.5f),
            GridColor = Line
        };
        grid.ColumnHeadersDefaultCellStyle.BackColor = Navy;
        grid.ColumnHeadersDefaultCellStyle.ForeColor = Color.White;
        grid.ColumnHeadersDefaultCellStyle.Font = new Font("Segoe UI Semibold", 9.5f);
        grid.DefaultCellStyle.SelectionBackColor = Mint;
        grid.DefaultCellStyle.SelectionForeColor = Ink;
        grid.AlternatingRowsDefaultCellStyle.BackColor = Color.FromArgb(249, 251, 252);
        return grid;
    }

    public static Panel EditorPanel()
    {
        return new Panel { Dock = DockStyle.Fill, BackColor = Sand, Padding = new Padding(18), AutoScroll = true };
    }

    public static void AddField(TableLayoutPanel layout, string label, Control control, int row)
    {
        layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        layout.Controls.Add(Label(label), 0, row);
        layout.Controls.Add(control, 1, row);
    }
}

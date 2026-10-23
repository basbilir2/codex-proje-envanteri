namespace THesap;

public sealed class PriceManagementForm : Form
{
    private readonly List<PriceGroup> _groups;
    private readonly List<PriceItem> _items;
    private readonly Action _saved;
    private readonly DataGridView _itemGrid = Grid();
    private readonly DataGridView _groupGrid = Grid();
    private readonly ComboBox _category = Combo("Malzeme", "Baskı", "Hizmet", "Ürün");
    private readonly TextBox _name = Box(), _variant = Box(), _unit = Box("m²");
    private readonly ComboBox _currency = Combo("TL", "USD", "%");
    private readonly ComboBox _formula = Combo(PricingFormula.SquareMeter, PricingFormula.Meter, PricingFormula.Piece, PricingFormula.Minute, PricingFormula.Hour, PricingFormula.Fixed, PricingFormula.SheetArea, PricingFormula.UvTable, PricingFormula.DtfTier, PricingFormula.PercentMaterial);
    private readonly NumericUpDown _cost = Number(), _secondaryCost = Number(), _sheetWidth = Number(), _sheetHeight = Number();
    private readonly TextBox _groupName = Box();
    private readonly NumericUpDown _groupProfit = Number();
    private PriceItem? _selectedItem;
    private PriceGroup? _selectedGroup;

    public PriceManagementForm(List<PriceGroup> groups, List<PriceItem> items, Action saved)
    {
        _groups = groups; _items = items; _saved = saved;
        Text = "THesap — Fiyat Tanımları ve Kâr Ayarları"; StartPosition = FormStartPosition.CenterParent; MinimumSize = new Size(1080, 680); Size = new Size(1180, 760); BackColor = Color.FromArgb(244, 247, 250);
        var tabs = new TabControl { Dock = DockStyle.Fill, Font = new Font("Segoe UI", 10f), Padding = new Point(18, 7) };
        tabs.TabPages.Add(ItemsTab()); tabs.TabPages.Add(GroupsTab()); Controls.Add(tabs);
        RefreshItems(); RefreshGroups();
    }

    private TabPage ItemsTab()
    {
        var tab = new TabPage("Fiyat Tanımları") { BackColor = Color.FromArgb(244, 247, 250), Padding = new Padding(16) };
        var split = new SplitContainer { Dock = DockStyle.Fill, SplitterDistance = 620 };
        _itemGrid.SelectionChanged += (_, _) => LoadItemSelection();
        split.Panel1.Controls.Add(_itemGrid);
        var editor = new Panel { Dock = DockStyle.Fill, BackColor = Color.White, Padding = new Padding(18) };
        var form = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, ColumnCount = 2 };
        form.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 135)); form.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        Add(form, "Kategori", _category); Add(form, "Ürün / hizmet adı", _name); Add(form, "Varyant", _variant); Add(form, "Birim", _unit); Add(form, "Para birimi", _currency); Add(form, "Birim maliyet", _cost); Add(form, "10 m üstü maliyet", _secondaryCost); Add(form, "Hesap formülü", _formula); Add(form, "Levha en (cm)", _sheetWidth); Add(form, "Levha boy (cm)", _sheetHeight);
        var actions = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 48, FlowDirection = FlowDirection.RightToLeft };
        var save = Button("Kaydet", true); save.Click += (_, _) => SaveItem(); var add = Button("Yeni", false); add.Click += (_, _) => NewItem(); var passive = Button("Pasif Yap", false); passive.Click += (_, _) => MakePassive();
        actions.Controls.Add(save); actions.Controls.Add(passive); actions.Controls.Add(add); editor.Controls.Add(form); editor.Controls.Add(actions); split.Panel2.Controls.Add(editor); tab.Controls.Add(split); return tab;
    }

    private TabPage GroupsTab()
    {
        var tab = new TabPage("Kâr Ayarları") { BackColor = Color.FromArgb(244, 247, 250), Padding = new Padding(16) };
        var split = new SplitContainer { Dock = DockStyle.Fill, SplitterDistance = 620 };
        _groupGrid.SelectionChanged += (_, _) => LoadGroupSelection(); split.Panel1.Controls.Add(_groupGrid);
        var editor = new Panel { Dock = DockStyle.Fill, BackColor = Color.White, Padding = new Padding(18) };
        var form = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, ColumnCount = 2 }; form.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 135)); form.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        Add(form, "Fiyat grubu adı", _groupName); Add(form, "Kâr oranı (%)", _groupProfit);
        var info = new Label { Text = "Örnek: %100 kâr = maliyet × 2", Dock = DockStyle.Top, Height = 30, ForeColor = Color.DimGray, Font = new Font("Segoe UI", 9f) };
        var actions = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 48, FlowDirection = FlowDirection.RightToLeft };
        var save = Button("Kaydet", true); save.Click += (_, _) => SaveGroup(); var add = Button("Yeni", false); add.Click += (_, _) => NewGroup();
        actions.Controls.Add(save); actions.Controls.Add(add); editor.Controls.Add(form); editor.Controls.Add(info); editor.Controls.Add(actions); split.Panel2.Controls.Add(editor); tab.Controls.Add(split); return tab;
    }

    private void RefreshItems()
    {
        _itemGrid.DataSource = null;
        _itemGrid.DataSource = _items.Where(x => !x.Deleted).OrderBy(x => x.Category).ThenBy(x => x.Name).ThenBy(x => x.Variant)
            .Select(x => new { x.Id, x.Category, Ürün = x.Name, Varyant = x.Variant, Birim = x.Unit, Para = x.Currency, Maliyet = x.UnitCost, Formül = x.Formula, Aktif = x.Active }).ToList();
        var idColumn = _itemGrid.Columns["Id"]; if (idColumn is not null) idColumn.Visible = false;
    }

    private void RefreshGroups()
    {
        _groupGrid.DataSource = null;
        _groupGrid.DataSource = _groups.Select(x => new { x.Id, Grup = x.Name, KârOranı = (x.CostMultiplier - 1m) * 100m, Çarpan = x.CostMultiplier }).ToList();
        var idColumn = _groupGrid.Columns["Id"]; if (idColumn is not null) idColumn.Visible = false;
    }

    private void LoadItemSelection()
    {
        if (_itemGrid.CurrentRow?.DataBoundItem is null) return;
        var id = _itemGrid.CurrentRow.Cells["Id"].Value as string ?? ""; _selectedItem = _items.FirstOrDefault(x => x.Id == id); if (_selectedItem is null) return;
        _category.Text = _selectedItem.Category; _name.Text = _selectedItem.Name; _variant.Text = _selectedItem.Variant; _unit.Text = _selectedItem.Unit; _currency.Text = _selectedItem.Currency; _cost.Value = Clamp(_cost, _selectedItem.UnitCost); _secondaryCost.Value = Clamp(_secondaryCost, _selectedItem.SecondaryCost); _formula.Text = _selectedItem.Formula; _sheetWidth.Value = Clamp(_sheetWidth, _selectedItem.SheetWidthCm); _sheetHeight.Value = Clamp(_sheetHeight, _selectedItem.SheetHeightCm);
    }

    private void LoadGroupSelection()
    {
        if (_groupGrid.CurrentRow?.DataBoundItem is null) return;
        var id = _groupGrid.CurrentRow.Cells["Id"].Value as string ?? ""; _selectedGroup = _groups.FirstOrDefault(x => x.Id == id); if (_selectedGroup is null) return;
        _groupName.Text = _selectedGroup.Name; _groupProfit.Value = Clamp(_groupProfit, (_selectedGroup.CostMultiplier - 1m) * 100m);
    }

    private void NewItem() { _selectedItem = null; _category.SelectedIndex = 0; _name.Clear(); _variant.Clear(); _unit.Text = "m²"; _currency.Text = "TL"; _cost.Value = _secondaryCost.Value = _sheetWidth.Value = _sheetHeight.Value = 0; _formula.Text = PricingFormula.SquareMeter; }
    private void SaveItem()
    {
        if (string.IsNullOrWhiteSpace(_name.Text)) { MessageBox.Show("Ürün veya hizmet adı boş olamaz.", "THesap"); return; }
        var item = _selectedItem ?? new PriceItem { Id = Guid.NewGuid().ToString("N") };
        item.Category = _category.Text; item.Name = _name.Text.Trim(); item.Variant = _variant.Text.Trim(); item.Unit = _unit.Text.Trim(); item.Currency = _currency.Text; item.UnitCost = _cost.Value; item.SecondaryCost = _secondaryCost.Value; item.Formula = _formula.Text; item.SheetWidthCm = _sheetWidth.Value; item.SheetHeightCm = _sheetHeight.Value; item.Active = true; item.Deleted = false;
        if (_selectedItem is null) _items.Add(item); CatalogStore.Save(_groups, _items); _saved(); RefreshItems(); SelectItem(item.Id);
    }

    private void MakePassive()
    {
        if (_selectedItem is null) return; _selectedItem.Active = false; CatalogStore.Save(_groups, _items); _saved(); NewItem(); RefreshItems();
    }

    private void NewGroup() { _selectedGroup = null; _groupName.Clear(); _groupProfit.Value = 0; }
    private void SaveGroup()
    {
        if (string.IsNullOrWhiteSpace(_groupName.Text)) { MessageBox.Show("Fiyat grubu adı boş olamaz.", "THesap"); return; }
        var group = _selectedGroup ?? new PriceGroup { Id = Guid.NewGuid().ToString("N"), Code = Guid.NewGuid().ToString("N")[..8] };
        group.Name = _groupName.Text.Trim(); group.CostMultiplier = 1m + _groupProfit.Value / 100m; if (_selectedGroup is null) _groups.Add(group);
        CatalogStore.Save(_groups, _items); _saved(); RefreshGroups(); SelectGroup(group.Id);
    }

    private void SelectItem(string id) { foreach (DataGridViewRow row in _itemGrid.Rows) if ((string?)row.Cells["Id"].Value == id) { row.Selected = true; _itemGrid.CurrentCell = row.Cells["Ürün"]; break; } }
    private void SelectGroup(string id) { foreach (DataGridViewRow row in _groupGrid.Rows) if ((string?)row.Cells["Id"].Value == id) { row.Selected = true; _groupGrid.CurrentCell = row.Cells["Grup"]; break; } }
    private static DataGridView Grid() => new() { Dock = DockStyle.Fill, ReadOnly = true, AllowUserToAddRows = false, AllowUserToDeleteRows = false, AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill, SelectionMode = DataGridViewSelectionMode.FullRowSelect, MultiSelect = false, BackgroundColor = Color.White, BorderStyle = BorderStyle.None, RowHeadersVisible = false, Font = new Font("Segoe UI", 9.5f) };
    private static ComboBox Combo(params string[] values) { var box = new ComboBox { Dock = DockStyle.Fill, DropDownStyle = ComboBoxStyle.DropDownList }; box.Items.AddRange(values); box.SelectedIndex = 0; return box; }
    private static TextBox Box(string value = "") => new() { Dock = DockStyle.Fill, Text = value };
    private static NumericUpDown Number() => new() { Dock = DockStyle.Fill, Maximum = 1000000, DecimalPlaces = 4, ThousandsSeparator = true };
    private static Button Button(string text, bool primary) { var b = new Button { Text = text, Size = new Size(96, 32), FlatStyle = FlatStyle.Flat, BackColor = primary ? Color.FromArgb(25, 126, 123) : Color.White, ForeColor = primary ? Color.White : Color.FromArgb(25, 42, 67), Margin = new Padding(6, 0, 0, 0) }; b.FlatAppearance.BorderColor = primary ? Color.FromArgb(25, 126, 123) : Color.FromArgb(203, 213, 225); return b; }
    private static decimal Clamp(NumericUpDown box, decimal value) => Math.Min(box.Maximum, Math.Max(box.Minimum, value));
    private static void Add(TableLayoutPanel form, string text, Control control) { var row = form.RowCount; form.RowStyles.Add(new RowStyle(SizeType.Absolute, 38)); form.Controls.Add(new Label { Text = text, Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleLeft, ForeColor = Color.FromArgb(71, 85, 105) }, 0, row); control.Margin = new Padding(0, 5, 0, 5); form.Controls.Add(control, 1, row); form.RowCount++; }
}

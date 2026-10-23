namespace THesap;

public sealed class MainForm : Form
{
    private readonly List<PriceGroup> _groups; private readonly List<PriceItem> _items;
    private readonly TabControl _tabs = new();
    private readonly DataGridView _priceGrid = UiTheme.Grid(), _profitGrid = UiTheme.Grid();
    private readonly ComboBox _priceCategory = UiTheme.Combo(), _priceCurrency = UiTheme.Combo(), _priceFormula = UiTheme.Combo(), _priceGroup = UiTheme.Combo(), _pricePreset = UiTheme.Combo();
    private readonly TextBox _priceName = UiTheme.TextBox(), _priceVariant = UiTheme.TextBox(), _priceUnit = UiTheme.TextBox();
    private readonly NumericUpDown _priceCost = UiTheme.Number(10000000, 4), _priceSecondary = UiTheme.Number(10000000, 4), _priceSheetW = UiTheme.Number(10000), _priceSheetH = UiTheme.Number(10000);
    private readonly CheckBox _priceActive = new() { Text = "Aktif", Checked = true, AutoSize = true };
    private readonly Dictionary<string, (CheckBox Enabled, NumericUpDown Percent)> _priceSpecialProfits = [];
    private bool _refreshingPrices;
    private PriceItem? _selectedPrice;
    private readonly ComboBox _calcGroup = UiTheme.Combo();
    private readonly CheckedListBox _calcItems = new() { Dock = DockStyle.Fill, Font = new Font("Segoe UI", 10f), CheckOnClick = true, BorderStyle = BorderStyle.FixedSingle };
    private readonly NumericUpDown _calcWidth = UiTheme.Number(100000, 2), _calcHeight = UiTheme.Number(100000, 2), _calcLength = UiTheme.Number(100000, 3), _calcMinutes = UiTheme.Number(100000, 2), _calcQty = UiTheme.Number(100000, 2), _calcRate = UiTheme.Number(1000, 4), _calcAlternativePercent = UiTheme.Number(10000, 2);
    private readonly CheckBox _calcAlternative = new() { Text = "Grup çarpanı yerine alternatif maliyet üstü % kullan", AutoSize = true };
    private readonly ListBox _calcLines = new() { Dock = DockStyle.Fill, Font = new Font("Consolas", 9.5f), BorderStyle = BorderStyle.FixedSingle };
    private readonly Label _calcCost = new() { Text = "Maliyet: 0,00 TL", AutoSize = true, ForeColor = UiTheme.Muted, Font = new Font("Segoe UI Semibold", 10f), Location = new Point(14, 10) };
    private readonly Label _calcSale = new() { Text = "Önerilen satış: 0,00 TL", AutoSize = true, ForeColor = UiTheme.Navy, Font = new Font("Segoe UI Semibold", 17f), Location = new Point(14, 37) };
    private readonly TextBox _groupName = UiTheme.TextBox();
    private readonly NumericUpDown _groupProfit = UiTheme.Number(10000, 2);
    private PriceGroup? _selectedGroup;

    public MainForm()
    {
        (_groups, _items) = CatalogStore.Load();
        Text = "THesap — Fiyat Hesaplama"; StartPosition = FormStartPosition.CenterScreen; MinimumSize = new Size(880, 610); Size = new Size(1240, 780); BackColor = Color.White;
        var header = new Panel { Dock = DockStyle.Top, Height = 74, BackColor = UiTheme.Navy, Padding = new Padding(24, 12, 24, 12) };
        header.Controls.Add(new Label { Text = "THesap", AutoSize = true, ForeColor = Color.White, Font = new Font("Segoe UI Semibold", 23f), Location = new Point(24, 8) });
        header.Controls.Add(new Label { Text = "Fiyat Hesaplama", AutoSize = true, ForeColor = Color.FromArgb(190, 230, 225), Font = new Font("Segoe UI", 10f), Location = new Point(28, 48) });
        _tabs.Dock = DockStyle.Fill; _tabs.Font = new Font("Segoe UI Semibold", 10f); _tabs.Padding = new Point(16, 7);
        _tabs.TabPages.Add(BuildPricesTab()); _tabs.TabPages.Add(BuildCalculatorTab()); _tabs.TabPages.Add(BuildProfitTab());
        Controls.Add(_tabs); Controls.Add(header);
        RefreshAll();
    }

    private TabPage NewTab(string name) => new(name) { BackColor = Color.White, Padding = new Padding(0) };
    private TabPage BuildPricesTab()
    {
        var tab = NewTab("Fiyat Tanımları"); var split = new SplitContainer { Dock = DockStyle.Fill, SplitterDistance = 430, FixedPanel = FixedPanel.Panel1 };
        var edit = UiTheme.EditorPanel(); var form = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, ColumnCount = 1 };
        form.Controls.Add(UiTheme.Label("Ürün / Malzeme Tanımı", true));
        form.Controls.Add(new Label { Text = "Malzeme, baskı veya hizmet ekleyin; bu fiyatlar hesaplamada hemen kullanılır.", AutoSize = true, MaximumSize = new Size(365, 0), ForeColor = UiTheme.Muted, Margin = new Padding(3, 4, 3, 12) });
        var modeBar = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Top, WrapContents = false };
        _priceCategory.Items.AddRange(["Malzeme", "Baskı", "Hizmet"]); _priceCategory.SelectedIndex = 0;
        foreach (var type in new[] { "Malzeme", "Baskı", "Hizmet" }) { var button = UiTheme.Button(type, false); button.Width = 112; button.Click += (_, _) => { _priceCategory.SelectedItem = type; RefreshPricePreset(); }; modeBar.Controls.Add(button); }
        form.Controls.Add(modeBar);
        AddStack(form, "Ürün / malzeme adı *", _priceName); AddStack(form, "Hazır seçim", _pricePreset); AddStack(form, "Açıklama / not", _priceVariant); _priceUnit.Text = "m²"; AddStack(form, "Birim", _priceUnit);
        _priceCurrency.Items.AddRange(["TL", "USD", "%"]); _priceCurrency.SelectedItem = "TL"; AddStack(form, "Para birimi", _priceCurrency);
        _priceFormula.Items.AddRange([PricingFormula.SquareMeter, PricingFormula.Meter, PricingFormula.Piece, PricingFormula.Minute, PricingFormula.Hour, PricingFormula.Fixed, PricingFormula.SheetArea, PricingFormula.UvTable, PricingFormula.DtfTier, PricingFormula.PercentMaterial]); _priceFormula.SelectedItem = PricingFormula.SquareMeter; AddStack(form, "Hesap formülü", _priceFormula);
        AddStack(form, "Alış birim fiyatı", _priceCost); AddStack(form, "10 m üstü alış fiyatı", _priceSecondary); AddStack(form, "Levha en (cm)", _priceSheetW); AddStack(form, "Levha boy (cm)", _priceSheetH);
        form.Controls.Add(new Label { Text = "Müşteri kategorisine özel ürün kârı (isteğe bağlı)", AutoSize = true, Font = new Font("Segoe UI Semibold", 9.5f), ForeColor = UiTheme.Navy, Margin = new Padding(3, 12, 3, 1) });
        form.Controls.Add(new Label { Text = "Özel işaretlenmezse kategori standart kârı kullanılır.", AutoSize = true, ForeColor = UiTheme.Muted, Margin = new Padding(3, 0, 3, 5) });
        foreach (var group in _groups) { var enabled = new CheckBox { Text = group.Name, AutoSize = true, Width = 200, Margin = new Padding(3, 3, 3, 3) }; var percent = UiTheme.Number(10000, 2); percent.Width = 100; percent.Dock = DockStyle.None; var row = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Top, WrapContents = false }; row.Controls.Add(enabled); row.Controls.Add(percent); form.Controls.Add(row); _priceSpecialProfits[group.Id] = (enabled, percent); }
        form.Controls.Add(_priceActive);
        var add = UiTheme.Button("Ürünü Kaydet"); add.Click += (_, _) => SavePrice(); var fresh = UiTheme.Button("Yeni Ürün", false); fresh.Click += (_, _) => ClearPrice(); var buttons = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true }; buttons.Controls.Add(add); buttons.Controls.Add(fresh); form.Controls.Add(buttons); edit.Controls.Add(form);
        _pricePreset.SelectedIndexChanged += (_, _) => ApplyPricePreset(); _priceGrid.SelectionChanged += (_, _) => SelectPrice(); split.Panel1.Controls.Add(edit); split.Panel2.Padding = new Padding(12);
        var priceView = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 46, Padding = new Padding(4, 7, 4, 5), BackColor = UiTheme.Sand }; priceView.Controls.Add(new Label { Text = "Tablo fiyat grubu:", AutoSize = true, Margin = new Padding(4, 7, 6, 0), ForeColor = UiTheme.Ink }); _priceGroup.Width = 240; _priceGroup.Dock = DockStyle.None; _priceGroup.SelectedIndexChanged += (_, _) => { if (!_refreshingPrices) RefreshPriceGrid(); }; priceView.Controls.Add(_priceGroup);
        split.Panel2.Controls.Add(_priceGrid); split.Panel2.Controls.Add(priceView); tab.Controls.Add(split); AddPanelToggle(tab, split, 430); return tab;
    }

    private TabPage BuildCalculatorTab()
    {
        var tab = NewTab("Fiyat Hesaplama"); var split = new SplitContainer { Dock = DockStyle.Fill, SplitterDistance = 480, FixedPanel = FixedPanel.Panel1 };
        var left = UiTheme.EditorPanel(); var form = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, ColumnCount = 2 }; form.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 42)); form.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 58));
        form.Controls.Add(UiTheme.Label("Fiyat Hesapla", true), 0, 0); form.SetColumnSpan(form.Controls[^1], 2);
        AddField(form, "Fiyat kategorisi / kâr oranı", _calcGroup, 1); AddField(form, "En (cm)", _calcWidth, 2); AddField(form, "Boy (cm)", _calcHeight, 3); AddField(form, "Uzunluk (m)", _calcLength, 4); AddField(form, "Süre (dk)", _calcMinutes, 5);
        _calcQty.Value = 1; AddField(form, "Adet", _calcQty, 6); _calcRate.Value = 40; AddField(form, "USD/TL", _calcRate, 7);
        form.Controls.Add(_calcAlternative, 0, 8); form.SetColumnSpan(_calcAlternative, 2); _calcAlternativePercent.Enabled = false; AddField(form, "Alternatif %", _calcAlternativePercent, 9);
        _calcAlternative.CheckedChanged += (_, _) => { _calcAlternativePercent.Enabled = _calcAlternative.Checked; Recalculate(); }; _calcAlternativePercent.ValueChanged += (_, _) => Recalculate(); left.Controls.Add(form);
        var right = new Panel { Dock = DockStyle.Fill, BackColor = Color.White, Padding = new Padding(18) }; var sections = new SplitContainer { Dock = DockStyle.Fill, Orientation = Orientation.Horizontal, SplitterDistance = 300 };
        var choose = new Panel { Dock = DockStyle.Fill, Padding = new Padding(0, 0, 0, 8) }; var chooseTitle = UiTheme.Label("Kullanılacak kalemleri seçin", true); chooseTitle.Dock = DockStyle.Top; _calcItems.ItemCheck += (_, _) => BeginInvoke(Recalculate); choose.Controls.Add(_calcItems); choose.Controls.Add(chooseTitle);
        var result = new Panel { Dock = DockStyle.Fill, Padding = new Padding(0, 12, 0, 0) }; var totals = new Panel { Dock = DockStyle.Bottom, Height = 90, BackColor = UiTheme.Mint }; totals.Controls.Add(_calcCost); totals.Controls.Add(_calcSale); result.Controls.Add(_calcLines); result.Controls.Add(totals); sections.Panel1.Controls.Add(choose); sections.Panel2.Controls.Add(result); right.Controls.Add(sections);
        var actions = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 58, Padding = new Padding(8), BackColor = UiTheme.Sand, FlowDirection = FlowDirection.RightToLeft }; var calculate = UiTheme.Button("Hesapla", false); calculate.Click += (_, _) => Recalculate(); var reset = UiTheme.Button("Hesabı Sıfırla", false); reset.Click += (_, _) => ResetCalculator(); actions.Controls.Add(calculate); actions.Controls.Add(reset);
        split.Panel1.Controls.Add(left); split.Panel2.Controls.Add(right); split.Panel2.Controls.Add(actions); tab.Controls.Add(split); AddPanelToggle(tab, split, 480); return tab;
    }

    private TabPage BuildProfitTab()
    {
        var tab = NewTab("Kâr Ayarları"); var split = new SplitContainer { Dock = DockStyle.Fill, SplitterDistance = 420, FixedPanel = FixedPanel.Panel1 };
        var edit = UiTheme.EditorPanel(); var form = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, ColumnCount = 1 }; form.Controls.Add(UiTheme.Label("Müşteri Kategorisi Kâr Oranları", true));
        form.Controls.Add(new Label { Text = "Kâr oranı değiştiğinde sonraki fiyat hesaplamaları anında yeni oranı kullanır.", AutoSize = true, MaximumSize = new Size(350, 0), ForeColor = UiTheme.Muted, Margin = new Padding(3, 5, 3, 14) });
        AddStack(form, "Kategori adı", _groupName); AddStack(form, "Alış maliyeti üstüne kâr (%)", _groupProfit);
        var save = UiTheme.Button("Kâr Oranını Kaydet"); save.Click += (_, _) => SaveGroup(); var fresh = UiTheme.Button("Yeni Kategori", false); fresh.Click += (_, _) => { _selectedGroup = null; _groupName.Clear(); _groupProfit.Value = 0; }; var buttons = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true }; buttons.Controls.Add(save); buttons.Controls.Add(fresh); form.Controls.Add(buttons); edit.Controls.Add(form);
        _profitGrid.SelectionChanged += (_, _) => SelectGroup(); split.Panel1.Controls.Add(edit); split.Panel2.Padding = new Padding(12); split.Panel2.Controls.Add(_profitGrid); tab.Controls.Add(split); AddPanelToggle(tab, split, 420); return tab;
    }

    private void RefreshAll()
    {
        var itemId = _selectedPrice?.Id;
        _refreshingPrices = true; var priceGroupId = (_priceGroup.SelectedItem as PriceGroup)?.Id; _priceGroup.DataSource = null; _priceGroup.DataSource = _groups; _priceGroup.SelectedItem = _groups.FirstOrDefault(x => x.Id == priceGroupId) ?? _groups.FirstOrDefault(x => x.Id == "retail") ?? _groups.First(); _refreshingPrices = false;
        RefreshPricePreset(); RefreshPriceGrid();
        _profitGrid.DataSource = _groups.Select(x => new { x.Id, MüşteriKategorisi = x.Name, KârYüzde = (x.CostMultiplier - 1m) * 100m, Çarpan = x.CostMultiplier }).ToList(); Hide(_profitGrid, "Id");
        var selected = (_calcGroup.SelectedItem as PriceGroup)?.Id; _calcGroup.DataSource = null; _calcGroup.DataSource = _groups; _calcGroup.SelectedItem = _groups.FirstOrDefault(x => x.Id == selected) ?? _groups.FirstOrDefault(x => x.Id == "retail") ?? _groups.First();
        var checkedIds = _calcItems.CheckedItems.Cast<PriceItem>().Select(x => x.Id).ToHashSet(); _calcItems.Items.Clear(); foreach (var item in _items.Where(x => x.Active && !x.Deleted).OrderBy(x => x.Category).ThenBy(x => x.Name).ThenBy(x => x.Variant)) _calcItems.Items.Add(item, checkedIds.Contains(item.Id));
        if (itemId is not null) SelectRow(_priceGrid, itemId); Recalculate();
    }
    private void RefreshPriceGrid()
    {
        var group = _priceGroup.SelectedItem as PriceGroup ?? _groups.FirstOrDefault(x => x.Id == "retail") ?? _groups.First();
        _priceGrid.DataSource = _items.Where(x => !x.Deleted).OrderBy(x => x.Category).ThenBy(x => x.Name).ThenBy(x => x.Variant).Select(x =>
        {
            var special = PricingEngine.GetSpecialProfitPercent(x, group.Id);
            var multiplier = PricingEngine.ResolveMultiplier(x, group.Id, group.CostMultiplier);
            return new { x.Id, Tür = x.Category, Ad = x.Name, Açıklama = x.Variant, Birim = x.Unit, Para = x.Currency, AlışFiyatı = x.UnitCost, SatışBirim = decimal.Round(x.UnitCost * multiplier, 4), Hesap = FormulaText(x.Formula), SatışKârı = special.HasValue ? $"{group.Name} özel %{special.Value:0.##}" : $"{group.Name} standart %{(group.CostMultiplier - 1m) * 100m:0.##}" };
        }).ToList();
        Hide(_priceGrid, "Id");
    }
    private void SavePrice()
    {
        if (string.IsNullOrWhiteSpace(_priceName.Text)) { MessageBox.Show("Ürün adı boş olamaz.", "Fiyat Tanımları"); return; }
        var item = _selectedPrice ?? new PriceItem { Id = Guid.NewGuid().ToString("N") }; item.Category = _priceCategory.Text; item.Name = _priceName.Text.Trim(); item.Variant = _priceVariant.Text.Trim(); item.Unit = _priceUnit.Text.Trim(); item.Currency = _priceCurrency.Text; item.Formula = _priceFormula.Text; item.UnitCost = _priceCost.Value; item.SecondaryCost = _priceSecondary.Value; item.SheetWidthCm = _priceSheetW.Value; item.SheetHeightCm = _priceSheetH.Value; item.Active = _priceActive.Checked; item.Deleted = false; item.IsPrintProduct = item.Category == "Baskı"; item.GroupProfitPercentOverrides ??= []; foreach (var (groupId, controls) in _priceSpecialProfits) { if (controls.Enabled.Checked) item.GroupProfitPercentOverrides[groupId] = controls.Percent.Value; else item.GroupProfitPercentOverrides.Remove(groupId); } if (_selectedPrice is null) _items.Add(item); _selectedPrice = item; CatalogStore.Save(_groups, _items); RefreshAll();
    }
    private void SelectPrice() { if (_priceGrid.CurrentRow?.Cells["Id"].Value is not string id) return; _selectedPrice = _items.FirstOrDefault(x => x.Id == id); if (_selectedPrice is null) return; var x = _selectedPrice; _priceCategory.Text = x.Category; RefreshPricePreset(); _priceName.Text = x.Name; _priceVariant.Text = x.Variant; _priceUnit.Text = x.Unit; _priceCurrency.Text = x.Currency; _priceFormula.Text = x.Formula; _priceCost.Value = x.UnitCost; _priceSecondary.Value = x.SecondaryCost; _priceSheetW.Value = x.SheetWidthCm; _priceSheetH.Value = x.SheetHeightCm; _priceActive.Checked = x.Active; foreach (var (groupId, controls) in _priceSpecialProfits) { decimal value = 0; var hasSpecial = x.GroupProfitPercentOverrides is not null && x.GroupProfitPercentOverrides.TryGetValue(groupId, out value); controls.Enabled.Checked = hasSpecial; controls.Percent.Value = hasSpecial ? value : (_groups.First(g => g.Id == groupId).CostMultiplier - 1m) * 100m; } }
    private void ClearPrice() { _selectedPrice = null; _priceCategory.SelectedIndex = 0; RefreshPricePreset(); _priceName.Clear(); _priceVariant.Clear(); _priceUnit.Text = "m²"; _priceCurrency.Text = "TL"; _priceFormula.Text = PricingFormula.SquareMeter; _priceCost.Value = _priceSecondary.Value = _priceSheetW.Value = _priceSheetH.Value = 0; _priceActive.Checked = true; foreach (var (groupId, controls) in _priceSpecialProfits) { controls.Enabled.Checked = false; controls.Percent.Value = (_groups.First(g => g.Id == groupId).CostMultiplier - 1m) * 100m; } }
    private void RefreshPricePreset()
    {
        var type = _priceCategory.SelectedItem?.ToString() ?? "Malzeme"; var choices = new List<PriceItem> { new() { Id = "", Name = "Seç" } };
        choices.AddRange(type == "Baskı" ? _items.Where(x => x.Category == "Baskı") : type == "Hizmet" ? _items.Where(x => x.Category == "Hizmet") : _items.Where(x => x.Category == "Malzeme"));
        _pricePreset.DataSource = null; _pricePreset.DisplayMember = nameof(PriceItem.DisplayName); _pricePreset.DataSource = choices;
    }
    private void ApplyPricePreset() { if (_pricePreset.SelectedItem is not PriceItem { Id: not "" } item) return; _priceName.Text = item.Name; _priceVariant.Text = item.Variant; _priceUnit.Text = item.Unit; _priceCurrency.Text = item.Currency; _priceFormula.Text = item.Formula; _priceCost.Value = item.UnitCost; _priceSecondary.Value = item.SecondaryCost; _priceSheetW.Value = item.SheetWidthCm; _priceSheetH.Value = item.SheetHeightCm; }
    private static string FormulaText(string formula) => formula switch { PricingFormula.SquareMeter => "m² üzerinden", PricingFormula.Meter => "metre üzerinden", PricingFormula.Piece => "adet üzerinden", PricingFormula.Minute => "dakika üzerinden", PricingFormula.Hour => "saat üzerinden", PricingFormula.Fixed => "sabit ücret", PricingFormula.SheetArea => "levha alanı oranı", PricingFormula.UvTable => "UV 60×90 oranı", PricingFormula.DtfTier => "DTF 10 m kademesi", PricingFormula.PercentMaterial => "malzeme yüzdesi", _ => formula };
    private void SelectGroup() { if (_profitGrid.CurrentRow?.Cells["Id"].Value is not string id) return; _selectedGroup = _groups.FirstOrDefault(x => x.Id == id); if (_selectedGroup is null) return; _groupName.Text = _selectedGroup.Name; _groupProfit.Value = (_selectedGroup.CostMultiplier - 1m) * 100m; }
    private void SaveGroup() { if (string.IsNullOrWhiteSpace(_groupName.Text)) return; var g = _selectedGroup ?? new PriceGroup { Id = Guid.NewGuid().ToString("N"), Code = Guid.NewGuid().ToString("N")[..8] }; g.Name = _groupName.Text.Trim(); g.CostMultiplier = 1m + _groupProfit.Value / 100m; if (_selectedGroup is null) _groups.Add(g); _selectedGroup = g; CatalogStore.Save(_groups, _items); RefreshAll(); }
    private void Recalculate() { var selected = _calcItems.CheckedItems.Cast<PriceItem>().ToList(); if (selected.Count == 0) { _calcLines.Items.Clear(); _calcCost.Text = "Maliyet: 0,00 TL"; _calcSale.Text = "Önerilen satış: 0,00 TL"; return; } var group = (PriceGroup)_calcGroup.SelectedItem!; var result = PricingEngine.Calculate(selected, new(_calcWidth.Value, _calcHeight.Value, _calcLength.Value, _calcMinutes.Value, _calcQty.Value, _calcRate.Value), group.CostMultiplier, _calcAlternative.Checked ? _calcAlternativePercent.Value : null, group.Id, _groups, _items); _calcLines.Items.Clear(); foreach (var line in result.Lines) _calcLines.Items.Add($"{line.Name,-42} {line.QuantityUsed,9:N4} × {line.UnitCost,10:N2} {line.Currency,-3} = {line.CostTl,10:N2} TL"); _calcCost.Text = $"Maliyet: {result.CostTl:N2} TL"; _calcSale.Text = $"Önerilen satış: {result.SaleTl:N2} TL"; }
    private void ResetCalculator() { _calcWidth.Value = _calcHeight.Value = _calcLength.Value = _calcMinutes.Value = 0; _calcQty.Value = 1; _calcRate.Value = 40; _calcAlternative.Checked = false; _calcAlternativePercent.Value = 0; for (var i = 0; i < _calcItems.Items.Count; i++) _calcItems.SetItemChecked(i, false); Recalculate(); }
    private static void Hide(DataGridView grid, string name) { if (grid.Columns[name] is DataGridViewColumn column) column.Visible = false; }
    private static void SelectRow(DataGridView grid, string id) { foreach (DataGridViewRow row in grid.Rows) if (row.Cells["Id"].Value as string == id) { grid.CurrentCell = row.Cells[1]; break; } }
    private static void AddStack(TableLayoutPanel form, string label, Control control) { form.Controls.Add(UiTheme.Label(label)); control.Margin = new Padding(3, 0, 3, 3); control.Width = 330; form.Controls.Add(control); }
    private static void AddField(TableLayoutPanel form, string label, Control control, int row) { form.RowStyles.Add(new RowStyle(SizeType.AutoSize)); form.Controls.Add(UiTheme.Label(label), 0, row); form.Controls.Add(control, 1, row); }
    private static void AddPanelToggle(TabPage tab, SplitContainer split, int preferredWidth)
    {
        var toggle = UiTheme.Button("", false); toggle.Width = 190; toggle.Height = 28; var bar = new Panel { Dock = DockStyle.Top, Height = 34, BackColor = UiTheme.Sand, Padding = new Padding(3, 0, 3, 0) }; bar.Controls.Add(toggle);
        void Text() => toggle.Text = split.Panel1Collapsed ? "▣ Detayları göster" : "▣ Detayları gizle";
        void OpenAtPreferredWidth()
        {
            // Kapalı panelin eski SplitterDistance değeri WinForms tarafından daraltılır.
            // Genişliği pencerenin mevcut alanına göre her açılışta yeniden hesapla.
            var usableWidth = Math.Max(0, split.ClientSize.Width - split.SplitterWidth);
            var maximum = Math.Max(220, usableWidth - 360);
            var target = Math.Min(preferredWidth, maximum);
            if (usableWidth > 0) split.SplitterDistance = Math.Max(220, target);
        }
        toggle.Click += (_, _) => { if (split.Panel1Collapsed) { split.Panel1Collapsed = false; split.BeginInvoke((Action)OpenAtPreferredWidth); } else split.Panel1Collapsed = true; Text(); };
        tab.Controls.Add(bar); split.Panel1Collapsed = true; Text();
    }
}

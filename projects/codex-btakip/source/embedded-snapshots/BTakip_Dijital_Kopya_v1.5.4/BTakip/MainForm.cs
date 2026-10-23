using Microsoft.Win32;

namespace BTakip;

public sealed class MainForm : Form
{
    private readonly DataStore _store;
    private readonly SyncService _sync;
    private readonly System.Windows.Forms.Timer _syncTimer = new();
    private readonly NotifyIcon _tray;
    private bool _exitRequested;
    private bool _syncRunning;
    private bool _changingTabs;
    private bool _unsavedPromptOpen;
    private bool _skipClosePrompt;

    private readonly TabControl _tabs = new();
    private readonly Label _syncBadge = new();
    private Button _undoButton = null!;
    private readonly Label _dashboardCustomer = new();
    private readonly Label _dashboardBalance = new();
    private readonly Label _dashboardOrders = new();
    private readonly Label _dashboardBackup = new();

    private DataGridView _customerGrid = null!;
    private TextBox _customerName = null!;
    private TextBox _customerCompany = null!;
    private TextBox _customerPhone = null!;
    private TextBox _customerEmail = null!;
    private TextBox _customerNotes = null!;
    private ComboBox _customerGroup = null!;
    private ComboBox _customerSort = null!;
    private string? _selectedCustomerId;
    private (DataGridView Grid, int RowIndex, int ColumnIndex, string Value)? _inlineGridEditOriginal;

    private DataGridView _priceGrid = null!;
    private ComboBox _priceCategory = null!;
    private ComboBox _priceStructure = null!;
    private TextBox _priceName = null!;
    private Label _priceNameLabel = null!;
    private TextBox _priceVariant = null!;
    private TextBox _priceUnit = null!;
    private ComboBox _priceCurrency = null!;
    private ComboBox _priceFormula = null!;
    private ComboBox _priceGroup = null!;
    private NumericUpDown _priceCost = null!;
    private NumericUpDown _priceSecondary = null!;
    private NumericUpDown _priceSheetWidth = null!;
    private NumericUpDown _priceSheetHeight = null!;
    private NumericUpDown _priceThickness = null!;
    private ComboBox _priceBaseMaterial = null!;
    private CheckBox _pricePrintEnabled = null!;
    private CheckBox _priceServiceEnabled = null!;
    private TextBox _priceServiceName = null!;
    private ComboBox _priceServiceFormula = null!;
    private NumericUpDown _priceServiceCost = null!;
    private CheckBox _priceActive = null!;
    private Label _priceVariantLabel = null!;
    private Label _priceUnitLabel = null!;
    private Label _priceCurrencyLabel = null!;
    private Label _priceFormulaLabel = null!;
    private Label _priceCostFieldLabel = null!;
    private Label _priceSecondaryLabel = null!;
    private Label _priceSheetWidthLabel = null!;
    private Label _priceSheetHeightLabel = null!;
    private Label _priceThicknessLabel = null!;
    private Label _priceBaseMaterialLabel = null!;
    private Label _priceServiceNameLabel = null!;
    private Label _priceServiceFormulaLabel = null!;
    private Label _priceServiceCostLabel = null!;
    private Label _priceFormulaHelp = null!;
    private Label _priceMaterialPreview = null!;
    private FlowLayoutPanel _priceProfitPanel = null!;
    private readonly Dictionary<string, (CheckBox UseSpecial, NumericUpDown ProfitPercent)> _priceProfitInputs = [];
    private Button _priceSaveButton = null!;
    private Button _priceNewButton = null!;
    private Button _priceActionButton = null!;
    private string? _selectedPriceId;
    private bool _loadingPriceEditor;
    private bool _changingPriceSelection;

    private ComboBox _calcGroup = null!;
    private TextBox _calcDescription = null!;
    private NumericUpDown _calcWidth = null!;
    private NumericUpDown _calcHeight = null!;
    private NumericUpDown _calcLength = null!;
    private NumericUpDown _calcMinutes = null!;
    private NumericUpDown _calcQuantity = null!;
    private NumericUpDown _calcRate = null!;
    private CheckBox _calcAlternative = null!;
    private NumericUpDown _calcAlternativePercent = null!;
    private CheckedListBox _calcItems = null!;
    private ListBox _calcLines = null!;
    private Label _calcCostLabel = null!;
    private Label _calcSaleLabel = null!;
    private CalculationResult? _lastCalculation;

    private ComboBox _ledgerCustomer = null!;
    private DataGridView _ledgerGrid = null!;
    private Label _ledgerBalance = null!;
    private CheckBox _ledgerDateFilter = null!;
    private CheckBox _ledgerShowDescription = null!;
    private DateTimePicker _ledgerFrom = null!;
    private DateTimePicker _ledgerTo = null!;
    private ComboBox _ledgerSort = null!;
    private bool _refreshingLedger;
    private (int RowIndex, int ColumnIndex, string Value)? _ledgerEditOriginal;
    private DateTimePicker _ledgerOrderDate = null!;
    private ComboBox _ledgerOrderMaterial = null!;
    private TextBox _ledgerOrderDescription = null!;
    private NumericUpDown _ledgerOrderWidth = null!;
    private NumericUpDown _ledgerOrderHeight = null!;
    private NumericUpDown _ledgerOrderLength = null!;
    private NumericUpDown _ledgerOrderQuantity = null!;
    private Label _ledgerOrderPreview = null!;
    private NumericUpDown _paymentAmount = null!;
    private ComboBox _paymentType = null!;
    private TextBox _paymentDescription = null!;

    private TextBox _syncUrl = null!;
    private TextBox _syncToken = null!;
    private NumericUpDown _syncInterval = null!;
    private NumericUpDown _usdRate = null!;
    private CheckBox _autoRate = null!;
    private CheckBox _startWindows = null!;
    private Label _syncStatus = null!;
    private Label _securityStatus = null!;

    private DataGridView _groupGrid = null!;
    private TextBox _groupName = null!;
    private NumericUpDown _groupProfitPercent = null!;
    private Label _groupExample = null!;
    private string? _selectedGroupId;
    private ComboBox _profitPriceItem = null!;
    private ComboBox _profitItemGroup = null!;
    private CheckBox _profitUseSpecial = null!;
    private NumericUpDown _profitSpecialPercent = null!;
    private Label _profitPriceItemStatus = null!;

    public MainForm(string[] args)
    {
        var dataDir = GetArgument(args, "--data-dir");
        _store = new DataStore(dataDir);
        _sync = new SyncService(_store) { ConflictResolver = ResolveConflictAsync };

        Text = "İzmirde Reklam";
        Width = 1380;
        Height = 860;
        MinimumSize = new Size(1120, 700);
        StartPosition = FormStartPosition.CenterScreen;
        BackColor = Color.White;
        Font = new Font("Segoe UI", 9.5f);

        _tray = new NotifyIcon
        {
            Icon = SystemIcons.Application,
            Text = "İzmirde Reklam — senkronizasyon çalışıyor",
            Visible = true,
            ContextMenuStrip = BuildTrayMenu()
        };
        _tray.DoubleClick += (_, _) => RestoreWindow();

        BuildShell();
        RefreshAll();
        ConfigureSyncTimer();
        Shown += async (_, _) =>
        {
            if (!_store.ApplicationIntegrityOk)
                MessageBox.Show(_store.SecurityStatus, "Yazılım Güvenliği", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            if (_store.State.Settings.AutoExchangeRate) await RefreshExchangeRateAsync(false);
            await RunSyncAsync(false);
        };
        FormClosing += MainForm_FormClosing;
    }

    private void BuildShell()
    {
        var header = new Panel { Dock = DockStyle.Top, Height = 72, BackColor = UiTheme.Navy, Padding = new Padding(22, 12, 18, 10) };
        var title = new Label { Text = "BTakip", ForeColor = Color.White, Font = new Font("Segoe UI Semibold", 22f), AutoSize = true, Location = new Point(20, 14) };
        var subtitle = new Label { Text = "İzmirde Reklam Müşteri Takip", ForeColor = Color.FromArgb(183, 213, 220), Font = new Font("Segoe UI", 9.5f), AutoSize = true, Location = new Point(170, 30) };
        _undoButton = UiTheme.Button("Geri Al", false);
        _undoButton.Width = 96;
        _undoButton.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        _undoButton.Click += async (_, _) => await UndoLastChangeAsync();
        _syncBadge.Text = "● Yerel kayıt hazır";
        _syncBadge.ForeColor = Color.FromArgb(155, 226, 205);
        _syncBadge.AutoSize = true;
        _syncBadge.Font = new Font("Segoe UI Semibold", 9.5f);
        _syncBadge.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        _syncBadge.Location = new Point(header.Width - 260, 26);
        header.Resize += (_, _) =>
        {
            _syncBadge.Location = new Point(header.ClientSize.Width - _syncBadge.Width - 24, 26);
            _undoButton.Location = new Point(Math.Max(520, _syncBadge.Left - _undoButton.Width - 22), 18);
        };
        header.Controls.AddRange([title, subtitle, _undoButton, _syncBadge]);

        _tabs.Dock = DockStyle.Fill;
        _tabs.Font = new Font("Segoe UI Semibold", 10f);
        _tabs.Padding = new Point(16, 7);
        _tabs.TabPages.Add(BuildDashboardTab());
        _tabs.TabPages.Add(BuildCustomersTab());
        _tabs.TabPages.Add(BuildPricesTab());
        _tabs.TabPages.Add(BuildCalculatorTab());
        _tabs.TabPages.Add(BuildLedgerTab());
        _tabs.TabPages.Add(BuildProfitSettingsTab());
        _tabs.TabPages.Add(BuildSyncTab());
        _tabs.Selecting += Tabs_Selecting;
        _tabs.SelectedIndexChanged += (_, _) => RefreshAll();

        Controls.Add(_tabs);
        Controls.Add(header);
    }

    private TabPage BuildDashboardTab()
    {
        var tab = NewTab("Genel Bakış");
        var body = new Panel { Dock = DockStyle.Fill, Padding = new Padding(28), BackColor = Color.White };
        var cards = new TableLayoutPanel { Location = new Point(28, 32), Height = 150, Width = 930, ColumnCount = 4, RowCount = 1, Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right };
        for (var i = 0; i < 4; i++) cards.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 25));
        cards.Controls.Add(Card("Müşteri", _dashboardCustomer, UiTheme.Teal), 0, 0);
        cards.Controls.Add(Card("Açık Bakiye", _dashboardBalance, UiTheme.Orange), 1, 0);
        cards.Controls.Add(Card("Sipariş", _dashboardOrders, Color.FromArgb(87, 102, 170)), 2, 0);
        cards.Controls.Add(Card("Son Yedek", _dashboardBackup, Color.FromArgb(83, 135, 91)), 3, 0);
        body.Resize += (_, _) => cards.Width = Math.Max(800, body.ClientSize.Width - 56);

        var actions = new FlowLayoutPanel { Location = new Point(28, 212), Width = 900, Height = 56, FlowDirection = FlowDirection.LeftToRight };
        var calc = UiTheme.Button("Yeni Fiyat Hesabı", true);
        calc.Click += (_, _) => _tabs.SelectedIndex = 3;
        var customer = UiTheme.Button("Yeni Müşteri", false);
        customer.Click += (_, _) => { _tabs.SelectedIndex = 1; ClearCustomerEditor(); _customerName.Focus(); };
        var payment = UiTheme.Button("Tahsilat Gir", false);
        payment.Click += (_, _) => _tabs.SelectedIndex = 4;
        var sync = UiTheme.Button("Şimdi Eşitle", false);
        sync.Click += async (_, _) => await RunSyncAsync(true);
        actions.Controls.AddRange([calc, customer, payment, sync]);

        body.Controls.AddRange([cards, actions]);
        tab.Controls.Add(body);
        return tab;
    }

    private static Panel Card(string title, Label value, Color accent)
    {
        var panel = new Panel { Dock = DockStyle.Fill, BackColor = Color.White, Margin = new Padding(6), Padding = new Padding(16), BorderStyle = BorderStyle.FixedSingle };
        var bar = new Panel { Dock = DockStyle.Left, Width = 5, BackColor = accent };
        var label = new Label { Text = title.ToUpperInvariant(), ForeColor = UiTheme.Muted, Font = new Font("Segoe UI Semibold", 8.5f), AutoSize = true, Location = new Point(23, 21) };
        value.ForeColor = UiTheme.Navy;
        value.Font = new Font("Segoe UI Semibold", 19f);
        value.AutoSize = true;
        value.Location = new Point(21, 55);
        panel.Controls.AddRange([bar, label, value]);
        return panel;
    }

    private TabPage BuildCustomersTab()
    {
        var tab = NewTab("Müşteriler");
        var split = new SplitContainer { Dock = DockStyle.Fill, SplitterDistance = 370, FixedPanel = FixedPanel.Panel1 };
        FixLeftPane(split, 370, 330);
        var editor = UiTheme.EditorPanel();
        var form = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, ColumnCount = 1, Padding = new Padding(0), GrowStyle = TableLayoutPanelGrowStyle.AddRows };
        form.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        form.Controls.Add(UiTheme.Label("Müşteri Kartı", true));
        _customerName = UiTheme.TextBox(); AddStackField(form, "Ad *", _customerName);
        _customerCompany = UiTheme.TextBox(); AddStackField(form, "Firma", _customerCompany);
        _customerPhone = UiTheme.TextBox(); AddStackField(form, "Telefon", _customerPhone);
        _customerEmail = UiTheme.TextBox(); AddStackField(form, "E-posta", _customerEmail);
        _customerGroup = UiTheme.Combo(); AddStackField(form, "Fiyat Grubu", _customerGroup);
        _customerNotes = UiTheme.TextBox(true); AddStackField(form, "Not", _customerNotes);
        var buttons = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Top, Margin = new Padding(0, 14, 0, 0) };
        var save = UiTheme.Button("Kaydet"); save.Click += async (_, _) => await SaveCustomerAsync();
        var clear = UiTheme.Button("Müşteri Ekle", false); clear.Click += (_, _) => { ClearCustomerEditor(); _customerName.Focus(); };
        var importCustomer = UiTheme.Button("Excel ile Yükle", false); importCustomer.Click += async (_, _) => await ImportExcelAsync(true);
        var convertCustomer = UiTheme.Button("Excel'i Dönüştür", false); convertCustomer.Click += async (_, _) => await ImportExcelAsync(true, true);
        var customerNote = UiTheme.Button("Müşteriye Not Yolla", false); customerNote.Click += (_, _) => CreateSelectedCustomerPdf();
        var customerPdf = UiTheme.Button("Müşteri Hesabını PDF Al", false); customerPdf.Click += (_, _) => CreateSelectedCustomerPdf();
        var delete = UiTheme.Button("Sil", false); delete.Click += async (_, _) => await DeleteCustomerAsync();
        buttons.Controls.AddRange([save, clear, importCustomer, convertCustomer, customerNote, customerPdf, delete]);
        form.Controls.Add(buttons);
        editor.Controls.Add(form);

        _customerGrid = UiTheme.Grid();
        _customerGrid.ReadOnly = false;
        AddGridColumn(_customerGrid, "id", "Kimlik", false);
        AddGridColumn(_customerGrid, "name", "Müşteri", true, 170);
        AddGridColumn(_customerGrid, "company", "Firma", true, 130);
        AddGridColumn(_customerGrid, "group", "Fiyat Grubu", true, 130);
        AddGridColumn(_customerGrid, "phone", "Telefon", true, 100);
        AddGridColumn(_customerGrid, "balance", "Bakiye", true, 90, "N2");
        foreach (var name in new[] { "id", "balance" })
            if (_customerGrid.Columns[name] is DataGridViewColumn column) column.ReadOnly = true;
        _customerGrid.CellBeginEdit += InlineGrid_CellBeginEdit;
        _customerGrid.CellEndEdit += async (_, e) => await SaveCustomerGridEditAsync(e);
        _customerGrid.SelectionChanged += (_, _) => LoadSelectedCustomer();
        var sortPanel = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 46, Padding = new Padding(4, 7, 4, 5), BackColor = UiTheme.Sand };
        sortPanel.Controls.Add(new Label { Text = "Sırala:", AutoSize = true, Margin = new Padding(4, 7, 6, 0), ForeColor = UiTheme.Ink });
        _customerSort = UiTheme.Combo();
        _customerSort.Width = 220; _customerSort.Dock = DockStyle.None;
        _customerSort.Items.AddRange(["A'dan Z'ye", "Z'den A'ya", "Yüksekten düşüğe", "Düşükten yükseğe", "Son değişenler"]);
        _customerSort.SelectedIndex = 0;
        _customerSort.SelectedIndexChanged += (_, _) => RefreshCustomerGrid();
        sortPanel.Controls.Add(_customerSort);
        var exportTable = UiTheme.Button("Tabloyu PDF Al", false); exportTable.Height = 32; exportTable.Margin = new Padding(10, 0, 0, 0); exportTable.Click += (_, _) => ExportCustomerTablePdf();
        sortPanel.Controls.Add(exportTable);
        split.Panel1.Controls.Add(editor);
        split.Panel2.Padding = new Padding(12);
        split.Panel2.Controls.Add(_customerGrid);
        split.Panel2.Controls.Add(sortPanel);
        tab.Controls.Add(split);
        return tab;
    }

    private TabPage BuildPricesTab()
    {
        var tab = NewTab("Fiyat Tanımları");
        var split = new SplitContainer { Dock = DockStyle.Fill, SplitterDistance = 430, FixedPanel = FixedPanel.Panel1 };
        FixLeftPane(split, 430, 390);
        var editor = UiTheme.EditorPanel();
        var form = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, ColumnCount = 1 };
        form.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        var priceModeBar = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Top, Margin = new Padding(0, 0, 0, 10) };
        _priceNewButton = UiTheme.Button("Ürün Ekle", false); _priceNewButton.Width = 160;
        _priceNewButton.Click += async (_, _) =>
        {
            if (_selectedPriceId is null) { UpdatePriceEditorMode(); _priceName.Focus(); return; }
            if (!HasPriceEditorChanges() || await ConfirmUnsavedChangesAsync(2)) { ClearPriceEditor(); _priceName.Focus(); }
        };
        _priceSaveButton = UiTheme.Button("Ürünü Güncelle", false); _priceSaveButton.Width = 160;
        _priceSaveButton.Click += (_, _) =>
        {
            if (_selectedPriceId is null) MessageBox.Show("Güncellemek için tablodan bir ürün seçin.", "Ürünü Güncelle", MessageBoxButtons.OK, MessageBoxIcon.Information);
            UpdatePriceEditorMode();
        };
        priceModeBar.Controls.AddRange([_priceNewButton, _priceSaveButton]);
        form.Controls.Add(priceModeBar);
        form.Controls.Add(UiTheme.Label("Tek Ürün Oluştur", true));
        form.Controls.Add(new Label
        {
            Text = "Her kayıt tek türdedir: Malzeme, Baskı veya Hizmet. Baskı kaydında kullanacağı malzeme seçilir; hizmet ayrı kayıt olarak eklenir. Satış, müşterinin kartındaki fiyat grubuna göre hesaplanır.",
            AutoSize = true, MaximumSize = new Size(365, 0), ForeColor = UiTheme.Muted, Margin = new Padding(3, 4, 3, 12)
        });
        _priceCategory = UiTheme.Combo(); _priceCategory.Items.Add("Ürün"); _priceCategory.SelectedIndex = 0;
        _priceStructure = UiTheme.Combo();
        _priceStructure.Items.AddRange(["Malzeme", "Baskı", "Hizmet"]);
        _priceStructure.SelectedIndex = 0;
        _priceStructure.SelectedIndexChanged += (_, _) => { if (!_loadingPriceEditor) ApplyPriceStructure(); };
        AddStackField(form, "Kayıt türü *", _priceStructure);
        _priceName = UiTheme.TextBox(); _priceNameLabel = AddStackField(form, "Ürün / malzeme adı *", _priceName);
        _priceVariant = UiTheme.TextBox(); _priceVariantLabel = new Label();
        _priceUnit = UiTheme.TextBox(); _priceUnitLabel = new Label();
        _priceCurrency = UiTheme.Combo(); _priceCurrency.Items.AddRange(["TL", "USD", "%"]); _priceCurrencyLabel = new Label();
        _pricePrintEnabled = new CheckBox { Text = "Bu üründe baskı var", AutoSize = true, Font = new Font("Segoe UI Semibold", 9.5f), ForeColor = UiTheme.Navy, Margin = new Padding(3, 10, 3, 5) };
        _pricePrintEnabled.CheckedChanged += (_, _) => { if (!_loadingPriceEditor) ConfigurePriceCategory(true); };
        _priceBaseMaterial = UiTheme.Combo(); _priceBaseMaterial.DropDownWidth = 430; _priceBaseMaterialLabel = AddStackField(form, "Baskıda kullanılan malzeme", _priceBaseMaterial);
        _priceFormula = UiTheme.Combo();
        _priceFormula.DropDownWidth = 330;
        _priceFormula.DisplayMember = "Value"; _priceFormula.ValueMember = "Key";
        _priceFormulaLabel = AddStackField(form, "Malzeme / baskı ölçüsü", _priceFormula);
        _priceFormulaHelp = new Label { AutoSize = true, MaximumSize = new Size(365, 0), ForeColor = UiTheme.Teal, Margin = new Padding(3, 2, 3, 8) };
        form.Controls.Add(_priceFormulaHelp);
        _priceCost = UiTheme.Number(10000000, 4); _priceCostFieldLabel = AddStackField(form, "Alış birim fiyatı / işlem yüzdesi", _priceCost);
        _priceSecondary = UiTheme.Number(10000000, 4); _priceSecondaryLabel = AddStackField(form, "10 metre üstü alış fiyatı", _priceSecondary);
        _priceSheetWidth = UiTheme.Number(10000, 2); _priceSheetWidthLabel = AddStackField(form, "Levha en (cm)", _priceSheetWidth);
        _priceSheetHeight = UiTheme.Number(10000, 2); _priceSheetHeightLabel = AddStackField(form, "Levha boy (cm)", _priceSheetHeight);
        _priceThickness = UiTheme.Number(1000, 2); _priceThicknessLabel = AddStackField(form, "Kalınlık (mm)", _priceThickness);
        _priceMaterialPreview = new Label { AutoSize = true, MaximumSize = new Size(365, 0), BackColor = UiTheme.Mint, ForeColor = UiTheme.Navy, Padding = new Padding(10), Margin = new Padding(3, 6, 3, 8) };
        form.Controls.Add(_priceMaterialPreview);
        _priceServiceEnabled = new CheckBox { Text = "Bu ürüne hizmet ekle", AutoSize = true, Font = new Font("Segoe UI Semibold", 9.5f), ForeColor = UiTheme.Navy, Margin = new Padding(3, 12, 3, 5) };
        _priceServiceEnabled.CheckedChanged += (_, _) => UpdateProductServiceFields();
        _priceServiceName = UiTheme.TextBox(); _priceServiceName.PlaceholderText = "Örn: Sıvama"; _priceServiceNameLabel = AddStackField(form, "Hizmet adı", _priceServiceName);
        _priceServiceFormula = UiTheme.Combo();
        _priceServiceFormula.DisplayMember = "Value"; _priceServiceFormula.ValueMember = "Key";
        _priceServiceFormula.DataSource = new[] { PricingFormula.SquareMeter, PricingFormula.Minute }.Select(code => new KeyValuePair<string, string>(code, PricingFormula.Labels[code])).ToList();
        _priceServiceFormulaLabel = AddStackField(form, "Hizmet hesabı", _priceServiceFormula);
        _priceServiceCost = UiTheme.Number(10000000, 4); _priceServiceCostLabel = AddStackField(form, "Hizmet birim maliyeti", _priceServiceCost);
        _priceServiceFormula.SelectedIndexChanged += (_, _) => UpdateProductServiceFields();
        _priceProfitPanel = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true, FlowDirection = FlowDirection.TopDown, WrapContents = false, Margin = new Padding(0, 0, 0, 5) };
        _priceActive = new CheckBox { Text = "Aktif", Checked = true, AutoSize = true, Margin = new Padding(3, 10, 3, 6) };
        form.Controls.Add(_priceActive);
        _priceActionButton = UiTheme.Button("Ürünü Ekle"); _priceActionButton.Width = 190; _priceActionButton.Click += async (_, _) => await SavePriceAsync();
        form.Controls.Add(_priceActionButton);
        _priceFormula.SelectedIndexChanged += (_, _) => { if (!_loadingPriceEditor) UpdatePriceFormulaFields(true); };
        _priceSheetWidth.ValueChanged += (_, _) => UpdatePriceMaterialPreview();
        _priceSheetHeight.ValueChanged += (_, _) => UpdatePriceMaterialPreview();
        _priceThickness.ValueChanged += (_, _) => UpdatePriceMaterialPreview();
        _priceCost.ValueChanged += (_, _) => UpdatePriceMaterialPreview();
        _priceCurrency.SelectedIndexChanged += (_, _) => UpdatePriceMaterialPreview();
        editor.Controls.Add(form);

        _priceGrid = UiTheme.Grid();
        _priceGrid.ReadOnly = false;
        AddGridColumn(_priceGrid, "id", "Kimlik", false);
        AddGridColumn(_priceGrid, "category", "Tür", true, 115);
        AddGridColumn(_priceGrid, "name", "Ad", true, 130);
        AddGridColumn(_priceGrid, "variant", "Açıklama", true, 180);
        AddGridColumn(_priceGrid, "unit", "Birim", true, 65);
        AddGridColumn(_priceGrid, "currency", "Para", true, 55);
        AddGridColumn(_priceGrid, "cost", "Alış Fiyatı", true, 85, "N4");
        AddGridColumn(_priceGrid, "sale", "Satış Birim", true, 90, "N4");
        AddGridColumn(_priceGrid, "formula", "Hesap", true, 110);
        AddGridColumn(_priceGrid, "specialProfit", "Satış Kârı", true, 190);
        foreach (var name in new[] { "id", "sale" })
            if (_priceGrid.Columns[name] is DataGridViewColumn column) column.ReadOnly = true;
        _priceGrid.CellBeginEdit += InlineGrid_CellBeginEdit;
        _priceGrid.CellEndEdit += async (_, e) => await SavePriceGridEditAsync(e);
        _priceGrid.SelectionChanged += PriceGrid_SelectionChanged;
        split.Panel1.Controls.Add(editor);
        split.Panel2.Padding = new Padding(12);
        var priceViewBar = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 46, Padding = new Padding(4, 7, 4, 5), BackColor = UiTheme.Sand };
        var delete = UiTheme.Button("Sil", false); delete.Height = 32; delete.Click += async (_, _) => await DeletePriceAsync();
        priceViewBar.Controls.Add(delete);
        priceViewBar.Controls.Add(new Label { Text = "Tablo fiyat grubu:", AutoSize = true, Margin = new Padding(4, 7, 6, 0), ForeColor = UiTheme.Ink });
        _priceGroup = UiTheme.Combo(); _priceGroup.Width = 240; _priceGroup.Dock = DockStyle.None;
        _priceGroup.SelectedIndexChanged += (_, _) => { if (!_loadingPriceEditor) RefreshPriceGrid(); };
        priceViewBar.Controls.Add(_priceGroup);
        split.Panel2.Controls.Add(_priceGrid);
        split.Panel2.Controls.Add(priceViewBar);
        tab.Controls.Add(split);
        ConfigurePriceCategory(true);
        UpdateProductServiceFields();
        PopulatePriceProfitInputs(null);
        UpdatePriceEditorMode();
        return tab;
    }

    private void UpdatePriceEditorMode()
    {
        if (_priceNewButton is null || _priceSaveButton is null || _priceActionButton is null) return;
        var adding = string.IsNullOrWhiteSpace(_selectedPriceId);
        SetPriceModeButton(_priceNewButton, adding);
        SetPriceModeButton(_priceSaveButton, !adding);
        _priceActionButton.Text = adding ? "Ürünü Ekle" : "Ürünü Güncelle";
    }

    private void ApplyPriceStructure()
    {
        var structure = _priceStructure.SelectedItem?.ToString() ?? "Malzeme";
        var wasLoading = _loadingPriceEditor;
        _loadingPriceEditor = true;
        _pricePrintEnabled.Checked = structure.Equals("Baskı", StringComparison.Ordinal);
        _priceServiceEnabled.Checked = false;
        _loadingPriceEditor = wasLoading;
        ConfigurePriceCategory(true);
        UpdateProductServiceFields();
    }

    private static void SetPriceModeButton(Button button, bool active)
    {
        button.BackColor = active ? UiTheme.Teal : Color.White;
        button.ForeColor = active ? Color.White : UiTheme.Navy;
        button.FlatAppearance.BorderSize = active ? 0 : 1;
        button.FlatAppearance.BorderColor = UiTheme.Line;
    }

    private TabPage BuildCalculatorTab()
    {
        var tab = NewTab("Fiyat Hesaplama");
        var main = new SplitContainer { Dock = DockStyle.Fill, SplitterDistance = 480, FixedPanel = FixedPanel.Panel1 };
        FixLeftPane(main, 480, 430);
        var left = UiTheme.EditorPanel();
        var form = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, ColumnCount = 2 };
        form.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 42));
        form.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 58));
        form.Controls.Add(UiTheme.Label("Fiyat Hesapla", true), 0, 0);
        form.SetColumnSpan(form.Controls[^1], 2);
        _calcGroup = UiTheme.Combo(); _calcGroup.DropDownWidth = 440; _calcGroup.SelectedIndexChanged += (_, _) => RecalculatePreview(); UiTheme.AddField(form, "Fiyat kategorisi / kâr oranı", _calcGroup, 1);
        _calcDescription = UiTheme.TextBox(); UiTheme.AddField(form, "Açıklama", _calcDescription, 2);
        _calcWidth = UiTheme.Number(100000, 2); UiTheme.AddField(form, "En (cm)", _calcWidth, 3);
        _calcHeight = UiTheme.Number(100000, 2); UiTheme.AddField(form, "Boy (cm)", _calcHeight, 4);
        _calcLength = UiTheme.Number(100000, 3); UiTheme.AddField(form, "Uzunluk (m)", _calcLength, 5);
        _calcMinutes = UiTheme.Number(100000, 2); UiTheme.AddField(form, "Süre (dk)", _calcMinutes, 6);
        _calcQuantity = UiTheme.Number(100000, 2); _calcQuantity.Value = 1; UiTheme.AddField(form, "Adet", _calcQuantity, 7);
        _calcRate = UiTheme.Number(1000, 4); _calcRate.Value = _store.State.Settings.UsdTryRate; UiTheme.AddField(form, "USD/TL", _calcRate, 8);
        _calcAlternative = new CheckBox { Text = "Grup çarpanı yerine alternatif maliyet üstü % kullan", AutoSize = true, Margin = new Padding(3, 10, 3, 4) };
        form.Controls.Add(_calcAlternative, 0, 9); form.SetColumnSpan(_calcAlternative, 2);
        _calcAlternativePercent = UiTheme.Number(10000, 2); _calcAlternativePercent.Enabled = false; UiTheme.AddField(form, "Alternatif %", _calcAlternativePercent, 10);
        _calcAlternative.CheckedChanged += (_, _) => { _calcAlternativePercent.Enabled = _calcAlternative.Checked; RecalculatePreview(); };
        _calcAlternativePercent.ValueChanged += (_, _) => RecalculatePreview();
        left.Controls.Add(form);

        var right = new Panel { Dock = DockStyle.Fill, BackColor = Color.White, Padding = new Padding(18) };
        var splitRight = new SplitContainer { Dock = DockStyle.Fill, Orientation = Orientation.Horizontal, SplitterDistance = 330 };
        var pickPanel = new Panel { Dock = DockStyle.Fill, Padding = new Padding(0, 0, 0, 8) };
        var pickTitle = UiTheme.Label("Kullanılacak kalemleri seçin", true); pickTitle.Dock = DockStyle.Top;
        _calcItems = new CheckedListBox { Dock = DockStyle.Fill, Font = new Font("Segoe UI", 10f), CheckOnClick = true, BorderStyle = BorderStyle.FixedSingle };
        _calcItems.ItemCheck += (_, _) => { if (IsHandleCreated) BeginInvoke((Action)RecalculatePreview); };
        pickPanel.Controls.Add(_calcItems); pickPanel.Controls.Add(pickTitle);

        var resultPanel = new Panel { Dock = DockStyle.Fill, Padding = new Padding(0, 12, 0, 0) };
        _calcLines = new ListBox { Dock = DockStyle.Fill, Font = new Font("Consolas", 9.5f), BorderStyle = BorderStyle.FixedSingle };
        var totals = new Panel { Dock = DockStyle.Bottom, Height = 90, BackColor = UiTheme.Mint, Padding = new Padding(14, 10, 14, 8) };
        _calcCostLabel = new Label { Text = "Maliyet: 0,00 TL", AutoSize = true, ForeColor = UiTheme.Muted, Font = new Font("Segoe UI Semibold", 10f), Location = new Point(14, 10) };
        _calcSaleLabel = new Label { Text = "Önerilen satış: 0,00 TL", AutoSize = true, ForeColor = UiTheme.Navy, Font = new Font("Segoe UI Semibold", 17f), Location = new Point(14, 37) };
        totals.Controls.AddRange([_calcCostLabel, _calcSaleLabel]);
        resultPanel.Controls.Add(_calcLines); resultPanel.Controls.Add(totals);
        splitRight.Panel1.Controls.Add(pickPanel); splitRight.Panel2.Controls.Add(resultPanel);
        right.Controls.Add(splitRight);

        var actionBar = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 58, Padding = new Padding(8), BackColor = UiTheme.Sand, FlowDirection = FlowDirection.RightToLeft };
        var saveOrder = UiTheme.Button("Siparişe Dönüştür"); saveOrder.Click += async (_, _) => await SaveOrderAsync();
        var calculate = UiTheme.Button("Hesapla", false); calculate.Click += (_, _) => Calculate();
        actionBar.Controls.AddRange([saveOrder, calculate]);
        main.Panel1.Controls.Add(left);
        main.Panel2.Controls.Add(right); main.Panel2.Controls.Add(actionBar);
        tab.Controls.Add(main);
        return tab;
    }

    private TabPage BuildLedgerTab()
    {
        var tab = NewTab("Cari & Tahsilat");
        var top = new Panel { Dock = DockStyle.Top, Height = 92, BackColor = UiTheme.Sand, Padding = new Padding(18, 10, 18, 10) };
        var customerLabel = UiTheme.Label("Müşteri"); customerLabel.Location = new Point(18, 7);
        _ledgerCustomer = UiTheme.Combo(); _ledgerCustomer.Location = new Point(18, 31); _ledgerCustomer.Width = 270; _ledgerCustomer.Dock = DockStyle.None;
        _ledgerCustomer.SelectedIndexChanged += (_, _) => { RefreshLedger(); PopulateLedgerOrderSelectors(); };
        _ledgerDateFilter = new CheckBox { Text = "Tarih aralığı", AutoSize = true, Location = new Point(310, 8) };
        _ledgerFrom = new DateTimePicker { Format = DateTimePickerFormat.Short, Width = 125, Location = new Point(310, 34), Value = DateTime.Today.AddYears(-5), Enabled = false };
        _ledgerTo = new DateTimePicker { Format = DateTimePickerFormat.Short, Width = 125, Location = new Point(445, 34), Value = DateTime.Today, Enabled = false };
        _ledgerDateFilter.CheckedChanged += (_, _) => { _ledgerFrom.Enabled = _ledgerTo.Enabled = _ledgerDateFilter.Checked; RefreshLedger(); };
        _ledgerFrom.ValueChanged += (_, _) => RefreshLedger();
        _ledgerTo.ValueChanged += (_, _) => RefreshLedger();
        _ledgerShowDescription = new CheckBox { Text = "Açıklamayı göster", AutoSize = true, Checked = true, Location = new Point(805, 8) };
        _ledgerShowDescription.CheckedChanged += (_, _) =>
        {
            if (_ledgerGrid.Columns["description"] is DataGridViewColumn descriptionColumn)
                descriptionColumn.Visible = _ledgerShowDescription.Checked;
        };
        var sortLabel = UiTheme.Label("Sıralama"); sortLabel.Location = new Point(590, 7);
        _ledgerSort = UiTheme.Combo(); _ledgerSort.Location = new Point(590, 31); _ledgerSort.Width = 190; _ledgerSort.Dock = DockStyle.None;
        _ledgerSort.Items.AddRange(["Eskiden yeniye", "Yeniden eskiye", "Tutar: Büyükten küçüğe"]); _ledgerSort.SelectedIndex = 0;
        _ledgerSort.SelectedIndexChanged += (_, _) => RefreshLedger();
        _ledgerBalance = new Label { Text = "Bakiye: 0,00 TL", Font = new Font("Segoe UI Semibold", 17f), ForeColor = UiTheme.Navy, AutoSize = true, Location = new Point(815, 31) };
        top.Controls.AddRange([customerLabel, _ledgerCustomer, _ledgerDateFilter, _ledgerFrom, _ledgerTo, sortLabel, _ledgerSort, _ledgerShowDescription, _ledgerBalance]);

        var split = new SplitContainer { Dock = DockStyle.Fill, SplitterDistance = 900, FixedPanel = FixedPanel.Panel2 };
        FixRightPane(split, 390, 560);
        _ledgerGrid = UiTheme.Grid();
        _ledgerGrid.ReadOnly = false;
        AddGridColumn(_ledgerGrid, "id", "Kimlik", false);
        AddGridColumn(_ledgerGrid, "kind", "Tür", false);
        AddGridColumn(_ledgerGrid, "date", "Tarih", true, 90);
        AddGridColumn(_ledgerGrid, "type", "Hareket", true, 80);
        AddGridColumn(_ledgerGrid, "description", "Açıklama", true, 210);
        AddGridColumn(_ledgerGrid, "material", "Malzeme", true, 150);
        AddGridColumn(_ledgerGrid, "measure", "Ölçü", true, 120);
        AddGridColumn(_ledgerGrid, "debit", "Borç", true, 90, "N2");
        AddGridColumn(_ledgerGrid, "credit", "Tahsilat", true, 90, "N2");
        AddGridColumn(_ledgerGrid, "balance", "Bakiye", true, 90, "N2");
        foreach (var name in new[] { "id", "kind", "type" })
            if (_ledgerGrid.Columns[name] is DataGridViewColumn column) column.ReadOnly = true;
        _ledgerGrid.CellBeginEdit += LedgerGrid_CellBeginEdit;
        _ledgerGrid.EditingControlShowing += LedgerGrid_EditingControlShowing;
        _ledgerGrid.CellEndEdit += (_, e) =>
        {
            var rowIndex = e.RowIndex;
            var columnIndex = e.ColumnIndex;
            var original = _ledgerEditOriginal;
            _ledgerEditOriginal = null;
            if (original is { } value && value.RowIndex == rowIndex && value.ColumnIndex == columnIndex &&
                LedgerCellText(_ledgerGrid.Rows[rowIndex].Cells[columnIndex].Value) == value.Value) return;
            BeginInvoke(async () => await SaveLedgerEditAsync(rowIndex, columnIndex));
        };
        var ledgerActions = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 52, Padding = new Padding(4, 6, 4, 4), BackColor = UiTheme.Sand, FlowDirection = FlowDirection.RightToLeft };
        var deleteMovement = UiTheme.Button("Seçili Hareketi Sil", false); deleteMovement.Click += async (_, _) => await DeleteSelectedLedgerMovementAsync();
        ledgerActions.Controls.Add(deleteMovement);
        ledgerActions.Controls.Add(new Label { Text = "Tarih, açıklama, malzeme ve ölçü hücrelerini doğrudan değiştirebilirsiniz.", AutoSize = true, ForeColor = UiTheme.Muted, Margin = new Padding(8, 10, 12, 0) });
        split.Panel1.Padding = new Padding(12);
        split.Panel1.Controls.Add(_ledgerGrid);
        split.Panel1.Controls.Add(ledgerActions);

        var rightTabs = new TabControl { Dock = DockStyle.Fill, Font = new Font("Segoe UI Semibold", 9.5f) };
        var paymentTab = NewTab("Tahsilat");
        var paymentPanel = UiTheme.EditorPanel();
        var form = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, ColumnCount = 1 };
        form.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        form.Controls.Add(UiTheme.Label("Tahsilat Ekle", true));
        _paymentAmount = UiTheme.Number(100000000, 2); AddStackField(form, "Tutar TL", _paymentAmount);
        _paymentType = UiTheme.Combo(); _paymentType.Items.AddRange(["Nakit", "Havale / EFT", "Kredi Kartı", "Çek", "Diğer"]); _paymentType.SelectedIndex = 0; AddStackField(form, "Ödeme Tipi", _paymentType);
        _paymentDescription = UiTheme.TextBox(true); _paymentDescription.Text = "Tahsilat"; AddStackField(form, "Açıklama", _paymentDescription);
        var pay = UiTheme.Button("Tahsilatı Kaydet"); pay.Click += async (_, _) => await SavePaymentAsync();
        form.Controls.Add(pay);
        var customerNote = UiTheme.Button("Müşteriye Not Yolla", false); customerNote.Click += (_, _) => CreateCustomerNote();
        customerNote.Margin = new Padding(3, 10, 3, 3);
        form.Controls.Add(customerNote);
        var customerPdf = UiTheme.Button("Müşteri Hesabını PDF Al", false); customerPdf.Click += (_, _) => CreateCustomerNote();
        form.Controls.Add(customerPdf);
        var customerExcel = UiTheme.Button("Müşteri Hesabını Excel Al", false); customerExcel.Click += (_, _) => ExportCustomerLedgerExcel();
        form.Controls.Add(customerExcel);
        paymentPanel.Controls.Add(form);
        paymentTab.Controls.Add(paymentPanel);

        var orderTab = NewTab("Sipariş Ekle");
        var orderPanel = UiTheme.EditorPanel();
        var orderForm = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, ColumnCount = 1 };
        orderForm.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        orderForm.Controls.Add(UiTheme.Label("Cariye Sipariş Ekle", true));
        _ledgerOrderDate = new DateTimePicker { Format = DateTimePickerFormat.Short, Height = 30, Dock = DockStyle.Top, Value = DateTime.Today }; AddStackField(orderForm, "Tarih", _ledgerOrderDate);
        _ledgerOrderMaterial = UiTheme.Combo(); _ledgerOrderMaterial.DropDownWidth = 520; AddStackField(orderForm, "Malzeme / Baskı / İşlem *", _ledgerOrderMaterial);
        _ledgerOrderDescription = UiTheme.TextBox(); AddStackField(orderForm, "Açıklama", _ledgerOrderDescription);
        _ledgerOrderWidth = UiTheme.Number(100000, 2); AddStackField(orderForm, "En (cm)", _ledgerOrderWidth);
        _ledgerOrderHeight = UiTheme.Number(100000, 2); AddStackField(orderForm, "Boy (cm)", _ledgerOrderHeight);
        _ledgerOrderLength = UiTheme.Number(100000, 3); AddStackField(orderForm, "Uzunluk (m)", _ledgerOrderLength);
        _ledgerOrderQuantity = UiTheme.Number(100000, 2); _ledgerOrderQuantity.Value = 1; AddStackField(orderForm, "Adet", _ledgerOrderQuantity);
        _ledgerOrderPreview = new Label { Text = "Toplam: 0,00 TL", AutoSize = true, Font = new Font("Segoe UI Semibold", 13f), ForeColor = UiTheme.Navy, Margin = new Padding(3, 12, 3, 6) }; orderForm.Controls.Add(_ledgerOrderPreview);
        var orderButtons = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true };
        var addOrder = UiTheme.Button("Siparişi Cariye Ekle"); addOrder.Click += async (_, _) => await SaveLedgerOrderAsync();
        var goMaterials = UiTheme.Button("Malzeme Tanımlarına Git", false); goMaterials.Click += (_, _) => _tabs.SelectedIndex = 2;
        orderButtons.Controls.AddRange([addOrder, goMaterials]); orderForm.Controls.Add(orderButtons);
        foreach (var input in new Control[] { _ledgerOrderMaterial, _ledgerOrderWidth, _ledgerOrderHeight, _ledgerOrderLength, _ledgerOrderQuantity })
        {
            if (input is ComboBox combo) combo.SelectedIndexChanged += (_, _) => UpdateLedgerOrderPreview();
            if (input is NumericUpDown number) number.ValueChanged += (_, _) => UpdateLedgerOrderPreview();
        }
        orderPanel.Controls.Add(orderForm); orderTab.Controls.Add(orderPanel);

        var excelTab = NewTab("Excel Ekle");
        var excelPanel = UiTheme.EditorPanel();
        var excelForm = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, ColumnCount = 1 };
        excelForm.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        excelForm.Controls.Add(UiTheme.Label("Excel'den Cariye Ekle", true));
        excelForm.Controls.Add(new Label
        {
            Text = "Excel dosyasındaki yeni müşteri, sipariş ve tahsilat satırları mevcut cari tablosuna eklenir. Önceki kayıtlar silinmez; aynı kayıt ikinci kez eklenmez.",
            AutoSize = true, MaximumSize = new Size(320, 0), ForeColor = UiTheme.Muted, Margin = new Padding(3, 6, 3, 14)
        });
        var addExcel = UiTheme.Button("Excel Dosyası Seç ve Ekle"); addExcel.Click += async (_, _) => await ImportExcelAsync(true);
        excelForm.Controls.Add(addExcel);
        excelPanel.Controls.Add(excelForm); excelTab.Controls.Add(excelPanel);

        rightTabs.TabPages.Add(paymentTab); rightTabs.TabPages.Add(orderTab); rightTabs.TabPages.Add(excelTab);
        split.Panel2.Controls.Add(rightTabs);
        tab.Controls.Add(split);
        tab.Controls.Add(top);
        return tab;
    }

    private TabPage BuildProfitSettingsTab()
    {
        var tab = NewTab("Kâr Ayarları");
        var split = new SplitContainer { Dock = DockStyle.Fill, SplitterDistance = 420, FixedPanel = FixedPanel.Panel1 };
        FixLeftPane(split, 420, 380);
        var editor = UiTheme.EditorPanel();
        var form = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, ColumnCount = 1 };
        form.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        form.Controls.Add(UiTheme.Label("Müşteri Kategorisi Kâr Oranları", true));
        form.Controls.Add(new Label
        {
            Text = "Reklamcı / fason, sürekli müşteri, çevre esnafı ve perakende oranlarını buradan değiştirin. Yeni oran sonraki hesaplamalara anında uygulanır.",
            AutoSize = true, MaximumSize = new Size(350, 0), ForeColor = UiTheme.Muted, Margin = new Padding(3, 5, 3, 14)
        });
        _groupName = UiTheme.TextBox(); AddStackField(form, "Kategori adı", _groupName);
        _groupProfitPercent = UiTheme.Number(10000, 2); AddStackField(form, "Alış maliyeti üstüne kâr (%)", _groupProfitPercent);
        _groupProfitPercent.ValueChanged += (_, _) => UpdateGroupExample();
        _groupExample = new Label { AutoSize = true, BackColor = UiTheme.Mint, ForeColor = UiTheme.Navy, Font = new Font("Segoe UI Semibold", 10f), Padding = new Padding(12), Margin = new Padding(3, 12, 3, 12) };
        form.Controls.Add(_groupExample);
        var saveGroup = UiTheme.Button("Kâr Oranını Kaydet"); saveGroup.Click += async (_, _) => await SavePriceGroupAsync();
        form.Controls.Add(saveGroup);
        form.Controls.Add(new Label
        {
            Text = "Malzemeye / Ürüne Özel Kâr",
            AutoSize = true,
            Font = new Font("Segoe UI Semibold", 11f),
            ForeColor = UiTheme.Navy,
            Margin = new Padding(3, 28, 3, 4)
        });
        form.Controls.Add(new Label
        {
            Text = "Ürünü ve müşteri kategorisini seçin. Özel yüzde yalnız seçilen ürün + müşteri kategorisi için geçerlidir; diğer kategoriler standart oranlarını kullanır. Alış maliyeti değişmez.",
            AutoSize = true,
            MaximumSize = new Size(350, 0),
            ForeColor = UiTheme.Muted,
            Margin = new Padding(3, 4, 3, 12)
        });
        _profitPriceItem = UiTheme.Combo();
        _profitPriceItem.SelectedIndexChanged += (_, _) => LoadProfitPriceItem();
        AddStackField(form, "Malzeme / ürün", _profitPriceItem);
        _profitItemGroup = UiTheme.Combo();
        _profitItemGroup.SelectedIndexChanged += (_, _) => LoadProfitPriceItemGroupOverride();
        AddStackField(form, "Müşteri kategorisi", _profitItemGroup);
        _profitUseSpecial = new CheckBox
        {
            Text = "Bu ürün ve müşteri kategorisinde özel kâr kullan",
            AutoSize = true,
            Font = new Font("Segoe UI Semibold", 9.5f),
            ForeColor = UiTheme.Navy,
            Margin = new Padding(3, 10, 3, 5)
        };
        _profitUseSpecial.CheckedChanged += (_, _) =>
        {
            _profitSpecialPercent.Enabled = _profitUseSpecial.Checked;
            RefreshProfitPriceItemStatus();
        };
        form.Controls.Add(_profitUseSpecial);
        _profitSpecialPercent = UiTheme.Number(10000, 2);
        _profitSpecialPercent.ValueChanged += (_, _) => RefreshProfitPriceItemStatus();
        AddStackField(form, "Seçilen kategoriye özel kâr (%)", _profitSpecialPercent);
        _profitPriceItemStatus = new Label
        {
            AutoSize = true,
            MaximumSize = new Size(350, 0),
            ForeColor = UiTheme.Teal,
            Font = new Font("Segoe UI Semibold", 9.5f),
            Margin = new Padding(3, 8, 3, 8)
        };
        form.Controls.Add(_profitPriceItemStatus);
        var saveItemProfit = UiTheme.Button("Ürün Kâr Ayarını Kaydet", false);
        saveItemProfit.Click += async (_, _) => await SaveProfitPriceItemAsync();
        form.Controls.Add(saveItemProfit);
        editor.Controls.Add(form);

        _groupGrid = UiTheme.Grid();
        _groupGrid.ReadOnly = false;
        AddGridColumn(_groupGrid, "id", "Kimlik", false);
        AddGridColumn(_groupGrid, "name", "Müşteri Kategorisi", true, 160);
        AddGridColumn(_groupGrid, "profit", "Kâr %", true, 80, "N2");
        AddGridColumn(_groupGrid, "example", "100 TL Alışın Satışı", true, 110, "N2");
        foreach (var name in new[] { "id", "example" })
            if (_groupGrid.Columns[name] is DataGridViewColumn column) column.ReadOnly = true;
        _groupGrid.CellBeginEdit += InlineGrid_CellBeginEdit;
        _groupGrid.CellEndEdit += async (_, e) => await SavePriceGroupGridEditAsync(e);
        _groupGrid.SelectionChanged += (_, _) => LoadSelectedPriceGroup();
        split.Panel1.Controls.Add(editor);
        split.Panel2.Padding = new Padding(12); split.Panel2.Controls.Add(_groupGrid);
        tab.Controls.Add(split);
        return tab;
    }

    private TabPage BuildSyncTab()
    {
        var tab = NewTab("Senkron & Yedek");
        var split = new SplitContainer { Dock = DockStyle.Fill, SplitterDistance = 650 };
        var settings = UiTheme.EditorPanel();
        var form = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, ColumnCount = 1 };
        form.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        form.Controls.Add(UiTheme.Label("Google Sheets Bağlantısı", true));
        var info = new Label { Text = "BTakip için oluşturulan ayrı Google Apps Script web uygulaması adresini ve güvenlik anahtarını girin. Mevcut tablolarınıza dokunulmaz.", AutoSize = true, MaximumSize = new Size(580, 0), ForeColor = UiTheme.Muted, Margin = new Padding(3, 4, 3, 12) };
        form.Controls.Add(info);
        _syncUrl = UiTheme.TextBox(); AddStackField(form, "Web uygulaması adresi", _syncUrl);
        _syncToken = UiTheme.TextBox(); _syncToken.UseSystemPasswordChar = true; AddStackField(form, "Senkron anahtarı", _syncToken);
        _syncInterval = UiTheme.Number(3600, 0); _syncInterval.Minimum = 15; AddStackField(form, "Kontrol aralığı (saniye)", _syncInterval);
        _usdRate = UiTheme.Number(1000, 4); AddStackField(form, "USD/TL kuru", _usdRate);
        _autoRate = new CheckBox { Text = "Kuru TCMB'den otomatik güncelle", AutoSize = true, Margin = new Padding(3, 10, 3, 4) }; form.Controls.Add(_autoRate);
        _startWindows = new CheckBox { Text = "Windows açılışında BTakip'i başlat", AutoSize = true, Margin = new Padding(3, 5, 3, 10) }; form.Controls.Add(_startWindows);
        var buttons = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Top };
        var save = UiTheme.Button("Ayarları Kaydet"); save.Click += async (_, _) => await SaveSettingsAsync();
        var sync = UiTheme.Button("Şimdi Eşitle", false); sync.Click += async (_, _) => await RunSyncAsync(true);
        var rate = UiTheme.Button("Kuru Güncelle", false); rate.Click += async (_, _) => await RefreshExchangeRateAsync(true);
        buttons.Controls.AddRange([save, sync, rate]);
        form.Controls.Add(buttons);
        _syncStatus = new Label { AutoSize = true, MaximumSize = new Size(580, 0), ForeColor = UiTheme.Navy, Font = new Font("Segoe UI Semibold", 10f), Margin = new Padding(3, 14, 3, 3) };
        form.Controls.Add(_syncStatus);
        _securityStatus = new Label { AutoSize = true, MaximumSize = new Size(580, 0), ForeColor = UiTheme.Teal, Font = new Font("Segoe UI Semibold", 9.5f), Margin = new Padding(3, 10, 3, 3) };
        form.Controls.Add(_securityStatus);
        settings.Controls.Add(form);

        var backup = UiTheme.EditorPanel();
        backup.BackColor = Color.White;
        var backupForm = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, ColumnCount = 1 };
        backupForm.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        var backupTitle = UiTheme.Label("Yerel Yedek ve Excel", true);
        var backupText = new Label
        {
            Text = $"Her kayıt sonrası veri ve Excel yedeği otomatik oluşturulur. Başka bilgisayara geçmek için tek dosyalık tam yedeği kullanın.\n\nKlasör:\n{_store.RootPath}",
            AutoSize = true, MaximumSize = new Size(520, 0), ForeColor = UiTheme.Ink, Font = new Font("Segoe UI", 10f), Margin = new Padding(3, 6, 3, 14)
        };
        var actions = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true, WrapContents = true, Margin = new Padding(0, 0, 0, 14) };
        var open = UiTheme.Button("Yedek Klasörünü Aç", false); open.Click += (_, _) => OpenPath(_store.RootPath);
        var export = UiTheme.Button("Tüm Hesapları Excel Al", true); export.Click += (_, _) => ExportExcel();
        var exportPdf = UiTheme.Button("Tüm Hesapları PDF Al", false); exportPdf.Click += (_, _) => ExportAllCustomerAccountsPdf();
        var import = UiTheme.Button("Excel'den İçe Aktar", false); import.Click += async (_, _) => await ImportExcelAsync();
        var fullBackup = UiTheme.Button("Tam Yedek Oluştur", true); fullBackup.Click += async (_, _) => await CreateFullBackupAsync();
        var restoreBackup = UiTheme.Button("Tam Yedek Yükle", false); restoreBackup.Click += async (_, _) => await RestoreFullBackupAsync();
        actions.Controls.AddRange([fullBackup, restoreBackup, exportPdf, export, import, open]);
        var safety = new Label
        {
            Text = "Veri ve yazılım güvenliği\nİçe aktarma kaynak Excel dosyasını değiştirmez. Silinenler eşitleme güvenliği için yumuşak silme olarak saklanır. Her JSON ve Excel yedeği SHA-256 ile doğrulanır; ana kayıt bozulursa son sağlam yedek otomatik kurtarılır. Uygulama dosyasının bütünlüğü de açılışta kontrol edilir.",
            AutoSize = true, MaximumSize = new Size(520, 0), ForeColor = UiTheme.Navy, BackColor = UiTheme.Mint, Padding = new Padding(16), Font = new Font("Segoe UI", 9.8f), Margin = new Padding(3, 8, 3, 3)
        };
        backup.Resize += (_, _) =>
        {
            var width = Math.Max(280, backup.ClientSize.Width - 42);
            backupText.MaximumSize = new Size(width, 0); safety.MaximumSize = new Size(width, 0); actions.MaximumSize = new Size(width, 0);
        };
        backupForm.Controls.Add(backupTitle); backupForm.Controls.Add(backupText); backupForm.Controls.Add(actions); backupForm.Controls.Add(safety);
        backup.Controls.Add(backupForm);
        split.Panel1.Controls.Add(settings); split.Panel2.Controls.Add(backup);
        tab.Controls.Add(split);
        return tab;
    }

    private void RefreshAll()
    {
        PopulateCustomerCombos();
        PopulateProfitPriceItems();
        PopulatePriceBaseMaterials();
        PopulateLedgerOrderSelectors();
        RefreshCustomerGrid();
        RefreshPriceGrid();
        RefreshPriceGroupGrid();
        RefreshCalcItems();
        RefreshLedger();
        RefreshDashboard();
        LoadSettingsControls();
    }

    private void PopulateProfitPriceItems()
    {
        if (_profitPriceItem is null) return;
        var selectedId = (_profitPriceItem.SelectedItem as PriceItem)?.Id;
        _profitPriceItem.DataSource = _store.State.PriceItems
            .Where(x => !x.Deleted)
            .OrderBy(x => x.Category)
            .ThenBy(x => x.Name)
            .ThenBy(x => x.Variant)
            .ToList();
        _profitPriceItem.DisplayMember = nameof(PriceItem.DisplayName);
        _profitPriceItem.ValueMember = nameof(PriceItem.Id);
        if (selectedId is not null) _profitPriceItem.SelectedValue = selectedId;
        LoadProfitPriceItem();
    }

    private void PopulatePriceBaseMaterials()
    {
        if (_priceBaseMaterial is null) return;
        var selectedId = (_priceBaseMaterial.SelectedItem as PriceItem)?.Id;
        var materials = new List<PriceItem> { new() { Id = "", Name = "Malzeme seçilmedi" } };
        materials.AddRange(_store.State.PriceItems
            .Where(x => !x.Deleted && x.Active && !x.IsPrintProduct && x.Category != "Hizmet" && x.Id != _selectedPriceId)
            .OrderBy(x => x.Name).ThenBy(x => x.Variant));
        _priceBaseMaterial.DataSource = materials;
        _priceBaseMaterial.DisplayMember = nameof(PriceItem.DisplayName);
        _priceBaseMaterial.ValueMember = nameof(PriceItem.Id);
        _priceBaseMaterial.SelectedValue = selectedId ?? "";
    }

    private void LoadProfitPriceItem()
    {
        var item = _profitPriceItem?.SelectedItem as PriceItem;
        if (item is null) { RefreshProfitPriceItemStatus(); return; }
        if (_profitItemGroup is not null) _profitItemGroup.SelectedValue = item.PriceGroupId;
        LoadProfitPriceItemGroupOverride();
    }

    private void LoadProfitPriceItemGroupOverride()
    {
        var item = _profitPriceItem?.SelectedItem as PriceItem;
        var group = _profitItemGroup?.SelectedItem as PriceGroup;
        if (item is null || group is null) { RefreshProfitPriceItemStatus(); return; }
        var specialPercent = PricingEngine.GetSpecialProfitPercent(item, group.Id);
        if (_profitUseSpecial is not null) _profitUseSpecial.Checked = specialPercent.HasValue;
        if (_profitSpecialPercent is not null)
        {
            var standardPercent = (group.CostMultiplier - 1m) * 100m;
            _profitSpecialPercent.Value = Clamp(_profitSpecialPercent, specialPercent ?? standardPercent);
            _profitSpecialPercent.Enabled = specialPercent.HasValue;
        }
        RefreshProfitPriceItemStatus();
    }

    private void RefreshProfitPriceItemStatus()
    {
        if (_profitPriceItemStatus is null) return;
        var item = _profitPriceItem?.SelectedItem as PriceItem;
        var group = _profitItemGroup?.SelectedItem as PriceGroup;
        if (item is null || group is null) { _profitPriceItemStatus.Text = "Ürün seçilmedi."; return; }
        var standardPercent = (group.CostMultiplier - 1m) * 100m;
        _profitPriceItemStatus.Text = _profitUseSpecial?.Checked == true
            ? $"{group.Name} için özel %{_profitSpecialPercent.Value:0.##} uygulanacak; diğer müşteri kategorileri değişmeyecek."
            : $"Bu üründe {group.Name} standart kârı %{standardPercent:0.##} uygulanacak.";
    }

    private async Task SaveProfitPriceItemAsync()
    {
        var item = _profitPriceItem?.SelectedItem as PriceItem;
        var group = _profitItemGroup?.SelectedItem as PriceGroup;
        if (item is null || group is null) return;
        _store.CaptureUndo(item.DisplayName + " ürün kâr ayarı değiştirildi");
        item.GroupProfitPercentOverrides ??= [];
        if (item.SpecialProfitPercent is decimal legacyPercent)
        {
            item.GroupProfitPercentOverrides.TryAdd(item.PriceGroupId, legacyPercent);
            item.SpecialProfitPercent = null;
        }
        if (_profitUseSpecial.Checked) item.GroupProfitPercentOverrides[group.Id] = _profitSpecialPercent.Value;
        else item.GroupProfitPercentOverrides.Remove(group.Id);
        _store.Touch(item);
        await PersistAndSyncAsync($"Ürün kâr ayarı güncellendi: {item.DisplayName} / {group.Name}");
        RefreshAll();
    }

    private void RefreshDashboard()
    {
        _dashboardCustomer.Text = _store.State.Customers.Count(x => !x.Deleted).ToString("N0");
        _dashboardOrders.Text = _store.State.Orders.Count(x => !x.Deleted).ToString("N0");
        var balance = _store.State.Orders.Where(x => !x.Deleted).Sum(x => x.SaleTotalTl) - _store.State.Payments.Where(x => !x.Deleted).Sum(x => x.AmountTl);
        _dashboardBalance.Text = balance.ToString("N2") + " TL";
        _dashboardBackup.Text = File.Exists(_store.LatestWorkbook) ? File.GetLastWriteTime(_store.LatestWorkbook).ToString("HH:mm:ss") : "—";
        if (_undoButton is not null)
        {
            _undoButton.Enabled = _store.CanUndo;
            _undoButton.Text = _store.CanUndo ? "Geri Al" : "Geri Al";
        }
    }

    private void PopulateCustomerCombos()
    {
        var customers = _store.State.Customers.Where(x => !x.Deleted).OrderBy(x => x.Name).ToList();
        var calcGroupId = (_calcGroup?.SelectedItem as PriceGroup)?.Id;
        var ledgerId = (_ledgerCustomer?.SelectedItem as Customer)?.Id;

        if (_customerGroup is not null)
        {
            var groupId = (_customerGroup.SelectedItem as PriceGroup)?.Id;
            _customerGroup.DataSource = _store.State.PriceGroups.Where(x => !x.Deleted).OrderBy(x => x.CostMultiplier).ToList();
            _customerGroup.DisplayMember = nameof(PriceGroup.Name);
            _customerGroup.ValueMember = nameof(PriceGroup.Id);
            if (groupId is not null) _customerGroup.SelectedValue = groupId;
        }
        if (_priceGroup is not null)
        {
            var groupId = (_priceGroup.SelectedItem as PriceGroup)?.Id;
            _priceGroup.DataSource = _store.State.PriceGroups.Where(x => !x.Deleted).OrderBy(x => x.CostMultiplier).ToList();
            _priceGroup.DisplayMember = nameof(PriceGroup.Name);
            _priceGroup.ValueMember = nameof(PriceGroup.Id);
            _priceGroup.SelectedValue = groupId ?? "retail";
        }
        if (_profitItemGroup is not null)
        {
            var groupId = (_profitItemGroup.SelectedItem as PriceGroup)?.Id;
            _profitItemGroup.DataSource = _store.State.PriceGroups.Where(x => !x.Deleted).OrderBy(x => x.CostMultiplier).ToList();
            _profitItemGroup.DisplayMember = nameof(PriceGroup.Name);
            _profitItemGroup.ValueMember = nameof(PriceGroup.Id);
            _profitItemGroup.SelectedValue = groupId ?? "retail";
        }
        if (_calcGroup is not null)
        {
            _calcGroup.DataSource = _store.State.PriceGroups.Where(x => !x.Deleted).OrderBy(x => x.CostMultiplier).ToList();
            _calcGroup.DisplayMember = nameof(PriceGroup.CalculatorLabel);
            _calcGroup.ValueMember = nameof(PriceGroup.Id);
            _calcGroup.SelectedValue = calcGroupId ?? "retail";
        }
        if (_ledgerCustomer is not null)
        {
            _ledgerCustomer.DataSource = customers.ToList();
            _ledgerCustomer.DisplayMember = nameof(Customer.Name);
            _ledgerCustomer.ValueMember = nameof(Customer.Id);
            if (ledgerId is not null) _ledgerCustomer.SelectedValue = ledgerId;
        }
    }

    private void RefreshCustomerGrid()
    {
        if (_customerGrid is null) return;
        _customerGrid.Rows.Clear();
        var customers = _store.State.Customers.Where(x => !x.Deleted).ToList();
        IEnumerable<Customer> ordered = _customerSort?.SelectedIndex switch
        {
            1 => customers.OrderByDescending(x => x.Name),
            2 => customers.OrderByDescending(x => _store.GetBalance(x.Id)).ThenBy(x => x.Name),
            3 => customers.OrderBy(x => _store.GetBalance(x.Id)).ThenBy(x => x.Name),
            4 => customers.OrderByDescending(x => x.UpdatedAtUtc),
            _ => customers.OrderBy(x => x.Name)
        };
        foreach (var customer in ordered)
        {
            var group = _store.State.PriceGroups.FirstOrDefault(x => x.Id == customer.PriceGroupId)?.Name ?? "";
            _customerGrid.Rows.Add(customer.Id, customer.Name, customer.Company, group, customer.Phone, _store.GetBalance(customer.Id));
        }
    }

    private void LoadSelectedCustomer()
    {
        if (_customerGrid.SelectedRows.Count == 0) return;
        var id = _customerGrid.SelectedRows[0].Cells["id"].Value?.ToString();
        var customer = _store.State.Customers.FirstOrDefault(x => x.Id == id);
        if (customer is null) return;
        _selectedCustomerId = customer.Id;
        _customerName.Text = customer.Name;
        _customerCompany.Text = customer.Company;
        _customerPhone.Text = customer.Phone;
        _customerEmail.Text = customer.Email;
        _customerNotes.Text = customer.Notes;
        _customerGroup.SelectedValue = customer.PriceGroupId;
    }

    private void ClearCustomerEditor()
    {
        _selectedCustomerId = null;
        _customerName.Clear(); _customerCompany.Clear(); _customerPhone.Clear(); _customerEmail.Clear(); _customerNotes.Clear();
        if (_customerGroup.Items.Count > 0) _customerGroup.SelectedValue = "retail";
        _customerGrid.ClearSelection();
    }

    private void OpenCustomerLedgerFromGrid(int rowIndex)
    {
        var id = _customerGrid.Rows[rowIndex].Cells["id"].Value?.ToString();
        if (string.IsNullOrWhiteSpace(id)) return;
        _tabs.SelectedIndex = 4;
        _ledgerCustomer.SelectedValue = id;
        RefreshLedger();
    }

    private async Task SaveCustomerAsync()
    {
        var name = _customerName.Text.Trim();
        if (name.Length == 0) { MessageBox.Show("Müşteri adı zorunludur.", "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
        var customer = _store.State.Customers.FirstOrDefault(x => x.Id == _selectedCustomerId) ?? new Customer { DeviceId = _store.State.DeviceId, Revision = 0 };
        _store.CaptureUndo(customer.Revision == 0 ? "Yeni müşteri eklendi" : $"{customer.Name} müşteri kartı değiştirildi");
        customer.Name = name;
        customer.Company = _customerCompany.Text.Trim();
        customer.Phone = _customerPhone.Text.Trim();
        customer.Email = _customerEmail.Text.Trim();
        customer.Notes = _customerNotes.Text.Trim();
        customer.PriceGroupId = (_customerGroup.SelectedItem as PriceGroup)?.Id ?? "retail";
        _store.Touch(customer);
        if (!_store.State.Customers.Contains(customer)) _store.State.Customers.Add(customer);
        _selectedCustomerId = customer.Id;
        await PersistAndSyncAsync("Müşteri kaydı: " + customer.Name);
        RefreshAll();
    }

    private async Task DeleteCustomerAsync()
    {
        var customer = _store.State.Customers.FirstOrDefault(x => x.Id == _selectedCustomerId);
        if (customer is null) return;
        if (MessageBox.Show($"{customer.Name} BTakip içinde silinmiş olarak işaretlensin mi? Geçmiş hareketler korunur.", "Müşteri Sil", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
        _store.CaptureUndo(customer.Name + " müşteri kartı silindi");
        customer.Deleted = true; _store.Touch(customer);
        await PersistAndSyncAsync("Müşteri silindi: " + customer.Name);
        ClearCustomerEditor(); RefreshAll();
    }

    private void RefreshPriceGrid()
    {
        if (_priceGrid is null) return;
        var selectedGroup = _priceGroup?.SelectedItem as PriceGroup
            ?? _store.State.PriceGroups.FirstOrDefault(x => !x.Deleted && x.Id == "retail")
            ?? _store.State.PriceGroups.First(x => !x.Deleted);
        if (_priceGrid.Columns["specialProfit"] is DataGridViewColumn profitColumn)
            profitColumn.HeaderText = $"Satış Kârı — {selectedGroup.Name}";
        var selectedItemId = _selectedPriceId;
        _changingPriceSelection = true;
        _priceGrid.Rows.Clear();
        foreach (var item in _store.State.PriceItems.Where(x => !x.Deleted).OrderBy(x => x.Name).ThenBy(x => x.Variant))
        {
            var structure = item.Category.Equals("Hizmet", StringComparison.OrdinalIgnoreCase)
                ? "Hizmet"
                : item.IsPrintProduct ? "Baskı" : "Malzeme";
            _priceGrid.Rows.Add(item.Id, structure, item.Name, item.Variant, item.Unit, item.Currency, item.UnitCost,
                PriceItemUnitSale(item, selectedGroup), PricingFormula.Labels.GetValueOrDefault(item.Formula, item.Formula), PriceOverrideSummary(item, selectedGroup));
        }
        SelectPriceGridRow(selectedItemId);
        _changingPriceSelection = false;
    }

    private static decimal PriceItemUnitSale(PriceItem item, PriceGroup group)
    {
        var multiplier = PricingEngine.ResolveMultiplier(item, group.Id, group.CostMultiplier);
        return decimal.Round(item.UnitCost * multiplier, 4);
    }

    private void RefreshPriceGroupGrid()
    {
        if (_groupGrid is null) return;
        _groupGrid.Rows.Clear();
        foreach (var group in _store.State.PriceGroups.Where(x => !x.Deleted).OrderBy(x => x.CostMultiplier))
        {
            var profit = (group.CostMultiplier - 1m) * 100m;
            _groupGrid.Rows.Add(group.Id, group.Name, profit, group.CostMultiplier * 100m);
        }
    }

    private void LoadSelectedPriceGroup()
    {
        if (_groupGrid?.SelectedRows.Count != 1) return;
        var id = _groupGrid.SelectedRows[0].Cells["id"].Value?.ToString();
        var group = _store.State.PriceGroups.FirstOrDefault(x => x.Id == id && !x.Deleted);
        if (group is null) return;
        _selectedGroupId = group.Id;
        _groupName.Text = group.Name;
        _groupProfitPercent.Value = Clamp(_groupProfitPercent, (group.CostMultiplier - 1m) * 100m);
        UpdateGroupExample();
    }

    private void UpdateGroupExample()
    {
        if (_groupExample is null) return;
        var sale = 100m * (1m + _groupProfitPercent.Value / 100m);
        _groupExample.Text = $"Örnek: 100,00 TL alış maliyeti → {sale:N2} TL satış";
    }

    private async Task SavePriceGroupAsync()
    {
        var group = _store.State.PriceGroups.FirstOrDefault(x => x.Id == _selectedGroupId && !x.Deleted);
        if (group is null) { MessageBox.Show("Güncellenecek kategoriyi tablodan seçin.", "Kâr Ayarları", MessageBoxButtons.OK, MessageBoxIcon.Information); return; }
        if (string.IsNullOrWhiteSpace(_groupName.Text)) { MessageBox.Show("Kategori adı boş olamaz.", "Kâr Ayarları", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
        _store.CaptureUndo(group.Name + " kâr oranı değiştirildi");
        group.Name = _groupName.Text.Trim();
        group.CostMultiplier = 1m + _groupProfitPercent.Value / 100m;
        _store.Touch(group);
        await PersistAndSyncAsync("Kâr oranı güncellendi: " + group.Name);
        RefreshAll();
    }

    private void ConfigurePriceCategory(bool resetFormula)
    {
        if (_priceCategory is null || _priceFormula is null) return;
        var isServiceOnly = (_priceStructure.SelectedItem?.ToString() ?? "").Equals("Hizmet", StringComparison.Ordinal);
        var isPrint = (_priceStructure.SelectedItem?.ToString() ?? "").Equals("Baskı", StringComparison.Ordinal);
        _priceName.PlaceholderText = isServiceOnly ? "Örn: Sıvama, Lazer Kesim, Montaj" : isPrint ? "Örn: Folyo Baskı, Branda Baskı, UV Baskı" : "Örn: Dekota, Pleksi, Folyo";
        _priceNameLabel.Text = isServiceOnly ? "Hizmet adı *" : "Ürün / malzeme adı *";
        _priceVariantLabel.Text = isServiceOnly ? "Açıklama / not" : isPrint ? "Baskı kalitesi / renk / açıklama" : "Renk / yüzey / açıklama";
        _priceFormulaLabel.Text = isServiceOnly ? "Hizmet hesabı" : "Malzeme / baskı ölçüsü";

        var formulas = (isServiceOnly
            ? new[] { PricingFormula.SquareMeter, PricingFormula.Minute, PricingFormula.Hour, PricingFormula.Piece, PricingFormula.Fixed, PricingFormula.PercentMaterial }
            : isPrint
            ? new[] { PricingFormula.SquareMeter, PricingFormula.Meter, PricingFormula.Piece, PricingFormula.Fixed }
            : new[] { PricingFormula.SquareMeter, PricingFormula.SheetArea, PricingFormula.Meter, PricingFormula.Piece, PricingFormula.Fixed }).ToList();
        var savedFormula = !resetFormula
            ? _store.State.PriceItems.FirstOrDefault(x => x.Id == _selectedPriceId)?.Formula
            : null;
        if (!string.IsNullOrWhiteSpace(savedFormula) && !formulas.Contains(savedFormula)) formulas.Add(savedFormula);
        var current = savedFormula ?? _priceFormula.SelectedValue?.ToString();
        var preferred = PricingFormula.SquareMeter;
        var selected = !resetFormula && current is not null && formulas.Contains(current) ? current : preferred;
        var wasLoading = _loadingPriceEditor;
        _loadingPriceEditor = true;
        _priceFormula.DataSource = formulas.Select(code => new KeyValuePair<string, string>(code, PricingFormula.Labels[code])).ToList();
        _priceFormula.SelectedValue = selected;
        _loadingPriceEditor = wasLoading;
        UpdatePriceFormulaFields(resetFormula);
    }

    private void UpdatePriceFormulaFields(bool setDefaults)
    {
        if (_priceFormula is null) return;
        var formula = _priceFormula.SelectedValue?.ToString() ?? PricingFormula.SquareMeter;
        var isServiceOnly = (_priceStructure.SelectedItem?.ToString() ?? "").Equals("Hizmet", StringComparison.Ordinal);
        var isPrint = _pricePrintEnabled.Checked && !isServiceOnly;
        var usesSheetDimensions = !isServiceOnly && !isPrint && formula == PricingFormula.SheetArea;
        SetPriceFieldVisibility(_priceSecondaryLabel, _priceSecondary, formula == PricingFormula.DtfTier);
        SetPriceFieldVisibility(_priceSheetWidthLabel, _priceSheetWidth, usesSheetDimensions);
        SetPriceFieldVisibility(_priceSheetHeightLabel, _priceSheetHeight, usesSheetDimensions);
        SetPriceFieldVisibility(_priceThicknessLabel, _priceThickness, usesSheetDimensions);
        SetPriceFieldVisibility(_priceBaseMaterialLabel, _priceBaseMaterial, isPrint);
        _priceMaterialPreview.Visible = usesSheetDimensions;
        _priceSheetWidthLabel.Text = "Malzeme eni (cm)";
        _priceSheetHeightLabel.Text = "Malzeme boyu (cm)";

        (_priceCostFieldLabel.Text, _priceFormulaHelp.Text) = formula switch
        {
            PricingFormula.Minute => ("Dakika başı işçilik maliyeti", "Fiyat hesabında girilen süre × dakika maliyeti kullanılır. Lazer kesim gibi süreli işler içindir."),
            PricingFormula.Hour => ("Saat başı işçilik maliyeti", "Fiyat hesabındaki dakika süreye çevrilerek saatlik işçilik hesaplanır."),
            PricingFormula.PercentMaterial => ("Baskı / malzeme maliyetine eklenecek hizmet (%)", "Plotter kesim gibi hizmetlerde seçilen baskı ve malzemelerin toplam maliyeti üzerinden yüzde hesaplanır."),
            PricingFormula.SheetArea => ("Levha alış fiyatı", "Dekota ve Pleksi gibi levhalarda en ve boy zorunludur; kullanılan alan levha alanına oranlanır."),
            PricingFormula.UvTable => ("60×90 tabla baskı maliyeti", "UV baskı maliyeti 60×90 cm tabla alanına oranlanır."),
            PricingFormula.DtfTier => ("Metre baskı maliyeti", "DTF uzunluğu metre üzerinden hesaplanır; 10 metre üstü için ikinci alış fiyatı kullanılabilir."),
            PricingFormula.Meter => (isPrint ? "Metre baskı maliyeti" : isServiceOnly ? "Metre hizmet maliyeti" : "Metre malzeme maliyeti", "Fiyat hesabında girilen uzunluk kullanılır."),
            PricingFormula.Piece => (isPrint ? "Adet baskı maliyeti" : isServiceOnly ? "Adet hizmet maliyeti" : "Adet malzeme maliyeti", "Girilen adet ile birim maliyet çarpılır."),
            PricingFormula.Fixed => (isPrint ? "Sabit baskı maliyeti" : isServiceOnly ? "Sabit hizmet maliyeti" : "Sabit malzeme maliyeti", "Ölçü ve adetten bağımsız olarak bir kez uygulanır."),
            _ => (isPrint ? "m² baskı maliyeti" : isServiceOnly ? "m² hizmet maliyeti" : "m² malzeme maliyeti", "Fiyat hesabındaki en × boy alanı kullanılır.")
        };

        SetPriceFieldVisibility(_priceVariantLabel, _priceVariant, true);
        _pricePrintEnabled.Visible = false;
        _priceServiceEnabled.Visible = false;

        var percent = formula == PricingFormula.PercentMaterial;
        _priceCurrency.Enabled = !percent;
        if (percent) _priceCurrency.SelectedItem = "%";
        else if (_priceCurrency.SelectedItem?.ToString() == "%") _priceCurrency.SelectedItem = "TL";
        if (!setDefaults) return;
        _priceUnit.Text = formula switch
        {
            PricingFormula.Minute => "dakika",
            PricingFormula.Hour => "saat",
            PricingFormula.PercentMaterial => "%",
            PricingFormula.SheetArea => "levha",
            PricingFormula.UvTable => "tabla",
            PricingFormula.DtfTier or PricingFormula.Meter => "metre",
            PricingFormula.Piece => "adet",
            PricingFormula.Fixed => "iş",
            _ => "m²"
        };
        UpdatePriceMaterialPreview();
    }

    private void UpdatePriceMaterialPreview()
    {
        if (_priceMaterialPreview is null || _pricePrintEnabled.Checked || _priceFormula.SelectedValue?.ToString() != PricingFormula.SheetArea) return;
        var area = _priceSheetWidth.Value * _priceSheetHeight.Value / 10_000m;
        var currency = _priceCurrency.SelectedItem?.ToString() ?? "TL";
        var formula = _priceFormula.SelectedValue?.ToString() ?? PricingFormula.SheetArea;
        var total = formula == PricingFormula.SheetArea ? _priceCost.Value : area * _priceCost.Value;
        var perM2 = area > 0 ? total / area : 0;
        _priceMaterialPreview.Text = $"Alan: {area:N4} m²   •   Kalınlık: {_priceThickness.Value:0.##} mm\nBu ölçünün maliyeti: {total:N2} {currency}   •   m² maliyeti: {perM2:N2} {currency}";
    }

    private void UpdateProductServiceFields()
    {
        if (_priceServiceEnabled is null) return;
        var visible = false;
        _priceServiceCostLabel.Text = _priceServiceFormula.SelectedValue?.ToString() == PricingFormula.Minute
            ? "Dakika başı hizmet maliyeti"
            : "m² başı hizmet maliyeti";
        SetPriceFieldVisibility(_priceServiceNameLabel, _priceServiceName, visible);
        SetPriceFieldVisibility(_priceServiceFormulaLabel, _priceServiceFormula, visible);
        SetPriceFieldVisibility(_priceServiceCostLabel, _priceServiceCost, visible);
    }

    private void PopulatePriceProfitInputs(PriceItem? item)
    {
        if (_priceProfitPanel is null) return;
        _priceProfitPanel.SuspendLayout();
        _priceProfitPanel.Controls.Clear();
        _priceProfitInputs.Clear();
        foreach (var group in _store.State.PriceGroups.Where(x => !x.Deleted).OrderBy(x => x.CostMultiplier))
        {
            var standardPercent = (group.CostMultiplier - 1m) * 100m;
            decimal specialPercent = 0;
            var hasSpecial = item is not null && item.GroupProfitPercentOverrides?.TryGetValue(group.Id, out specialPercent) == true;
            var row = new FlowLayoutPanel { Width = 370, Height = 34, FlowDirection = FlowDirection.LeftToRight, WrapContents = false, Margin = new Padding(0, 1, 0, 1) };
            var groupLabel = new Label { Text = $"{group.Name} (standart %{standardPercent:0.##})", Width = 195, Height = 28, TextAlign = ContentAlignment.MiddleLeft, ForeColor = UiTheme.Ink };
            var useSpecial = new CheckBox { Text = "Özel", Width = 58, Height = 28, Checked = hasSpecial, TextAlign = ContentAlignment.MiddleLeft };
            var profitPercent = UiTheme.Number(10000, 2); profitPercent.Dock = DockStyle.None; profitPercent.Width = 100;
            profitPercent.Value = Clamp(profitPercent, hasSpecial ? specialPercent : standardPercent);
            profitPercent.Enabled = hasSpecial;
            useSpecial.CheckedChanged += (_, _) => profitPercent.Enabled = useSpecial.Checked;
            row.Controls.AddRange([groupLabel, useSpecial, profitPercent]);
            _priceProfitPanel.Controls.Add(row);
            _priceProfitInputs[group.Id] = (useSpecial, profitPercent);
        }
        _priceProfitPanel.ResumeLayout();
    }

    private bool PriceProfitInputsChanged(PriceItem? item)
    {
        foreach (var (groupId, input) in _priceProfitInputs)
        {
            decimal savedPercent = 0;
            var hasSaved = item is not null && item.GroupProfitPercentOverrides?.TryGetValue(groupId, out savedPercent) == true;
            if (input.UseSpecial.Checked != hasSaved) return true;
            if (input.UseSpecial.Checked && input.ProfitPercent.Value != savedPercent) return true;
        }
        return false;
    }

    private static void SetPriceFieldVisibility(Label label, Control control, bool visible)
    {
        label.Visible = visible;
        control.Visible = visible;
    }

    private void LoadSelectedPrice()
    {
        if (_priceGrid.SelectedRows.Count == 0) return;
        var id = _priceGrid.SelectedRows[0].Cells["id"].Value?.ToString();
        var item = _store.State.PriceItems.FirstOrDefault(x => x.Id == id);
        if (item is null) return;
        _loadingPriceEditor = true;
        _selectedPriceId = item.Id;
        _priceCategory.SelectedItem = "Ürün";
        _priceStructure.SelectedItem = item.Category.Equals("Hizmet", StringComparison.OrdinalIgnoreCase)
            ? "Hizmet"
            : item.IsPrintProduct ? "Baskı" : "Malzeme";
        _pricePrintEnabled.Checked = !item.Category.Equals("Hizmet", StringComparison.OrdinalIgnoreCase) && (item.IsPrintProduct || item.Category == "Baskı");
        ConfigurePriceCategory(false);
        _priceName.Text = item.Name; _priceVariant.Text = item.Variant; _priceUnit.Text = item.Unit;
        _priceCurrency.SelectedItem = item.Currency;
        _priceFormula.SelectedValue = item.Formula;
        _priceCost.Value = Clamp(_priceCost, item.UnitCost); _priceSecondary.Value = Clamp(_priceSecondary, item.SecondaryCost);
        _priceSheetWidth.Value = Clamp(_priceSheetWidth, item.SheetWidthCm); _priceSheetHeight.Value = Clamp(_priceSheetHeight, item.SheetHeightCm);
        _priceThickness.Value = Clamp(_priceThickness, item.ThicknessMm);
        _priceBaseMaterial.SelectedValue = item.BaseMaterialPriceItemId ?? "";
        _priceServiceEnabled.Checked = false;
        _priceServiceName.Text = item.ServiceName;
        _priceServiceFormula.SelectedValue = item.ServiceFormula;
        _priceServiceCost.Value = Clamp(_priceServiceCost, item.ServiceUnitCost);
        _priceActive.Checked = item.Active;
        PopulatePriceProfitInputs(item);
        _loadingPriceEditor = false;
        UpdatePriceFormulaFields(false);
        UpdateProductServiceFields();
        UpdatePriceEditorMode();
        RefreshPriceGrid();
    }

    private void ClearPriceEditor()
    {
        _loadingPriceEditor = true;
        _selectedPriceId = null;
        _priceCategory.SelectedIndex = 0; _priceStructure.SelectedIndex = 0; _priceName.Clear(); _priceVariant.Clear(); _priceUnit.Text = "m²";
        _priceCurrency.SelectedItem = "TL"; _pricePrintEnabled.Checked = false;
        _priceCost.Value = 0; _priceSecondary.Value = 0; _priceSheetWidth.Value = 0; _priceSheetHeight.Value = 0; _priceThickness.Value = 0; _priceBaseMaterial.SelectedValue = "";
        _priceServiceEnabled.Checked = false; _priceServiceName.Clear(); _priceServiceFormula.SelectedValue = PricingFormula.SquareMeter; _priceServiceCost.Value = 0;
        _priceActive.Checked = true;
        PopulatePriceProfitInputs(null);
        _loadingPriceEditor = false;
        ConfigurePriceCategory(true);
        UpdateProductServiceFields();
        UpdatePriceEditorMode();
        _priceGrid.ClearSelection();
    }

    private async Task SavePriceAsync()
    {
        if (string.IsNullOrWhiteSpace(_priceName.Text)) { MessageBox.Show("Ürün adı zorunludur.", "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
        var selectedFormula = _priceFormula.SelectedValue?.ToString() ?? PricingFormula.SquareMeter;
        var isServiceOnly = (_priceStructure.SelectedItem?.ToString() ?? "").Equals("Hizmet", StringComparison.Ordinal);
        var isPrint = (_priceStructure.SelectedItem?.ToString() ?? "").Equals("Baskı", StringComparison.Ordinal);
        var currentItem = _store.State.PriceItems.FirstOrDefault(x => x.Id == _selectedPriceId);
        var usesSheetDimensions = !isServiceOnly && !isPrint && selectedFormula == PricingFormula.SheetArea;
        if (usesSheetDimensions && (_priceSheetWidth.Value <= 0 || _priceSheetHeight.Value <= 0))
        {
            MessageBox.Show("Malzeme için cm cinsinden en ve boy zorunludur.", "Ürün Ekle", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }
        if (isPrint && string.IsNullOrWhiteSpace((_priceBaseMaterial.SelectedItem as PriceItem)?.Id))
        {
            MessageBox.Show("Baskılı ürün için kullanılan malzemeyi seçin.", "Ürün Ekle", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }
        if (!isServiceOnly && _priceServiceEnabled.Checked && string.IsNullOrWhiteSpace(_priceServiceName.Text))
        {
            MessageBox.Show("Eklenen hizmetin adını yazın.", "Ürün Ekle", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }
        var item = currentItem ?? new PriceItem { DeviceId = _store.State.DeviceId, Revision = 0 };
        _store.CaptureUndo(item.Revision == 0 ? "Yeni ürün eklendi" : $"{item.DisplayName} ürünü değiştirildi");
        item.Category = isServiceOnly ? "Hizmet" : isPrint ? "Baskı" : "Malzeme";
        item.Name = _priceName.Text.Trim(); item.Variant = _priceVariant.Text.Trim(); item.Unit = _priceUnit.Text.Trim();
        item.Currency = _priceCurrency.SelectedItem?.ToString() ?? "TL";
        item.Formula = selectedFormula;
        item.UnitCost = _priceCost.Value;
        item.SecondaryCost = item.Formula == PricingFormula.DtfTier ? _priceSecondary.Value : 0;
        item.SheetWidthCm = usesSheetDimensions ? _priceSheetWidth.Value : 0;
        item.SheetHeightCm = usesSheetDimensions ? _priceSheetHeight.Value : 0;
        item.ThicknessMm = usesSheetDimensions ? _priceThickness.Value : 0;
        item.BaseMaterialPriceItemId = isPrint ? (_priceBaseMaterial.SelectedItem as PriceItem)?.Id ?? "" : "";
        item.IsPrintProduct = isPrint;
        // Yeni yapıda hizmet ayrı bir kayıttır. Eski birleşik kayıtlarda daha önce
        // saklanmış hizmet bilgisini kullanıcı düzenleme sırasında kaybetmesin.
        var preserveLegacyService = currentItem?.ServiceEnabled == true;
        item.ServiceEnabled = preserveLegacyService;
        item.ServiceName = preserveLegacyService ? currentItem!.ServiceName : "";
        item.ServiceFormula = preserveLegacyService ? currentItem!.ServiceFormula : PricingFormula.SquareMeter;
        item.ServiceUnitCost = preserveLegacyService ? currentItem!.ServiceUnitCost : 0;
        item.GroupProfitPercentOverrides ??= [];
        foreach (var (groupId, input) in _priceProfitInputs)
        {
            if (input.UseSpecial.Checked) item.GroupProfitPercentOverrides[groupId] = input.ProfitPercent.Value;
            else item.GroupProfitPercentOverrides.Remove(groupId);
        }
        item.Active = _priceActive.Checked;
        _store.Touch(item);
        if (!_store.State.PriceItems.Contains(item)) _store.State.PriceItems.Add(item);
        _selectedPriceId = item.Id;
        UpdatePriceEditorMode();
        await PersistAndSyncAsync("Ürün güncellendi: " + item.DisplayName);
        RefreshAll();
    }

    private async Task DeletePriceAsync()
    {
        var item = _store.State.PriceItems.FirstOrDefault(x => x.Id == _selectedPriceId);
        if (item is null) return;
        if (MessageBox.Show($"{item.DisplayName} silinmiş olarak işaretlensin mi? Eski siparişler değişmez.", "Fiyat Kalemi Sil", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
        _store.CaptureUndo(item.DisplayName + " fiyat kalemi silindi");
        item.Deleted = true; _store.Touch(item);
        await PersistAndSyncAsync("Fiyat kalemi silindi: " + item.DisplayName);
        ClearPriceEditor(); RefreshAll();
    }

    private static string PriceOverrideSummary(PriceItem item, PriceGroup group)
    {
        var special = PricingEngine.GetSpecialProfitPercent(item, group.Id);
        return special.HasValue
            ? $"{group.Name} özel %{special.Value:0.##}"
            : $"{group.Name} standart %{(group.CostMultiplier - 1m) * 100m:0.##}";
    }

    private void RefreshCalcItems()
    {
        if (_calcItems is null) return;
        var checkedIds = _calcItems.CheckedItems.Cast<PriceItem>().Select(x => x.Id).ToHashSet();
        _calcItems.Items.Clear();
        foreach (var item in _store.State.PriceItems.Where(x => !x.Deleted && x.Active).OrderBy(x => x.Category).ThenBy(x => x.Name).ThenBy(x => x.Variant))
            _calcItems.Items.Add(item, checkedIds.Contains(item.Id));
        _calcItems.DisplayMember = nameof(PriceItem.DisplayName);
        if (_calcRate is not null) _calcRate.Value = Clamp(_calcRate, _store.State.Settings.UsdTryRate);
    }

    private void RecalculatePreview()
    {
        if (_calcItems is null || _calcItems.CheckedItems.Count == 0) return;
        Calculate(false);
    }

    private void Calculate(bool showWarning = true)
    {
        _lastCalculation = null;
        var selected = _calcItems.CheckedItems.Cast<PriceItem>().ToList();
        if (selected.Count == 0)
        {
            if (showWarning) MessageBox.Show("En az bir malzeme, baskı veya işlem seçin.", "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        var group = _calcGroup.SelectedItem as PriceGroup ?? _store.State.PriceGroups.First(x => x.Id == "retail");
        var input = new CalculationInput(_calcWidth.Value, _calcHeight.Value, _calcLength.Value, _calcMinutes.Value, _calcQuantity.Value, _calcRate.Value);
        _lastCalculation = PricingEngine.Calculate(selected, input, group.CostMultiplier, _calcAlternative.Checked ? _calcAlternativePercent.Value : null, group.Id, _store.State.PriceGroups, _store.State.PriceItems);
        _calcLines.Items.Clear();
        foreach (var line in _lastCalculation.Lines)
            _calcLines.Items.Add($"{line.Name,-38} {line.CostTl,12:N2} TL");
        _calcCostLabel.Text = $"Maliyet: {_lastCalculation.CostTl:N2} TL";
        var usesSpecialProfit = !_calcAlternative.Checked && selected.Any(item => PricingEngine.GetSpecialProfitPercent(item, group.Id).HasValue);
        _calcSaleLabel.Text = usesSpecialProfit
            ? $"{group.Name} (ürüne özel oran): {_lastCalculation.SaleTl:N2} TL"
            : $"{group.Name}: {_lastCalculation.SaleTl:N2} TL";
    }

    private async Task SaveOrderAsync()
    {
        Calculate();
        if (_lastCalculation is null || _lastCalculation.Lines.Count == 0) return;
        var customer = ChooseOrderCustomer();
        if (customer is null) return;
        var group = CustomerPriceGroup(customer);
        if (group is null) return;
        var selected = _calcItems.CheckedItems.Cast<PriceItem>().ToList();
        var input = new CalculationInput(_calcWidth.Value, _calcHeight.Value, _calcLength.Value, _calcMinutes.Value, _calcQuantity.Value, _calcRate.Value);
        _lastCalculation = PricingEngine.Calculate(selected, input, group.CostMultiplier, _calcAlternative.Checked ? _calcAlternativePercent.Value : null,
            group.Id, _store.State.PriceGroups, _store.State.PriceItems);
        if (_lastCalculation.Lines.Count == 0) return;
        var description = string.IsNullOrWhiteSpace(_calcDescription.Text) ? string.Join(" + ", _lastCalculation.Lines.Select(x => x.Name)) : _calcDescription.Text.Trim();
        var order = new Order
        {
            CustomerId = customer.Id, Description = description, Material = string.Join(" + ", _lastCalculation.Lines.Select(x => x.Name).Distinct()), Date = DateTime.Today,
            WidthCm = _calcWidth.Value, HeightCm = _calcHeight.Value, LengthMeter = _calcLength.Value,
            DurationMinutes = _calcMinutes.Value, Quantity = _calcQuantity.Value, ExchangeRate = _calcRate.Value,
            CostTotalTl = _lastCalculation.CostTl, SaleTotalTl = _lastCalculation.SaleTl,
            PriceGroupId = group.Id, AlternativePercent = _calcAlternative.Checked ? _calcAlternativePercent.Value : null,
            Lines = _lastCalculation.Lines, DeviceId = _store.State.DeviceId, Revision = 1
        };
        _store.CaptureUndo(customer.Name + " için sipariş eklendi");
        _store.State.Orders.Add(order);
        await PersistAndSyncAsync("Sipariş kaydı: " + description);
        MessageBox.Show($"Sipariş {group.Name} fiyatıyla kaydedildi ve {customer.Name} carisine {_lastCalculation.SaleTl:N2} TL borç işlendi.", "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Information);
        _calcDescription.Clear(); _lastCalculation = null; _calcLines.Items.Clear();
        RefreshAll();
    }

    private Customer? ChooseOrderCustomer()
    {
        var customers = _store.State.Customers.Where(x => !x.Deleted).OrderBy(x => x.Name).ToList();
        if (customers.Count == 0)
        {
            MessageBox.Show("Siparişe dönüştürmek için önce müşteri ekleyin.", "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return null;
        }
        using var dialog = new Form
        {
            Text = "Siparişi Cariye İşle", Width = 460, Height = 235, StartPosition = FormStartPosition.CenterParent,
            FormBorderStyle = FormBorderStyle.FixedDialog, MaximizeBox = false, MinimizeBox = false,
            BackColor = Color.White, Font = Font
        };
        var title = new Label { Text = "Sipariş hangi müşterinin carisine işlensin?", AutoSize = true, Font = new Font("Segoe UI Semibold", 12f), ForeColor = UiTheme.Navy, Location = new Point(24, 22) };
        var groupInfo = new Label { Text = "Seçilen müşterinin kartındaki fiyat grubu uygulanır.", AutoSize = true, ForeColor = UiTheme.Muted, Location = new Point(26, 57) };
        var combo = UiTheme.Combo(); combo.Location = new Point(26, 87); combo.Width = 390; combo.Dock = DockStyle.None;
        combo.DataSource = customers; combo.DisplayMember = nameof(Customer.Name); combo.ValueMember = nameof(Customer.Id);
        var ok = UiTheme.Button("Siparişi Kaydet", true); ok.Location = new Point(238, 137); ok.DialogResult = DialogResult.OK;
        var cancel = UiTheme.Button("Vazgeç", false); cancel.Location = new Point(128, 137); cancel.DialogResult = DialogResult.Cancel;
        dialog.Controls.AddRange([title, groupInfo, combo, cancel, ok]); dialog.AcceptButton = ok; dialog.CancelButton = cancel;
        return dialog.ShowDialog(this) == DialogResult.OK ? combo.SelectedItem as Customer : null;
    }

    private PriceGroup? CustomerPriceGroup(Customer? customer)
    {
        if (customer is null) return null;
        var group = _store.State.PriceGroups.FirstOrDefault(x => !x.Deleted && x.Id == customer.PriceGroupId);
        if (group is null)
            MessageBox.Show($"{customer.Name} için geçerli bir fiyat grubu bulunamadı.", "Müşteri fiyat grubu", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        return group;
    }

    private void RefreshLedger(string? selectedMovementId = null, string? selectedColumn = null)
    {
        if (_ledgerGrid is null) return;
        _refreshingLedger = true;
        _ledgerGrid.Rows.Clear();
        var customer = _ledgerCustomer.SelectedItem as Customer;
        if (customer is null) { _ledgerBalance.Text = "Bakiye: 0,00 TL"; _refreshingLedger = false; return; }
        decimal running = 0;
        var prepared = new List<(string Id, DateTime Date, string Type, string Description, string Material, string Measure, decimal Debit, decimal Credit, decimal Balance)>();
        foreach (var row in _store.GetLedger(customer.Id))
        {
            running += row.Debit - row.Credit;
            prepared.Add((row.Id, row.Date, row.Type, row.Description, row.Material, row.Measure, row.Debit, row.Credit, running));
        }
        IEnumerable<(string Id, DateTime Date, string Type, string Description, string Material, string Measure, decimal Debit, decimal Credit, decimal Balance)> visible = prepared;
        if (_ledgerDateFilter?.Checked == true)
            visible = visible.Where(x => x.Date.Date >= _ledgerFrom.Value.Date && x.Date.Date <= _ledgerTo.Value.Date);
        visible = _ledgerSort?.SelectedIndex switch
        {
            1 => visible.OrderByDescending(x => x.Date).ThenByDescending(x => x.Type),
            2 => visible.OrderByDescending(x => Math.Max(x.Debit, x.Credit)).ThenByDescending(x => x.Date),
            _ => visible.OrderBy(x => x.Date).ThenBy(x => x.Type)
        };
        foreach (var row in visible)
            _ledgerGrid.Rows.Add(row.Id, row.Type == "Satış" ? "order" : "payment", row.Date == DateTime.MinValue ? "" : row.Date.ToString("dd.MM.yyyy"), row.Type, row.Description, row.Material, row.Measure, row.Debit == 0 ? "" : row.Debit, row.Credit == 0 ? "" : row.Credit, row.Balance);
        var balance = _store.GetBalance(customer.Id);
        _ledgerBalance.Text = $"Bakiye: {balance:N2} TL";
        _ledgerBalance.ForeColor = balance > 0 ? UiTheme.Orange : UiTheme.Teal;
        _refreshingLedger = false;
        if (!string.IsNullOrWhiteSpace(selectedMovementId))
        {
            var row = _ledgerGrid.Rows.Cast<DataGridViewRow>()
                .FirstOrDefault(x => string.Equals(x.Cells["id"].Value?.ToString(), selectedMovementId, StringComparison.Ordinal));
            if (row is not null)
            {
                var targetColumn = !string.IsNullOrWhiteSpace(selectedColumn) && _ledgerGrid.Columns.Contains(selectedColumn)
                    ? selectedColumn : "material";
                var cell = row.Cells[targetColumn];
                _ledgerGrid.ClearSelection();
                cell.Selected = true;
                _ledgerGrid.CurrentCell = cell;
                if (!row.Displayed) _ledgerGrid.FirstDisplayedScrollingRowIndex = row.Index;
            }
        }
    }

    private void PopulateLedgerOrderSelectors()
    {
        if (_ledgerOrderMaterial is null) return;
        var materialId = (_ledgerOrderMaterial.SelectedItem as PriceItem)?.Id;
        _ledgerOrderMaterial.DataSource = _store.State.PriceItems.Where(x => !x.Deleted && x.Active).OrderBy(x => x.Category).ThenBy(x => x.Name).ThenBy(x => x.Variant).ToList();
        _ledgerOrderMaterial.DisplayMember = nameof(PriceItem.DisplayName); _ledgerOrderMaterial.ValueMember = nameof(PriceItem.Id);
        if (materialId is not null) _ledgerOrderMaterial.SelectedValue = materialId;
        UpdateLedgerOrderPreview();
    }

    private CalculationResult? CalculateLedgerOrder()
    {
        var item = _ledgerOrderMaterial?.SelectedItem as PriceItem;
        var group = CustomerPriceGroup(_ledgerCustomer?.SelectedItem as Customer);
        if (item is null || group is null) return null;
        try
        {
            return PricingEngine.Calculate([item], new CalculationInput(_ledgerOrderWidth.Value, _ledgerOrderHeight.Value, _ledgerOrderLength.Value, 0, _ledgerOrderQuantity.Value, _store.State.Settings.UsdTryRate), group.CostMultiplier, null, group.Id, _store.State.PriceGroups, _store.State.PriceItems);
        }
        catch { return null; }
    }

    private void UpdateLedgerOrderPreview()
    {
        if (_ledgerOrderPreview is null) return;
        var result = CalculateLedgerOrder();
        _ledgerOrderPreview.Text = result is null ? "Alış ve satış: ölçü/bilgi girin" : $"Alış: {result.CostTl:N2} TL   Satış: {result.SaleTl:N2} TL";
    }

    private async Task SaveLedgerOrderAsync()
    {
        var customer = _ledgerCustomer.SelectedItem as Customer;
        var item = _ledgerOrderMaterial.SelectedItem as PriceItem;
        var group = CustomerPriceGroup(customer);
        var calculation = CalculateLedgerOrder();
        if (customer is null || item is null || group is null || calculation is null || calculation.Lines.Count == 0)
        {
            MessageBox.Show("Müşteri, malzeme ve gerekli ölçüleri seçin.", "Sipariş Ekle", MessageBoxButtons.OK, MessageBoxIcon.Warning); return;
        }
        var description = string.IsNullOrWhiteSpace(_ledgerOrderDescription.Text) ? item.DisplayName : _ledgerOrderDescription.Text.Trim();
        if (MessageBox.Show($"{customer.Name} carisine {calculation.SaleTl:N2} TL borç kaydedilsin mi?\n\n{description}", "Yeni Borcu Kaydet", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
        var order = new Order
        {
            CustomerId = customer.Id, Date = _ledgerOrderDate.Value.Date, Description = description, Material = item.DisplayName,
            WidthCm = _ledgerOrderWidth.Value, HeightCm = _ledgerOrderHeight.Value, LengthMeter = _ledgerOrderLength.Value,
            Quantity = _ledgerOrderQuantity.Value, ExchangeRate = _store.State.Settings.UsdTryRate,
            CostTotalTl = calculation.CostTl, SaleTotalTl = calculation.SaleTl, PriceGroupId = group.Id,
            Lines = calculation.Lines, DeviceId = _store.State.DeviceId
        };
        _store.CaptureUndo(customer.Name + " carisine sipariş eklendi");
        _store.State.Orders.Add(order);
        await PersistAndSyncAsync("Cari siparişi: " + description);
        _ledgerOrderDescription.Clear(); _ledgerOrderWidth.Value = 0; _ledgerOrderHeight.Value = 0; _ledgerOrderLength.Value = 0; _ledgerOrderQuantity.Value = 1;
        RefreshAll();
    }

    private void InlineGrid_CellBeginEdit(object? sender, DataGridViewCellCancelEventArgs e)
    {
        _inlineGridEditOriginal = null;
        if (sender is not DataGridView grid || e.RowIndex < 0 || e.ColumnIndex < 0 || grid.ReadOnly || grid.Columns[e.ColumnIndex].ReadOnly)
        {
            e.Cancel = true;
            return;
        }
        _inlineGridEditOriginal = (grid, e.RowIndex, e.ColumnIndex, LedgerCellText(grid.Rows[e.RowIndex].Cells[e.ColumnIndex].Value));
    }

    private bool InlineGridEditChanged(DataGridView grid, DataGridViewCellEventArgs e)
    {
        var original = _inlineGridEditOriginal;
        _inlineGridEditOriginal = null;
        return original is { } value && value.Grid == grid && value.RowIndex == e.RowIndex && value.ColumnIndex == e.ColumnIndex &&
               !string.Equals(value.Value, LedgerCellText(grid.Rows[e.RowIndex].Cells[e.ColumnIndex].Value), StringComparison.Ordinal);
    }

    private static void SelectGridRow(DataGridView grid, string id)
    {
        grid.ClearSelection();
        var row = grid.Rows.Cast<DataGridViewRow>().FirstOrDefault(x => string.Equals(x.Cells["id"].Value?.ToString(), id, StringComparison.Ordinal));
        if (row is not null) row.Selected = true;
    }

    private static bool ConfirmInlineGridSave(string header, string value) =>
        MessageBox.Show($"{header} alanındaki değişiklik kaydedilsin mi?\n\nYeni değer: {value}", "Tablo Değişikliğini Kaydet", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes;

    private async Task SaveCustomerGridEditAsync(DataGridViewCellEventArgs e)
    {
        if (!InlineGridEditChanged(_customerGrid, e)) return;
        var row = _customerGrid.Rows[e.RowIndex];
        var id = row.Cells["id"].Value?.ToString();
        var column = _customerGrid.Columns[e.ColumnIndex].Name;
        var value = LedgerCellText(row.Cells[e.ColumnIndex].Value);
        if (string.IsNullOrWhiteSpace(id)) return;
        if (!ConfirmInlineGridSave(_customerGrid.Columns[e.ColumnIndex].HeaderText, value)) { RefreshCustomerGrid(); SelectGridRow(_customerGrid, id); return; }
        try
        {
            var customer = _store.State.Customers.FirstOrDefault(x => !x.Deleted && x.Id == id) ?? throw new InvalidDataException("Müşteri kaydı bulunamadı.");
            _store.CaptureUndo("Müşteri tablodan güncellendi");
            switch (column)
            {
                case "name":
                    if (string.IsNullOrWhiteSpace(value)) throw new InvalidDataException("Müşteri adı boş olamaz.");
                    customer.Name = value;
                    break;
                case "company": customer.Company = value; break;
                case "phone": customer.Phone = value; break;
                case "group":
                    var group = _store.State.PriceGroups.FirstOrDefault(x => !x.Deleted && x.Name.Equals(value, StringComparison.CurrentCultureIgnoreCase));
                    if (group is null) throw new InvalidDataException("Fiyat grubu bulunamadı. Mevcut grup adlarından birini yazın.");
                    customer.PriceGroupId = group.Id;
                    break;
                default: return;
            }
            _store.Touch(customer);
            await PersistAndSyncAsync("Müşteri tablodan güncellendi: " + customer.Name);
            PopulateCustomerCombos();
            RefreshCustomerGrid();
            SelectGridRow(_customerGrid, id);
            LoadSelectedCustomer();
        }
        catch (Exception ex)
        {
            RefreshCustomerGrid(); SelectGridRow(_customerGrid, id);
            MessageBox.Show("Değişiklik uygulanamadı: " + ex.Message, "Müşteri Güncelleme", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    private async Task SavePriceGridEditAsync(DataGridViewCellEventArgs e)
    {
        if (!InlineGridEditChanged(_priceGrid, e)) return;
        var row = _priceGrid.Rows[e.RowIndex];
        var id = row.Cells["id"].Value?.ToString();
        var column = _priceGrid.Columns[e.ColumnIndex].Name;
        var value = LedgerCellText(row.Cells[e.ColumnIndex].Value);
        if (string.IsNullOrWhiteSpace(id)) return;
        if (!ConfirmInlineGridSave(_priceGrid.Columns[e.ColumnIndex].HeaderText, value)) { RefreshPriceGrid(); SelectGridRow(_priceGrid, id); return; }
        try
        {
            var item = _store.State.PriceItems.FirstOrDefault(x => !x.Deleted && x.Id == id) ?? throw new InvalidDataException("Ürün kaydı bulunamadı.");
            _store.CaptureUndo("Ürün tablodan güncellendi");
            switch (column)
            {
                case "category":
                    var category = NormalizePriceCategory(value);
                    item.Category = category;
                    item.IsPrintProduct = category == "Baskı";
                    if (category != "Baskı") item.BaseMaterialPriceItemId = "";
                    break;
                case "name":
                    if (string.IsNullOrWhiteSpace(value)) throw new InvalidDataException("Ürün adı boş olamaz.");
                    item.Name = value;
                    break;
                case "variant": item.Variant = value; break;
                case "unit":
                    if (string.IsNullOrWhiteSpace(value)) throw new InvalidDataException("Birim boş olamaz.");
                    item.Unit = value;
                    break;
                case "currency":
                    if (value is not ("TL" or "USD" or "%")) throw new InvalidDataException("Para alanına TL, USD veya % yazın.");
                    item.Currency = value;
                    break;
                case "cost":
                    if (!TryParseDecimal(value, out var cost) || cost < 0) throw new InvalidDataException("Alış fiyatı geçerli değil.");
                    item.UnitCost = cost;
                    break;
                case "formula": item.Formula = ResolvePricingFormula(value); break;
                case "specialProfit":
                    var priceGroup = _priceGroup.SelectedItem as PriceGroup ?? throw new InvalidDataException("Tablo fiyat grubu bulunamadı.");
                    item.GroupProfitPercentOverrides ??= [];
                    if (string.IsNullOrWhiteSpace(value)) item.GroupProfitPercentOverrides.Remove(priceGroup.Id);
                    else
                    {
                        if (!TryParseDecimal(value.Trim().TrimStart('%'), out var percent) || percent < 0) throw new InvalidDataException("Özel kâr için yüzde değeri yazın; kaldırmak için hücreyi boş bırakın.");
                        item.GroupProfitPercentOverrides[priceGroup.Id] = percent;
                    }
                    break;
                default: return;
            }
            _store.Touch(item);
            await PersistAndSyncAsync("Ürün tablodan güncellendi: " + item.DisplayName);
            PopulatePriceBaseMaterials();
            PopulateProfitPriceItems();
            PopulateLedgerOrderSelectors();
            RefreshCalcItems();
            RefreshPriceGrid();
            SelectPriceGridRow(id);
            LoadSelectedPrice();
        }
        catch (Exception ex)
        {
            RefreshPriceGrid(); SelectPriceGridRow(id);
            MessageBox.Show("Değişiklik uygulanamadı: " + ex.Message, "Ürün Güncelleme", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    private async Task SavePriceGroupGridEditAsync(DataGridViewCellEventArgs e)
    {
        if (!InlineGridEditChanged(_groupGrid, e)) return;
        var row = _groupGrid.Rows[e.RowIndex];
        var id = row.Cells["id"].Value?.ToString();
        var column = _groupGrid.Columns[e.ColumnIndex].Name;
        var value = LedgerCellText(row.Cells[e.ColumnIndex].Value);
        if (string.IsNullOrWhiteSpace(id)) return;
        if (!ConfirmInlineGridSave(_groupGrid.Columns[e.ColumnIndex].HeaderText, value)) { RefreshPriceGroupGrid(); SelectGridRow(_groupGrid, id); return; }
        try
        {
            var group = _store.State.PriceGroups.FirstOrDefault(x => !x.Deleted && x.Id == id) ?? throw new InvalidDataException("Müşteri kategorisi bulunamadı.");
            _store.CaptureUndo("Kâr ayarı tablodan güncellendi");
            if (column == "name")
            {
                if (string.IsNullOrWhiteSpace(value)) throw new InvalidDataException("Müşteri kategorisi adı boş olamaz.");
                group.Name = value;
            }
            else if (column == "profit")
            {
                if (!TryParseDecimal(value, out var profit) || profit < 0) throw new InvalidDataException("Kâr oranı geçerli değil.");
                group.CostMultiplier = 1m + profit / 100m;
            }
            else return;
            _store.Touch(group);
            await PersistAndSyncAsync("Kâr ayarı tablodan güncellendi: " + group.Name);
            PopulateCustomerCombos();
            RefreshCustomerGrid();
            RefreshPriceGrid();
            RefreshPriceGroupGrid();
            SelectGridRow(_groupGrid, id);
            LoadSelectedPriceGroup();
        }
        catch (Exception ex)
        {
            RefreshPriceGroupGrid(); SelectGridRow(_groupGrid, id);
            MessageBox.Show("Değişiklik uygulanamadı: " + ex.Message, "Kâr Ayarları", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    private static string NormalizePriceCategory(string value) => value.Trim().ToLowerInvariant() switch
    {
        "malzeme" => "Malzeme",
        "baskı" or "baski" => "Baskı",
        "hizmet" => "Hizmet",
        _ => throw new InvalidDataException("Tür alanına Malzeme, Baskı veya Hizmet yazın.")
    };

    private static string ResolvePricingFormula(string value)
    {
        var match = PricingFormula.Labels.FirstOrDefault(x => x.Key.Equals(value, StringComparison.OrdinalIgnoreCase) || x.Value.Equals(value, StringComparison.CurrentCultureIgnoreCase));
        return string.IsNullOrWhiteSpace(match.Key) ? throw new InvalidDataException("Hesap türü tanınmadı.") : match.Key;
    }

    private void LedgerGrid_CellBeginEdit(object? sender, DataGridViewCellCancelEventArgs e)
    {
        _ledgerEditOriginal = null;
        if (_refreshingLedger || e.RowIndex < 0 || e.ColumnIndex < 0) { e.Cancel = true; return; }
        var kind = _ledgerGrid.Rows[e.RowIndex].Cells["kind"].Value?.ToString();
        var column = _ledgerGrid.Columns[e.ColumnIndex].Name;
        if ((kind == "payment" && column is "material" or "measure" or "debit") || (kind == "order" && column == "credit")) e.Cancel = true;
        if (!e.Cancel) _ledgerEditOriginal = (e.RowIndex, e.ColumnIndex, LedgerCellText(_ledgerGrid.Rows[e.RowIndex].Cells[e.ColumnIndex].Value));
    }

    private static string LedgerCellText(object? value) => value?.ToString()?.Trim() ?? "";

    private void LedgerGrid_EditingControlShowing(object? sender, DataGridViewEditingControlShowingEventArgs e)
    {
        if (e.Control is not TextBox editor) return;
        if (_ledgerGrid.CurrentCell?.OwningColumn?.Name != "material")
        {
            editor.AutoCompleteMode = AutoCompleteMode.None;
            editor.AutoCompleteSource = AutoCompleteSource.None;
            return;
        }

        var suggestions = new AutoCompleteStringCollection();
        suggestions.AddRange(_store.State.PriceItems
            .Where(x => !x.Deleted && x.Active)
            .Select(x => x.DisplayName)
            .Where(x => !string.IsNullOrWhiteSpace(x))
            .Distinct(StringComparer.CurrentCultureIgnoreCase)
            .OrderBy(x => x, StringComparer.CurrentCultureIgnoreCase)
            .ToArray());
        editor.AutoCompleteCustomSource = suggestions;
        editor.AutoCompleteSource = AutoCompleteSource.CustomSource;
        editor.AutoCompleteMode = AutoCompleteMode.SuggestAppend;
    }

    private async Task SaveLedgerEditAsync(int rowIndex, int columnIndex)
    {
        if (_refreshingLedger || rowIndex < 0 || columnIndex < 0) return;
        var row = _ledgerGrid.Rows[rowIndex];
        var id = row.Cells["id"].Value?.ToString();
        var kind = row.Cells["kind"].Value?.ToString();
        var column = _ledgerGrid.Columns[columnIndex].Name;
        if (string.IsNullOrWhiteSpace(id) || column is not ("date" or "description" or "material" or "measure" or "debit" or "credit" or "balance")) return;
        try
        {
            var header = _ledgerGrid.Columns[column]?.HeaderText ?? column;
            var newValue = row.Cells[column].Value?.ToString() ?? "";
            if (MessageBox.Show($"{header} alanındaki değişiklik kaydedilsin mi?\n\nYeni değer: {newValue}", "Cari Değişikliğini Kaydet", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes)
            {
                RefreshLedger(id, column);
                return;
            }
            if (kind == "order")
            {
                var order = _store.State.Orders.FirstOrDefault(x => x.Id == id && !x.Deleted);
                if (order is null) return;
                _store.CaptureUndo("Cari sipariş satırı değiştirildi");
                if (column == "date")
                {
                    if (!DateTime.TryParse(row.Cells["date"].Value?.ToString(), new System.Globalization.CultureInfo("tr-TR"), System.Globalization.DateTimeStyles.None, out var date)) throw new InvalidDataException("Tarih geçerli değil.");
                    order.Date = date.Date;
                }
                else if (column == "description") order.Description = row.Cells["description"].Value?.ToString()?.Trim() ?? "";
                else if (column == "material")
                {
                    order.Material = row.Cells["material"].Value?.ToString()?.Trim() ?? "";
                    RecalculateEditedOrder(order, GetOrderBasis(order));
                }
                else if (column == "measure")
                {
                    var oldBasis = GetOrderBasis(order);
                    if (!TryApplyMeasure(order, row.Cells["measure"].Value?.ToString() ?? "")) throw new InvalidDataException("Ölçüyü '120 x 250 cm', '5 m²' veya '3,8 m' biçiminde yazın.");
                    RecalculateEditedOrder(order, oldBasis);
                }
                else if (column == "debit")
                {
                    if (!TryParseDecimal(newValue, out var amount) || amount < 0) throw new InvalidDataException("Borç tutarı geçerli değil.");
                    SetOrderSaleTotal(order, amount);
                }
                else if (column == "balance")
                {
                    if (!TryParseDecimal(newValue, out var targetBalance)) throw new InvalidDataException("Bakiye geçerli değil.");
                    var amount = targetBalance - GetBalanceBeforeMovement(order.CustomerId, order.Id);
                    if (amount < 0) throw new InvalidDataException("Bu satış satırında istenen bakiye negatif borç oluşturuyor. Tahsilat satırını düzenleyin.");
                    SetOrderSaleTotal(order, amount);
                }
                _store.Touch(order);
                await PersistAndSyncAsync("Cari sipariş satırı güncellendi");
            }
            else if (kind == "payment")
            {
                var payment = _store.State.Payments.FirstOrDefault(x => x.Id == id && !x.Deleted);
                if (payment is null) return;
                _store.CaptureUndo("Cari tahsilat satırı değiştirildi");
                if (column == "date")
                {
                    if (!DateTime.TryParse(row.Cells["date"].Value?.ToString(), new System.Globalization.CultureInfo("tr-TR"), System.Globalization.DateTimeStyles.None, out var date)) throw new InvalidDataException("Tarih geçerli değil.");
                    payment.Date = date.Date;
                }
                else if (column == "description") payment.Description = row.Cells["description"].Value?.ToString()?.Trim() ?? "Tahsilat";
                else if (column == "credit")
                {
                    if (!TryParseDecimal(row.Cells["credit"].Value?.ToString(), out var amount) || amount <= 0) throw new InvalidDataException("Tahsilat tutarı geçerli değil.");
                    payment.AmountTl = amount;
                }
                else if (column == "balance")
                {
                    if (!TryParseDecimal(newValue, out var targetBalance)) throw new InvalidDataException("Bakiye geçerli değil.");
                    var amount = GetBalanceBeforeMovement(payment.CustomerId, payment.Id) - targetBalance;
                    if (amount < 0) throw new InvalidDataException("Bu tahsilat satırında istenen bakiye negatif tahsilat oluşturuyor. Borç satırını düzenleyin.");
                    payment.AmountTl = amount;
                }
                _store.Touch(payment);
                await PersistAndSyncAsync("Cari tahsilat satırı güncellendi");
            }
            RefreshLedger(id, column);
        }
        catch (Exception ex)
        {
            RefreshLedger(id, column);
            MessageBox.Show("Değişiklik uygulanamadı: " + ex.Message, "Cari Güncelleme", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    private decimal GetBalanceBeforeMovement(string customerId, string movementId)
    {
        decimal balance = 0;
        foreach (var movement in _store.GetLedger(customerId))
        {
            if (movement.Id == movementId) break;
            balance += movement.Debit - movement.Credit;
        }
        return balance;
    }

    private static void SetOrderSaleTotal(Order order, decimal saleTotal)
    {
        order.SaleTotalTl = decimal.Round(saleTotal, 2);
        order.AlternativePercent = order.CostTotalTl > 0
            ? decimal.Round((order.SaleTotalTl / order.CostTotalTl - 1m) * 100m, 4)
            : null;
    }

    private void RecalculateEditedOrder(Order order, decimal oldBasis)
    {
        var item = ResolveLedgerPriceItem(order);
        var customer = _store.State.Customers.FirstOrDefault(x => !x.Deleted && x.Id == order.CustomerId);
        var group = CustomerPriceGroup(customer);
        if (group is null) return;
        if (item is not null)
        {
            var calculationWidthCm = order.AreaM2 > 0 ? 100m : order.WidthCm;
            var calculationHeightCm = order.AreaM2 > 0 ? order.AreaM2 * 100m : order.HeightCm;
            var result = PricingEngine.Calculate([item], new CalculationInput(calculationWidthCm, calculationHeightCm, order.LengthMeter, order.DurationMinutes, order.Quantity, order.ExchangeRate <= 0 ? _store.State.Settings.UsdTryRate : order.ExchangeRate), group.CostMultiplier, order.AlternativePercent, group.Id, _store.State.PriceGroups, _store.State.PriceItems);
            if (result.Lines.Count > 0)
            {
                order.CostTotalTl = result.CostTl; order.SaleTotalTl = result.SaleTl; order.Lines = result.Lines; order.Material = item.DisplayName; order.PriceGroupId = group.Id;
                return;
            }
        }
        var newBasis = GetOrderBasis(order);
        if (oldBasis > 0 && newBasis > 0)
        {
            var ratio = newBasis / oldBasis;
            order.CostTotalTl = decimal.Round(order.CostTotalTl * ratio, 2);
            order.SaleTotalTl = decimal.Round(order.SaleTotalTl * ratio, 2);
        }
    }

    private PriceItem? ResolveLedgerPriceItem(Order order)
    {
        // Cari tablosunda Malzeme hücresi değiştirilmişse yeni yazılan değer,
        // geçmiş sipariş satırındaki eski PriceItemId'den önceliklidir.
        var exactDisplay = _store.State.PriceItems.FirstOrDefault(x => !x.Deleted && x.Active && x.DisplayName.Equals(order.Material, StringComparison.CurrentCultureIgnoreCase));
        if (exactDisplay is not null) return exactDisplay;
        var exactName = _store.State.PriceItems.Where(x => !x.Deleted && x.Active && x.Name.Equals(order.Material, StringComparison.CurrentCultureIgnoreCase)).ToList();
        if (exactName.Count == 1) return exactName[0];
        return order.Lines.Select(line => _store.State.PriceItems.FirstOrDefault(x => x.Id == line.PriceItemId && !x.Deleted)).FirstOrDefault(x => x is not null);
    }

    private static decimal GetOrderBasis(Order order) => order.WidthCm > 0 && order.HeightCm > 0 ? order.WidthCm * order.HeightCm / 10000m : order.AreaM2 > 0 ? order.AreaM2 : order.LengthMeter > 0 ? order.LengthMeter : order.Quantity;

    private static bool TryApplyMeasure(Order order, string text)
    {
        var dimension = System.Text.RegularExpressions.Regex.Match(text, @"(?<w>\d+(?:[.,]\d+)?)\s*[x×]\s*(?<h>\d+(?:[.,]\d+)?)", System.Text.RegularExpressions.RegexOptions.IgnoreCase);
        if (dimension.Success && TryParseDecimal(dimension.Groups["w"].Value, out var width) && TryParseDecimal(dimension.Groups["h"].Value, out var height))
        {
            if (text.Contains("mm", StringComparison.OrdinalIgnoreCase)) { width /= 10m; height /= 10m; }
            order.WidthCm = width; order.HeightCm = height; order.AreaM2 = 0; order.LengthMeter = 0; return width > 0 && height > 0;
        }
        var squareMeter = System.Text.RegularExpressions.Regex.Match(text, @"(?<m2>\d+(?:[.,]\d+)?)\s*(?:m\s*[²2]|metrekare)(?:\s|$)", System.Text.RegularExpressions.RegexOptions.IgnoreCase);
        if (squareMeter.Success && TryParseDecimal(squareMeter.Groups["m2"].Value, out var area))
        {
            order.WidthCm = 0; order.HeightCm = 0; order.AreaM2 = area; order.LengthMeter = 0; return area > 0;
        }
        if (TryParseDecimal(text, out area) && area > 0)
        {
            order.WidthCm = 0; order.HeightCm = 0; order.AreaM2 = area; order.LengthMeter = 0; return true;
        }
        var meter = System.Text.RegularExpressions.Regex.Match(text, @"(?<m>\d+(?:[.,]\d+)?)\s*m(?:etre)?\b", System.Text.RegularExpressions.RegexOptions.IgnoreCase);
        if (meter.Success && TryParseDecimal(meter.Groups["m"].Value, out var length))
        {
            order.WidthCm = 0; order.HeightCm = 0; order.AreaM2 = 0; order.LengthMeter = length; return length > 0;
        }
        return false;
    }

    private static bool TryParseDecimal(string? text, out decimal value)
    {
        var normalized = (text ?? "").Trim().Replace(" ", "").Replace(".", ",");
        return decimal.TryParse(normalized, System.Globalization.NumberStyles.Number, new System.Globalization.CultureInfo("tr-TR"), out value);
    }

    private async Task DeleteSelectedLedgerMovementAsync()
    {
        if (_ledgerGrid.SelectedRows.Count == 0) { MessageBox.Show("Silmek için bir hareket seçin.", "Cari", MessageBoxButtons.OK, MessageBoxIcon.Information); return; }
        var row = _ledgerGrid.SelectedRows[0];
        var id = row.Cells["id"].Value?.ToString(); var kind = row.Cells["kind"].Value?.ToString();
        if (string.IsNullOrWhiteSpace(id)) return;
        if (MessageBox.Show("Seçili cari hareketi silinsin mi? Geri Al ile kurtarabilirsiniz.", "Hareketi Sil", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
        SyncEntity? entity = kind == "order" ? _store.State.Orders.FirstOrDefault(x => x.Id == id) : _store.State.Payments.FirstOrDefault(x => x.Id == id);
        if (entity is null) return;
        _store.CaptureUndo("Cari hareketi silindi"); entity.Deleted = true; _store.Touch(entity);
        await PersistAndSyncAsync("Cari hareketi silindi"); RefreshAll();
    }

    private async Task SavePaymentAsync()
    {
        var customer = _ledgerCustomer.SelectedItem as Customer;
        if (customer is null) { MessageBox.Show("Müşteri seçin.", "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
        if (_paymentAmount.Value <= 0) { MessageBox.Show("Tahsilat tutarı 0'dan büyük olmalıdır.", "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
        if (MessageBox.Show($"{customer.Name} için {_paymentAmount.Value:N2} TL tahsilat kaydedilsin mi?", "Yeni Tahsilatı Kaydet", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
        var payment = new Payment
        {
            CustomerId = customer.Id, AmountTl = _paymentAmount.Value, Date = DateTime.Today,
            PaymentType = _paymentType.SelectedItem?.ToString() ?? "Diğer",
            Description = string.IsNullOrWhiteSpace(_paymentDescription.Text) ? "Tahsilat" : _paymentDescription.Text.Trim(),
            DeviceId = _store.State.DeviceId
        };
        _store.CaptureUndo(customer.Name + " için tahsilat eklendi");
        _store.State.Payments.Add(payment);
        await PersistAndSyncAsync("Tahsilat: " + customer.Name);
        _paymentAmount.Value = 0; _paymentDescription.Text = "Tahsilat";
        RefreshAll();
    }

    private void CreateSelectedCustomerPdf()
    {
        var customer = _store.State.Customers.FirstOrDefault(x => x.Id == _selectedCustomerId && !x.Deleted);
        if (customer is null) { MessageBox.Show("PDF almak için tablodan bir müşteri seçin.", "Müşteri PDF", MessageBoxButtons.OK, MessageBoxIcon.Information); return; }
        CreateCustomerNote(customer, false);
    }

    private void ExportCustomerLedgerExcel()
    {
        var customer = _ledgerCustomer.SelectedItem as Customer;
        if (customer is null) { MessageBox.Show("Önce müşteri seçin.", "Müşteri Hesabı", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
        var filterByDate = _ledgerDateFilter.Checked;
        if (filterByDate && _ledgerFrom.Value.Date > _ledgerTo.Value.Date)
        {
            MessageBox.Show("Başlangıç tarihi bitiş tarihinden sonra olamaz.", "Müşteri Hesabı", MessageBoxButtons.OK, MessageBoxIcon.Warning); return;
        }
        var all = _store.GetLedger(customer.Id).ToList();
        var dated = all.Where(x => x.Date != DateTime.MinValue).Select(x => x.Date.Date).ToList();
        var from = filterByDate ? _ledgerFrom.Value.Date : dated.DefaultIfEmpty(DateTime.Today).Min();
        var to = filterByDate ? _ledgerTo.Value.Date : dated.DefaultIfEmpty(DateTime.Today).Max();
        var movements = all.Where(x => x.Date.Date >= from && x.Date.Date <= to).OrderBy(x => x.Date).ThenBy(x => x.Type).ToList();
        var safeName = string.Concat(customer.Name.Select(ch => Path.GetInvalidFileNameChars().Contains(ch) ? '_' : ch));
        using var dialog = new SaveFileDialog
        {
            Title = "Müşteri hesabını Excel olarak kaydet",
            Filter = "Excel çalışma kitabı (*.xlsx)|*.xlsx",
            DefaultExt = "xlsx",
            AddExtension = true,
            InitialDirectory = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),
            FileName = $"{safeName}_Hesap_Ozeti_{from:yyyyMMdd}_{to:yyyyMMdd}.xlsx"
        };
        if (dialog.ShowDialog(this) != DialogResult.OK) return;
        try
        {
            SimpleXlsx.ExportCustomerLedger(customer, movements, from, to, _store.GetBalance(customer.Id), dialog.FileName);
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(dialog.FileName) { UseShellExecute = true });
            MessageBox.Show($"Müşteri hesabı Excel olarak kaydedildi.\n\n{dialog.FileName}", "Excel Hazır", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex) { MessageBox.Show("Müşteri hesabı Excel'e aktarılamadı: " + ex.Message, "Müşteri Hesabı", MessageBoxButtons.OK, MessageBoxIcon.Error); }
    }

    private void CreateCustomerNote(Customer? requestedCustomer = null, bool useLedgerDateFilter = true)
    {
        var customer = requestedCustomer ?? _ledgerCustomer.SelectedItem as Customer;
        if (customer is null) { MessageBox.Show("Önce müşteri seçin.", "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
        var filterByDate = useLedgerDateFilter && _ledgerDateFilter.Checked;
        if (filterByDate && _ledgerFrom.Value.Date > _ledgerTo.Value.Date)
        {
            MessageBox.Show("Başlangıç tarihi bitiş tarihinden sonra olamaz.", "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Warning); return;
        }
        var all = _store.GetLedger(customer.Id).ToList();
        var dated = all.Where(x => x.Date != DateTime.MinValue).Select(x => x.Date.Date).ToList();
        var from = filterByDate ? _ledgerFrom.Value.Date : dated.DefaultIfEmpty(DateTime.Today).Min();
        var to = filterByDate ? _ledgerTo.Value.Date : dated.DefaultIfEmpty(DateTime.Today).Max();
        var movements = all.Where(x => x.Date.Date >= from && x.Date.Date <= to).OrderBy(x => x.Date).ThenBy(x => x.Type).ToList();
        if (movements.Count == 0)
        {
            MessageBox.Show("Seçilen tarih aralığında hareket bulunamadı.", "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Information); return;
        }
        try
        {
            var currentBalance = _store.GetBalance(customer.Id);
            var periodDebit = movements.Sum(x => x.Debit);
            var periodCredit = movements.Sum(x => x.Credit);
            var politeMessage = currentBalance > 0
                ? $"Sayın {customer.Name}, {from:dd.MM.yyyy}–{to:dd.MM.yyyy} tarihleri arasındaki hesap hareketlerinizi bilgilerinize sunuyoruz. Güncel bakiyeniz {currentBalance:N2} TL'dir. Uygun olduğunuzda ödeme konusunda desteğinizi rica eder, iyi çalışmalar dileriz. İzmirde Reklam"
                : $"Sayın {customer.Name}, {from:dd.MM.yyyy}–{to:dd.MM.yyyy} tarihleri arasındaki hesap hareketlerinizi bilgilerinize sunuyoruz. Ödemeleriniz için teşekkür eder, iyi çalışmalar dileriz. İzmirde Reklam";
            static string H(string value) => System.Net.WebUtility.HtmlEncode(value);
            var html = new System.Text.StringBuilder();
            html.Append("<!doctype html><html lang='tr'><head><meta charset='utf-8'><title>Hesap Özeti</title><style>");
            html.Append("*{box-sizing:border-box}body{font-family:'Segoe UI',Arial,sans-serif;font-size:13px;line-height:1.4;background:#f3f6f7;color:#173446;margin:0;padding:22px}.page{max-width:940px;margin:auto;background:#fff;border-radius:12px;box-shadow:0 8px 28px #1734461c;overflow:hidden}.head{background:#123548;color:#fff;padding:20px 28px}.brand{font-size:23px;font-weight:700}.sub{font-size:12px;color:#c7dde3;margin-top:2px}.content{padding:22px 28px}.meta{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:16px}.card{min-width:0;background:#eef8f6;border-left:4px solid #25a18e;padding:11px 13px;border-radius:7px;overflow-wrap:anywhere}.card b{font-size:11px;color:#55727e}.card small{font-size:10px;color:#687f89}.amount{font-size:18px;font-weight:700;color:#c66c38;white-space:nowrap}table{width:100%;table-layout:fixed;border-collapse:collapse;margin:16px 0;font-size:11px}th{background:#173f52;color:#fff;text-align:left;padding:8px 7px;font-size:10.5px}td{padding:7px;border-bottom:1px solid #dce5e8;vertical-align:top;overflow-wrap:anywhere;word-break:break-word}.num{text-align:right;white-space:nowrap}.message{background:#fff6e8;border-radius:8px;padding:13px 15px;line-height:1.5;font-size:12px}.foot{color:#687f89;font-size:9.5px;margin-top:14px}@media(max-width:720px){body{padding:8px}.content{padding:14px}.meta{grid-template-columns:1fr}.table-wrap{overflow-x:auto}table{min-width:720px}}@page{size:A4 landscape;margin:9mm}@media print{body{background:#fff;padding:0;font-size:10px}.page{max-width:none;box-shadow:none;border-radius:0}.head{padding:12px 16px}.brand{font-size:18px}.content{padding:12px 16px}.meta{gap:7px;margin-bottom:10px}.card{padding:7px 9px}.amount{font-size:14px}table{font-size:8.5px;margin:10px 0}th{font-size:8px;padding:5px}td{padding:5px}.message{font-size:9px;padding:8px 10px}.foot{font-size:7.5px;margin-top:8px}}</style></head><body><div class='page'>");
            html.Append($"<div class='head'><div class='brand'>İzmirde Reklam</div><div class='sub'>Müşteri Hesap Özeti</div></div><div class='content'><div class='meta'><div class='card'><b>Müşteri</b><br>{H(customer.Name)}<br><small>{H(customer.Company)}</small></div><div class='card'><b>Dönem</b><br>{from:dd.MM.yyyy} – {to:dd.MM.yyyy}<br><small>Belge tarihi: {DateTime.Now:dd.MM.yyyy HH:mm}</small></div><div class='card'><b>Güncel Bakiye</b><br><span class='amount'>{currentBalance:N2} TL</span></div></div>");
            html.Append("<div class='table-wrap'><table><colgroup><col style='width:10%'><col style='width:9%'><col style='width:27%'><col style='width:18%'><col style='width:12%'><col style='width:12%'><col style='width:12%'></colgroup><thead><tr><th>Tarih</th><th>Hareket</th><th>Açıklama</th><th>Malzeme</th><th>Ölçü</th><th class='num'>Borç</th><th class='num'>Tahsilat</th></tr></thead><tbody>");
            foreach (var row in movements)
                html.Append($"<tr><td>{(row.Date == DateTime.MinValue ? "" : row.Date.ToString("dd.MM.yyyy"))}</td><td>{H(row.Type)}</td><td>{H(row.Description)}</td><td>{H(row.Material)}</td><td>{H(row.Measure)}</td><td class='num'>{(row.Debit == 0 ? "" : row.Debit.ToString("N2") + " TL")}</td><td class='num'>{(row.Credit == 0 ? "" : row.Credit.ToString("N2") + " TL")}</td></tr>");
            html.Append($"</tbody><tfoot><tr><th colspan='5'>Dönem Toplamı</th><th class='num'>{periodDebit:N2} TL</th><th class='num'>{periodCredit:N2} TL</th></tr></tfoot></table></div><div class='message'>{H(politeMessage)}</div><div class='foot'>Bu belge BTakip tarafından mevcut kayıtlar değiştirilmeden hazırlanmıştır.</div></div></div></body></html>");
            var safeName = string.Concat(customer.Name.Select(ch => Path.GetInvalidFileNameChars().Contains(ch) ? '_' : ch));
            using var dialog = new SaveFileDialog
            {
                Title = "Müşteri hesap özetini PDF olarak kaydet",
                Filter = "PDF Belgesi (*.pdf)|*.pdf",
                DefaultExt = "pdf",
                AddExtension = true,
                InitialDirectory = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),
                FileName = $"{safeName}_Hesap_Ozeti_{from:yyyyMMdd}_{to:yyyyMMdd}.pdf"
            };
            if (dialog.ShowDialog(this) != DialogResult.OK) return;
            SaveHtmlAsPdf(html.ToString(), dialog.FileName);
            Clipboard.SetText(politeMessage);
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(dialog.FileName) { UseShellExecute = true });
            MessageBox.Show($"Müşteriye gönderebileceğiniz PDF hazırlandı.\n\nKaydedildiği yer:\n{dialog.FileName}\n\nBu PDF'yi WhatsApp veya e-postaya dosya olarak ekleyebilirsiniz. Mesaj metni de panoya kopyalandı.", "Müşteri PDF Hazır", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex) { MessageBox.Show("Müşteri PDF'i hazırlanamadı: " + ex.Message, "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Error); }
    }

    private void ExportCustomerTablePdf()
    {
        if (_customerGrid.Rows.Count == 0) { MessageBox.Show("Çıktı alınacak müşteri bulunamadı.", "Müşteri Tablosu", MessageBoxButtons.OK, MessageBoxIcon.Information); return; }
        using var dialog = new SaveFileDialog
        {
            Title = "Müşteri tablosunu PDF olarak kaydet",
            Filter = "PDF Belgesi (*.pdf)|*.pdf",
            DefaultExt = "pdf",
            AddExtension = true,
            InitialDirectory = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),
            FileName = $"Musteri_Tablosu_{DateTime.Now:yyyyMMdd}.pdf"
        };
        if (dialog.ShowDialog(this) != DialogResult.OK) return;
        try
        {
            static string H(string value) => System.Net.WebUtility.HtmlEncode(value);
            var html = new System.Text.StringBuilder();
            html.Append("<!doctype html><html lang='tr'><head><meta charset='utf-8'><title>Müşteri Tablosu</title><style>*{box-sizing:border-box}body{font-family:'Segoe UI',Arial,sans-serif;color:#173446;margin:0;padding:22px;font-size:12px}h1{font-size:21px;margin:0;color:#123548}.sub{color:#687f89;margin:4px 0 16px}table{width:100%;table-layout:fixed;border-collapse:collapse}th{background:#173f52;color:#fff;text-align:left;padding:8px}td{padding:7px 8px;border-bottom:1px solid #dce5e8;overflow-wrap:anywhere}th:last-child,td:last-child{text-align:right;white-space:nowrap}tr:nth-child(even){background:#f5f8f8}@page{size:A4 landscape;margin:10mm}@media print{body{padding:0;font-size:9px}h1{font-size:16px}.sub{margin-bottom:9px}th,td{padding:5px}}</style></head><body>");
            html.Append($"<h1>İzmirde Reklam - Müşteri Tablosu</h1><div class='sub'>Çıktı tarihi: {DateTime.Now:dd.MM.yyyy HH:mm}</div><table><colgroup><col style='width:25%'><col style='width:23%'><col style='width:20%'><col style='width:17%'><col style='width:15%'></colgroup><thead><tr><th>Müşteri</th><th>Firma</th><th>Fiyat Grubu</th><th>Telefon</th><th>Bakiye</th></tr></thead><tbody>");
            foreach (DataGridViewRow row in _customerGrid.Rows)
                html.Append($"<tr><td>{H(row.Cells["name"].Value?.ToString() ?? "")}</td><td>{H(row.Cells["company"].Value?.ToString() ?? "")}</td><td>{H(row.Cells["group"].Value?.ToString() ?? "")}</td><td>{H(row.Cells["phone"].Value?.ToString() ?? "")}</td><td>{H(row.Cells["balance"].FormattedValue?.ToString() ?? "")} TL</td></tr>");
            html.Append("</tbody></table></body></html>");
            SaveHtmlAsPdf(html.ToString(), dialog.FileName);
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(dialog.FileName) { UseShellExecute = true });
            MessageBox.Show($"Müşteri tablosu PDF olarak kaydedildi.\n\n{dialog.FileName}", "PDF Hazır", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex) { MessageBox.Show("Müşteri tablosu PDF'i hazırlanamadı: " + ex.Message, "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Error); }
    }

    private void ExportAllCustomerAccountsPdf()
    {
        var customers = _store.State.Customers.Where(x => !x.Deleted).OrderBy(x => x.Name).ToList();
        if (customers.Count == 0) { MessageBox.Show("Dışa aktarılacak müşteri bulunamadı.", "Tüm Hesaplar", MessageBoxButtons.OK, MessageBoxIcon.Information); return; }
        using var dialog = new SaveFileDialog
        {
            Title = "Tüm müşteri hesaplarını PDF olarak kaydet",
            Filter = "PDF Belgesi (*.pdf)|*.pdf",
            DefaultExt = "pdf",
            AddExtension = true,
            InitialDirectory = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),
            FileName = $"BTakip_Tum_Hesaplar_{DateTime.Now:yyyyMMdd_HHmm}.pdf"
        };
        if (dialog.ShowDialog(this) != DialogResult.OK) return;
        try
        {
            static string H(string value) => System.Net.WebUtility.HtmlEncode(value);
            var html = new System.Text.StringBuilder();
            html.Append("<!doctype html><html lang='tr'><head><meta charset='utf-8'><title>Tüm Müşteri Hesapları</title><style>*{box-sizing:border-box}body{font-family:'Segoe UI',Arial,sans-serif;color:#173446;margin:0;padding:18px;font-size:11px}.account{page-break-after:always}.account:last-child{page-break-after:auto}h1{font-size:20px;margin:0;color:#123548}h2{font-size:15px;margin:14px 0 4px;color:#123548}.meta{color:#687f89;margin:3px 0 10px}.balance{font-weight:700;color:#c66c38;margin:4px 0 10px}table{width:100%;table-layout:fixed;border-collapse:collapse}th{background:#173f52;color:#fff;text-align:left;padding:6px;font-size:9px}td{padding:5px;border-bottom:1px solid #dce5e8;vertical-align:top;overflow-wrap:anywhere}.num{text-align:right;white-space:nowrap}.empty{color:#687f89;padding:12px 0}@page{size:A4 landscape;margin:9mm}@media print{body{padding:0;font-size:9px}h1{font-size:16px}h2{font-size:12px;margin-top:9px}th{font-size:7.5px;padding:4px}td{padding:4px}}</style></head><body>");
            foreach (var customer in customers)
            {
                var movements = _store.GetLedger(customer.Id).OrderBy(x => x.Date).ThenBy(x => x.Type).ToList();
                var debit = movements.Sum(x => x.Debit); var credit = movements.Sum(x => x.Credit);
                html.Append($"<section class='account'><h1>İzmirde Reklam - Müşteri Hesapları</h1><h2>{H(customer.Name)}</h2><div class='meta'>{H(customer.Company)} &nbsp; {H(customer.Phone)}</div><div class='balance'>Güncel bakiye: {_store.GetBalance(customer.Id):N2} TL &nbsp; | &nbsp; Toplam borç: {debit:N2} TL &nbsp; | &nbsp; Toplam tahsilat: {credit:N2} TL</div>");
                if (movements.Count == 0) html.Append("<div class='empty'>Kayıtlı cari hareket bulunmuyor.</div>");
                else
                {
                    html.Append("<table><colgroup><col style='width:11%'><col style='width:10%'><col style='width:29%'><col style='width:18%'><col style='width:12%'><col style='width:10%'><col style='width:10%'></colgroup><thead><tr><th>Tarih</th><th>Hareket</th><th>Açıklama</th><th>Malzeme</th><th>Ölçü</th><th class='num'>Borç</th><th class='num'>Tahsilat</th></tr></thead><tbody>");
                    foreach (var row in movements)
                        html.Append($"<tr><td>{(row.Date == DateTime.MinValue ? "" : row.Date.ToString("dd.MM.yyyy"))}</td><td>{H(row.Type)}</td><td>{H(row.Description)}</td><td>{H(row.Material)}</td><td>{H(row.Measure)}</td><td class='num'>{(row.Debit == 0 ? "" : row.Debit.ToString("N2") + " TL")}</td><td class='num'>{(row.Credit == 0 ? "" : row.Credit.ToString("N2") + " TL")}</td></tr>");
                    html.Append("</tbody></table>");
                }
                html.Append("</section>");
            }
            html.Append("</body></html>");
            SaveHtmlAsPdf(html.ToString(), dialog.FileName);
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(dialog.FileName) { UseShellExecute = true });
            MessageBox.Show($"Tüm müşteri hesapları PDF olarak kaydedildi.\n\n{dialog.FileName}", "PDF Hazır", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex) { MessageBox.Show("Tüm hesaplar PDF'e aktarılamadı: " + ex.Message, "Tüm Hesaplar", MessageBoxButtons.OK, MessageBoxIcon.Error); }
    }

    private static void SaveHtmlAsPdf(string html, string pdfPath)
    {
        var edgePath = FindEdgePath() ?? throw new InvalidOperationException("PDF oluşturmak için Microsoft Edge bulunamadı.");
        var tempHtml = Path.Combine(Path.GetTempPath(), "btakip-pdf-" + Guid.NewGuid().ToString("N") + ".html");
        try
        {
            File.WriteAllText(tempHtml, html, new System.Text.UTF8Encoding(false));
            if (File.Exists(pdfPath)) File.Delete(pdfPath);
            var startInfo = new System.Diagnostics.ProcessStartInfo(edgePath)
            {
                UseShellExecute = false,
                CreateNoWindow = true,
                WindowStyle = System.Diagnostics.ProcessWindowStyle.Hidden
            };
            startInfo.ArgumentList.Add("--headless");
            startInfo.ArgumentList.Add("--disable-gpu");
            startInfo.ArgumentList.Add("--no-pdf-header-footer");
            startInfo.ArgumentList.Add("--print-to-pdf=" + pdfPath);
            startInfo.ArgumentList.Add(new Uri(tempHtml).AbsoluteUri);
            using var process = System.Diagnostics.Process.Start(startInfo) ?? throw new InvalidOperationException("PDF dönüştürücü başlatılamadı.");
            var deadline = DateTime.UtcNow.AddSeconds(30);
            while (DateTime.UtcNow < deadline && (!File.Exists(pdfPath) || new FileInfo(pdfPath).Length == 0)) Thread.Sleep(100);
            if (!File.Exists(pdfPath) || new FileInfo(pdfPath).Length == 0) throw new InvalidOperationException("PDF dosyası oluşturulamadı.");
            if (!process.HasExited) process.Kill(true);
        }
        finally
        {
            try { if (File.Exists(tempHtml)) File.Delete(tempHtml); } catch { }
        }
    }

    private static string? FindEdgePath()
    {
        var candidates = new[]
        {
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "Microsoft", "Edge", "Application", "msedge.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Microsoft", "Edge", "Application", "msedge.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Microsoft", "Edge", "Application", "msedge.exe")
        };
        return candidates.FirstOrDefault(File.Exists);
    }

    private void LoadSettingsControls()
    {
        if (_syncUrl is null) return;
        var s = _store.State.Settings;
        if (!_syncUrl.Focused) _syncUrl.Text = s.GoogleWebAppUrl;
        if (!_syncToken.Focused) _syncToken.Text = s.GoogleSyncToken;
        if (!_syncInterval.Focused) _syncInterval.Value = Math.Clamp(s.SyncIntervalSeconds, (int)_syncInterval.Minimum, (int)_syncInterval.Maximum);
        if (!_usdRate.Focused) _usdRate.Value = Clamp(_usdRate, s.UsdTryRate);
        _autoRate.Checked = s.AutoExchangeRate; _startWindows.Checked = s.StartWithWindows;
        _syncStatus.Text = s.LastSyncUtc.HasValue
            ? $"Son başarılı senkron: {s.LastSyncUtc.Value.ToLocalTime():dd.MM.yyyy HH:mm:ss}"
            : "Henüz Google senkronizasyonu yapılmadı.";
        _securityStatus.Text = _store.SecurityStatus;
        _securityStatus.ForeColor = _store.ApplicationIntegrityOk ? UiTheme.Teal : Color.Firebrick;
    }

    private async Task SaveSettingsAsync()
    {
        var s = _store.State.Settings;
        _store.CaptureUndo("Senkron ve yedek ayarları değiştirildi");
        s.GoogleWebAppUrl = _syncUrl.Text.Trim(); s.GoogleSyncToken = _syncToken.Text.Trim();
        s.SyncIntervalSeconds = (int)_syncInterval.Value; s.UsdTryRate = _usdRate.Value;
        s.AutoExchangeRate = _autoRate.Checked; s.StartWithWindows = _startWindows.Checked;
        ConfigureWindowsStartup(s.StartWithWindows);
        ConfigureSyncTimer();
        await _store.SaveAsync("Ayarlar güncellendi");
        RefreshAll();
        if (!string.IsNullOrWhiteSpace(s.GoogleWebAppUrl)) await RunSyncAsync(true);
    }

    private void ConfigureSyncTimer()
    {
        _syncTimer.Stop();
        _syncTimer.Interval = Math.Clamp(_store.State.Settings.SyncIntervalSeconds, 15, 3600) * 1000;
        _syncTimer.Tick -= SyncTimer_Tick;
        _syncTimer.Tick += SyncTimer_Tick;
        _syncTimer.Start();
    }

    private async void SyncTimer_Tick(object? sender, EventArgs e) => await RunSyncAsync(false);

    private async Task RunSyncAsync(bool showResult)
    {
        if (_syncRunning) return;
        if (string.IsNullOrWhiteSpace(_store.State.Settings.GoogleWebAppUrl))
        {
            _syncBadge.Text = "● Yerel — Google kurulmadı";
            _syncBadge.ForeColor = Color.FromArgb(255, 205, 125);
            if (showResult) MessageBox.Show("Google Sheets bağlantı adresi henüz girilmedi. Yerel kayıt ve Excel yedeği çalışmaya devam ediyor.", "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        _syncRunning = true;
        _syncBadge.Text = "● Eşitleniyor…"; _syncBadge.ForeColor = Color.White;
        try
        {
            var status = await _sync.SyncAsync();
            _syncStatus.Text = status.Message;
            _syncBadge.Text = status.Success ? "● Google ile güncel" : "● Google bekliyor";
            _syncBadge.ForeColor = status.Success ? Color.FromArgb(155, 226, 205) : Color.FromArgb(255, 205, 125);
            if (status.Received > 0) RefreshAll();
            if (showResult) MessageBox.Show(status.Message, "BTakip Senkron", MessageBoxButtons.OK, status.Success ? MessageBoxIcon.Information : MessageBoxIcon.Warning);
        }
        finally { _syncRunning = false; }
    }

    private async Task RefreshExchangeRateAsync(bool showResult)
    {
        var rate = await _sync.FetchTcmbUsdRateAsync();
        if (rate.HasValue)
        {
            if (showResult) _store.CaptureUndo("USD/TL kuru elle güncellendi");
            _store.State.Settings.UsdTryRate = rate.Value;
            if (_usdRate is not null) _usdRate.Value = Clamp(_usdRate, rate.Value);
            if (_calcRate is not null) _calcRate.Value = Clamp(_calcRate, rate.Value);
            await _store.SaveAsync("TCMB USD kuru güncellendi");
            if (showResult) MessageBox.Show($"USD/TL kuru {rate.Value:N4} olarak güncellendi.", "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        else if (showResult) MessageBox.Show("TCMB kuru şu anda alınamadı. Mevcut kur korunuyor.", "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Warning);
    }

    private async Task PersistAndSyncAsync(string reason)
    {
        await _store.SaveAsync(reason);
        RefreshDashboard();
        _ = RunSyncAsync(false);
    }

    private async Task UndoLastChangeAsync()
    {
        if (!_store.CanUndo)
        {
            MessageBox.Show("Geri alınabilecek bir işlem bulunmuyor.", "Geri Al", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        var description = _store.UndoDescription;
        if (MessageBox.Show($"Son işlem geri alınacak:\n\n{description}\n\nDevam edilsin mi?", "Geri Al", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
        try
        {
            var undone = await _store.UndoLastAsync();
            RefreshAll();
            _ = RunSyncAsync(false);
            MessageBox.Show($"İşlem geri alındı: {undone}", "Geri Alındı", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex) { MessageBox.Show("İşlem geri alınamadı: " + ex.Message, "Geri Al", MessageBoxButtons.OK, MessageBoxIcon.Error); }
    }

    private async Task<ConflictDecision> ResolveConflictAsync(ConflictRecord conflict)
    {
        if (InvokeRequired)
        {
            var tcs = new TaskCompletionSource<ConflictDecision>();
            BeginInvoke(async () => tcs.SetResult(await ResolveConflictAsync(conflict)));
            return await tcs.Task;
        }
        var answer = MessageBox.Show(
            "Aynı kayıt hem bu bilgisayarda hem Google tablosunda değişmiş.\n\nEvet: Google sürümünü kullan\nHayır: Bu PC sürümünü kullan\nİptal: İki sürümü de ayrı kayıt olarak koru",
            "Senkronizasyon Çakışması", MessageBoxButtons.YesNoCancel, MessageBoxIcon.Warning);
        return answer switch
        {
            DialogResult.Yes => ConflictDecision.UseGoogle,
            DialogResult.No => ConflictDecision.UsePc,
            DialogResult.Cancel => ConflictDecision.KeepBoth,
            _ => ConflictDecision.Skip
        };
    }

    private void ExportExcel()
    {
        using var dialog = new SaveFileDialog
        {
            Title = "BTakip Excel Dışa Aktarım",
            Filter = "Excel çalışma kitabı (*.xlsx)|*.xlsx",
            FileName = $"BTakip_Tum_Veriler_{DateTime.Now:yyyyMMdd_HHmm}.xlsx",
            InitialDirectory = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments)
        };
        if (dialog.ShowDialog(this) != DialogResult.OK) return;
        try
        {
            SimpleXlsx.Export(_store.State, dialog.FileName);
            MessageBox.Show("Müşteriler, fiyatlar, siparişler ve tahsilatlar tek Excel dosyasına aktarıldı.", "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex) { MessageBox.Show("Excel oluşturulamadı: " + ex.Message, "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Error); }
    }

    private async Task ImportExcelAsync(bool appendOnly = false, bool convertLegacy = false)
    {
        using var dialog = new OpenFileDialog { Title = convertLegacy ? "Eski Excel'i BTakip'e Dönüştür" : "BTakip Excel İçe Aktarım", Filter = "Excel çalışma kitabı (*.xlsx)|*.xlsx" };
        if (dialog.ShowDialog(this) != DialogResult.OK) return;
        ExcelConversionPreview? conversionPreview = null;
        if (convertLegacy)
        {
            try
            {
                conversionPreview = SimpleXlsx.AnalyzeConversion(dialog.FileName, _store.State);
                if (conversionPreview.Movements.Count == 0)
                {
                    MessageBox.Show("Bu dosyada dönüştürülebilecek gerçek bir hareket listesi bulunamadı.", "Excel'i Dönüştür", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    return;
                }
                if (!ShowExcelConversionPreview(conversionPreview, Path.GetFileName(dialog.FileName))) return;
            }
            catch (Exception ex)
            {
                MessageBox.Show("Excel okunamadı: " + ex.Message, "Excel'i Dönüştür", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }
        }

        var prompt = appendOnly
            ? "Excel dosyasındaki yalnız yeni kayıtlar mevcut cari tablosuna eklenecek. Önceki bilgiler silinmeyecek veya değiştirilmeyecek. Devam edilsin mi?"
            : "Seçilen dosyadaki kayıtlar BTakip'e kopyalanacak. Kaynak Excel dosyası değiştirilmeyecek. Devam edilsin mi?";
        if (!convertLegacy && MessageBox.Show(prompt, appendOnly ? "Excel'den Cariye Ekle" : "Excel İçe Aktar", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
        try
        {
            await _store.SaveAsync("Excel içe aktarma öncesi güvenlik kopyası");
            _store.CaptureUndo("Excel içe aktarması yapıldı");
            var report = convertLegacy ? SimpleXlsx.ImportConversion(conversionPreview!, _store, true) : SimpleXlsx.Import(dialog.FileName, _store, appendOnly);
            await PersistAndSyncAsync(convertLegacy ? "Eski Excel dönüştürülerek cariye eklendi" : appendOnly ? "Excel'den cariye yeni kayıtlar eklendi" : "Excel içe aktarma");
            RefreshAll();
            MessageBox.Show(report.ToString(), convertLegacy ? "Dönüştürme Tamamlandı" : "İçe Aktarma Tamamlandı", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex) { MessageBox.Show("Excel içe aktarılamadı: " + ex.Message, "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Error); }
    }

    private bool ShowExcelConversionPreview(ExcelConversionPreview preview, string fileName)
    {
        using var dialog = new Form
        {
            Text = "Excel Dönüştürme Önizlemesi",
            Width = 1360,
            Height = 720,
            MinimumSize = new Size(900, 560),
            StartPosition = FormStartPosition.CenterParent,
            BackColor = Color.White,
            Font = Font,
            ShowIcon = false
        };

        var layout = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            ColumnCount = 1,
            RowCount = 3,
            Padding = new Padding(18),
            BackColor = Color.White
        };
        layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));

        var usedSheets = preview.UsedSheets.Count == 0 ? "Yok" : string.Join(", ", preview.UsedSheets);
        var ignoredSheets = preview.IgnoredSheets.Count == 0 ? "Yok" : string.Join(", ", preview.IgnoredSheets);
        var priced = preview.Movements.Count(x => !string.IsNullOrWhiteSpace(x.PriceItemId));
        var summary = UiTheme.Label(
            $"{fileName}\n{preview.SourceRows} kaynak satırı bulundu; {preview.Movements.Count} hareket eklenmeye hazır.\n" +
            $"Kullanılan sayfa: {usedSheets}\nKullanılmayan sayfalar: {ignoredSheets}\n\n" +
            $"{priced} satış BTakip fiyat motoruyla hesaplandı. Eşleşmeyen ürünler kaynak bilgileri korunarak ayrıca belirtilir.\n\n" +
            "Aşağıdaki listeyi kontrol edin. Excel'i Ekle düğmesine basılana kadar hiçbir kayıt eklenmez. Aynı kayıtlar yeniden eklenmez.");
        summary.Dock = DockStyle.Fill;
        summary.MaximumSize = new Size(1300, 0);
        summary.Margin = new Padding(3, 3, 3, 14);
        layout.Controls.Add(summary, 0, 0);

        var grid = UiTheme.Grid();
        AddGridColumn(grid, "source", "Kaynak Satır", true, 75);
        AddGridColumn(grid, "date", "Tarih", true, 75);
        AddGridColumn(grid, "movement", "Hareket", true, 65);
        AddGridColumn(grid, "description", "Açıklama", true, 220);
        AddGridColumn(grid, "material", "Malzeme", true, 135);
        AddGridColumn(grid, "measure", "Ölçü", true, 90);
        AddGridColumn(grid, "cost", "Maliyet", true, 75, "N2");
        AddGridColumn(grid, "debit", "Borç", true, 75, "N2");
        AddGridColumn(grid, "credit", "Tahsilat", true, 75, "N2");
        AddGridColumn(grid, "pricing", "Hesap", true, 170);
        foreach (var movement in preview.Movements)
        {
            grid.Rows.Add($"{movement.SourceSheet} / {movement.SourceRow}",
                movement.Date == DateTime.MinValue ? "" : movement.Date.ToString("dd.MM.yyyy"),
                movement.Movement, movement.Description, movement.Material, movement.Measure,
                movement.CostTotalTl == 0 ? "" : movement.CostTotalTl, movement.Debit, movement.Credit, movement.PricingStatus);
        }
        layout.Controls.Add(grid, 0, 1);

        var buttons = new FlowLayoutPanel
        {
            Dock = DockStyle.Fill,
            FlowDirection = FlowDirection.RightToLeft,
            AutoSize = true,
            Padding = new Padding(0, 12, 0, 0)
        };
        var add = UiTheme.Button("Excel'i Ekle");
        add.DialogResult = DialogResult.OK;
        var cancel = UiTheme.Button("Vazgeç", false);
        cancel.DialogResult = DialogResult.Cancel;
        buttons.Controls.Add(add);
        buttons.Controls.Add(cancel);
        layout.Controls.Add(buttons, 0, 2);

        dialog.Controls.Add(layout);
        dialog.AcceptButton = add;
        dialog.CancelButton = cancel;
        return dialog.ShowDialog(this) == DialogResult.OK;
    }

    private async Task CreateFullBackupAsync()
    {
        using var dialog = new SaveFileDialog
        {
            Title = "BTakip Tek Dosyalık Tam Yedek",
            Filter = "BTakip tam yedek (*.btakip)|*.btakip",
            FileName = $"BTakip_Tam_Yedek_{DateTime.Now:yyyyMMdd_HHmm}.btakip",
            InitialDirectory = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory)
        };
        if (dialog.ShowDialog(this) != DialogResult.OK) return;
        try
        {
            await _store.SaveAsync("Tam yedek öncesi kayıt");
            _store.ExportFullBackup(dialog.FileName);
            MessageBox.Show("Müşteriler, fiyatlar, siparişler, tahsilatlar ve ayarlar tek dosyaya yedeklendi.", "Tam Yedek Hazır", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex) { MessageBox.Show("Tam yedek oluşturulamadı: " + ex.Message, "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Error); }
    }

    private async Task RestoreFullBackupAsync()
    {
        using var dialog = new OpenFileDialog { Title = "BTakip Tam Yedek Yükle", Filter = "BTakip tam yedek (*.btakip)|*.btakip" };
        if (dialog.ShowDialog(this) != DialogResult.OK) return;
        if (MessageBox.Show("Bu tek dosyadaki tüm müşteri, fiyat, sipariş, tahsilat ve ayarlar bu bilgisayara yüklenecek. Mevcut kayıtların güvenlik kopyası alınacak. Devam edilsin mi?", "Tam Yedek Yükle", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
        try
        {
            await _store.SaveAsync("Tam yedek yükleme öncesi güvenlik kopyası");
            _store.CaptureUndo("Tam yedek yüklendi");
            await _store.ImportFullBackupAsync(dialog.FileName);
            RefreshAll(); _ = RunSyncAsync(false);
            MessageBox.Show("Tam yapı yüklendi. Bu bilgisayar önceki bilgisayarın kaldığı yerden devam edebilir.", "Yedek Yüklendi", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex) { MessageBox.Show("Tam yedek yüklenemedi: " + ex.Message, "BTakip", MessageBoxButtons.OK, MessageBoxIcon.Error); }
    }

    private void ConfigureWindowsStartup(bool enabled)
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Run", true);
            if (enabled) key?.SetValue("BTakip", $"\"{Application.ExecutablePath}\" --tray");
            else key?.DeleteValue("BTakip", false);
        }
        catch (Exception ex) { _ = _store.AppendLogAsync("Windows başlangıç ayarı: " + ex.Message); }
    }

    private ContextMenuStrip BuildTrayMenu()
    {
        var menu = new ContextMenuStrip();
        menu.Items.Add("İzmirde Reklam'ı Aç", null, (_, _) => RestoreWindow());
        menu.Items.Add("Şimdi Eşitle", null, async (_, _) => await RunSyncAsync(true));
        menu.Items.Add("Yedek Klasörünü Aç", null, (_, _) => OpenPath(_store.RootPath));
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add("Çıkış", null, (_, _) => { _exitRequested = true; Close(); });
        return menu;
    }

    public void RestoreFromExternalLaunch()
    {
        if (InvokeRequired) { BeginInvoke((Action)RestoreFromExternalLaunch); return; }
        RestoreWindow();
    }

    private void RestoreWindow()
    {
        ShowInTaskbar = true;
        Show();
        WindowState = FormWindowState.Normal;
        BringToFront();
        Activate();
    }

    private async void Tabs_Selecting(object? sender, TabControlCancelEventArgs e)
    {
        if (_changingTabs || e.TabPageIndex == _tabs.SelectedIndex || !HasUnsavedChanges(_tabs.SelectedIndex)) return;
        e.Cancel = true;
        if (_unsavedPromptOpen) return;
        _unsavedPromptOpen = true;
        var proceed = await ConfirmUnsavedChangesAsync(_tabs.SelectedIndex);
        _unsavedPromptOpen = false;
        if (!proceed) return;
        _changingTabs = true;
        _tabs.SelectedIndex = e.TabPageIndex;
        _changingTabs = false;
    }

    private async void PriceGrid_SelectionChanged(object? sender, EventArgs e)
    {
        if (_changingPriceSelection || _priceGrid.SelectedRows.Count == 0) return;
        var targetId = _priceGrid.SelectedRows[0].Cells["id"].Value?.ToString();
        if (string.IsNullOrWhiteSpace(targetId)) return;
        if (targetId == _selectedPriceId || !HasPriceEditorChanges()) { LoadSelectedPrice(); return; }

        var previousId = _selectedPriceId;
        _changingPriceSelection = true;
        var proceed = await ConfirmUnsavedChangesAsync(2);
        if (proceed)
        {
            SelectPriceGridRow(targetId);
            LoadSelectedPrice();
        }
        else SelectPriceGridRow(previousId);
        _changingPriceSelection = false;
    }

    private void SelectPriceGridRow(string? id)
    {
        _priceGrid.ClearSelection();
        if (string.IsNullOrWhiteSpace(id)) return;
        var row = _priceGrid.Rows.Cast<DataGridViewRow>().FirstOrDefault(x => x.Cells["id"].Value?.ToString() == id);
        if (row is not null) row.Selected = true;
    }

    private bool HasUnsavedChanges(int tabIndex) => tabIndex switch
    {
        1 => HasCustomerEditorChanges(),
        2 => HasPriceEditorChanges(),
        5 => HasProfitEditorChanges(),
        6 => HasSettingsEditorChanges(),
        _ => false
    };

    private bool HasCustomerEditorChanges()
    {
        var customer = _store.State.Customers.FirstOrDefault(x => !x.Deleted && x.Id == _selectedCustomerId);
        if (customer is null)
            return !string.IsNullOrWhiteSpace(_customerName.Text) || !string.IsNullOrWhiteSpace(_customerCompany.Text) ||
                   !string.IsNullOrWhiteSpace(_customerPhone.Text) || !string.IsNullOrWhiteSpace(_customerEmail.Text) || !string.IsNullOrWhiteSpace(_customerNotes.Text);
        return customer.Name != _customerName.Text.Trim() || customer.Company != _customerCompany.Text.Trim() ||
               customer.Phone != _customerPhone.Text.Trim() || customer.Email != _customerEmail.Text.Trim() ||
               customer.Notes != _customerNotes.Text.Trim() || customer.PriceGroupId != ((_customerGroup.SelectedItem as PriceGroup)?.Id ?? "retail");
    }

    private bool HasPriceEditorChanges()
    {
        var item = _store.State.PriceItems.FirstOrDefault(x => !x.Deleted && x.Id == _selectedPriceId);
        var currency = _priceCurrency.SelectedItem?.ToString() ?? "TL";
        var formula = _priceFormula.SelectedValue?.ToString() ?? PricingFormula.SquareMeter;
        var baseMaterialId = (_priceBaseMaterial.SelectedItem as PriceItem)?.Id ?? "";
        var serviceFormula = _priceServiceFormula.SelectedValue?.ToString() ?? PricingFormula.SquareMeter;
        if (item is null)
            return !string.IsNullOrWhiteSpace(_priceName.Text) || !string.IsNullOrWhiteSpace(_priceVariant.Text) || _priceCost.Value != 0 ||
                   _priceSecondary.Value != 0 || _priceSheetWidth.Value != 0 || _priceSheetHeight.Value != 0 || _priceThickness.Value != 0 ||
                   !string.IsNullOrWhiteSpace(baseMaterialId) || _pricePrintEnabled.Checked ||
                   !string.IsNullOrWhiteSpace(_priceServiceName.Text) || _priceServiceCost.Value != 0 || !(_priceActive.Checked) ||
                   _priceUnit.Text.Trim() != "m²" || currency != "TL" || formula != PricingFormula.SquareMeter || PriceProfitInputsChanged(null);
        return item.Name != _priceName.Text.Trim() || item.Variant != _priceVariant.Text.Trim() ||
               item.Unit != _priceUnit.Text.Trim() || item.Currency != currency || item.Formula != formula ||
               item.UnitCost != _priceCost.Value || item.SecondaryCost != _priceSecondary.Value || item.SheetWidthCm != _priceSheetWidth.Value ||
               item.SheetHeightCm != _priceSheetHeight.Value || item.ThicknessMm != _priceThickness.Value ||
               item.BaseMaterialPriceItemId != baseMaterialId || item.IsPrintProduct != _pricePrintEnabled.Checked ||
               PriceProfitInputsChanged(item) || item.Active != _priceActive.Checked;
    }

    private bool HasProfitEditorChanges()
    {
        var group = _store.State.PriceGroups.FirstOrDefault(x => !x.Deleted && x.Id == _selectedGroupId);
        var groupDirty = group is not null && (group.Name != _groupName.Text.Trim() || (group.CostMultiplier - 1m) * 100m != _groupProfitPercent.Value);
        var item = _profitPriceItem.SelectedItem as PriceItem;
        var itemGroup = _profitItemGroup.SelectedItem as PriceGroup;
        var savedSpecial = PricingEngine.GetSpecialProfitPercent(item, itemGroup?.Id);
        var itemDirty = item is not null && itemGroup is not null &&
                        (_profitUseSpecial.Checked != savedSpecial.HasValue || (_profitUseSpecial.Checked && savedSpecial != _profitSpecialPercent.Value));
        return groupDirty || itemDirty;
    }

    private bool HasSettingsEditorChanges()
    {
        var settings = _store.State.Settings;
        return settings.GoogleWebAppUrl != _syncUrl.Text.Trim() || settings.GoogleSyncToken != _syncToken.Text.Trim() ||
               settings.SyncIntervalSeconds != (int)_syncInterval.Value || settings.UsdTryRate != _usdRate.Value ||
               settings.AutoExchangeRate != _autoRate.Checked || settings.StartWithWindows != _startWindows.Checked;
    }

    private async Task<bool> ConfirmUnsavedChangesAsync(int tabIndex)
    {
        if (!HasUnsavedChanges(tabIndex)) return true;
        var pageName = tabIndex >= 0 && tabIndex < _tabs.TabPages.Count ? _tabs.TabPages[tabIndex].Text : "Bu sayfa";
        var answer = MessageBox.Show(
            $"{pageName} sayfasında kaydedilmemiş değişiklikler var.\n\nDeğişiklikler kaydedilsin mi?",
            "Kaydedilmemiş Değişiklik", MessageBoxButtons.YesNoCancel, MessageBoxIcon.Question);
        if (answer == DialogResult.Cancel) return false;
        if (answer == DialogResult.No)
        {
            ReloadEditor(tabIndex);
            return true;
        }
        await SaveEditorAsync(tabIndex);
        return !HasUnsavedChanges(tabIndex);
    }

    private async Task SaveEditorAsync(int tabIndex)
    {
        if (tabIndex == 1) await SaveCustomerAsync();
        else if (tabIndex == 2) await SavePriceAsync();
        else if (tabIndex == 5)
        {
            var itemId = (_profitPriceItem.SelectedItem as PriceItem)?.Id;
            var itemGroupId = (_profitItemGroup.SelectedItem as PriceGroup)?.Id;
            var useSpecial = _profitUseSpecial.Checked;
            var specialPercent = _profitSpecialPercent.Value;
            var group = _store.State.PriceGroups.FirstOrDefault(x => !x.Deleted && x.Id == _selectedGroupId);
            if (group is not null && (group.Name != _groupName.Text.Trim() || (group.CostMultiplier - 1m) * 100m != _groupProfitPercent.Value)) await SavePriceGroupAsync();
            if (itemId is not null && itemGroupId is not null)
            {
                _profitPriceItem.SelectedValue = itemId;
                _profitItemGroup.SelectedValue = itemGroupId;
                _profitUseSpecial.Checked = useSpecial;
                _profitSpecialPercent.Value = Clamp(_profitSpecialPercent, specialPercent);
                if (HasProfitEditorChanges()) await SaveProfitPriceItemAsync();
            }
        }
        else if (tabIndex == 6) await SaveSettingsAsync();
    }

    private void ReloadEditor(int tabIndex)
    {
        if (tabIndex == 1)
        {
            if (_selectedCustomerId is null) ClearCustomerEditor(); else LoadSelectedCustomer();
        }
        else if (tabIndex == 2)
        {
            if (_selectedPriceId is null) ClearPriceEditor(); else LoadSelectedPrice();
        }
        else if (tabIndex == 5)
        {
            LoadSelectedPriceGroup();
            LoadProfitPriceItemGroupOverride();
        }
        else if (tabIndex == 6)
        {
            _tabs.Focus();
            LoadSettingsControls();
        }
    }

    private async void MainForm_FormClosing(object? sender, FormClosingEventArgs e)
    {
        if (e.CloseReason == CloseReason.WindowsShutDown || _skipClosePrompt)
        {
            _tray.Visible = false; _syncTimer.Stop(); _sync.Dispose(); return;
        }
        e.Cancel = true;
        if (HasUnsavedChanges(_tabs.SelectedIndex))
        {
            if (_unsavedPromptOpen) return;
            _unsavedPromptOpen = true;
            var proceed = await ConfirmUnsavedChangesAsync(_tabs.SelectedIndex);
            _unsavedPromptOpen = false;
            if (!proceed) { _exitRequested = false; return; }
        }
        if (_exitRequested)
        {
            _skipClosePrompt = true;
            Close();
            return;
        }
        ShowInTaskbar = true;
        WindowState = FormWindowState.Minimized;
        _tray.ShowBalloonTip(1800, "İzmirde Reklam küçültüldü", "Görev çubuğundaki BTakip simgesine tıklayarak aynı pencereyi yeniden açabilirsiniz.", ToolTipIcon.Info);
    }

    private static void OpenPath(string path)
    {
        try { System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo("explorer.exe", $"\"{path}\"") { UseShellExecute = true }); }
        catch { }
    }

    private static void OpenHtmlDocument(string path)
    {
        var browsers = new[]
        {
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Google", "Chrome", "Application", "chrome.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Google", "Chrome", "Application", "chrome.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "Google", "Chrome", "Application", "chrome.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "Microsoft", "Edge", "Application", "msedge.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Microsoft", "Edge", "Application", "msedge.exe")
        };
        var browser = browsers.FirstOrDefault(File.Exists);
        var info = browser is null
            ? new System.Diagnostics.ProcessStartInfo(path) { UseShellExecute = true }
            : new System.Diagnostics.ProcessStartInfo(browser, $"\"{path}\"") { UseShellExecute = true };
        System.Diagnostics.Process.Start(info);
    }

    private static TabPage NewTab(string text) => new(text) { BackColor = Color.White, Padding = new Padding(0) };

    private static Label AddStackField(TableLayoutPanel layout, string label, Control control)
    {
        var fieldLabel = UiTheme.Label(label);
        layout.Controls.Add(fieldLabel);
        control.Margin = new Padding(3, 0, 3, 3);
        control.Width = 310;
        layout.Controls.Add(control);
        return fieldLabel;
    }

    private static void AddGridColumn(DataGridView grid, string name, string header, bool visible, int fillWeight = 100, string? format = null)
    {
        var column = new DataGridViewTextBoxColumn { Name = name, HeaderText = header, Visible = visible, FillWeight = fillWeight, SortMode = DataGridViewColumnSortMode.Automatic };
        if (format is not null) { column.DefaultCellStyle.Format = format; column.DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleRight; }
        grid.Columns.Add(column);
    }

    private static void AddGridLinkColumn(DataGridView grid, string name, string header, int fillWeight = 100)
    {
        grid.Columns.Add(new DataGridViewLinkColumn
        {
            Name = name, HeaderText = header, Visible = true, FillWeight = fillWeight,
            SortMode = DataGridViewColumnSortMode.Automatic, LinkColor = UiTheme.Teal,
            ActiveLinkColor = UiTheme.Orange, VisitedLinkColor = UiTheme.Teal,
            TrackVisitedState = false, UseColumnTextForLinkValue = false
        });
    }

    private static void FixLeftPane(SplitContainer split, int desired, int minimum)
    {
        void Apply()
        {
            const int otherMinimum = 360;
            if (split.Width <= minimum + otherMinimum + split.SplitterWidth) return;
            split.Panel1MinSize = 0;
            split.Panel2MinSize = 0;
            var target = Math.Min(desired, split.Width - otherMinimum - split.SplitterWidth);
            if (target >= minimum && split.SplitterDistance != target) split.SplitterDistance = target;
            split.Panel1MinSize = minimum;
            split.Panel2MinSize = otherMinimum;
        }
        split.HandleCreated += (_, _) => split.BeginInvoke((Action)Apply);
        split.Resize += (_, _) => Apply();
    }

    private static void FixRightPane(SplitContainer split, int rightWidth, int leftMinimum)
    {
        void Apply()
        {
            const int otherMinimum = 330;
            if (split.Width <= leftMinimum + otherMinimum + split.SplitterWidth) return;
            split.Panel1MinSize = 0;
            split.Panel2MinSize = 0;
            var target = Math.Max(leftMinimum, split.Width - rightWidth - split.SplitterWidth);
            if (split.SplitterDistance != target) split.SplitterDistance = target;
            split.Panel1MinSize = leftMinimum;
            split.Panel2MinSize = otherMinimum;
        }
        split.HandleCreated += (_, _) => split.BeginInvoke((Action)Apply);
        split.Resize += (_, _) => Apply();
    }

    private static decimal Clamp(NumericUpDown input, decimal value) => Math.Max(input.Minimum, Math.Min(input.Maximum, value));

    private static string? GetArgument(string[] args, string key)
    {
        var index = Array.FindIndex(args, x => x.Equals(key, StringComparison.OrdinalIgnoreCase));
        return index >= 0 && index + 1 < args.Length ? args[index + 1] : null;
    }
}

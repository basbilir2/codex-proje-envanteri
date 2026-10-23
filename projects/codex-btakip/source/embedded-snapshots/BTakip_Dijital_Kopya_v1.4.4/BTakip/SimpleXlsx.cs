using System.Globalization;
using System.IO.Compression;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Xml.Linq;

namespace BTakip;

public sealed class ImportReport
{
    public int Customers { get; set; }
    public int Prices { get; set; }
    public int Orders { get; set; }
    public int Payments { get; set; }
    public List<string> Warnings { get; set; } = [];
    public override string ToString() =>
        $"{Customers} müşteri, {Prices} fiyat, {Orders} satış, {Payments} tahsilat içe aktarıldı." +
        (Warnings.Count > 0 ? $"\n\nUyarılar:\n• {string.Join("\n• ", Warnings.Take(8))}" : "");
}

public sealed class ExcelConversionPreview
{
    public List<ExcelConvertedMovement> Movements { get; } = [];
    public List<string> UsedSheets { get; } = [];
    public List<string> IgnoredSheets { get; } = [];
    public int SourceRows { get; set; }
    public int BlankDateRows { get; set; }
    public int SkippedTemplateRows { get; set; }
}

public sealed class ExcelConvertedMovement
{
    public string SourceSheet { get; init; } = "";
    public int SourceRow { get; init; }
    public string CustomerName { get; init; } = "";
    public DateTime Date { get; init; } = DateTime.MinValue;
    public string Movement { get; init; } = "";
    public string Description { get; init; } = "";
    public string Material { get; init; } = "";
    public string Measure { get; init; } = "";
    public decimal Debit { get; init; }
    public decimal Credit { get; init; }
    public decimal Quantity { get; init; } = 1;
    public decimal ExchangeRate { get; init; }
    public decimal WidthCm { get; init; }
    public decimal HeightCm { get; init; }
    public decimal LengthMeter { get; init; }
    public string PaymentType { get; init; } = "Diğer";
}

public static class SimpleXlsx
{
    private sealed record SheetData(string Name, IReadOnlyList<string> Headers, IReadOnlyList<IReadOnlyList<object?>> Rows);

    public static void Export(AppState state, string path)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(path))!);
        var sheets = BuildSheets(state);
        var temp = path + ".tmp";
        if (File.Exists(temp)) File.Delete(temp);

        using (var archive = ZipFile.Open(temp, ZipArchiveMode.Create))
        {
            WriteText(archive, "[Content_Types].xml", ContentTypes(sheets.Count));
            WriteText(archive, "_rels/.rels", RootRels());
            WriteText(archive, "docProps/app.xml", AppProps(sheets));
            WriteText(archive, "docProps/core.xml", CoreProps());
            WriteText(archive, "xl/workbook.xml", Workbook(sheets));
            WriteText(archive, "xl/_rels/workbook.xml.rels", WorkbookRels(sheets.Count));
            WriteText(archive, "xl/styles.xml", Styles());
            for (var i = 0; i < sheets.Count; i++)
                WriteText(archive, $"xl/worksheets/sheet{i + 1}.xml", Worksheet(sheets[i]));
        }
        File.Move(temp, path, true);
    }

    public static ImportReport Import(string path, DataStore store, bool appendOnly = false)
    {
        var workbook = ReadWorkbook(path);
        var report = new ImportReport();
        var names = workbook.Keys.ToDictionary(Normalize, x => x, StringComparer.OrdinalIgnoreCase);
        var recognized = false;

        if (names.TryGetValue(Normalize("Müşteriler"), out var customersSheet))
        { recognized = true; ImportCustomers(workbook[customersSheet], store, report, appendOnly); }
        if (names.TryGetValue(Normalize("Fiyatlar"), out var pricesSheet))
        { recognized = true; ImportPrices(workbook[pricesSheet], store, report, appendOnly); }
        if (names.TryGetValue(Normalize("Siparişler"), out var ordersSheet))
        { recognized = true; ImportOrders(workbook[ordersSheet], store, report, appendOnly); }
        if (names.TryGetValue(Normalize("Tahsilatlar"), out var paymentsSheet))
        { recognized = true; ImportPayments(workbook[paymentsSheet], store, report, appendOnly); }

        if (!recognized) ImportLegacy(workbook, store, report, appendOnly);

        return report;
    }

    public static ExcelConversionPreview AnalyzeConversion(string path)
    {
        var workbook = ReadWorkbook(path);
        var preview = new ExcelConversionPreview();
        var fallbackCustomerName = Path.GetFileNameWithoutExtension(path);
        var workbookCustomerName = workbook.Values.Select(rows => FindLabeledCustomerName(rows.Take(50)))
            .FirstOrDefault(x => !string.IsNullOrWhiteSpace(x)) ?? fallbackCustomerName;
        var candidates = workbook.Select(entry =>
        {
            var headerIndex = FindConversionHeader(entry.Value);
            return new ConversionSheetCandidate(entry.Key, entry.Value, headerIndex, headerIndex < 0 ? 0 : ConversionHeaderScore(entry.Value[headerIndex]));
        }).Where(x => x.HeaderIndex >= 0).ToList();
        var usable = candidates.Where(x => !IsIgnoredConversionSheet(x.Name)).ToList();
        if (usable.Count == 0) usable = candidates;
        var preferred = usable.Where(x => IsPreferredConversionSheet(x.Name)).ToList();
        List<ConversionSheetCandidate> selected;
        if (preferred.Count > 0) selected = preferred;
        else if (usable.Count > 0)
        {
            var bestScore = usable.Max(x => x.Score);
            selected = usable.Where(x => x.Score == bestScore).ToList();
        }
        else selected = [];

        preview.UsedSheets.AddRange(selected.Select(x => x.Name));
        preview.IgnoredSheets.AddRange(workbook.Keys.Where(name => !preview.UsedSheets.Contains(name, StringComparer.OrdinalIgnoreCase)));

        foreach (var candidate in selected)
        {
            var sheetName = candidate.Name;
            var rows = candidate.Rows;
            var headerIndex = candidate.HeaderIndex;
            var headers = rows[headerIndex];
            var columns = ConversionColumns.From(headers);
            var sheetCustomerName = FindWorkbookCustomerName(rows, headerIndex, sheetName, workbookCustomerName);
            var paymentSheet = NormalizeHeader(sheetName).Contains("tahsilat");

            foreach (var (row, offset) in rows.Skip(headerIndex + 1).Select((row, offset) => (row, offset)))
            {
                if (!HasRealMovement(row, columns))
                {
                    if (row.Any(x => !string.IsNullOrWhiteSpace(x))) preview.SkippedTemplateRows++;
                    continue;
                }

                var rawDate = Cell(row, columns.Date);
                var hasDate = TryDate(rawDate, out var date);
                if (!hasDate) { date = DateTime.MinValue; preview.BlankDateRows++; }

                var movement = Cell(row, columns.Movement);
                var group = Cell(row, columns.Group);
                var sourceDescription = Cell(row, columns.Description);
                var materialService = Cell(row, columns.MaterialService);
                var measure = Cell(row, columns.Measurement);
                var note = Cell(row, columns.Note);
                var paymentType = Cell(row, columns.PaymentType);
                var quantity = PositiveDecimal(Cell(row, columns.Quantity));
                var unitPrice = PositiveDecimal(Cell(row, columns.UnitPrice));
                var exchangeRate = PositiveDecimal(Cell(row, columns.ExchangeRate));
                var debt = PositiveDecimal(Cell(row, columns.Debt));
                var credit = PositiveDecimal(Cell(row, columns.Credit));
                var totalPrice = PositiveDecimal(Cell(row, columns.TotalPrice));
                var normalizedMovement = Normalize(movement);
                var explicitPayment = IsPaymentMovement(normalizedMovement);
                var explicitSale = IsSaleMovement(normalizedMovement);
                var measurementHeader = columns.Measurement >= 0 && columns.Measurement < headers.Count ? headers[columns.Measurement] : "";

                if (string.IsNullOrWhiteSpace(measure)) measure = InferMeasurement(sourceDescription, materialService, group, rawDate);
                var areaM2 = MeasurementAreaM2(measure, measurementHeader);
                if (areaM2 > 0 && IsAreaHeader(measurementHeader) && Regex.IsMatch(measure, @"^\s*\d+(?:[.,]\d+)?\s*$"))
                    measure = $"{areaM2.ToString("0.####", new CultureInfo("tr-TR"))} m²";

                var calculationDetail = "";
                if (!explicitPayment && debt == 0 && credit == 0 && totalPrice == 0 && unitPrice > 0 && areaM2 > 0)
                {
                    var countedQuantity = quantity > 0 ? quantity : 1;
                    totalPrice = Math.Round(areaM2 * unitPrice * countedQuantity, 2, MidpointRounding.AwayFromZero);
                    calculationDetail = $"{areaM2.ToString("0.####", new CultureInfo("tr-TR"))} m² × {unitPrice.ToString("N2", new CultureInfo("tr-TR"))} TL × {countedQuantity.ToString("0.####", new CultureInfo("tr-TR"))} adet = {totalPrice.ToString("N2", new CultureInfo("tr-TR"))} TL";
                }

                var sourceCredit = credit;
                var isPayment = explicitPayment || (!explicitSale && (paymentSheet || (credit > 0 && debt == 0)));
                var isSale = explicitSale || (!isPayment && (debt > 0 || totalPrice > 0)) || (debt > 0 && sourceCredit > 0);
                if (isPayment && credit == 0) credit = totalPrice > 0 ? totalPrice : debt;
                if (!isPayment && debt == 0) debt = totalPrice;

                var customerName = Cell(row, columns.Customer);
                var material = NonEmpty(materialService, group);
                var descriptionHeader = columns.Description >= 0 && columns.Description < headers.Count ? NormalizeHeader(headers[columns.Description]) : "";
                if (string.IsNullOrWhiteSpace(material) && descriptionHeader == NormalizeHeader("İş / Hizmet")) material = sourceDescription;
                if (string.IsNullOrWhiteSpace(material) && !hasDate && LooksLikeText(rawDate)) material = rawDate.Trim();
                var description = BuildConvertedDescription(row, headers, columns, sourceDescription, movement, group, materialService,
                    measure, note, rawDate, hasDate, isPayment ? "Tahsilat" : "Satış", calculationDetail);
                ApplyMeasurement(measure, out var widthCm, out var heightCm, out var lengthMeter);

                var sourceRow = headerIndex + offset + 2;
                var added = false;
                if (isSale || !isPayment)
                {
                    preview.Movements.Add(new ExcelConvertedMovement
                    {
                        SourceSheet = sheetName, SourceRow = sourceRow, CustomerName = NonEmpty(customerName, sheetCustomerName),
                        Date = date, Movement = "Satış", Description = description, Material = material, Measure = measure,
                        WidthCm = widthCm, HeightCm = heightCm, LengthMeter = lengthMeter,
                        Quantity = quantity > 0 ? quantity : 1, ExchangeRate = exchangeRate, Debit = debt
                    });
                    added = true;
                }

                if (credit > 0 || (isPayment && !isSale))
                {
                    preview.Movements.Add(new ExcelConvertedMovement
                    {
                        SourceSheet = sheetName, SourceRow = sourceRow, CustomerName = NonEmpty(customerName, sheetCustomerName),
                        Date = date, Movement = "Tahsilat", Description = description, Material = material, Measure = measure,
                        Credit = credit, PaymentType = NonEmpty(paymentType, "Diğer")
                    });
                    added = true;
                }

                if (added) preview.SourceRows++;
            }
        }

        return preview;
    }

    public static ImportReport ConvertAndImport(string path, DataStore store, bool appendOnly = true)
    {
        var preview = AnalyzeConversion(path);
        return ImportConversion(preview, store, appendOnly);
    }

    public static ImportReport ImportConversion(ExcelConversionPreview preview, DataStore store, bool appendOnly = true)
    {
        var report = new ImportReport();
        var addedSources = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var movement in preview.Movements)
        {
            var customer = ResolveCustomer(store, movement.CustomerName, "", report);
            if (movement.Movement == "Satış")
            {
                var order = new Order
                {
                    Date = movement.Date, CustomerId = customer.Id, Description = movement.Description, Material = movement.Material,
                    WidthCm = movement.WidthCm, HeightCm = movement.HeightCm, LengthMeter = movement.LengthMeter,
                    Quantity = movement.Quantity, ExchangeRate = movement.ExchangeRate, CostTotalTl = 0,
                    SaleTotalTl = movement.Debit, PriceGroupId = customer.PriceGroupId, DeviceId = store.State.DeviceId
                };
                var duplicate = appendOnly && store.State.Orders.Any(x => !x.Deleted && x.CustomerId == order.CustomerId && x.Date.Date == order.Date.Date &&
                    Normalize(x.Description) == Normalize(order.Description) && Normalize(x.Material) == Normalize(order.Material) &&
                    x.WidthCm == order.WidthCm && x.HeightCm == order.HeightCm && x.LengthMeter == order.LengthMeter &&
                    x.Quantity == order.Quantity && x.SaleTotalTl == order.SaleTotalTl);
                if (!duplicate)
                {
                    store.State.Orders.Add(order); report.Orders++;
                    addedSources.Add($"{movement.SourceSheet}\n{movement.SourceRow}");
                }
            }
            else
            {
                var payment = new Payment
                {
                    Date = movement.Date, CustomerId = customer.Id, AmountTl = movement.Credit,
                    PaymentType = movement.PaymentType, Description = movement.Description, DeviceId = store.State.DeviceId
                };
                var duplicate = appendOnly && store.State.Payments.Any(x => !x.Deleted && x.CustomerId == payment.CustomerId && x.Date.Date == payment.Date.Date &&
                    x.AmountTl == payment.AmountTl && Normalize(x.Description) == Normalize(payment.Description));
                if (!duplicate)
                {
                    store.State.Payments.Add(payment); report.Payments++;
                    addedSources.Add($"{movement.SourceSheet}\n{movement.SourceRow}");
                }
            }
        }

        if (preview.Movements.Count == 0) report.Warnings.Add("Tarih, Hareket, Açıklama, Malzeme veya tutar alanlarını içeren bir hareket tablosu bulunamadı.");
        else
        {
            report.Warnings.Add($"{preview.SourceRows} kaynak satırı incelendi; {addedSources.Count} yeni satır cariye eklendi.");
            report.Warnings.Add($"Yalnız {string.Join(", ", preview.UsedSheets)} sayfası kullanıldı; diğer sayfalar veri kaynağı yapılmadı.");
            if (preview.BlankDateRows > 0) report.Warnings.Add($"{preview.BlankDateRows} satırda geçerli tarih yoktu; tarih boş bırakıldı ve hücredeki metin korundu.");
            if (preview.SkippedTemplateRows > 0) report.Warnings.Add($"{preview.SkippedTemplateRows} boş veya yalnız formül sonucu taşıyan şablon satırı atlandı.");
        }
        return report;
    }

    private sealed record ConversionSheetCandidate(string Name, List<List<string>> Rows, int HeaderIndex, int Score);

    private sealed record ConversionColumns(
        int Date, int Movement, int Group, int Description, int MaterialService, int Measurement, int Quantity,
        int UnitPrice, int TotalPrice, int Debt, int Credit, int Balance, int Note, int PaymentType,
        int ExchangeRate, int Customer, HashSet<int> Known)
    {
        public static ConversionColumns From(List<string> headers)
        {
            int Find(params string[] aliases)
            {
                var normalized = aliases.Select(NormalizeHeader).ToHashSet();
                return headers.FindIndex(x => normalized.Contains(NormalizeHeader(x)));
            }

            var date = Find("Tarih", "İşlem Tarihi", "Hareket Tarihi", "Date");
            var movement = Find("Hareket", "İşlem", "İşlem Türü", "Hareket Türü", "Tür");
            var group = Find("Grup", "Ürün Grubu", "Malzeme Grubu", "Kategori");
            var description = Find("Açıklama", "İş Açıklaması", "İş Adı", "İş / Hizmet", "Proje", "İsim", "Ürün");
            var material = Find("Malzeme-Hizmet", "Malzeme / Hizmet", "Malzeme Hizmet", "Malzeme", "Hizmet", "Ürün Hizmet");
            var measurement = Find("Miktar", "Ölçü", "Ölçü / Alan", "Ebat", "Boyut", "Alan", "m2", "m²", "Metrekare");
            var quantity = Find("Adet", "Quantity", "Qty");
            var unitPrice = Find("Birim Fiyat", "Birim Ücret", "Fiyat");
            var totalPrice = Find("Toplam Fiyat", "Satır Toplamı", "Tutar", "Tutar TL");
            var debt = Find("Borcunuz", "Borç", "Borç TL", "Debit", "Satış TL");
            var credit = Find("Alacağınız", "Alacak", "Tahsilat", "Ödenen", "Credit");
            var balance = Find("Toplam", "Bakiye", "Kalan", "Balance");
            var note = Find("Not", "Notlar", "Ek Açıklama", "Defter / Okuma Notu");
            var paymentType = Find("Ödeme Tipi", "Tahsilat Tipi", "Ödeme Şekli");
            var exchangeRate = Find("KUR", "Döviz Kuru", "Kur TL");
            var customer = Find("Müşteri", "Müşteri Adı", "Cari", "Cari Adı", "Firma", "Firma Adı");
            var known = new[] { date, movement, group, description, material, measurement, quantity, unitPrice, totalPrice, debt, credit, balance, note, paymentType, exchangeRate, customer }
                .Where(x => x >= 0).ToHashSet();
            return new(date, movement, group, description, material, measurement, quantity, unitPrice, totalPrice, debt, credit, balance, note, paymentType, exchangeRate, customer, known);
        }
    }

    private static int FindConversionHeader(List<List<string>> rows)
    {
        var bestIndex = -1;
        var bestScore = 0;
        for (var index = 0; index < Math.Min(rows.Count, 50); index++)
        {
            var columns = ConversionColumns.From(rows[index]);
            var score = ConversionHeaderScore(rows[index]);
            var hasMovementData = columns.Date >= 0 || columns.Description >= 0 || columns.TotalPrice >= 0 ||
                columns.Debt >= 0 || columns.Credit >= 0;
            if (hasMovementData && score >= 2 && score > bestScore) { bestIndex = index; bestScore = score; }
        }
        return bestIndex;
    }

    private static int ConversionHeaderScore(List<string> row)
    {
        var columns = ConversionColumns.From(row);
        return new[] { columns.Date, columns.Movement, columns.Group, columns.Description, columns.MaterialService, columns.Measurement,
            columns.TotalPrice, columns.Debt, columns.Credit, columns.Note }.Count(x => x >= 0);
    }

    private static bool IsIgnoredConversionSheet(string name)
    {
        var normalized = NormalizeHeader(name);
        return new[] { "ozet", "kontrol", "fiyat", "kural", "kaynak", "gorsel", "ayar", "rapor" }.Any(normalized.Contains);
    }

    private static bool IsPreferredConversionSheet(string name)
    {
        var normalized = NormalizeHeader(name);
        return new[] { "hareket", "siparis", "satis", "tahsilat", "cari" }.Any(normalized.Contains);
    }

    private static bool HasRealMovement(List<string> row, ConversionColumns columns)
    {
        var textColumns = new[] { columns.Date, columns.Movement, columns.Group, columns.Description, columns.MaterialService, columns.Measurement,
            columns.Note, columns.PaymentType, columns.Customer };
        if (textColumns.Any(index => HasMeaningfulCell(Cell(row, index)))) return true;
        return new[] { columns.Quantity, columns.UnitPrice, columns.TotalPrice, columns.Debt, columns.Credit }
            .Any(index => PositiveDecimal(Cell(row, index)) > 0);
    }

    private static string FindWorkbookCustomerName(List<List<string>> rows, int headerIndex, string sheetName, string fallback)
    {
        var labeled = FindLabeledCustomerName(rows.Take(headerIndex));
        if (!string.IsNullOrWhiteSpace(labeled)) return labeled;

        var normalizedSheet = NormalizeHeader(sheetName);
        var genericSheet = normalizedSheet is "sayfa1" or "sheet1" or "hareketler" or "cari" or "ekstre" ||
            new[] { "hareket", "cari", "ekstre", "tahsilat", "siparis", "satis", "rapor" }.Any(normalizedSheet.Contains);
        if (!genericSheet) return sheetName;
        return fallback;
    }

    private static string FindLabeledCustomerName(IEnumerable<List<string>> rows)
    {
        var aliases = new[] { "Müşteri", "Müşteri Adı", "Cari", "Cari Adı", "Cari Ünvanı", "Firma", "Firma Adı" }
            .Select(NormalizeHeader).ToHashSet();
        foreach (var row in rows)
        {
            for (var index = 0; index < row.Count; index++)
            {
                var value = row[index].Trim();
                var key = NormalizeHeader(value.TrimEnd(':'));
                if (aliases.Contains(key))
                {
                    var next = row.Skip(index + 1).FirstOrDefault(x => !string.IsNullOrWhiteSpace(x));
                    if (!string.IsNullOrWhiteSpace(next)) return next.Trim();
                }
                var separator = value.IndexOf(':');
                if (separator > 0 && aliases.Contains(NormalizeHeader(value[..separator])) && value[(separator + 1)..].Trim() is { Length: > 0 } inline)
                    return inline;
            }
        }
        return "";
    }

    private static string BuildConvertedDescription(List<string> row, List<string> headers, ConversionColumns columns, string sourceDescription,
        string movement, string group, string materialService, string measure, string note, string rawDate, bool hasDate, string targetMovement,
        string calculationDetail)
    {
        var parts = new List<string>();
        void Add(string value) { if (!string.IsNullOrWhiteSpace(value) && !parts.Any(x => Normalize(x) == Normalize(value))) parts.Add(value.Trim()); }
        void AddLabel(string label, string value) { if (!string.IsNullOrWhiteSpace(value)) Add($"{label}: {value.Trim()}"); }

        Add(sourceDescription);
        if (!string.IsNullOrWhiteSpace(movement) && Normalize(movement) != Normalize(targetMovement)) AddLabel("Hareket", movement);
        AddLabel("Grup", group);
        if (!string.IsNullOrWhiteSpace(materialService) && Normalize(materialService) != Normalize(group)) AddLabel("Malzeme-Hizmet", materialService);
        AddLabel("Not", note);
        AddLabel("Ödeme Tipi", Cell(row, columns.PaymentType));
        if (!hasDate) AddLabel("Tarih", rawDate);
        AddLabel("Adet", Cell(row, columns.Quantity));
        AddLabel("Birim Fiyat", Cell(row, columns.UnitPrice));
        AddLabel("Toplam Fiyat", Cell(row, columns.TotalPrice));
        AddLabel("Kaynak Borç", Cell(row, columns.Debt));
        AddLabel("Kaynak Tahsilat", Cell(row, columns.Credit));
        AddLabel("Kaynak Bakiye", Cell(row, columns.Balance));
        AddLabel("KUR", Cell(row, columns.ExchangeRate));
        AddLabel("Dönüştürme Hesabı", calculationDetail);

        for (var index = 0; index < row.Count; index++)
        {
            if (columns.Known.Contains(index) || string.IsNullOrWhiteSpace(row[index])) continue;
            var header = index < headers.Count ? headers[index].Trim() : "";
            if (!string.IsNullOrWhiteSpace(header)) AddLabel(header, row[index]);
        }
        AddLabel("Ölçü", measure);
        return string.Join(" | ", parts);
    }

    private static void ApplyMeasurement(string value, out decimal widthCm, out decimal heightCm, out decimal lengthMeter)
    {
        widthCm = heightCm = lengthMeter = 0;
        if (string.IsNullOrWhiteSpace(value)) return;
        if (TryDimensionsMeters(value, out var widthMeter, out var heightMeter))
        {
            widthCm = widthMeter * 100;
            heightCm = heightMeter * 100;
            return;
        }
        if (!Regex.IsMatch(value, @"m\s*[²2]", RegexOptions.IgnoreCase))
        {
            var length = Regex.Match(value, @"(?<m>\d+(?:[.,]\d+)?)\s*m(?:etre)?\b", RegexOptions.IgnoreCase);
            if (length.Success) lengthMeter = PositiveDecimal(length.Groups["m"].Value);
        }
    }

    private static decimal MeasurementAreaM2(string value, string header)
    {
        if (string.IsNullOrWhiteSpace(value)) return 0;
        if (TryDimensionsMeters(value, out var widthMeter, out var heightMeter)) return widthMeter * heightMeter;

        var directArea = Regex.Match(value, @"(?<area>\d+(?:[.,]\d+)?)\s*(?:m\s*(?:²|2)|metrekare)", RegexOptions.IgnoreCase);
        if (directArea.Success) return PositiveDecimal(directArea.Groups["area"].Value);
        if (IsAreaHeader(header) && Regex.IsMatch(value, @"^\s*\d+(?:[.,]\d+)?\s*$")) return PositiveDecimal(value);
        return 0;
    }

    private static bool IsAreaHeader(string header)
    {
        var normalized = NormalizeHeader(header);
        return normalized.Contains("alan") || normalized.Contains("m2") || normalized.Contains("metrekare");
    }

    private static bool TryDimensionsMeters(string value, out decimal widthMeter, out decimal heightMeter)
    {
        widthMeter = heightMeter = 0;
        var size = Regex.Match(value,
            @"(?<w>\d+(?:[.,]\d+)?)\s*(?<wu>mm|cm|m)?\s*[x×*]\s*(?<h>\d+(?:[.,]\d+)?)\s*(?<hu>mm|cm|m)?",
            RegexOptions.IgnoreCase);
        if (!size.Success) return false;

        var width = PositiveDecimal(size.Groups["w"].Value);
        var height = PositiveDecimal(size.Groups["h"].Value);
        var widthUnit = size.Groups["wu"].Value;
        var heightUnit = size.Groups["hu"].Value;
        if (string.IsNullOrWhiteSpace(widthUnit)) widthUnit = string.IsNullOrWhiteSpace(heightUnit) ? "cm" : heightUnit;
        if (string.IsNullOrWhiteSpace(heightUnit)) heightUnit = widthUnit;

        static decimal InMeters(decimal number, string unit) => unit.ToLowerInvariant() switch
        {
            "mm" => number / 1000m,
            "m" => number,
            _ => number / 100m
        };

        widthMeter = InMeters(width, widthUnit);
        heightMeter = InMeters(height, heightUnit);
        return widthMeter > 0 && heightMeter > 0;
    }

    private static string InferMeasurement(params string[] values)
    {
        foreach (var value in values.Where(x => !string.IsNullOrWhiteSpace(x)))
        {
            var match = Regex.Match(value, @"\d+(?:[.,]\d+)?\s*(?:cm)?\s*[x×]\s*\d+(?:[.,]\d+)?\s*(?:cm)?|\d+(?:[.,]\d+)?\s*m\s*[²2]|\d+(?:[.,]\d+)?\s*m(?:etre)?\b", RegexOptions.IgnoreCase);
            if (match.Success) return match.Value.Trim();
        }
        return "";
    }

    private static bool IsPaymentMovement(string value) => new[] { "tahsilat", "odeme", "odendi", "nakit", "havale", "eft", "cek" }.Any(value.Contains);
    private static bool IsSaleMovement(string value) => new[] { "satis", "borc", "fatura", "siparis", "islem" }.Any(value.Contains);
    private static bool LooksLikeText(string value) => value.Any(char.IsLetter);
    private static bool HasMeaningfulCell(string value) => !string.IsNullOrWhiteSpace(value) && value.Trim() is not ("0" or "0,00" or "0.00" or "-" or "—");
    private static string Cell(List<string> row, int index) => index >= 0 && index < row.Count ? row[index].Trim() : "";
    private static string NormalizeHeader(string value) => Regex.Replace(Normalize(value), @"[^a-z0-9]+", " ").Trim();

    private static decimal PositiveDecimal(string value)
    {
        var text = Regex.Replace(value ?? "", @"[^0-9,\.\-]", "");
        if (string.IsNullOrWhiteSpace(text)) return 0;
        if (text.Contains(',') && text.Contains('.'))
            text = text.LastIndexOf(',') > text.LastIndexOf('.') ? text.Replace(".", "").Replace(',', '.') : text.Replace(",", "");
        else if (text.Contains(',')) text = text.Replace(',', '.');
        return decimal.TryParse(text, NumberStyles.Number | NumberStyles.AllowLeadingSign, CultureInfo.InvariantCulture, out var parsed) ? Math.Abs(parsed) : 0;
    }

    private static bool TryDate(string value, out DateTime date)
    {
        if (DateTime.TryParse(value, new CultureInfo("tr-TR"), DateTimeStyles.AllowWhiteSpaces, out date) ||
            DateTime.TryParse(value, CultureInfo.InvariantCulture, DateTimeStyles.AllowWhiteSpaces, out date))
        { date = date.Date; return true; }
        if (double.TryParse(value, NumberStyles.Number, CultureInfo.InvariantCulture, out var serial) && serial >= 20000 && serial < 2958466)
        {
            try { date = DateTime.FromOADate(serial).Date; return true; } catch { }
        }
        date = DateTime.MinValue;
        return false;
    }

    private static List<SheetData> BuildSheets(AppState state)
    {
        string CustomerName(string id) => state.Customers.FirstOrDefault(x => x.Id == id)?.Name ?? "";
        string GroupName(string id) => state.PriceGroups.FirstOrDefault(x => x.Id == id)?.Name ?? id;

        return
        [
            new("Müşteriler",
                ["Kimlik", "Ad", "Firma", "Telefon", "E-posta", "Fiyat Grubu", "Not", "Bakiye TL", "Son Değişiklik", "Sürüm", "Cihaz", "Silindi"],
                state.Customers.Select(x => (IReadOnlyList<object?>)[x.Id, x.Name, x.Company, x.Phone, x.Email,
                    GroupName(x.PriceGroupId), x.Notes,
                    state.Orders.Where(o => !o.Deleted && o.CustomerId == x.Id).Sum(o => o.SaleTotalTl) - state.Payments.Where(p => !p.Deleted && p.CustomerId == x.Id).Sum(p => p.AmountTl),
                    x.UpdatedAtUtc, x.Revision, x.DeviceId, x.Deleted]).ToList()),
            new("Fiyat Grupları",
                ["Kimlik", "Kod", "Ad", "Maliyet Çarpanı", "Son Değişiklik", "Sürüm", "Cihaz", "Silindi"],
                state.PriceGroups.Select(x => (IReadOnlyList<object?>)[x.Id, x.Code, x.Name, x.CostMultiplier, x.UpdatedAtUtc, x.Revision, x.DeviceId, x.Deleted]).ToList()),
            new("Fiyatlar",
                ["Kimlik", "Kategori", "Ad", "Varyant", "Birim", "Para Birimi", "Birim Maliyet", "İkincil Fiyat", "Levha En cm", "Levha Boy cm", "Kalınlık mm", "Kullanılan Malzeme Kimlik", "Üründe Baskı", "Hizmet Var", "Hizmet Adı", "Hizmet Hesabı", "Hizmet Birim Maliyeti", "Formül", "Aktif", "Müşteri Fiyat Grubu", "Gruba Özel Kârlar", "Özel Kâr %", "Son Değişiklik", "Sürüm", "Cihaz", "Silindi"],
                state.PriceItems.Select(x => (IReadOnlyList<object?>)[x.Id, x.Category, x.Name, x.Variant, x.Unit, x.Currency, x.UnitCost,
                    x.SecondaryCost, x.SheetWidthCm, x.SheetHeightCm, x.ThicknessMm, x.BaseMaterialPriceItemId, x.IsPrintProduct, x.ServiceEnabled,
                    x.ServiceName, x.ServiceFormula, x.ServiceUnitCost, x.Formula, x.Active, GroupName(x.PriceGroupId), JsonSerializer.Serialize(x.GroupProfitPercentOverrides), x.SpecialProfitPercent, x.UpdatedAtUtc, x.Revision, x.DeviceId, x.Deleted]).ToList()),
            new("Siparişler",
                ["Kimlik", "Tarih", "Müşteri Kimlik", "Müşteri", "Açıklama", "Malzeme", "En cm", "Boy cm", "Alan m²", "Uzunluk m", "Süre dk", "Adet", "Kur", "Maliyet TL", "Satış TL", "Fiyat Grubu", "Alternatif %", "Kalemler", "Son Değişiklik", "Sürüm", "Cihaz", "Silindi"],
                state.Orders.Select(x => (IReadOnlyList<object?>)[x.Id, x.Date == DateTime.MinValue ? null : x.Date, x.CustomerId, CustomerName(x.CustomerId), x.Description, x.Material, x.WidthCm, x.HeightCm,
                    x.AreaM2, x.LengthMeter, x.DurationMinutes, x.Quantity, x.ExchangeRate, x.CostTotalTl, x.SaleTotalTl, GroupName(x.PriceGroupId),
                    x.AlternativePercent, string.Join(" + ", x.Lines.Select(l => l.Name)), x.UpdatedAtUtc, x.Revision, x.DeviceId, x.Deleted]).ToList()),
            new("Tahsilatlar",
                ["Kimlik", "Tarih", "Müşteri Kimlik", "Müşteri", "Tutar TL", "Ödeme Tipi", "Açıklama", "Son Değişiklik", "Sürüm", "Cihaz", "Silindi"],
                state.Payments.Select(x => (IReadOnlyList<object?>)[x.Id, x.Date == DateTime.MinValue ? null : x.Date, x.CustomerId, CustomerName(x.CustomerId), x.AmountTl, x.PaymentType,
                    x.Description, x.UpdatedAtUtc, x.Revision, x.DeviceId, x.Deleted]).ToList()),
            new("Ayarlar",
                ["Ayar", "Değer", "Açıklama"],
                new List<IReadOnlyList<object?>>
                {
                    new object?[] { "USD/TL", state.Settings.UsdTryRate, "Otomatik kur kapalıyken kullanılan değer" },
                    new object?[] { "Otomatik kur", state.Settings.AutoExchangeRate, "TCMB döviz satış kuru" },
                    new object?[] { "Senkron aralığı", state.Settings.SyncIntervalSeconds, "Saniye" },
                    new object?[] { "Son senkron", state.Settings.LastSyncUtc, "UTC" },
                    new object?[] { "Cihaz", state.DeviceId, "Bu bilgisayarın kimliği" }
                })
        ];
    }

    private static string Worksheet(SheetData sheet)
    {
        var sb = new StringBuilder();
        sb.Append("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>");
        sb.Append("<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"><sheetViews><sheetView workbookViewId=\"0\"/></sheetViews>");
        sb.Append("<cols>");
        for (var c = 0; c < sheet.Headers.Count; c++)
        {
            var width = Math.Clamp(Math.Max(sheet.Headers[c].Length + 3, sheet.Rows.Take(200).Select(r => c < r.Count ? (r[c]?.ToString()?.Length ?? 0) + 2 : 0).DefaultIfEmpty().Max()), 10, 42);
            sb.Append($"<col min=\"{c + 1}\" max=\"{c + 1}\" width=\"{width}\" customWidth=\"1\"/>");
        }
        sb.Append("</cols><sheetData>");
        sb.Append("<row r=\"1\" ht=\"24\" customHeight=\"1\">");
        for (var c = 0; c < sheet.Headers.Count; c++) sb.Append(Cell(c, 1, sheet.Headers[c], 1));
        sb.Append("</row>");
        for (var r = 0; r < sheet.Rows.Count; r++)
        {
            sb.Append($"<row r=\"{r + 2}\">");
            var row = sheet.Rows[r];
            for (var c = 0; c < row.Count; c++) sb.Append(Cell(c, r + 2, row[c], 0));
            sb.Append("</row>");
        }
        var lastCol = ColumnName(Math.Max(0, sheet.Headers.Count - 1));
        sb.Append($"</sheetData><autoFilter ref=\"A1:{lastCol}{Math.Max(1, sheet.Rows.Count + 1)}\"/><freezePane xSplit=\"0\" ySplit=\"1\" topLeftCell=\"A2\" activePane=\"bottomLeft\" state=\"frozen\"/></worksheet>");
        return sb.ToString();
    }

    private static string Cell(int column, int row, object? value, int style)
    {
        var cellRef = ColumnName(column) + row;
        if (value is null) return $"<c r=\"{cellRef}\" s=\"{style}\"/>";
        if (value is DateTime dt)
            return $"<c r=\"{cellRef}\" t=\"inlineStr\" s=\"{style}\"><is><t>{Xml(dt.ToLocalTime().ToString("yyyy-MM-dd HH:mm:ss"))}</t></is></c>";
        if (value is bool b)
            return $"<c r=\"{cellRef}\" t=\"b\" s=\"{style}\"><v>{(b ? 1 : 0)}</v></c>";
        if (value is decimal or double or float or int or long or short)
            return $"<c r=\"{cellRef}\" s=\"{style}\"><v>{Convert.ToString(value, CultureInfo.InvariantCulture)}</v></c>";
        return $"<c r=\"{cellRef}\" t=\"inlineStr\" s=\"{style}\"><is><t>{Xml(value.ToString() ?? "")}</t></is></c>";
    }

    private static string ColumnName(int index)
    {
        var name = "";
        for (var n = index + 1; n > 0; n = (n - 1) / 26) name = (char)('A' + (n - 1) % 26) + name;
        return name;
    }

    private static string Xml(string value) => System.Security.SecurityElement.Escape(value) ?? "";
    private static void WriteText(ZipArchive archive, string name, string content)
    {
        var entry = archive.CreateEntry(name, CompressionLevel.Optimal);
        using var writer = new StreamWriter(entry.Open(), new UTF8Encoding(false));
        writer.Write(content);
    }

    private static string ContentTypes(int count) => $"<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\"><Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/><Default Extension=\"xml\" ContentType=\"application/xml\"/><Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/><Override PartName=\"/xl/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml\"/>{string.Join("", Enumerable.Range(1, count).Select(i => $"<Override PartName=\"/xl/worksheets/sheet{i}.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>"))}<Override PartName=\"/docProps/core.xml\" ContentType=\"application/vnd.openxmlformats-package.core-properties+xml\"/><Override PartName=\"/docProps/app.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.extended-properties+xml\"/></Types>";
    private static string RootRels() => "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\"><Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/><Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties\" Target=\"docProps/core.xml\"/><Relationship Id=\"rId3\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties\" Target=\"docProps/app.xml\"/></Relationships>";
    private static string CoreProps() => $"<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><cp:coreProperties xmlns:cp=\"http://schemas.openxmlformats.org/package/2006/metadata/core-properties\" xmlns:dc=\"http://purl.org/dc/elements/1.1/\" xmlns:dcterms=\"http://purl.org/dc/terms/\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><dc:creator>BTakip</dc:creator><cp:lastModifiedBy>BTakip</cp:lastModifiedBy><dcterms:created xsi:type=\"dcterms:W3CDTF\">{DateTime.UtcNow:s}Z</dcterms:created></cp:coreProperties>";
    private static string AppProps(List<SheetData> sheets) => $"<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><Properties xmlns=\"http://schemas.openxmlformats.org/officeDocument/2006/extended-properties\" xmlns:vt=\"http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes\"><Application>BTakip</Application><TitlesOfParts><vt:vector size=\"{sheets.Count}\" baseType=\"lpstr\">{string.Join("", sheets.Select(s => $"<vt:lpstr>{Xml(s.Name)}</vt:lpstr>"))}</vt:vector></TitlesOfParts></Properties>";
    private static string Workbook(List<SheetData> sheets) => $"<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\"><sheets>{string.Join("", sheets.Select((s, i) => $"<sheet name=\"{Xml(s.Name)}\" sheetId=\"{i + 1}\" r:id=\"rId{i + 1}\"/>"))}</sheets></workbook>";
    private static string WorkbookRels(int count) => $"<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">{string.Join("", Enumerable.Range(1, count).Select(i => $"<Relationship Id=\"rId{i}\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet{i}.xml\"/>"))}<Relationship Id=\"rId{count + 1}\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles\" Target=\"styles.xml\"/></Relationships>";
    private static string Styles() => "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><styleSheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"><fonts count=\"2\"><font><sz val=\"11\"/><name val=\"Aptos\"/></font><font><b/><color rgb=\"FFFFFFFF\"/><sz val=\"11\"/><name val=\"Aptos\"/></font></fonts><fills count=\"3\"><fill><patternFill patternType=\"none\"/></fill><fill><patternFill patternType=\"gray125\"/></fill><fill><patternFill patternType=\"solid\"><fgColor rgb=\"FF174A63\"/><bgColor indexed=\"64\"/></patternFill></fill></fills><borders count=\"1\"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count=\"1\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\"/></cellStyleXfs><cellXfs count=\"2\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\" xfId=\"0\"/><xf numFmtId=\"0\" fontId=\"1\" fillId=\"2\" borderId=\"0\" xfId=\"0\" applyFill=\"1\" applyFont=\"1\"/></cellXfs></styleSheet>";

    private static Dictionary<string, List<List<string>>> ReadWorkbook(string path)
    {
        using var archive = ZipFile.OpenRead(path);
        XNamespace main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main";
        XNamespace rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships";
        XNamespace pkg = "http://schemas.openxmlformats.org/package/2006/relationships";
        var shared = ReadSharedStrings(archive, main);
        var wb = XDocument.Load(archive.GetEntry("xl/workbook.xml")!.Open());
        var rels = XDocument.Load(archive.GetEntry("xl/_rels/workbook.xml.rels")!.Open());
        var targets = rels.Descendants(pkg + "Relationship").ToDictionary(x => (string)x.Attribute("Id")!, x => (string)x.Attribute("Target")!);
        var result = new Dictionary<string, List<List<string>>>(StringComparer.OrdinalIgnoreCase);

        foreach (var sheet in wb.Descendants(main + "sheet"))
        {
            var name = (string)sheet.Attribute("name")!;
            var rid = (string)sheet.Attribute(rel + "id")!;
            var target = targets[rid].Replace("\\", "/").TrimStart('/');
            if (!target.StartsWith("xl/", StringComparison.OrdinalIgnoreCase)) target = "xl/" + target;
            var entry = archive.GetEntry(target);
            if (entry is null) continue;
            var doc = XDocument.Load(entry.Open());
            var rows = new List<List<string>>();
            foreach (var row in doc.Descendants(main + "row"))
            {
                var values = new List<string>();
                foreach (var cell in row.Elements(main + "c"))
                {
                    var reference = (string?)cell.Attribute("r") ?? "A1";
                    var col = ColumnIndex(reference);
                    while (values.Count <= col) values.Add("");
                    var type = (string?)cell.Attribute("t") ?? "";
                    var raw = cell.Element(main + "v")?.Value ?? cell.Descendants(main + "t").FirstOrDefault()?.Value ?? "";
                    values[col] = type == "s" && int.TryParse(raw, out var idx) && idx >= 0 && idx < shared.Count ? shared[idx] : raw;
                }
                rows.Add(values);
            }
            result[name] = rows;
        }
        return result;
    }

    private static List<string> ReadSharedStrings(ZipArchive archive, XNamespace main)
    {
        var entry = archive.GetEntry("xl/sharedStrings.xml");
        if (entry is null) return [];
        var doc = XDocument.Load(entry.Open());
        return doc.Descendants(main + "si").Select(si => string.Concat(si.Descendants(main + "t").Select(t => t.Value))).ToList();
    }

    private static int ColumnIndex(string reference)
    {
        var n = 0;
        foreach (var ch in reference.TakeWhile(char.IsLetter)) n = n * 26 + (char.ToUpperInvariant(ch) - 'A' + 1);
        return Math.Max(0, n - 1);
    }

    private static void ImportCustomers(List<List<string>> rows, DataStore store, ImportReport report, bool appendOnly)
    {
        if (rows.Count < 2) return;
        var map = HeaderMap(rows[0]);
        foreach (var row in rows.Skip(1))
        {
            var name = Get(row, map, "Ad");
            if (string.IsNullOrWhiteSpace(name)) continue;
            var id = Get(row, map, "Kimlik");
            if (string.IsNullOrWhiteSpace(id)) id = Guid.NewGuid().ToString("N");
            var entity = store.State.Customers.FirstOrDefault(x => x.Id == id)
                ?? store.State.Customers.FirstOrDefault(x => Normalize(x.Name) == Normalize(name));
            if (appendOnly && entity is not null) continue;
            entity ??= new Customer { Id = id };
            entity.Name = name;
            entity.Company = Get(row, map, "Firma");
            entity.Phone = Get(row, map, "Telefon");
            entity.Email = Get(row, map, "E-posta");
            entity.Notes = Get(row, map, "Not");
            var groupName = Get(row, map, "Fiyat Grubu");
            entity.PriceGroupId = store.State.PriceGroups.FirstOrDefault(x => Normalize(x.Name) == Normalize(groupName))?.Id ?? "retail";
            entity.DeviceId = store.State.DeviceId;
            entity.UpdatedAtUtc = DateTime.UtcNow;
            entity.Revision++;
            if (!store.State.Customers.Contains(entity)) store.State.Customers.Add(entity);
            report.Customers++;
        }
    }

    private static void ImportPrices(List<List<string>> rows, DataStore store, ImportReport report, bool appendOnly)
    {
        if (rows.Count < 2) return;
        var map = HeaderMap(rows[0]);
        foreach (var row in rows.Skip(1))
        {
            var name = Get(row, map, "Ad");
            if (string.IsNullOrWhiteSpace(name)) continue;
            var id = Get(row, map, "Kimlik");
            if (string.IsNullOrWhiteSpace(id)) id = Guid.NewGuid().ToString("N");
            var category = Get(row, map, "Kategori", "Malzeme");
            var variant = Get(row, map, "Varyant");
            var item = store.State.PriceItems.FirstOrDefault(x => x.Id == id)
                ?? store.State.PriceItems.FirstOrDefault(x => Normalize(x.Category) == Normalize(category) && Normalize(x.Name) == Normalize(name) && Normalize(x.Variant) == Normalize(variant));
            if (appendOnly && item is not null) continue;
            item ??= new PriceItem { Id = id };
            item.Category = category;
            item.Name = name;
            item.Variant = variant;
            item.Unit = Get(row, map, "Birim", "m²");
            item.Currency = Get(row, map, "Para Birimi", "TL");
            item.UnitCost = Decimal(Get(row, map, "Birim Maliyet"));
            item.SecondaryCost = Decimal(Get(row, map, "İkincil Fiyat"));
            item.SheetWidthCm = Decimal(Get(row, map, "Levha En cm"));
            item.SheetHeightCm = Decimal(Get(row, map, "Levha Boy cm"));
            item.ThicknessMm = Decimal(Get(row, map, "Kalınlık mm"));
            item.BaseMaterialPriceItemId = Get(row, map, "Kullanılan Malzeme Kimlik");
            item.IsPrintProduct = Bool(Get(row, map, "Üründe Baskı"), category is "Baskı" or "Dijital Baskı");
            item.ServiceEnabled = Bool(Get(row, map, "Hizmet Var"), false);
            item.ServiceName = Get(row, map, "Hizmet Adı");
            item.ServiceFormula = Get(row, map, "Hizmet Hesabı", PricingFormula.SquareMeter);
            item.ServiceUnitCost = Decimal(Get(row, map, "Hizmet Birim Maliyeti"));
            item.Formula = Get(row, map, "Formül", PricingFormula.SquareMeter);
            item.Active = Bool(Get(row, map, "Aktif"), true);
            var priceGroup = Get(row, map, "Müşteri Fiyat Grubu");
            item.PriceGroupId = store.State.PriceGroups.FirstOrDefault(x => x.Id.Equals(priceGroup, StringComparison.OrdinalIgnoreCase) || Normalize(x.Name) == Normalize(priceGroup))?.Id ?? "retail";
            var specialProfit = Get(row, map, "Özel Kâr %");
            item.SpecialProfitPercent = string.IsNullOrWhiteSpace(specialProfit) ? null : Decimal(specialProfit);
            var groupOverrides = Get(row, map, "Gruba Özel Kârlar");
            if (!string.IsNullOrWhiteSpace(groupOverrides))
            {
                try { item.GroupProfitPercentOverrides = JsonSerializer.Deserialize<Dictionary<string, decimal>>(groupOverrides) ?? []; }
                catch { report.Warnings.Add($"{item.DisplayName}: gruba özel kâr oranları okunamadı."); }
            }
            item.GroupProfitPercentOverrides ??= [];
            if (item.SpecialProfitPercent is decimal legacyPercent)
            {
                item.GroupProfitPercentOverrides.TryAdd(item.PriceGroupId, legacyPercent);
                item.SpecialProfitPercent = null;
            }
            item.DeviceId = store.State.DeviceId;
            item.UpdatedAtUtc = DateTime.UtcNow;
            item.Revision++;
            if (!store.State.PriceItems.Contains(item)) store.State.PriceItems.Add(item);
            report.Prices++;
        }
    }

    private static void ImportOrders(List<List<string>> rows, DataStore store, ImportReport report, bool appendOnly)
    {
        if (rows.Count < 2) return;
        var map = HeaderMap(rows[0]);
        foreach (var row in rows.Skip(1))
        {
            var description = Get(row, map, "Açıklama");
            if (string.IsNullOrWhiteSpace(description)) continue;
            var customer = ResolveCustomer(store, Get(row, map, "Müşteri"), Get(row, map, "Müşteri Kimlik"), report);
            var groupName = Get(row, map, "Fiyat Grubu");
            var groupId = store.State.PriceGroups.FirstOrDefault(x => Normalize(x.Name) == Normalize(groupName))?.Id ?? customer.PriceGroupId;
            var alternativeText = Get(row, map, "Alternatif %");
            var order = new Order
            {
                Id = NonEmpty(Get(row, map, "Kimlik"), Guid.NewGuid().ToString("N")),
                Date = Date(Get(row, map, "Tarih")), CustomerId = customer.Id, Description = description, Material = Get(row, map, "Malzeme"),
                WidthCm = Decimal(Get(row, map, "En cm")), HeightCm = Decimal(Get(row, map, "Boy cm")), AreaM2 = Decimal(Get(row, map, "Alan m²")),
                LengthMeter = Decimal(Get(row, map, "Uzunluk m")), DurationMinutes = Decimal(Get(row, map, "Süre dk")),
                Quantity = Math.Max(1, Decimal(Get(row, map, "Adet"))), ExchangeRate = Decimal(Get(row, map, "Kur")),
                CostTotalTl = Decimal(Get(row, map, "Maliyet TL")), SaleTotalTl = Decimal(Get(row, map, "Satış TL")),
                PriceGroupId = groupId, AlternativePercent = string.IsNullOrWhiteSpace(alternativeText) ? null : Decimal(alternativeText), DeviceId = store.State.DeviceId
            };
            var duplicate = store.State.Orders.Any(x => x.Id == order.Id) ||
                (appendOnly && store.State.Orders.Any(x => !x.Deleted && SameOrderMovement(x, order)));
            if (!duplicate) { store.State.Orders.Add(order); report.Orders++; }
        }
    }

    private static void ImportPayments(List<List<string>> rows, DataStore store, ImportReport report, bool appendOnly)
    {
        if (rows.Count < 2) return;
        var map = HeaderMap(rows[0]);
        foreach (var row in rows.Skip(1))
        {
            var amount = Decimal(Get(row, map, "Tutar TL"));
            if (amount <= 0) continue;
            var customer = ResolveCustomer(store, Get(row, map, "Müşteri"), Get(row, map, "Müşteri Kimlik"), report);
            var payment = new Payment
            {
                Id = NonEmpty(Get(row, map, "Kimlik"), Guid.NewGuid().ToString("N")), Date = Date(Get(row, map, "Tarih")),
                CustomerId = customer.Id, AmountTl = amount, PaymentType = Get(row, map, "Ödeme Tipi", "Diğer"),
                Description = Get(row, map, "Açıklama", "Excel içe aktarımı"), DeviceId = store.State.DeviceId
            };
            var duplicate = store.State.Payments.Any(x => x.Id == payment.Id) ||
                (appendOnly && store.State.Payments.Any(x => !x.Deleted && SamePaymentMovement(x, payment)));
            if (!duplicate) { store.State.Payments.Add(payment); report.Payments++; }
        }
    }

    private static void ImportLegacy(Dictionary<string, List<List<string>>> workbook, DataStore store, ImportReport report, bool appendOnly)
    {
        var candidate = workbook.FirstOrDefault(kv => kv.Value.Any(r => r.Any(v => Normalize(v) == "tarih")) && kv.Value.Any(r => r.Any(v => Normalize(v) == "hareket")));
        if (candidate.Value is null)
        {
            report.Warnings.Add("Tanınan BTakip veya eski cari tablosu bulunamadı.");
            return;
        }
        var headerIndex = candidate.Value.FindIndex(r => r.Any(v => Normalize(v) == "tarih") && r.Any(v => Normalize(v) == "hareket"));
        if (headerIndex < 0) return;
        var map = HeaderMap(candidate.Value[headerIndex]);
        var customerName = candidate.Value.Take(headerIndex).SelectMany(x => x).FirstOrDefault(x => !string.IsNullOrWhiteSpace(x)) ?? Path.GetFileNameWithoutExtension(candidate.Key);
        var customer = ResolveCustomer(store, customerName, "", report);

        foreach (var row in candidate.Value.Skip(headerIndex + 1))
        {
            var movement = Normalize(Get(row, map, "Hareket"));
            var description = Get(row, map, "Açıklama");
            var date = Date(Get(row, map, "Tarih"));
            if (movement.Contains("tahsilat"))
            {
                var amount = FirstPositive(Get(row, map, "Alacağınız"), Get(row, map, "Toplam Fiyat"), Get(row, map, "Borcunuz"));
                if (amount <= 0) continue;
                var text = NonEmpty(description, "Eski Excel tahsilatı");
                if (appendOnly && store.State.Payments.Any(x => !x.Deleted && x.CustomerId == customer.Id && x.Date.Date == date.Date && x.AmountTl == amount && Normalize(x.Description) == Normalize(text))) continue;
                store.State.Payments.Add(new Payment { Date = date, CustomerId = customer.Id, AmountTl = amount, Description = text, PaymentType = Get(row, map, "Ödeme Tipi", "Diğer"), DeviceId = store.State.DeviceId });
                report.Payments++;
            }
            else if (movement.Contains("satis") || movement.Contains("satış"))
            {
                var amount = FirstPositive(Get(row, map, "Borcunuz"), Get(row, map, "Toplam Fiyat"));
                var qty = Decimal(Get(row, map, "Adet"));
                var text = NonEmpty(description, Get(row, map, "Grup", "Eski Excel satışı"));
                if (appendOnly && store.State.Orders.Any(x => !x.Deleted && x.CustomerId == customer.Id && x.Date.Date == date.Date && x.SaleTotalTl == amount && Normalize(x.Description) == Normalize(text))) continue;
                store.State.Orders.Add(new Order { Date = date, CustomerId = customer.Id, Description = text, Quantity = qty <= 0 ? 1 : qty, SaleTotalTl = amount, CostTotalTl = amount, ExchangeRate = Decimal(Get(row, map, "KUR")), PriceGroupId = customer.PriceGroupId, DeviceId = store.State.DeviceId });
                report.Orders++;
            }
        }
        report.Warnings.Add("Eski cari düzeni algılandı. Formül sonucu boş olan satırlar 0 TL olarak aktarıldı; dışa aktarılan dosyada kontrol edebilirsiniz.");
    }

    private static Customer ResolveCustomer(DataStore store, string name, string id, ImportReport report)
    {
        Customer? customer = null;
        if (!string.IsNullOrWhiteSpace(id)) customer = store.State.Customers.FirstOrDefault(x => x.Id == id);
        if (customer is null && !string.IsNullOrWhiteSpace(name)) customer = store.State.Customers.FirstOrDefault(x => Normalize(x.Name) == Normalize(name));
        if (customer is not null) return customer;
        customer = new Customer { Id = NonEmpty(id, Guid.NewGuid().ToString("N")), Name = NonEmpty(name, "Excel Müşterisi"), PriceGroupId = "retail", DeviceId = store.State.DeviceId };
        store.State.Customers.Add(customer);
        report.Customers++;
        return customer;
    }

    private static bool SameOrderMovement(Order existing, Order incoming) =>
        existing.CustomerId.Equals(incoming.CustomerId, StringComparison.OrdinalIgnoreCase) &&
        existing.Date.Date == incoming.Date.Date &&
        Normalize(existing.Description) == Normalize(incoming.Description) &&
        Normalize(existing.Material) == Normalize(incoming.Material) &&
        existing.WidthCm == incoming.WidthCm &&
        existing.HeightCm == incoming.HeightCm &&
        existing.AreaM2 == incoming.AreaM2 &&
        existing.LengthMeter == incoming.LengthMeter &&
        existing.DurationMinutes == incoming.DurationMinutes &&
        existing.Quantity == incoming.Quantity &&
        existing.ExchangeRate == incoming.ExchangeRate &&
        existing.CostTotalTl == incoming.CostTotalTl &&
        existing.SaleTotalTl == incoming.SaleTotalTl &&
        existing.PriceGroupId.Equals(incoming.PriceGroupId, StringComparison.OrdinalIgnoreCase) &&
        (existing.AlternativePercent ?? 0m) == (incoming.AlternativePercent ?? 0m);

    private static bool SamePaymentMovement(Payment existing, Payment incoming) =>
        existing.CustomerId.Equals(incoming.CustomerId, StringComparison.OrdinalIgnoreCase) &&
        existing.Date.Date == incoming.Date.Date &&
        existing.AmountTl == incoming.AmountTl &&
        Normalize(existing.PaymentType) == Normalize(incoming.PaymentType) &&
        Normalize(existing.Description) == Normalize(incoming.Description);

    private static Dictionary<string, int> HeaderMap(List<string> row) => row.Select((v, i) => (Key: Normalize(v), Index: i)).Where(x => x.Key.Length > 0).GroupBy(x => x.Key).ToDictionary(g => g.Key, g => g.First().Index);
    private static string Get(List<string> row, Dictionary<string, int> map, string name, string fallback = "") => map.TryGetValue(Normalize(name), out var i) && i < row.Count ? NonEmpty(row[i], fallback) : fallback;
    private static string NonEmpty(string? value, string fallback) => string.IsNullOrWhiteSpace(value) ? fallback : value.Trim();
    private static string Normalize(string value) => value.Trim().ToLower(new CultureInfo("tr-TR")).Replace("ı", "i").Replace("ş", "s").Replace("ğ", "g").Replace("ü", "u").Replace("ö", "o").Replace("ç", "c");
    private static decimal Decimal(string value)
    {
        var text = value.Trim();
        if (text.Contains('.') && !text.Contains(','))
            return decimal.TryParse(text, NumberStyles.Any, CultureInfo.InvariantCulture, out var invariant) ? invariant : 0;
        return decimal.TryParse(text, NumberStyles.Any, new CultureInfo("tr-TR"), out var tr)
            ? tr
            : decimal.TryParse(text, NumberStyles.Any, CultureInfo.InvariantCulture, out var fallback) ? fallback : 0;
    }
    private static decimal FirstPositive(params string[] values) => values.Select(Decimal).FirstOrDefault(x => x > 0);
    private static bool Bool(string value, bool fallback) => string.IsNullOrWhiteSpace(value) ? fallback : value is "1" || value.Equals("true", StringComparison.OrdinalIgnoreCase) || value.Equals("evet", StringComparison.OrdinalIgnoreCase);
    private static DateTime Date(string value) => TryDate(value, out var date) ? date : DateTime.MinValue;
}

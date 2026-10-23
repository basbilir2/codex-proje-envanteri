using System.Reflection;
using BTakip;

var source = Path.Combine(AppContext.BaseDirectory, "sample.xlsx");
var preview = SimpleXlsx.AnalyzeConversion(source);
if (preview.UsedSheets.Count != 1 || preview.UsedSheets[0] != "Hareketler") throw new Exception("Yanlış sayfa seçildi.");
if (preview.SourceRows != 104 || preview.Movements.Count != 104) throw new Exception($"Satır sayısı beklenmiyor: {preview.SourceRows}/{preview.Movements.Count}");
if (preview.Movements.Any(x => x.CustomerName != "AnonPerson_0004")) throw new Exception("Müşteri adı okunamadı.");
if (preview.Movements.Sum(x => x.Debit) != 29257.99m) throw new Exception("Borç toplamı korunmadı.");

var areaMethod = typeof(SimpleXlsx).GetMethod("MeasurementAreaM2", BindingFlags.NonPublic | BindingFlags.Static)!;
decimal Area(string value, string header) => (decimal)areaMethod.Invoke(null, [value, header])!;
if (Area("0,48 m²", "Ölçü / Alan") != 0.48m) throw new Exception("Doğrudan m² okunamadı.");
if (Area("120 × 250 cm", "Ölçü") != 3m) throw new Exception("cm ölçüsü m²'ye çevrilemedi.");

Console.WriteLine($"OK | sayfa={preview.UsedSheets[0]} | satır={preview.SourceRows} | hareket={preview.Movements.Count} | borç={preview.Movements.Sum(x => x.Debit):N2}");

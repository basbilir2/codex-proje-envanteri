import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const sourcePath = "C:/Users/USER/Downloads/siparisler-2026-09-06.xlsx";
const outputDir = "C:/Users/USER/Documents/Codex/outputs/btakip_excel_20260906";
const outputPath = `${outputDir}/siparisler-2026-09-06_BTakip_Aktarim.xlsx`;

const source = await FileBlob.load(sourcePath);
const sourceWorkbook = await SpreadsheetFile.importXlsx(source);
const sourceSheet = sourceWorkbook.worksheets.getItem("siparisler");
const sourceRows = sourceSheet.getUsedRange().values;
const headers = sourceRows[0].map((value) => String(value ?? "").trim());
const indexOf = (name) => headers.indexOf(name);
const get = (row, name) => String(row[indexOf(name)] ?? "").trim();

const months = {
  "oca": 0, "şub": 1, "sub": 1, "mar": 2, "nis": 3,
  "may": 4, "haz": 5, "tem": 6, "ağu": 7, "agu": 7,
  "eyl": 8, "eki": 9, "kas": 10, "ara": 11,
};

function parseDate(value) {
  if (value instanceof Date && !Number.isNaN(value.valueOf())) return value;
  const match = String(value ?? "").trim().match(/^(\d{1,2})\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(\d{4})$/);
  if (!match) return null;
  const month = months[match[2].slice(0, 3).toLocaleLowerCase("tr-TR")];
  if (month === undefined) return null;
  return new Date(Number(match[3]), month, Number(match[1]));
}

function parseNumber(value) {
  const normalized = String(value).trim().replace(/\./g, "").replace(",", ".");
  const number = Number(normalized);
  return Number.isFinite(number) ? number : null;
}

function parseMeasure(...texts) {
  const text = texts.filter(Boolean).join(" | ");
  const dimension = text.match(/(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*(mm|cm|m|metre)\b/i);
  if (dimension) {
    const first = parseNumber(dimension[1]);
    const second = parseNumber(dimension[2]);
    const unit = dimension[3].toLocaleLowerCase("tr-TR");
    if (first && second) {
      if (unit === "mm") return { widthCm: first / 10, heightCm: second / 10, areaM2: null, lengthM: null, text: `${dimension[1]} × ${dimension[2]} mm` };
      if (unit === "cm") return { widthCm: first, heightCm: second, areaM2: null, lengthM: null, text: `${dimension[1]} × ${dimension[2]} cm` };
      return { widthCm: null, heightCm: null, areaM2: first * second, lengthM: null, text: `${dimension[1]} × ${dimension[2]} m` };
    }
  }
  const area = text.match(/(\d+(?:[.,]\d+)?)\s*(?:m²|m2|metrekare)\b/i);
  if (area) {
    const value = parseNumber(area[1]);
    if (value) return { widthCm: null, heightCm: null, areaM2: value, lengthM: null, text: `${area[1]} m²` };
  }
  const length = text.match(/(\d+(?:[.,]\d+)?)\s*(?:m|metre)\b/i);
  if (length) {
    const value = parseNumber(length[1]);
    if (value) return { widthCm: null, heightCm: null, areaM2: null, lengthM: value, text: `${length[1]} m` };
  }
  return { widthCm: null, heightCm: null, areaM2: null, lengthM: null, text: "" };
}

function inferMaterial(sourceMaterial, project) {
  const text = `${sourceMaterial} ${project}`.toLocaleLowerCase("tr-TR");
  if (/\buv\s*bask/.test(text)) return "UV Baskı";
  if (/\bdtf\b/.test(text)) return "DTF Baskı";
  return "";
}

const sourceData = sourceRows.slice(1).filter((row) => row.some((value) => String(value ?? "").trim() !== ""));
const customerNames = [...new Set(sourceData.map((row) => get(row, "Müşteri")).filter(Boolean))];
const orderRows = [];
const controlRows = [];
const unresolvedMaterials = new Map();

for (let offset = 0; offset < sourceData.length; offset += 1) {
  const row = sourceData[offset];
  const customer = get(row, "Müşteri");
  const project = get(row, "Proje");
  const sourceMaterial = get(row, "Malzeme");
  const sourceMeasure = get(row, "Ölçü");
  const date = parseDate(get(row, "Geliş tarihi"));
  const quantity = parseNumber(get(row, "Adet")) ?? 1;
  const status = get(row, "Durum");
  const priority = get(row, "Öncelik");
  const measure = parseMeasure(sourceMeasure === "—" ? "" : sourceMeasure, project, sourceMaterial);
  const material = inferMaterial(sourceMaterial, project);
  const note = [
    project && `Proje: ${project}`,
    sourceMaterial && sourceMaterial !== "Diğer" && `Kaynak malzeme: ${sourceMaterial}`,
    status && `Durum: ${status}`,
    priority && `Öncelik: ${priority}`,
    measure.text && `Ölçü: ${measure.text}`,
  ].filter(Boolean).join(" | ");

  const reasons = [];
  if (!material) reasons.push("Malzeme varyantı/fiyat tanımı kesin değil; boş bırakıldı.");
  if (!measure.text) reasons.push("Güvenilir ölçü bulunamadı; boş bırakıldı.");
  if (!date) reasons.push("Tarih okunamadı; boş bırakıldı.");

  orderRows.push([
    "",
    customer || "",
    date,
    note,
    material,
    measure.widthCm,
    measure.heightCm,
    measure.areaM2,
    measure.lengthM,
    "",
    quantity,
    "",
    "",
    "",
    "",
  ]);
  controlRows.push([
    offset + 2,
    customer,
    project,
    sourceMaterial,
    date,
    material,
    measure.text,
    reasons.join(" "),
  ]);
  if (!material) {
    const key = sourceMaterial || "Belirtilmemiş";
    if (!unresolvedMaterials.has(key)) unresolvedMaterials.set(key, project);
  }
}

const workbook = Workbook.create();
const customersSheet = workbook.worksheets.add("Müşteriler");
const ordersSheet = workbook.worksheets.add("Siparişler");
const paymentsSheet = workbook.worksheets.add("Tahsilatlar");
const newMaterialsSheet = workbook.worksheets.add("Tespit Edilen Yeni Malzemeler");
const controlSheet = workbook.worksheets.add("Dönüşüm Kontrolü");

const customerHeaders = ["Kimlik", "Ad", "Firma", "Telefon", "E-posta", "Fiyat Grubu", "Not"];
const customerRows = customerNames.map((name) => ["", name, "", "", "", "", "Kaynak sipariş listesinden oluşturuldu. Fiyat grubu kaynakta belirtilmedi."]);
const orderHeaders = ["Kimlik", "Müşteri", "Tarih", "Açıklama", "Malzeme", "En cm", "Boy cm", "Alan m²", "Uzunluk m", "Süre dk", "Adet", "Kur", "Maliyet TL", "Satış TL", "Alternatif %"];
const paymentHeaders = ["Kimlik", "Müşteri", "Tarih", "Tutar TL", "Ödeme Tipi", "Açıklama"];
const newMaterialHeaders = ["Kaynak Malzeme", "Kaynak Proje Örneği", "Önerilen İşlem", "Not"];
const controlHeaders = ["Kaynak Satır", "Müşteri", "Kaynak Proje", "Kaynak Malzeme", "Tarih", "BTakip Malzeme", "Bulunan Ölçü", "Dönüşüm Notu"];
const newMaterialRows = [...unresolvedMaterials.entries()].map(([material, project]) => [
  material,
  project,
  "Fiyat Tanımlarında varyantı doğrula",
  "Ölçü veya varyant kesin olmadığı için Siparişler sayfasındaki Malzeme alanı boş bırakıldı.",
]);

function writeTable(sheet, headersRow, dataRows, name, widths) {
  sheet.getRangeByIndexes(0, 0, 1, headersRow.length).values = [headersRow];
  if (dataRows.length) sheet.getRangeByIndexes(1, 0, dataRows.length, headersRow.length).values = dataRows;
  const lastRow = Math.max(2, dataRows.length + 1);
  const range = sheet.getRangeByIndexes(0, 0, lastRow, headersRow.length);
  range.format.font = { name: "Aptos", size: 10, color: "#173446" };
  sheet.getRangeByIndexes(0, 0, 1, headersRow.length).format = { fill: "#173F52", font: { name: "Aptos", size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", verticalAlignment: "center" };
  sheet.getRangeByIndexes(0, 0, lastRow, headersRow.length).format.borders = { preset: "all", style: "thin", color: "#DCE5E8" };
  sheet.getRangeByIndexes(1, 0, Math.max(1, dataRows.length), headersRow.length).format.verticalAlignment = "center";
  sheet.getRangeByIndexes(1, 0, Math.max(1, dataRows.length), headersRow.length).format.wrapText = true;
  widths.forEach((width, index) => { sheet.getRangeByIndexes(0, index, lastRow, 1).format.columnWidth = width; });
  sheet.getRangeByIndexes(0, 0, 1, headersRow.length).format.rowHeight = 26;
  sheet.freezePanes.freezeRows(1);
  sheet.tables.add(`A1:${String.fromCharCode(64 + headersRow.length)}${lastRow}`, true, name);
  sheet.showGridLines = false;
}

writeTable(customersSheet, customerHeaders, customerRows, "MusterilerTable", [16, 28, 20, 16, 28, 18, 42]);
writeTable(ordersSheet, orderHeaders, orderRows, "SiparislerTable", [16, 28, 14, 50, 20, 11, 11, 12, 12, 12, 10, 12, 14, 14, 14]);
writeTable(paymentsSheet, paymentHeaders, [], "TahsilatlarTable", [16, 28, 14, 14, 18, 42]);
writeTable(newMaterialsSheet, newMaterialHeaders, newMaterialRows, "YeniMalzemelerTable", [22, 50, 32, 52]);
writeTable(controlSheet, controlHeaders, controlRows, "DonusumKontrolTable", [12, 28, 48, 20, 14, 20, 16, 48]);

ordersSheet.getRange(`C2:C${orderRows.length + 1}`).format.numberFormat = "yyyy-mm-dd";
ordersSheet.getRange(`F2:O${orderRows.length + 1}`).format.numberFormat = "#,##0.00";
controlSheet.getRange(`E2:E${controlRows.length + 1}`).format.numberFormat = "yyyy-mm-dd";
customersSheet.tabColor = "#1F7A8C";
ordersSheet.tabColor = "#1F7A8C";
controlSheet.tabColor = "#C66C38";
newMaterialsSheet.tabColor = "#C66C38";

const check = await workbook.inspect({ kind: "table", range: "Siparişler!A1:O12", include: "values,formulas", tableMaxRows: 12, tableMaxCols: 15 });
console.log(check.ndjson);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 50 }, summary: "final formula error scan" });
console.log(errors.ndjson);
const preview = await workbook.render({ sheetName: "Siparişler", range: "A1:O16", scale: 1.25, format: "png" });
await fs.writeFile(`${outputDir}/siparisler_preview.png`, new Uint8Array(await preview.arrayBuffer()));
await fs.mkdir(outputDir, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(JSON.stringify({ outputPath, orderCount: orderRows.length, customerCount: customerRows.length, inferredMaterials: orderRows.filter((row) => row[4]).length, parsedMeasures: orderRows.filter((row) => row[5] || row[6] || row[7] || row[8]).length }));

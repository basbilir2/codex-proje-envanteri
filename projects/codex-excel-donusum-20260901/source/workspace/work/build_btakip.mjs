import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const sourcePath = "C:/Users/USER/Downloads/AnonPerson_0004 - AnonPerson_0008.xlsx";
const outputDir = "C:/Users/USER/Documents/Codex/2026-09-01/excel-conversion-workspace/outputs/01a05e70-btakip-asi";
const outputPath = `${outputDir}/ASI_Reklam_AnonPerson_0008_BTakip.xlsx`;
const verificationDir = "C:/Users/USER/Documents/Codex/2026-09-01/excel-conversion-workspace/work/verification";

function excelSerialToDate(serial) {
  return new Date(Date.UTC(1899, 11, 30) + Math.round(Number(serial) * 86400000));
}

function toText(value) {
  return typeof value === "string" ? value.trim() : "";
}

function isFiniteNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function fixedMeasure(value) {
  return Number(value).toFixed(2);
}

function formatTurkishNumber(value) {
  return Number(value).toFixed(2).replace(".", ",");
}

function extractExplicitMeasure(text) {
  if (!text) return { text: "", measure: "" };

  let cleaned = text;
  let measure = "";
  const dimensions = cleaned.match(/(\d+(?:[.,]\d+)?)\s*(?:cm)?\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*cm\b/i);
  if (dimensions) {
    measure = `${dimensions[1].replace(",", ".")} × ${dimensions[2].replace(",", ".")} cm`;
    cleaned = cleaned.replace(dimensions[0], " ");
  } else {
    const area = cleaned.match(/(\d+(?:[.,]\d+)?)\s*m(?:2|²)\b/i);
    if (area) {
      measure = `${area[1].replace(",", ".")} m²`;
      cleaned = cleaned.replace(area[0], " ");
    }
  }

  cleaned = cleaned.replace(/\s*[—–|-]\s*(?=$)/g, "").replace(/\s{2,}/g, " ").trim();
  return { text: cleaned, measure };
}

function inferredMeasure(group, quantity) {
  if (!isFiniteNumber(quantity)) return "";
  const normalized = group.toLocaleLowerCase("tr-TR");
  if (normalized.includes("dtf")) return `${fixedMeasure(quantity)} m`;
  if (
    normalized.includes("branda") ||
    normalized.includes("folyo") ||
    normalized.includes("oneway") ||
    normalized.includes("poster") ||
    normalized.includes("citylight") ||
    normalized.includes("kanvas") ||
    normalized.includes("kumlama")
  ) {
    return `${fixedMeasure(quantity)} m²`;
  }
  return fixedMeasure(quantity);
}

function joinNotes(parts) {
  return parts.filter(Boolean).join(" | ");
}

const input = await FileBlob.load(sourcePath);
const sourceWorkbook = await SpreadsheetFile.importXlsx(input);
const sourceSheet = sourceWorkbook.worksheets.getItem("Cari");
const sourceRows = sourceSheet.getRange("A3:M85").values;

const converted = [];
let sourceRowNumber = 3;

for (const row of sourceRows) {
  const [dateValue, movementValue, groupValue, descriptionValue, quantity, adet, unitPrice, rate, totalPrice, debtValue, collectionValue, runningTotal, paymentNote] = row;
  const hasRealDate = isFiniteNumber(dateValue) && dateValue > 30000 && dateValue < 70000;
  const group = toText(groupValue);
  const sourceDescription = toText(descriptionValue);
  const sourcePaymentNote = toText(paymentNote);
  const hasRealRecord = hasRealDate && (group || sourceDescription || isFiniteNumber(quantity));

  if (!hasRealRecord) {
    sourceRowNumber += 1;
    continue;
  }

  const movement = toText(movementValue);
  const combinedSourceText = joinNotes([sourceDescription, sourcePaymentNote]);
  const extracted = extractExplicitMeasure(combinedSourceText);
  const measure = extracted.measure || inferredMeasure(group, quantity);
  const notes = [];

  if (extracted.text) notes.push(extracted.text);

  const financialValuesExist = isFiniteNumber(totalPrice) || isFiniteNumber(debtValue);
  const debt = isFiniteNumber(debtValue) && financialValuesExist ? debtValue : null;
  const collection = isFiniteNumber(collectionValue) && financialValuesExist ? collectionValue : null;

  if (isFiniteNumber(unitPrice) && unitPrice > 0 && isFiniteNumber(debtValue) && debtValue > 0) {
    notes.push(`Birim fiyat: ${formatTurkishNumber(unitPrice)}`);
  }

  if (!movement) {
    notes.push("KONTROL: Kaynakta hareket türü boş.");
  }
  if (!financialValuesExist) {
    notes.push("KONTROL: Finansal tutar kaynakta boş.");
  }
  if (group.toLocaleLowerCase("tr-TR") === "dtf" && Number(rate) === 0 && Number(debtValue) === 0) {
    const unitPriceText = isFiniteNumber(unitPrice) ? formatTurkishNumber(unitPrice) : "boş";
    notes.push(`KONTROL: DTF birim fiyatı ${unitPriceText}, KUR 0 ve borç/toplam 0 görünüyor.`);
  }
  if (group.toLocaleLowerCase("tr-TR") === "branda" && /kanvas/i.test(sourceDescription)) {
    notes.push("KONTROL: Grup Branda, açıklama Kanvas; malzeme doğrulanmalı.");
  }
  if (isFiniteNumber(adet) && adet !== 1) {
    notes.push(`Adet: ${adet}`);
  }

  converted.push({
    sourceRowNumber,
    date: excelSerialToDate(dateValue),
    movement,
    description: joinNotes(notes),
    material: group,
    measure,
    debt,
    collection,
    sourceRunningTotal: isFiniteNumber(runningTotal) ? runningTotal : null,
  });

  sourceRowNumber += 1;
}

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("BTakip");
sheet.showGridLines = false;
sheet.freezePanes.freezeRows(1);

const headers = [["Tarih", "Hareket", "Açıklama", "Malzeme", "Ölçü", "Borç", "Tahsilat", "Bakiye"]];
sheet.getRange("A1:H1").values = headers;

const outputRows = converted.map((row) => [
  row.date,
  row.movement || null,
  row.description || null,
  row.material || null,
  row.measure || null,
  row.debt,
  row.collection,
]);

const lastRow = converted.length + 1;
sheet.getRange(`A2:G${lastRow}`).values = outputRows;
sheet.getRange("H2").formulas = [["=IF(COUNTA(A2:G2)=0,\"\",N(F2)-N(G2))"]];
if (lastRow >= 3) {
  sheet.getRange("H3").formulas = [["=IF(COUNTA(A3:G3)=0,\"\",N(H2)+N(F3)-N(G3))"]];
  sheet.getRange(`H3:H${lastRow}`).fillDown();
}

const table = sheet.tables.add(`A1:H${lastRow}`, true, "BTakipHareketleri");
table.style = "TableStyleMedium2";
table.showBandedColumns = false;
table.showFilterButton = true;

sheet.getRange("A1:H1").format = {
  fill: "#1F4E78",
  font: { bold: true, color: "#FFFFFF", size: 11 },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  rowHeight: 28,
  wrapText: true,
  borders: { preset: "outside", style: "thin", color: "#17365D" },
};

sheet.getRange(`A2:H${lastRow}`).format = {
  font: { color: "#1F2937", size: 10 },
  verticalAlignment: "center",
  rowHeight: 27,
};
sheet.getRange(`A2:A${lastRow}`).format.horizontalAlignment = "center";
sheet.getRange(`A2:A${lastRow}`).format.numberFormat = "dd\".\"mm\".\"yyyy";
sheet.getRange(`B2:B${lastRow}`).format.horizontalAlignment = "center";
sheet.getRange(`C2:C${lastRow}`).format = { wrapText: true, horizontalAlignment: "left" };
sheet.getRange(`D2:D${lastRow}`).format.horizontalAlignment = "left";
sheet.getRange(`E2:E${lastRow}`).format.horizontalAlignment = "center";
sheet.getRange(`F2:H${lastRow}`).format.horizontalAlignment = "right";
sheet.getRange(`F2:H${lastRow}`).setNumberFormat("#,##0.00");

sheet.getRange(`A1:A${lastRow}`).format.columnWidth = 14;
sheet.getRange(`B1:B${lastRow}`).format.columnWidth = 12;
sheet.getRange(`C1:C${lastRow}`).format.columnWidth = 62;
sheet.getRange(`D1:D${lastRow}`).format.columnWidth = 22;
sheet.getRange(`E1:E${lastRow}`).format.columnWidth = 14;
sheet.getRange(`F1:H${lastRow}`).format.columnWidth = 15;

sheet.getRange(`B2:B${lastRow}`).dataValidation = {
  rule: { type: "list", values: ["Satış", "Tahsilat"] },
};
sheet.getRange(`C2:C${lastRow}`).conditionalFormats.add("containsText", {
  text: "KONTROL:",
  format: { fill: "#FFF2CC", font: { color: "#7F6000" } },
});

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(verificationDir, { recursive: true });

const verificationTable = await workbook.inspect({
  kind: "table",
  range: `BTakip!A1:H${lastRow}`,
  include: "values,formulas",
  tableMaxRows: 60,
  tableMaxCols: 8,
  maxChars: 30000,
});
const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
const preview = await workbook.render({
  sheetName: "BTakip",
  range: `A1:H${lastRow}`,
  scale: 1.5,
  format: "png",
});
await fs.writeFile(`${verificationDir}/BTakip_preview.png`, new Uint8Array(await preview.arrayBuffer()));

const exported = await SpreadsheetFile.exportXlsx(workbook);
await exported.save(outputPath);

const summary = {
  outputPath,
  recordCount: converted.length,
  salesCount: converted.filter((row) => row.movement === "Satış").length,
  blankMovementCount: converted.filter((row) => !row.movement).length,
  missingFinancialCount: converted.filter((row) => row.debt === null && row.collection === null).length,
  debtTotal: converted.reduce((sum, row) => sum + (row.debt ?? 0), 0),
  collectionTotal: converted.reduce((sum, row) => sum + (row.collection ?? 0), 0),
  firstDate: converted.reduce((min, row) => (!min || row.date < min ? row.date : min), null)?.toISOString().slice(0, 10),
  lastDate: converted.reduce((max, row) => (!max || row.date > max ? row.date : max), null)?.toISOString().slice(0, 10),
  formulaErrors: formulaErrors.ndjson,
  verificationTable: verificationTable.ndjson,
};

await fs.writeFile(`${verificationDir}/summary.json`, JSON.stringify(summary, null, 2), "utf8");
console.log(JSON.stringify({ ...summary, verificationTable: undefined }, null, 2));

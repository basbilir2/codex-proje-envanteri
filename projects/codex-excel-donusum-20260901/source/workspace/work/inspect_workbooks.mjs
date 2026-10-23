import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const sourcePath = "C:/Users/USER/Downloads/AnonPerson_0004 - AnonPerson_0008.xlsx";
const referencePath = "C:/Users/USER/.codex/.chatgpt-projects/g-p-6a9465391f5481918301e2b7174d134b/outputs/01a05bc0-btakip-AnonPerson_0001/Arya_Reklam_BTakip_Aktarim.xlsx";
const importTemplate2Path = "C:/Users/USER/AppData/Local/Temp/codex-file-preview-h716ru/AKTARIM (2).xlsx";
const importTemplate1Path = "C:/Users/USER/AppData/Local/Temp/codex-file-preview-JqU0gb/AKTARIM (1).xlsx";
const outDir = "C:/Users/USER/Documents/Codex/2026-09-01/excel-conversion-workspace/work/inspection";

const focusedRanges = {
  "source:Cari": "A1:M85",
  "source:Cari_Bilgileri": "A1:B11",
  "source:Değerler": "A1:B30",
  "import_template_2:Cari": "A1:S2",
  "import_template_2:Hareket": "A1:AJ11",
  "import_template_1:Müşteriler": "A1:J2",
  "import_template_1:Hareketler": "A1:O11",
  "reference:Müşteriler": "A1:L4",
  "reference:Fiyat Grupları": "A1:H5",
  "reference:Fiyatlar": "A1:P19",
  "reference:Siparişler": "A1:U30",
  "reference:Tahsilatlar": "A1:K10",
  "reference:Ayarlar": "A1:C6",
};

await fs.mkdir(outDir, { recursive: true });

async function inspectWorkbook(label, filePath) {
  const input = await FileBlob.load(filePath);
  const workbook = await SpreadsheetFile.importXlsx(input);
  const summary = await workbook.inspect({
    kind: "workbook,sheet,table,drawing",
    include: "id,name,values,formulas",
    maxChars: 12000,
    tableMaxRows: 12,
    tableMaxCols: 16,
    tableMaxCellChars: 160,
  });

  const sheets = [];
  for (let i = 0; i < workbook.worksheets.items.length; i += 1) {
    const sheet = workbook.worksheets.getItemAt(i);
    const used = sheet.getUsedRange();
    const usedValues = used?.values ?? [];
    const usedFormulas = used?.formulas ?? [];
    const usedAddress = used?.address ?? null;
    const styleProbe = await workbook.inspect({
      kind: "computedStyle",
      sheetId: sheet.name,
      range: usedAddress || "A1:Z30",
      maxChars: 5000,
    });
    const formulaProbe = await workbook.inspect({
      kind: "formula",
      sheetId: sheet.name,
      range: usedAddress || "A1:Z200",
      maxChars: 6000,
      options: { maxResults: 150 },
    });
    const preview = await workbook.render({
      sheetName: sheet.name,
      range: focusedRanges[`${label}:${sheet.name}`] || usedAddress || "A1:Z30",
      scale: 1.5,
      format: "png",
    });
    const safeName = sheet.name.replace(/[\\/:*?"<>|]/g, "_");
    const previewPath = path.join(outDir, `${label}_${i + 1}_${safeName}.png`);
    await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
    sheets.push({
      name: sheet.name,
      usedAddress,
      values: usedValues,
      formulas: usedFormulas,
      styleProbe: styleProbe.ndjson,
      formulaProbe: formulaProbe.ndjson,
      previewPath,
    });
  }

  const report = {
    label,
    filePath,
    summary: summary.ndjson,
    sheets,
  };
  const reportPath = path.join(outDir, `${label}.json`);
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2), "utf8");
  return {
    label,
    reportPath,
    sheets: sheets.map((sheet) => ({
      name: sheet.name,
      usedAddress: sheet.usedAddress,
      rows: sheet.values.length,
      cols: Math.max(0, ...sheet.values.map((row) => row.length)),
      previewPath: sheet.previewPath,
    })),
    summary: summary.ndjson,
  };
}

const results = [];
results.push(await inspectWorkbook("source", sourcePath));
results.push(await inspectWorkbook("reference", referencePath));
results.push(await inspectWorkbook("import_template_2", importTemplate2Path));
results.push(await inspectWorkbook("import_template_1", importTemplate1Path));
console.log(JSON.stringify(results, null, 2));

import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const workDir = "C:/Users/USER/Documents/Codex/2026-08-14/referenced-chatgpt-conversation-this-is-an/work/spreadsheet";
const sourcePath = "C:/Users/USER/Downloads/AnonPerson_0005.xlsx";
const templatePath = "C:/Users/USER/Downloads/Siparis-Deneme.xlsx";
const inspectDir = path.join(workDir, "inspection");
const buildRequested = process.argv.includes("--build");

await fs.mkdir(inspectDir, { recursive: true });

function parseNdjson(ndjson) {
  return ndjson
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

async function inspectWorkbook(label, filePath, { renderPreviews = true } = {}) {
  const input = await FileBlob.load(filePath);
  const workbook = await SpreadsheetFile.importXlsx(input);
  const sheetInspection = await workbook.inspect({
    kind: "sheet",
    include: "id,name",
    maxChars: 10000,
  });
  const sheetRecords = parseNdjson(sheetInspection.ndjson);
  const sheetNames = sheetRecords
    .map((record) => record.name)
    .filter((name) => typeof name === "string");

  const summary = await workbook.inspect({
    kind: "workbook,sheet,table",
    maxChars: 20000,
    tableMaxRows: 12,
    tableMaxCols: 16,
    tableMaxCellChars: 200,
  });

  const result = {
    label,
    filePath,
    sheetInspection: sheetInspection.ndjson,
    summary: summary.ndjson,
    sheets: [],
  };

  for (let index = 0; index < sheetNames.length; index += 1) {
    const sheetName = sheetNames[index];
    const sheet = workbook.worksheets.getItem(sheetName);
    const usedRange = sheet.getUsedRange();
    const values = usedRange ? usedRange.values : [];
    const formulas = usedRange ? usedRange.formulas : [];
    let regionInspection = { ndjson: "" };
    let styleInspection = { ndjson: "" };
    let drawingInspection = { ndjson: "" };
    let previewPath = null;

    if (renderPreviews) {
      regionInspection = await workbook.inspect({
        kind: "region",
        sheetId: sheetName,
        range: "A1:AZ1000",
        maxChars: 30000,
        tableMaxRows: 60,
        tableMaxCols: 30,
        tableMaxCellChars: 250,
      });
      styleInspection = await workbook.inspect({
        kind: "computedStyle",
        sheetId: sheetName,
        range: "A1:Z30",
        maxChars: 12000,
      });
      drawingInspection = await workbook.inspect({
        kind: "drawing",
        sheetId: sheetName,
        maxChars: 5000,
      });

      const preview = await workbook.render({
        sheetName,
        autoCrop: "all",
        scale: 1.5,
        format: "png",
      });
      previewPath = path.join(inspectDir, `${label}-${index + 1}.png`);
      await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
    }

    result.sheets.push({
      name: sheetName,
      values,
      formulas,
      regionInspection: regionInspection.ndjson,
      styleInspection: styleInspection.ndjson,
      drawingInspection: drawingInspection.ndjson,
      previewPath,
    });
  }

  return { workbook, result };
}

const source = await inspectWorkbook("source", sourcePath, { renderPreviews: !buildRequested });
const template = await inspectWorkbook("template", templatePath, { renderPreviews: !buildRequested });

function toText(value) {
  return value === null || value === undefined ? "" : String(value).trim();
}

function excelSerialToDate(serial) {
  if (typeof serial !== "number" || !Number.isFinite(serial)) return null;
  return new Date(Date.UTC(1899, 11, 30 + Math.floor(serial)));
}

function findMeasureMatches(text) {
  const value = toText(text);
  if (!value) return [];

  const dimensionPattern = /\d+(?:[.,]\d+)?\s*(?:mm|cm|metre|meter)?\s*[xX×]\s*\d+(?:[.,]\d+)?\s*(?:mm|cm|metre|meter)?(?:\s*[xX×]\s*\d+(?:[.,]\d+)?\s*(?:mm|cm|metre|meter)?)?/giu;
  const unitPattern = /\d+(?:[.,]\d+)?\s*(?:mm|cm|metre|meter)\b/giu;
  const matches = [];
  const occupied = [];

  for (const match of value.matchAll(dimensionPattern)) {
    matches.push({ raw: match[0], index: match.index ?? 0 });
    occupied.push([match.index ?? 0, (match.index ?? 0) + match[0].length]);
  }
  for (const match of value.matchAll(unitPattern)) {
    const start = match.index ?? 0;
    const end = start + match[0].length;
    if (!occupied.some(([from, to]) => start >= from && end <= to)) {
      matches.push({ raw: match[0], index: start });
    }
  }

  return matches.sort((a, b) => a.index - b.index);
}

function normalizeMeasure(raw) {
  return raw
    .replace(/[X×]/gu, "x")
    .replace(/\s*x\s*/gu, " x ")
    .replace(/\s*(mm|cm|metre|meter)\b/giu, " $1")
    .replace(/\s+/gu, " ")
    .trim();
}

function extractMeasure(...values) {
  const measures = [];
  for (const value of values) {
    for (const match of findMeasureMatches(value)) {
      const normalized = normalizeMeasure(match.raw);
      if (!measures.some((item) => item.toLocaleLowerCase("tr-TR") === normalized.toLocaleLowerCase("tr-TR"))) {
        measures.push(normalized);
      }
    }
  }
  return measures.join(" / ");
}

function extractName(description) {
  const original = toText(description);
  if (!original) return "";

  let cleaned = original;
  const matches = findMeasureMatches(original).sort((a, b) => b.index - a.index);
  for (const match of matches) {
    cleaned = `${cleaned.slice(0, match.index)}${cleaned.slice(match.index + match.raw.length)}`;
  }

  cleaned = cleaned
    .replace(/\(\s*\)|\[\s*\]/gu, " ")
    .replace(/^\s*[-–—/+,:;]+|[-–—/+,:;]+\s*$/gu, "")
    .replace(/\s*\(\s*[-–—/+,:;]*\s*\)\s*/gu, " ")
    .replace(/\s{2,}/gu, " ")
    .trim();

  if (/^\d+(?:[.,]\d+)?\s*(?:dk|dakika)$/iu.test(cleaned)) return "";
  if (/^(?:pleksi|folyo|branda|baskes|dtf|uv baskı|lazer kesim)$/iu.test(cleaned)) return "";
  if (/^(?:mm|cm|metre|meter)$/iu.test(cleaned)) return "";
  return cleaned;
}

function extractOrders(values) {
  const orders = [];
  for (let index = 2; index < Math.min(values.length, 220); index += 1) {
    const row = values[index] ?? [];
    const movement = toText(row[1]).toLocaleLowerCase("tr-TR");
    if (movement !== "satış") continue;

    const hasOrderContent = [row[0], row[2], row[3], row[12], row[13], row[14]].some(
      (value) => toText(value) !== "",
    );
    if (!hasOrderContent) continue;

    const date = excelSerialToDate(row[0]);
    const material = toText(row[2]);
    const description = toText(row[3]);
    const name = extractName(description);
    const measure = extractMeasure(description, row[12], row[13], row[14]);

    orders.push({
      sourceRow: index + 1,
      dateSerial: typeof row[0] === "number" ? row[0] : null,
      date,
      dateIso: date ? date.toISOString().slice(0, 10) : "",
      name,
      material,
      measure,
      description,
      extraNotes: [row[12], row[13], row[14]].map(toText).filter(Boolean).join(" | "),
    });
  }
  return orders;
}

const orders = extractOrders(source.result.sheets[0].values);

const groupClassification = new Map([
  ["Bant Çift Taraf", { material: "Bant Çift Taraf", service: "" }],
  ["Baskes", { material: "", service: "Baskes" }],
  ["Baskes Temizle", { material: "", service: "Baskes Temizle" }],
  ["Baskes Transfer Taşıyıcı", { material: "Taşıyıcı", service: "Baskes Transfer" }],
  ["Branda", { material: "Branda", service: "" }],
  ["Dekota", { material: "Dekota", service: "" }],
  ["Dekota + Folyo", { material: "Dekota + Folyo", service: "" }],
  ["Dekota + Lazer", { material: "Dekota", service: "Lazer Kesim" }],
  ["Dekota + Lazer + UV", { material: "Dekota + UV", service: "Lazer Kesim" }],
  ["Dekota + UV", { material: "Dekota + UV", service: "" }],
  ["DTF", { material: "DTF", service: "" }],
  ["Folyo", { material: "Folyo", service: "" }],
  ["Folyo GOLD", { material: "Folyo GOLD", service: "" }],
  ["Karton Ayak - Destek", { material: "Karton Ayak - Destek", service: "" }],
  ["Lazer Kesim", { material: "", service: "Lazer Kesim" }],
  ["Pleksi", { material: "Pleksi", service: "" }],
  ["Pleksi + Lazer Kesim", { material: "Pleksi", service: "Lazer Kesim" }],
  ["Pleksi + Lazer Kesim + Kazıma", { material: "Pleksi", service: "Lazer Kesim + Kazıma" }],
  ["Pleksi + Lazer Kesim + UV", { material: "Pleksi + UV", service: "Lazer Kesim" }],
  ["Pleksi + UV", { material: "Pleksi + UV", service: "" }],
  ["Plotter Kesim", { material: "", service: "Plotter Kesim" }],
  ["Plotter Kesim + Taşıyıcı", { material: "Taşıyıcı", service: "Plotter Kesim" }],
  ["Taşıyıcı", { material: "Taşıyıcı", service: "" }],
  ["UV BASKI", { material: "UV", service: "Baskı" }],
]);

function splitThicknessFromMeasure(measure) {
  const thicknesses = [];
  const dimensions = [];
  for (const part of toText(measure).split(/\s*\/\s*/u).filter(Boolean)) {
    const thickness = part.match(/^(\d+(?:[.,]\d+)?)\s*mm$/iu);
    if (thickness) {
      thicknesses.push(`${thickness[1]} mm`);
    } else {
      dimensions.push(part);
    }
  }
  return {
    thickness: thicknesses.join(" / "),
    measure: dimensions.join(" / "),
  };
}

function classifyOrder(order) {
  const classification = groupClassification.get(order.material);
  if (!classification) {
    throw new Error(`Sınıflandırılmamış grup: ${order.material}`);
  }
  const measurement = splitThicknessFromMeasure(order.measure);
  return {
    ...order,
    material: [measurement.thickness, classification.material].filter(Boolean).join(" "),
    service: classification.service,
    measure: measurement.measure,
  };
}

const classifiedOrders = orders.map(classifyOrder);

async function buildFinalWorkbook() {
  const outputDir = "C:/Users/USER/Documents/Codex/2026-08-14/referenced-chatgpt-conversation-this-is-an/outputs/01a000ec-5d8b-74b0-a968-2e94222a7cf3";
  const outputPath = path.join(outputDir, "Siparis-Deneme-Duzenlenmis.xlsx");
  const verificationDir = path.join(workDir, "verification");
  const previewPath = path.join(verificationDir, "final-before-export.png");
  const exportedPreviewPath = path.join(verificationDir, "final-exported.png");
  await fs.mkdir(outputDir, { recursive: true });
  await fs.mkdir(verificationDir, { recursive: true });

  const workbook = template.workbook;
  const sheet = workbook.worksheets.getItem("Siparişler");
  const lastRow = classifiedOrders.length + 1;
  const oldLastRow = Math.max(template.result.sheets[0].values.length, 4);

  sheet.getRange(`A1:E${oldLastRow}`).clear({ applyTo: "contents" });
  sheet.getRange("A1:E1").values = [["Tarih", "İsim", "Malzeme", "Hizmet", "Ölçü"]];
  sheet.getRange(`A2:E${lastRow}`).values = classifiedOrders.map((order) => [
    order.dateSerial,
    order.name || null,
    order.material || null,
    order.service || null,
    order.measure || null,
  ]);

  sheet.getRange(`A2:A${lastRow}`).setNumberFormat("yyyy-mm-dd");
  sheet.getRange(`D2:E${lastRow}`).setNumberFormat("@");
  sheet.getRange(`A1:A${lastRow}`).format.columnWidth = 13;
  sheet.getRange(`B1:B${lastRow}`).format.columnWidth = 42;
  sheet.getRange(`C1:C${lastRow}`).format.columnWidth = 28;
  sheet.getRange(`D1:D${lastRow}`).format.columnWidth = 26;
  sheet.getRange(`E1:E${lastRow}`).format.columnWidth = 25;

  const topCheck = await workbook.inspect({
    kind: "table",
    range: `Siparişler!A1:E15`,
    include: "values,formulas",
    tableMaxRows: 15,
    tableMaxCols: 5,
    maxChars: 10000,
  });
  const bottomCheck = await workbook.inspect({
    kind: "table",
    range: `Siparişler!A${Math.max(2, lastRow - 14)}:E${lastRow}`,
    include: "values,formulas",
    tableMaxRows: 15,
    tableMaxCols: 5,
    maxChars: 10000,
  });
  const formulaErrors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 300 },
    summary: "final formula error scan",
  });
  const preview = await workbook.render({
    sheetName: "Siparişler",
    range: `A1:E${lastRow}`,
    scale: 1.2,
    format: "png",
  });
  await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));

  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(outputPath);

  const finalBlob = await FileBlob.load(outputPath);
  const finalWorkbook = await SpreadsheetFile.importXlsx(finalBlob);
  const finalCheck = await finalWorkbook.inspect({
    kind: "table",
    range: `Siparişler!A1:E${lastRow}`,
    include: "values,formulas",
    tableMaxRows: 8,
    tableMaxCols: 5,
    maxChars: 8000,
  });
  const finalErrors = await finalWorkbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 300 },
    summary: "exported workbook formula error scan",
  });
  const exportedPreview = await finalWorkbook.render({
    sheetName: "Siparişler",
    range: `A1:E${lastRow}`,
    scale: 1.2,
    format: "png",
  });
  await fs.writeFile(exportedPreviewPath, new Uint8Array(await exportedPreview.arrayBuffer()));

  return {
    outputPath,
    lastRow,
    orderCount: classifiedOrders.length,
    previewPath,
    exportedPreviewPath,
    topCheck: topCheck.ndjson,
    bottomCheck: bottomCheck.ndjson,
    formulaErrors: formulaErrors.ndjson,
    finalCheck: finalCheck.ndjson,
    finalErrors: finalErrors.ndjson,
  };
}

if (!buildRequested) {
  await fs.writeFile(
    path.join(inspectDir, "inspection.json"),
    JSON.stringify({ source: source.result, template: template.result }, null, 2),
    "utf8",
  );
}
await fs.writeFile(
  path.join(inspectDir, "extracted-preview.json"),
  JSON.stringify(orders, null, 2),
  "utf8",
);

const buildResult = buildRequested ? await buildFinalWorkbook() : null;

console.log(
  JSON.stringify({
    sourceSheets: source.result.sheets.map((sheet) => ({
      name: sheet.name,
      rows: sheet.values.length,
      cols: sheet.values[0]?.length ?? 0,
      previewPath: sheet.previewPath,
    })),
    templateSheets: template.result.sheets.map((sheet) => ({
      name: sheet.name,
      rows: sheet.values.length,
      cols: sheet.values[0]?.length ?? 0,
      previewPath: sheet.previewPath,
    })),
    extractedOrders: orders.length,
    ordersWithBlankName: orders.filter((order) => !order.name).length,
    ordersWithBlankMeasure: orders.filter((order) => !order.measure).length,
    ordersWithBlankMaterial: orders.filter((order) => !order.material).length,
    ordersWithService: classifiedOrders.filter((order) => order.service).length,
    ordersWithThicknessInMaterial: classifiedOrders.filter((order) => /^\d+(?:[.,]\d+)?\s+mm\b/iu.test(order.material)).length,
    inspectionPath: path.join(inspectDir, "inspection.json"),
    extractedPreviewPath: path.join(inspectDir, "extracted-preview.json"),
    buildResult,
  }),
);

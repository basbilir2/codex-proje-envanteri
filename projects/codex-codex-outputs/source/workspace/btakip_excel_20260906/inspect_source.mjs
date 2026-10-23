import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const sourcePath = "C:/Users/USER/Downloads/siparisler-2026-09-06.xlsx";
const source = await FileBlob.load(sourcePath);
const workbook = await SpreadsheetFile.importXlsx(source);
const summary = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 8000,
  tableMaxRows: 20,
  tableMaxCols: 16,
  tableMaxCellChars: 140,
});
console.log(summary.ndjson);

import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const file = await FileBlob.load("C:/Users/USER/Documents/Codex/2026-09-01/excel-conversion-workspace/outputs/01a05e70-btakip-asi/ASI_Reklam_AnonPerson_0008_BTakip.xlsx");
const workbook = await SpreadsheetFile.importXlsx(file);
const sheet = workbook.worksheets.getItem("BTakip");
const keyRanges = await workbook.inspect({
  kind: "table",
  range: "BTakip!A1:H18",
  include: "values,formulas",
  tableMaxRows: 18,
  tableMaxCols: 8,
  maxChars: 15000,
});
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "post-export formula error scan",
});
console.log(JSON.stringify({
  usedAddress: sheet.getUsedRange().address,
  dateNumberFormat: sheet.getRange("A2:A55").format.numberFormat,
  balanceChecks: sheet.getRange("H2:H55").values.filter((_, index) => [0, 12, 13, 53].includes(index)),
  balanceFormulas: sheet.getRange("H2:H55").formulas.filter((_, index) => [0, 1, 12, 13, 53].includes(index)),
  errors: errors.ndjson,
  keyRanges: keyRanges.ndjson,
}, null, 2));

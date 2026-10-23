import csv
import json
from datetime import datetime
from pathlib import Path

import openpyxl

root = Path(r"C:\Users\USER\AppData\Local\Temp\browser-use\exports")
old_csv = root / "KASA-c2f0f227-89a3-4fa2-846b-11ed5a6bfe61.csv"
new_csv = root / "KASA-338ab684-a5af-484f-8402-b840d568c30d.csv"
old_xlsx = root / "KASA-8f750f36-24fe-467b-bb8b-1974de9bfa80.xlsx"
new_xlsx = root / "KASA-0c992295-03c1-4a95-8c6d-6afed319147a.xlsx"


def load(csv_file, xlsx_file):
    labels = list(csv.reader(csv_file.open(encoding="utf-8-sig", newline="")))
    values = list(openpyxl.load_workbook(xlsx_file, read_only=True, data_only=True)["Sayfa1"].values)
    result = []
    for i in range(1, len(labels)):
        row = values[i]
        if isinstance(row[1], datetime) and row[1] >= datetime(2026, 8, 20):
            result.append({"row": i+1, "date": row[1].date().isoformat(), "income": row[2] or 0,
                           "expense": row[3] or 0, "balance": row[4], "category": labels[i][5],
                           "counterparty": labels[i][6], "description": labels[i][7]})
    return result


old, new = load(old_csv, old_xlsx), load(new_csv, new_xlsx)
old_map = {r["row"]: r for r in old}
new_map = {r["row"]: r for r in new}
changes = []
for key in sorted(old_map.keys() | new_map.keys()):
    if old_map.get(key) != new_map.get(key):
        changes.append({"row": key, "old": old_map.get(key), "new": new_map.get(key)})
print(json.dumps({"old_count": len(old), "new_count": len(new),
                  "old_income": sum(r["income"] for r in old), "new_income": sum(r["income"] for r in new),
                  "old_expense": sum(r["expense"] for r in old), "new_expense": sum(r["expense"] for r in new),
                  "changes": changes}, ensure_ascii=True, indent=2))

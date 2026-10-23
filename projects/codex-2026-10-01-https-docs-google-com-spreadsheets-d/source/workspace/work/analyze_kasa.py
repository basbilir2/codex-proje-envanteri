import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import openpyxl


ROOT = Path(r"C:\Users\USER\AppData\Local\Temp\browser-use\exports")
CSV = ROOT / "KASA-338ab684-a5af-484f-8402-b840d568c30d.csv"
XLSX = ROOT / "KASA-0c992295-03c1-4a95-8c6d-6afed319147a.xlsx"
text_rows = list(csv.reader(CSV.open(encoding="utf-8-sig", newline="")))
value_rows = list(openpyxl.load_workbook(XLSX, read_only=True, data_only=True)["Sayfa1"].values)
start = datetime(2026, 8, 20)
entries = []
for index in range(1, len(text_rows)):
    values = value_rows[index]
    if not isinstance(values[1], datetime) or values[1] < start:
        continue
    labels = text_rows[index]
    entries.append({
        "row": index + 1,
        "date": values[1].strftime("%Y-%m-%d"),
        "income": values[2] or 0,
        "expense": values[3] or 0,
        "balance": values[4],
        "category": labels[5],
        "counterparty": labels[6],
        "description": labels[7],
    })

# User-requested reporting exclusions; the source spreadsheet remains untouched.
excluded_source_rows = {497, 535, 546}
entries = [entry for entry in entries if entry["row"] not in excluded_source_rows]

summary = defaultdict(lambda: {"income": 0, "expense": 0, "income_count": 0, "expense_count": 0})
for e in entries:
    for grouping, key in (("category", e["category"]), ("month", e["date"][:7]), ("date", e["date"])):
        item = summary[(grouping, key)]
        item["income"] += e["income"]
        item["expense"] += e["expense"]
        item["income_count"] += bool(e["income"])
        item["expense_count"] += bool(e["expense"])

output = {
    "row_count": len(entries),
    "first_row": entries[0],
    "last_row": entries[-1],
    "total_income": sum(e["income"] for e in entries),
    "total_expense": sum(e["expense"] for e in entries),
    "income_count": sum(bool(e["income"]) for e in entries),
    "expense_count": sum(bool(e["expense"]) for e in entries),
    "by_category": {key: value for (group, key), value in summary.items() if group == "category"},
    "by_month": {key: value for (group, key), value in summary.items() if group == "month"},
    "column_category_conflicts": [e for e in entries if e["expense"] and e["category"].startswith("GELİR")],
}
print(json.dumps(output, ensure_ascii=True, default=str, indent=2))


def money(amount):
    return f"{amount:,.0f}".replace(",", ".") + " ₺"


def safe(value):
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def detail(entry):
    first, second = safe(entry["counterparty"]), safe(entry["description"])
    return first + (f" — {second}" if second and second.casefold() != first.casefold() else "")


incoming = sorted((e for e in entries if e["income"]), key=lambda e: (e["date"], e["row"]))
outgoing = sorted((e for e in entries if e["expense"]), key=lambda e: (e["date"], e["row"]))
lines = [
    "# KASA: Gelen ve giden para raporu",
    "",
    "**Dönem:** 20 Ağustos–29 Eylül 2026 (iki tarih dahil). "
    "**Kaynak:** KASA Google E-Tablosu, Sayfa1; 1 Ekim 2026'da salt okunur alınan kopya. "
    "Kaynak tablo ve hesaplar değiştirilmedi.",
    "",
    "## Sonuç",
    "",
    f"- **Gelen:** {money(output['total_income'])} ({len(incoming)} hareket)",
    f"- **Giden:** {money(output['total_expense'])} ({len(outgoing)} hareket)",
    f"- **Net kasa hareketi:** {money(output['total_income'] - output['total_expense'])}",
    "",
    "**Toplamların hesabı:** Tablonun GELİR sütunu 140.974 ₺; rapor dışı tutulan 8.340 ₺ çıkarılınca 132.634 ₺. "
    "Tablonun GİDER sütunu 175.649 ₺; rapor dışı tutulan iki ayrı 20.000 ₺ çıkarılınca 135.649 ₺. "
    "Aşağıdaki hareket listelerinde de bu üç kayıt yer almıyor.",
    "",
    "## Aya göre",
    "",
    "| Dönem | Gelen | Giden | Net kasa hareketi |",
    "|---|---:|---:|---:|",
]
for month, totals in output["by_month"].items():
    lines.append(f"| {month} | {money(totals['income'])} | {money(totals['expense'])} | {money(totals['income'] - totals['expense'])} |")
lines += ["", "## Giden paranın sınıfları", "", "| Tablodaki sınıf | Giden | Hareket |", "|---|---:|---:|"]
for category, totals in sorted(output["by_category"].items(), key=lambda pair: pair[1]["expense"], reverse=True):
    if totals["expense"]:
        lines.append(f"| {safe(category)} | {money(totals['expense'])} | {totals['expense_count']} |")
lines += [
    "",
    "## Gün gün gelen ve giden",
    "",
    "| Tarih | Gelen | Giden | Net |",
    "|---|---:|---:|---:|",
]
for date, totals in sorted((key, value) for (group, key), value in summary.items() if group == "date"):
    lines.append(f"| {date} | {money(totals['income'])} | {money(totals['expense'])} | {money(totals['income'] - totals['expense'])} |")
lines += [
    "",
    "## Gelenlerin tamamı",
    "",
    "| Tarih | Tutar | Kayıt açıklaması | Kaynak satır |",
    "|---|---:|---|---:|",
]
for e in incoming:
    lines.append(f"| {e['date']} | {money(e['income'])} | {detail(e)} | {e['row']} |")
lines += ["", "## Gidenlerin tamamı", "", "| Tarih | Tutar | Tablodaki sınıf | Kayıt açıklaması | Kaynak satır |", "|---|---:|---|---|---:|"]
for e in outgoing:
    lines.append(f"| {e['date']} | {money(e['expense'])} | {safe(e['category'])} | {detail(e)} | {e['row']} |")
lines += ["", "**Okuma notları:** GİDER sütunundaki 170 ₺ ve 100 ₺ hareketleri tabloda GELİR - PERAKENDE sınıfıyla etiketli; sütunlarına göre giden tutara dahil edildi. Bir yemek kaydının tarihi 1 Eylül, notu 5'inde ödendi diyor; raporda hücre tarihi kullanıldı."]
destination = Path("outputs/KASA_20_Agustos_2026_itibaren_rapor.md")
destination.parent.mkdir(exist_ok=True)
destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"REPORT={destination.resolve()}")

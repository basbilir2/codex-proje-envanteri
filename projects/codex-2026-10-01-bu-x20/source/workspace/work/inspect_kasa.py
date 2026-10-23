import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'pydeps'))
import xlrd

src = Path(__file__).parent / 'KASA-readonly.xls'
book = xlrd.open_workbook(src, on_demand=True, formatting_info=False)
print('SHEETS', json.dumps([(s.name, s.nrows, s.ncols) for s in book.sheets()], ensure_ascii=False))
for sheet in book.sheets():
    print('\nSHEET', sheet.name)
    nonempty = []
    for ri in range(sheet.nrows):
        vals = [sheet.cell_value(ri, ci) for ci in range(sheet.ncols)]
        cells = [(ci + 1, v) for ci, v in enumerate(vals) if v not in ('', None)]
        if cells:
            nonempty.append((ri + 1, cells))
    print('NONEMPTY ROWS', len(nonempty))
    for ri, cells in nonempty[:45]:
        print(ri, json.dumps(cells, ensure_ascii=False, default=str))
    print('LAST ROWS')
    for ri, cells in nonempty[-10:]:
        print(ri, json.dumps(cells, ensure_ascii=False, default=str))

import sys
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent / 'pydeps'))
import xlrd

b=xlrd.open_workbook(Path(__file__).parent/'KASA-readonly.xls')
s=b.sheet_by_name('Sayfa1')
rows=[]
for i in range(1,s.nrows):
    v=[s.cell_value(i,j) for j in range(9)]
    date=xlrd.xldate_as_datetime(v[1],b.datemode).date().isoformat() if isinstance(v[1],(float,int)) and v[1] else ''
    rows.append(dict(row=i+1,date=date,income=v[2] if isinstance(v[2],(float,int)) else 0,expense=v[3] if isinstance(v[3],(float,int)) else 0,category=str(v[5]),payee=str(v[6]),note=str(v[7])))

print('DATES',min(x['date'] for x in rows),max(x['date'] for x in rows),'ROWS',len(rows))
print('TOTALS',sum(x['income'] for x in rows),sum(x['expense'] for x in rows), 'NET',sum(x['income']-x['expense'] for x in rows))
print('COUNTS',sum(x['income']>0 for x in rows),sum(x['expense']>0 for x in rows),sum(x['income']==x['expense']==0 for x in rows),sum(x['income']>0 and x['expense']>0 for x in rows))
months=defaultdict(lambda:[0,0])
for x in rows:
    months[x['date'][:7]][0]+=x['income']; months[x['date'][:7]][1]+=x['expense']
print('MONTHS',dict(months))
print('INCOME_CAT_EXPENSE',*[x for x in rows if x['category'].startswith('GEL') and x['expense']>0])
print('SPECIAL_EXPENSE',*[x for x in rows if x['category'].startswith('MASRAF - Di') or x['category'].startswith('MALZEME') or x['category'].startswith('MASRAF - Genel')],sep='\n')
cat=defaultdict(lambda:[0,0,0])
for x in rows:
    a=cat[x['category']];a[0]+=x['income'];a[1]+=x['expense'];a[2]+=1
print('CATEGORIES')
for k,v in sorted(cat.items(),key=lambda kv:-kv[1][1]):print(repr(k),v)
dates=defaultdict(lambda:[0,0,0])
for x in rows:
    a=dates[x['date']];a[0]+=x['income'];a[1]+=x['expense'];a[2]+=1
print('DAILY')
for k,v in sorted(dates.items()):print(k,v)
print('TOP_EXPENSE')
for x in sorted(rows,key=lambda x:-x['expense'])[:35]:print(x)
print('TOP_INCOME')
for x in sorted(rows,key=lambda x:-x['income'])[:30]:print(x)
print('ALL_ROWS')
for x in rows:print(x)

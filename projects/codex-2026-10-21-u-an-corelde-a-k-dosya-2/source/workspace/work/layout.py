from pathlib import Path
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject
import json

root = Path(__file__).resolve().parent.parent
src = PdfReader(r'C:\Users\USER\Downloads\Yali1925_19_A4_Baski.pdf')
mm = 72 / 25.4
writer = PdfWriter()
canvas = writer.add_blank_page(width=600*mm, height=2100*mm)
items = []
for i, p in enumerate(src.pages):
    trim = p.trimbox
    l,b,r,t = map(float, trim)
    assert abs((r-l)/mm-210)<0.001 and abs((t-b)/mm-297)<0.001
    p.cropbox = RectangleObject([l,b,r,t])
    col, row = i%2, i//2
    x, y = (3+col*297)*mm, (2100-(row+1)*210)*mm
    # Rotate the A4 trim clockwise; preserve vector content and embedded fonts.
    transform = Transformation((0,-1,1,0,x-b,y+r))
    canvas.merge_transformed_page(p, transform, expand=False)
    items.append(dict(design=i+1, x_mm=3+col*297, y_mm=2100-(row+1)*210, width_mm=297, height_mm=210))
out=root/'outputs'/'Yali1925_19_A4_60cm_Dizilim.pdf'
with out.open('wb') as f: writer.write(f)
check=PdfReader(out)
assert len(check.pages)==1
assert ''.join(check.pages[0].extract_text().split()) == ''.join(''.join(p.extract_text() for p in src.pages).split())
(root/'work'/'layout-check.json').write_text(json.dumps(dict(count=len(items),page_mm=[600,2100],columns=2,rows=10,items=items),indent=2),encoding='utf-8')
print(out)

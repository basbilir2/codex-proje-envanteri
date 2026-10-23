"""Read-only source audit; previews are presentation files, never training inputs."""
import collections, hashlib, json, pathlib, shutil, subprocess
from PIL import Image, ImageOps, ImageDraw, ImageFont
from pypdf import PdfReader

root=pathlib.Path(__file__).resolve().parent
source=pathlib.Path('C:/Users/USER/Downloads/Downloads.rar')
dest=root/'user-assets-20261022'
raw=dest/'raw'; previews=dest/'previews'
raw.mkdir(parents=True,exist_ok=True);previews.mkdir(exist_ok=True)
listing=subprocess.run(['7z','l','-slt','-sccUTF-8',str(source)],capture_output=True,check=True,encoding='utf-8').stdout
members=[]
for block in listing.split('----------\n',1)[1].split('\n\n'):
    values=dict(line.split(' = ',1) for line in block.splitlines() if ' = ' in line)
    if 'Path' not in values or values.get('Folder')=='+':continue
    name=values['Path']; path=pathlib.PureWindowsPath(name)
    if path.is_absolute() or path.drive or '..' in path.parts or ':' in name or any(values.get(k) for k in ['Symbolic Link','Hard Link','Copy Link']):
        raise ValueError('Unsafe archive entry')
    if path.suffix.lower() not in {'.png','.jpg','.jpeg','.pdf'}:raise ValueError('Unexpected file type')
    members.append(values)
assert sum(int(v['Size']) for v in members)<500*1024**2
result=subprocess.run(['7z','x','-y','-aos','-sccUTF-8','-o'+str(raw),str(source)],capture_output=True,encoding='utf-8')
if result.returncode:raise RuntimeError(result.stdout[-1500:]+result.stderr[-1500:])
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
records=[]; display=[]
for number,m in enumerate(members,1):
    path=raw/m['Path']
    record={'id':number,'file':m['Path'],'bytes':path.stat().st_size,'sha256':hashlib.file_digest(path.open('rb'),'sha256').hexdigest()}
    if path.suffix.lower()=='.pdf':
        pdf=PdfReader(path)
        record.update(kind='pdf',pages=len(pdf.pages))
        assert len(pdf.pages)<=30
        for page in range(len(pdf.pages)):
            preview=previews/f'pdf-{number:03d}-p{page+1:02d}'
            subprocess.run(['pdftoppm','-f',str(page+1),'-l',str(page+1),'-singlefile','-scale-to','900','-png',str(path),str(preview)],check=True,capture_output=True)
            display.append((str(number)+f'/p{page+1}',path.name,preview.with_suffix('.png')))
    else:
        with Image.open(path) as image:
            record.update(kind='image',width=image.width,height=image.height,mode=image.mode,alpha='A' in image.getbands())
            gray=ImageOps.exif_transpose(image).convert('L').resize((9,8))
            bits=[gray.getpixel((x,y))>gray.getpixel((x+1,y)) for y in range(8) for x in range(8)]
            record['dhash']=f'{sum(int(bit)<<i for i,bit in enumerate(bits)):016x}'
        display.append((str(number),path.name,path))
    records.append(record)
byhash=collections.defaultdict(list)
for r in records:byhash[r['sha256']].append(r['id'])
duplicates=[v for v in byhash.values() if len(v)>1]
near=[]
images=[r for r in records if r['kind']=='image']
for i,a in enumerate(images):
    for b in images[i+1:]:
        distance=(int(a['dhash'],16)^int(b['dhash'],16)).bit_count()
        if distance<=5 and a['sha256']!=b['sha256']:near.append({'ids':[a['id'],b['id']],'distance':distance})
for start in range(0,len(display),20):
    sheet=Image.new('RGB',(1280,1450),'#e5e7eb');draw=ImageDraw.Draw(sheet)
    for j,(id,name,path) in enumerate(display[start:start+20]):
        x=(j%4)*320;y=(j//4)*290
        with Image.open(path) as original:
            picture=ImageOps.exif_transpose(original).convert('RGBA')
            picture.thumbnail((308,238))
            backdrop=Image.new('RGBA',picture.size,'#dddddd');backdrop.alpha_composite(picture)
            sheet.paste(backdrop.convert('RGB'),(x+6+(308-picture.width)//2,y+5+(238-picture.height)//2))
        draw.text((x+6,y+246),id+' | '+name[:31],fill='black',font=font)
        draw.text((x+6,y+267),name[31:68],fill='black',font=font)
    sheet.save(previews/f'sheet-{start//20+1:02d}.jpg',quality=92)
report={'archive':str(source),'archive_sha256':hashlib.file_digest(source.open('rb'),'sha256').hexdigest(),'files':len(records),'images':len(images),'pdfs':sum(r['kind']=='pdf' for r in records),'pdf_pages':sum(r.get('pages',0) for r in records),'exact_duplicate_groups':duplicates,'near_duplicate_candidates':near,'records':records,'preview_sheets':(len(display)+19)//20,'previews_are_training_inputs':False}
(dest/'inventory.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['records','archive','archive_sha256']},ensure_ascii=False))

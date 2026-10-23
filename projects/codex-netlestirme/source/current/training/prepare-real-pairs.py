"""Extract one original PDF image per design, preserving PDF masks/colors.
Poppler renders the isolated PDF artwork. No tracing, retouching or synthesis.
"""
import hashlib,json,pathlib,subprocess
from pypdf import PdfReader,PdfWriter
from pypdf.generic import NameObject,DictionaryObject,DecodedStreamObject
from PIL import Image,ImageDraw,ImageFont,ImageOps

root=pathlib.Path(__file__).resolve().parent/'user-assets-20261022'
inventory=json.loads((root/'inventory.json').read_text(encoding='utf-8'))
records={r['id']:r for r in inventory['records']}
out=root/'pairs';out.mkdir(exist_ok=True)
mapping=[('wolf',92,106),('mavi',93,107),('zen-cat',94,108),('floral-cat',95,109),('m-stripes',96,110),('chess',97,111),('shark',98,87),('palms',99,88),('black',100,89),('cards',101,90),('black-white',102,91)]
rows=[]
for name,source_id,target_id in mapping:
    target=records[target_id];reader=PdfReader(root/'raw'/target['file']);page=reader.pages[0]
    placed=[]
    def visitor(op,args,cm,tm):
        if op==b'Do':placed.append(str(args[0]))
    page.extract_text(visitor_operand_before=visitor)
    key=placed[0];image=page['/Resources']['/XObject'][key].get_object()
    assert image['/Subtype']=='/Image'
    w,h=int(image['/Width']),int(image['/Height'])
    writer=PdfWriter();newpage=writer.add_blank_page(width=w+64,height=h+64)
    cloned=image.clone(writer)
    resources=DictionaryObject({NameObject('/XObject'):DictionaryObject({NameObject('/Artwork'):cloned.indirect_reference})})
    if '/ColorSpace' in page['/Resources']:
        resources[NameObject('/ColorSpace')]=page['/Resources']['/ColorSpace'].clone(writer)
    newpage[NameObject('/Resources')]=resources
    stream=DecodedStreamObject()
    stream.set_data(f'q 0.86 0.86 0.86 rg 0 0 {w+64} {h+64} re f Q\nq {w} 0 0 {h} 32 32 cm /Artwork Do Q'.encode())
    newpage[NameObject('/Contents')]=writer._add_object(stream)
    pdf=out/(name+'-target.pdf');png=out/(name+'-target.png')
    with pdf.open('wb') as f:writer.write(f)
    subprocess.run(['pdftoppm','-f','1','-l','1','-singlefile','-r','72','-png',str(pdf),str(png.with_suffix(''))],capture_output=True,check=True)
    rows.append({'id':name,'source_id':source_id,'source':'raw/'+records[source_id]['file'],'source_sha256':records[source_id]['sha256'],'target_pdf_id':target_id,'target_pdf':'raw/'+target['file'],'target_pdf_sha256':target['sha256'],'pdf_image_object':key,'image':'pairs/'+png.name,'isolated_pdf':'pairs/'+pdf.name,'target_sha256':hashlib.file_digest(png.open('rb'),'sha256').hexdigest(),'native_pixels':[w,h],'split':'validation' if name in ['mavi','wolf'] else 'train','status':'candidate_requires_pair_review','transformation':'One original PDF image XObject and its soft mask, rendered by Poppler on neutral gray; no artwork edits.'})
(root/'candidate-pairs.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
for start in range(0,len(rows),4):
    sheet=Image.new('RGB',(1280,4*410),'#eeeeee');draw=ImageDraw.Draw(sheet)
    for j,row in enumerate(rows[start:start+4]):
        y=j*410;draw.text((12,y+8),row['id']+' | photographed source / original PDF artwork',font=font,fill='black')
        for col,key in enumerate(['source','image']):
            with Image.open(root/row[key]) as im:
                im=ImageOps.exif_transpose(im).convert('RGBA');im.thumbnail((620,355))
                bg=Image.new('RGBA',im.size,'#dddddd');bg.alpha_composite(im)
                sheet.paste(bg.convert('RGB'),(col*640+(640-im.width)//2,y+40+(355-im.height)//2))
    sheet.save(root/'previews'/f'pairs-{start//4+1:02d}.jpg',quality=93)
print(json.dumps({'candidate_pairs':len(rows),'train_candidates':9,'held_out_design_families':['mavi','wolf'],'original_training_pixels_synthesized':False}))

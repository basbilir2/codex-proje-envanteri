from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
SRC=ROOT/'outputs/surface-upgrade-20261009-220345/native-portrait-final';NEW=OUT/'coupled'
right=NEW/('views/view_0011.png' if (NEW/'views/view_0011.png').exists() else 'views/view_0001.png')
font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',19)
box=(370,1020,770,1540)
items=[('Kaynak fotoğraf',SRC/'source.png'),('Önce · sol uç',SRC/'views/view_0000.png'),('Düzeltme · sol uç',NEW/'views/view_0000.png'),('Önce · sağ uç',SRC/'views/view_0011.png'),('Düzeltme · sağ uç',right)]
canvas=Image.new('RGB',(2000,564),'#222933');draw=ImageDraw.Draw(canvas)
for i,(label,path) in enumerate(items):
    with Image.open(path) as im:canvas.paste(im.crop(box).convert('RGB'),(i*400,44))
    draw.text((i*400+10,10),label,font=font,fill='white')
canvas.save(OUT/'thumb-before-after.png')
compact=Image.new('RGB',(1200,564),'#222933')
for col,source_col in enumerate((0,3,4)):compact.paste(canvas.crop((source_col*400,0,(source_col+1)*400,564)),(col*400,0))
compact.save(OUT/'son-karsilastirma.png')
full=Image.new('RGB',(1400,1203),'#222933');d=ImageDraw.Draw(full)
for i,(label,path) in enumerate([('Önce · sağ uç',SRC/'views/view_0011.png'),('Düzeltme · sağ uç',right)]):
    with Image.open(path) as im:
        im=im.convert('RGB');im.thumbnail((700,1159),Image.Resampling.LANCZOS);full.paste(im,(700*i,44))
    d.text((700*i+10,10),label,font=font,fill='white')
full.save(OUT/'scene-before-after.jpg',quality=95)
print('Comparisons saved')
